#!/usr/bin/env python3
"""Mechanical audit gate for Exercises 2.0 batch outputs.

Runs every check that does not require linguistic judgment: triage coverage,
notes/keep agreement, full note-schema validation (via the shipping parser),
cloze reduction, wrong-language heuristics, and keep-rate stats.  Chunks that
pass go to the human/premium linguistic review; chunks that fail go back to
codex.  Usage: tools/x2_batch_gate.py [chunk-name ...] (default: all inputs
with landed output pairs).
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from idiomatic.grammar import exercises2 as x2  # noqa: E402
from idiomatic.grammar import exercises2_shadowing as shadow  # noqa: E402

BATCH_DIR = REPO / "idiomatic" / "grammar" / "data" / "exercises2" / "batches"

_LANG_HINTS = {
    # Bare ``la`` is shared by Spanish, French, and Italian.  It supplied all
    # three "Spanish" votes in two known false positives, so only the
    # Spanish-exclusive plural articles remain evidence here.
    "es": (r"[¿¡]|ción\b|\bel\b|\blas\b|\blos\b|\bsin embargo\b|ñ", r""),
    "pt": (r"ção\b|ções\b|[ãõ]|\bnão\b|\buma\b|\bos\b|\bas\b", r""),
    # ``à`` is productive Italian too (dipenderà, disponibilità).  French
    # circumflexes and function words remain the useful discriminators.
    "fr": (r"\bles\b|\bdes\b|\bdans\b|\bpas\b|[âêîôû]|qu'|l'|d'", r""),
    "de": (r"[äöüß]|\bnicht\b|\bund\b|\bdie\b|\bder\b|\bdas\b|\bsich\b", r""),
    "it": (r"zione\b|\bperché\b|\bpiù\b|\bgli\b|\bnon\b|\bche\b|\bè\b", r""),
}

_CHUNK_RE = re.compile(
    r"^(?P<lang>de|es|fr|it|pt)_(?P<topic>[a-z0-9]+(?:_[a-z0-9]+)*?)"
    r"(?:_pilot)?_b[0-9]{2}$"
)

_TENSES_INPUT_KEYS = frozenset({"id", "en", "old_back"})
_TENSES_TRIAGE_KEYS = frozenset({"id", "en", "verdict", "reason"})
_TENSES_NOTE_KEYS = frozenset({
    "id", "en", "category", "tl", "alts", "register", "trap",
    "example_tl", "example_en", "cloze", "note",
})
# docs/commissions/EXERCISES2_TENSES_ADDENDUM.md, Note contract §1.
# Keep this narrower than exercises2.CATEGORIES: Wave 4--6 lexical categories
# are valid globally but must never leak into a Wave 3 Tenses chunk.
_TENSES_CATEGORIES = frozenset({
    "past-anteriority",
    "ongoing-to-present",
    "modal-construction",
    "counterfactual-sequence",
    "future-perfect",
    "literary-sequence",
})


def _strict_tenses_rows(
    rows: object,
    *,
    label: str,
    exact_keys: frozenset[str],
    list_keys: frozenset[str] = frozenset(),
) -> list[str]:
    """Validate the non-coercing Wave 3 JSON surface before normal parsing."""

    if not isinstance(rows, list):
        return [f"Tenses {label} must be a JSON array"]
    problems: list[str] = []
    ids: list[str] = []
    for index, row in enumerate(rows):
        location = f"Tenses {label}[{index}]"
        if not isinstance(row, dict):
            problems.append(f"{location} must be an object")
            continue
        present = set(row)
        if present != exact_keys:
            missing = sorted(exact_keys - present)
            extra = sorted(present - exact_keys)
            problems.append(
                f"{location} keys mismatch (missing {missing}, extra {extra})"
            )
        for key in sorted(present & exact_keys):
            value = row[key]
            if key in list_keys:
                if not isinstance(value, list) or any(
                    not isinstance(item, str) for item in value
                ):
                    problems.append(f"{location}.{key} must be a list of strings")
            elif not isinstance(value, str):
                problems.append(f"{location}.{key} must be a string")
        if isinstance(row.get("id"), str):
            ids.append(row["id"])
    duplicates = sorted(item_id for item_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        problems.append(f"Tenses {label} has duplicate ids: {duplicates[:5]}")
    return problems


def _exact_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return unicodedata.normalize("NFC", value).strip()


def _example_tl(row: dict, lang: str) -> str:
    """Read current or legacy-pilot target-example spelling."""

    value = row.get("example_tl")
    if not isinstance(value, str):
        value = row.get(f"example_{lang}")
    return _exact_text(value)


def _tenses_example_duplicate_problems(
    *,
    lang: str,
    notes_raw: list[dict],
    root: Path,
    notes_path: Path,
) -> list[str]:
    """Reject exact reuse of a Tenses practice example within one language.

    A Wave 3 example must be a new sentence.  Compare it with production
    answers/source prompts and examples from every other landed Tenses chunk,
    as well as already merged Exercises2 topics.  A future merged copy of the
    same Tenses note is ignored so re-gating after merge remains idempotent.
    """

    # side -> normalized text -> human-readable origins
    primary: dict[str, dict[str, list[tuple[str, str, str, str]]]] = {
        "tl": {}, "en": {},
    }
    examples: dict[str, dict[str, list[tuple[str, str, str, str]]]] = {
        "tl": {}, "en": {},
    }

    def add(
        target: dict[str, dict[str, list[tuple[str, str, str, str]]]],
        side: str,
        value: object,
        origin: tuple[str, str, str, str],
    ) -> None:
        normalized = _exact_text(value)
        if normalized:
            target[side].setdefault(normalized, []).append(origin)

    def add_external_rows(
        rows: object, *, kind: str, topic: str, source: str,
    ) -> None:
        if not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            item_id = row.get("id")
            if not isinstance(item_id, str):
                continue
            add(primary, "tl", row.get("tl", row.get(f"{lang}_main")),
                (kind, topic, item_id, f"{source}:tl"))
            add(primary, "en", row.get("en"),
                (kind, topic, item_id, f"{source}:en"))
            add(examples, "tl", _example_tl(row, lang),
                (kind, topic, item_id, f"{source}:example_tl"))
            add(examples, "en", row.get("example_en"),
                (kind, topic, item_id, f"{source}:example_en"))

    for path in sorted((root / "output").glob(f"{lang}_tenses_b*_notes.json")):
        if path.resolve() == notes_path.resolve():
            continue
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # That chunk's own gate reports malformed output.  It must not make
            # an otherwise valid neighbouring chunk impossible to inspect.
            continue
        add_external_rows(rows, kind="landed", topic="tenses", source=path.name)

    merged_dir = root.parent / "notes"
    for path in sorted(merged_dir.glob(f"{lang}_*.json")):
        topic = path.stem[len(lang) + 1:]
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        add_external_rows(rows, kind="merged", topic=topic, source=path.name)

    # Index every current answer/source before inspecting its examples so an
    # example cannot copy a later row's primary sentence and escape the gate.
    for row in notes_raw:
        item_id = row["id"]
        add(primary, "tl", row["tl"], ("current", "tenses", item_id, "tl"))
        add(primary, "en", row["en"], ("current", "tenses", item_id, "en"))

    current_examples: dict[str, dict[str, list[str]]] = {"tl": {}, "en": {}}
    for row in notes_raw:
        for side, key in (("tl", "example_tl"), ("en", "example_en")):
            normalized = _exact_text(row[key])
            current_examples[side].setdefault(normalized, []).append(row["id"])

    conflicts: list[str] = []
    for row in notes_raw:
        item_id = row["id"]
        for side, key in (("tl", "example_tl"), ("en", "example_en")):
            normalized = _exact_text(row[key])
            origins = list(primary[side].get(normalized, ()))
            origins.extend(examples[side].get(normalized, ()))
            for other_id in current_examples[side].get(normalized, ()):
                if other_id != item_id:
                    origins.append(("current", "tenses", other_id, key))

            filtered = []
            for origin in origins:
                kind, topic, origin_id, detail = origin
                # A merged Wave 3 row is the expected durable copy of this same
                # authored note, not an independent duplicate.
                if kind == "merged" and topic == "tenses" and origin_id == item_id:
                    continue
                # Do not compare the current example with itself.  Current
                # primary fields remain intentionally visible to catch a
                # supposed example that simply repeats its own answer/source.
                if kind == "current" and origin_id == item_id and detail == key:
                    continue
                filtered.append(origin)
            if filtered:
                labels = sorted({
                    f"{kind}:{topic}:{origin_id}:{detail}"
                    for kind, topic, origin_id, detail in filtered
                })
                conflicts.append(f"{item_id}:{key} duplicates {labels[0]}")
    if conflicts:
        return [f"exact duplicate Tenses examples: {conflicts[:8]}"]
    return []


def _chunk_lang_topic(chunk: str) -> tuple[str, str]:
    """Parse the full topic slug, including multiword wave 4--6 topics."""
    match = _CHUNK_RE.fullmatch(chunk)
    if match is None:
        raise ValueError(f"invalid chunk name {chunk!r}")
    return match.group("lang"), match.group("topic")


def _lang_score(text: str, lang: str) -> int:
    return len(re.findall(_LANG_HINTS[lang][0], f" {text.lower()} "))


def _wrong_language(text: str, lang: str) -> str | None:
    """Flag when another supported language outscores the target by 2+.

    Known false-positive classes (adjudicated 2026-08-04): the fr pattern's
    l'/d'/qu' elisions and circumflexes also occur in Italian (l'accordo,
    d'altronde) and Portuguese (independência) — suppress those signals
    when scoring fr against it/pt targets."""
    own = _lang_score(text, lang)
    for other, _pattern in _LANG_HINTS.items():
        if other == lang:
            continue
        score = _lang_score(text, other)
        if other == "fr" and lang in ("it", "pt"):
            score -= len(re.findall(r"l'|d'|qu'|[êâîôû]", text.lower()))
        if score >= max(own + 2, 3):
            return other
    return None


def gate_chunk(
    chunk: str, *, batch_dir: Path | None = None,
) -> tuple[bool, list[str], dict]:
    problems: list[str] = []
    stats: dict = {"chunk": chunk}
    root = Path(batch_dir) if batch_dir is not None else BATCH_DIR
    input_path = root / "input" / f"{chunk}.json"
    notes_path = root / "output" / f"{chunk}_notes.json"
    triage_path = root / "output" / f"{chunk}_triage.json"
    if not input_path.exists():
        return False, [f"unknown chunk {chunk!r}"], stats
    if not notes_path.exists() or not triage_path.exists():
        return False, ["output pair not landed yet"], stats

    try:
        lang, topic = _chunk_lang_topic(chunk)
    except ValueError as exc:
        return False, [str(exc)], stats
    try:
        inputs = json.loads(input_path.read_text(encoding="utf-8"))
        notes_raw = json.loads(notes_path.read_text(encoding="utf-8"))
        triage = json.loads(triage_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"invalid JSON: {exc}"], stats

    if topic == "tenses":
        problems.extend(_strict_tenses_rows(
            inputs, label="input", exact_keys=_TENSES_INPUT_KEYS,
        ))
        problems.extend(_strict_tenses_rows(
            triage, label="triage", exact_keys=_TENSES_TRIAGE_KEYS,
        ))
        problems.extend(_strict_tenses_rows(
            notes_raw, label="notes", exact_keys=_TENSES_NOTE_KEYS,
            list_keys=frozenset({"alts"}),
        ))
        # Stop before the legacy/general checks index malformed rows.  The
        # complete schema/type diagnostics above are more useful than a crash
        # or a cascade of misleading ID mismatches.
        if problems:
            return False, problems, stats

    input_ids = [row["id"] for row in inputs]
    input_by_id = {row["id"]: row for row in inputs}
    triage_ids = [row.get("id") for row in triage]
    if sorted(triage_ids) != sorted(input_ids):
        missing = set(input_ids) - set(triage_ids)
        extra = set(triage_ids) - set(input_ids)
        problems.append(
            f"triage id mismatch (missing {sorted(missing)[:5]}, extra {sorted(extra)[:5]})"
        )
    elif triage_ids != input_ids:
        problems.append("triage does not preserve input order")
    changed_triage_en = [
        row.get("id") for row in triage
        if row.get("id") in input_by_id
        and row.get("en") != input_by_id[row["id"]].get("en")
    ]
    if changed_triage_en:
        problems.append(f"triage changed source English: {changed_triage_en[:5]}")
    bad_verdicts = [row["id"] for row in triage
                    if row.get("verdict") not in ("keep", "drop")]
    if bad_verdicts:
        problems.append(f"invalid verdicts: {bad_verdicts[:5]}")
    if topic == "tenses":
        blank_drop_reasons = [
            row["id"] for row in triage
            if row["verdict"] == "drop" and not row["reason"].strip()
        ]
        multiline_drop_reasons = [
            row["id"] for row in triage
            if row["verdict"] == "drop"
            and ("\n" in row["reason"] or "\r" in row["reason"])
        ]
        if blank_drop_reasons:
            problems.append(
                f"Tenses drop reasons must be nonempty: {blank_drop_reasons[:5]}"
            )
        if multiline_drop_reasons:
            problems.append(
                f"Tenses drop reasons must be single-line: {multiline_drop_reasons[:5]}"
            )
    keep_ids = {row["id"] for row in triage if row.get("verdict") == "keep"}
    note_ids = [row.get("id") for row in notes_raw]
    if sorted(note_ids) != sorted(keep_ids):
        problems.append(
            f"notes/keep mismatch (notes {len(note_ids)}, keeps {len(keep_ids)})"
        )
    expected_note_order = [
        row["id"] for row in triage if row.get("verdict") == "keep"
    ]
    if note_ids == expected_note_order:
        pass
    elif sorted(note_ids) == sorted(keep_ids):
        problems.append("notes do not preserve kept-input order")
    changed_note_en = [
        raw.get("id") for raw in notes_raw
        if isinstance(raw, dict) and raw.get("id") in input_by_id
        and raw.get("en") != input_by_id[raw["id"]].get("en")
    ]
    if changed_note_en:
        problems.append(f"notes changed source English: {changed_note_en[:5]}")

    if topic == "tenses":
        bad_categories = [
            f"{row['id']}:{row['category']}" for row in notes_raw
            if row["category"] not in _TENSES_CATEGORIES
        ]
        if bad_categories:
            problems.append(
                f"invalid Tenses categories: {bad_categories[:8]}"
            )
        problems.extend(_tenses_example_duplicate_problems(
            lang=lang, notes_raw=notes_raw, root=root, notes_path=notes_path,
        ))

    old_backs = {row["id"]: row.get("old_back", "") for row in inputs}
    parsed = 0
    wrong_lang: list[str] = []
    bad_example_lengths: list[str] = []
    copied_legacy = 0
    if topic == "big_tech_phrases":
        try:
            parsed_notes = shadow.parse_notes_data(
                notes_raw, lang=lang, source_name=f"{chunk}_notes.json",
            )
        except shadow.ShadowSourceError as exc:
            problems.append(str(exc))
            parsed_notes = []
        texts_by_note = ((note, (note.tl,)) for note in parsed_notes)
    else:
        parsed_notes = []
        for raw in notes_raw:
            try:
                parsed_notes.append(
                    x2._parse_note(Path(f"{lang}_{topic}.json"), lang, topic, raw)
                )
            except x2.Ex2SourceError as exc:
                problems.append(str(exc))
        texts_by_note = (
            (note, (note.tl, note.example_tl)) for note in parsed_notes
        )

    for note, texts in texts_by_note:
        parsed += 1
        for text in texts:
            other = _wrong_language(text, lang)
            if other:
                wrong_lang.append(f"{note.item_id}:{other}:{text[:40]!r}")
        if topic != "big_tech_phrases":
            words = re.findall(r"[^\W_]+(?:['’\-][^\W_]+)*", note.example_tl)
            if topic in {
                "tenses", "fancy_vocab", "big_tech_vocab",
                "cold_war_vocab", "geopolitics",
            } and not 18 <= len(words) <= 30:
                bad_example_lengths.append(f"{note.item_id}:{len(words)}")
        if note.tl and note.tl == old_backs.get(note.item_id, ""):
            copied_legacy += 1
    if wrong_lang:
        problems.append(f"wrong-language suspects: {wrong_lang[:8]}")
    if bad_example_lengths:
        problems.append(f"example word counts outside 18..30: {bad_example_lengths[:8]}")

    verdict_counts = Counter(row.get("verdict") for row in triage)
    stats.update({
        "inputs": len(inputs),
        "keep": verdict_counts.get("keep", 0),
        "drop": verdict_counts.get("drop", 0),
        "notes_parsed": parsed,
        "with_trap": sum(
            1 for raw in notes_raw
            if isinstance(raw, dict) and str(raw.get("trap", "")).strip()
        ),
        "same_as_legacy": copied_legacy,
    })
    return not problems, problems, stats


def main() -> int:
    if len(sys.argv) > 1:
        chunks = sys.argv[1:]
    else:
        chunks = sorted(
            path.stem for path in (BATCH_DIR / "input").glob("*.json")
            if (BATCH_DIR / "output" / f"{path.stem}_notes.json").exists()
        )
    if not chunks:
        print("no landed output pairs to gate")
        return 1
    failures = 0
    for chunk in chunks:
        ok, problems, stats = gate_chunk(chunk)
        line = " ".join(f"{key}={value}" for key, value in stats.items() if key != "chunk")
        print(f"{'PASS' if ok else 'FAIL'} {chunk}  {line}")
        for problem in problems:
            print(f"  - {problem}")
        failures += not ok
    print(f"\n{len(chunks) - failures}/{len(chunks)} chunks pass the mechanical gate")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
