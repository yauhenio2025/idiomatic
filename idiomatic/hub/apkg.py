"""Expression Hub APKG builder: the two frozen models + package assembly.

Model rules (docs/research/ankidroid-tech.md, design §4): both models are
FROZEN at pilot approval — never change field count/order/names or template
count of HUB_MODEL_ID / EXAMPLE_MODEL_ID afterwards; Extra1..Extra3 are the
only escape hatches. The 2026-08-08 owner amendments are implemented here
at model-freeze time, as they bind:

1. EN→TL expression-production card = second template on the hub model
   (English gloss front → expression back), succeeding the retired e2t task.
2. Per-occurrence source context clip (expression_idioms.audio_context)
   embedded on the hub-card back AND the EN→TL card back (ContextAudio
   field; seconds-long occurrence audio — the long stitched compilations
   stay retired).

Deck names always compose from idiomatic/anki_tree.py::anki_root; the
disposable pilot overrides them with PILOT_DECK_ROOT and uses the separate
pilot GUID namespace so it can never collide with production releases.
"""

from __future__ import annotations

import hashlib
import html
from pathlib import Path

import genanki
import structlog

from ..anki_tree import anki_root
from . import identity

log = structlog.get_logger()

HUB_MODEL_ID = 1_820_180_001
HUB_MODEL_NAME = "Idiomatic Expression Hub v1"

EXAMPLE_MODEL_ID = 1_820_180_002
EXAMPLE_MODEL_NAME = "Idiomatic Expression Example v1"

# Field order is a frozen contract. Design §4.1 fields 1-9, then the
# amendment fields, then three frozen spares (commission quality bar:
# >= 3 spares per model).
HUB_FIELDS = [
    "ExpressionId",     # decimal expressions.id, plain text
    "Lang",             # de|es|fr|it|pt
    "Expression",       # reviewed display/citation form
    "GlossEN",
    "UsageLineEN",
    "KeySynonym",       # nullable; only a consequential synonym
    "FalseFriend",      # nullable; may name another known language
    "ExamplesHTML",     # compiled vertical rail; projection, not authority
    "SourcesHTML",      # visible titles + full URL text
    "ContextAudio",     # [sound:] per-occurrence source clip (amendment 2)
    "ExpressionAudio",  # [sound:] atomic expression clip (EN→TL back)
    "Extra1", "Extra2", "Extra3",
]

EXAMPLE_FIELDS = [
    "ExpressionId",
    "ExampleId",        # decimal expression_examples.id, plain text
    "Lang",
    "English",
    "Target",
    "EnglishAudio",
    "TargetAudio",
    "Image",            # approved <img> for this exact example
    "Expression",       # compact answer-side reminder
    "GlossEN",
    "SourceHTML",
    "Origin",           # initial | topup:<batch> | legacy_adopted
    "Extra1", "Extra2", "Extra3",
]

PILOT_DECK_ROOT = "ZZ Hub Pilot (disposable)"

_CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; background: #fff;
       color: #111; text-align: center; padding: 22px 14px;}
.lang-badge {display: inline-block; font-size: clamp(11px, 2.2vw, 14px);
             letter-spacing: 0.12em; text-transform: uppercase; color: #fff;
             background: #0b4a7a; border-radius: 4px; padding: 2px 8px;
             margin-bottom: 14px;}
.prompt-label {font-size: clamp(12px, 2.5vw, 15px); color: #888;
               letter-spacing: 0.05em; text-transform: uppercase;
               margin-bottom: 10px;}
.hub-expr {font-size: clamp(26px, 6vw, 42px); font-weight: 700;
           line-height: 1.25; margin: 12px auto; max-width: 680px;}
.hub-gloss {font-size: clamp(16px, 3.6vw, 22px); color: #0b4a7a;
            margin: 6px auto 2px; max-width: 680px;}
.hub-gloss-front {font-size: clamp(22px, 5vw, 32px); font-weight: 600;
                  color: #0b4a7a; line-height: 1.35; margin: 12px auto;
                  max-width: 640px;}
.usage {font-size: clamp(14px, 3vw, 18px); color: #444; margin: 12px auto 0;
        max-width: 600px; text-align: left; background: #f4f6f5;
        border-radius: 8px; padding: 10px 12px;}
.note-line {font-size: clamp(13px, 2.8vw, 17px); margin: 8px auto 0;
            max-width: 600px; text-align: left; border-radius: 8px;
            padding: 8px 12px;}
.note-line.syn {background: #eef4fb; color: #23486b;}
.note-line.ff {background: #fbf0ee; color: #7a2e20;}
/* Example grid (owner verdict 2026-08-09): tiles, ~3 per row, image on
   top, compact sentence pair beneath; 2 columns on tablets/phones, 1 on
   narrow phones. Text-only tiles share the same tile chrome so
   image-less languages look intentional, not broken. */
.rail {margin: 18px auto 0; max-width: 760px; display: grid;
       grid-template-columns: repeat(3, 1fr); gap: 12px;}
.rail-item {margin: 0; background: #f5f7f7; border-radius: 10px;
            padding: 10px; display: flex; flex-direction: column;
            gap: 6px; text-align: center;}
.rail-item img {width: 100%; border-radius: 8px; display: block;}
.rail-tl {font-size: clamp(13px, 2.6vw, 17px); font-weight: 600;
          line-height: 1.35;}
.rail-en {font-size: clamp(11px, 2.2vw, 14px); color: #888;
          line-height: 1.35;}
@media (max-width: 640px) {.rail {grid-template-columns: repeat(2, 1fr);}}
@media (max-width: 400px) {.rail {grid-template-columns: 1fr;}}
.ctx {font-size: clamp(12px, 2.5vw, 15px); color: #666; margin-top: 10px;}
.sources {margin-top: 22px; font-size: clamp(10px, 2vw, 13px); color: #888;}
.src {margin-top: 6px;}
.src-title {font-weight: 600;}
.src-url {word-break: break-all; color: #9aa;}
.sentence {font-size: clamp(22px, 4.8vw, 34px); font-weight: 600;
           line-height: 1.35; margin: 14px auto; max-width: 640px;}
.sentence-en {color: #111;}
.sentence-tgt {color: #0b4a7a;}
.ex-img img {width: 100%; max-width: 560px; border-radius: 10px;
             margin-top: 12px;}
.idiom-hint {font-size: clamp(14px, 3vw, 18px); color: #666; margin-top: 18px;}
.idiom-hint .idiom-word {font-weight: 600; color: #111;}
.hint-gloss {color: #999;}
.footer {margin-top: 20px; font-size: clamp(10px, 2vw, 13px); color: #888;}
hr#answer {border: 0; border-top: 1px solid #bbb; margin: 18px auto;
           max-width: 640px;}
.replay-button svg {width: 44px; height: 44px;}
/* Explicit night mode — without a .night_mode rule AnkiDroid heuristically
   color-inverts the whole card. */
.card.night_mode, .card.nightMode {background: #23272a; color: #e8e8e8;}
.card.night_mode .hub-gloss, .card.nightMode .hub-gloss,
.card.night_mode .hub-gloss-front, .card.nightMode .hub-gloss-front,
.card.night_mode .sentence-tgt, .card.nightMode .sentence-tgt {color: #7fb2dd;}
.card.night_mode .sentence-en, .card.nightMode .sentence-en {color: #e8e8e8;}
.card.night_mode .usage, .card.nightMode .usage {background: #2e3438; color: #ddd;}
.card.night_mode .note-line.syn, .card.nightMode .note-line.syn
  {background: #26313d; color: #b9d4ee;}
.card.night_mode .note-line.ff, .card.nightMode .note-line.ff
  {background: #3a2b28; color: #eec2b8;}
.card.night_mode .rail-en, .card.nightMode .rail-en {color: #9aa0a6;}
.card.night_mode .rail-item, .card.nightMode .rail-item {background: #2e3438;}
"""

# Card 1 — the accepted TL-front hub card (design §5.2): front is the
# target-language expression ONLY; back is the vertical comic rail.
_HUB_FRONT = """<div class="hub-expr">{{Expression}}</div>"""

_HUB_BACK = """<div class="hub-expr">{{Expression}}</div>
<div class="hub-gloss">{{GlossEN}}</div>
<hr id="answer">
{{#UsageLineEN}}<div class="usage">{{UsageLineEN}}</div>{{/UsageLineEN}}
{{#KeySynonym}}<div class="note-line syn">&#8776; {{KeySynonym}}</div>{{/KeySynonym}}
{{#FalseFriend}}<div class="note-line ff">&#9888; {{FalseFriend}}</div>{{/FalseFriend}}
<div class="rail">{{ExamplesHTML}}</div>
<div class="sources">{{SourcesHTML}}
{{#ContextAudio}}<div class="ctx">In the source video: {{ContextAudio}}</div>{{/ContextAudio}}
</div>"""

# Card 2 — the amended EN→TL expression-production card (owner amendment 1):
# English gloss on the front, the expression on the back. Successor of the
# retired e2t task; the lang badge disambiguates in mixed review.
_EN2TL_FRONT = """<div class="lang-badge">{{Lang}}</div>
<div class="prompt-label">Say the expression</div>
<div class="hub-gloss-front">{{GlossEN}}</div>"""

_EN2TL_BACK = """<div class="lang-badge">{{Lang}}</div>
<hr id="answer">
<div class="hub-expr">{{Expression}}</div>
{{#ExpressionAudio}}<div>{{ExpressionAudio}}</div>{{/ExpressionAudio}}
<div class="hub-gloss">{{GlossEN}}</div>
{{#ContextAudio}}<div class="ctx">In the source video: {{ContextAudio}}</div>{{/ContextAudio}}
<div class="sources">{{SourcesHTML}}</div>"""

# Fluency card (design §5.1): English prompt front — no image, no
# expression hint (neither may leak the answer); everything on the back.
_EXAMPLE_FRONT = """<div class="sentence sentence-en">{{English}}</div>
<div>{{EnglishAudio}}</div>"""

_EXAMPLE_BACK = """<hr id="answer">
<div class="sentence sentence-tgt">{{Target}}</div>
<div>{{TargetAudio}}</div>
{{#Image}}<div class="ex-img">{{Image}}</div>{{/Image}}
<div class="idiom-hint">Expression: <span class="idiom-word">{{Expression}}</span>
<br><span class="hint-gloss">({{GlossEN}})</span></div>
<div class="footer">{{SourceHTML}}</div>"""


def make_hub_model() -> genanki.Model:
    return genanki.Model(
        HUB_MODEL_ID, HUB_MODEL_NAME,
        fields=[{"name": n} for n in HUB_FIELDS],
        templates=[
            {"name": "Hub", "qfmt": _HUB_FRONT, "afmt": _HUB_BACK},
            {"name": "EN -> expression",
             "qfmt": _EN2TL_FRONT, "afmt": _EN2TL_BACK},
        ],
        css=_CSS,
        sort_field_index=HUB_FIELDS.index("Expression"),
    )


def make_example_model() -> genanki.Model:
    return genanki.Model(
        EXAMPLE_MODEL_ID, EXAMPLE_MODEL_NAME,
        fields=[{"name": n} for n in EXAMPLE_FIELDS],
        templates=[
            {"name": "EN -> target",
             "qfmt": _EXAMPLE_FRONT, "afmt": _EXAMPLE_BACK},
        ],
        css=_CSS,
        sort_field_index=EXAMPLE_FIELDS.index("Target"),
    )


# --- deck placement ---------------------------------------------------------

def hub_deck_name(lang: str) -> str:
    """Reserved estate destination for hub cards."""
    return f"{anki_root(lang)}::1 Expressions::2 Expression Focus"


def fluency_deck_name(lang: str) -> str:
    """Reserved estate destination for fluency example cards."""
    return f"{anki_root(lang)}::1 Expressions::1 Fluency"


def _deck_id(deck_name: str) -> int:
    return 1_812_000_000 + (
        int(hashlib.sha1(f"idiomatic-hub::{deck_name}".encode()
                         ).hexdigest()[:8], 16) % 100_000_000
    )


# --- field compilation ------------------------------------------------------

def build_examples_html(examples: list[dict]) -> str:
    """Compile the hub's example grid (verdict 4 as amended 2026-08-09:
    tiles ~3 per row instead of a single vertical column).

    One tile per canonical published example: the sentence's image on
    top (when approved bytes exist), target sentence, muted English line.
    ``data-example-id`` is the projection audit hook — the set of IDs must
    equal the canonical published example set (design acceptance checks).
    """
    items = []
    for ex in examples:
        img = ""
        if ex.get("image_media"):
            img = (f'<img src="{html.escape(str(ex["image_media"]), quote=True)}"'
                   f' alt="">')
        items.append(
            f'<div class="rail-item" data-example-id="{int(ex["example_id"])}">'
            f'{img}'
            f'<div class="rail-tl">{html.escape(ex["target_text"])}</div>'
            f'<div class="rail-en">{html.escape(ex["en_text"])}</div>'
            f'</div>')
    return "\n".join(items)


def build_sources_html(sources: list[dict]) -> str:
    """Visible source titles + full URL as text (no per-video decks)."""
    parts = []
    for s in sources:
        title = html.escape(s.get("title") or "")
        url = html.escape(s.get("url") or "")
        inner = f'<span class="src-title">{title}</span>'
        if url:
            inner += f'<br><span class="src-url">{url}</span>'
        parts.append(f'<div class="src">{inner}</div>')
    return "\n".join(parts)


def _sound(name: str | None) -> str:
    return f"[sound:{name}]" if name else ""


def _img(name: str | None) -> str:
    if not name:
        return ""
    return f'<img src="{html.escape(str(name), quote=True)}">'


# --- package assembly -------------------------------------------------------

def build_hub_apkg(*, out_path: Path, hub_notes: list[dict],
                   example_notes: list[dict],
                   media_files: list[str | Path] | None = None,
                   pilot: bool = False) -> tuple[int, int]:
    """Assemble one APKG holding hub + example notes.

    hub_notes rows: {expression_id, lang, expression, gloss_en,
      usage_line_en, key_synonym, false_friend,
      examples: [{example_id, target_text, en_text, image_media}],
      sources: [{title, url, youtube_id}],
      context_audio_media, expression_audio_media}
    example_notes rows: {expression_id, example_id, lang, en_text,
      target_text, en_audio_media, tl_audio_media, image_media,
      expression, gloss_en, source: {title, url}, origin}

    Media values are flat basenames already staged by the caller;
    ``media_files`` carries the absolute paths to package. ``pilot=True``
    routes every card under PILOT_DECK_ROOT and switches to the pilot GUID
    namespace — a disposable pilot import can never collide with a
    production release.
    """
    hub_model = make_hub_model()
    example_model = make_example_model()
    decks: dict[str, genanki.Deck] = {}

    def deck_for(name: str) -> genanki.Deck:
        deck = decks.get(name)
        if deck is None:
            deck = decks[name] = genanki.Deck(_deck_id(name), name)
        return deck

    n_hub = 0
    for h in hub_notes:
        lang = h["lang"]
        expression_id = int(h["expression_id"])
        deck_name = (f"{PILOT_DECK_ROOT}::Hub" if pilot
                     else hub_deck_name(lang))
        guid = (identity.pilot_hub_guid(lang, expression_id) if pilot
                else identity.hub_guid(lang, expression_id))
        tags = ["idiomatic::expression-hub", f"lang::{lang}",
                f"expression::{expression_id}", "hub-schema::1"]
        for s in h.get("sources", []):
            if s.get("youtube_id"):
                tags.append(f"source::youtube::{s['youtube_id']}")
        if pilot:
            tags.append("zz-hub-pilot")
        deck_for(deck_name).add_note(genanki.Note(
            model=hub_model,
            fields=[
                str(expression_id),
                lang,
                html.escape(h["expression"]),
                html.escape(h.get("gloss_en") or ""),
                html.escape(h.get("usage_line_en") or ""),
                html.escape(h.get("key_synonym") or ""),
                html.escape(h.get("false_friend") or ""),
                build_examples_html(h.get("examples", [])),
                build_sources_html(h.get("sources", [])),
                _sound(h.get("context_audio_media")),
                _sound(h.get("expression_audio_media")),
                "", "", "",
            ],
            guid=guid,
            tags=tags,
        ))
        n_hub += 1

    n_example = 0
    for ex in example_notes:
        lang = ex["lang"]
        expression_id = int(ex["expression_id"])
        example_id = int(ex["example_id"])
        deck_name = (f"{PILOT_DECK_ROOT}::Fluency" if pilot
                     else fluency_deck_name(lang))
        guid = (identity.pilot_example_guid(example_id) if pilot
                else identity.example_guid(example_id))
        origin = ex.get("origin") or "initial"
        tags = ["idiomatic::expression-example", f"lang::{lang}",
                f"expression::{expression_id}", f"example::{example_id}",
                f"origin::{origin}"]
        if pilot:
            tags.append("zz-hub-pilot")
        deck_for(deck_name).add_note(genanki.Note(
            model=example_model,
            fields=[
                str(expression_id),
                str(example_id),
                lang,
                html.escape(ex["en_text"]),
                html.escape(ex["target_text"]),
                _sound(ex.get("en_audio_media")),
                _sound(ex.get("tl_audio_media")),
                _img(ex.get("image_media")),
                html.escape(ex.get("expression") or ""),
                html.escape(ex.get("gloss_en") or ""),
                build_sources_html([ex["source"]] if ex.get("source") else []),
                origin,
                "", "", "",
            ],
            guid=guid,
            tags=tags,
        ))
        n_example += 1

    pkg = genanki.Package(sorted(decks.values(), key=lambda d: d.name))
    pkg.media_files = [str(p) for p in (media_files or [])]
    pkg.write_to_file(str(out_path))
    log.info("hub.apkg.written", path=str(out_path), hubs=n_hub,
             examples=n_example, decks=len(decks), pilot=pilot,
             size_kb=round(Path(out_path).stat().st_size / 1e3))
    return n_hub, n_example
