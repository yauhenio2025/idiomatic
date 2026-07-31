"""F3 personal-error cards: deterministic tests with no network or DB."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sqlite3
import zipfile

import pytest

from idiomatic.grammar import f3 as f3_module
from idiomatic.grammar.apkg import build_grammar_apkg
from idiomatic.grammar.audio import full_sentence_text
from idiomatic.grammar.curriculum import topic_by_key, topics_for, unit_seed_rows
from idiomatic.grammar.f3 import (
    candidate_to_item,
    choose_candidates,
    is_suitable_pair,
)


# Literal values on purpose: changing the production constants and the model
# together must not make this frozen-model regression test pass.
_FROZEN_MODEL_ID = 1_820_130_001
_FROZEN_MODEL_NAME = "Idiomatic Grammar Drill v1"
_FROZEN_FIELDS = [
    "ItemId",
    "Lang",
    "Topic",
    "TenseLabel",
    "Symbol",
    "Sentence",
    "Answer",
    "SentenceFull",
    "GlossEn",
    "Why",
    "Extra1",
    "Extra2",
    "Extra3",
    "Extra4",
]

_F3_TOPICS = {
    "fr": ("fr_mes_erreurs", "9 Mes erreurs", "Corrige : ce que j'ai dit"),
    "pt": ("pt_meus_erros", "9 Meus erros", "Corrija: o que eu disse"),
    "es": ("es_mis_errores", "9 Mis errores", "Corrige: lo que dije"),
    "it": ("it_miei_errori", "9 I miei errori", "Correggi: quello che ho detto"),
    "de": ("de_meine_fehler", "9 Meine Fehler", "Korrigiere: was ich gesagt habe"),
}


def _candidate(**overrides):
    row = {
        "id": 11,
        "lang": "fr",
        "kind": "error",
        "wrong": "en Berlin",
        "right_form": "à Berlin",
        "gloss_en": None,
        "category": "prep_place",
        "why": "Cities take à; en is for countries.",
        "occurrences": 3,
        "last_seen": date(2024, 3, 1),
        "confidence": "high",
        "status": "active",
        "f3_item_id": None,
    }
    row.update(overrides)
    return row


@pytest.mark.parametrize(
    ("wrong", "right", "expected"),
    [
        ("J'habite en Berlin.", "J'habite à Berlin.", True),
        ("insérir", "insérer", True),
        ("[cercare a → cercare di]", "cercare di", False),
        ("aussprechen (z)", "aussprechen", False),
        ("mot (explication complète)", "mot juste (explication complète)", True),
        ("same phrase", "same phrase", False),
        ("", "à Berlin", False),
        (None, "à Berlin", False),
        ("en Berlin", None, False),
    ],
)
def test_suitability_accepts_real_pairs_and_rejects_mangled_fragments(
    wrong: str | None, right: str | None, expected: bool,
):
    assert is_suitable_pair(wrong, right) is expected


def test_choose_candidates_filters_ranks_and_deduplicates_by_f3_item_id():
    rows = [
        _candidate(id=1, wrong="one old", occurrences=7,
                   last_seen=date(2023, 1, 1)),
        _candidate(id=2, wrong="one recent", occurrences=7,
                   last_seen=date(2024, 1, 1)),
        _candidate(id=3, wrong="most frequent", occurrences=9,
                   last_seen=date(2020, 1, 1)),
        _candidate(id=4, wrong="already converted", occurrences=100,
                   f3_item_id=404),
        _candidate(id=5, wrong="low confidence", occurrences=50,
                   confidence="low"),
        _candidate(id=6, wrong="retired pair", occurrences=50,
                   status="retired"),
        _candidate(id=7, wrong="vocabulary gap", occurrences=50,
                   kind="vocab_gap"),
        _candidate(id=8, wrong="[mangled correction]", occurrences=50),
    ]

    assert [row["id"] for row in choose_candidates(rows, 10)] == [3, 2, 1]
    assert [row["id"] for row in choose_candidates(rows, 2)] == [3, 2]

    # Simulate successful conversion writing the grammar item id back. A
    # rerun must not offer any of those personal errors again.
    for row in rows:
        if row["id"] in (1, 2, 3):
            row["f3_item_id"] = 1_000 + row["id"]
    assert choose_candidates(rows, 10) == []


def test_candidate_mapping_uses_frozen_model_semantics():
    item = candidate_to_item(_candidate())
    assert item["fmt"] == "f3"
    assert item["lang"] == "fr"
    assert item["topic"] == "fr_mes_erreurs"
    assert item["sentence"] == "en Berlin"
    assert item["answer"] == "à Berlin"
    assert item["gloss_en"] == "prep_place"
    assert item["why_en"] == "Cities take à; en is for countries."

    with_gloss = candidate_to_item(_candidate(gloss_en="in Berlin"))
    assert with_gloss["gloss_en"] == "in Berlin"


@pytest.mark.asyncio
async def test_convert_counts_collisions_and_keeps_scanning(monkeypatch):
    rows = [
        _candidate(id=1, wrong="highest collision", occurrences=9,
                   sentence_collision=True),
        _candidate(id=2, wrong="first insert", occurrences=8),
        _candidate(id=3, wrong="racing collision", occurrences=7),
    ]

    async def fetch_candidates(lang: str):
        assert lang == "fr"
        return rows

    async def insert_item(personal_error_id: int, item: dict, *, batch: str):
        assert item["fmt"] == "f3"
        assert batch.startswith("f3-")
        return 902 if personal_error_id == 2 else None

    monkeypatch.setattr(f3_module.db, "fetch_f3_candidates", fetch_candidates)
    monkeypatch.setattr(f3_module.db, "insert_f3_grammar_item", insert_item)

    result = await f3_module.convert("fr", 2)

    assert result == {
        "converted": 1,
        "skipped": 2,
        "examples": [{"wrong": "first insert", "right": "à Berlin"}],
    }


def test_f3_topics_are_appended_attested_units():
    seed_rows = {row["key"]: row for row in unit_seed_rows()}

    for lang, (key, cluster, label) in _F3_TOPICS.items():
        topic = topic_by_key(key)
        assert topic is not None
        expected_index = -1 if lang == "de" else -2
        assert topics_for(lang)[expected_index] == topic
        assert (topic.lang, topic.key, topic.cluster) == (lang, key, cluster)
        assert topic.label == label
        assert topic.symbol == "⚠"
        assert topic.mood == topic.tense == ""
        assert topic.verify == "attested"
        assert topic.verbs == []

        seed = seed_rows[key]
        assert seed["lang"] == lang
        assert seed["cluster"] == cluster
        assert seed["label"] == label
        assert seed["symbol"] == "⚠"
        assert seed["status"] == "active"


def _render_plain(template: str, fields: dict[str, str]) -> str:
    """Substitute ordinary model fields; conditionals are irrelevant here."""
    for name, value in fields.items():
        template = template.replace("{{" + name + "}}", value)
    return template


def test_f3_apkg_keeps_frozen_model_and_renders_correction(tmp_path: Path):
    item = {**candidate_to_item(_candidate()), "id": 901}
    topic = topic_by_key(item["topic"])
    assert topic is not None
    out = tmp_path / "f3.apkg"

    count = build_grammar_apkg(
        out_path=out,
        lang="fr",
        items=[item],
        topic_labels={topic.key: (topic.label, topic.symbol)},
        topic_clusters={topic.key: topic.cluster},
    )
    assert count == 1

    unpacked = tmp_path / "unpacked"
    with zipfile.ZipFile(out) as package:
        package.extract("collection.anki2", unpacked)
    with sqlite3.connect(unpacked / "collection.anki2") as con:
        field_blob = con.execute("SELECT flds FROM notes").fetchone()[0]
        models = json.loads(con.execute("SELECT models FROM col").fetchone()[0])

    assert set(models) == {str(_FROZEN_MODEL_ID)}
    model = models[str(_FROZEN_MODEL_ID)]
    assert int(model["id"]) == _FROZEN_MODEL_ID
    assert model["name"] == _FROZEN_MODEL_NAME
    assert [field["name"] for field in model["flds"]] == _FROZEN_FIELDS
    assert len(model["tmpls"]) == 1

    values = field_blob.split("\x1f")
    assert len(values) == 14
    fields = dict(zip(_FROZEN_FIELDS, values, strict=True))
    assert fields["ItemId"] == "901"
    assert fields["Lang"] == "fr"
    assert fields["Topic"] == "fr_mes_erreurs"
    assert fields["TenseLabel"] == "Corrige : ce que j'ai dit"
    assert fields["Symbol"] == "⚠"
    assert fields["Sentence"] == "en Berlin"
    assert fields["Answer"] == "à Berlin"
    assert fields["SentenceFull"] == "à Berlin"
    assert "en Berlin" not in fields["SentenceFull"]
    assert fields["GlossEn"] == "prep_place"
    assert fields["Why"] == "Cities take à; en is for countries."

    template = model["tmpls"][0]
    assert "{{Sentence}}" in template["qfmt"]
    assert "{{Answer}}" not in template["qfmt"]
    assert "{{Answer}}" in template["afmt"]
    assert "{{SentenceFull}}" in template["afmt"]
    front = _render_plain(template["qfmt"], fields)
    back = _render_plain(template["afmt"], fields)
    assert "⚠" in front
    assert "en Berlin" in front
    assert "à Berlin" not in front
    assert "à Berlin" in back
    assert "Cities take à; en is for countries." in back


def test_f3_audio_uses_the_corrected_sentence():
    assert full_sentence_text("en Berlin", "à Berlin", "", fmt="f3") == "à Berlin"
