"""Exercises 2.0: rich EN→TL discourse/usage notes as a rolling deck.

Content lives in the repo as reviewed JSON files under
``data/exercises2/notes/<lang>_<topic>.json`` (codex-authored against a
commission, audited before merge — see docs/research/legacy-excercises-audit.md
and docs/commissions/EXERCISES2_PILOT_COMMISSION.md).  This module validates
those files, synthesizes cached per-note TTS through the shared provider
chain, and packages one rolling APKG per language delivered through the
standard add-on path.

Model rules: the model is FROZEN — never change field count/order/names or
template count of MODEL_ID (docs/research/ankidroid-tech.md).  Extra1..Extra3
are spares.  GUIDs derive from (lang, topic, item id), so re-authored content
updates fields in place and preserves scheduling.
"""

from __future__ import annotations

import asyncio
import hashlib
import html
import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import genanki
import structlog

from .. import db, gemini
from ..anki_tree import anki_root
from ..pipeline.audio import LANG_VOICE
from ..settings import get_settings
from .explainers import VoiceRoute, _voice_fingerprint, leveled_speech_clip

log = structlog.get_logger()

SOURCE_DIR = Path(__file__).parent / "data" / "exercises2" / "notes"
SUPPORTED_LANGS = frozenset({"de", "es", "fr", "it", "pt"})

MODEL_ID = 1_820_150_001
MODEL_NAME = "Idiomatic Exercises v1"
FIELDS = [
    "ItemId",
    "Lang",
    "Topic",
    "Category",
    "EN",
    "TL",
    "Alts",
    "Register",
    "Trap",
    "ExampleTL",     # example sentence, connector wrapped in <mark>
    "ExampleEN",
    "ClozeFront",    # example sentence, connector replaced by a blank
    "AudioTL",       # [sound:] — the TL answer
    "AudioExample",  # [sound:] — the full TL example sentence
    "Extra1",
    "Extra2",
    "Extra3",
]

CATEGORIES = frozenset({
    "result", "concession", "contrast", "condition", "reformulation",
    "generalization", "stance", "structuring", "addition",
    # sentence-level conditional types (CONDITIONALS topic, 2026-08-04)
    "real-condition", "counterfactual", "mixed-condition", "habitual",
})

# Deck label per (topic, lang); unlisted combinations fall back to the
# title-cased topic slug.  Labels are learner-facing deck names — keep stable.
TOPIC_LABELS = {
    ("connecting", "es"): "Conectores",
    ("connecting", "pt"): "Conectores",
    ("connecting", "fr"): "Connecteurs",
    ("connecting", "it"): "Connettivi",
    ("connecting", "de"): "Konnektoren",
    ("conditionals", "es"): "Condicionales",
    ("conditionals", "pt"): "Condicionais",
    ("conditionals", "fr"): "Conditionnels",
    ("conditionals", "it"): "Periodo ipotetico",
    ("conditionals", "de"): "Konditionalsätze",
}

CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; background: #f6f6f3;
       color: #1f2023; text-align: center; padding: 24px 16px;}
.x2-meta {font-size: clamp(11px, 2.5vw, 14px); color: #6c6d66;
          letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 16px;}
.x2-en {font-family: Georgia, 'Times New Roman', serif;
        font-size: clamp(22px, 5vw, 32px); line-height: 1.3;
        margin: 10px auto; max-width: 640px;}
.x2-tl {font-family: Georgia, 'Times New Roman', serif;
        font-size: clamp(26px, 6vw, 38px); color: #9e2b33;
        line-height: 1.3; margin: 14px auto 6px; max-width: 640px;}
.x2-alts {font-size: clamp(13px, 3vw, 16px); color: #6c6d66; margin: 4px auto 10px;}
.x2-alts span {display: inline-block; border: 1px solid #e1e1d8; border-radius: 999px;
               padding: 1px 10px; margin: 2px 3px; color: #1f2023;}
.x2-register {font-size: clamp(13px, 3vw, 16px); color: #6c6d66;
              margin: 10px auto; max-width: 600px;}
.x2-trap {font-size: clamp(13px, 3vw, 16px); color: #1f2023; margin: 12px auto;
          max-width: 580px; text-align: left; background: #f5eedd;
          border-left: 3px solid #8c6a1d; border-radius: 0 8px 8px 0;
          padding: 8px 12px;}
.x2-example {font-family: Georgia, 'Times New Roman', serif;
             font-size: clamp(17px, 4vw, 23px); line-height: 1.5;
             margin: 14px auto 4px; max-width: 620px;}
.x2-example mark {background: #f4dfe0; color: inherit; padding: 0 3px;
                  border-radius: 3px;}
.x2-example-en {font-size: clamp(13px, 3vw, 17px); color: #6c6d66;
                margin: 4px auto 0; max-width: 600px;}
.x2-cloze {font-family: Georgia, 'Times New Roman', serif;
           font-size: clamp(19px, 4.5vw, 26px); line-height: 1.55;
           margin: 12px auto; max-width: 620px;}
.x2-cloze .blank {display: inline-block; min-width: 3.2em;
                  border-bottom: 2px solid #9e2b33; height: 0.85em;}
.x2-hint {font-size: clamp(13px, 3vw, 17px); color: #6c6d66; margin-top: 14px;}
hr#answer {border: 0; border-top: 1px solid #e1e1d8; margin: 18px 0;}
/* Explicit night mode prevents AnkiDroid's heuristic whole-card inversion. */
.card.night_mode, .card.nightMode {background: #1b1a19; color: #edeae4;}
.card.night_mode .x2-meta, .card.nightMode .x2-meta {color: #9b978e;}
.card.night_mode .x2-tl, .card.nightMode .x2-tl {color: #d98f94;}
.card.night_mode .x2-alts, .card.nightMode .x2-alts {color: #9b978e;}
.card.night_mode .x2-alts span, .card.nightMode .x2-alts span
  {border-color: #343230; color: #edeae4;}
.card.night_mode .x2-register, .card.nightMode .x2-register {color: #9b978e;}
.card.night_mode .x2-trap, .card.nightMode .x2-trap
  {background: #2e2919; border-left-color: #d4b35b; color: #edeae4;}
.card.night_mode .x2-example mark, .card.nightMode .x2-example mark
  {background: #4a3032;}
.card.night_mode .x2-example-en, .card.nightMode .x2-example-en {color: #9b978e;}
.card.night_mode .x2-cloze .blank, .card.nightMode .x2-cloze .blank
  {border-bottom-color: #d98f94;}
.card.night_mode .x2-hint, .card.nightMode .x2-hint {color: #9b978e;}
.card.night_mode hr#answer, .card.nightMode hr#answer {border-top-color: #343230;}
"""

PRODUCTION_FRONT = """<div class="x2-meta">{{Topic}} · {{Category}}</div>
<div class="x2-en">{{EN}}</div>
<div class="x2-hint">→ {{Lang}}</div>"""

PRODUCTION_BACK = """<div class="x2-meta">{{Topic}} · {{Category}}</div>
<div class="x2-tl">{{TL}}</div>
{{AudioTL}}
{{#Alts}}<div class="x2-alts">{{Alts}}</div>{{/Alts}}
<div class="x2-register">{{Register}}</div>
{{#Trap}}<div class="x2-trap">{{Trap}}</div>{{/Trap}}
<hr id="answer">
<div class="x2-example">{{ExampleTL}}</div>
{{AudioExample}}
<div class="x2-example-en">{{ExampleEN}}</div>"""

CLOZE_FRONT = """<div class="x2-meta">{{Topic}} · {{Category}}</div>
<div class="x2-cloze">{{ClozeFront}}</div>
<div class="x2-hint">{{EN}}</div>"""

CLOZE_BACK = """<div class="x2-meta">{{Topic}} · {{Category}}</div>
<div class="x2-example">{{ExampleTL}}</div>
{{AudioExample}}
<div class="x2-tl">{{TL}}</div>
{{#Alts}}<div class="x2-alts">{{Alts}}</div>{{/Alts}}
<hr id="answer">
<div class="x2-example-en">{{ExampleEN}}</div>"""

_CLOZE_SPAN = re.compile(r"\{\{c1::(.*?)\}\}", re.DOTALL)


@dataclass(frozen=True)
class Ex2Note:
    lang: str
    topic: str
    item_id: str
    en: str
    tl: str
    alts: tuple[str, ...]
    category: str
    register: str
    trap: str
    example_en: str
    cloze: str  # example sentence with {{c1::…}} around the connector

    @property
    def example_tl(self) -> str:
        return _CLOZE_SPAN.sub(lambda m: m.group(1), self.cloze)


class Ex2SourceError(ValueError):
    """An exercises2 notes file does not satisfy its contract."""


def _note_error(path: Path, item_id: str, message: str) -> Ex2SourceError:
    return Ex2SourceError(f"{path.name}: {item_id or '<missing id>'}: {message}")


def _text(path: Path, raw: dict, item_id: str, key: str, *,
          required: bool = True) -> str:
    value = raw.get(key, "")
    if not isinstance(value, str):
        raise _note_error(path, item_id, f"{key} must be a string")
    value = value.strip()
    if required and not value:
        raise _note_error(path, item_id, f"{key} must be nonempty")
    return value


def _parse_note(path: Path, lang: str, topic: str, raw: dict) -> Ex2Note:
    if not isinstance(raw, dict):
        raise Ex2SourceError(f"{path.name}: every item must be an object")
    item_id = str(raw.get("id", "")).strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_\-]*", item_id):
        raise Ex2SourceError(f"{path.name}: invalid or missing item id {item_id!r}")

    # The ES pilot predates the generalized key names; accept both spellings.
    tl_key = "tl" if "tl" in raw else f"{lang}_main"
    alts_key = "alts" if "alts" in raw else f"{lang}_alts"
    example_key = "example_tl" if "example_tl" in raw else f"example_{lang}"

    category = _text(path, raw, item_id, "category")
    if category not in CATEGORIES:
        raise _note_error(path, item_id, f"unknown category {category!r}")
    alts_raw = raw.get(alts_key, [])
    if not isinstance(alts_raw, list) or any(
        not isinstance(alt, str) or not alt.strip() for alt in alts_raw
    ):
        raise _note_error(path, item_id, f"{alts_key} must be a list of nonempty strings")

    cloze = _text(path, raw, item_id, "cloze")
    spans = _CLOZE_SPAN.findall(cloze)
    if not spans or any(not span.strip() for span in spans):
        raise _note_error(path, item_id, "cloze needs at least one nonempty {{c1::…}}")
    example_tl = _text(path, raw, item_id, example_key)
    if _CLOZE_SPAN.sub(lambda m: m.group(1), cloze) != example_tl:
        raise _note_error(
            path, item_id,
            f"cloze does not reduce to {example_key} when unwrapped",
        )

    return Ex2Note(
        lang=lang,
        topic=topic,
        item_id=item_id,
        en=_text(path, raw, item_id, "en"),
        tl=_text(path, raw, item_id, tl_key),
        alts=tuple(alt.strip() for alt in alts_raw),
        category=category,
        register=_text(path, raw, item_id, "register"),
        trap=_text(path, raw, item_id, "trap", required=False),
        example_en=_text(path, raw, item_id, "example_en"),
        cloze=cloze,
    )


def parse_notes_file(path: Path) -> list[Ex2Note]:
    """Parse one `<lang>_<topic>.json` notes file with full validation."""
    path = Path(path)
    match = re.fullmatch(r"([a-z]{2})_([a-z0-9]+(?:_[a-z0-9]+)*)\.json", path.name)
    if match is None or match.group(1) not in SUPPORTED_LANGS:
        raise Ex2SourceError(f"{path.name}: filename must be <lang>_<topic>.json")
    lang, topic = match.group(1), match.group(2)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise Ex2SourceError(f"{path.name}: expected a nonempty JSON array")
    notes = [_parse_note(path, lang, topic, raw) for raw in data]
    seen: set[str] = set()
    for note in notes:
        if note.item_id in seen:
            raise Ex2SourceError(f"{path.name}: duplicate item id {note.item_id!r}")
        seen.add(note.item_id)
    return notes


def load_notes(lang: str, *, source_dir: Path | None = None) -> list[Ex2Note]:
    if lang not in SUPPORTED_LANGS:
        raise ValueError("lang must be de|es|fr|it|pt")
    root = Path(source_dir) if source_dir is not None else SOURCE_DIR
    notes: list[Ex2Note] = []
    for path in sorted(root.glob(f"{lang}_*.json")):
        notes.extend(parse_notes_file(path))
    return notes


def exercises_guid(lang: str, topic: str, item_id: str) -> str:
    return hashlib.sha1(
        f"idiomatic-exercises::{lang}::{topic}::{item_id}".encode("utf-8")
    ).hexdigest()[:16]


def _deck_id(deck_name: str) -> int:
    """Stable id from the full deck name, in a range disjoint from the
    grammar/pool formulas."""
    return 1_920_000_000 + (
        int(hashlib.sha1(f"idiomatic-exercises::{deck_name}".encode()
                          ).hexdigest()[:8], 16) % 70_000_000
    )


def deck_name_for(lang: str, topic: str) -> str:
    label = TOPIC_LABELS.get((topic, lang), topic.replace("_", " ").title())
    return f"{anki_root(lang)}::4 Exercises::{label}"


def make_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        MODEL_NAME,
        fields=[{"name": name} for name in FIELDS],
        templates=[
            {"name": "Production", "qfmt": PRODUCTION_FRONT, "afmt": PRODUCTION_BACK},
            {"name": "Cloze", "qfmt": CLOZE_FRONT, "afmt": CLOZE_BACK},
        ],
        css=CSS,
    )


def example_tl_html(cloze: str) -> str:
    """Escaped example sentence with the connector spans wrapped in <mark>."""
    parts: list[str] = []
    cursor = 0
    for match in _CLOZE_SPAN.finditer(cloze):
        parts.append(html.escape(cloze[cursor:match.start()]))
        parts.append(f"<mark>{html.escape(match.group(1))}</mark>")
        cursor = match.end()
    parts.append(html.escape(cloze[cursor:]))
    return "".join(parts)


def cloze_front_html(cloze: str) -> str:
    """Escaped example sentence with the connector spans blanked."""
    parts: list[str] = []
    cursor = 0
    for match in _CLOZE_SPAN.finditer(cloze):
        parts.append(html.escape(cloze[cursor:match.start()]))
        parts.append('<span class="blank"></span>')
        cursor = match.end()
    parts.append(html.escape(cloze[cursor:]))
    return "".join(parts)


def alts_html(note: Ex2Note) -> str:
    if not note.alts:
        return ""
    return "".join(f"<span>{html.escape(alt)}</span>" for alt in note.alts)


def audio_cache_key(note_text: str, lang: str, settings: Any) -> str:
    route = VoiceRoute(lang, LANG_VOICE[lang])
    payload = {"route": _voice_fingerprint(route, settings), "text": note_text}
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]


def audio_filename(lang: str, digest: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{16}", digest):
        raise ValueError("digest must be 16 lowercase hex characters")
    return f"idx2_{lang}_{digest}.mp3"


@dataclass(frozen=True)
class NoteAudio:
    answer: Path | None
    example: Path | None


async def _synthesize_note_audio(
    notes: list[Ex2Note],
    *,
    lang: str,
    settings: Any,
    synthesize_fn: Callable[..., Awaitable[None]] | None = None,
    level_fn: Callable[[Path], Path] | None = None,
) -> tuple[dict[str, NoteAudio], int, int]:
    """Synthesize + level the two clips per note through the shared cache.

    A failed clip (silence marker) drops that one [sound:] tag rather than
    failing the language build — same resilience stance as the grammar deck.
    Returns (audio by item_id, synthesized count, failed count).
    """
    synthesize_fn = synthesize_fn or gemini.synthesize
    level_fn = level_fn or leveled_speech_clip
    work_dir = (
        Path(settings.data_dir) / "staged_audio" / "grammar" / "exercises2" / lang
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    voice = LANG_VOICE[lang]

    wanted: dict[str, tuple[str, str]] = {}  # item_id -> (answer text, example text)
    for note in notes:
        wanted[note.item_id] = (note.tl, note.example_tl)

    clip_paths: dict[str, Path] = {}
    pending: dict[Path, str] = {}
    for texts in wanted.values():
        for text in texts:
            digest = audio_cache_key(text, lang, settings)
            clip = work_dir / audio_filename(lang, digest)
            clip_paths[text] = clip
            if not (
                clip.exists() and clip.stat().st_size > 0
                and not gemini.silence_marker(clip).exists()
            ):
                pending[clip] = text

    await asyncio.gather(
        *(synthesize_fn(text, voice=voice, out=clip, lang=lang)
          for clip, text in pending.items())
    )

    usable: dict[str, Path] = {}
    failed = 0
    for text, clip in clip_paths.items():
        if (clip.exists() and clip.stat().st_size > 0
                and not gemini.silence_marker(clip).exists()):
            usable[text] = clip
        else:
            failed += 1
    leveled_list = await asyncio.gather(
        *(asyncio.to_thread(level_fn, clip) for clip in usable.values())
    )
    leveled = dict(zip(usable, leveled_list, strict=True))

    result = {
        item_id: NoteAudio(answer=leveled.get(answer), example=leveled.get(example))
        for item_id, (answer, example) in wanted.items()
    }
    return result, len(pending), failed


def build_exercises2_apkg(
    *, out_path: Path, lang: str, notes: list[Ex2Note],
    audio: dict[str, NoteAudio] | None = None,
) -> int:
    """Package one language's validated notes (2 cards each) into an APKG."""
    model = make_model()
    audio = audio or {}
    decks: dict[str, genanki.Deck] = {}
    media: list[str] = []
    media_seen: set[str] = set()

    for note in notes:
        if note.lang != lang:
            raise ValueError(f"note {note.item_id} lang {note.lang!r} != {lang!r}")
        deck_name = deck_name_for(lang, note.topic)
        deck = decks.get(deck_name)
        if deck is None:
            deck = decks[deck_name] = genanki.Deck(_deck_id(deck_name), deck_name)

        record = audio.get(note.item_id) or NoteAudio(None, None)
        sounds: list[str] = []
        for clip in (record.answer, record.example):
            if clip is None:
                sounds.append("")
                continue
            clip = Path(clip)
            if not clip.exists() or clip.stat().st_size <= 0:
                raise ValueError(f"missing exercises2 media: {clip}")
            sounds.append(f"[sound:{clip.name}]")
            key = str(clip.resolve())
            if key not in media_seen:
                media.append(str(clip))
                media_seen.add(key)

        label = TOPIC_LABELS.get((note.topic, lang),
                                 note.topic.replace("_", " ").title())
        deck.add_note(genanki.Note(
            model=model,
            fields=[
                f"{lang}:{note.topic}:{note.item_id}",
                lang,
                label,
                note.category,
                html.escape(note.en),
                html.escape(note.tl),
                alts_html(note),
                html.escape(note.register),
                html.escape(note.trap),
                example_tl_html(note.cloze),
                html.escape(note.example_en),
                cloze_front_html(note.cloze),
                sounds[0],
                sounds[1],
                "", "", "",
            ],
            guid=exercises_guid(lang, note.topic, note.item_id),
            tags=[
                "idiomatic-exercises",
                f"idiomatic-exercises::{lang}::{note.topic}",
            ],
        ))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(sorted(decks.values(), key=lambda deck: deck.name))
    package.media_files = media
    package.write_to_file(str(out_path))
    log.info(
        "grammar.exercises2.apkg_written",
        path=str(out_path), n=len(notes), decks=len(decks),
        size_kb=round(out_path.stat().st_size / 1e3),
    )
    return len(notes)


async def build_language(
    lang: str,
    *,
    synthesize_fn: Callable[..., Awaitable[None]] | None = None,
    level_fn: Callable[[Path], Path] | None = None,
) -> dict[str, Any]:
    """Build one language's exercises deck end to end and publish its row."""
    if lang not in SUPPORTED_LANGS:
        raise ValueError("lang must be de|es|fr|it|pt")
    notes = load_notes(lang)
    if not notes:
        raise ValueError(f"no exercises2 notes files for lang {lang!r}")
    settings = get_settings()
    audio, synthesized, failed = await _synthesize_note_audio(
        notes, lang=lang, settings=settings,
        synthesize_fn=synthesize_fn, level_fn=level_fn,
    )
    apkg_root = Path(settings.data_dir) / "apkgs" / lang
    apkg_root.mkdir(parents=True, exist_ok=True)
    out = apkg_root / "_exercises2.apkg"
    note_count = await asyncio.to_thread(
        build_exercises2_apkg, out_path=out, lang=lang, notes=notes, audio=audio,
    )
    relative = out.relative_to(Path(settings.data_dir))
    apkg_id = await db.upsert_pool_apkg(
        lang=lang,
        kind="exercises2",
        filename=str(relative),
        size_bytes=out.stat().st_size,
        n_idioms=note_count,
    )
    topics = sorted({note.topic for note in notes})
    result = {
        "lang": lang,
        "notes": note_count,
        "cards": note_count * 2,
        "topics": topics,
        "decks": [deck_name_for(lang, topic) for topic in topics],
        "clips_synthesized": synthesized,
        "clips_failed": failed,
        "apkg_id": apkg_id,
    }
    log.info("grammar.exercises2.built", **result)
    return result


def list_sources() -> list[dict[str, Any]]:
    """List notes files with validation state — the admin inventory view."""
    rows: list[dict[str, Any]] = []
    for path in sorted(SOURCE_DIR.glob("*_*.json")):
        row: dict[str, Any] = {"file": path.name}
        try:
            notes = parse_notes_file(path)
        except (Ex2SourceError, json.JSONDecodeError) as exc:
            row.update({"valid": False, "error": str(exc)[:200]})
        else:
            row.update({
                "valid": True,
                "lang": notes[0].lang,
                "topic": notes[0].topic,
                "notes": len(notes),
                "with_trap": sum(1 for note in notes if note.trap),
            })
        rows.append(row)
    return rows
