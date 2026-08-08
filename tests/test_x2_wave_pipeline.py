"""Deterministic tests for Exercises 2.0 Wave 3--6 staging/audit tools."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools import x2_batch_gate as gate
from tools import x2_wave_pipeline as wave


def _staged_json(files: dict, suffix: str) -> list[dict]:
    path = next(path for path in files if path.name == suffix)
    return json.loads(files[path])


def test_wave3_plan_is_five_languages_three_chunks_of_100_with_source_ids():
    manifest, files = wave.render_plan("wave3")
    assert len(manifest["chunks"]) == 15
    assert {chunk["rows"] for chunk in manifest["chunks"]} == {100}
    assert len(manifest["source_files"]) == 6
    assert all(len(chunk["sha256"]) == 64 for chunk in manifest["chunks"])

    for lang in wave.LANGS:
        rows = []
        for number in range(1, 4):
            rows.extend(_staged_json(files, f"{lang}_tenses_b{number:02d}.json"))
        assert [row["id"] for row in rows] == [
            f"it_tenses_{number:03d}" for number in range(1, 301)
        ]
        assert all(set(row) == {"id", "en", "old_back"} for row in rows)
    assert _staged_json(files, "es_tenses_b01.json")[0]["old_back"] == ""
    assert _staged_json(files, "it_tenses_b01.json")[0]["old_back"]


def test_plan_hashes_are_hashes_of_exact_staged_bytes():
    manifest, files = wave.render_plan("wave3")
    by_name = {path.relative_to(wave.REPO).as_posix(): data for path, data in files.items()}
    for chunk in manifest["chunks"]:
        assert hashlib.sha256(by_name[chunk["path"]]).hexdigest() == chunk["sha256"]


def test_only_bounded_representative_pilots_are_commissioned():
    vocab, vocab_files = wave.render_plan("vocab-pilot")
    geopolitics, geo_files = wave.render_plan("geopolitics-pilot")
    phrases, phrase_files = wave.render_plan("phrases-pilot")
    assert [chunk["rows"] for chunk in vocab["chunks"]] == [30]
    assert [chunk["rows"] for chunk in geopolitics["chunks"]] == [30]
    assert [chunk["rows"] for chunk in phrases["chunks"]] == [30]
    assert all(topic["owner_gate"] for manifest in (vocab, geopolitics, phrases)
               for topic in manifest["topics"])
    assert len(_staged_json(vocab_files, "es_fancy_vocab_pilot_b01.json")) == 30
    assert len(_staged_json(geo_files, "es_geopolitics_pilot_b01.json")) == 30
    pt_rows = _staged_json(phrase_files, "pt_big_tech_phrases_pilot_b01.json")
    assert len(pt_rows) == 30
    assert all(row["old_back"] == "" for row in pt_rows)


def test_missing_ref_allowlist_is_exact_not_a_blanket_exception():
    rows, _italian, _paths = wave.load_topic("tenses")
    broken = copy.deepcopy(rows)
    broken[1]["refs"].pop("fr")
    with pytest.raises(wave.PipelineError, match="allowlist drift"):
        wave.validate_missing_refs("tenses", broken)

    unexpectedly_filled = copy.deepcopy(rows)
    unexpectedly_filled[0]["refs"]["es"] = "rellenado"
    with pytest.raises(wave.PipelineError, match="no-longer-missing"):
        wave.validate_missing_refs("tenses", unexpectedly_filled)


def test_cross_topic_exact_duplicate_report_is_deterministic_and_adjudicated():
    report = wave.render_duplicate_report()
    assert report["group_count"] == 20
    clarify = next(group for group in report["groups"] if group["en"] == "To clarify")
    assert clarify["preferred_topic"] == "connecting"
    assert {row["topic"] for row in clarify["occurrences"]} == {
        "connecting", "fancy_vocab",
    }


@pytest.mark.parametrize(
    ("chunk", "expected"),
    [
        ("es_big_tech_vocab_b02", ("es", "big_tech_vocab")),
        ("pt_big_tech_phrases_pilot_b01", ("pt", "big_tech_phrases")),
        ("de_tenses_b03", ("de", "tenses")),
    ],
)
def test_multiword_chunk_parsing(chunk: str, expected: tuple[str, str]):
    assert gate._chunk_lang_topic(chunk) == expected
    lang, topic, _pilot, _number = wave.parse_chunk_name(chunk)
    assert (lang, topic) == expected


@pytest.mark.parametrize(
    ("text", "lang"),
    [
        (
            "Si les enseignements de la guerre froide sont intégrés à la "
            "réflexion géopolitique contemporaine, la diplomatie reposera "
            "davantage sur la coopération.",
            "fr",
        ),
        (
            "Se la dottoranda dedica la tesi alla propaganda digitale durante "
            "la guerra fredda, avrà bisogno di numerose fonti archivistiche inedite.",
            "it",
        ),
        (
            "In ultima analisi, la credibilità dell'alleanza dipenderà dalla "
            "disponibilità dei governi a condividere tecnologie sensibili.",
            "it",
        ),
        (
            "In definitiva, la sovranità tecnologica europea sarà credibile "
            "soltanto se produrrà capacità condivise.",
            "it",
        ),
    ],
)
def test_four_adjudicated_language_gate_false_positives(text: str, lang: str):
    assert gate._wrong_language(text, lang) is None


def test_language_gate_still_catches_strong_spanish_in_portuguese_output():
    text = "Las plataformas no protegen los datos; la regulación sigue pendiente."
    assert gate._wrong_language(text, "pt") == "es"


def test_shadowing_pilot_uses_its_separate_gate_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    batch_dir = tmp_path / "batches"
    (batch_dir / "input").mkdir(parents=True)
    (batch_dir / "output").mkdir()
    chunk = "pt_big_tech_phrases_pilot_b01"
    source = [{"id": "it_big_tech_phrases_001", "en": "In light of this", "old_back": ""}]
    notes = [{
        "id": "it_big_tech_phrases_001",
        "en": "In light of this",
        "category": "context-frame",
        "tl": "À luz desses fatos, a comissão reavaliará a proposta.",
        "focus_tl": "À luz desses fatos",
        "focus_en": "in light of",
        "register": "Formal institutional framing.",
        "trap": "Do not calque Spanish a la luz de.",
        "note": "",
    }]
    triage = [{
        "id": "it_big_tech_phrases_001",
        "en": "In light of this",
        "verdict": "keep",
        "reason": "",
    }]
    for directory, suffix, payload in (
        ("input", "", source),
        ("output", "_notes", notes),
        ("output", "_triage", triage),
    ):
        (batch_dir / directory / f"{chunk}{suffix}.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8",
        )
    monkeypatch.setattr(gate, "BATCH_DIR", batch_dir)
    ok, problems, stats = gate.gate_chunk(chunk)
    assert ok, problems
    assert stats["notes_parsed"] == 1


def test_existing_merges_match_their_keep_triage_and_have_no_cross_topic_copies():
    results = wave.verify_all_merges()
    assert results["fr_connecting"] == 191
    assert results["es_conditionals"] == 168
    assert wave.check_merged_duplicates() == 1772
