"""Authored grammar-walk lessons delivered as two-sided Anki notes.

Each source episode is split into short front/back listening chunks.  The
shared explainer renderer supplies routed narration and its persistent clip
cache; this module adds display markup, generated images, and a separate
frozen Anki model without changing the existing grammar decks.
"""

from __future__ import annotations

import asyncio
import hashlib
import html
import json
import re
import shutil
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import genanki
import structlog

from .. import db, gemini
from ..settings import get_settings
from . import apkg, explainers, podcasts
from .explainers import ExplainerScript, Segment, _segments, _WORD, render_explainer
from .podcasts import _lenient_frontmatter

log = structlog.get_logger()

SOURCE_DIR = Path(__file__).parent / "data" / "podcast_cards"
SUPPORTED_LANGS = frozenset({"de", "es", "fr", "it", "pt"})
DEFAULT_ASPECT_RATIO = "4:3"

MODEL_ID = 1_820_140_001
MODEL_NAME = "Idiomatic Podcast Lesson v1"
FIELDS = [
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

CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; background: #ffffff;
       color: #111; text-align: center; padding: 22px 14px;}
.pc-meta {font-size: clamp(12px, 2.7vw, 15px); color: #777;
          letter-spacing: 0.04em; margin-bottom: 14px;}
.pc-title {font-size: clamp(24px, 5vw, 36px); font-weight: 700;
           line-height: 1.25; margin: 12px auto; max-width: 680px;}
.pc-tl {font-size: clamp(24px, 5.5vw, 40px); color: #0a7;
        line-height: 1.35; margin: 12px auto; max-width: 680px;}
.pc-note {font-size: clamp(15px, 3.2vw, 20px); color: #666;
          line-height: 1.45; margin: 9px auto; max-width: 620px;}
.pc-img {max-width: 100%; height: auto; border-radius: 12px;
         margin: 10px auto 18px;}
/* Explicit night mode prevents AnkiDroid's heuristic whole-card inversion. */
.card.night_mode, .card.nightMode {background: #23272a; color: #e8e8e8;}
.card.night_mode .pc-meta, .card.nightMode .pc-meta {color: #999;}
.card.night_mode .pc-note, .card.nightMode .pc-note {color: #bbb;}
.card.night_mode .pc-tl, .card.nightMode .pc-tl {color: #20c997;}
"""

FRONT = """<div class="pc-meta">Ep {{Episode}} · {{Seq}} · {{Lang}}</div>
{{FrontImage}}
{{FrontHTML}}
{{FrontAudio}}"""

BACK = """<div class="pc-meta">Ep {{Episode}} · {{Seq}} · {{Lang}}</div>
{{BackImage}}
{{BackHTML}}
{{BackAudio}}"""


@dataclass(frozen=True)
class DisplayItem:
    kind: Literal["show", "tl"]
    text: str


@dataclass(frozen=True)
class CardSide:
    seq: int
    side: Literal["front", "back"]
    title: str
    img_prompt: str
    segments: tuple[Segment, ...]
    display: tuple[DisplayItem, ...]


@dataclass(frozen=True)
class LessonCard:
    seq: int
    front: CardSide
    back: CardSide


@dataclass(frozen=True)
class PodcastCardScript:
    path: Path
    lang: str
    slug: str
    episode: int
    title: str
    short_title: str
    img_style: str
    cards: tuple[LessonCard, ...]


@dataclass(frozen=True)
class BuiltSide:
    side: CardSide
    audio_path: Path
    image_path: Path
    duration_seconds: float


@dataclass(frozen=True)
class BuiltEpisode:
    script: PodcastCardScript
    sides: tuple[BuiltSide, ...]


class PodcastCardSourceError(ValueError):
    """A podcast-card Markdown source does not satisfy its contract."""


def _source_error(path: Path, line_no: int, message: str) -> PodcastCardSourceError:
    return PodcastCardSourceError(f"{path.name}: line {line_no}: {message}")


def _top_level_lines(lines: Sequence[str], *, first_line_no: int) -> dict[str, int]:
    result: dict[str, int] = {}
    for offset, line in enumerate(lines):
        if ":" not in line or line.startswith((" ", "-", "\t")):
            continue
        key = line.split(":", 1)[0].strip()
        result[key] = first_line_no + offset
    return result


def _metadata(
    path: Path, lines: list[str]
) -> tuple[dict[str, str], dict[str, int], int]:
    if not lines or lines[0].strip() != "---":
        raise _source_error(path, 1, "frontmatter must start with ---")
    try:
        closing = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise _source_error(path, 1, "frontmatter has no closing ---") from exc
    raw_lines = lines[1:closing]
    return (
        _lenient_frontmatter(list(raw_lines)),
        _top_level_lines(raw_lines, first_line_no=2),
        closing,
    )


def _required_text(
    path: Path, metadata: dict[str, str], line_numbers: dict[str, int], key: str
) -> str:
    value = metadata.get(key)
    if value is None:
        raise _source_error(path, 1, f"missing frontmatter field {key!r}")
    if not value.strip():
        raise _source_error(
            path, line_numbers.get(key, 1), f"{key} must be nonempty text"
        )
    return value.strip()


def _validate_metadata(
    path: Path, metadata: dict[str, str], line_numbers: dict[str, int]
) -> tuple[str, str, int, str, str, str]:
    series = _required_text(path, metadata, line_numbers, "series")
    if series != "grammar-walk-cards":
        raise _source_error(
            path, line_numbers.get("series", 1),
            "series must be 'grammar-walk-cards'",
        )

    episode_raw = _required_text(path, metadata, line_numbers, "episode")
    if not re.fullmatch(r"\d+", episode_raw) or int(episode_raw) < 1:
        raise _source_error(
            path, line_numbers.get("episode", 1),
            "episode must be an integer >= 1",
        )
    episode = int(episode_raw)

    lang = _required_text(path, metadata, line_numbers, "lang")
    if lang not in SUPPORTED_LANGS:
        raise _source_error(
            path, line_numbers.get("lang", 1),
            f"unsupported lang {lang!r}; expected de|es|fr|it|pt",
        )

    prefix = f"{lang}_"
    slug = path.stem[len(prefix):] if path.stem.startswith(prefix) else ""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise _source_error(path, line_numbers.get("lang", 1), f"invalid slug {slug!r}")
    if path.name != f"{lang}_{slug}.md":
        raise _source_error(
            path, line_numbers.get("lang", 1),
            f"filename must be {lang}_{slug}.md",
        )

    title = _required_text(path, metadata, line_numbers, "title")
    short_title = _required_text(path, metadata, line_numbers, "short_title")
    img_style = _required_text(path, metadata, line_numbers, "img_style")
    return lang, slug, episode, title, short_title, img_style


def _converted_segment_error(
    path: Path, exc: ValueError, *, fallback_line: int
) -> PodcastCardSourceError:
    message = str(exc)
    prefix = f"{path.name}: "
    if message.startswith(prefix):
        message = message[len(prefix):]
    if message.startswith("line "):
        return PodcastCardSourceError(f"{path.name}: {message}")
    return _source_error(path, fallback_line, message)


def _parse_side(
    path: Path,
    *,
    lang: str,
    seq: int,
    side: Literal["front", "back"],
    physical_lines: Sequence[tuple[int, str]],
) -> CardSide:
    fallback_line = physical_lines[0][0] if physical_lines else 1
    nonblank = [(line_no, raw.strip()) for line_no, raw in physical_lines if raw.strip()]
    if not nonblank:
        raise _source_error(path, fallback_line, f"card {seq} {side} is empty")
    if not nonblank[0][1].startswith("TITLE:"):
        raise _source_error(
            path, nonblank[0][0],
            f"card {seq} {side} must start with TITLE:",
        )

    titles = [(line_no, line[6:].strip()) for line_no, line in nonblank
              if line.startswith("TITLE:")]
    if len(titles) != 1:
        raise _source_error(
            path, titles[1][0] if len(titles) > 1 else fallback_line,
            f"card {seq} {side} expected exactly one TITLE:, found {len(titles)}",
        )
    title_line, title = titles[0]
    if not title:
        raise _source_error(path, title_line, "TITLE: must be nonempty")

    images = [(line_no, line[4:].strip()) for line_no, line in nonblank
              if line.startswith("IMG:")]
    if len(images) != 1:
        raise _source_error(
            path, images[1][0] if len(images) > 1 else fallback_line,
            f"card {seq} {side} expected exactly one IMG:, found {len(images)}",
        )
    image_line, img_prompt = images[0]
    if not img_prompt:
        raise _source_error(path, image_line, "IMG: must be nonempty")

    display: list[DisplayItem] = []
    spoken_lines: list[str] = []
    for line_no, raw in physical_lines:
        line = raw.strip()
        if line.startswith(("TITLE:", "IMG:")):
            spoken_lines.append("")
        elif line.startswith("SHOW:"):
            text = line[5:].strip()
            if not text:
                raise _source_error(path, line_no, "SHOW: must be nonempty")
            display.append(DisplayItem("show", text))
            spoken_lines.append("")
        elif line.startswith("TL-:"):
            text = line[4:].strip()
            if not text:
                raise _source_error(path, line_no, "empty TL- segment")
            spoken_lines.append(f"TL: {text}")
        elif line.startswith("TL:"):
            text = line[3:].strip()
            if not text:
                raise _source_error(path, line_no, "empty TL segment")
            display.append(DisplayItem("tl", text))
            spoken_lines.append(f"TL: {text}")
        else:
            spoken_lines.append(raw)

    if not display:
        raise _source_error(
            path, fallback_line,
            f"card {seq} {side} needs a displayed TL: or SHOW: item",
        )

    first_line_no = physical_lines[0][0] - 1 if physical_lines else fallback_line - 1
    try:
        segments = _segments(
            ["## SCRIPT", *spoken_lines],
            path=path,
            lang=lang,
            first_line_no=first_line_no,
        )
    except ValueError as exc:
        raise _converted_segment_error(
            path, exc, fallback_line=fallback_line
        ) from exc
    if not any(segment.kind == "speech" for segment in segments):
        raise _source_error(
            path, fallback_line, f"card {seq} {side} has no spoken segment"
        )
    return CardSide(
        seq=seq,
        side=side,
        title=title,
        img_prompt=img_prompt,
        segments=segments,
        display=tuple(display),
    )


def _parse_cards(
    path: Path, lines: list[str], *, closing: int, lang: str
) -> tuple[LessonCard, ...]:
    body_start = closing + 1
    body = lines[body_start:]
    headings = [offset for offset, line in enumerate(body)
                if line.strip() == "## SCRIPT"]
    if len(headings) != 1:
        line_no = body_start + 1
        if len(headings) > 1:
            line_no = body_start + headings[1] + 1
        raise _source_error(
            path, line_no,
            f"expected exactly one ## SCRIPT heading, found {len(headings)}",
        )
    heading = headings[0]
    for offset, line in enumerate(body[:heading]):
        if line.strip():
            raise _source_error(
                path, body_start + offset + 1,
                "content before ## SCRIPT is not allowed",
            )

    script_lines = body[heading + 1:]
    script_first_line = body_start + heading + 2
    card_markers = [offset for offset, line in enumerate(script_lines)
                    if line.strip() == "[CARD]"]
    if not 4 <= len(card_markers) <= 6:
        line_no = (
            script_first_line + card_markers[6]
            if len(card_markers) > 6 else body_start + heading + 1
        )
        raise _source_error(
            path, line_no, f"expected 4-6 [CARD] markers, found {len(card_markers)}"
        )

    for offset, line in enumerate(script_lines[:card_markers[0]]):
        if line.strip():
            raise _source_error(
                path, script_first_line + offset,
                "content before the first [CARD] is not allowed",
            )

    cards: list[LessonCard] = []
    boundaries = [*card_markers, len(script_lines)]
    for seq, (marker, end) in enumerate(zip(boundaries, boundaries[1:]), 1):
        content = script_lines[marker + 1:end]
        content_first_line = script_first_line + marker + 1
        side_markers = [offset for offset, line in enumerate(content)
                        if line.strip() == "[SIDE]"]
        if len(side_markers) != 1:
            line_no = (
                content_first_line + side_markers[1]
                if len(side_markers) > 1 else script_first_line + marker
            )
            raise _source_error(
                path, line_no,
                f"card {seq} expected exactly one [SIDE], found {len(side_markers)}",
            )
        divider = side_markers[0]
        front_lines = [
            (content_first_line + offset, line)
            for offset, line in enumerate(content[:divider])
        ]
        back_lines = [
            (content_first_line + offset, line)
            for offset, line in enumerate(content[divider + 1:], divider + 1)
        ]
        front = _parse_side(
            path, lang=lang, seq=seq, side="front", physical_lines=front_lines
        )
        back = _parse_side(
            path, lang=lang, seq=seq, side="back", physical_lines=back_lines
        )
        cards.append(LessonCard(seq, front, back))
    return tuple(cards)


def parse_podcast_cards(path: Path) -> PodcastCardScript:
    """Parse one authored episode into validated cards and routed segments."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata, line_numbers, closing = _metadata(path, lines)
    lang, slug, episode, title, short_title, img_style = _validate_metadata(
        path, metadata, line_numbers
    )
    cards = _parse_cards(path, lines, closing=closing, lang=lang)
    return PodcastCardScript(
        path=path,
        lang=lang,
        slug=slug,
        episode=episode,
        title=title,
        short_title=short_title,
        img_style=img_style,
        cards=cards,
    )


def load_card_scripts(
    lang: str, *, source_dir: Path | None = None
) -> list[PodcastCardScript]:
    """Load one language's sources, rejecting duplicate episode numbers."""
    if lang not in SUPPORTED_LANGS:
        raise ValueError("lang must be de|es|fr|it|pt")
    root = Path(source_dir) if source_dir is not None else SOURCE_DIR
    scripts = [parse_podcast_cards(path) for path in sorted(root.glob(f"{lang}_*.md"))]
    seen: dict[tuple[str, int], PodcastCardScript] = {}
    for script in scripts:
        identity = (script.lang, script.episode)
        if identity in seen:
            raise _source_error(
                script.path, 1,
                f"duplicate (lang, episode) source {identity!r}",
            )
        seen[identity] = script
    return scripts


_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"\*(.+?)\*")


def _inline_markup(text: str) -> str:
    escaped = html.escape(text)
    escaped = _BOLD.sub(r"<b>\1</b>", escaped)
    return _ITALIC.sub(r"<i>\1</i>", escaped)


def side_html(side: CardSide) -> str:
    """Render the deliberately small display-markup subset for one side."""
    parts = [f'<div class="pc-title">{_inline_markup(side.title)}</div>']
    for item in side.display:
        css_class = "pc-tl" if item.kind == "tl" else "pc-note"
        parts.append(f'<div class="{css_class}">{_inline_markup(item.text)}</div>')
    return "\n".join(parts)


def podcast_card_guid(lang: str, slug: str, seq: int) -> str:
    return hashlib.sha1(
        f"idiomatic-podcast-lesson::{lang}::{slug}::{seq}".encode("utf-8")
    ).hexdigest()[:16]


def side_audio_filename(
    episode: int,
    lang: str,
    card_seq: int,
    side: Literal["front", "back", "f", "b"],
    content_hash: str,
) -> str:
    if side not in ("front", "back", "f", "b"):
        raise ValueError("side must be front|back")
    if not re.fullmatch(r"[0-9a-f]{12}", content_hash):
        raise ValueError("content_hash must be 12 lowercase hex characters")
    marker = "f" if side in ("front", "f") else "b"
    return f"idgpc_ep{episode:02d}_{lang}_c{card_seq}{marker}_{content_hash}.mp3"


def full_image_prompt(img_style: str, img_prompt: str) -> str:
    return f"{img_style}. {img_prompt}. No watermarks, no signature."


def image_cache_key(
    img_style: str,
    img_prompt: str,
    *,
    model: str,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
) -> str:
    payload = {
        "model": model,
        "aspect": aspect_ratio,
        "full_prompt": full_image_prompt(img_style, img_prompt),
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]


async def ensure_side_image(
    side: CardSide,
    img_style: str,
    *,
    image_dir: Path,
    model: str,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    generate_fn: Callable[..., Awaitable[None]] | None = None,
) -> tuple[Path, bool]:
    """Return one cached/generated side image and whether it was generated."""
    image_dir = Path(image_dir)
    key = image_cache_key(
        img_style, side.img_prompt, model=model, aspect_ratio=aspect_ratio
    )
    out = image_dir / f"idgpc_img_{key}.png"
    if out.exists() and out.stat().st_size > 10_000:
        return out, False
    image_dir.mkdir(parents=True, exist_ok=True)
    generate_fn = generate_fn or gemini.generate_image
    await generate_fn(
        full_image_prompt(img_style, side.img_prompt),
        out=out,
        aspect_ratio=aspect_ratio,
    )
    if not out.exists() or out.stat().st_size <= 10_000:
        raise RuntimeError(f"image generation produced an undersized file: {out}")
    return out, True


def _side_script(script: PodcastCardScript, side: CardSide) -> ExplainerScript:
    return ExplainerScript(
        path=script.path,
        lang=script.lang,
        slug=script.slug,
        title=side.title,
        takeaway="",
        fossil_evidence=(),
        est_seconds=180,
        segments=side.segments,
        word_count=sum(
            len(_WORD.findall(segment.text))
            for segment in side.segments
            if segment.kind == "speech"
        ),
    )


async def _copy_audio(source: Path, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)

    def copy() -> None:
        temporary = destination.with_name(f".{destination.name}.building")
        temporary.unlink(missing_ok=True)
        try:
            shutil.copyfile(source, temporary)
            temporary.replace(destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    await asyncio.to_thread(copy)


async def _render_side_audio(
    script: PodcastCardScript,
    side: CardSide,
    *,
    settings: Any,
    render_fn: Callable[..., Awaitable[Any]] | None = None,
) -> tuple[Path, float]:
    render_fn = render_fn or render_explainer
    rendered = await render_fn(
        _side_script(script, side),
        stage_dir=podcasts.podcast_stage_dir(),
        settings=settings,
    )
    match = re.search(r"_([0-9a-f]{12})\.mp3$", rendered.media_filename)
    if match is None:
        raise RuntimeError(
            f"rendered side has an unexpected filename: {rendered.media_filename}"
        )
    filename = side_audio_filename(
        script.episode, script.lang, side.seq, side.side, match.group(1)
    )
    destination = (
        Path(settings.data_dir) / "staged_audio" / "grammar" / "podcast_cards"
        / filename
    )
    await _copy_audio(Path(rendered.path), destination)
    return destination, float(rendered.duration_seconds)


def _ordered_sides(script: PodcastCardScript) -> tuple[CardSide, ...]:
    return tuple(side for card in script.cards for side in (card.front, card.back))


async def _build_episode_assets(
    script: PodcastCardScript,
    *,
    settings: Any,
    render_fn: Callable[..., Awaitable[Any]] | None = None,
    generate_fn: Callable[..., Awaitable[None]] | None = None,
) -> tuple[BuiltEpisode, int, int]:
    sides = _ordered_sides(script)
    audio: list[tuple[Path, float]] = []
    for side in sides:
        audio.append(
            await _render_side_audio(
                script, side, settings=settings, render_fn=render_fn
            )
        )

    image_dir = (
        Path(settings.data_dir) / "staged_audio" / "grammar" / "podcasts" / "images"
    )
    image_results = await asyncio.gather(*(
        ensure_side_image(
            side,
            script.img_style,
            image_dir=image_dir,
            model=settings.gemini_image_model,
            generate_fn=generate_fn,
        )
        for side in sides
    ))
    built_sides = tuple(
        BuiltSide(
            side=side,
            audio_path=audio_result[0],
            image_path=image_result[0],
            duration_seconds=audio_result[1],
        )
        for side, audio_result, image_result in zip(
            sides, audio, image_results, strict=True
        )
    )
    generated = sum(was_generated for _path, was_generated in image_results)
    return BuiltEpisode(script, built_sides), generated, len(sides) - generated


def make_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        MODEL_NAME,
        fields=[{"name": name} for name in FIELDS],
        templates=[{"name": "Lesson", "qfmt": FRONT, "afmt": BACK}],
        css=CSS,
    )


def episode_deck_name(script: PodcastCardScript) -> str:
    unit = explainers.EXPLAINER_UNITS[script.lang]
    return (
        apkg.deck_name_for(script.lang, unit.cluster)
        + f"::{script.episode:02d} {script.short_title}"
    )


def build_podcast_lessons_apkg(
    *, out_path: Path, lang: str, episodes: list[BuiltEpisode]
) -> int:
    """Build all staged podcast lessons for one language into one APKG."""
    model = make_model()
    decks: dict[str, genanki.Deck] = {}
    media: list[str] = []
    media_seen: set[str] = set()
    note_count = 0

    for episode in sorted(
        episodes, key=lambda built: (built.script.episode, built.script.slug)
    ):
        script = episode.script
        if script.lang != lang:
            raise ValueError(
                f"episode {script.episode} lang {script.lang!r} does not match {lang!r}"
            )
        deck_name = episode_deck_name(script)
        deck = decks.get(deck_name)
        if deck is None:
            deck = decks[deck_name] = genanki.Deck(apkg._deck_id(deck_name), deck_name)
        sides = {(built.side.seq, built.side.side): built for built in episode.sides}
        if len(sides) != len(episode.sides):
            raise ValueError(f"episode {script.episode} has duplicate built sides")

        for card in script.cards:
            try:
                front = sides[(card.seq, "front")]
                back = sides[(card.seq, "back")]
            except KeyError as exc:
                raise ValueError(
                    f"episode {script.episode} card {card.seq} is missing staged media"
                ) from exc
            for built in (front, back):
                for media_path in (built.audio_path, built.image_path):
                    media_path = Path(media_path)
                    if not media_path.exists() or media_path.stat().st_size <= 0:
                        raise ValueError(f"missing podcast lesson media: {media_path}")
                    key = str(media_path.resolve())
                    if key not in media_seen:
                        media.append(str(media_path))
                        media_seen.add(key)

            front_audio = f"[sound:{front.audio_path.name}]"
            back_audio = f"[sound:{back.audio_path.name}]"
            front_image = f'<img class="pc-img" src="{front.image_path.name}">'
            back_image = f'<img class="pc-img" src="{back.image_path.name}">'
            deck.add_note(genanki.Note(
                model=model,
                fields=[
                    f"podcast:{lang}:{script.slug}:{card.seq}",
                    str(script.episode),
                    str(card.seq),
                    lang,
                    side_html(card.front),
                    side_html(card.back),
                    front_audio,
                    back_audio,
                    front_image,
                    back_image,
                    "", "", "", "",
                ],
                guid=podcast_card_guid(lang, script.slug, card.seq),
                tags=[
                    "idiomatic-podcast",
                    f"idiomatic-podcast::{lang}::{script.slug}",
                ],
            ))
            note_count += 1

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(sorted(decks.values(), key=lambda deck: deck.name))
    package.media_files = media
    package.write_to_file(str(out_path))
    log.info(
        "grammar.podcast_cards.apkg_written",
        path=str(out_path),
        n=note_count,
        decks=len(decks),
        size_kb=round(out_path.stat().st_size / 1e3),
    )
    return note_count


async def build_episode(lang: str, episode: int) -> dict[str, Any]:
    """Build one requested episode, then repackage every episode for its lang."""
    if lang not in SUPPORTED_LANGS:
        raise ValueError("lang must be de|es|fr|it|pt")
    if isinstance(episode, bool) or not isinstance(episode, int) or episode < 1:
        raise ValueError("episode must be an integer >= 1")
    scripts = load_card_scripts(lang)
    selected = next((script for script in scripts if script.episode == episode), None)
    if selected is None:
        raise ValueError(f"no podcast-card source for {lang} episode {episode}")

    settings = get_settings()
    requested, new_images, cached_images = await _build_episode_assets(
        selected, settings=settings
    )

    built_episodes: list[BuiltEpisode] = []
    for script in scripts:
        built, _new, _cached = await _build_episode_assets(script, settings=settings)
        built_episodes.append(built)

    apkg_root = Path(settings.data_dir) / "apkgs" / lang
    apkg_root.mkdir(parents=True, exist_ok=True)
    out = apkg_root / "_podcast_lessons.apkg"
    note_count = await asyncio.to_thread(
        build_podcast_lessons_apkg,
        out_path=out,
        lang=lang,
        episodes=built_episodes,
    )
    relative = out.relative_to(Path(settings.data_dir))
    apkg_id = await db.upsert_pool_apkg(
        lang=lang,
        kind="podcast_lesson",
        filename=str(relative),
        size_bytes=out.stat().st_size,
        n_idioms=note_count,
    )
    durations = [round(side.duration_seconds, 3) for side in requested.sides]
    result = {
        "lang": lang,
        "episode": episode,
        "cards": len(selected.cards),
        "sides": len(requested.sides),
        "new_images": new_images,
        "cached_images": cached_images,
        "side_durations_s": durations,
        "total_minutes": round(sum(durations) / 60, 2),
        "apkg_id": apkg_id,
        "deck": episode_deck_name(selected),
    }
    log.info("grammar.podcast_cards.built", **result)
    return result


def _has_staged_audio(script: PodcastCardScript, side: CardSide, root: Path) -> bool:
    marker = "f" if side.side == "front" else "b"
    pattern = f"idgpc_ep{script.episode:02d}_{script.lang}_c{side.seq}{marker}_*.mp3"
    return any(path.stat().st_size > 0 for path in root.glob(pattern) if path.is_file())


def list_episode_sources() -> list[dict[str, Any]]:
    """List authored sources with counts of already staged side assets."""
    settings = get_settings()
    data_root = Path(settings.data_dir)
    audio_dir = data_root / "staged_audio" / "grammar" / "podcast_cards"
    image_dir = data_root / "staged_audio" / "grammar" / "podcasts" / "images"
    rows: list[dict[str, Any]] = []
    for lang in sorted(SUPPORTED_LANGS):
        for script in load_card_scripts(lang):
            sides = _ordered_sides(script)
            staged_audio = sum(
                _has_staged_audio(script, side, audio_dir) for side in sides
            )
            staged_images = 0
            for side in sides:
                key = image_cache_key(
                    script.img_style,
                    side.img_prompt,
                    model=settings.gemini_image_model,
                )
                path = image_dir / f"idgpc_img_{key}.png"
                staged_images += bool(path.exists() and path.stat().st_size > 10_000)
            rows.append({
                "lang": script.lang,
                "episode": script.episode,
                "slug": script.slug,
                "title": script.title,
                "cards": len(script.cards),
                "staged_audio": staged_audio,
                "staged_images": staged_images,
            })
    return sorted(rows, key=lambda row: (row["lang"], row["episode"]))
