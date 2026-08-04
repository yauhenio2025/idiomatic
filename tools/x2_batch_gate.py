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
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from idiomatic.grammar import exercises2 as x2  # noqa: E402

BATCH_DIR = REPO / "idiomatic" / "grammar" / "data" / "exercises2" / "batches"

_LANG_HINTS = {
    "es": (r"[¿¡]|ción\b|\bel\b|\blas?\b|\blos\b|\bsin embargo\b|ñ", r""),
    "pt": (r"ção\b|ções\b|[ãõ]|\bnão\b|\buma\b|\bos\b|\bas\b", r""),
    "fr": (r"\bles\b|\bdes\b|\bdans\b|\bpas\b|[àâêîôû]|qu'|l'|d'", r""),
    "de": (r"[äöüß]|\bnicht\b|\bund\b|\bdie\b|\bder\b|\bdas\b|\bsich\b", r""),
    "it": (r"zione\b|\bperché\b|\bpiù\b|\bgli\b|\bnon\b|\bche\b|\bè\b", r""),
}


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


def gate_chunk(chunk: str) -> tuple[bool, list[str], dict]:
    problems: list[str] = []
    stats: dict = {"chunk": chunk}
    input_path = BATCH_DIR / "input" / f"{chunk}.json"
    notes_path = BATCH_DIR / "output" / f"{chunk}_notes.json"
    triage_path = BATCH_DIR / "output" / f"{chunk}_triage.json"
    if not input_path.exists():
        return False, [f"unknown chunk {chunk!r}"], stats
    if not notes_path.exists() or not triage_path.exists():
        return False, ["output pair not landed yet"], stats

    lang, topic = chunk.split("_")[0], chunk.split("_")[1]
    inputs = json.loads(input_path.read_text(encoding="utf-8"))
    try:
        notes_raw = json.loads(notes_path.read_text(encoding="utf-8"))
        triage = json.loads(triage_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"invalid JSON: {exc}"], stats

    input_ids = [row["id"] for row in inputs]
    triage_ids = [row.get("id") for row in triage]
    if sorted(triage_ids) != sorted(input_ids):
        missing = set(input_ids) - set(triage_ids)
        extra = set(triage_ids) - set(input_ids)
        problems.append(
            f"triage id mismatch (missing {sorted(missing)[:5]}, extra {sorted(extra)[:5]})"
        )
    bad_verdicts = [row["id"] for row in triage
                    if row.get("verdict") not in ("keep", "drop")]
    if bad_verdicts:
        problems.append(f"invalid verdicts: {bad_verdicts[:5]}")
    keep_ids = {row["id"] for row in triage if row.get("verdict") == "keep"}
    note_ids = [row.get("id") for row in notes_raw]
    if sorted(note_ids) != sorted(keep_ids):
        problems.append(
            f"notes/keep mismatch (notes {len(note_ids)}, keeps {len(keep_ids)})"
        )

    old_backs = {row["id"]: row.get("old_back", "") for row in inputs}
    parsed = 0
    wrong_lang: list[str] = []
    copied_legacy = 0
    for raw in notes_raw:
        try:
            note = x2._parse_note(Path(f"{lang}_{topic}.json"), lang, topic, raw)
        except x2.Ex2SourceError as exc:
            problems.append(str(exc))
            continue
        parsed += 1
        for text in (note.tl, note.example_tl):
            other = _wrong_language(text, lang)
            if other:
                wrong_lang.append(f"{note.item_id}:{other}:{text[:40]!r}")
        if note.tl and note.tl == old_backs.get(note.item_id, ""):
            copied_legacy += 1
    if wrong_lang:
        problems.append(f"wrong-language suspects: {wrong_lang[:8]}")

    verdict_counts = Counter(row.get("verdict") for row in triage)
    stats.update({
        "inputs": len(inputs),
        "keep": verdict_counts.get("keep", 0),
        "drop": verdict_counts.get("drop", 0),
        "notes_parsed": parsed,
        "with_trap": sum(1 for raw in notes_raw if str(raw.get("trap", "")).strip()),
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
