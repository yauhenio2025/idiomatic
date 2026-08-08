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
