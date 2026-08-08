"""Pilot-only model contract for BIG_TECH_PHRASES production/shadowing.

This module deliberately has no builder, delivery hook, audio synthesis, or
API route.  The long phrase prompts do not have one uniquely correct
translation and therefore must not be forced into the frozen Exercises v1
production+cloze model.  The separate skeleton can be frozen and wired only
after the owner approves the format pilot.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import genanki

DRAFT_MODEL_ID = 1_820_150_002
DRAFT_MODEL_NAME = "Idiomatic Exercises Shadowing v1 (pilot)"
DRAFT_FIELDS = [
    "ItemId",
    "Lang",
    "Topic",
    "Category",
    "EN",
    "TL",
    "FocusTL",
    "FocusEN",
    "Register",
    "Trap",
    "AudioTL",
    "Extra1",
    "Extra2",
]

SHADOW_FRONT = """<div class="x2s-meta">{{Topic}} · listen, then shadow</div>
<div class="x2s-audio">{{AudioTL}}</div>"""
SHADOW_BACK = """<div class="x2s-tl">{{TL}}</div>
<div class="x2s-focus">{{FocusTL}}</div>
<div class="x2s-en">{{EN}}</div>
{{#Trap}}<div class="x2s-trap">{{Trap}}</div>{{/Trap}}"""
CUE_FRONT = """<div class="x2s-meta">{{Topic}} · produce, then compare</div>
<div class="x2s-en">{{EN}}</div>
<div class="x2s-focus">{{FocusEN}}</div>"""
CUE_BACK = """<div class="x2s-tl">{{TL}}</div>
{{AudioTL}}
<div class="x2s-focus">{{FocusTL}}</div>
<div class="x2s-register">{{Register}}</div>
{{#Trap}}<div class="x2s-trap">{{Trap}}</div>{{/Trap}}"""

DRAFT_CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; text-align: center;
       background: #f6f6f3; color: #1f2023; padding: 24px 16px;}
.x2s-meta {font-size: 13px; color: #6c6d66; text-transform: uppercase;
           letter-spacing: .08em; margin-bottom: 16px;}
.x2s-en, .x2s-tl {font-family: Georgia, serif; font-size: 25px;
                  line-height: 1.4; max-width: 680px; margin: 12px auto;}
.x2s-tl {color: #9e2b33;}
.x2s-focus, .x2s-register, .x2s-trap {max-width: 620px; margin: 10px auto;}
.x2s-focus {font-weight: 600;}
.x2s-register {color: #6c6d66;}
.x2s-trap {background: #f5eedd; border-left: 3px solid #8c6a1d;
           padding: 8px 12px; text-align: left;}
"""

CATEGORIES = frozenset(
    {"context-frame", "concession-frame", "stance-frame", "transition-frame"}
)
SUPPORTED_LANGS = frozenset({"de", "es", "fr", "it", "pt"})


class ShadowSourceError(ValueError):
    """A pilot shadowing output does not satisfy the draft contract."""


@dataclass(frozen=True)
class ShadowNote:
    lang: str
    item_id: str
    en: str
    tl: str
    focus_tl: str
    focus_en: str
    category: str
    register: str
    trap: str


def _text(path: Path, raw: dict, key: str, *, required: bool = True) -> str:
    value = raw.get(key, "")
    if not isinstance(value, str) or (required and not value.strip()):
        raise ShadowSourceError(f"{path.name}: {key} must be a string"
                                + (" and nonempty" if required else ""))
    return value.strip()


def parse_notes_file(path: Path) -> list[ShadowNote]:
    path = Path(path)
    match = re.fullmatch(
        r"(de|es|fr|it|pt)_big_tech_phrases\.json", path.name
    )
    if match is None:
        raise ShadowSourceError(
            f"{path.name}: filename must be <lang>_big_tech_phrases.json"
        )
    try:
        raw_notes = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ShadowSourceError(f"{path.name}: invalid JSON: {exc}") from exc
    return parse_notes_data(raw_notes, lang=match.group(1), source_name=path.name)


def parse_notes_data(
    raw_notes: object, *, lang: str, source_name: str = "shadowing-pilot.json",
) -> list[ShadowNote]:
    """Validate in-memory pilot rows for batch gates and preview tooling."""
    path = Path(source_name)
    if lang not in SUPPORTED_LANGS:
        raise ShadowSourceError(f"{path.name}: unsupported language {lang!r}")
    if not isinstance(raw_notes, list) or not raw_notes:
        raise ShadowSourceError(f"{path.name}: expected a nonempty array")
    result: list[ShadowNote] = []
    seen: set[str] = set()
    for raw in raw_notes:
        if not isinstance(raw, dict):
            raise ShadowSourceError(f"{path.name}: every item must be an object")
        item_id = _text(path, raw, "id")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", item_id) or item_id in seen:
            raise ShadowSourceError(f"{path.name}: invalid or duplicate id {item_id!r}")
        category = _text(path, raw, "category")
        if category not in CATEGORIES:
            raise ShadowSourceError(f"{path.name}: unknown category {category!r}")
        tl = _text(path, raw, "tl")
        focus_tl = _text(path, raw, "focus_tl")
        if focus_tl.casefold() not in tl.casefold():
            raise ShadowSourceError(f"{path.name}: {item_id}: focus_tl must occur in tl")
        result.append(
            ShadowNote(
                lang=lang,
                item_id=item_id,
                en=_text(path, raw, "en"),
                tl=tl,
                focus_tl=focus_tl,
                focus_en=_text(path, raw, "focus_en"),
                category=category,
                register=_text(path, raw, "register"),
                trap=_text(path, raw, "trap", required=False),
            )
        )
        seen.add(item_id)
    return result


def make_draft_model() -> genanki.Model:
    """Return the isolated pilot skeleton; no production code calls this."""
    return genanki.Model(
        DRAFT_MODEL_ID,
        DRAFT_MODEL_NAME,
        fields=[{"name": name} for name in DRAFT_FIELDS],
        templates=[
            {"name": "Listen & Shadow", "qfmt": SHADOW_FRONT, "afmt": SHADOW_BACK},
            {"name": "Cue & Produce", "qfmt": CUE_FRONT, "afmt": CUE_BACK},
        ],
        css=DRAFT_CSS,
    )
