"""Deterministic conjugation truth for the grammar verifier.

Spanish v1: Fred Jehle's hand-curated verb database (637 verbs, all
moods/tenses, vendored gzipped in grammar/data/). Every LLM-generated
form MUST match this table or the item is rejected — LLMs are
near-ceiling on Spanish conjugation but the strategy doc documents the
failure modes (rare tenses, agreement, post-training regressions), and
a wrong form on a drill card is worse than no card.

Lookup keys are lowercased Spanish names as they appear in the CSV:
  mood:  indicativo | subjuntivo | imperativo afirmativo | imperativo negativo
  tense: presente | pretérito | imperfecto | futuro | condicional |
         pretérito perfecto | pluscuamperfecto | futuro perfecto |
         condicional perfecto | pretérito anterior
  person: 1s 2s 3s 1p 2p 3p
"""

from __future__ import annotations

import csv
import gzip
import unicodedata
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).parent / "data"

PERSONS = ("1s", "2s", "3s", "1p", "2p", "3p")

_PERSON_COL = {p: f"form_{p}" for p in PERSONS}


def _norm(s: str) -> str:
    """Comparison form: NFC, lowercased, collapsed whitespace. Accents are
    preserved — 'hablo' vs 'habló' is exactly the kind of error we exist
    to catch."""
    s = unicodedata.normalize("NFC", (s or "").strip().lower())
    return " ".join(s.split())


@lru_cache(maxsize=1)
def _load_es() -> dict[tuple[str, str, str], dict[str, str]]:
    """(infinitive, mood, tense) -> {person: form}."""
    table: dict[tuple[str, str, str], dict[str, str]] = {}
    with gzip.open(_DATA / "es_verbs_jehle.csv.gz", "rt", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (_norm(row["infinitive"]), _norm(row["mood"]), _norm(row["tense"]))
            table[key] = {
                p: _norm(row[col]) for p, col in _PERSON_COL.items() if row.get(col)
            }
    return table


def known_verbs(lang: str) -> set[str]:
    if lang != "es":
        return set()
    return {inf for inf, _, _ in _load_es()}


def lookup(lang: str, infinitive: str, mood: str, tense: str,
           person: str) -> str | None:
    """Expected form, or None if the (verb, mood, tense, person) cell is
    unknown to the database (unknown ≠ wrong: caller decides policy)."""
    if lang != "es":
        return None
    forms = _load_es().get((_norm(infinitive), _norm(mood), _norm(tense)))
    if not forms:
        return None
    return forms.get(person)


def verify(lang: str, infinitive: str, mood: str, tense: str, person: str,
           form: str) -> tuple[bool, str | None]:
    """(ok, expected). ok=False when the cell is known and doesn't match,
    OR when the cell is unknown — for v1 an unverifiable form does not
    ship."""
    expected = lookup(lang, infinitive, mood, tense, person)
    if expected is None:
        return False, None
    # Imperative rows prefix pronouns in some sources; Jehle stores the
    # bare form. Accept either the bare form or a 'no ' prefix match for
    # the negative imperative (Jehle already includes 'no').
    return _norm(form) == expected, expected
