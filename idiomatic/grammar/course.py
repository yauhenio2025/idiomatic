"""Grammar Course: sequenced, book-grounded lesson + exercise units.

Design: docs/GRAMMAR_COURSE_DESIGN.md; commission:
docs/commissions/GRAMMAR_COURSE_COMMISSION.md.

A unit is ~10 two-sided pure-lesson cards ("twenty slides") plus a distinct
population of atomic exercise cards (owner-ratified atomicity principle:
exercises are individually-graded cards, never embedded in lessons).  First
exposure is sequenced by new-card due POSITIONS: one lesson card (= 2
slides), then that card's exercise block, then the next lesson card.

Model rules: BOTH models are FROZEN — never change field count/order/names
or template count (docs/research/ankidroid-tech.md).  Extra fields are
spares.  GUIDs derive from (lang, unit, seq|item_id), so re-authored
content updates fields in place and preserves scheduling.

COPYRIGHT RULE (hard): workbook-derived exercise content lives ONLY under
``data/course/book_local/`` which is gitignored — the repo is public and
book text must never enter git.  Lesson scripts under ``data/course/
lessons/`` are authored in our own words (grounded in, and citing, Hammer
sections) and are committed like any other original content.
"""

from __future__ import annotations

import copy
import hashlib
import html
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

import subprocess

import genanki
import structlog

from ..anki_tree import anki_root
from ..pipeline.audio import concat_mp3s, silence_mp3
from .explainers import (
    BETWEEN_SPEECH_MS,
    PAUSE_MS,
    Segment,
    _WORD,
    _segments,
    leveled_speech_clip,
)
from .podcast_cards import _lenient_frontmatter

log = structlog.get_logger()

DATA_DIR = Path(__file__).parent / "data" / "course"
LESSON_DIR = DATA_DIR / "lessons"
# Book-derived content: gitignored, machine-local, never committed.
BOOK_LOCAL_DIR = DATA_DIR / "book_local"

SUPPORTED_LANGS = frozenset({"de", "es", "fr", "it", "pt"})

# ---------------------------------------------------------------------------
# Frozen models (1_820_190_0xx — the Grammar Course range)
# ---------------------------------------------------------------------------

LESSON_MODEL_ID = 1_820_190_001
LESSON_MODEL_NAME = "Idiomatic Course Lesson v1"
LESSON_FIELDS = [
    "LessonId",
    "Unit",
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

EXERCISE_MODEL_ID = 1_820_190_002
EXERCISE_MODEL_NAME = "Idiomatic Book Exercise v1"
EXERCISE_FIELDS = [
    "ItemId",
    "Lang",
    "Unit",
    "Block",
    "Instruction",
    "PromptHTML",
    "SolutionHTML",
    "AltsHTML",
    "SourceRef",
    "HammerRefs",
    "Provenance",
    "SolutionAudio",
    # Spare fields, semantically assigned by the 2026-08-10 exercise-card
    # redesign (enrichment sidecar). Field NAMES stay frozen — the
    # EXERCISE_*_FIELD constants below pin what each spare carries so no
    # other feature may reuse them:
    "Extra1",  # example_html — the block's worked example (front)
    "Extra2",  # solution_en — English gloss of the solution (back)
    "Extra3",  # why_en — one-line grammar "why" (back)
]

# Enrichment sidecar → spare-field mapping (names FROZEN, see above).
EXERCISE_EXAMPLE_FIELD = "Extra1"      # example_html (front worked example)
EXERCISE_SOLUTION_EN_FIELD = "Extra2"  # solution_en (EN gloss, back)
EXERCISE_WHY_FIELD = "Extra3"          # why_en (grammar why, back)

PROVENANCES = frozenset({"book-verbatim"})  # "llm-generated" reserved for v2

# Lesson CSS follows the podcast-lesson house style: shared SVG palette
# classes, explicit night mode (prevents AnkiDroid's heuristic inversion).
LESSON_CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; background: #ffffff;
       color: #111; text-align: center; padding: 22px 14px;}
.cl-meta {font-size: clamp(12px, 2.7vw, 15px); color: #777;
          letter-spacing: 0.04em; margin-bottom: 14px;}
.cl-title {font-size: clamp(24px, 5vw, 36px); font-weight: 700;
           line-height: 1.25; margin: 12px auto; max-width: 680px;}
.cl-tl {font-size: clamp(24px, 5.5vw, 40px); color: #0a7;
        line-height: 1.35; margin: 12px auto; max-width: 680px;}
.cl-en {font-size: clamp(12px, 2.6vw, 15px); color: #9a9b95;
        line-height: 1.4; margin: 2px auto 0; max-width: 620px;}
.cl-tl-list {list-style: none; margin: 14px auto; padding: 0;
             max-width: 620px; text-align: left;}
.cl-tl-item {position: relative; padding-left: 26px; margin: 13px 0;
             font-size: clamp(20px, 4.5vw, 32px);}
.cl-tl-item::before {content: ""; position: absolute; left: 6px; top: 0.42em;
                     width: 8px; height: 8px; border-radius: 50%;
                     background: #b9c2be;}
.cl-tl-list .cl-tl {font-size: 1em; margin: 0; max-width: none;
                    text-align: left;}
.cl-tl-list .cl-en {margin: 2px 0 0; max-width: none; text-align: left;}
.cl-note {font-size: clamp(15px, 3.2vw, 20px); color: #666;
          line-height: 1.45; margin: 9px auto; max-width: 620px;}
.cl-refs {font-size: clamp(11px, 2.4vw, 13px); color: #999;
          letter-spacing: 0.03em; margin-top: 18px;}
.cl-img-wrap {margin: 10px auto 18px; max-width: 640px;}
.cl-img-wrap svg {width: 100%; height: auto; display: block;}
.cl-img {max-width: 100%; height: auto; border-radius: 12px;
         margin: 10px auto 18px;}
/* Authored-diagram palette — inline SVGs carry classes, colors live here
   so night mode is one override block, not per-file edits. */
svg .s-ink {fill: #22302e;}
svg .s-muted {fill: #6d7a76;}
svg .s-teal {fill: #0a9c76;}
svg .s-coral {fill: #e8604c;}
svg .s-sun {fill: #f2c94c;}
svg .s-dead {fill: #b9c2be;}
svg .s-tile {fill: #ffffff; stroke: #e3ddd0;}
svg .s-stroke-teal {stroke: #0a9c76; fill: none;}
svg .s-stroke-coral {stroke: #e8604c; fill: none;}
svg .s-stroke-line {stroke: #e3ddd0; fill: none;}
.card.night_mode, .card.nightMode {background: #23272a; color: #e8e8e8;}
.card.night_mode .cl-meta, .card.nightMode .cl-meta {color: #999;}
.card.night_mode .cl-note, .card.nightMode .cl-note {color: #bbb;}
.card.night_mode .cl-refs, .card.nightMode .cl-refs {color: #888;}
.card.night_mode .cl-tl, .card.nightMode .cl-tl {color: #20c997;}
.card.night_mode .cl-en, .card.nightMode .cl-en {color: #7f8a86;}
.card.night_mode .cl-tl-item::before, .card.nightMode .cl-tl-item::before
  {background: #55625d;}
.card.night_mode svg .s-ink, .card.nightMode svg .s-ink {fill: #e8ece9;}
.card.night_mode svg .s-muted, .card.nightMode svg .s-muted {fill: #97a49f;}
.card.night_mode svg .s-teal, .card.nightMode svg .s-teal {fill: #2fc296;}
.card.night_mode svg .s-coral, .card.nightMode svg .s-coral {fill: #f0765f;}
.card.night_mode svg .s-sun, .card.nightMode svg .s-sun {fill: #e6c25a;}
.card.night_mode svg .s-dead, .card.nightMode svg .s-dead {fill: #55625d;}
.card.night_mode svg .s-tile, .card.nightMode svg .s-tile
  {fill: #2a3431; stroke: #3a4642;}
.card.night_mode svg .s-stroke-teal, .card.nightMode svg .s-stroke-teal
  {stroke: #2fc296;}
.card.night_mode svg .s-stroke-coral, .card.nightMode svg .s-stroke-coral
  {stroke: #f0765f;}
.card.night_mode svg .s-stroke-line, .card.nightMode svg .s-stroke-line
  {stroke: #3a4642;}
"""

LESSON_FRONT = """<div class="cl-meta">{{Unit}} · {{Seq}} · {{Lang}}</div>
{{FrontImage}}
{{FrontHTML}}
{{FrontAudio}}"""

LESSON_BACK = """<div class="cl-meta">{{Unit}} · {{Seq}} · {{Lang}}</div>
{{BackImage}}
{{BackHTML}}
{{BackAudio}}"""

EXERCISE_CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; background: #f6f6f3;
       color: #1f2023; text-align: center; padding: 24px 16px;}
.cx-meta {font-size: clamp(11px, 2.5vw, 14px); color: #6c6d66;
          letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 16px;}
.cx-instr {font-size: clamp(13px, 3vw, 17px); color: #3d3e38;
           line-height: 1.45; margin: 10px auto; max-width: 620px;}
/* German inside English instruction/example/why text: serif italic, the
   same voice as the prompt, so the two languages never blur together. */
.cx-instr i, .cx-example i, .cx-why i
  {font-family: Georgia, 'Times New Roman', serif; font-style: italic;}
.cx-prompt {font-family: Georgia, 'Times New Roman', serif;
            font-size: clamp(20px, 4.8vw, 28px); line-height: 1.5;
            margin: 16px auto; max-width: 640px;}
.cx-example {font-size: clamp(13px, 3vw, 16px); color: #6c6d66;
             line-height: 1.5; margin: 18px auto 0; max-width: 620px;
             padding-top: 10px; border-top: 1px dotted #d6d6cb;}
.cx-example-label {display: block; font-size: 11px; color: #9b978e;
                   letter-spacing: 0.14em; text-transform: uppercase;
                   margin-bottom: 4px;}
.cx-prompt-echo {font-family: Georgia, 'Times New Roman', serif;
                 font-size: clamp(14px, 3.2vw, 17px); color: #6c6d66;
                 line-height: 1.45; margin: 0 auto 8px; max-width: 640px;}
.cx-solution {font-family: Georgia, 'Times New Roman', serif;
              font-size: clamp(20px, 4.8vw, 28px); line-height: 1.5;
              margin: 16px auto; max-width: 640px;}
.cx-solution mark {background: #f4dfe0; color: inherit; padding: 0 3px;
                   border-radius: 3px; font-weight: 600;}
.cx-gloss {font-size: clamp(14px, 3.2vw, 18px); color: #52534d;
           line-height: 1.45; margin: 2px auto 14px; max-width: 620px;}
.cx-gloss::before {content: "= "; color: #9b978e;}
.cx-alts {font-size: clamp(13px, 3vw, 16px); color: #6c6d66; margin: 4px auto 10px;}
.cx-alts span {display: inline-block; border: 1px solid #e1e1d8;
               border-radius: 999px; padding: 1px 10px; margin: 2px 3px;
               color: #1f2023;}
.cx-why {font-size: clamp(13px, 3vw, 16px); color: #3d3e38; text-align: left;
         line-height: 1.5; margin: 16px auto 0; max-width: 600px;
         padding: 10px 12px; background: #f0f0ea; border-radius: 4px;
         border-left: 3px solid #0a9c76;}
.cx-refs {font-size: clamp(11px, 2.4vw, 13px); color: #9b978e;
          letter-spacing: 0.03em; margin-top: 16px;}
hr#answer {border: 0; border-top: 1px solid #e1e1d8; margin: 18px 0;}
.card.night_mode, .card.nightMode {background: #1b1a19; color: #edeae4;}
.card.night_mode .cx-meta, .card.nightMode .cx-meta {color: #9b978e;}
.card.night_mode .cx-instr, .card.nightMode .cx-instr {color: #c9c6bd;}
.card.night_mode .cx-example, .card.nightMode .cx-example
  {color: #9b978e; border-top-color: #3a3835;}
.card.night_mode .cx-example-label, .card.nightMode .cx-example-label
  {color: #7d7a72;}
.card.night_mode .cx-prompt-echo, .card.nightMode .cx-prompt-echo
  {color: #9b978e;}
.card.night_mode .cx-gloss, .card.nightMode .cx-gloss {color: #b8b5ac;}
.card.night_mode .cx-gloss::before, .card.nightMode .cx-gloss::before
  {color: #7d7a72;}
.card.night_mode .cx-alts, .card.nightMode .cx-alts {color: #9b978e;}
.card.night_mode .cx-alts span, .card.nightMode .cx-alts span
  {border-color: #343230; color: #edeae4;}
.card.night_mode .cx-why, .card.nightMode .cx-why
  {color: #c9c6bd; background: #22211f; border-left-color: #2fc296;}
.card.night_mode .cx-solution mark, .card.nightMode .cx-solution mark
  {background: #4a3032; color: #edeae4;}
.card.night_mode .cx-refs, .card.nightMode .cx-refs {color: #7d7a72;}
.card.night_mode hr#answer, .card.nightMode hr#answer
  {border-top-color: #343230;}
"""

EXERCISE_FRONT = """<div class="cx-meta">{{Unit}} · {{Block}}</div>
<div class="cx-instr">{{Instruction}}</div>
<div class="cx-prompt">{{PromptHTML}}</div>
{{#Extra1}}<div class="cx-example">\
<span class="cx-example-label">Example</span>{{Extra1}}</div>{{/Extra1}}"""

EXERCISE_BACK = """<div class="cx-meta">{{Unit}} · {{Block}}</div>
<div class="cx-prompt-echo">{{PromptHTML}}</div>
<div class="cx-solution">{{SolutionHTML}}</div>
{{#Extra2}}<div class="cx-gloss">{{Extra2}}</div>{{/Extra2}}
{{SolutionAudio}}
{{#AltsHTML}}<div class="cx-alts">{{AltsHTML}}</div>{{/AltsHTML}}
{{#Extra3}}<div class="cx-why">{{Extra3}}</div>{{/Extra3}}
<hr id="answer">
<div class="cx-refs">{{HammerRefs}} · {{SourceRef}} · {{Provenance}}</div>"""

AUDIO_PENDING_TAG = "idiomatic-course-audio-pending"

_REF_ID = re.compile(r"(?:\d{1,2}(?:\.\d{1,3}){0,3}[a-z]?|Ch\.\s?\d{1,2})")
_MARK_SPAN = re.compile(r"<mark>(.*?)</mark>", re.DOTALL)
_SVG_EVENT_HANDLER = re.compile(r"\son[a-z]+\s*=")
_PAUSE_LINE = re.compile(r"\[PAUSE(?::\d+)?\]")  # the segment grammar's forms


class CourseSourceError(ValueError):
    """A Grammar Course source file does not satisfy its contract."""


# ---------------------------------------------------------------------------
# Lesson source parsing (Markdown, podcast-cards line grammar + REF:)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DisplayItem:
    kind: Literal["show", "tl"]
    text: str
    # English gloss for a TL sentence (``EN:`` line). DISPLAY-ONLY: it is
    # never spoken, never becomes a speech segment, and cannot shift the
    # narration clip ordinals.
    gloss: str | None = None


@dataclass(frozen=True)
class CourseSide:
    seq: int
    side: Literal["front", "back"]
    title: str
    refs: tuple[str, ...]  # Hammer §-ids, the per-slide Sources footer
    segments: tuple[Segment, ...]
    display: tuple[DisplayItem, ...]
    svg_file: str | None = None  # authored diagram sidecar (svg/<name>)


@dataclass(frozen=True)
class CourseCard:
    seq: int
    front: CourseSide
    back: CourseSide


@dataclass(frozen=True)
class CourseLesson:
    path: Path
    lang: str
    unit: str
    title: str
    unit_label: str  # learner-facing deck segment, e.g. "Kasus (cases)"
    cards: tuple[CourseCard, ...]


def _source_error(path: Path, line_no: int, message: str) -> CourseSourceError:
    return CourseSourceError(f"{path.name}: line {line_no}: {message}")


def _parse_refs(path: Path, line_no: int, raw: str) -> tuple[str, ...]:
    refs = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not refs:
        raise _source_error(path, line_no, "REF: must list at least one §-id")
    for ref in refs:
        if not _REF_ID.fullmatch(ref):
            raise _source_error(
                path, line_no, f"REF: invalid Hammer §-id {ref!r}"
            )
    return refs


def _parse_side(
    path: Path,
    *,
    lang: str,
    seq: int,
    side: Literal["front", "back"],
    physical_lines: Sequence[tuple[int, str]],
) -> CourseSide:
    fallback_line = physical_lines[0][0] if physical_lines else 1
    nonblank = [
        (line_no, raw.strip()) for line_no, raw in physical_lines if raw.strip()
    ]
    if not nonblank:
        raise _source_error(path, fallback_line, f"card {seq} {side} is empty")
    if not nonblank[0][1].startswith("TITLE:"):
        raise _source_error(
            path, nonblank[0][0], f"card {seq} {side} must start with TITLE:"
        )

    titles = [(no, line[6:].strip()) for no, line in nonblank
              if line.startswith("TITLE:")]
    if len(titles) != 1:
        raise _source_error(
            path, titles[1][0] if len(titles) > 1 else fallback_line,
            f"card {seq} {side} expected exactly one TITLE:, found {len(titles)}",
        )
    title_line, title = titles[0]
    if not title:
        raise _source_error(path, title_line, "TITLE: must be nonempty")

    ref_lines = [(no, line[4:].strip()) for no, line in nonblank
                 if line.startswith("REF:")]
    if len(ref_lines) != 1:
        raise _source_error(
            path, ref_lines[1][0] if len(ref_lines) > 1 else fallback_line,
            f"card {seq} {side} expected exactly one REF:, found {len(ref_lines)}",
        )
    refs = _parse_refs(path, ref_lines[0][0], ref_lines[0][1])

    svgs = [(no, line[4:].strip()) for no, line in nonblank
            if line.startswith("SVG:")]
    if len(svgs) > 1:
        raise _source_error(
            path, svgs[1][0],
            f"card {seq} {side} expected at most one SVG:, found {len(svgs)}",
        )
    svg_file: str | None = None
    if svgs:
        svg_line, svg_file = svgs[0]
        if not re.fullmatch(r"[a-z0-9][a-z0-9_\-]*\.svg", svg_file):
            raise _source_error(
                path, svg_line, f"SVG: invalid sidecar filename {svg_file!r}"
            )
        if not (path.parent / "svg" / svg_file).is_file():
            raise _source_error(
                path, svg_line, f"SVG: sidecar svg/{svg_file} does not exist"
            )

    display: list[DisplayItem] = []
    spoken_lines: list[str] = []
    # ``EN:`` glosses attach to the most recent TL: line; only [PAUSE]
    # lines (and blanks) may sit between a TL and its EN.  ``pending_tl``
    # is the display index of that still-glossable TL.
    pending_tl: int | None = None
    for line_no, raw in physical_lines:
        line = raw.strip()
        if line.startswith(("TITLE:", "SVG:", "REF:")):
            spoken_lines.append("")
            pending_tl = None
        elif line.startswith("SHOW:"):
            text = line[5:].strip()
            if not text:
                raise _source_error(path, line_no, "SHOW: must be nonempty")
            display.append(DisplayItem("show", text))
            spoken_lines.append("")
            pending_tl = None
        elif line.startswith("TL-:"):
            text = line[4:].strip()
            if not text:
                raise _source_error(path, line_no, "empty TL- segment")
            spoken_lines.append(f"TL: {text}")
            pending_tl = None
        elif line.startswith("TL:"):
            text = line[3:].strip()
            if not text:
                raise _source_error(path, line_no, "empty TL segment")
            display.append(DisplayItem("tl", text))
            spoken_lines.append(f"TL: {text}")
            pending_tl = len(display) - 1
        elif line.startswith("EN:"):
            # Display-only English gloss — contributes NO spoken line, so
            # the speech-segment plan (and every clip ordinal/content
            # hash) is byte-identical with or without EN: lines.
            text = line[3:].strip()
            if not text:
                raise _source_error(path, line_no, "EN: must be nonempty")
            if pending_tl is None:
                raise _source_error(
                    path, line_no,
                    "EN: must directly follow its TL: line "
                    "(only [PAUSE] lines may sit between)",
                )
            if display[pending_tl].gloss is not None:
                raise _source_error(
                    path, line_no, "TL: line already has an EN: gloss"
                )
            display[pending_tl] = replace(display[pending_tl], gloss=text)
            spoken_lines.append("")
        else:
            if line and not _PAUSE_LINE.fullmatch(line):
                pending_tl = None
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
        message = str(exc)
        prefix = f"{path.name}: "
        if message.startswith(prefix):
            message = message[len(prefix):]
        raise CourseSourceError(f"{path.name}: {message}") from exc
    if not any(segment.kind == "speech" for segment in segments):
        raise _source_error(
            path, fallback_line, f"card {seq} {side} has no spoken segment"
        )
    return CourseSide(
        seq=seq,
        side=side,
        title=title,
        refs=refs,
        segments=segments,
        display=tuple(display),
        svg_file=svg_file,
    )


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
    numbers: dict[str, int] = {}
    for offset, line in enumerate(raw_lines):
        if ":" in line and not line.startswith((" ", "-", "\t")):
            numbers[line.split(":", 1)[0].strip()] = 2 + offset
    return _lenient_frontmatter(list(raw_lines)), numbers, closing


def _required(path: Path, metadata: dict[str, str],
              numbers: dict[str, int], key: str) -> str:
    value = (metadata.get(key) or "").strip()
    if not value:
        raise _source_error(
            path, numbers.get(key, 1), f"missing or empty frontmatter field {key!r}"
        )
    return value


def parse_course_lesson(path: Path) -> CourseLesson:
    """Parse one authored unit lesson into validated cards."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata, numbers, closing = _metadata(path, lines)

    series = _required(path, metadata, numbers, "series")
    if series != "grammar-course-lesson":
        raise _source_error(
            path, numbers.get("series", 1),
            "series must be 'grammar-course-lesson'",
        )
    lang = _required(path, metadata, numbers, "lang")
    if lang not in SUPPORTED_LANGS:
        raise _source_error(
            path, numbers.get("lang", 1),
            f"unsupported lang {lang!r}; expected de|es|fr|it|pt",
        )
    unit = _required(path, metadata, numbers, "unit")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", unit):
        raise _source_error(path, numbers.get("unit", 1), f"invalid unit {unit!r}")
    if path.name != f"{lang}_{unit}.md":
        raise _source_error(
            path, numbers.get("unit", 1), f"filename must be {lang}_{unit}.md"
        )
    title = _required(path, metadata, numbers, "title")
    unit_label = _required(path, metadata, numbers, "unit_label")
    if "::" in unit_label:
        raise _source_error(
            path, numbers.get("unit_label", 1),
            "unit_label must not contain '::' (it is one deck segment)",
        )

    body = lines[closing + 1:]
    body_start = closing + 1
    headings = [i for i, line in enumerate(body) if line.strip() == "## SCRIPT"]
    if len(headings) != 1:
        raise _source_error(
            path, body_start + 1,
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
    markers = [i for i, line in enumerate(script_lines) if line.strip() == "[CARD]"]
    if not 8 <= len(markers) <= 12:
        raise _source_error(
            path, body_start + heading + 1,
            f"expected 8-12 [CARD] markers, found {len(markers)}",
        )
    for offset, line in enumerate(script_lines[:markers[0]]):
        if line.strip():
            raise _source_error(
                path, script_first_line + offset,
                "content before the first [CARD] is not allowed",
            )

    cards: list[CourseCard] = []
    boundaries = [*markers, len(script_lines)]
    for seq, (marker, end) in enumerate(zip(boundaries, boundaries[1:]), 1):
        content = script_lines[marker + 1:end]
        content_first_line = script_first_line + marker + 1
        side_markers = [i for i, line in enumerate(content)
                        if line.strip() == "[SIDE]"]
        if len(side_markers) != 1:
            raise _source_error(
                path, script_first_line + marker,
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
        cards.append(CourseCard(
            seq,
            _parse_side(path, lang=lang, seq=seq, side="front",
                        physical_lines=front_lines),
            _parse_side(path, lang=lang, seq=seq, side="back",
                        physical_lines=back_lines),
        ))
    return CourseLesson(
        path=path, lang=lang, unit=unit, title=title,
        unit_label=unit_label, cards=tuple(cards),
    )


# ---------------------------------------------------------------------------
# Exercise source parsing (JSON, book-derived, gitignored path)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CourseExercise:
    lang: str
    unit: str
    item_id: str
    block: int  # lesson card seq this exercise follows (telemetry span key)
    instruction: str
    prompt: str
    solution_html: str  # full solution, answer spans in <mark>
    alternatives: tuple[str, ...]
    hammer_refs: tuple[str, ...]
    source_ref: str  # e.g. "PGG Kap. 2, Üb. 4, Nr. 3"
    provenance: str  # ∈ PROVENANCES


def _exercise_error(path: Path, item_id: str, message: str) -> CourseSourceError:
    return CourseSourceError(f"{path.name}: {item_id or '<missing id>'}: {message}")


def validate_solution_html(path: Path, item_id: str, solution: str) -> None:
    """Structural hygiene for book-derived solutions.

    The corpus carries occasional mangled reconstructions even on unflagged
    items (e.g. Case ex. 16 duplicates the prompt inside <mark>), so the
    loader re-checks structure instead of trusting flags alone.
    """
    spans = _MARK_SPAN.findall(solution)
    if not spans or any(not span.strip() for span in spans):
        raise _exercise_error(
            path, item_id, "solution_html needs at least one nonempty <mark>"
        )
    if "___" in solution:
        raise _exercise_error(
            path, item_id, "solution_html still contains a blank placeholder"
        )
    stripped = _MARK_SPAN.sub("", solution)
    if "<" in stripped or ">" in stripped:
        raise _exercise_error(
            path, item_id, "solution_html may contain only <mark> markup"
        )


def _text_field(path: Path, raw: dict, item_id: str, key: str, *,
                required: bool = True) -> str:
    value = raw.get(key, "")
    if not isinstance(value, str):
        raise _exercise_error(path, item_id, f"{key} must be a string")
    value = value.strip()
    if required and not value:
        raise _exercise_error(path, item_id, f"{key} must be nonempty")
    return value


def _parse_exercise(
    path: Path, lang: str, unit: str, block: int, raw: dict
) -> CourseExercise:
    if not isinstance(raw, dict):
        raise CourseSourceError(f"{path.name}: every exercise must be an object")
    item_id = str(raw.get("id", "")).strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_\-]*", item_id):
        raise CourseSourceError(
            f"{path.name}: invalid or missing exercise id {item_id!r}"
        )
    solution = _text_field(path, raw, item_id, "solution_html")
    validate_solution_html(path, item_id, solution)

    provenance = _text_field(path, raw, item_id, "provenance")
    if provenance not in PROVENANCES:
        raise _exercise_error(path, item_id, f"unknown provenance {provenance!r}")

    refs_raw = raw.get("hammer_refs", [])
    if (not isinstance(refs_raw, list) or not refs_raw or any(
            not isinstance(ref, str) or not _REF_ID.fullmatch(ref.strip())
            for ref in refs_raw)):
        raise _exercise_error(
            path, item_id, "hammer_refs must be a nonempty list of §-ids"
        )

    alts_raw = raw.get("alternatives", [])
    if not isinstance(alts_raw, list) or any(
        not isinstance(alt, str) or not alt.strip() for alt in alts_raw
    ):
        raise _exercise_error(
            path, item_id, "alternatives must be a list of nonempty strings"
        )

    return CourseExercise(
        lang=lang,
        unit=unit,
        item_id=item_id,
        block=block,
        instruction=_text_field(path, raw, item_id, "instruction"),
        prompt=_text_field(path, raw, item_id, "prompt"),
        solution_html=solution,
        alternatives=tuple(alt.strip() for alt in alts_raw),
        hammer_refs=tuple(ref.strip() for ref in refs_raw),
        source_ref=_text_field(path, raw, item_id, "source_ref"),
        provenance=provenance,
    )


def parse_exercises_file(path: Path) -> list[CourseExercise]:
    """Parse one ``<lang>_<unit>.exercises.json`` with full validation."""
    path = Path(path)
    match = re.fullmatch(
        r"([a-z]{2})_([a-z0-9]+(?:-[a-z0-9]+)*)\.exercises\.json", path.name
    )
    if match is None or match.group(1) not in SUPPORTED_LANGS:
        raise CourseSourceError(
            f"{path.name}: filename must be <lang>_<unit>.exercises.json"
        )
    lang, unit = match.group(1), match.group(2)
    data = json.loads(path.read_text(encoding="utf-8"))
    exercises = parse_exercises_payload(data, name=path.name)
    if exercises[0].lang != lang or exercises[0].unit != unit:
        raise CourseSourceError(
            f"{path.name}: lang/unit fields must match the filename"
        )
    return exercises


def parse_exercises_payload(data: Any, *, name: str) -> list[CourseExercise]:
    """Validate one exercises payload (the exercises-file JSON object).

    Shared by the file loader and the admin seeding endpoint — book-derived
    content reaches the server as a POSTed payload, never through the
    public repo.
    """
    path = Path(name)
    if not isinstance(data, dict):
        raise CourseSourceError(f"{path.name}: expected a JSON object")
    lang = data.get("lang")
    unit = data.get("unit")
    if not isinstance(lang, str) or lang not in SUPPORTED_LANGS:
        raise CourseSourceError(f"{path.name}: lang must be de|es|fr|it|pt")
    if not isinstance(unit, str) or not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*", unit
    ):
        raise CourseSourceError(f"{path.name}: invalid unit {unit!r}")
    blocks = data.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise CourseSourceError(f"{path.name}: blocks must be a nonempty array")

    exercises: list[CourseExercise] = []
    seen_blocks: set[int] = set()
    for raw_block in blocks:
        if not isinstance(raw_block, dict):
            raise CourseSourceError(f"{path.name}: every block must be an object")
        block_no = raw_block.get("block")
        if not isinstance(block_no, int) or isinstance(block_no, bool) \
                or block_no < 1:
            raise CourseSourceError(
                f"{path.name}: block must be an integer >= 1"
            )
        if block_no in seen_blocks:
            raise CourseSourceError(f"{path.name}: duplicate block {block_no}")
        seen_blocks.add(block_no)
        items = raw_block.get("exercises")
        if not isinstance(items, list) or not items:
            raise CourseSourceError(
                f"{path.name}: block {block_no} exercises must be nonempty"
            )
        for raw in items:
            exercises.append(_parse_exercise(path, lang, unit, block_no, raw))

    seen_ids: set[str] = set()
    for exercise in exercises:
        if exercise.item_id in seen_ids:
            raise CourseSourceError(
                f"{path.name}: duplicate exercise id {exercise.item_id!r}"
            )
        seen_ids.add(exercise.item_id)
    return exercises


# ---------------------------------------------------------------------------
# Enrichment sidecar (codex-authored, machine-local, contract 2)
#
# ``<lang>_<unit>.enrichment.json`` beside the exercises file re-authors each
# block's repeated book rubric as ONE short task line (+ optional worked
# example) and adds a per-exercise English gloss + "why" + the COMPLETE
# production sentence (solution_full_html — what the back displays and
# voices; null when the original solution already IS the full production).
# It may be ABSENT — units then build exactly as before.  Hard rule: codex
# may only COPY German from the block's own source text, never write its
# own; every ``<i>`` span is mechanically checked against the block source
# (validate_enrichment; solution_full_html glue is gated by the mark-span
# rules there instead — the sentence frame comes from rubric patterns).
# ---------------------------------------------------------------------------

ENRICHMENT_CONTRACT = 2

_I_SPAN = re.compile(r"<i>(.*?)</i>", re.DOTALL)
_ANY_TAG = re.compile(r"<[^>]*>")
_SRC_OR_HREF = re.compile(r"\b(?:src|href)\s*=", re.IGNORECASE)
_TASK_TAGS = re.compile(r"</?(?:i|b)>|<br\s*/?>")     # task_html whitelist
_EXAMPLE_TAGS = re.compile(r"</?i>|<br\s*/?>")        # example_html whitelist
_WHY_TAGS = re.compile(r"</?i>")                      # why_en whitelist
_FULL_SOLUTION_TAGS = re.compile(r"</?(?:mark|i)>|<br\s*/?>")
_ITAL_TAG = re.compile(r"</?i>")
_BR_TAG = re.compile(r"<br\s*/?>")


@dataclass(frozen=True)
class BlockEnrichment:
    block: int
    task_html: str            # short re-authored task line (tags: i, b, br)
    example_html: str | None  # worked example from the rubric (tags: i, br)


@dataclass(frozen=True)
class ExerciseEnrichment:
    item_id: str
    solution_en: str  # plain-text English gloss of the solution
    why_en: str       # one-line grammar why (tags: i)
    solution_full_html: str | None  # complete sentence(s) (tags: mark, i,
    #   br), answer spans in <mark>; None = original solution is already
    #   the complete production


@dataclass(frozen=True)
class CourseEnrichment:
    lang: str
    unit: str
    block_tasks: dict[int, BlockEnrichment]
    exercises: dict[str, ExerciseEnrichment]


def _enrichment_error(path: Path, context: str,
                      message: str) -> CourseSourceError:
    return CourseSourceError(f"{path.name}: {context}: {message}")


def _checked_markup(path: Path, context: str, key: str, value: str,
                    tag_re: re.Pattern[str], allowed: str) -> str:
    """Whitelist-check one enrichment HTML field, return it unchanged.

    Same posture as the SVG guard: scripts, event handlers and resource
    references must be structurally impossible.  Attributes on allowed
    tags always leave ``<`` residue, so ``<i onclick=…>`` fails even
    before the explicit handler check.
    """
    lowered = value.lower()
    if _SVG_EVENT_HANDLER.search(lowered) or "javascript:" in lowered:
        raise _enrichment_error(
            path, context, f"{key} contains a script/event-handler pattern"
        )
    if _SRC_OR_HREF.search(lowered):
        raise _enrichment_error(
            path, context, f"{key} must not carry src/href attributes"
        )
    residue = tag_re.sub("", value)
    if "<" in residue or ">" in residue:
        raise _enrichment_error(
            path, context, f"{key} may contain only {allowed} markup"
        )
    return value


def parse_enrichment_file(path: Path) -> CourseEnrichment:
    """Parse one ``<lang>_<unit>.enrichment.json`` sidecar (contract 2)."""
    path = Path(path)
    match = re.fullmatch(
        r"([a-z]{2})_([a-z0-9]+(?:-[a-z0-9]+)*)\.enrichment\.json", path.name
    )
    if match is None or match.group(1) not in SUPPORTED_LANGS:
        raise CourseSourceError(
            f"{path.name}: filename must be <lang>_<unit>.enrichment.json"
        )
    lang, unit = match.group(1), match.group(2)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CourseSourceError(f"{path.name}: expected a JSON object")
    if data.get("lang") != lang or data.get("unit") != unit:
        raise CourseSourceError(
            f"{path.name}: lang/unit fields must match the filename"
        )
    if data.get("contract") != ENRICHMENT_CONTRACT:
        raise CourseSourceError(
            f"{path.name}: contract must be {ENRICHMENT_CONTRACT}, "
            f"got {data.get('contract')!r}"
        )

    blocks_raw = data.get("blocks")
    if not isinstance(blocks_raw, list) or not blocks_raw:
        raise CourseSourceError(f"{path.name}: blocks must be a nonempty array")
    block_tasks: dict[int, BlockEnrichment] = {}
    for raw in blocks_raw:
        if not isinstance(raw, dict):
            raise CourseSourceError(f"{path.name}: every block must be an object")
        block_no = raw.get("block")
        if not isinstance(block_no, int) or isinstance(block_no, bool) \
                or block_no < 1:
            raise CourseSourceError(f"{path.name}: block must be an integer >= 1")
        if block_no in block_tasks:
            raise CourseSourceError(f"{path.name}: duplicate block {block_no}")
        context = f"block {block_no}"
        task_html = raw.get("task_html")
        if not isinstance(task_html, str) or not task_html.strip():
            raise _enrichment_error(
                path, context, "task_html must be a nonempty string"
            )
        task_html = _checked_markup(
            path, context, "task_html", task_html.strip(),
            _TASK_TAGS, "<i>/<b>/<br>",
        )
        example_html = raw.get("example_html")
        if example_html is not None:
            if not isinstance(example_html, str) or not example_html.strip():
                raise _enrichment_error(
                    path, context, "example_html must be null or a nonempty string"
                )
            example_html = _checked_markup(
                path, context, "example_html", example_html.strip(),
                _EXAMPLE_TAGS, "<i>/<br>",
            )
        block_tasks[block_no] = BlockEnrichment(
            block=block_no, task_html=task_html, example_html=example_html
        )

    exercises_raw = data.get("exercises")
    if not isinstance(exercises_raw, list) or not exercises_raw:
        raise CourseSourceError(
            f"{path.name}: exercises must be a nonempty array"
        )
    exercises: dict[str, ExerciseEnrichment] = {}
    for raw in exercises_raw:
        if not isinstance(raw, dict):
            raise CourseSourceError(
                f"{path.name}: every exercise must be an object"
            )
        item_id = str(raw.get("id", "")).strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_\-]*", item_id):
            raise CourseSourceError(
                f"{path.name}: invalid or missing exercise id {item_id!r}"
            )
        if item_id in exercises:
            raise CourseSourceError(
                f"{path.name}: duplicate exercise id {item_id!r}"
            )
        solution_en = raw.get("solution_en")
        if not isinstance(solution_en, str) or not solution_en.strip():
            raise _enrichment_error(
                path, item_id, "solution_en must be a nonempty string"
            )
        solution_en = solution_en.strip()
        if "<" in solution_en:
            raise _enrichment_error(
                path, item_id, "solution_en must be plain text (no '<')"
            )
        why_en = raw.get("why_en")
        if not isinstance(why_en, str) or not why_en.strip():
            raise _enrichment_error(
                path, item_id, "why_en must be a nonempty string"
            )
        why_en = _checked_markup(
            path, item_id, "why_en", why_en.strip(), _WHY_TAGS, "<i>"
        )
        if "solution_full_html" not in raw:
            raise _enrichment_error(
                path, item_id,
                "solution_full_html is required (string or null)",
            )
        full = raw.get("solution_full_html")
        if full is not None:
            if not isinstance(full, str) or not full.strip():
                raise _enrichment_error(
                    path, item_id,
                    "solution_full_html must be null or a nonempty string",
                )
            full = _checked_markup(
                path, item_id, "solution_full_html", full.strip(),
                _FULL_SOLUTION_TAGS, "<mark>/<i>/<br>",
            )
            spans = _MARK_SPAN.findall(full)
            if not spans or any(not span.strip() for span in spans):
                raise _enrichment_error(
                    path, item_id,
                    "solution_full_html needs at least one nonempty <mark>",
                )
            if "___" in full:
                raise _enrichment_error(
                    path, item_id,
                    "solution_full_html still contains a blank placeholder",
                )
            text = _normalized_text(full)
            if not text or text[-1] not in ".!?":
                raise _enrichment_error(
                    path, item_id,
                    "solution_full_html must end with terminal "
                    "punctuation (./!/?)",
                )
        exercises[item_id] = ExerciseEnrichment(
            item_id=item_id, solution_en=solution_en, why_en=why_en,
            solution_full_html=full,
        )

    return CourseEnrichment(
        lang=lang, unit=unit, block_tasks=block_tasks, exercises=exercises
    )


def _normalized_text(text: str) -> str:
    """Whitespace-collapsed, entity-unescaped, tag-stripped plain text."""
    return " ".join(html.unescape(_ANY_TAG.sub(" ", text)).split())


def validate_enrichment(
    exercises: Sequence[CourseExercise], enrichment: CourseEnrichment
) -> None:
    """Cross-check a sidecar against its unit's parsed exercises.

    Enforces set EQUALITY on exercise ids and block numbers, plus the
    NO-INVENTED-GERMAN rule: every ``<i>`` span in task_html/example_html/
    why_en must appear verbatim (whitespace-normalized, tags stripped) in
    the concatenation of that block's source texts — instructions,
    prompts, solutions, alternatives.  This is the mechanical guarantee
    that codex only copied German from the book material, never wrote
    its own.
    """
    name = f"{enrichment.lang}_{enrichment.unit}.enrichment.json"
    if not exercises:
        raise CourseSourceError(f"{name}: no exercises to enrich")
    if exercises[0].lang != enrichment.lang \
            or exercises[0].unit != enrichment.unit:
        raise CourseSourceError(
            f"{name}: enrichment is for {enrichment.lang}:{enrichment.unit}, "
            f"exercises are {exercises[0].lang}:{exercises[0].unit}"
        )

    exercise_ids = {exercise.item_id for exercise in exercises}
    unknown = sorted(set(enrichment.exercises) - exercise_ids)
    if unknown:
        raise CourseSourceError(
            f"{name}: unknown exercise id(s): {', '.join(unknown)}"
        )
    missing = sorted(exercise_ids - set(enrichment.exercises))
    if missing:
        raise CourseSourceError(
            f"{name}: missing enrichment for exercise id(s): "
            f"{', '.join(missing)}"
        )

    blocks = {exercise.block for exercise in exercises}
    unknown_blocks = sorted(set(enrichment.block_tasks) - blocks)
    if unknown_blocks:
        raise CourseSourceError(f"{name}: unknown block(s): {unknown_blocks}")
    missing_blocks = sorted(blocks - set(enrichment.block_tasks))
    if missing_blocks:
        raise CourseSourceError(
            f"{name}: missing enrichment for block(s): {missing_blocks}"
        )

    # solution_full_html mark-span rules: the full sentence may add glue,
    # but every highlighted span must BE an original answer span, and every
    # original answer span must survive into the full sentence.
    for exercise in exercises:
        extra = enrichment.exercises[exercise.item_id]
        if extra.solution_full_html is None:
            continue
        original_spans = {
            _normalized_text(span)
            for span in _MARK_SPAN.findall(exercise.solution_html)
        }
        for span in _MARK_SPAN.findall(extra.solution_full_html):
            span_text = _normalized_text(span)
            if span_text not in original_spans:
                raise CourseSourceError(
                    f"{name}: {exercise.item_id}: solution_full_html <mark> "
                    f"span {span_text!r} does not match any <mark> span of "
                    "the original solution_html"
                )
        full_text = _normalized_text(extra.solution_full_html)
        for span_text in sorted(original_spans):
            if span_text not in full_text:
                raise CourseSourceError(
                    f"{name}: {exercise.item_id}: original solution <mark> "
                    f"span {span_text!r} is missing from solution_full_html"
                )

    pools: dict[int, str] = {}
    for block_no in blocks:
        parts: list[str] = []
        for exercise in exercises:
            if exercise.block != block_no:
                continue
            parts.extend((exercise.instruction, exercise.prompt,
                          exercise.solution_html, *exercise.alternatives))
        pools[block_no] = _normalized_text(" ".join(parts))

    def check_spans(context: str, key: str, value: str, pool: str) -> None:
        for span in _I_SPAN.findall(value):
            span_text = _normalized_text(span)
            if span_text and span_text not in pool:
                raise CourseSourceError(
                    f"{name}: {context}: {key} <i> span {span_text!r} is not "
                    "verbatim source text of its block "
                    "(no-invented-German rule)"
                )

    for block_no, block in enrichment.block_tasks.items():
        pool = pools[block_no]
        check_spans(f"block {block_no}", "task_html", block.task_html, pool)
        if block.example_html:
            check_spans(
                f"block {block_no}", "example_html", block.example_html, pool
            )
    for exercise in exercises:
        extra = enrichment.exercises[exercise.item_id]
        check_spans(
            exercise.item_id, "why_en", extra.why_en, pools[exercise.block]
        )


def speakable_solution_html(full_html: str) -> str:
    """A full solution reduced to ``<mark>``-only markup for the TTS lane.

    ``<i>`` unwrapped, ``<br>`` becomes a space, whitespace collapsed.
    This form passes validate_solution_html on the (already deployed)
    server and keeps solution_spoken_text free of tag noise, while still
    carrying the complete sentence — so the content hash, and therefore
    the voiced clip, follows the displayed solution automatically.
    """
    text = _ITAL_TAG.sub("", full_html)
    text = _BR_TAG.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def apply_effective_solutions(
    exercises: Sequence[CourseExercise],
    enrichment: CourseEnrichment | None,
) -> list[CourseExercise]:
    """Exercises whose solution_html carries the speakable EFFECTIVE form.

    Feed the result to the TTS clip plan (local_tts.course_expected_job_
    rows) so voicing follows the display: content hashes shift exactly for
    the exercises that gained a full sentence, everything else keeps its
    completed clip.  Display/build code must keep using the ORIGINAL
    exercises + enrichment.
    """
    if enrichment is None:
        return list(exercises)
    effective: list[CourseExercise] = []
    for exercise in exercises:
        extra = enrichment.exercises.get(exercise.item_id)
        if extra is None or extra.solution_full_html is None:
            effective.append(exercise)
        else:
            effective.append(replace(
                exercise,
                solution_html=speakable_solution_html(
                    extra.solution_full_html
                ),
            ))
    return effective


def enrich_seed_payload(payload: Any, enrichment: CourseEnrichment) -> Any:
    """Deep-copied exercises payload with effective speakable solutions.

    The seed server derives spoken text from the POSTed payload
    (parse_exercises_payload → solution_spoken_text), so substituting each
    row's solution_html here is the whole voicing change — no server-side
    change needed.  The caller MUST have parsed the payload and run
    validate_enrichment first; a bad sidecar aborts the seed.
    """
    substituted = copy.deepcopy(payload)
    if not isinstance(substituted, dict):
        return substituted
    for block in substituted.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        for raw in block.get("exercises") or []:
            if not isinstance(raw, dict):
                continue
            extra = enrichment.exercises.get(str(raw.get("id", "")).strip())
            if extra is not None and extra.solution_full_html is not None:
                raw["solution_html"] = speakable_solution_html(
                    extra.solution_full_html
                )
    return substituted


# ---------------------------------------------------------------------------
# Identity, decks, interleave
# ---------------------------------------------------------------------------


def lesson_guid(lang: str, unit: str, seq: int) -> str:
    return hashlib.sha1(
        f"idiomatic-course-lesson::{lang}::{unit}::{seq}".encode("utf-8")
    ).hexdigest()[:16]


def exercise_guid(lang: str, unit: str, item_id: str) -> str:
    return hashlib.sha1(
        f"idiomatic-course-exercise::{lang}::{unit}::{item_id}".encode("utf-8")
    ).hexdigest()[:16]


def _deck_id(deck_name: str) -> int:
    """Stable id from the full deck name, disjoint from the pool
    (1.82G), grammar and exercises2 (1.92G) formulas."""
    return 1_930_000_000 + (
        int(hashlib.sha1(
            f"idiomatic-course::{deck_name}".encode()
        ).hexdigest()[:8], 16) % 60_000_000
    )


def course_deck_names(
    lang: str, unit_label: str, *, root_override: str | None = None
) -> tuple[str, str]:
    """(lesson deck, exercises deck) for a unit.

    ``root_override`` supports disposable pilot decks; production units live
    under the estate tree: ``<ROOT>::2 Grammar::<unit_label>``.
    """
    root = root_override or f"{anki_root(lang)}::2 Grammar::{unit_label}"
    return f"{root}::1 Lesson", f"{root}::2 Exercises"


def interleave_plan(
    lesson: CourseLesson, exercises: Sequence[CourseExercise]
) -> list[tuple[str, str, int]]:
    """Sequenced first exposure encoded as new-card due positions.

    Returns ``(kind, key, due)`` rows: for each lesson card (= 2 slides) the
    lesson note, then its exercise block, then the next card — the dictated
    "2 slides → ~20 exercises → 2 slides → …" interleave.  ``key`` is the
    card seq (lesson) or item id (exercise).  Dues are 1-based, unique and
    contiguous.  A block number beyond the lesson's card count is an error;
    blocks may be empty (cards then follow one another directly).
    """
    seqs = {card.seq for card in lesson.cards}
    by_block: dict[int, list[CourseExercise]] = {}
    for exercise in exercises:
        if exercise.lang != lesson.lang or exercise.unit != lesson.unit:
            raise ValueError(
                f"exercise {exercise.item_id} belongs to "
                f"{exercise.lang}:{exercise.unit}, not "
                f"{lesson.lang}:{lesson.unit}"
            )
        if exercise.block not in seqs:
            raise ValueError(
                f"exercise {exercise.item_id} references block "
                f"{exercise.block}, but the lesson has cards 1..{len(seqs)}"
            )
        by_block.setdefault(exercise.block, []).append(exercise)

    plan: list[tuple[str, str, int]] = []
    due = 1
    for card in sorted(lesson.cards, key=lambda card: card.seq):
        plan.append(("lesson", str(card.seq), due))
        due += 1
        for exercise in by_block.get(card.seq, []):
            plan.append(("exercise", exercise.item_id, due))
            due += 1
    return plan


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"\*(.+?)\*")


def _inline_markup(text: str) -> str:
    escaped = html.escape(text)
    escaped = _BOLD.sub(r"<b>\1</b>", escaped)
    return _ITALIC.sub(r"<i>\1</i>", escaped)


def refs_html(refs: Sequence[str]) -> str:
    return " · ".join(
        ref if ref.startswith("Ch") else f"§{ref}" for ref in refs
    )


def side_html(side: CourseSide) -> str:
    """Display markup for one lesson slide, Sources footer included.

    A side with 2+ TL sentences renders them as a left-aligned example
    list (house dot markers, EN gloss in small light type under each
    sentence); a single TL keeps the classic centered rendering, with
    its gloss underneath in the same small light style.  SHOW notes
    break a list run and render as before.
    """
    parts = [f'<div class="cl-title">{_inline_markup(side.title)}</div>']
    list_mode = sum(1 for item in side.display if item.kind == "tl") >= 2

    def gloss_div(item: DisplayItem) -> str:
        if item.gloss is None:
            return ""
        return f'<div class="cl-en">{_inline_markup(item.gloss)}</div>'

    run: list[str] = []

    def flush_run() -> None:
        if run:
            parts.append(
                '<ul class="cl-tl-list">' + "".join(run) + "</ul>"
            )
            run.clear()

    for item in side.display:
        if item.kind == "tl":
            tl_div = f'<div class="cl-tl">{_inline_markup(item.text)}</div>'
            if list_mode:
                run.append(
                    f'<li class="cl-tl-item">{tl_div}{gloss_div(item)}</li>'
                )
            else:
                parts.append(tl_div)
                if item.gloss is not None:
                    parts.append(gloss_div(item))
        else:
            flush_run()
            parts.append(
                f'<div class="cl-note">{_inline_markup(item.text)}</div>'
            )
    flush_run()
    parts.append(
        f'<div class="cl-refs">Hammer {html.escape(refs_html(side.refs))}</div>'
    )
    return "\n".join(parts)


def load_side_svg(lesson: CourseLesson, side: CourseSide) -> str:
    """Read one authored diagram sidecar as inline-safe markup.

    Same guard as the podcast lessons: inline SVG goes verbatim into a note
    field rendered in a webview, so scripts and event handlers must be
    structurally impossible, not merely unauthored.
    """
    assert side.svg_file is not None
    path = lesson.path.parent / "svg" / side.svg_file
    markup = path.read_text(encoding="utf-8").strip()
    if markup.startswith("<?xml"):
        markup = markup.split("?>", 1)[1].strip()
    if not markup.startswith("<svg") or "viewBox" not in markup:
        raise ValueError(f"{path.name}: inline SVG needs an <svg …viewBox> root")
    lowered = markup.lower()
    if ("<script" in lowered or "javascript:" in lowered
            or _SVG_EVENT_HANDLER.search(lowered)):
        raise ValueError(f"{path.name}: scripts/event handlers are not allowed")
    if len(markup) > 200_000:
        raise ValueError(f"{path.name}: SVG too large to inline into a field")
    return markup


def _visual_field(lesson: CourseLesson, side: CourseSide) -> str:
    if side.svg_file is None:
        return ""
    return f'<div class="cl-img-wrap">{load_side_svg(lesson, side)}</div>'


def alts_html(exercise: CourseExercise) -> str:
    if not exercise.alternatives:
        return ""
    return "".join(
        f"<span>{html.escape(alt)}</span>" for alt in exercise.alternatives
    )


def exercise_solution_html(exercise: CourseExercise) -> str:
    """Escape everything outside the validated <mark> spans."""
    parts: list[str] = []
    cursor = 0
    for match in _MARK_SPAN.finditer(exercise.solution_html):
        parts.append(html.escape(exercise.solution_html[cursor:match.start()]))
        parts.append(f"<mark>{html.escape(match.group(1))}</mark>")
        cursor = match.end()
    parts.append(html.escape(exercise.solution_html[cursor:]))
    return "".join(parts)


def effective_solution_html(
    exercise: CourseExercise, enrichment: CourseEnrichment | None
) -> str:
    """What the back DISPLAYS: the complete production sentence.

    When the enrichment carries a solution_full_html string for this
    exercise, that markup is display-ready (whitelist-validated: mark, i,
    br) and is returned verbatim; otherwise the original solution renders
    exactly as before (everything outside its <mark> spans escaped).
    """
    if enrichment is not None:
        extra = enrichment.exercises.get(exercise.item_id)
        if extra is not None and extra.solution_full_html is not None:
            return extra.solution_full_html
    return exercise_solution_html(exercise)


def exercise_note_fields(
    exercise: CourseExercise,
    *,
    unit_label: str,
    solution_sound: str = "",
    enrichment: CourseEnrichment | None = None,
) -> list[str]:
    """The 15 EXERCISE_FIELDS values for one exercise note.

    With an enrichment sidecar, Instruction carries the block's short
    task_html (validated markup, inserted verbatim), the spare fields
    carry example/gloss/why, and SolutionHTML carries the EFFECTIVE
    solution — the complete production sentence when solution_full_html
    exists, the original solution otherwise (the field semantic is "what
    the back displays").  Without a sidecar everything is byte-identical
    to the legacy build.  Voicing follows the same effective solution via
    apply_effective_solutions in the TTS lane, never through this
    function.
    """
    instruction = html.escape(exercise.instruction)
    example = solution_en = why = ""
    if enrichment is not None:
        block = enrichment.block_tasks[exercise.block]
        extra = enrichment.exercises[exercise.item_id]
        instruction = block.task_html
        example = block.example_html or ""
        solution_en = html.escape(extra.solution_en)
        why = extra.why_en
    return [
        f"course:{exercise.lang}:{exercise.unit}:{exercise.item_id}",
        exercise.lang,
        unit_label,
        f"c{exercise.block:02d}",
        instruction,
        html.escape(exercise.prompt),
        effective_solution_html(exercise, enrichment),
        alts_html(exercise),
        html.escape(exercise.source_ref),
        "Hammer " + html.escape(refs_html(exercise.hammer_refs)),
        exercise.provenance,
        solution_sound,
        example,      # EXERCISE_EXAMPLE_FIELD (Extra1)
        solution_en,  # EXERCISE_SOLUTION_EN_FIELD (Extra2)
        why,          # EXERCISE_WHY_FIELD (Extra3)
    ]


def make_lesson_model() -> genanki.Model:
    return genanki.Model(
        LESSON_MODEL_ID,
        LESSON_MODEL_NAME,
        fields=[{"name": name} for name in LESSON_FIELDS],
        templates=[{"name": "Lesson", "qfmt": LESSON_FRONT, "afmt": LESSON_BACK}],
        css=LESSON_CSS,
    )


def make_exercise_model() -> genanki.Model:
    return genanki.Model(
        EXERCISE_MODEL_ID,
        EXERCISE_MODEL_NAME,
        fields=[{"name": name} for name in EXERCISE_FIELDS],
        templates=[{
            "name": "Exercise", "qfmt": EXERCISE_FRONT, "afmt": EXERCISE_BACK,
        }],
        css=EXERCISE_CSS,
    )


# ---------------------------------------------------------------------------
# APKG build
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SideAudio:
    """Rendered narration for one lesson side (absent = audio-pending)."""
    path: Path


def word_count(side: CourseSide) -> int:
    return sum(
        len(_WORD.findall(segment.text))
        for segment in side.segments
        if segment.kind == "speech"
    )


def build_course_apkg(
    *,
    out_path: Path,
    lesson: CourseLesson,
    exercises: Sequence[CourseExercise],
    root_override: str | None = None,
    lesson_audio: dict[tuple[int, str], SideAudio] | None = None,
    exercise_audio: dict[str, Path] | None = None,
    enrichment: CourseEnrichment | None = None,
) -> dict[str, Any]:
    """Package one unit — lesson + exercises — with interleaved due positions.

    Audio maps are optional: missing clips leave the audio fields empty and
    tag the note ``idiomatic-course-audio-pending`` (the local-TTS seeding
    contract is the documented follow-up; GUIDs are stable, so a rebuild
    with audio updates fields in place and preserves scheduling).

    ``enrichment`` is the optional sidecar (see parse_enrichment_file); it
    is cross-validated here so a bad sidecar can never half-ship through
    ANY caller.  Audio identity is untouched in both modes.
    """
    lesson_audio = lesson_audio or {}
    exercise_audio = exercise_audio or {}
    if enrichment is not None:
        validate_enrichment(exercises, enrichment)
    plan = interleave_plan(lesson, exercises)
    dues = {(kind, key): due for kind, key, due in plan}

    lesson_deck_name, exercise_deck_name = course_deck_names(
        lesson.lang, lesson.unit_label, root_override=root_override
    )
    lesson_deck = genanki.Deck(_deck_id(lesson_deck_name), lesson_deck_name)
    exercise_deck = genanki.Deck(_deck_id(exercise_deck_name), exercise_deck_name)
    media: list[str] = []
    media_seen: set[str] = set()
    audio_pending = 0

    def sound_tag(path: Path | None) -> str:
        nonlocal audio_pending
        if path is None:
            audio_pending += 1
            return ""
        path = Path(path)
        if not path.exists() or path.stat().st_size <= 0:
            raise ValueError(f"missing course media: {path}")
        key = str(path.resolve())
        if key not in media_seen:
            media.append(str(path))
            media_seen.add(key)
        return f"[sound:{path.name}]"

    base_tags = ["idiomatic-course",
                 f"idiomatic-course::{lesson.lang}::{lesson.unit}"]

    for card in sorted(lesson.cards, key=lambda card: card.seq):
        front_audio = lesson_audio.get((card.seq, "front"))
        back_audio = lesson_audio.get((card.seq, "back"))
        front_sound = sound_tag(front_audio.path if front_audio else None)
        back_sound = sound_tag(back_audio.path if back_audio else None)
        tags = [
            *base_tags,
            "idiomatic-course-lesson",
            f"idiomatic-course-block::{lesson.lang}::{lesson.unit}"
            f"::c{card.seq:02d}",
        ]
        if not (front_sound and back_sound):
            tags.append(AUDIO_PENDING_TAG)
        lesson_deck.add_note(genanki.Note(
            model=make_lesson_model(),
            fields=[
                f"course:{lesson.lang}:{lesson.unit}:{card.seq}",
                lesson.unit_label,
                str(card.seq),
                lesson.lang,
                side_html(card.front),
                side_html(card.back),
                front_sound,
                back_sound,
                _visual_field(lesson, card.front),
                _visual_field(lesson, card.back),
                "", "", "", "",
            ],
            guid=lesson_guid(lesson.lang, lesson.unit, card.seq),
            tags=tags,
            due=dues[("lesson", str(card.seq))],
        ))

    for exercise in exercises:
        solution_sound = sound_tag(exercise_audio.get(exercise.item_id))
        tags = [
            *base_tags,
            "idiomatic-course-exercise",
            f"idiomatic-course-block::{exercise.lang}::{exercise.unit}"
            f"::c{exercise.block:02d}",
            f"idiomatic-course-src::{exercise.provenance}",
        ]
        if not solution_sound:
            tags.append(AUDIO_PENDING_TAG)
        exercise_deck.add_note(genanki.Note(
            model=make_exercise_model(),
            fields=exercise_note_fields(
                exercise,
                unit_label=lesson.unit_label,
                solution_sound=solution_sound,
                enrichment=enrichment,
            ),
            guid=exercise_guid(exercise.lang, exercise.unit, exercise.item_id),
            tags=tags,
            due=dues[("exercise", exercise.item_id)],
        ))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package([lesson_deck, exercise_deck])
    package.media_files = media
    package.write_to_file(str(out_path))
    result = {
        "lang": lesson.lang,
        "unit": lesson.unit,
        "lesson_cards": len(lesson.cards),
        "exercises": len(exercises),
        "notes": len(lesson.cards) + len(exercises),
        "audio_pending": audio_pending,
        "enriched": enrichment is not None,
        "decks": [lesson_deck_name, exercise_deck_name],
        "size_kb": round(out_path.stat().st_size / 1e3),
    }
    log.info("grammar.course.apkg_written", path=str(out_path), **result)
    return result


# ---------------------------------------------------------------------------
# Narration audio (local-TTS lane — design doc §6)
# ---------------------------------------------------------------------------

_BRACKETED = re.compile(r"\[[^\]]*\]")
_PARENTHETICAL = re.compile(r"\([^)]*\)")


def speech_segments(side: CourseSide) -> tuple[Segment, ...]:
    """The side's spoken segments in script order (pauses excluded).

    The ordinal of a segment in this tuple is its clip index — the
    ``segNNN`` clip kind in the local-TTS queue.
    """
    return tuple(seg for seg in side.segments if seg.kind == "speech")


def solution_spoken_text(exercise: CourseExercise) -> str:
    """The exercise solution as text for the TL voice.

    ``<mark>`` unwrapped; bracketed original-prompt fragments (``[der
    weite Weg]``) and parenthetical key commentary (often English)
    removed; whitespace collapsed. Raises if nothing speakable remains.
    """
    text = _MARK_SPAN.sub(lambda m: m.group(1), exercise.solution_html)
    text = _BRACKETED.sub(" ", text)
    text = _PARENTHETICAL.sub(" ", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", re.sub(r"\s+", " ", text)).strip()
    if not text:
        raise ValueError(
            f"exercise {exercise.item_id} has no speakable solution text"
        )
    return text


def _uniform_speech_clip(clip: Path) -> Path:
    """Re-encode one clip to the house 24 kHz mono so the concat demuxer's
    ``-c copy`` splice stays within defined behavior (see pipeline/audio.py).
    Cached beside the input; idempotent."""
    out = clip.with_name(f"{clip.stem}_u24m.mp3")
    if out.exists() and out.stat().st_size > 0:
        return out
    temporary = out.with_name(f".{out.stem}.building.mp3")
    temporary.unlink(missing_ok=True)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(clip),
             "-ar", "24000", "-ac", "1",
             "-c:a", "libmp3lame", "-q:a", "4", str(temporary)],
            check=True,
        )
        temporary.replace(out)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return out


def stitch_side_narration(
    side: CourseSide,
    clips_by_speech_index: dict[int, Path],
    *,
    out_path: Path,
    work_dir: Path,
    silence_fn: Any = silence_mp3,
    concat_fn: Any = concat_mp3s,
    level_fn: Any = leveled_speech_clip,
    uniform_fn: Any = _uniform_speech_clip,
) -> Path:
    """Stitch one side's narration from its per-segment clips.

    Follows the explainer renderer's conventions: every speech clip is
    leveled to the house loudness target, consecutive speech segments get
    a short breathing gap, explicit ``[PAUSE:ms]`` segments become
    silence, and the concat pass loudnorm-levels the result. The caller
    provides a COMPLETE clip map — a missing segment is an error here
    (the graceful audio-pending path is decided by the caller, per side).
    """
    speech = speech_segments(side)
    missing = [i for i in range(len(speech)) if i not in clips_by_speech_index]
    if missing:
        raise ValueError(
            f"card {side.seq} {side.side} narration is missing segment "
            f"clip(s): {missing}"
        )
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    pieces: list[Path] = []
    speech_index = 0
    previous_kind: str | None = None
    for segment in side.segments:
        if segment.kind == "pause":
            ms = int(segment.text) if segment.text else PAUSE_MS
            pieces.append(silence_fn(work_dir, ms))
        elif segment.kind == "speech":
            if previous_kind == "speech":
                pieces.append(silence_fn(work_dir, BETWEEN_SPEECH_MS))
            clip = Path(clips_by_speech_index[speech_index])
            pieces.append(uniform_fn(level_fn(clip)))
            speech_index += 1
        else:
            # Course narration is speech+pause only; chime/music/think are
            # podcast flavor and deliberately unsupported here.
            raise ValueError(
                f"card {side.seq} {side.side}: unsupported narration "
                f"segment kind {segment.kind!r}"
            )
        previous_kind = segment.kind
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    concat_fn(pieces, out_path)
    return out_path
