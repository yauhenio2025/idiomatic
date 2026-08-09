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


def _write_gate_chunk(
    batch_dir: Path,
    chunk: str,
    source: list[dict],
    notes: list[dict],
    triage: list[dict],
) -> None:
    (batch_dir / "input").mkdir(parents=True, exist_ok=True)
    (batch_dir / "output").mkdir(parents=True, exist_ok=True)
    for directory, suffix, payload in (
        ("input", "", source),
        ("output", "_notes", notes),
        ("output", "_triage", triage),
    ):
        (batch_dir / directory / f"{chunk}{suffix}.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8",
        )


def _valid_tenses_gate_payloads() -> tuple[list[dict], list[dict], list[dict]]:
    source = [{
        "id": "it_tenses_001",
        "en": "The committee had approved the proposal before the hearing began.",
        "old_back": "El comité había aprobado la propuesta antes de que comenzara la audiencia.",
    }]
    notes = [{
        "id": "it_tenses_001",
        "en": source[0]["en"],
        "category": "past-anteriority",
        "tl": "El comité ya había aprobado la propuesta antes de que comenzara la audiencia.",
        "alts": [],
        "register": "Registro institucional neutro.",
        "trap": "El pluscuamperfecto marca la anterioridad respecto de otro hecho pasado.",
        "example_tl": (
            "Cuando la comisión publicó el informe definitivo, los investigadores ya "
            "habían verificado cuidadosamente todos los documentos del archivo ministerial."
        ),
        "example_en": (
            "When the commission published the final report, the researchers had already "
            "carefully verified every document in the ministerial archive."
        ),
        "cloze": (
            "Cuando la comisión publicó el informe definitivo, los investigadores ya "
            "{{c1::habían}} {{c1::verificado}} cuidadosamente todos los documentos del "
            "archivo ministerial."
        ),
        "note": "Nueva situación que conserva la arquitectura de anterioridad.",
    }]
    triage = [{
        "id": "it_tenses_001",
        "en": source[0]["en"],
        "verdict": "keep",
        "reason": "",
    }]
    return source, notes, triage


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


@pytest.mark.parametrize("plan", ["wave3", "wave4", "wave5", "wave6"])
def test_plan_hashes_are_hashes_of_exact_staged_bytes(plan: str):
    manifest, files = wave.render_plan(plan)
    by_name = {path.relative_to(wave.REPO).as_posix(): data for path, data in files.items()}
    for chunk in manifest["chunks"]:
        assert hashlib.sha256(by_name[chunk["path"]]).hexdigest() == chunk["sha256"]


def test_wave4_stages_all_582_fancy_vocab_prompts_in_forty_row_chunks():
    manifest, files = wave.render_plan("wave4")
    assert manifest["schema_version"] == 2
    assert manifest["chunk_size"] == 40
    assert manifest["format_verdict"].endswith(
        "'this looks good to me too - all three formats'"
    )
    assert len(manifest["chunks"]) == 75
    for lang in wave.LANGS:
        rows = []
        for number in range(1, 16):
            rows.extend(_staged_json(files, f"{lang}_fancy_vocab_b{number:02d}.json"))
        assert [row["id"] for row in rows] == [
            f"it_fancy_vocab_{number:03d}" for number in range(1, 583)
        ]
        assert all(set(row) == {"id", "en", "old_back"} for row in rows)
        sizes = [chunk["rows"] for chunk in manifest["chunks"] if chunk["lang"] == lang]
        assert sizes == [40] * 14 + [22]
    assert _staged_json(files, "it_fancy_vocab_b01.json")[0]["old_back"]
    pt_missing = [
        item
        for chunk in manifest["chunks"]
        if chunk["lang"] == "pt"
        for item in chunk["missing_ref_ids"]
    ]
    assert pt_missing == ["it_fancy_vocab_312", "it_fancy_vocab_484"]


def test_wave4_flags_exactly_the_committed_nonpreferred_duplicate_copies():
    manifest, _files = wave.render_plan("wave4")
    (topic,) = manifest["topics"]
    assert topic["format_verdict"] == "owner-approved 2026-08-09"
    assert topic["expected_duplicate_drops"] == 20
    for lang in wave.LANGS:
        flagged = [
            item
            for chunk in manifest["chunks"]
            if chunk["lang"] == lang
            for item in chunk["expected_duplicate_drop_ids"]
        ]
        assert len(flagged) == 20
        # The two the V1 pilot already adjudicated, plus the CONNECTING-owned one.
        assert {
            "it_fancy_vocab_098", "it_fancy_vocab_099", "it_fancy_vocab_407",
        } <= set(flagged)


def test_wave5_stages_the_specialist_trio_at_517_prompts_per_language():
    manifest, _files = wave.render_plan("wave5")
    assert [topic["topic"] for topic in manifest["topics"]] == [
        "big_tech_vocab", "cold_war_vocab", "geopolitics",
    ]
    assert [topic["source_rows"] for topic in manifest["topics"]] == [145, 222, 150]
    assert all(topic["expected_duplicate_drops"] == 0 for topic in manifest["topics"])
    assert len(manifest["chunks"]) == 70
    for lang in wave.LANGS:
        sizes = [chunk["rows"] for chunk in manifest["chunks"] if chunk["lang"] == lang]
        assert sizes == [40, 40, 40, 25] + [40] * 5 + [22] + [40, 40, 40, 30]
        assert sum(sizes) == 517
    assert all(
        chunk["expected_duplicate_drop_ids"] == [] for chunk in manifest["chunks"]
    )
    pt_missing = [
        item
        for chunk in manifest["chunks"]
        if chunk["lang"] == "pt"
        for item in chunk["missing_ref_ids"]
    ]
    assert pt_missing == ["it_big_tech_vocab_052"]


def test_wave6_stages_90_shadowing_frames_with_the_pt_pilot_prefix_skipped():
    manifest, files = wave.render_plan("wave6")
    assert len(manifest["chunks"]) == 15
    for lang in ("de", "es", "fr", "it"):
        sizes = [chunk["rows"] for chunk in manifest["chunks"] if chunk["lang"] == lang]
        assert sizes == [40, 40, 10]
        rows = []
        for number in range(1, 4):
            rows.extend(_staged_json(files, f"{lang}_big_tech_phrases_b{number:02d}.json"))
        assert [row["id"] for row in rows] == [
            f"it_big_tech_phrases_{number:03d}" for number in range(1, 91)
        ]
    # The approved 30-row PT pilot owns rows 1-30: bulk staging skips them
    # but keeps the canonical 40-row grid, so b02/b03 stay aligned with the
    # already-authored chunks and b01 is the rows 31-40 tail.
    pt_sizes = [chunk["rows"] for chunk in manifest["chunks"] if chunk["lang"] == "pt"]
    assert pt_sizes == [10, 40, 10]
    pt_rows = []
    for number in range(1, 4):
        pt_rows.extend(_staged_json(files, f"pt_big_tech_phrases_b{number:02d}.json"))
    assert [row["id"] for row in pt_rows] == [
        f"it_big_tech_phrases_{number:03d}" for number in range(31, 91)
    ]
    assert all(row["old_back"].strip() for row in pt_rows)
    pt_topic = next(
        topic for topic in manifest["topics"] if topic["languages"] == ["pt"]
    )
    assert pt_topic["pilot_prefix_rows"] == 30
    assert pt_topic["pilot_prefix_chunk"] == "pt_big_tech_phrases_pilot_b01"
    assert pt_topic["staged_rows"] == 60
    assert all(
        chunk["expected_duplicate_drop_ids"] == [] for chunk in manifest["chunks"]
    )


def _valid_shadowing_chunk_payloads() -> tuple[list[dict], list[dict], list[dict]]:
    source = [{
        "id": "it_big_tech_phrases_031",
        "en": "In alignment with consumer demand, tech giants are moving into AR commerce.",
        "old_back": "Em sintonia com a demanda dos consumidores, as gigantes avançam no comércio de RA.",
    }]
    notes = [{
        "id": "it_big_tech_phrases_031",
        "en": source[0]["en"],
        "category": "context-frame",
        "tl": (
            "Em sintonia com a demanda dos consumidores, os gigantes da tecnologia "
            "estão avançando no comércio baseado em realidade aumentada."
        ),
        "focus_tl": "Em sintonia com a demanda dos consumidores",
        "focus_en": "in alignment with",
        "register": "Registro empresarial neutro.",
        "trap": "Não decalcar o espanhol en sintonía con.",
        "note": "",
    }]
    triage = [{
        "id": "it_big_tech_phrases_031",
        "en": source[0]["en"],
        "verdict": "keep",
        "reason": "",
    }]
    return source, notes, triage


def test_merge_lane_validates_shadowing_chunks_under_the_p1_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    batch_dir = tmp_path / "batches"
    chunk = "pt_big_tech_phrases_b01"
    source, notes, triage = _valid_shadowing_chunk_payloads()
    _write_gate_chunk(batch_dir, chunk, source, notes, triage)
    monkeypatch.setattr(wave, "BATCH_DIR", batch_dir)

    verified = wave._verified_chunk_notes(chunk)

    assert [row["id"] for row in verified] == ["it_big_tech_phrases_031"]


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("v1-category", "unknown category"),
        ("focus-outside-tl", "focus_tl must occur in tl"),
        ("v1-note-shape", "shadowing keys mismatch"),
        ("non-string-note", "note must be a string"),
    ],
)
def test_merge_lane_rejects_shadowing_contract_violations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str, expected: str,
):
    batch_dir = tmp_path / "batches"
    chunk = "pt_big_tech_phrases_b01"
    source, notes, triage = _valid_shadowing_chunk_payloads()
    if case == "v1-category":
        # Valid for CONNECTING, forbidden under the shadowing contract.
        notes[0]["category"] = "result"
    elif case == "focus-outside-tl":
        notes[0]["focus_tl"] = "Fora da frase autorizada"
    elif case == "v1-note-shape":
        notes[0].pop("focus_tl")
        notes[0]["cloze"] = "{{c1::Em sintonia}} com a demanda."
    elif case == "non-string-note":
        notes[0]["note"] = 7
    _write_gate_chunk(batch_dir, chunk, source, notes, triage)
    monkeypatch.setattr(wave, "BATCH_DIR", batch_dir)

    with pytest.raises(wave.PipelineError, match=expected):
        wave._verified_chunk_notes(chunk)


def test_v1_topics_still_reject_shadowing_categories_at_merge():
    _source, notes, _triage = _valid_tenses_gate_payloads()
    notes[0]["category"] = "context-frame"
    with pytest.raises(wave.x2.Ex2SourceError, match="unknown category"):
        wave._validate_notes("es_tenses", "es", "tenses", notes)


def test_pt_big_tech_phrases_merge_is_blocked_until_the_gap_chunk_lands():
    # Rows 31-40 are staged as pt b01 but not yet authored; the composed
    # pilot-prefix merge must refuse rather than land an 80-note corpus.
    with pytest.raises(
        wave.PipelineError,
        match="pt_big_tech_phrases_b01: awaiting authored outputs",
    ):
        wave.expected_merged_notes("pt", "big_tech_phrases")


def test_pilot_prefix_composition_rejects_out_of_order_ids():
    rows = [{"id": "it_big_tech_phrases_041"}, {"id": "it_big_tech_phrases_001"}]
    with pytest.raises(wave.PipelineError, match="canonical source order"):
        wave._require_canonical_order("pt", "big_tech_phrases", rows)


def test_legacy_plans_still_render_schema_one_without_bulk_annotations():
    for plan in ("wave3", "vocab-pilot", "geopolitics-pilot", "phrases-pilot"):
        manifest, _files = wave.render_plan(plan)
        assert manifest["schema_version"] == 1
        assert manifest["chunk_size"] == 100
        assert "format_verdict" not in manifest
        assert "duplicate_policy" not in manifest
        assert all(
            "expected_duplicate_drop_ids" not in chunk
            for chunk in manifest["chunks"]
        )
        assert all(
            "format_verdict" not in topic and "expected_duplicate_drops" not in topic
            for topic in manifest["topics"]
        )


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


def test_tenses_gate_accepts_the_exact_approved_contract(tmp_path: Path):
    batch_dir = tmp_path / "batches"
    chunk = "es_tenses_b01"
    source, notes, triage = _valid_tenses_gate_payloads()
    _write_gate_chunk(batch_dir, chunk, source, notes, triage)

    ok, problems, stats = gate.gate_chunk(chunk, batch_dir=batch_dir)

    assert ok, problems
    assert stats == {
        "chunk": chunk,
        "inputs": 1,
        "keep": 1,
        "drop": 0,
        "notes_parsed": 1,
        "with_trap": 1,
        "same_as_legacy": 0,
    }


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("input-extra-key", "Tenses input[0] keys mismatch"),
        ("input-wrong-scalar", "Tenses input[0].old_back must be a string"),
        ("triage-missing-key", "Tenses triage[0] keys mismatch"),
        ("note-extra-key", "Tenses notes[0] keys mismatch"),
        ("note-wrong-list", "Tenses notes[0].alts must be a list of strings"),
        ("note-wrong-scalar", "Tenses notes[0].note must be a string"),
    ],
)
def test_tenses_gate_requires_exact_keys_and_types(
    tmp_path: Path, case: str, expected: str,
):
    batch_dir = tmp_path / "batches"
    chunk = "es_tenses_b01"
    source, notes, triage = _valid_tenses_gate_payloads()
    if case == "input-extra-key":
        source[0]["refs"] = {}
    elif case == "input-wrong-scalar":
        source[0]["old_back"] = []
    elif case == "triage-missing-key":
        triage[0].pop("reason")
    elif case == "note-extra-key":
        notes[0]["focus_tl"] = "habían verificado"
    elif case == "note-wrong-list":
        notes[0]["alts"] = "ninguna"
    elif case == "note-wrong-scalar":
        notes[0]["note"] = 7
    _write_gate_chunk(batch_dir, chunk, source, notes, triage)

    ok, problems, _stats = gate.gate_chunk(chunk, batch_dir=batch_dir)

    assert not ok
    assert any(expected in problem for problem in problems), problems


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("invalid-verdict", "invalid verdicts"),
        ("blank-drop-reason", "drop reasons must be nonempty"),
        ("multiline-drop-reason", "drop reasons must be single-line"),
        ("non-tenses-category", "invalid Tenses categories"),
    ],
)
def test_tenses_gate_enforces_verdict_reason_and_category_allowlists(
    tmp_path: Path, case: str, expected: str,
):
    batch_dir = tmp_path / "batches"
    chunk = "es_tenses_b01"
    source, notes, triage = _valid_tenses_gate_payloads()
    if case == "invalid-verdict":
        triage[0]["verdict"] = "revise"
    elif case in {"blank-drop-reason", "multiline-drop-reason"}:
        triage[0]["verdict"] = "drop"
        triage[0]["reason"] = "" if case == "blank-drop-reason" else "Broken\nDuplicate"
        notes = []
    elif case == "non-tenses-category":
        # Globally valid for CONNECTING, but forbidden in a Wave 3 chunk.
        notes[0]["category"] = "result"
    _write_gate_chunk(batch_dir, chunk, source, notes, triage)

    ok, problems, _stats = gate.gate_chunk(chunk, batch_dir=batch_dir)

    assert not ok
    assert any(expected in problem for problem in problems), problems


def test_tenses_gate_rejects_exact_duplicate_examples_inside_chunk(tmp_path: Path):
    batch_dir = tmp_path / "batches"
    chunk = "es_tenses_b01"
    source, notes, triage = _valid_tenses_gate_payloads()
    second_source = {
        "id": "it_tenses_002",
        "en": "The researchers had checked the archive before the report appeared.",
        "old_back": "Los investigadores habían revisado el archivo antes del informe.",
    }
    second_note = copy.deepcopy(notes[0])
    second_note.update({
        "id": second_source["id"],
        "en": second_source["en"],
        "tl": "Los investigadores ya habían revisado el archivo antes de publicarse el informe.",
    })
    second_triage = {
        "id": second_source["id"],
        "en": second_source["en"],
        "verdict": "keep",
        "reason": "",
    }
    source.append(second_source)
    notes.append(second_note)
    triage.append(second_triage)
    _write_gate_chunk(batch_dir, chunk, source, notes, triage)

    ok, problems, _stats = gate.gate_chunk(chunk, batch_dir=batch_dir)

    assert not ok
    assert any("exact duplicate Tenses examples" in problem for problem in problems)


def test_tenses_gate_rejects_example_already_present_in_merged_notes(tmp_path: Path):
    batch_dir = tmp_path / "batches"
    chunk = "es_tenses_b01"
    source, notes, triage = _valid_tenses_gate_payloads()
    _write_gate_chunk(batch_dir, chunk, source, notes, triage)
    merged_dir = batch_dir.parent / "notes"
    merged_dir.mkdir()
    (merged_dir / "es_conditionals.json").write_text(
        json.dumps([{
            "id": "esd999",
            "en": "A different production prompt.",
            "tl": "Una respuesta diferente.",
            "example_tl": notes[0]["example_tl"],
            "example_en": notes[0]["example_en"],
        }], ensure_ascii=False),
        encoding="utf-8",
    )

    ok, problems, _stats = gate.gate_chunk(chunk, batch_dir=batch_dir)

    assert not ok
    assert any("exact duplicate Tenses examples" in problem for problem in problems)


def test_tenses_only_rules_do_not_reject_wave4_lexical_categories(
    tmp_path: Path,
):
    batch_dir = tmp_path / "batches"
    chunk = "es_fancy_vocab_pilot_b01"
    source, notes, triage = _valid_tenses_gate_payloads()
    notes[0]["category"] = "lexical-expression"
    _write_gate_chunk(batch_dir, chunk, source, notes, triage)

    ok, problems, _stats = gate.gate_chunk(chunk, batch_dir=batch_dir)

    assert ok, problems


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
    for lang in ("de", "es", "fr", "it"):
        assert results[f"{lang}_big_tech_phrases"] == 90
    # 4022 (through geopolitics) + 360 big_tech_phrases; pt lands its 80+10
    # notes only after the staged rows 31-40 gap chunk (pt b01) is authored,
    # which will take this to 4472.
    assert wave.check_merged_duplicates() == 4382
