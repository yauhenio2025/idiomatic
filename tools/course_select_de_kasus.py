#!/usr/bin/env python3
"""Select the DE Kasus pilot exercises from the sealed Hammer workbook corpus.

Usage:
    .venv/bin/python tools/course_select_de_kasus.py /path/to/extracted/corpus

The corpus is the extracted ``de_hammer_v1.tar.gz`` (docs/research/
grammar_books/) — transcriptions of copyrighted books that must NEVER be
committed: this tool reads them from a machine-local scratch directory and
writes the selected, hygiene-gated exercise file to the gitignored
``idiomatic/grammar/data/course/book_local/de_kasus.exercises.json``.

Selection policy (docs/GRAMMAR_COURSE_DESIGN.md):
- book-verbatim items only: any Pass-2 flag (reconstructed-by-model,
  judgment-call, answer-by-model, source-suspect, …) excludes the item;
- a structural hygiene gate re-checks every solution because the corpus
  carries occasional mangled reconstructions even on unflagged items
  (Case ex. 16 duplicates prompt text inside <mark>);
- ``mode="key"`` exercises (construct-the-whole-sentence types whose
  reconstructed HTML is unusable) fall back to the printed answer key
  verbatim, wrapped in one whole-sentence <mark> — still book-verbatim.

The per-exercise Hammer §-refs below were verified against the workbook's
printed exercise headers (the ``(GGU …)`` lines in work/workbook_pages.txt).
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = (
    REPO_ROOT / "idiomatic" / "grammar" / "data" / "course" / "book_local"
    / "de_kasus.exercises.json"
)

_MARK_SPAN = re.compile(r"<mark>(.*?)</mark>", re.DOTALL)
_WS = re.compile(r"\s+")


@dataclass(frozen=True)
class Selection:
    ex_no: int
    block: int          # lesson card seq the exercises follow
    hammer_refs: tuple[str, ...]  # verified against the printed GGU header
    mode: str           # "html" (use full_solution_html) | "key" (answer key)


# Lesson card map (idiomatic/grammar/data/course/lessons/de_kasus.md):
#  c01 why cases   c02 nominative   c03 acc object   c04 acc adverbial
#  c05 dat object  c06 free dative  c07 genitive     c08 genitive-vs-von
#  c09 apposition  c10 measurement
SELECTIONS = [
    Selection(1, 2, ("2.1.3", "16.6"), "key"),
    Selection(4, 3, ("2.2", "6.1"), "html"),
    Selection(5, 4, ("2.2.2", "2.3.3"), "html"),
    Selection(12, 5, ("2.5",), "html"),
    Selection(10, 6, ("2.5.2",), "key"),
    Selection(9, 8, ("2.4",), "html"),
    Selection(14, 9, ("2.6",), "html"),
    Selection(17, 10, ("2.7",), "html"),
]


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


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    corpus = Path(sys.argv[1])
    chapter = json.loads(
        (corpus / "chapters" / "ch02.json").read_text(encoding="utf-8")
    )
    assert chapter["chapter"] == 2 and chapter["title"] == "Case"
    by_no = {ex["ex_no"]: ex for ex in chapter["exercises"]}

    blocks: dict[int, list[dict]] = {}
    kept = 0
    skipped: list[str] = []
    for selection in sorted(SELECTIONS, key=lambda s: s.block):
        exercise = by_no[selection.ex_no]
        instruction = _WS.sub(" ", exercise["instruction"]).strip()
        for item in exercise["items"]:
            label = f"ex{selection.ex_no} item {item['item_no']}"
            if item["flags"]:
                skipped.append(f"{label}: flags {item['flags']}")
                continue
            prompt = _WS.sub(" ", item["prompt"]).strip()
            if not prompt:
                skipped.append(f"{label}: empty prompt")
                continue
            if selection.mode == "key":
                solution = _key_solution(item)
                if solution is None:
                    skipped.append(f"{label}: unusable answer key")
                    continue
            else:
                solution = _WS.sub(" ", item["full_solution_html"]).strip()
                ok, reason = _solution_ok(prompt, solution)
                if not ok:
                    skipped.append(f"{label}: {reason}")
                    continue
            item_no = str(item["item_no"]).strip().lower()
            if not re.fullmatch(r"[a-z0-9]+", item_no):
                skipped.append(f"{label}: unusable item number")
                continue
            blocks.setdefault(selection.block, []).append({
                "id": f"pgg-c02-e{selection.ex_no:02d}-i{item_no}",
                "instruction": instruction,
                "prompt": prompt,
                "solution_html": solution,
                "alternatives": [
                    _WS.sub(" ", alt).strip()
                    for alt in item.get("alternatives", []) if alt.strip()
                ],
                "hammer_refs": list(selection.hammer_refs),
                "source_ref": (
                    f"PGG Kap. 2, Üb. {selection.ex_no}, Nr. {item['item_no']}"
                    f" (S. {exercise['page']}; Key S. {item['key_page']})"
                ),
                "provenance": "book-verbatim",
            })
            kept += 1

    payload = {
        "lang": "de",
        "unit": "kasus",
        "source": {
            "workbook": "Practising German Grammar (Kaiser & Kohl), Ch. 2 Case",
            "reference": "Hammer's German Grammar and Usage, 7th ed. "
                         "(Durrell), Ch. 2",
            "corpus": "de_hammer_v1 (sealed extraction, Pass 3)",
        },
        "blocks": [
            {"block": block, "exercises": items}
            for block, items in sorted(blocks.items())
        ],
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(f"kept {kept} items into {len(blocks)} blocks -> {OUT_PATH}")
    for block, items in sorted(blocks.items()):
        sources = sorted({item["id"].split("-i")[0] for item in items})
        print(f"  block c{block:02d}: {len(items):3d} items  ({', '.join(sources)})")
    print(f"skipped {len(skipped)}:")
    for line in skipped:
        print(f"  - {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
