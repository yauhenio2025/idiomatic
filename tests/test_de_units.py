"""German adjective-ending and process-passive unit integration tests."""

import asyncio

import pytest

from idiomatic.grammar.curriculum import (
    OBSOLETE_UNIT_KEYS,
    PLANNED_UNITS,
    topic_by_key,
    topics_for,
    unit_seed_rows,
)
from idiomatic.grammar import generate as gen


def _adj_item(**overrides):
    item = {
        "sentence": (
            "Die Beobachter erwarten, dass ___ (härtest) Konkurrent "
            "schon morgen reagiert."
        ),
        "noun": "Konkurrent",
        "case": "nom",
        "number": "sg",
        "definiteness": "definite",
        "adjective": "härtest",
        "target": "article_adjective",
        "answer": "der härteste",
        "gloss_en": "Observers expect the toughest competitor to react tomorrow.",
        "why": "A definite masculine nominative phrase takes the weak -e ending.",
    }
    item.update(overrides)
    return item


def _passive_item(**overrides):
    item = {
        "sentence": (
            "Die Redaktion bestätigt, dass der Bericht morgen "
            "___ (veröffentlichen)."
        ),
        "infinitive": "veröffentlichen",
        "participle": "veröffentlicht",
        "person": "3s",
        "tense": "present",
        "modal": None,
        "answer": "veröffentlicht wird",
        "gloss_en": "The editors confirm that the report will be published tomorrow.",
        "why": "Present process passive in a subordinate clause.",
    }
    item.update(overrides)
    return item


def test_de_units_are_active_ordered_and_not_planned():
    de_topics = topics_for("de")
    keys = [topic.key for topic in de_topics]
    assert keys == [
        "de_gender",
        "de_prep_fest",
        "de_prep_wechsel",
        "de_adj_endings",
        "de_passiv",
        "de_dativ_verben",
        "de_meine_fehler",
    ]

    adjective = topic_by_key("de_adj_endings")
    passive = topic_by_key("de_passiv")
    assert (adjective.cluster, adjective.symbol, adjective.verify) == (
        "3 Adjektive", "🖌", "de_np",
    )
    assert (passive.cluster, passive.symbol, passive.verify) == (
        "4 Verben", "⚙", "de_passiv",
    )
    assert topic_by_key("de_verb_core") is None

    planned = {row["key"] for row in PLANNED_UNITS}
    assert "de_adj_endings" not in planned
    assert "de_verb_core" not in planned
    seeds = {row["key"]: row for row in unit_seed_rows()}
    assert seeds["de_adj_endings"]["status"] == "active"
    assert seeds["de_passiv"]["status"] == "active"
    assert seeds["de_adj_endings"]["sort_order"] == 3
    assert seeds["de_passiv"]["sort_order"] == 4
    assert "de_verb_core" not in seeds
    assert OBSOLETE_UNIT_KEYS == ("de_verb_core",)


def test_de_unit_prompts_declare_the_deterministic_schemas():
    adjective_prompt = gen.build_prompt(topic_by_key("de_adj_endings"), 6)
    for field in (
        "noun", "case", "number", "definiteness", "adjective", "target",
    ):
        assert f'"{field}"' in adjective_prompt
    assert "article_adjective | adjective" in adjective_prompt
    assert "definite | indefinite | none | kein | mein" in adjective_prompt
    assert "F5 landmark paradigm-card" in adjective_prompt
    assert "Schlüsse" in adjective_prompt
    for pattern in ("weak", "mixed", "strong"):
        assert pattern in adjective_prompt

    passive_prompt = gen.build_prompt(topic_by_key("de_passiv"), 4)
    for field in ("infinitive", "participle", "person", "tense", "modal"):
        assert f'"{field}"' in passive_prompt
    for answer in (
        "veröffentlicht wird",
        "veröffentlicht wurde",
        "veröffentlicht worden ist",
        "veröffentlicht werden muss",
    ):
        assert answer in passive_prompt
    assert "NEVER \"geworden\"" in passive_prompt


@pytest.mark.parametrize(
    "item",
    [
        _adj_item(),
        _adj_item(
            sentence=(
                "Die Beobachter erwarten, dass der ___ (härtest) Konkurrent "
                "schon morgen reagiert."
            ),
            target="adjective",
            answer="härteste",
        ),
        _adj_item(
            sentence=(
                "Die Studie zeigt, dass die Gruppe ___ (kohärent) Weltbild "
                "entwickelt hat."
            ),
            noun="Weltbild",
            case="akk",
            definiteness="kein",
            adjective="kohärent",
            answer="kein kohärentes",
        ),
        _adj_item(
            sentence=(
                "Sie erklärt, dass ___ (ultimativ) Ziel ein Dokumentarfilm ist."
            ),
            noun="Ziel",
            definiteness="mein",
            adjective="ultimativ",
            answer="mein ultimatives",
        ),
        _adj_item(
            sentence=(
                "Die Redaktion erklärt, dass sie ___ (tiefgründig) Schlüsse "
                "gezogen hat."
            ),
            noun="Schlüsse",
            case="akk",
            number="pl",
            definiteness="none",
            adjective="tiefgründig",
            answer="tiefgründige",
        ),
    ],
)
def test_de_adjective_targets_and_attested_fossils(item):
    assert gen.verify_item(topic_by_key("de_adj_endings"), item) == (True, "")


def test_de_adjective_verifier_rejects_wrong_answer_target_and_placement():
    topic = topic_by_key("de_adj_endings")
    good = _adj_item()
    ok, reason = gen.verify_item(topic, dict(good, answer="der härtester"))
    assert not ok and "wrong noun-phrase answer" in reason
    ok, reason = gen.verify_item(topic, dict(good, target="ending"))
    assert not ok and "bad adjective target" in reason
    doubled = dict(
        good,
        sentence=(
            "Die Beobachter erwarten, dass der ___ (härtest) Konkurrent "
            "morgen reagiert."
        ),
    )
    ok, reason = gen.verify_item(topic, doubled)
    assert not ok and "visible determiner" in reason
    misplaced = dict(
        good,
        sentence="Die Beobachter erwarten, dass ___ Konkurrent morgen reagiert.",
    )
    ok, reason = gen.verify_item(topic, misplaced)
    assert not ok and "blank/hint" in reason
    two_blanks = dict(good, sentence=good["sentence"] + " ___")
    assert gen.verify_item(topic, two_blanks) == (
        False, "sentence must contain exactly one blank",
    )

    unknown_plural = _adj_item(
        sentence="Die Studie nennt ___ (neu) Qxyzzy.",
        noun="Qxyzzy", number="pl", adjective="neu",
        definiteness="none", answer="neue",
    )
    ok, reason = gen.verify_item(topic, unknown_plural)
    assert not ok and "plural noun is not in adjective bank" in reason

    compound_prefix = _adj_item(
        sentence="Der Bericht beschreibt ___ (gut) Kinderwagen.",
        noun="Kinder", number="pl", adjective="gut", answer="die guten",
    )
    ok, reason = gen.verify_item(topic, compound_prefix)
    assert not ok and "blank/hint" in reason

    wrong_hint_case = dict(
        good,
        sentence=good["sentence"].replace("(härtest)", "(Härtest)"),
    )
    ok, reason = gen.verify_item(topic, wrong_hint_case)
    assert not ok and "blank/hint" in reason

    indeclinable = _adj_item(
        sentence="Die Redaktion beschreibt ___ (lila) Farbe.",
        noun="Farbe", adjective="lila", answer="die lila",
    )
    ok, reason = gen.verify_item(topic, indeclinable)
    assert not ok and "indeclinable" in reason


@pytest.mark.parametrize(
    "item",
    [
        _passive_item(tense="Präsens"),
        _passive_item(
            sentence=(
                "Die Redaktion bestätigte, dass der Bericht gestern "
                "___ (veröffentlichen)."
            ),
            tense="Präteritum",
            answer="veröffentlicht wurde",
        ),
        _passive_item(
            sentence=(
                "Wir wissen, dass die Berichte bereits ___ (prüfen)."
            ),
            infinitive="prüfen",
            participle="geprüft",
            person="3p",
            tense="Perfekt",
            answer="geprüft worden sind",
        ),
        _passive_item(
            sentence=(
                "Die Leitung sagt, dass ihr beide sofort ___ (ersetzen)."
            ),
            infinitive="ersetzen",
            participle="ersetzt",
            person="2p",
            tense="modal+infinitive",
            modal="müssen",
            answer="ersetzt werden müsst",
        ),
    ],
)
def test_de_passive_verifier_accepts_all_four_forms_and_aliases(item):
    assert gen.verify_item(topic_by_key("de_passiv"), item) == (True, "")


def test_de_passive_verifier_rejects_bad_auxiliary_participle_and_worden():
    topic = topic_by_key("de_passiv")
    good = _passive_item()
    ok, reason = gen.verify_item(topic, dict(good, answer="veröffentlicht werden"))
    assert not ok and "wrong passive" in reason
    ok, reason = gen.verify_item(
        topic,
        dict(good, participle="geöffentlicht", answer="geöffentlicht wird"),
    )
    assert not ok and "wrong participle" in reason
    perfect = dict(
        good,
        tense="perfect",
        answer="veröffentlicht geworden ist",
    )
    ok, reason = gen.verify_item(topic, perfect)
    assert not ok and "wrong passive" in reason
    ok, reason = gen.verify_item(topic, dict(good, person="9x"))
    assert not ok and "bad person" in reason

    main_clause = dict(
        good,
        sentence="Der Bericht ___ (veröffentlichen).",
    )
    ok, reason = gen.verify_item(topic, main_clause)
    assert not ok and "subordinate clause" in reason

    person_mismatch = dict(
        good,
        sentence=(
            "Die Redaktion bestätigt, dass ich morgen "
            "___ (veröffentlichen)."
        ),
    )
    ok, reason = gen.verify_item(topic, person_mismatch)
    assert not ok and "subject pronoun" in reason

    wrong_hint_case = dict(
        good,
        infinitive="Veröffentlichen",
        sentence=good["sentence"].replace(
            "(veröffentlichen)", "(Veröffentlichen)"
        ),
    )
    ok, reason = gen.verify_item(topic, wrong_hint_case)
    assert not ok and "lowercase citation" in reason

    off_inventory = _passive_item(
        sentence=(
            "Die Leitung bestätigt, dass das Haus morgen ___ (bauen)."
        ),
        infinitive="bauen", participle="gebaut", answer="gebaut wird",
    )
    ok, reason = gen.verify_item(topic, off_inventory)
    assert not ok and "outside topic inventory" in reason


def test_de_adjective_generation_persists_hint_and_metadata(monkeypatch):
    generated = _adj_item()

    async def fake_generate(_prompt, **_kwargs):
        return [generated]

    monkeypatch.setattr(gen.gemini, "generate_text", fake_generate)
    accepted, rejected = asyncio.run(
        gen.generate_batch(topic_by_key("de_adj_endings"), 1)
    )
    assert not rejected
    assert len(accepted) == 1
    assert accepted[0]["infinitive"] == "härtest"
    assert accepted[0]["meta"] == {
        key: generated[key]
        for key in (
            "noun", "case", "number", "definiteness", "adjective", "target",
        )
    }


def test_known_passive_participle_is_tier_a_without_blind_calls(monkeypatch):
    generated = _passive_item()
    calls = []

    async def fake_generate(prompt, **_kwargs):
        calls.append(prompt)
        return [generated]

    monkeypatch.setattr(gen.gemini, "generate_text", fake_generate)
    accepted, rejected = asyncio.run(
        gen.generate_batch(topic_by_key("de_passiv"), 1)
    )
    assert not rejected
    assert len(accepted) == 1
    assert len(calls) == 1
    item = accepted[0]
    assert (item["infinitive"], item["person"], item["tense"]) == (
        "veröffentlichen", "3s", "present",
    )
    assert item["meta"] == {
        key: generated[key]
        for key in ("infinitive", "participle", "person", "tense", "modal")
    }


def test_unknown_passive_participle_alone_uses_k3_fallback(monkeypatch):
    generated = _passive_item(
        sentence=(
            "Das Archiv bestätigt, dass der Vertrag morgen "
            "___ (archivieren)."
        ),
        infinitive="archivieren",
        participle="archiviert",
        answer="archiviert wird",
    )
    calls = []

    async def fake_generate(prompt, **_kwargs):
        calls.append(prompt)
        if "Produce 1 items" in prompt:
            return [generated]
        return {"answer": "archiviert wird"}

    monkeypatch.setattr(gen.gemini, "generate_text", fake_generate)
    accepted, rejected = asyncio.run(
        gen.generate_batch(topic_by_key("de_passiv"), 1)
    )
    assert not rejected
    assert len(accepted) == 1
    assert len(calls) == 1 + gen.BLIND_K


def test_unknown_passive_participle_is_rejected_on_blind_disagreement(monkeypatch):
    generated = _passive_item(
        sentence=(
            "Das Archiv bestätigt, dass der Vertrag morgen "
            "___ (archivieren)."
        ),
        infinitive="archivieren",
        participle="archiviert",
        answer="archiviert wird",
    )

    async def fake_generate(prompt, **_kwargs):
        if "Produce 1 items" in prompt:
            return [generated]
        return {"answer": "archiviert wurde"}

    monkeypatch.setattr(gen.gemini, "generate_text", fake_generate)
    accepted, rejected = asyncio.run(
        gen.generate_batch(topic_by_key("de_passiv"), 1)
    )
    assert not accepted
    assert len(rejected) == 1
    assert "blind disagreement" in rejected[0]["reject_reason"]


def test_malformed_new_unit_metadata_rejects_without_aborting_batch(monkeypatch):
    malformed = _adj_item(adjective=["hart"])

    async def fake_generate(_prompt, **_kwargs):
        return [malformed]

    monkeypatch.setattr(gen.gemini, "generate_text", fake_generate)
    accepted, rejected = asyncio.run(
        gen.generate_batch(topic_by_key("de_adj_endings"), 1)
    )
    assert not accepted and len(rejected) == 1
    assert "adjective must be text" in rejected[0]["reject_reason"]


def test_seed_prunes_superseded_unit_on_upgrade(monkeypatch):
    from idiomatic import db

    calls = []

    class FakeConnection:
        async def execute(self, query, *args):
            calls.append((query, args))

    class Acquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, *_exc):
            return False

    class FakePool:
        def acquire(self):
            return Acquire()

    async def fake_pool():
        return FakePool()

    monkeypatch.setattr(db, "get_pool", fake_pool)
    asyncio.run(db.seed_grammar_units([], obsolete_keys=OBSOLETE_UNIT_KEYS))
    assert len(calls) == 1
    assert "DELETE FROM grammar_units" in calls[0][0]
    assert calls[0][1] == (["de_verb_core"],)
