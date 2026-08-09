from __future__ import annotations

import json
from pathlib import Path

import pytest

from idiomatic.grammar import exercises2 as x2
from idiomatic.grammar import exercises2_shadowing as shadow


def _write(path: Path, **overrides) -> Path:
    row = {
        "id": "it_big_tech_phrases_001",
        "en": "In light of recent breaches, platforms are revising policy.",
        "category": "context-frame",
        "tl": "À luz das violações recentes, as plataformas estão revendo a política.",
        "focus_tl": "À luz das violações recentes",
        "focus_en": "in light of",
        "register": "neutral-formal",
        "trap": "Do not calque Spanish a la luz de.",
        "note": "",
    }
    row.update(overrides)
    path.write_text(json.dumps([row], ensure_ascii=False), encoding="utf-8")
    return path


def test_shadowing_parser_accepts_isolated_pilot_shape(tmp_path: Path):
    notes = shadow.parse_notes_file(_write(tmp_path / "pt_big_tech_phrases.json"))
    assert len(notes) == 1
    assert notes[0].lang == "pt"
    assert notes[0].focus_tl in notes[0].tl


def test_shadowing_parser_requires_focus_inside_target(tmp_path: Path):
    path = _write(tmp_path / "pt_big_tech_phrases.json", focus_tl="Fora da frase")
    with pytest.raises(shadow.ShadowSourceError, match="focus_tl"):
        shadow.parse_notes_file(path)


def test_shadowing_in_memory_parser_supports_batch_gate_filename(tmp_path: Path):
    raw = json.loads(_write(tmp_path / "source.json").read_text(encoding="utf-8"))
    notes = shadow.parse_notes_data(
        raw,
        lang="pt",
        source_name="pt_big_tech_phrases_pilot_b01_notes.json",
    )
    assert len(notes) == 1
    assert notes[0].lang == "pt"


def _v1_note_dict() -> dict:
    return {
        "id": "ptc01",
        "en": "Be that as it may",
        "category": "concession",
        "tl": "Seja como for",
        "alts": [],
        "register": "written-formal",
        "trap": "",
        "example_tl": "Seja como for, a comissão não pode adiar a regulação.",
        "example_en": "Be that as it may, the commission cannot postpone regulation.",
        "cloze": "{{c1::Seja como for}}, a comissão não pode adiar a regulação.",
        "note": "",
    }


def test_v1_loader_never_ingests_merged_shadowing_notes(tmp_path: Path):
    (tmp_path / "pt_connecting.json").write_text(
        json.dumps([_v1_note_dict()], ensure_ascii=False), encoding="utf-8",
    )
    _write(tmp_path / "pt_big_tech_phrases.json")

    notes = x2.load_notes("pt", source_dir=tmp_path)

    assert [note.topic for note in notes] == ["connecting"]


def test_admin_inventory_reports_shadowing_files_via_their_own_parser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    (tmp_path / "pt_connecting.json").write_text(
        json.dumps([_v1_note_dict()], ensure_ascii=False), encoding="utf-8",
    )
    _write(tmp_path / "pt_big_tech_phrases.json")
    monkeypatch.setattr(x2, "SOURCE_DIR", tmp_path)

    by_file = {row["file"]: row for row in x2.list_sources()}

    shadow_row = by_file["pt_big_tech_phrases.json"]
    assert shadow_row["valid"] is True
    assert (shadow_row["topic"], shadow_row["notes"]) == ("big_tech_phrases", 1)
    assert by_file["pt_connecting.json"]["valid"] is True


def test_shadowing_model_is_separate_and_existing_model_remains_frozen():
    model = shadow.make_draft_model()
    assert model.model_id == shadow.DRAFT_MODEL_ID
    assert model.model_id != x2.MODEL_ID
    assert [field["name"] for field in model.fields] == shadow.DRAFT_FIELDS
    assert [template["name"] for template in model.templates] == [
        "Listen & Shadow", "Cue & Produce",
    ]
    existing = x2.make_model()
    assert existing.model_id == 1_820_150_001
    assert len(existing.fields) == 17
    assert [template["name"] for template in existing.templates] == [
        "Production", "Cloze",
    ]
