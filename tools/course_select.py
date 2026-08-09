#!/usr/bin/env python3
"""Select one DE course unit's exercises from the sealed Hammer corpus.

Usage:
    .venv/bin/python tools/course_select.py \
        idiomatic/grammar/data/course/plans/de_<unit>.plan.json \
        [--corpus-dir /path/to/de_hammer_work/chapters]

Data-driven successor of ``course_select_de_kasus.py`` (RETIRED into this
tool: its hand-picked SELECTIONS table now lives on as the committed plan
``plans/de_kasus.plan.json``; the hygiene gate below is that tool's gate,
factored, unchanged — rerunning this tool on the kasus plan reproduces the
shipped ``de_kasus.exercises.json`` byte for byte).

The PLAN (committed — carries only set ids and metadata, never book text):
    {"lang": "de", "unit": "praepositionen", "chapter": 18,
     "unit_label": "Präpositionen (prepositions)",
     "blocks": [{"block": 1, "card_seq": 2,
                 "exercise_sets": ["3", "5:key"],
                 "max_items": 14,
                 "hammer_refs": ["18.1", "18.2"],
                 "note": "short rationale"}, ...]}
- ``block``: unique, ascending plan-order ints.
- ``card_seq``: the lesson card the block follows (unique; becomes the
  output ``blocks[].block``, which is what interleave_plan keys on).
- ``exercise_sets``: workbook set ids exactly as they appear in the
  corpus chapter file (``ex_no``); the suffix ``:key`` selects the
  printed-answer-key solution mode for construct-the-sentence sets whose
  reconstructed HTML is unusable (same rule the kasus tool applied).
- ``hammer_refs``: §-ids for the block, REQUIRED here because the corpus
  chapter file does not map exercises to printed headers; every ref is
  verified to appear in the chapter's printed ``(GGU …)`` header pool
  (``hammer_sections``) — the mechanical form of the kasus tool's
  "verified against the printed exercise headers" promise.
- ``max_items``: optional cap applied AFTER the hygiene gate, preserving
  book order; going over cap logs a warning and truncates (not fatal).

The corpus is the sealed ``de_hammer_v1`` extraction — transcriptions of
copyrighted books that must NEVER be committed. It is read from the
machine-local main tree by default (CORPUS_DIR) and the selected,
hygiene-gated output is written to the gitignored
``idiomatic/grammar/data/course/book_local/de_<unit>.exercises.json``.

Selection policy (docs/GRAMMAR_COURSE_DESIGN.md):
- book-verbatim items only: any Pass-2 flag excludes the item;
- the structural hygiene gate re-checks every solution (the corpus
  carries occasional mangled reconstructions even on unflagged items);
- ``:key`` sets fall back to the printed answer key verbatim, wrapped in
  one whole-sentence <mark> — still book-verbatim.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import structlog  # noqa: E402

from idiomatic.grammar import course  # noqa: E402

log = structlog.get_logger()

# The sealed corpus lives in the MAIN tree only (gitignored book content;
# worktrees do not carry it) — hence an absolute machine-local default.
CORPUS_DIR = Path(
    "/home/admin/projects/idiomatic/docs/research/grammar_books"
    "/de_hammer_work/chapters"
)
PLANS_DIR = course.DATA_DIR / "plans"

_MARK_SPAN = re.compile(r"<mark>(.*?)</mark>", re.DOTALL)
_WS = re.compile(r"\s+")
_SET_TOKEN = re.compile(r"(\d{1,3})(:key)?")
# Section ids as printed in the (GGU …) headers, e.g. "2.2.2", "1.1.2e".
_HEADER_SECTION = re.compile(r"\d{1,2}(?:\.\d{1,3}){0,3}[a-z]?")
_HEADER_CHAPTER = re.compile(r"Chapter\s+(\d{1,2})")


class PlanError(course.CourseSourceError):
    """A unit plan (or its match against the corpus) is invalid."""


@dataclass(frozen=True)
class PlanBlock:
    block: int
    card_seq: int
    sets: tuple[tuple[int, str], ...]  # (ex_no, mode) with mode html|key
    hammer_refs: tuple[str, ...]
    max_items: int | None
    note: str = ""


@dataclass(frozen=True)
class UnitPlan:
    path: Path
    lang: str
    unit: str
    chapter: int
    unit_label: str
    blocks: tuple[PlanBlock, ...] = field(default_factory=tuple)


def _plan_error(path: Path, message: str) -> PlanError:
    return PlanError(f"{path.name}: {message}")


def load_plan(path: Path) -> UnitPlan:
    """Parse + validate one ``de_<unit>.plan.json`` against DE_UNITS."""
    path = Path(path)
    match = re.fullmatch(r"de_([a-z0-9]+(?:-[a-z0-9]+)*)\.plan\.json",
                         path.name)
    if match is None:
        raise _plan_error(path, "filename must be de_<unit>.plan.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise _plan_error(path, "expected a JSON object")
    unit = data.get("unit")
    if unit != match.group(1):
        raise _plan_error(path, "unit field must match the filename")
    if data.get("lang") != "de":
        raise _plan_error(path, "lang must be 'de'")
    try:
        chapter, unit_label = course.de_unit(unit)
    except ValueError as exc:
        raise _plan_error(path, str(exc)) from exc
    if data.get("chapter") != chapter:
        raise _plan_error(
            path, f"chapter must be {chapter} for unit {unit!r}, "
            f"got {data.get('chapter')!r}"
        )
    if data.get("unit_label") != unit_label:
        raise _plan_error(
            path, f"unit_label must be {unit_label!r} (DE_UNITS is the "
            f"authority), got {data.get('unit_label')!r}"
        )

    blocks_raw = data.get("blocks")
    if not isinstance(blocks_raw, list) or not blocks_raw:
        raise _plan_error(path, "blocks must be a nonempty array")
    blocks: list[PlanBlock] = []
    seen_seqs: set[int] = set()
    for raw in blocks_raw:
        if not isinstance(raw, dict):
            raise _plan_error(path, "every block must be an object")
        block_no = raw.get("block")
        if not isinstance(block_no, int) or isinstance(block_no, bool) \
                or block_no < 1:
            raise _plan_error(path, "block must be an integer >= 1")
        if blocks and block_no <= blocks[-1].block:
            raise _plan_error(
                path, f"block ints must be unique ascending "
                f"(block {block_no} after {blocks[-1].block})"
            )
        card_seq = raw.get("card_seq")
        if not isinstance(card_seq, int) or isinstance(card_seq, bool) \
                or card_seq < 1:
            raise _plan_error(
                path, f"block {block_no}: card_seq must be an integer >= 1"
            )
        if card_seq in seen_seqs:
            raise _plan_error(
                path, f"block {block_no}: duplicate card_seq {card_seq}"
            )
        seen_seqs.add(card_seq)

        sets_raw = raw.get("exercise_sets")
        if not isinstance(sets_raw, list) or not sets_raw:
            raise _plan_error(
                path, f"block {block_no}: exercise_sets must be nonempty"
            )
        sets: list[tuple[int, str]] = []
        for token in sets_raw:
            token_str = str(token).strip()
            token_match = _SET_TOKEN.fullmatch(token_str)
            if token_match is None:
                raise _plan_error(
                    path, f"block {block_no}: invalid exercise set "
                    f"{token!r} (want a workbook ex_no, optionally ':key')"
                )
            sets.append((
                int(token_match.group(1)),
                "key" if token_match.group(2) else "html",
            ))

        refs_raw = raw.get("hammer_refs")
        if (not isinstance(refs_raw, list) or not refs_raw or any(
                not isinstance(ref, str)
                or not course._REF_ID.fullmatch(ref.strip())
                for ref in refs_raw)):
            raise _plan_error(
                path, f"block {block_no}: hammer_refs must be a nonempty "
                "list of §-ids"
            )

        max_items = raw.get("max_items")
        if max_items is not None and (
            not isinstance(max_items, int) or isinstance(max_items, bool)
            or max_items < 1
        ):
            raise _plan_error(
                path, f"block {block_no}: max_items must be null or an "
                "integer >= 1"
            )
        blocks.append(PlanBlock(
            block=block_no,
            card_seq=card_seq,
            sets=tuple(sets),
            hammer_refs=tuple(ref.strip() for ref in refs_raw),
            max_items=max_items,
            note=str(raw.get("note") or ""),
        ))
    return UnitPlan(
        path=path, lang="de", unit=unit, chapter=chapter,
        unit_label=unit_label, blocks=tuple(blocks),
    )


# ---------------------------------------------------------------------------
# Structural hygiene gate — factored VERBATIM from course_select_de_kasus.py
# (same checks, same skip reasons; the kasus output must stay reproducible).
# ---------------------------------------------------------------------------


def _plain(text: str) -> str:
    return _WS.sub(" ", _MARK_SPAN.sub(lambda m: m.group(1), text)).strip()


def _solution_ok(prompt: str, solution: str) -> tuple[bool, str]:
    """Structural hygiene: catch the corpus's known mangling patterns."""
    spans = _MARK_SPAN.findall(solution)
    if not spans or any(not span.strip() for span in spans):
        return False, "no nonempty <mark> span"
    if "___" in solution:
        return False, "blank placeholder left in solution"
    stripped = _MARK_SPAN.sub("", solution)
    if "<" in stripped or ">" in stripped:
        return False, "markup beyond <mark>"
    if " / " in _plain(solution):
        return False, "slash-list remnant in solution"
    prompt_norm = _WS.sub(" ", prompt)
    for span in spans:
        span_norm = _WS.sub(" ", span).strip()
        if len(span_norm.split()) >= 3 and span_norm in prompt_norm:
            return False, f"mark duplicates prompt text: {span_norm[:40]!r}"
    return True, ""


def _key_solution(item: dict) -> str | None:
    key = _WS.sub(" ", (item.get("answer_key_raw") or "")).strip()
    if not key or "___" in key or "<" in key or ">" in key:
        return None
    return f"<mark>{key}</mark>"


def _header_ref_pool(chapter_data: dict) -> set[str]:
    """Every §-id printed in the chapter's (GGU …) exercise headers."""
    pool: set[str] = set()
    for header in chapter_data.get("hammer_sections", []):
        pool.update(_HEADER_SECTION.findall(header))
        pool.update(
            f"Ch. {number}" for number in _HEADER_CHAPTER.findall(header)
        )
    return pool


def select_unit(plan: UnitPlan, chapter_data: dict) -> tuple[dict, dict]:
    """Explode the plan's sets into gated atomic exercises.

    Returns ``(payload, report)``: the payload is the exact kasus
    exercises-file shape (accepted by course.parse_exercises_file), the
    report carries kept/skipped/capped detail for the CLI.
    """
    if chapter_data.get("chapter") != plan.chapter:
        raise PlanError(
            f"{plan.path.name}: corpus chapter is "
            f"{chapter_data.get('chapter')!r}, plan wants {plan.chapter}"
        )
    ref_pool = _header_ref_pool(chapter_data)
    for block in plan.blocks:
        for ref in block.hammer_refs:
            if ref not in ref_pool:
                raise PlanError(
                    f"{plan.path.name}: block {block.block}: hammer ref "
                    f"§{ref} does not appear in the chapter's printed "
                    f"headers: {chapter_data.get('hammer_sections', [])}"
                )

    by_no = {ex["ex_no"]: ex for ex in chapter_data["exercises"]}
    out_blocks: list[dict] = []
    skipped: list[str] = []
    capped: list[str] = []
    kept = 0
    for block in plan.blocks:
        items_out: list[dict] = []
        for ex_no, mode in block.sets:
            if ex_no not in by_no:
                available = ", ".join(str(no) for no in sorted(by_no))
                raise PlanError(
                    f"{plan.path.name}: block {block.block}: unknown "
                    f"exercise set {ex_no} in ch{plan.chapter:02d}; "
                    f"available set ids: {available}"
                )
            exercise = by_no[ex_no]
            instruction = _WS.sub(" ", exercise["instruction"]).strip()
            for item in exercise["items"]:
                label = f"ex{ex_no} item {item['item_no']}"
                if item["flags"]:
                    skipped.append(f"{label}: flags {item['flags']}")
                    continue
                prompt = _WS.sub(" ", item["prompt"]).strip()
                if not prompt:
                    skipped.append(f"{label}: empty prompt")
                    continue
                if mode == "key":
                    solution = _key_solution(item)
                    if solution is None:
                        skipped.append(f"{label}: unusable answer key")
                        continue
                else:
                    solution = _WS.sub(
                        " ", item["full_solution_html"]
                    ).strip()
                    ok, reason = _solution_ok(prompt, solution)
                    if not ok:
                        skipped.append(f"{label}: {reason}")
                        continue
                item_no = str(item["item_no"]).strip().lower()
                if not re.fullmatch(r"[a-z0-9]+", item_no):
                    skipped.append(f"{label}: unusable item number")
                    continue
                items_out.append({
                    "id": (
                        f"pgg-c{plan.chapter:02d}-e{ex_no:02d}-i{item_no}"
                    ),
                    "instruction": instruction,
                    "prompt": prompt,
                    "solution_html": solution,
                    "alternatives": [
                        _WS.sub(" ", alt).strip()
                        for alt in item.get("alternatives", [])
                        if alt.strip()
                    ],
                    "hammer_refs": list(block.hammer_refs),
                    "source_ref": (
                        f"PGG Kap. {plan.chapter}, Üb. {ex_no}, "
                        f"Nr. {item['item_no']} (S. {exercise['page']}; "
                        f"Key S. {item['key_page']})"
                    ),
                    "provenance": "book-verbatim",
                })
        if not items_out:
            raise PlanError(
                f"{plan.path.name}: block {block.block} is empty after the "
                "hygiene gate — pick different sets"
            )
        if block.max_items is not None and len(items_out) > block.max_items:
            capped.append(
                f"block {block.block} (card c{block.card_seq:02d}): kept "
                f"first {block.max_items} of {len(items_out)} gated items"
            )
            items_out = items_out[:block.max_items]
        kept += len(items_out)
        out_blocks.append({"block": block.card_seq, "exercises": items_out})

    title = chapter_data.get("title", "")
    payload = {
        "lang": "de",
        "unit": plan.unit,
        "source": {
            "workbook": (
                "Practising German Grammar (Kaiser & Kohl), "
                f"Ch. {plan.chapter} {title}"
            ),
            "reference": (
                "Hammer's German Grammar and Usage, 7th ed. (Durrell), "
                f"Ch. {plan.chapter}"
            ),
            "corpus": "de_hammer_v1 (sealed extraction, Pass 3)",
        },
        "blocks": out_blocks,
    }
    report = {"kept": kept, "skipped": skipped, "capped": capped}
    return payload, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path,
                        help="path to plans/de_<unit>.plan.json")
    parser.add_argument("--corpus-dir", type=Path, default=CORPUS_DIR,
                        help="sealed corpus chapters directory")
    args = parser.parse_args()

    plan = load_plan(args.plan)
    chapter_path = args.corpus_dir / f"ch{plan.chapter:02d}.json"
    if not chapter_path.is_file():
        raise SystemExit(
            f"corpus chapter not found: {chapter_path} (the sealed corpus "
            "is machine-local; pass --corpus-dir)"
        )
    chapter_data = json.loads(chapter_path.read_text(encoding="utf-8"))
    payload, report = select_unit(plan, chapter_data)

    # Cross-check card_seq against the lesson when it already exists
    # (lesson authoring runs in parallel — absence is not an error).
    lesson_path = course.LESSON_DIR / f"de_{plan.unit}.md"
    if lesson_path.is_file():
        lesson = course.parse_course_lesson(lesson_path)
        seqs = {card.seq for card in lesson.cards}
        bad = [b.card_seq for b in plan.blocks if b.card_seq not in seqs]
        if bad:
            raise SystemExit(
                f"plan card_seq(s) {bad} not in lesson cards 1..{len(seqs)}"
            )
    else:
        log.info("course.select.no_lesson_yet", lesson=str(lesson_path))

    out_path = course.BOOK_LOCAL_DIR / f"de_{plan.unit}.exercises.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    # Belt-and-braces: the output must parse under the course contract.
    course.parse_exercises_file(out_path)

    log.info(
        "course.select.written", unit=plan.unit, path=str(out_path),
        kept=report["kept"], blocks=len(payload["blocks"]),
        skipped=len(report["skipped"]), capped=len(report["capped"]),
    )
    for line in report["capped"]:
        log.warning("course.select.over_cap", detail=line)
    for block in payload["blocks"]:
        sources = sorted({
            item["id"].split("-i")[0] for item in block["exercises"]
        })
        print(f"  block c{block['block']:02d}: "
              f"{len(block['exercises']):3d} items  ({', '.join(sources)})")
    print(f"skipped {len(report['skipped'])}:")
    for line in report["skipped"]:
        print(f"  - {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
