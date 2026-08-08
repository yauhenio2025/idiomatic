"""Owner preview tests use synthetic pilots, never the live authoring outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import x2_pilot_preview as preview


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _pilot_rows(chunk: str, kept: dict) -> tuple[list[dict], list[dict], list[dict]]:
    topic = preview.gate._chunk_lang_topic(chunk)[1]
    stem = f"it_{topic}"
    inputs = []
    triage = []
    for number in range(1, 31):
        item_id = f"{stem}_{number:03d}"
        en = kept["en"] if number == 1 else f"Discarded fixture prompt {number}"
        inputs.append({"id": item_id, "en": en, "old_back": "legacy reference"})
        triage.append(
            {
                "id": item_id,
                "en": en,
                "verdict": "keep" if number == 1 else "drop",
                "reason": "" if number == 1 else "fixture duplicate <not rendered>",
            }
        )
    kept = dict(kept, id=inputs[0]["id"])
    return inputs, [kept], triage


def _fixture_batches(tmp_path: Path) -> Path:
    batch_dir = tmp_path / "batches"
    fancy = {
        "en": 'To regulate <script>alert("owner")</script>',
        "category": "lexical-verb",
        "tl": "regular <b>ahora</b>",
        "alts": ["reglamentar & supervisar"],
        "register": "Neutral-formal <unsafe>.",
        "trap": "Never copy <script>this</script>.",
        "example_tl": (
            "La comisión decidió regular <b>ahora</b> los mercados digitales porque "
            "las plataformas dominantes ocultaban riesgos graves para consumidores, "
            "medios y empresas europeas."
        ),
        "example_en": "The commission decided to regulate now & explain why.",
        "cloze": (
            "La comisión decidió {{c1::regular <b>ahora</b>}} los mercados digitales "
            "porque las plataformas dominantes ocultaban riesgos graves para "
            "consumidores, medios y empresas europeas."
        ),
        "note": "fixture",
    }
    geopolitics = {
        "en": "Balance of Power - A distribution of power among states.",
        "category": "term-definition",
        "tl": "equilibrio de poder",
        "alts": [],
        "register": "Relaciones internacionales; término técnico.",
        "trap": "No confundir con un mero equilibrio presupuestario.",
        "example_tl": (
            "El nuevo pacto regional alteró el equilibrio de poder al coordinar "
            "capacidades militares, tecnológicas y financieras entre cinco Estados "
            "anteriormente rivales."
        ),
        "example_en": (
            "The new regional pact altered the balance of power by coordinating "
            "military, technological, and financial capabilities among five former rivals."
        ),
        "cloze": (
            "El nuevo pacto regional alteró el {{c1::equilibrio de poder}} al coordinar "
            "capacidades militares, tecnológicas y financieras entre cinco Estados "
            "anteriormente rivales."
        ),
        "note": "Definición corregida: <em>distribución & relación</em> de capacidades.",
    }
    phrases = {
        "en": "In light of <script>recent evidence</script>, the board changed course.",
        "category": "context-frame",
        "tl": "À luz dos dados recentes, o conselho mudou de rumo.",
        "focus_tl": "À luz dos dados recentes",
        "focus_en": "base a reassessment on evidence",
        "register": "Formal analysis & policy writing.",
        "trap": "Do not write <b>em luz de</b>.",
        "note": "The sentence is complete <and audited>.",
    }
    for spec, row in zip(preview.PILOTS, (fancy, geopolitics, phrases), strict=True):
        inputs, notes, triage = _pilot_rows(spec.chunk, row)
        _write(batch_dir / "input" / f"{spec.chunk}.json", inputs)
        _write(batch_dir / "output" / f"{spec.chunk}_notes.json", notes)
        _write(batch_dir / "output" / f"{spec.chunk}_triage.json", triage)
    return batch_dir


def test_preview_is_deterministic_complete_and_html_escaped(tmp_path: Path):
    batch_dir = _fixture_batches(tmp_path)
    first = tmp_path / "first.html"
    second = tmp_path / "second.html"

    assert preview.write_preview(first, batch_dir=batch_dir) == 3
    assert preview.write_preview(second, batch_dir=batch_dir) == 3
    assert first.read_bytes() == second.read_bytes()
    rendered = first.read_text(encoding="utf-8")

    assert "Production" in rendered
    assert "Cloze" in rendered
    assert "Listen &amp; Shadow" in rendered
    assert "Cue &amp; Produce" in rendered
    assert "Corrected definition (from audit note)" in rendered
    assert "Definición corregida: &lt;em&gt;distribución &amp; relación&lt;/em&gt;" in rendered
    assert "Local Qwen · full-sentence clip pending owner voicing clearance" in rendered
    assert "<script>" not in rendered
    assert "<b>ahora</b>" not in rendered
    assert "&lt;script&gt;alert(&quot;owner&quot;)&lt;/script&gt;" in rendered
    assert "<mark>regular &lt;b&gt;ahora&lt;/b&gt;</mark>" in rendered
    assert '<span class="blank"></span>' in rendered


def test_preview_refuses_failed_gate_before_writing(tmp_path: Path):
    batch_dir = _fixture_batches(tmp_path)
    triage_path = (
        batch_dir / "output" / "es_fancy_vocab_pilot_b01_triage.json"
    )
    triage = json.loads(triage_path.read_text(encoding="utf-8"))
    triage[0]["en"] = "Source text changed behind the gate"
    _write(triage_path, triage)
    output = tmp_path / "must-not-exist.html"

    with pytest.raises(preview.PreviewError, match="mechanical gate failed"):
        preview.write_preview(output, batch_dir=batch_dir)
    assert not output.exists()


def test_definition_gate_requires_corrected_definition_in_note(tmp_path: Path):
    batch_dir = _fixture_batches(tmp_path)
    notes_path = batch_dir / "output" / "es_geopolitics_pilot_b01_notes.json"
    notes = json.loads(notes_path.read_text(encoding="utf-8"))
    notes[0]["note"] = ""
    _write(notes_path, notes)

    with pytest.raises(preview.PreviewError, match="corrected definition missing"):
        preview.load_pilots(batch_dir)
