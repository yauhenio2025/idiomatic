"""Translation-exercise decks repurposing grammar-drill audio.

FRONT = the English gloss of a verified grammar drill sentence, spoken by
the English narrator (new, cheap TTS through the shared provider chain,
content-addressed cache under ``staged_audio/grammar/translation_en/<lang>/``).
BACK = the target-language sentence with the drilled form bolded, REUSING
the drill deck's existing back-audio clip (``staged_audio/grammar/<lang>/
idg_<lang>_<id>.mp3``).  Reuse-only guarantee: this module NEVER synthesizes
target-language audio — items whose drill clip is absent are skipped and
counted (docs/commissions/TRANSLATION_DECKS_COMMISSION.md).

Model rules: the model is FROZEN — never change field count/order/names or
template count of MODEL_ID (docs/research/ankidroid-tech.md).  Extra1..Extra4
are spares.  GUIDs derive from (lang, grammar item id), so rebuilds update
fields in place and preserve scheduling.

Spec divergences (deliberate, reuse-only guarantee intact):
- Selection order: the sentence dedupe runs on text-eligible items BEFORE
  the drill-clip disk check (the spec lists the audio requirement first).
  Card identity (GUID = item id) must not depend on disk state — with
  audio-first ordering, a clip healing on a later rebuild would flip the
  dedupe winner to a different item id and orphan the learner's card.
- The dedupe key is the PLAIN corrected sentence (grammar/audio.py
  full_sentence_text), not the bolded HTML: the same sentence drilled at a
  different span is still the same translation exercise.
- The spec calls the 1_930M + sha1 % 60M deck-id range disjoint from
  exercises (1_920M + sha1 % 70M); the ranges actually overlap above
  1_930M.  The formula is kept as commissioned — inputs are namespaced
  ("idiomatic-translation::") and Anki matches decks by name on import,
  so a numeric collision is harmless.
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
from ..pipeline.audio import EN_VOICE
from ..settings import get_settings
from .apkg import _full_html
from .audio import _media_name, full_sentence_text
from .curriculum import GRAMMAR_LANGS, topics_for
from .explainers import VoiceRoute, _voice_fingerprint, leveled_speech_clip

log = structlog.get_logger()

SUPPORTED_LANGS = frozenset(GRAMMAR_LANGS)

MODEL_ID = 1_820_160_001
MODEL_NAME = "Idiomatic Translation v1"
FIELDS = [
    "ItemId",
    "Lang",
    "Topic",
    "TenseLabel",
    "Symbol",
    "EnText",
    "EnAudio",   # [sound:] — EN gloss, autoplays on the front
    "TlHTML",    # full TL sentence, drilled form in <b>
    "TlAudio",   # [sound:] — the reused drill back-audio clip
    "Why",
    "Extra1",
    "Extra2",
    "Extra3",
    "Extra4",
]

# Wrong-phrase fronts (f3), contrast pairs (f4), and radio lessons
# (explainer) are not translation material.
EXCLUDED_FMTS = frozenset({"f3", "f4", "explainer"})
MIN_TL_WORDS = 4

CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; background: #ffffff;
       color: #111; text-align: center; padding: 22px 14px;}
.tense-line {font-size: clamp(13px, 3vw, 17px); color: #777; margin-bottom: 18px;
             letter-spacing: 0.04em;}
.tense-line .sym {font-size: 1.2em; margin-right: 6px;}
.en-text {font-size: clamp(22px, 5vw, 32px); line-height: 1.45; margin: 10px auto;
          max-width: 620px;}
.tl-full {font-size: clamp(24px, 5.5vw, 36px); line-height: 1.45;
          margin: 12px auto 6px; max-width: 620px;}
.tl-full b {color: #0a7;}
.en-small {font-size: clamp(14px, 3vw, 19px); color: #666; margin-top: 12px;
           font-style: italic;}
.why {font-size: clamp(14px, 3vw, 18px); color: #444; margin: 14px auto 0;
      max-width: 560px; text-align: left; background: #f4f6f5;
      border-radius: 8px; padding: 10px 12px;}
hr#answer {border: 0; border-top: 1px solid #ccc; margin: 18px 0;}
/* Explicit night mode — without a .night_mode rule AnkiDroid heuristically
   color-inverts the whole card. */
.card.night_mode, .card.nightMode {background: #23272a; color: #e8e8e8;}
.card.night_mode .tl-full, .card.nightMode .tl-full {color: #e8e8e8;}
.card.night_mode .tl-full b, .card.nightMode .tl-full b {color: #3fc397;}
.card.night_mode .en-small, .card.nightMode .en-small {color: #999;}
.card.night_mode .why, .card.nightMode .why {background: #2e3438; color: #ddd;}
.card.night_mode hr#answer, .card.nightMode hr#answer {border-top-color: #444;}
"""

FRONT = """<div class="tense-line"><span class="sym">{{Symbol}}</span>{{TenseLabel}}</div>
<div class="en-text">{{EnText}}</div>
{{EnAudio}}"""

BACK = """<div class="tense-line"><span class="sym">{{Symbol}}</span>{{TenseLabel}}</div>
<div class="tl-full">{{TlHTML}}</div>
{{#TlAudio}}<div>{{TlAudio}}</div>{{/TlAudio}}
<hr id="answer">
<div class="en-small">{{EnText}}</div>
{{#Why}}<div class="why">{{Why}}</div>{{/Why}}"""


def make_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        MODEL_NAME,
        fields=[{"name": name} for name in FIELDS],
        templates=[{"name": "Translate", "qfmt": FRONT, "afmt": BACK}],
        css=CSS,
    )


def translation_guid(lang: str, item_id: int) -> str:
    return hashlib.sha1(
        f"idiomatic-translation::{lang}::{item_id}".encode("utf-8")
    ).hexdigest()[:16]


def _deck_id(deck_name: str) -> int:
    """Stable id from the full deck name, namespaced apart from the
    grammar (1_811M) and exercises (1_920M) formulas."""
    return 1_930_000_000 + (
        int(hashlib.sha1(f"idiomatic-translation::{deck_name}".encode()
                          ).hexdigest()[:8], 16) % 60_000_000
    )


def deck_name_for(lang: str, cluster: str) -> str:
    """Same cluster strings as the grammar deck; clusterless items fall
    back to the root deck."""
    root = f"Idiomatic Translation {lang.upper()}"
    return f"{root}::{cluster}" if cluster else root


@dataclass(frozen=True)
class TranslationItem:
    item_id: int
    lang: str
    topic: str
    en_text: str   # gloss_en — shown and spoken on the front
    tl_html: str   # corrected sentence, drilled form in <b>
    tl_text: str   # plain corrected sentence (dedupe key + word count)
    why: str
    tl_clip: str   # drill mp3 basename under staged_audio/grammar/<lang>/


def select_items(rows: list[dict], *, lang: str, audio_dir: Path,
                 ) -> tuple[list[TranslationItem], dict[str, int]]:
    """Filter verified grammar rows down to translation material.

    Returns (selected items, stats).  ``eligible`` counts items passing
    every text rule including the dedupe; ``selected`` is the subset whose
    drill clip already exists on disk (same reuse check as
    audio.ensure_item_audio) — the only ones a build may ship.
    """
    stats = {"considered": len(rows), "excluded_fmt": 0, "missing_text": 0,
             "too_short": 0, "duplicate": 0, "eligible": 0,
             "no_tl_audio": 0, "selected": 0}
    selected: list[TranslationItem] = []
    seen_sentences: set[str] = set()
    for it in rows:
        fmt = it.get("fmt") or "cloze"
        if fmt in EXCLUDED_FMTS:
            stats["excluded_fmt"] += 1
            continue
        gloss = (it.get("gloss_en") or "").strip()
        sentence = (it.get("sentence") or "").strip()
        answer = (it.get("answer") or "").strip()
        if not (gloss and sentence and answer):
            stats["missing_text"] += 1
            continue
        infinitive = it.get("infinitive") or ""
        tl_text = full_sentence_text(sentence, answer, infinitive, fmt)
        if len(tl_text.split()) < MIN_TL_WORDS:
            stats["too_short"] += 1
            continue
        if tl_text in seen_sentences:
            stats["duplicate"] += 1
            continue
        seen_sentences.add(tl_text)
        stats["eligible"] += 1
        clip_name = _media_name(lang, it["id"])
        clip = audio_dir / clip_name
        if not (clip.exists() and clip.stat().st_size > 1000):
            stats["no_tl_audio"] += 1
            continue
        selected.append(TranslationItem(
            item_id=it["id"],
            lang=lang,
            topic=it["topic"],
            en_text=gloss,
            tl_html=_full_html(sentence, answer, infinitive),
            tl_text=tl_text,
            why=(it.get("why_en") or "").strip(),
            tl_clip=clip_name,
        ))
    stats["selected"] = len(selected)
    return selected, stats


def en_cache_key(text: str, settings: Any) -> str:
    """Content address for one EN gloss clip: narrator routing + text only."""
    route = VoiceRoute("en", EN_VOICE)
    payload = {"route": _voice_fingerprint(route, settings), "text": text}
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]


def en_audio_filename(lang: str, digest: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{16}", digest):
        raise ValueError("digest must be 16 lowercase hex characters")
    return f"idtr_{lang}_{digest}.mp3"


def _usable_clip(clip: Path) -> bool:
    return (clip.exists() and clip.stat().st_size > 0
            and not gemini.silence_marker(clip).exists())


async def _synthesize_en_audio(
    items: list[TranslationItem],
    *,
    lang: str,
    settings: Any,
    synthesize_fn: Callable[..., Awaitable[None]] | None = None,
    level_fn: Callable[[Path], Path] | None = None,
) -> tuple[dict[int, Path | None], int, int]:
    """Synthesize + level the EN gloss clips through the shared cache.

    A failed clip (silence marker) ships that card without EN audio rather
    than failing the language build — same resilience stance as the grammar
    deck.  Returns (clip by item_id, synthesized count, failed count).
    """
    synthesize_fn = synthesize_fn or gemini.synthesize
    level_fn = level_fn or leveled_speech_clip
    work_dir = (
        Path(settings.data_dir) / "staged_audio" / "grammar"
        / "translation_en" / lang
    )
    work_dir.mkdir(parents=True, exist_ok=True)

    clip_paths: dict[str, Path] = {}
    pending: dict[Path, str] = {}
    for item in items:
        digest = en_cache_key(item.en_text, settings)
        clip = work_dir / en_audio_filename(lang, digest)
        clip_paths[item.en_text] = clip
        if not _usable_clip(clip):
            pending[clip] = item.en_text

    await asyncio.gather(
        *(synthesize_fn(text, voice=EN_VOICE, out=clip, lang="en")
          for clip, text in pending.items())
    )

    usable: dict[str, Path] = {}
    failed = 0
    for text, clip in clip_paths.items():
        if _usable_clip(clip):
            usable[text] = clip
        else:
            failed += 1
    leveled_list = await asyncio.gather(
        *(asyncio.to_thread(level_fn, clip) for clip in usable.values())
    )
    leveled = dict(zip(usable, leveled_list, strict=True))

    result = {item.item_id: leveled.get(item.en_text) for item in items}
    return result, len(pending), failed


def build_translation_apkg(
    *, out_path: Path, lang: str, items: list[TranslationItem],
    audio_dir: Path,
    en_audio: dict[int, Path | None] | None = None,
    topic_labels: dict[str, tuple[str, str]] | None = None,
    topic_clusters: dict[str, str] | None = None,
) -> int:
    """Package selected items (1 card each) into an APKG."""
    model = make_model()
    en_audio = en_audio or {}
    topic_labels = topic_labels or {}
    topic_clusters = topic_clusters or {}
    decks: dict[str, genanki.Deck] = {}
    media: list[str] = []
    media_seen: set[str] = set()

    def _pack(clip: Path) -> str:
        if not clip.exists() or clip.stat().st_size <= 0:
            raise ValueError(f"missing translation media: {clip}")
        # genanki flattens every media path to basename — [sound:] must
        # reference the basename only.
        key = str(clip.resolve())
        if key not in media_seen:
            media.append(str(clip))
            media_seen.add(key)
        return f"[sound:{clip.name}]"

    for item in items:
        if item.lang != lang:
            raise ValueError(f"item {item.item_id} lang {item.lang!r} != {lang!r}")
        label, symbol = topic_labels.get(item.topic, (item.topic, ""))
        deck_name = deck_name_for(lang, topic_clusters.get(item.topic, ""))
        deck = decks.get(deck_name)
        if deck is None:
            deck = decks[deck_name] = genanki.Deck(_deck_id(deck_name), deck_name)

        tl_sound = _pack(audio_dir / item.tl_clip)
        en_clip = en_audio.get(item.item_id)
        en_sound = _pack(Path(en_clip)) if en_clip is not None else ""

        deck.add_note(genanki.Note(
            model=model,
            fields=[
                str(item.item_id),
                lang,
                item.topic,
                label,
                symbol,
                html.escape(item.en_text),
                en_sound,
                item.tl_html,
                tl_sound,
                html.escape(item.why),
                "", "", "", "",
            ],
            guid=translation_guid(lang, item.item_id),
            tags=["idiomatic-translation", item.topic],
        ))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(sorted(decks.values(), key=lambda deck: deck.name))
    package.media_files = media
    package.write_to_file(str(out_path))
    log.info(
        "grammar.translation.apkg_written",
        path=str(out_path), n=len(items), decks=len(decks),
        size_kb=round(out_path.stat().st_size / 1e3),
    )
    return len(items)


async def build_language(
    lang: str,
    *,
    fetch_items_fn: Callable[..., Awaitable[list[dict]]] | None = None,
    synthesize_fn: Callable[..., Awaitable[None]] | None = None,
    level_fn: Callable[[Path], Path] | None = None,
) -> dict[str, Any]:
    """Build one language's translation deck end to end and publish its row."""
    if lang not in SUPPORTED_LANGS:
        raise ValueError("lang must be de|es|fr|it|pt")
    fetch_items_fn = fetch_items_fn or db.fetch_grammar_items
    rows = await fetch_items_fn(lang, status="verified")
    settings = get_settings()
    audio_dir = Path(settings.data_dir) / "staged_audio" / "grammar" / lang
    selected, stats = select_items(rows, lang=lang, audio_dir=audio_dir)
    if not selected:
        raise ValueError(
            f"no translation-eligible items with drill audio for lang {lang!r}"
        )
    en_audio, synthesized, failed = await _synthesize_en_audio(
        selected, lang=lang, settings=settings,
        synthesize_fn=synthesize_fn, level_fn=level_fn,
    )
    labels = {t.key: (t.label, t.symbol) for t in topics_for(lang)}
    clusters = {t.key: t.cluster for t in topics_for(lang)}
    apkg_root = Path(settings.data_dir) / "apkgs" / lang
    apkg_root.mkdir(parents=True, exist_ok=True)
    out = apkg_root / "_translation.apkg"
    note_count = await asyncio.to_thread(
        lambda: build_translation_apkg(
            out_path=out, lang=lang, items=selected, audio_dir=audio_dir,
            en_audio=en_audio, topic_labels=labels, topic_clusters=clusters,
        )
    )
    relative = out.relative_to(Path(settings.data_dir))
    apkg_id = await db.upsert_pool_apkg(
        lang=lang,
        kind="translation",
        filename=str(relative),
        size_bytes=out.stat().st_size,
        n_idioms=note_count,
    )
    result = {
        "lang": lang,
        "cards": note_count,
        "apkg_id": apkg_id,
        "en_synthesized": synthesized,
        "en_failed": failed,
        **stats,
    }
    log.info("grammar.translation.built", **result)
    return result


async def language_inventory(
    *,
    fetch_items_fn: Callable[..., Awaitable[list[dict]]] | None = None,
) -> list[dict[str, Any]]:
    """Per-language counts: eligible items, drill audio present, EN cached."""
    fetch_items_fn = fetch_items_fn or db.fetch_grammar_items
    settings = get_settings()
    inventory: list[dict[str, Any]] = []
    for lang in GRAMMAR_LANGS:
        rows = await fetch_items_fn(lang, status="verified")
        audio_dir = Path(settings.data_dir) / "staged_audio" / "grammar" / lang
        selected, stats = select_items(rows, lang=lang, audio_dir=audio_dir)
        en_dir = (Path(settings.data_dir) / "staged_audio" / "grammar"
                  / "translation_en" / lang)
        en_cached = sum(
            1 for item in selected
            if _usable_clip(
                en_dir / en_audio_filename(lang, en_cache_key(item.en_text,
                                                              settings)))
        )
        inventory.append({
            "lang": lang,
            "eligible": stats["eligible"],
            "with_tl_audio": stats["selected"],
            "en_cached": en_cached,
        })
    return inventory
