"""Translation-deck tests: deterministic, with no network or DB."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from idiomatic import gemini
from idiomatic.grammar import translation as tr


_FROZEN_FIELDS = [
    "ItemId", "Lang", "Topic", "TenseLabel", "Symbol", "EnText", "EnAudio",
    "TlHTML", "TlAudio", "Why", "Extra1", "Extra2", "Extra3", "Extra4",
]


def _row(**overrides) -> dict:
    base = {
        "id": 101,
        "lang": "es",
        "topic": "es_preterito",
        "fmt": "cloze",
        "infinitive": "tener",
        "sentence": "Ayer ___ (tener) una reunión con el equipo.",
        "answer": "tuve",
        "gloss_en": "Yesterday I had a meeting with the team.",
        "why_en": "Completed past action → pretérito indefinido.",
    }
    base.update(overrides)
    return base


def _stage(audio_dir: Path, lang: str, item_id: int, size: int = 2000) -> Path:
    audio_dir.mkdir(parents=True, exist_ok=True)
    clip = audio_dir / f"idg_{lang}_{item_id}.mp3"
    clip.write_bytes(b"m" * size)
    return clip


def _item(item_id: int, gloss: str = "Yesterday I had a meeting.",
          *, topic: str = "es_preterito", lang: str = "es") -> tr.TranslationItem:
    return tr.TranslationItem(
        item_id=item_id,
        lang=lang,
        topic=topic,
        en_text=gloss,
        tl_html=f"Ayer <b>tuve</b> la reunión {item_id}.",
        tl_text=f"Ayer tuve la reunión {item_id}.",
        why="Completed past action.",
        tl_clip=f"idg_{lang}_{item_id}.mp3",
    )


def _settings(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        data_dir=str(tmp_path),
        tts_provider="elevenlabs",
        elevenlabs_api_key="k",
        elevenlabs_model="eleven_turbo_v2_5",
        gemini_tts_model="gemini-tts",
    )


def test_model_is_frozen_with_one_template():
    model = tr.make_model()
    assert model.model_id == 1_820_160_001
    assert [field["name"] for field in model.fields] == _FROZEN_FIELDS
    assert [template["name"] for template in model.templates] == ["Translate"]


def test_guid_is_stable_and_namespaced():
    guid = tr.translation_guid("es", 7)
    assert guid == tr.translation_guid("es", 7)
    assert guid != tr.translation_guid("de", 7)
    assert guid != tr.translation_guid("es", 8)
    # Never collides with the drill deck's GUID for the very same item.
    drill = hashlib.sha1(b"idiomatic-grammar::es::7").hexdigest()[:16]
    assert guid != drill


def test_deck_id_range_and_deck_names():
    assert tr.deck_name_for("es", "1 Tiempos") == "Idiomatic Translation ES::1 Tiempos"
    assert tr.deck_name_for("es", "") == "Idiomatic Translation ES"
    for name in ("Idiomatic Translation ES::1 Tiempos", "Idiomatic Translation DE"):
        deck_id = tr._deck_id(name)
        assert 1_930_000_000 <= deck_id < 1_990_000_000
        assert deck_id == tr._deck_id(name)


def test_select_excludes_wrong_formats(tmp_path: Path):
    rows = [_row(), _row(id=102, fmt="f3"), _row(id=103, fmt="f4"),
            _row(id=104, fmt="explainer")]
    _stage(tmp_path, "es", 101)
    selected, stats = tr.select_items(rows, lang="es", audio_dir=tmp_path)
    assert [item.item_id for item in selected] == [101]
    assert stats["excluded_fmt"] == 3


def test_select_requires_gloss_answer_sentence(tmp_path: Path):
    rows = [_row(id=1, gloss_en=""), _row(id=2, answer="  "),
            _row(id=3, sentence=None), _row(id=4, gloss_en=None)]
    selected, stats = tr.select_items(rows, lang="es", audio_dir=tmp_path)
    assert selected == []
    assert stats["missing_text"] == 4


def test_select_skips_short_sentences(tmp_path: Path):
    rows = [_row(id=101, sentence="___ (ser) yo.", answer="soy",
                 infinitive="ser")]
    _stage(tmp_path, "es", 101)
    selected, stats = tr.select_items(rows, lang="es", audio_dir=tmp_path)
    assert selected == []
    assert stats["too_short"] == 1


def test_select_dedupes_first_wins(tmp_path: Path):
    rows = [_row(id=101), _row(id=102)]  # identical rendered sentence
    _stage(tmp_path, "es", 101)
    _stage(tmp_path, "es", 102)
    selected, stats = tr.select_items(rows, lang="es", audio_dir=tmp_path)
    assert [item.item_id for item in selected] == [101]
    assert stats["duplicate"] == 1 and stats["eligible"] == 1


def test_select_requires_existing_drill_clip(tmp_path: Path):
    rows = [_row(id=101),
            _row(id=102, sentence="Mañana ___ (tener) otra reunión con ellos.",
                 answer="tendré")]
    _stage(tmp_path, "es", 101, size=100)  # undersized = the reuse check fails
    _stage(tmp_path, "es", 102)
    selected, stats = tr.select_items(rows, lang="es", audio_dir=tmp_path)
    assert [item.item_id for item in selected] == [102]
    assert stats["no_tl_audio"] == 1 and stats["eligible"] == 2
    assert selected[0].tl_clip == "idg_es_102.mp3"


def test_select_dedupe_runs_before_audio_check(tmp_path: Path):
    # Identity must not depend on disk state: the audioless first occurrence
    # keeps winning the dedupe, so its duplicate never ships under another
    # GUID (see the module comment).
    rows = [_row(id=101), _row(id=102)]
    _stage(tmp_path, "es", 102)  # only the duplicate has a clip
    selected, stats = tr.select_items(rows, lang="es", audio_dir=tmp_path)
    assert selected == []
    assert stats["duplicate"] == 1 and stats["no_tl_audio"] == 1


def test_tl_html_bolds_and_escapes(tmp_path: Path):
    rows = [_row(sentence='Ayer "él" <b> & ___ (tener) una reunión.',
                 answer='tuvo & "vio"')]
    _stage(tmp_path, "es", 101)
    selected, _ = tr.select_items(rows, lang="es", audio_dir=tmp_path)
    assert selected[0].tl_html == (
        'Ayer &quot;él&quot; &lt;b&gt; &amp; '
        '<b>tuvo &amp; &quot;vio&quot;</b> una reunión.'
    )


def test_en_cache_key_pure_and_text_sensitive(tmp_path: Path):
    settings = _settings(tmp_path)
    key = tr.en_cache_key("Yesterday I had a meeting.", settings)
    assert key == tr.en_cache_key("Yesterday I had a meeting.", settings)
    assert key != tr.en_cache_key("Another sentence entirely.", settings)
    rerouted = _settings(tmp_path)
    rerouted.elevenlabs_model = "eleven_flash_v3"
    assert key != tr.en_cache_key("Yesterday I had a meeting.", rerouted)


def test_en_audio_filename_validates_digest():
    assert tr.en_audio_filename("es", "a" * 16) == f"idtr_es_{'a' * 16}.mp3"
    with pytest.raises(ValueError):
        tr.en_audio_filename("es", "nope")


def test_synthesize_en_audio_caches_shares_and_drops_failures(tmp_path: Path):
    settings = _settings(tmp_path)
    items = [
        _item(101, "Shared gloss."),
        _item(102, "Shared gloss."),
        _item(103, "Broken gloss."),
    ]

    async def fake_synthesize(text: str, *, voice: str, out: Path, lang: str) -> None:
        assert voice == "Kore" and lang == "en"
        out.parent.mkdir(parents=True, exist_ok=True)
        if text == "Broken gloss.":
            out.write_bytes(b"x")  # then marked as silence below
            gemini.silence_marker(out).touch()
        else:
            out.write_bytes(b"mp3" + text.encode("utf-8"))

    audio, synthesized, failed = asyncio.run(
        tr._synthesize_en_audio(
            items, lang="es", settings=settings,
            synthesize_fn=fake_synthesize, level_fn=lambda clip: clip,
        )
    )
    assert synthesized == 2 and failed == 1  # shared gloss synthesized once
    assert audio[101] is not None and audio[101] == audio[102]
    assert audio[103] is None  # silence-marked clip is unusable

    # Second run: the usable clip is cached; only the failure retries.
    audio2, synthesized2, failed2 = asyncio.run(
        tr._synthesize_en_audio(
            items, lang="es", settings=settings,
            synthesize_fn=fake_synthesize, level_fn=lambda clip: clip,
        )
    )
    assert synthesized2 == 1 and failed2 == 1
    assert audio2[101] == audio[101]


def test_apkg_build_packages_fields_media_and_subdecks(tmp_path: Path):
    audio_dir = tmp_path / "tl"
    clips = {item_id: _stage(audio_dir, "es", item_id)
             for item_id in (101, 102, 103)}
    en_clip = tmp_path / "idtr_es_aaaaaaaaaaaaaaaa.mp3"
    en_clip.write_bytes(b"mp3")
    items = [
        _item(101, "Shared gloss."),
        _item(102, "Solo gloss.", topic="es_subjuntivo"),
        _item(103, "Shared gloss."),
    ]
    out = tmp_path / "out.apkg"
    n = tr.build_translation_apkg(
        out_path=out, lang="es", items=items, audio_dir=audio_dir,
        en_audio={101: en_clip, 102: None, 103: en_clip},
        topic_labels={"es_preterito": ("Pretérito indefinido", "←")},
        topic_clusters={"es_preterito": "1 Tiempos"},
    )
    assert n == 3
    with zipfile.ZipFile(out) as archive:
        assert "collection.anki2" in archive.namelist()
        media = json.loads(archive.read("media"))
        # The shared EN clip is packaged once despite two [sound:] references.
        assert sorted(media.values()) == sorted(
            [clip.name for clip in clips.values()] + [en_clip.name]
        )
        db_bytes = archive.read("collection.anki2")
    db_path = tmp_path / "collection.anki2"
    db_path.write_bytes(db_bytes)
    connection = sqlite3.connect(db_path)
    try:
        (deck_json,) = connection.execute("SELECT decks FROM col").fetchone()
        deck_names = {deck["name"] for deck in json.loads(deck_json).values()}
        assert "Idiomatic Translation ES::1 Tiempos" in deck_names
        assert "Idiomatic Translation ES" in deck_names  # clusterless fallback
        rows = connection.execute("SELECT guid, flds FROM notes").fetchall()
        by_id = {fields.split("\x1f")[0]: (guid, fields.split("\x1f"))
                 for guid, fields in rows}
        guid_a, a = by_id["101"]
        assert guid_a == tr.translation_guid("es", 101)
        assert a[1] == "es" and a[2] == "es_preterito"
        assert a[3] == "Pretérito indefinido" and a[4] == "←"
        assert a[5] == "Shared gloss."
        assert a[6] == f"[sound:{en_clip.name}]"
        assert a[7] == "Ayer <b>tuve</b> la reunión 101."
        assert a[8] == "[sound:idg_es_101.mp3]"
        assert a[9] == "Completed past action."
        assert a[10:] == ["", "", "", ""]
        _, b = by_id["102"]
        assert b[3] == "es_subjuntivo" and b[4] == ""  # label fallback
        (n_cards,) = connection.execute("SELECT count(*) FROM cards").fetchone()
        assert n_cards == 3  # one template per note
    finally:
        connection.close()


def test_apkg_build_rejects_wrong_lang_and_missing_media(tmp_path: Path):
    item = _item(101)
    with pytest.raises(ValueError, match="lang"):
        tr.build_translation_apkg(
            out_path=tmp_path / "x.apkg", lang="de", items=[item],
            audio_dir=tmp_path,
        )
    with pytest.raises(ValueError, match="missing translation media"):
        tr.build_translation_apkg(
            out_path=tmp_path / "x.apkg", lang="es", items=[item],
            audio_dir=tmp_path,  # no drill clip staged
        )


def test_silence_marked_en_clip_ships_card_without_en_audio(tmp_path: Path):
    settings = _settings(tmp_path)
    item = _item(101, "Broken gloss.")

    async def fake_synthesize(text: str, *, voice: str, out: Path, lang: str) -> None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"x")
        gemini.silence_marker(out).touch()

    audio, _, failed = asyncio.run(
        tr._synthesize_en_audio(
            [item], lang="es", settings=settings,
            synthesize_fn=fake_synthesize, level_fn=lambda clip: clip,
        )
    )
    assert failed == 1 and audio[101] is None

    audio_dir = tmp_path / "tl"
    _stage(audio_dir, "es", 101)
    out = tmp_path / "out.apkg"
    tr.build_translation_apkg(
        out_path=out, lang="es", items=[item], audio_dir=audio_dir,
        en_audio=audio,
    )
    with zipfile.ZipFile(out) as archive:
        db_bytes = archive.read("collection.anki2")
    db_path = tmp_path / "collection.anki2"
    db_path.write_bytes(db_bytes)
    connection = sqlite3.connect(db_path)
    try:
        (fields,) = connection.execute("SELECT flds FROM notes").fetchone()
        values = fields.split("\x1f")
        assert values[6] == ""  # no EN audio, card still ships
        assert values[8] == "[sound:idg_es_101.mp3]"
    finally:
        connection.close()


def test_sentence_audio_prefers_cached_constituent_and_heals(tmp_path: Path):
    """Back audio is the sentence-only clip: cached _work constituents are
    reused, missing ones are synthesized, silence-marked ones fall back."""
    from types import SimpleNamespace

    from idiomatic import gemini

    items = [
        tr.TranslationItem(
            item_id=1, lang="it", topic="t", en_text="one",
            tl_html="<b>x</b>", tl_text="Frase uno completa.", why="",
            tl_clip="idg_it_1.mp3"),
        tr.TranslationItem(
            item_id=2, lang="it", topic="t", en_text="two",
            tl_html="<b>y</b>", tl_text="Frase due completa.", why="",
            tl_clip="idg_it_2.mp3"),
        tr.TranslationItem(
            item_id=3, lang="it", topic="t", en_text="three",
            tl_html="<b>z</b>", tl_text="Frase tre completa.", why="",
            tl_clip="idg_it_3.mp3"),
    ]
    audio_dir = tmp_path / "it"
    work = audio_dir / "_work"
    work.mkdir(parents=True)
    (work / "1_sentence.mp3").write_bytes(b"cached-sentence")

    async def fake_synthesize(text, *, voice, out, lang):
        out.parent.mkdir(parents=True, exist_ok=True)
        if text == "Frase tre completa.":
            out.write_bytes(b"x")
            gemini.silence_marker(out).touch()
        else:
            out.write_bytes(b"synth:" + text.encode())

    settings = SimpleNamespace(data_dir=str(tmp_path))
    tl_audio, synthesized, fallback = asyncio.run(
        tr._ensure_sentence_audio(
            items, lang="it", settings=settings, audio_dir=audio_dir,
            synthesize_fn=fake_synthesize, level_fn=lambda clip: clip,
        )
    )
    assert synthesized == 2          # items 2 and 3 attempted
    assert fallback == 1             # item 3 silence-marked -> stitched fallback
    assert tl_audio[1].read_bytes() == b"cached-sentence"
    assert tl_audio[2].read_bytes().startswith(b"synth:")
    assert 3 not in tl_audio

    # Packaging: item 3 falls back to the stitched drill clip.
    (audio_dir / "idg_it_3.mp3").write_bytes(b"stitched")
    (audio_dir / "idg_it_1.mp3").write_bytes(b"stitched1")
    (audio_dir / "idg_it_2.mp3").write_bytes(b"stitched2")
    out = tmp_path / "o.apkg"
    tr.build_translation_apkg(
        out_path=out, lang="it", items=items, audio_dir=audio_dir,
        en_audio={}, tl_audio=tl_audio,
    )
    import json as _json
    import zipfile as _zip
    with _zip.ZipFile(out) as archive:
        media = set(_json.loads(archive.read("media")).values())
    assert "1_sentence.mp3" in media and "2_sentence.mp3" in media
    assert "idg_it_3.mp3" in media
    assert "idg_it_1.mp3" not in media
