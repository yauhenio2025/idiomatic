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
# German: noun gender + NP declension + preposition case government.
# Gender table: gambolputty/german-nouns (de.wiktionary-derived, CC BY-SA),
# vendored as a gender-only table of predominantly non-weak nouns. Prep bank:
# grammar/data/de_preps.json (codex-produced,
# review-validated). Articles and adjective endings are closed matrices.
# ============================================================================

DE_CASES = ("nom", "akk", "dat", "gen")
DE_NUMBERS = ("sg", "pl")

_DE_DEF = {
    "nom": {"m": "der", "f": "die", "n": "das", "pl": "die"},
    "akk": {"m": "den", "f": "die", "n": "das", "pl": "die"},
    "dat": {"m": "dem", "f": "der", "n": "dem", "pl": "den"},
    "gen": {"m": "des", "f": "der", "n": "des", "pl": "der"},
}
_DE_INDEF = {
    "nom": {"m": "ein", "f": "eine", "n": "ein"},
    "akk": {"m": "einen", "f": "eine", "n": "ein"},
    "dat": {"m": "einem", "f": "einer", "n": "einem"},
    "gen": {"m": "eines", "f": "einer", "n": "eines"},
}

# Adjective endings are indexed by declension pattern, case, then gender.
# "pl" is a number cell rather than a fourth gender.
_DE_ADJ_ENDINGS = {
    "weak": {
        "nom": {"m": "e", "f": "e", "n": "e", "pl": "en"},
        "akk": {"m": "en", "f": "e", "n": "e", "pl": "en"},
        "dat": {"m": "en", "f": "en", "n": "en", "pl": "en"},
        "gen": {"m": "en", "f": "en", "n": "en", "pl": "en"},
    },
    "mixed": {
        "nom": {"m": "er", "f": "e", "n": "es", "pl": "en"},
        "akk": {"m": "en", "f": "e", "n": "es", "pl": "en"},
        "dat": {"m": "en", "f": "en", "n": "en", "pl": "en"},
        "gen": {"m": "en", "f": "en", "n": "en", "pl": "en"},
    },
    "strong": {
        "nom": {"m": "er", "f": "e", "n": "es", "pl": "e"},
        "akk": {"m": "en", "f": "e", "n": "es", "pl": "e"},
        "dat": {"m": "em", "f": "er", "n": "em", "pl": "en"},
        "gen": {"m": "en", "f": "er", "n": "en", "pl": "er"},
    },
}

# Suffixes for ein-class determiners.  The empty cells in nominative
# masculine and nominative/accusative neuter are precisely the cells in
# which the adjective has to carry the gender signal (mixed declension).
_DE_EIN_ENDINGS = {
    "nom": {"m": "", "f": "e", "n": "", "pl": "e"},
    "akk": {"m": "en", "f": "e", "n": "", "pl": "e"},
    "dat": {"m": "em", "f": "er", "n": "em", "pl": "en"},
    "gen": {"m": "es", "f": "er", "n": "es", "pl": "er"},
}

_DE_POSSESSIVES = frozenset({
    "mein", "dein", "sein", "ihr", "unser", "euer",
})

# Mixed-declension nouns use n-declension in the oblique cases but retain
# an additional genitive -s.  Herz is the sole neuter member and also keeps
# its bare form in the accusative.  These explicit exceptions keep the data
# file itself a reviewable list of standard lemmas.
_DE_MIXED_GENITIVES = {
    "Buchstabe": "Buchstabens",
    "Friede": "Friedens",
    "Funke": "Funkens",
    "Gedanke": "Gedankens",
    "Glaube": "Glaubens",
    "Name": "Namens",
    "Same": "Samens",
    "Wille": "Willens",
    "Herz": "Herzens",
}
_DE_WEAK_OBLIQUE_OVERRIDES = {
    "Bauer": "Bauern",
    "Herr": "Herrn",
    "Nachbar": "Nachbarn",
    "Ungar": "Ungarn",
    "Herz": "Herzen",
}
_DE_WEAK_PLURAL_OVERRIDES = {
    "Herr": "Herren",
    "Herz": "Herzen",
}
_DE_SINGULAR_ONLY_WEAK = frozenset({"Glaube"})

# Counted masculine/neuter units conventionally remain unmarked after a
# numeral ("mit zwanzig Schilling").  With this fixed public signature the
# absence of a determiner is the only available signal for that construction,
# so the exception is deliberately narrow and exact.  Article-bearing count
# nouns still use the ordinary plural surface supplied by the caller, e.g.
# decline_np("Schillinge", case="dat", number="pl", definiteness="definite")
# -> "den Schillingen".
_DE_BARE_COUNTED_UNITS = frozenset({
    "Cent", "Dollar", "Euro", "Franken", "Grad", "Gramm", "Kilogramm",
    "Liter", "Meter", "Pfund", "Prozent", "Schilling", "Watt", "Zoll",
})

# A few plural surfaces do not take the otherwise productive dative -n.
# Watt is the unit plural ("die/den Watt"); the homographic landscape noun
# reaches the regular plural by being supplied as "Watten".
_DE_DATIVE_PLURAL_INVARIANTS = frozenset({"Watt"})

# These adjectives are used attributively without German adjective endings.
# Rejecting them is safer than certifying mechanical forms such as *lilae*.
_DE_INDECLINABLE_ADJECTIVES = frozenset({
    "klasse", "lila", "prima", "rosa", "super",
})

# Genitive formation is not fully predictable from spelling. These common
# lexical cells precede the productive -s/-es heuristic so the deterministic
# engine never blesses forms such as *Buses*, *Kürbises*, or *Jobes*.
_DE_GENITIVE_OVERRIDES = {
    "Atlas": "Atlas",
    "Bonus": "Bonus",
    "Bus": "Busses",
    "Campus": "Campus",
    "Chef": "Chefs",
    "Club": "Clubs",
    "Deal": "Deals",
    "Fokus": "Fokus",
    "Job": "Jobs",
    "Kaktus": "Kaktus",
    "Kürbis": "Kürbisses",
    "Rhythmus": "Rhythmus",
    "Status": "Status",
    "Team": "Teams",
    "Trend": "Trends",
    "Zirkus": "Zirkus",
}


@lru_cache(maxsize=1)
def _load_de_nouns() -> dict[str, str]:
    import gzip as _gz
    import json
    with _gz.open(_DATA / "de_nouns.json.gz", "rt", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_de_weak_nouns() -> frozenset[str]:
    import json
    entries = json.loads(
        (_DATA / "de_weak_nouns.json").read_text(encoding="utf-8")
    )
    if not isinstance(entries, list) or not all(isinstance(x, str) for x in entries):
        raise ValueError("de_weak_nouns.json must be a list of noun lemmas")
    return frozenset(entries)


@lru_cache(maxsize=1)
def _load_de_preps() -> dict[str, str]:
    import json
    entries = json.loads((_DATA / "de_preps.json").read_text(encoding="utf-8"))
    return {e["prep"]: e["case"] for e in entries}


def de_gender(noun: str) -> str | None:
    noun = (noun or "").strip()
    # The vendored gender table intentionally lacks most weak nouns and has
    # an archaic neuter entry for Mensch.  Standard weak-list membership is
    # authoritative for the productive engine.
    if noun == "Herz":
        return "n"
    if noun in _load_de_weak_nouns():
        return "m"
    return _load_de_nouns().get(noun)


def de_prep_case(prep: str) -> str | None:
    """'akk' | 'dat' | 'gen' | 'wechsel' | None."""
    return _load_de_preps().get((prep or "").strip().lower())


def de_article(case: str, gender: str, definite: bool = True) -> str | None:
    table = _DE_DEF if definite else _DE_INDEF
    return table.get(case, {}).get(gender)


def _de_number(number: str) -> str:
    value = (number or "").strip().lower()
    aliases = {"sg": "sg", "singular": "sg", "pl": "pl", "plural": "pl"}
    try:
        return aliases[value]
    except KeyError as exc:
        raise ValueError(f"unsupported German number: {number!r}") from exc


def _de_case(case: str) -> str:
    value = (case or "").strip().lower()
    if value not in DE_CASES:
        raise ValueError(f"unsupported German case: {case!r}")
    return value


def _de_determiner(definiteness: str | None, number: str) -> tuple[str, str]:
    """Return ``(surface-class/base, adjective pattern)``.

    The first value is ``definite``, ``bare``, or the actual ein-class stem.
    ``possessive`` intentionally defaults to *mein* because the fixed API has
    no separate possessor argument.
    """
    raw = "none" if definiteness is None else str(definiteness).strip()
    value = raw.lower()
    if value in {"definite", "der"}:
        return "definite", "weak"
    if value in {"none", "bare", "strong"}:
        return "bare", "strong"
    if value in {"indefinite", "ein"}:
        if number == "pl":
            raise ValueError("ein has no plural; use bare, kein, or a possessive")
        return "ein", "mixed"
    if value == "kein":
        return "kein", "mixed"
    if value == "possessive":
        return "mein", "mixed"
    if value in _DE_POSSESSIVES:
        # Preserve the formal second-person capital in Ihr.
        return "Ihr" if raw == "Ihr" else value, "mixed"
    raise ValueError(f"unsupported German definiteness: {definiteness!r}")


def _de_ein_class(stem: str, case: str, gender: str) -> str:
    ending = _DE_EIN_ENDINGS[case][gender]
    # Standard inflected forms contract euer- to eur- (eure, eurem, ...).
    if stem.lower() == "euer" and ending:
        stem = stem[:-2] + "r"
    return stem + ending


def _de_adjective_stem(adjective: str) -> str:
    """Return the attributive stem used before a declension ending.

    The caller supplies degree: ``härtest`` therefore becomes ``härteste``;
    the function does not attempt to derive a superlative from ``hart``.
    Only productive spelling contractions needed when adding an ending live
    here.
    """
    adjective = adjective.strip()
    lower = adjective.lower()
    if lower in _DE_INDECLINABLE_ADJECTIVES:
        raise ValueError(
            f"indeclinable German adjective is not supported: {adjective!r}"
        )
    if lower.endswith("hoch"):
        return adjective[:-2] + adjective[-1]     # hoch -> hoh
    if lower.endswith("el"):
        return adjective[:-2] + adjective[-1]     # dunkel -> dunkl
    if lower.endswith(("sauer", "teuer", "ungeheuer")):
        return adjective[:-2] + adjective[-1]     # teuer -> teur
    if lower.endswith("e"):
        return adjective[:-1]                     # leise -> leis
    return adjective


def _de_weak_oblique(noun: str) -> str:
    if noun in _DE_WEAK_OBLIQUE_OVERRIDES:
        return _DE_WEAK_OBLIQUE_OVERRIDES[noun]
    if noun.endswith("e"):
        return noun + "n"
    return noun + "en"


def _de_weak_plural(noun: str) -> str:
    return _DE_WEAK_PLURAL_OVERRIDES.get(noun, _de_weak_oblique(noun))


def _de_is_monosyllabic(noun: str) -> bool:
    groups = 0
    in_vowel = False
    for char in noun.lower():
        is_vowel = char in "aeiouyäöü"
        if is_vowel and not in_vowel:
            groups += 1
        in_vowel = is_vowel
    return groups == 1


def _de_genitive_singular(noun: str) -> str:
    lower = noun.lower()
    if noun in _DE_GENITIVE_OVERRIDES:
        return _DE_GENITIVE_OVERRIDES[noun]
    if lower.endswith("nis"):
        return noun + "ses"                       # Zeugnis -> Zeugnisses
    if lower.endswith("us"):
        return noun                                # Status -> Status
    if lower.endswith(("s", "ß", "x", "z", "tz", "tsch")):
        return noun + "es"
    if lower.endswith(("chen", "lein", "el", "en", "er")):
        return noun + "s"
    if lower[-1:] in "aeiouyäöü":
        return noun + "s"
    return noun + ("es" if _de_is_monosyllabic(noun) else "s")


def _decline_de_noun(noun: str, *, case: str, number: str, gender: str,
                     determiner: str, has_adjective: bool) -> str:
    weak = noun in _load_de_weak_nouns()
    if number == "pl":
        if weak and noun in _DE_SINGULAR_ONLY_WEAK:
            raise ValueError(f"German noun has no standard plural: {noun!r}")
        # A weak lemma is the one safe class for which this engine can derive
        # a plural.  Otherwise noun is already the nominative plural surface.
        surface = _de_weak_plural(noun) if weak else noun
        # A bare NP without an adjective is the narrow proxy for an omitted
        # numeral ("mit zwanzig Schilling"). Do not apply it to an ordinary
        # adjectival plural such as "mit wenigen Metern".
        if (determiner == "bare" and not has_adjective
                and noun in _DE_BARE_COUNTED_UNITS):
            return noun
        if (case == "dat" and surface not in _DE_DATIVE_PLURAL_INVARIANTS
                and not surface.lower().endswith(("n", "s"))):
            surface += "n"
        return surface

    if weak:
        if noun == "Herz" and case == "akk":
            return noun
        if case == "nom":
            return noun
        if case == "gen" and noun in _DE_MIXED_GENITIVES:
            return _DE_MIXED_GENITIVES[noun]
        return _de_weak_oblique(noun)
    if case == "gen" and gender in {"m", "n"}:
        return _de_genitive_singular(noun)
    return noun


def decline_np(noun: str, *, case: str, number: str,
               definiteness: str | None, adjective: str | None = None) -> str:
    """Produce a deterministic German noun phrase.

    ``noun`` is the nominative surface for the requested number.  German
    plural formation is not predictable from gender, so callers pass an
    ordinary plural as such (``Kinder``); a weak lemma is the one class whose
    plural this engine can safely derive (``Student`` -> ``Studenten``).
    Lexical validation of an ordinary plural belongs to the caller; the
    adjective-card verifier restricts generation to a curated plural bank.

    Definiteness accepts ``definite``/``der``, ``indefinite``/``ein``,
    ``none``/``bare``/``strong``, ``kein``, ``possessive`` (default *mein*),
    or an actual possessive stem.  Invalid or unverifiable inputs raise
    ``ValueError`` rather than silently shipping a wrong drill answer.
    """
    noun = (noun or "").strip()
    if not noun:
        raise ValueError("German noun must not be empty")
    case = _de_case(case)
    number = _de_number(number)
    determiner, pattern = _de_determiner(definiteness, number)
    gender = "pl" if number == "pl" else de_gender(noun)
    if gender not in {"m", "f", "n", "pl"}:
        raise ValueError(f"German noun is not in gender DB: {noun!r}")

    article = ""
    if determiner == "definite":
        article = _DE_DEF[case][gender]
    elif determiner != "bare":
        article = _de_ein_class(determiner, case, gender)

    inflected_adjective = ""
    if adjective is not None:
        if not adjective.strip():
            raise ValueError("German adjective must not be empty")
        ending = _DE_ADJ_ENDINGS[pattern][case][gender]
        inflected_adjective = _de_adjective_stem(adjective) + ending

    inflected_noun = _decline_de_noun(
        noun, case=case, number=number, gender=gender, determiner=determiner,
        has_adjective=adjective is not None,
    )
    return " ".join(x for x in (article, inflected_adjective, inflected_noun) if x)


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
