"""Exercises 2.0 tests: deterministic, with no network or DB."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from idiomatic import gemini
from idiomatic.grammar import exercises2 as x2


_FROZEN_FIELDS = [
    "ItemId", "Lang", "Topic", "Category", "EN", "TL", "Alts", "Register",
    "Trap", "ExampleTL", "ExampleEN", "ClozeFront", "AudioTL", "AudioExample",
    "Extra1", "Extra2", "Extra3",
]


def _note_dict(**overrides) -> dict:
    base = {
        "id": "esc01",
        "en": "Be that as it may",
        "category": "concession",
        "tl": "Sea como fuere",
        "alts": ["Sea como sea"],
        "register": "written-formal",
        "trap": "Aunque subordinates a clause.",
        "example_tl": "Sea como fuere, la comisión no puede aplazar la regulación.",
        "example_en": "Be that as it may, the commission cannot postpone regulation.",
        "cloze": "{{c1::Sea como fuere}}, la comisión no puede aplazar la regulación.",
        "note": "",
    }
    base.update(overrides)
    return base


def _write(tmp_path: Path, name: str, items: list[dict]) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return path


def test_parse_accepts_generalized_keys(tmp_path: Path):
    notes = x2.parse_notes_file(_write(tmp_path, "es_connecting.json", [_note_dict()]))
    assert len(notes) == 1
    note = notes[0]
    assert (note.lang, note.topic, note.item_id) == ("es", "connecting", "esc01")
    assert note.tl == "Sea como fuere"
    assert note.example_tl.startswith("Sea como fuere,")


def test_parse_accepts_es_pilot_key_spelling(tmp_path: Path):
    raw = _note_dict()
    raw["es_main"] = raw.pop("tl")
    raw["es_alts"] = raw.pop("alts")
    raw["example_es"] = raw.pop("example_tl")
    notes = x2.parse_notes_file(_write(tmp_path, "es_connecting.json", [raw]))
    assert notes[0].tl == "Sea como fuere"
    assert notes[0].alts == ("Sea como sea",)


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("connecting.json", "filename"),
        ("xx_connecting.json", "filename"),
        ("es-connecting.json", "filename"),
    ],
)
def test_parse_rejects_bad_filenames(tmp_path: Path, name: str, message: str):
    path = _write(tmp_path, name, [_note_dict()])
    with pytest.raises(x2.Ex2SourceError, match=message):
        x2.parse_notes_file(path)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"category": "vibes"}, "unknown category"),
        ({"tl": "  "}, "must be nonempty"),
        ({"cloze": "sin marcador"}, "c1"),
        ({"example_tl": "Otra frase."}, "does not reduce"),
        ({"alts": ["ok", ""]}, "list of nonempty strings"),
        ({"id": "Bad Id"}, "invalid or missing item id"),
    ],
)
def test_parse_rejects_contract_violations(
    tmp_path: Path, overrides: dict, message: str
):
    path = _write(tmp_path, "es_connecting.json", [_note_dict(**overrides)])
    with pytest.raises(x2.Ex2SourceError, match=message):
        x2.parse_notes_file(path)


def test_parse_rejects_duplicate_ids(tmp_path: Path):
    path = _write(tmp_path, "es_connecting.json", [_note_dict(), _note_dict()])
    with pytest.raises(x2.Ex2SourceError, match="duplicate item id"):
        x2.parse_notes_file(path)


def test_trap_is_optional_but_other_fields_are_not(tmp_path: Path):
    notes = x2.parse_notes_file(
        _write(tmp_path, "es_connecting.json", [_note_dict(trap="")])
    )
    assert notes[0].trap == ""


def test_real_pilot_file_parses():
    notes = x2.parse_notes_file(x2.SOURCE_DIR / "es_connecting.json")
    assert len(notes) == 207
    assert {note.lang for note in notes} == {"es"}
    assert sum(1 for note in notes if note.trap) >= 30


def test_guid_and_deck_id_are_stable_and_namespaced():
    guid = x2.exercises_guid("es", "connecting", "esc10")
    assert guid == x2.exercises_guid("es", "connecting", "esc10")
    assert guid != x2.exercises_guid("it", "connecting", "esc10")
    deck_id = x2._deck_id(x2.deck_name_for("es", "connecting"))
    assert 1_920_000_000 <= deck_id < 1_990_000_000


def test_deck_name_uses_label_map_with_title_fallback():
    assert x2.deck_name_for("es", "connecting") == "ES Spanish::4 Exercises::Conectores"
    assert x2.deck_name_for("de", "fancy_vocab") == "DE German::4 Exercises::Fancy Vocab"


def test_cloze_rendering_escapes_and_marks_multiple_spans():
    cloze = "{{c1::Aunque}} <b> raro, {{c1::sino que}} sigue."
    marked = x2.example_tl_html(cloze)
    assert marked == "<mark>Aunque</mark> &lt;b&gt; raro, <mark>sino que</mark> sigue."
    blanked = x2.cloze_front_html(cloze)
    assert blanked.count('<span class="blank"></span>') == 2
    assert "Aunque" not in blanked and "&lt;b&gt;" in blanked


def test_model_is_frozen_with_two_templates():
    model = x2.make_model()
    assert model.model_id == 1_820_150_001
    assert [field["name"] for field in model.fields] == _FROZEN_FIELDS
    assert [template["name"] for template in model.templates] == [
        "Production", "Cloze",
    ]


def test_audio_filename_validates_digest():
    assert x2.audio_filename("es", "a" * 16) == f"idx2_es_{'a' * 16}.mp3"
    with pytest.raises(ValueError):
        x2.audio_filename("es", "nope")


def _settings(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        data_dir=str(tmp_path),
        tts_provider="elevenlabs",
        elevenlabs_api_key="k",
        elevenlabs_model="eleven_turbo_v2_5",
        gemini_tts_model="gemini-tts",
    )


def test_audio_cache_key_depends_on_text_and_lang(tmp_path: Path):
    settings = _settings(tmp_path)
    key = x2.audio_cache_key("Sea como fuere", "es", settings)
    assert key == x2.audio_cache_key("Sea como fuere", "es", settings)
    assert key != x2.audio_cache_key("Sea como sea", "es", settings)
    assert key != x2.audio_cache_key("Sea como fuere", "pt", settings)


def test_synthesize_note_audio_caches_and_drops_failures(tmp_path: Path):
    settings = _settings(tmp_path)
    notes = [
        x2._parse_note(Path("es_connecting.json"), "es", "connecting", _note_dict()),
        x2._parse_note(
            Path("es_connecting.json"), "es", "connecting",
            _note_dict(
                id="esc02", tl="En suma",
                example_tl="En suma, la estrategia fracasó.",
                cloze="{{c1::En suma}}, la estrategia fracasó.",
            ),
        ),
    ]

    async def fake_synthesize(text: str, *, voice: str, out: Path, lang: str) -> None:
        out.parent.mkdir(parents=True, exist_ok=True)
        if text == "En suma":
            out.write_bytes(b"x")  # then marked as silence below
            gemini.silence_marker(out).touch()
        else:
            out.write_bytes(b"mp3" + text.encode("utf-8"))

    audio, synthesized, failed = asyncio.run(
        x2._synthesize_note_audio(
            notes, lang="es", settings=settings,
            synthesize_fn=fake_synthesize, level_fn=lambda clip: clip,
        )
    )
    assert synthesized == 4 and failed == 1
    assert audio["esc01"].answer is not None and audio["esc01"].example is not None
    assert audio["esc02"].answer is None  # silence-marked clip is unusable
    assert audio["esc02"].example is not None

    # Second run: everything usable is cached; only the failure retries.
    audio2, synthesized2, failed2 = asyncio.run(
        x2._synthesize_note_audio(
            notes, lang="es", settings=settings,
            synthesize_fn=fake_synthesize, level_fn=lambda clip: clip,
        )
    )
    assert synthesized2 == 1 and failed2 == 1
    assert audio2["esc01"].answer == audio["esc01"].answer


def test_apkg_build_packages_fields_media_and_subdeck(tmp_path: Path):
    notes = [
        x2._parse_note(Path("es_connecting.json"), "es", "connecting", _note_dict()),
    ]
    clip = tmp_path / "idx2_es_aaaaaaaaaaaaaaaa.mp3"
    clip.write_bytes(b"mp3")
    out = tmp_path / "out.apkg"
    n = x2.build_exercises2_apkg(
        out_path=out, lang="es", notes=notes,
        audio={"esc01": x2.NoteAudio(answer=clip, example=None)},
    )
    assert n == 1
    with zipfile.ZipFile(out) as archive:
        names = archive.namelist()
        assert "collection.anki2" in names
        media = json.loads(archive.read("media"))
        assert list(media.values()) == [clip.name]
        db_bytes = archive.read("collection.anki2")
    db_path = tmp_path / "collection.anki2"
    db_path.write_bytes(db_bytes)
    connection = sqlite3.connect(db_path)
    try:
        (deck_json,) = connection.execute("SELECT decks FROM col").fetchone()
        deck_names = {deck["name"] for deck in json.loads(deck_json).values()}
        assert "ES Spanish::4 Exercises::Conectores" in deck_names
        (fields,) = connection.execute("SELECT flds FROM notes").fetchone()
        values = fields.split("\x1f")
        assert values[0] == "es:connecting:esc01"
        assert values[5] == "Sea como fuere"
        assert values[9] == (
            "<mark>Sea como fuere</mark>, la comisión no puede aplazar la regulación."
        )
        assert values[12] == f"[sound:{clip.name}]"
        assert values[13] == ""  # example clip absent → text-only, not a failure
        (n_cards,) = connection.execute("SELECT count(*) FROM cards").fetchone()
        assert n_cards == 2  # Production + Cloze
    finally:
        connection.close()


def test_apkg_build_rejects_wrong_lang_and_missing_media(tmp_path: Path):
    note = x2._parse_note(
        Path("es_connecting.json"), "es", "connecting", _note_dict()
    )
    with pytest.raises(ValueError, match="lang"):
        x2.build_exercises2_apkg(
            out_path=tmp_path / "x.apkg", lang="it", notes=[note],
        )
    with pytest.raises(ValueError, match="missing exercises2 media"):
        x2.build_exercises2_apkg(
            out_path=tmp_path / "x.apkg", lang="es", notes=[note],
            audio={"esc01": x2.NoteAudio(answer=tmp_path / "ghost.mp3", example=None)},
        )
