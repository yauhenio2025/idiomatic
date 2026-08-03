"""Podcast lesson-card tests: deterministic, with no network or DB."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from types import SimpleNamespace
import zipfile

import pytest

from idiomatic import gemini
from idiomatic.grammar import podcast_cards as pc
from idiomatic.grammar.apkg import MODEL_ID as GRAMMAR_MODEL_ID
from idiomatic.grammar.explainers import Segment


_FROZEN_FIELDS = [
    "LessonId",
    "Episode",
    "Seq",
    "Lang",
    "FrontHTML",
    "BackHTML",
    "FrontAudio",
    "BackAudio",
    "FrontImage",
    "BackImage",
    "Extra1",
    "Extra2",
    "Extra3",
    "Extra4",
]


def _frontmatter(*, series: str = "grammar-walk-cards", lang: str = "fr") -> str:
    return f"""---
series: {series}
episode: 3
format_version: 1
lang: {lang}
title: "Fixture lesson"
short_title: "Beaucoup de"
img_style: "Clean flat art"
evidence_refs:
  - ignored
---
"""


def _card(index: int = 1) -> str:
    return f"""[CARD]
TITLE: Front {index}
IMG: Front image {index}
Narrate front {index}.
SHOW: Front note {index}
[SIDE]
TITLE: Back {index}
IMG: Back image {index}
TL: C'est le dos {index}.
SHOW: Back note {index}
"""


def _write_source(
    tmp_path: Path,
    body: str,
    *,
    series: str = "grammar-walk-cards",
    lang: str = "fr",
    slug: str = "fixture",
) -> Path:
    path = tmp_path / f"{lang}_{slug}.md"
    path.write_text(
        _frontmatter(series=series, lang=lang)
        + "\n## SCRIPT\n\n"
        + body.strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def _four_cards(*, first: str | None = None) -> str:
    cards = [first if first is not None else _card(1)]
    cards.extend(_card(index) for index in range(2, 5))
    return "\n".join(cards)


def _assert_source_error(path: Path, match: str) -> None:
    with pytest.raises(pc.PodcastCardSourceError, match=match) as caught:
        pc.parse_podcast_cards(path)
    assert re.match(rf"^{re.escape(path.name)}: line \d+: ", str(caught.value))


def test_real_pilot_source_parses_into_five_two_sided_cards():
    path = pc.SOURCE_DIR / "fr_quantity-system.md"

    script = pc.parse_podcast_cards(path)

    assert (script.lang, script.slug, script.episode) == (
        "fr",
        "quantity-system",
        3,
    )
    assert len(script.cards) == 5
    sides = [side for card in script.cards for side in (card.front, card.back)]
    assert len(sides) == 10
    assert [card.seq for card in script.cards] == [1, 2, 3, 4, 5]
    for card in script.cards:
        assert card.front.seq == card.back.seq == card.seq
        assert card.front.side == "front"
        assert card.back.side == "back"
    assert all(side.title and side.img_prompt for side in sides)
    assert all(
        "flip" in [s for s in card.front.segments if s.kind == "speech"][-1].text.casefold()
        for card in script.cards
    )

    hidden_answer = "Il lit beaucoup de journaux."
    practice = script.cards[2].front
    assert any(
        segment.kind == "speech"
        and segment.lang == "fr"
        and segment.text == hidden_answer
        for segment in practice.segments
    )
    assert hidden_answer not in [item.text for item in practice.display]

    practice_fronts = [
        card.front
        for card in script.cards
        if "practice" in card.front.title.casefold()
        or "quick fire" in card.front.title.casefold()
    ]
    assert len(practice_fronts) == 3
    assert all(any(item.kind == "show" for item in side.display)
               for side in practice_fronts)


def test_parser_rejects_bad_series(tmp_path: Path):
    path = _write_source(tmp_path, _four_cards(), series="grammar-walk")
    _assert_source_error(path, "series")


def test_parser_rejects_cross_language_v1_source(tmp_path: Path):
    path = _write_source(tmp_path, _four_cards(), lang="x")
    _assert_source_error(path, "unsupported lang|'x'")


def test_parser_rejects_zero_cards(tmp_path: Path):
    path = _write_source(tmp_path, "English narration without a card.")
    _assert_source_error(path, "4.?6 cards|CARD")


def test_parser_rejects_seven_cards(tmp_path: Path):
    path = _write_source(tmp_path, "\n".join(_card(i) for i in range(1, 8)))
    _assert_source_error(path, r"4-6.*CARD|found 7")


@pytest.mark.parametrize(
    ("first", "match"),
    [
        (
            """[CARD]
TITLE: Front
IMG: Front image
Narration.
SHOW: Visible body
""",
            "SIDE",
        ),
        (
            """[CARD]
TITLE: Front
IMG: Front image
Narration.
SHOW: Visible body
[SIDE]
TITLE: Back
IMG: Back image
Narration.
SHOW: Visible body
[SIDE]
TITLE: Third side
IMG: Third image
Narration.
SHOW: Visible body
""",
            "SIDE",
        ),
    ],
    ids=["zero-side-markers", "two-side-markers"],
)
def test_parser_requires_exactly_one_side_marker_per_card(
    tmp_path: Path, first: str, match: str,
):
    path = _write_source(tmp_path, _four_cards(first=first))
    _assert_source_error(path, match)


@pytest.mark.parametrize(
    ("first", "match"),
    [
        (
            """[CARD]
IMG: Front image
Narration.
SHOW: Visible body
[SIDE]
TITLE: Back
IMG: Back image
Narration.
SHOW: Visible body
""",
            "TITLE",
        ),
        (
            """[CARD]
TITLE: Front
Narration.
SHOW: Visible body
[SIDE]
TITLE: Back
IMG: Back image
Narration.
SHOW: Visible body
""",
            "IMG",
        ),
        (
            """[CARD]
TITLE: Front
IMG: First image
IMG: Second image
Narration.
SHOW: Visible body
[SIDE]
TITLE: Back
IMG: Back image
Narration.
SHOW: Visible body
""",
            "IMG",
        ),
        (
            """[CARD]
TITLE: Front
IMG: Front image
Narration only.
[SIDE]
TITLE: Back
IMG: Back image
Narration.
SHOW: Visible body
""",
            "display|SHOW|TL",
        ),
        (
            """[CARD]
TITLE: Front
IMG: Front image
Narration.
SHOW: Visible body
TL-:
[SIDE]
TITLE: Back
IMG: Back image
Narration.
SHOW: Visible body
""",
            "empty TL",
        ),
    ],
    ids=["missing-title", "missing-image", "two-images", "no-body", "empty-tl-hidden"],
)
def test_parser_rejects_invalid_side_contract(
    tmp_path: Path, first: str, match: str,
):
    path = _write_source(tmp_path, _four_cards(first=first))
    _assert_source_error(path, match)


def test_side_html_escapes_text_applies_minimal_markup_and_preserves_order():
    side = pc.CardSide(
        seq=1,
        side="front",
        title="A & <title> **bold**",
        img_prompt="unused",
        segments=(Segment("speech", "Narrated.", "en", 1),),
        display=(
            pc.DisplayItem("show", "First & **strong**"),
            pc.DisplayItem("tl", "<ensuite> *italique*"),
            pc.DisplayItem("show", "Last"),
        ),
    )

    rendered = pc.side_html(side)

    expected = [
        '<div class="pc-title">A &amp; &lt;title&gt; <b>bold</b></div>',
        '<div class="pc-note">First &amp; <b>strong</b></div>',
        '<div class="pc-tl">&lt;ensuite&gt; <i>italique</i></div>',
        '<div class="pc-note">Last</div>',
    ]
    assert all(piece in rendered for piece in expected)
    assert [rendered.index(piece) for piece in expected] == sorted(
        rendered.index(piece) for piece in expected
    )
    assert "<title>" not in rendered


def test_podcast_model_identity_guid_and_frozen_fields():
    assert pc.MODEL_ID == 1_820_140_001
    assert pc.MODEL_ID != GRAMMAR_MODEL_ID
    assert pc.MODEL_NAME == "Idiomatic Podcast Lesson v1"
    assert pc.FIELDS == _FROZEN_FIELDS
    assert len(pc.FIELDS) == 14

    first = pc.podcast_card_guid("fr", "quantity-system", 1)
    repeated = pc.podcast_card_guid("fr", "quantity-system", 1)
    second = pc.podcast_card_guid("fr", "quantity-system", 2)
    assert first == repeated
    assert first != second
    assert first == hashlib.sha1(
        b"idiomatic-podcast-lesson::fr::quantity-system::1"
    ).hexdigest()[:16]


def _fake_assets(
    tmp_path: Path, script: pc.PodcastCardScript,
) -> tuple[pc.BuiltEpisode, set[str]]:
    assets: list[pc.BuiltSide] = []
    names: set[str] = set()
    for card in script.cards:
        for side in (card.front, card.back):
            marker = side.side[0]
            audio = tmp_path / f"idgpc_ep03_fr_c{card.seq}{marker}_{card.seq:011x}{marker}.mp3"
            image = tmp_path / f"idgpc_img_{card.seq:015x}{marker}.png"
            audio.write_bytes(b"fake mp3")
            image.write_bytes(b"fake png")
            names.update((audio.name, image.name))
            assets.append(pc.BuiltSide(
                side=side,
                audio_path=audio,
                image_path=image,
                duration_seconds=3.25,
            ))
    return pc.BuiltEpisode(script=script, sides=tuple(assets)), names


def test_apkg_build_packages_notes_fields_media_and_listening_subdeck(tmp_path: Path):
    script = pc.parse_podcast_cards(pc.SOURCE_DIR / "fr_quantity-system.md")
    episode, expected_media = _fake_assets(tmp_path, script)
    out = tmp_path / "podcast-lessons.apkg"

    count = pc.build_podcast_lessons_apkg(
        out_path=out,
        lang="fr",
        episodes=[episode],
    )

    assert count == 5
    with zipfile.ZipFile(out) as package:
        media_map = json.loads(package.read("media"))
        unpacked = tmp_path / "unpacked"
        package.extract("collection.anki2", unpacked)
    assert set(media_map.values()) == expected_media
    assert len(media_map) == len(expected_media)

    with sqlite3.connect(unpacked / "collection.anki2") as con:
        models = json.loads(con.execute("SELECT models FROM col").fetchone()[0])
        decks = json.loads(con.execute("SELECT decks FROM col").fetchone()[0])
        rows = con.execute("SELECT guid, flds, tags FROM notes ORDER BY sfld").fetchall()

    assert set(models) == {str(pc.MODEL_ID)}
    model = models[str(pc.MODEL_ID)]
    assert [field["name"] for field in model["flds"]] == _FROZEN_FIELDS
    assert len(model["tmpls"]) == 1
    assert model["tmpls"][0]["name"] == "Lesson"
    assert {deck["name"] for deck in decks.values()} >= {
        "Idiomatic Grammar FR::0 Écoute::03 Beaucoup de"
    }

    assert len(rows) == 5
    for expected_seq, (guid, field_blob, tags_blob) in enumerate(rows, 1):
        fields = dict(zip(_FROZEN_FIELDS, field_blob.split("\x1f"), strict=True))
        assert fields["LessonId"] == f"podcast:fr:quantity-system:{expected_seq}"
        assert fields["Episode"] == "3"
        assert fields["Seq"] == str(expected_seq)
        assert fields["Lang"] == "fr"
        assert fields["FrontAudio"].startswith("[sound:idgpc_ep03_fr_")
        assert fields["BackAudio"].startswith("[sound:idgpc_ep03_fr_")
        assert fields["FrontImage"].startswith('<img class="pc-img" src="idgpc_img_')
        assert fields["BackImage"].startswith('<img class="pc-img" src="idgpc_img_')
        assert "/" not in fields["FrontAudio"]
        assert "/" not in fields["BackAudio"]
        assert guid == pc.podcast_card_guid("fr", "quantity-system", expected_seq)
        assert set(tags_blob.split()) == {
            "idiomatic-podcast",
            "idiomatic-podcast::fr::quantity-system",
        }


def test_side_audio_filename_is_pure_and_maps_side_to_f_or_b():
    content_hash = "0123456789ab"
    front = pc.side_audio_filename(3, "fr", 1, "front", content_hash)
    assert front == "idgpc_ep03_fr_c1f_0123456789ab.mp3"
    assert pc.side_audio_filename(3, "fr", 1, "front", content_hash) == front
    assert (
        pc.side_audio_filename(3, "fr", 1, "back", content_hash)
        == "idgpc_ep03_fr_c1b_0123456789ab.mp3"
    )


def test_image_cache_key_is_pure_stable_and_sensitive_to_inputs():
    kwargs = {
        "model": "gemini-3-pro-image-preview",
        "aspect_ratio": "4:3",
    }
    first = pc.image_cache_key("Flat art", "A teal funnel", **kwargs)
    assert re.fullmatch(r"[0-9a-f]{16}", first)
    assert pc.image_cache_key("Flat art", "A teal funnel", **kwargs) == first
    assert pc.image_cache_key("Flat art", "A coral funnel", **kwargs) != first
    assert pc.image_cache_key(
        "Flat art", "A teal funnel", model=kwargs["model"], aspect_ratio="16:9"
    ) != first


@pytest.mark.asyncio
async def test_image_cache_skips_complete_file_but_regenerates_small_stub(tmp_path: Path):
    side = pc.CardSide(
        seq=1,
        side="front",
        title="Title",
        img_prompt="A teal funnel",
        segments=(Segment("speech", "Narration.", "en", 1),),
        display=(pc.DisplayItem("show", "Visible"),),
    )
    calls: list[tuple[str, Path, str]] = []

    async def fake_generate(prompt: str, *, out: Path, aspect_ratio: str = "4:3") -> None:
        calls.append((prompt, out, aspect_ratio))
        out.write_bytes(b"generated" * 1_300)

    kwargs = {
        "image_dir": tmp_path,
        "model": "fake-image-model",
        "generate_fn": fake_generate,
    }
    expected_key = pc.image_cache_key(
        "Flat art", side.img_prompt, model="fake-image-model", aspect_ratio="4:3"
    )
    expected = tmp_path / f"idgpc_img_{expected_key}.png"
    expected.write_bytes(b"cached" * 1_800)

    cached_path, generated = await pc.ensure_side_image(side, "Flat art", **kwargs)
    assert (cached_path, generated) == (expected, False)
    assert calls == []

    expected.write_bytes(b"small")
    regenerated_path, generated = await pc.ensure_side_image(side, "Flat art", **kwargs)
    assert (regenerated_path, generated) == (expected, True)
    assert calls == [(
        "Flat art. A teal funnel. No watermarks, no signature.",
        expected,
        "4:3",
    )]
    assert expected.stat().st_size > 10_000


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


class _FakeAsyncClient:
    responses: list[_FakeResponse] = []
    calls: list[dict] = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, **kwargs):
        type(self).calls.append({"url": url, **kwargs})
        return type(self).responses.pop(0)


def _image_response(data: bytes, *, inline_key: str = "inlineData") -> _FakeResponse:
    return _FakeResponse(
        200,
        {
            "candidates": [{
                "content": {
                    "parts": [
                        {"text": "ignored"},
                        {inline_key: {
                            "mimeType": "image/png",
                            "data": base64.b64encode(data).decode("ascii"),
                        }},
                    ]
                }
            }]
        },
    )


@pytest.fixture
def fake_image_http(monkeypatch):
    _FakeAsyncClient.responses = []
    _FakeAsyncClient.calls = []
    monkeypatch.setattr(gemini.httpx, "AsyncClient", _FakeAsyncClient)
    monkeypatch.setattr(
        gemini,
        "get_settings",
        lambda: SimpleNamespace(
            gemini_api_key="fake-key",
            gemini_image_model="fake-image-model",
        ),
    )
    return _FakeAsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize("inline_key", ["inlineData", "inline_data"])
async def test_generate_image_decodes_inline_image_and_writes_atomically(
    tmp_path: Path, fake_image_http, inline_key: str,
):
    data = b"\x89PNG\r\n\x1a\n" + b"image" * 2_100
    fake_image_http.responses = [_image_response(data, inline_key=inline_key)]
    out = tmp_path / "image.png"

    await gemini.generate_image("Draw it", out=out)

    assert out.read_bytes() == data
    assert not out.with_suffix(out.suffix + ".tmp").exists()
    assert len(fake_image_http.calls) == 1
    call = fake_image_http.calls[0]
    assert call["url"] == gemini._model_url("fake-image-model")
    assert call["params"] == {"key": "fake-key"}
    assert call["json"] == {
        "contents": [{"parts": [{"text": "Draw it"}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "4:3"},
        },
    }


@pytest.mark.asyncio
async def test_generate_image_rejects_undersized_payload(tmp_path: Path, fake_image_http):
    fake_image_http.responses = [_image_response(b"too small")]
    out = tmp_path / "image.png"

    with pytest.raises(RuntimeError, match="small|10.?000|image"):
        await gemini.generate_image("Draw it", out=out)

    assert not out.exists()


@pytest.mark.asyncio
async def test_generate_image_retries_one_400_without_image_config(
    tmp_path: Path, fake_image_http,
):
    data = b"\x89PNG\r\n\x1a\n" + b"image" * 2_100
    fake_image_http.responses = [
        _FakeResponse(400, text="unknown imageConfig"),
        _image_response(data),
    ]
    out = tmp_path / "image.png"

    await gemini.generate_image("Draw wide", out=out, aspect_ratio="16:9")

    assert out.read_bytes() == data
    assert len(fake_image_http.calls) == 2
    first = fake_image_http.calls[0]["json"]
    second = fake_image_http.calls[1]["json"]
    assert first["generationConfig"]["imageConfig"] == {"aspectRatio": "16:9"}
    assert "imageConfig" not in second["generationConfig"]
    assert second["generationConfig"]["responseModalities"] == ["IMAGE"]
