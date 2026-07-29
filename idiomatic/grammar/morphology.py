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
    if lang == "es":
        forms = _load_es().get((_norm(infinitive), _norm(mood), _norm(tense)))
        return forms.get(person) if forms else None
    if lang in _VERBECC_LANGS:
        forms = (_load_verbecc(lang)
                 .get(_norm(infinitive), {})
                 .get(_norm(mood), {})
                 .get(_norm(tense)))
        return forms.get(person) if forms else None
    return None


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


# ============================================================================
# German: noun gender + article declension + preposition case government.
# Gender table: gambolputty/german-nouns (de.wiktionary-derived, CC BY-SA),
# frequency-filtered to 4k unambiguous, non-weak nouns (surface form stable
# across cases). Prep bank: grammar/data/de_preps.json (codex-produced,
# review-validated). Articles are a closed 2×4×4 matrix — hardcoded.
# ============================================================================

DE_CASES = ("nom", "akk", "dat", "gen")

_DE_DEF = {
    "nom": {"m": "der", "f": "die", "n": "das"},
    "akk": {"m": "den", "f": "die", "n": "das"},
    "dat": {"m": "dem", "f": "der", "n": "dem"},
    "gen": {"m": "des", "f": "der", "n": "des"},
}
_DE_INDEF = {
    "nom": {"m": "ein", "f": "eine", "n": "ein"},
    "akk": {"m": "einen", "f": "eine", "n": "ein"},
    "dat": {"m": "einem", "f": "einer", "n": "einem"},
    "gen": {"m": "eines", "f": "einer", "n": "eines"},
}


@lru_cache(maxsize=1)
def _load_de_nouns() -> dict[str, str]:
    import gzip as _gz
    import json
    with _gz.open(_DATA / "de_nouns.json.gz", "rt", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_de_preps() -> dict[str, str]:
    import json
    entries = json.loads((_DATA / "de_preps.json").read_text(encoding="utf-8"))
    return {e["prep"]: e["case"] for e in entries}


def de_gender(noun: str) -> str | None:
    return _load_de_nouns().get((noun or "").strip())


def de_prep_case(prep: str) -> str | None:
    """'akk' | 'dat' | 'gen' | 'wechsel' | None."""
    return _load_de_preps().get((prep or "").strip().lower())


def de_article(case: str, gender: str, definite: bool = True) -> str | None:
    table = _DE_DEF if definite else _DE_INDEF
    return table.get(case, {}).get(gender)


# ============================================================================
# fr / it / pt verbs: tables generated offline from verbecc (Verbiste-derived,
# GPL data; template-based conjugations only, no ML-predicted verbs) and
# vendored as {infinitive: {mood: {tense: {person: form}}}}. Compound forms
# default to the MASCULINE participle (être/essere verbs) — curriculum
# guidance keeps subjects masculine in those units.
# ============================================================================

_VERBECC_LANGS = ("fr", "it", "pt")


@lru_cache(maxsize=4)
def _load_verbecc(lang: str) -> dict:
    import gzip as _gz
    import json
    with _gz.open(_DATA / f"{lang}_verbs_verbecc.json.gz", "rt",
                  encoding="utf-8") as f:
        return json.load(f)
