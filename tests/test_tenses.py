"""Tenses Rescue tests: deterministic, no network or DB."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from idiomatic import gemini
from idiomatic.grammar import tenses


def _verb_dict(**overrides) -> dict:
    base = {
        "lang": "pt", "verb": "vir", "gloss": "to come",
        "tense_key": "presente", "tense_label": "Presente",
        "verify": {"mood": "indicativo", "tense": "presente"},
        "history": {"lapses": 76, "reps": 344},
        "fork": "vimos collision",
        "paradigm": [
            {"key": "1s", "pronoun": "eu", "form": "venho", "drill": True},
            {"key": "2s", "pronoun": "tu", "form": "vens", "drill": True},
            {"key": "3s", "pronoun": "ele/você", "form": "vem", "drill": True},
            {"key": "1p", "pronoun": "nós", "form": "vimos", "drill": True},
            {"key": "2p", "pronoun": "vós", "form": "vindes", "drill": False,
             "archaic": True},
            {"key": "3p", "pronoun": "eles/vocês", "form": "vêm", "drill": True},
        ],
        "items": [
            {"person": "1s", "en": "I come to this debate as a skeptic.",
             "tl": "Eu venho a este debate como cético."},
        ],
    }
    base.update(overrides)
    return base


def _write_batch(tmp_path: Path, *verbs: dict) -> Path:
    (tmp_path / "batch1.json").write_text(
        json.dumps({"meta": {}, "verbs": list(verbs)}, ensure_ascii=False),
        encoding="utf-8")
    return tmp_path


def test_parse_verifies_forms_against_truth_table(tmp_path: Path):
    verbs = tenses.load_batches(source_dir=_write_batch(tmp_path, _verb_dict()))
    assert len(verbs) == 1
    assert verbs[0].paradigm[0].form == "venho"


def test_parse_rejects_wrong_table_form(tmp_path: Path):
    bad = _verb_dict()
    bad["paradigm"][1]["form"] = "venes"
    with pytest.raises(tenses.TensesSourceError, match="!= table"):
        tenses.load_batches(source_dir=_write_batch(tmp_path, bad))


def test_parse_rejects_sentence_without_the_form(tmp_path: Path):
    bad = _verb_dict()
    bad["items"][0]["tl"] = "Eu chego a este debate como cético."
    with pytest.raises(tenses.TensesSourceError, match="lacks the exact form"):
        tenses.load_batches(source_dir=_write_batch(tmp_path, bad))


def test_parse_rejects_drilled_archaic_and_unknown_person(tmp_path: Path):
    bad = _verb_dict()
    bad["paradigm"][4]["drill"] = True
    with pytest.raises(tenses.TensesSourceError, match="archaic"):
        tenses.load_batches(source_dir=_write_batch(tmp_path, bad))
    bad2 = _verb_dict(items=[{"person": "9x", "en": "e", "tl": "venho t"}])
    with pytest.raises(tenses.TensesSourceError, match="unknown"):
        tenses.load_batches(source_dir=_write_batch(tmp_path, bad2))


def test_missing_items_lists_drilled_gaps(tmp_path: Path):
    verbs = tenses.load_batches(source_dir=_write_batch(tmp_path, _verb_dict()))
    gaps = tenses.missing_items(verbs)
    assert "pt:vir:presente:2s" in gaps
    assert "pt:vir:presente:2p" not in gaps  # archaic → not required


def test_real_batch1_is_complete_and_valid():
    verbs = tenses.load_batches()
    assert len(verbs) == 15
    assert tenses.missing_items(verbs) == []
    langs = {v.lang for v in verbs}
    assert langs == {"de", "es", "fr", "it", "pt"}
    # the pt/es archaic second-person rows are displayed, never drilled
    for v in verbs:
        for row in v.paradigm:
            if row.archaic:
                assert not row.drill


def test_guids_are_stable_and_kind_namespaced():
    a = tenses.tenses_guid("prod", "pt", "vir", "presente", "1s")
    assert a == tenses.tenses_guid("prod", "pt", "vir", "presente", "1s")
    assert a != tenses.tenses_guid("ex", "pt", "vir", "presente", "1s")
    assert a != tenses.tenses_guid("prod", "pt", "vir", "imperfeito", "1s")


def test_blank_and_mark_hit_only_the_exact_form():
    tl = "Nós vimos de uma era de protocolos abertos."
    assert "＿＿＿" in tenses.blank_sentence(tl, "vimos")
    assert "<b>vimos</b>" in tenses.sentence_html(tl, "vimos")
    with pytest.raises(tenses.TensesSourceError):
        tenses.blank_sentence("Eles chegam tarde.", "vimos")
    # word boundaries: 'vem' must not match inside 'vêm' or 'venho'
    with pytest.raises(tenses.TensesSourceError):
        tenses.blank_sentence("Eu venho amanhã.", "vem")


def test_spoken_answer_shapes():
    verbs = tenses.load_batches()
    by = {(v.lang, v.verb, v.tense_key): v for v in verbs}
    vir = by[("pt", "vir", "presente")]
    rows = {r.key: r for r in vir.paradigm}
    assert tenses.spoken_answer(vir, rows["3p"]) == "eles vêm"
    saber = by[("es", "saber", "presente_subjuntivo")]
    rows = {r.key: r for r in saber.paradigm}
    assert tenses.spoken_answer(saber, rows["1s"]) == "que yo sepa"
    imp = by[("pt", "vir", "imperativo")]
    rows = {r.key: r for r in imp.paradigm}
    assert tenses.spoken_answer(imp, rows["2s"]) == "vem!"


def test_audio_cache_key_depends_on_voice_and_text():
    s1 = SimpleNamespace(tenses_es_voice_id="voiceA")
    s2 = SimpleNamespace(tenses_es_voice_id="voiceB")
    k = tenses.audio_cache_key("que yo sepa", "es", s1)
    assert k == tenses.audio_cache_key("que yo sepa", "es", s1)
    assert k != tenses.audio_cache_key("que yo sepa", "es", s2)
    assert k != tenses.audio_cache_key("que tú sepas", "es", s1)
    # non-es languages ride the house voice regardless of the es setting
    assert (tenses.audio_cache_key("io vorrò", "it", s1)
            == tenses.audio_cache_key("io vorrò", "it", s2))


def test_models_are_frozen():
    for kind, mid, name in (("prod", 1_820_170_001, "Idiomatic Tenses v1"),
                            ("ex", 1_820_170_002,
                             "Idiomatic Tenses Exercises v1")):
        model = tenses.make_model(kind)
        assert model.model_id == mid and model.name == name
        assert [f["name"] for f in model.fields] == tenses.FIELDS
        assert len(model.templates) == 1


def test_synthesize_audio_uses_es_override_and_caches(tmp_path: Path):
    settings = SimpleNamespace(data_dir=str(tmp_path),
                               tenses_es_voice_id="esVoice123")
    verbs = [v for v in tenses.load_batches("es")
             if v.tense_key == "presente_subjuntivo" and v.verb == "saber"]
    seen: list[str | None] = []

    async def fake_synthesize(text, *, voice, out, lang, eleven_voice_id=None):
        seen.append(eleven_voice_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"mp3" + text.encode("utf-8"))

    audio, synthesized, failed = asyncio.run(tenses._synthesize_audio(
        verbs, lang="es", settings=settings,
        synthesize_fn=fake_synthesize, level_fn=lambda c: c))
    assert failed == 0 and synthesized == len(seen)
    assert set(seen) == {"esVoice123"}
    assert all(a.answer and a.sentence for a in audio.values())
    # second run: everything cached
    _, synthesized2, _ = asyncio.run(tenses._synthesize_audio(
        verbs, lang="es", settings=settings,
        synthesize_fn=fake_synthesize, level_fn=lambda c: c))
    assert synthesized2 == 0


def test_apkg_build_both_kinds(tmp_path: Path):
    verbs = tenses.load_batches("pt")
    n = tenses.build_tenses_apkg(
        kind="prod", out_path=tmp_path / "p.apkg", lang="pt", verbs=verbs)
    n_ex = tenses.build_tenses_apkg(
        kind="ex", out_path=tmp_path / "e.apkg", lang="pt", verbs=verbs)
    assert n == n_ex == sum(len(v.items) for v in verbs)
    with zipfile.ZipFile(tmp_path / "e.apkg") as archive:
        db_path = tmp_path / "collection.anki2"
        db_path.write_bytes(archive.read("collection.anki2"))
    con = sqlite3.connect(db_path)
    try:
        (deck_json,) = con.execute("SELECT decks FROM col").fetchone()
        names = {d["name"] for d in json.loads(deck_json).values()}
        assert "PT Portuguese::3 Tenses::2 Exercises::vir" in names
        rows = con.execute("SELECT flds FROM notes").fetchall()
        blanks = [r[0].split("\x1f")[tenses.FIELDS.index("TLBlank")]
                  for r in rows]
        forms = [r[0].split("\x1f")[tenses.FIELDS.index("Form")]
                 for r in rows]
        assert all("＿＿＿" in b for b in blanks)
        # the exercises front must never leak the drilled form
        for b, f in zip(blanks, forms):
            bare = f.rstrip("!").split()[-1]
            assert bare not in b.split()
    finally:
        con.close()


def test_gemini_synthesize_accepts_voice_override():
    import inspect
    assert "eleven_voice_id" in inspect.signature(gemini.synthesize).parameters
    assert "voice_id" in inspect.signature(gemini._elevenlabs_tts).parameters
