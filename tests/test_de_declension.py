"""Exhaustive tests for the deterministic German NP declension engine."""

import json
from pathlib import Path

import pytest

from idiomatic.grammar import morphology as m


_MATRIX = {
    "weak": {
        ("Mann", "sg"): (
            "der gute Mann",
            "den guten Mann",
            "dem guten Mann",
            "des guten Mannes",
        ),
        ("Frau", "sg"): (
            "die gute Frau",
            "die gute Frau",
            "der guten Frau",
            "der guten Frau",
        ),
        ("Kind", "sg"): (
            "das gute Kind",
            "das gute Kind",
            "dem guten Kind",
            "des guten Kindes",
        ),
        ("Kinder", "pl"): (
            "die guten Kinder",
            "die guten Kinder",
            "den guten Kindern",
            "der guten Kinder",
        ),
    },
    "mixed": {
        ("Mann", "sg"): (
            "ein guter Mann",
            "einen guten Mann",
            "einem guten Mann",
            "eines guten Mannes",
        ),
        ("Frau", "sg"): (
            "eine gute Frau",
            "eine gute Frau",
            "einer guten Frau",
            "einer guten Frau",
        ),
        ("Kind", "sg"): (
            "ein gutes Kind",
            "ein gutes Kind",
            "einem guten Kind",
            "eines guten Kindes",
        ),
        ("Kinder", "pl"): (
            "keine guten Kinder",
            "keine guten Kinder",
            "keinen guten Kindern",
            "keiner guten Kinder",
        ),
    },
    "strong": {
        ("Mann", "sg"): (
            "guter Mann",
            "guten Mann",
            "gutem Mann",
            "guten Mannes",
        ),
        ("Frau", "sg"): (
            "gute Frau",
            "gute Frau",
            "guter Frau",
            "guter Frau",
        ),
        ("Kind", "sg"): (
            "gutes Kind",
            "gutes Kind",
            "gutem Kind",
            "guten Kindes",
        ),
        ("Kinder", "pl"): (
            "gute Kinder",
            "gute Kinder",
            "guten Kindern",
            "guter Kinder",
        ),
    },
}


def _matrix_params():
    for pattern, nouns in _MATRIX.items():
        for (noun, number), phrases in nouns.items():
            definiteness = (
                "definite" if pattern == "weak"
                else ("kein" if number == "pl" else "ein")
                if pattern == "mixed"
                else "bare"
            )
            for case, phrase in zip(m.DE_CASES, phrases, strict=True):
                yield pytest.param(
                    noun, number, case, definiteness, phrase,
                    id=f"{pattern}-{number}-{noun}-{case}",
                )


@pytest.mark.parametrize(
    "noun,number,case,definiteness,expected", list(_matrix_params()),
)
def test_complete_adjective_declension_matrix(
    noun, number, case, definiteness, expected,
):
    assert m.decline_np(
        noun,
        case=case,
        number=number,
        definiteness=definiteness,
        adjective="gut",
    ) == expected


def test_attested_adjective_fossils():
    assert m.decline_np(
        "Konkurrent", case="nom", number="sg",
        definiteness="der", adjective="härtest",
    ) == "der härteste Konkurrent"
    assert m.decline_np(
        "Weltbild", case="akk", number="sg",
        definiteness="kein", adjective="kohärent",
    ) == "kein kohärentes Weltbild"
    assert m.decline_np(
        "Ziel", case="nom", number="sg",
        definiteness="mein", adjective="ultimativ",
    ) == "mein ultimatives Ziel"
    assert m.decline_np(
        "Schlüsse", case="akk", number="pl",
        definiteness="bare", adjective="tiefgründig",
    ) == "tiefgründige Schlüsse"
    assert m.decline_np(
        "Publikum", case="akk", number="sg",
        definiteness="ein", adjective="größtmöglich",
    ) == "ein größtmögliches Publikum"


@pytest.mark.parametrize(
    "adjective,noun,expected",
    [
        ("hoch", "Haus", "das hohe Haus"),
        ("dunkel", "Haus", "das dunkle Haus"),
        ("teuer", "Auto", "das teure Auto"),
        ("leise", "Stimme", "die leise Stimme"),
    ],
)
def test_adjective_stem_spelling(adjective, noun, expected):
    assert m.decline_np(
        noun, case="nom", number="singular",
        definiteness="definite", adjective=adjective,
    ) == expected


def test_weak_and_mixed_noun_inflection():
    assert m.de_gender("Konkurrent") == "m"
    assert m.de_gender("Mensch") == "m"  # overrides archaic vendored neuter
    assert m.de_gender("Herz") == "n"

    assert m.decline_np(
        "Junge", case="nom", number="sg", definiteness="der",
    ) == "der Junge"
    assert m.decline_np(
        "Junge", case="akk", number="sg", definiteness="der",
    ) == "den Jungen"
    assert m.decline_np(
        "Student", case="dat", number="sg", definiteness="der",
    ) == "dem Studenten"
    assert m.decline_np(
        "Konkurrent", case="gen", number="sg", definiteness="der",
    ) == "des Konkurrenten"
    assert m.decline_np(
        "Herr", case="dat", number="sg", definiteness="der",
    ) == "dem Herrn"
    assert m.decline_np(
        "Herr", case="nom", number="pl", definiteness="der",
    ) == "die Herren"
    assert m.decline_np(
        "Name", case="gen", number="sg", definiteness="der",
    ) == "des Namens"
    assert m.decline_np(
        "Herz", case="akk", number="sg", definiteness="der",
    ) == "das Herz"
    assert m.decline_np(
        "Herz", case="dat", number="sg", definiteness="der",
    ) == "dem Herzen"
    assert m.decline_np(
        "Herz", case="gen", number="sg", definiteness="der",
    ) == "des Herzens"
    # Vetter has a plural in -n but is strong in the singular.
    assert m.decline_np(
        "Vetter", case="akk", number="sg", definiteness="der",
    ) == "den Vetter"
    assert m.decline_np(
        "Vetter", case="gen", number="sg", definiteness="der",
    ) == "des Vetters"


@pytest.mark.parametrize(
    "noun,oblique",
    [
        ("Asteroid", "Asteroiden"),
        ("Automat", "Automaten"),
        ("Komet", "Kometen"),
        ("Planet", "Planeten"),
    ],
)
def test_additional_standard_weak_nouns(noun, oblique):
    assert m.decline_np(
        noun, case="akk", number="sg", definiteness="definite",
    ) == f"den {oblique}"


def test_weak_lemma_can_supply_its_plural():
    assert m.decline_np(
        "Student", case="nom", number="plural", definiteness="kein",
    ) == "keine Studenten"
    assert m.decline_np(
        "Student", case="dat", number="pl", definiteness="kein",
    ) == "keinen Studenten"
    with pytest.raises(ValueError, match="no standard plural"):
        m.decline_np(
            "Glaube", case="nom", number="pl", definiteness="definite",
        )


@pytest.mark.parametrize(
    "noun,expected",
    [
        ("Kinder", "den Kindern"),
        ("Frauen", "den Frauen"),
        ("Autos", "den Autos"),
    ],
)
def test_dative_plural_n(noun, expected):
    assert m.decline_np(
        noun, case="dat", number="pl", definiteness="definite",
    ) == expected


def test_bare_counted_unit_is_narrowly_invariant():
    assert m.decline_np(
        "Schilling", case="dat", number="pl", definiteness="bare",
    ) == "Schilling"
    # An article-bearing ordinary plural is passed in its nominative surface.
    assert m.decline_np(
        "Schillinge", case="dat", number="pl", definiteness="definite",
    ) == "den Schillingen"
    # An adjective signals an ordinary bare plural, not an omitted numeral.
    assert m.decline_np(
        "Meter", case="dat", number="pl", definiteness="bare",
        adjective="wenig",
    ) == "wenigen Metern"
    assert m.decline_np(
        "Watt", case="dat", number="pl", definiteness="bare",
    ) == "Watt"
    assert m.decline_np(
        "Watt", case="dat", number="pl", definiteness="definite",
    ) == "den Watt"


@pytest.mark.parametrize(
    "noun,expected",
    [
        ("Mann", "des Mannes"),
        ("Kind", "des Kindes"),
        ("Lehrer", "des Lehrers"),
        ("Auto", "des Autos"),
        ("Zeugnis", "des Zeugnisses"),
    ],
)
def test_genitive_s_es_heuristic(noun, expected):
    assert m.decline_np(
        noun, case="gen", number="sg", definiteness="definite",
    ) == expected


@pytest.mark.parametrize(
    "noun,expected",
    [
        ("Bus", "des Busses"),
        ("Kürbis", "des Kürbisses"),
        ("Campus", "des Campus"),
        ("Status", "des Status"),
        ("Job", "des Jobs"),
        ("Team", "des Teams"),
    ],
)
def test_lexical_genitive_overrides(noun, expected):
    assert m.decline_np(
        noun, case="gen", number="sg", definiteness="definite",
    ) == expected


def test_determiner_modes_and_aliases():
    assert m.de_article("dat", "pl") == "den"
    assert m.de_article("dat", "pl", definite=False) is None
    assert m.decline_np(
        "Kind", case="nom", number="singular",
        definiteness="possessive", adjective="neu",
    ) == "mein neues Kind"
    assert m.decline_np(
        "Kinder", case="dat", number="plural",
        definiteness="euer", adjective="neu",
    ) == "euren neuen Kindern"
    assert m.decline_np(
        "Frau", case="nom", number="sg",
        definiteness="Ihr", adjective="neu",
    ) == "Ihre neue Frau"
    assert m.decline_np(
        "Kind", case="nom", number="sg", definiteness=None,
    ) == "Kind"


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"noun": "", "case": "nom", "number": "sg",
          "definiteness": "der"}, "must not be empty"),
        ({"noun": "Kind", "case": "voc", "number": "sg",
          "definiteness": "der"}, "unsupported German case"),
        ({"noun": "Kind", "case": "nom", "number": "dual",
          "definiteness": "der"}, "unsupported German number"),
        ({"noun": "Kind", "case": "nom", "number": "sg",
          "definiteness": "some"}, "unsupported German definiteness"),
        ({"noun": "Kinder", "case": "nom", "number": "pl",
          "definiteness": "ein"}, "ein has no plural"),
        ({"noun": "Xyzfoo", "case": "nom", "number": "sg",
          "definiteness": "der"}, "not in gender DB"),
        ({"noun": "Kind", "case": "nom", "number": "sg",
          "definiteness": "der", "adjective": "  "},
         "adjective must not be empty"),
        ({"noun": "Farbe", "case": "nom", "number": "sg",
          "definiteness": "der", "adjective": "lila"},
         "indeclinable German adjective"),
    ],
)
def test_invalid_inputs_raise(kwargs, match):
    with pytest.raises(ValueError, match=match):
        m.decline_np(**kwargs)


def test_weak_noun_data_is_reviewable_and_complete_enough():
    path = (
        Path(m.__file__).parent / "data" / "de_weak_nouns.json"
    )
    entries = json.loads(path.read_text(encoding="utf-8"))
    assert 110 <= len(entries) <= 160
    assert len(entries) == len(set(entries))
    assert all(isinstance(noun, str) and noun[:1].isupper() for noun in entries)
    assert {
        "Asteroid", "Automat", "Bursche", "Drache", "Geselle", "Herr",
        "Herz", "Junge", "Komet", "Konkurrent", "Mensch", "Name",
        "Planet", "Student",
    } <= set(entries)
    assert "Vetter" not in entries
