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

import hashlib
import html
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
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
    "Extra1",
    "Extra2",
    "Extra3",
]

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
.cx-instr {font-size: clamp(13px, 3vw, 17px); color: #6c6d66;
           line-height: 1.45; margin: 10px auto; max-width: 620px;}
.cx-prompt {font-family: Georgia, 'Times New Roman', serif;
            font-size: clamp(20px, 4.8vw, 28px); line-height: 1.5;
            margin: 16px auto; max-width: 640px;}
.cx-solution {font-family: Georgia, 'Times New Roman', serif;
              font-size: clamp(20px, 4.8vw, 28px); line-height: 1.5;
              margin: 16px auto; max-width: 640px;}
.cx-solution mark {background: #f4dfe0; color: inherit; padding: 0 3px;
                   border-radius: 3px; font-weight: 600;}
.cx-alts {font-size: clamp(13px, 3vw, 16px); color: #6c6d66; margin: 4px auto 10px;}
.cx-alts span {display: inline-block; border: 1px solid #e1e1d8;
               border-radius: 999px; padding: 1px 10px; margin: 2px 3px;
               color: #1f2023;}
.cx-refs {font-size: clamp(11px, 2.4vw, 13px); color: #9b978e;
          letter-spacing: 0.03em; margin-top: 16px;}
hr#answer {border: 0; border-top: 1px solid #e1e1d8; margin: 18px 0;}
.card.night_mode, .card.nightMode {background: #1b1a19; color: #edeae4;}
.card.night_mode .cx-meta, .card.nightMode .cx-meta {color: #9b978e;}
.card.night_mode .cx-instr, .card.nightMode .cx-instr {color: #9b978e;}
.card.night_mode .cx-alts, .card.nightMode .cx-alts {color: #9b978e;}
.card.night_mode .cx-alts span, .card.nightMode .cx-alts span
  {border-color: #343230; color: #edeae4;}
.card.night_mode .cx-solution mark, .card.nightMode .cx-solution mark
  {background: #4a3032; color: #edeae4;}
.card.night_mode .cx-refs, .card.nightMode .cx-refs {color: #7d7a72;}
.card.night_mode hr#answer, .card.nightMode hr#answer
  {border-top-color: #343230;}
"""

EXERCISE_FRONT = """<div class="cx-meta">{{Unit}} · {{Block}}</div>
<div class="cx-instr">{{Instruction}}</div>
<div class="cx-prompt">{{PromptHTML}}</div>"""

EXERCISE_BACK = """<div class="cx-meta">{{Unit}} · {{Block}}</div>
<div class="cx-solution">{{SolutionHTML}}</div>
{{SolutionAudio}}
{{#AltsHTML}}<div class="cx-alts">{{AltsHTML}}</div>{{/AltsHTML}}
<hr id="answer">
<div class="cx-refs">{{HammerRefs}} · {{SourceRef}} · {{Provenance}}</div>"""

AUDIO_PENDING_TAG = "idiomatic-course-audio-pending"

_REF_ID = re.compile(r"(?:\d{1,2}(?:\.\d{1,3}){0,3}[a-z]?|Ch\.\s?\d{1,2})")
_MARK_SPAN = re.compile(r"<mark>(.*?)</mark>", re.DOTALL)
_SVG_EVENT_HANDLER = re.compile(r"\son[a-z]+\s*=")


class CourseSourceError(ValueError):
    """A Grammar Course source file does not satisfy its contract."""


# ---------------------------------------------------------------------------
# Lesson source parsing (Markdown, podcast-cards line grammar + REF:)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DisplayItem:
    kind: Literal["show", "tl"]
    text: str


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
    for line_no, raw in physical_lines:
        line = raw.strip()
        if line.startswith(("TITLE:", "SVG:", "REF:")):
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
    """Display markup for one lesson slide, Sources footer included."""
    parts = [f'<div class="cl-title">{_inline_markup(side.title)}</div>']
    for item in side.display:
        css_class = "cl-tl" if item.kind == "tl" else "cl-note"
        parts.append(f'<div class="{css_class}">{_inline_markup(item.text)}</div>')
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
) -> dict[str, Any]:
    """Package one unit — lesson + exercises — with interleaved due positions.

    Audio maps are optional: missing clips leave the audio fields empty and
    tag the note ``idiomatic-course-audio-pending`` (the local-TTS seeding
    contract is the documented follow-up; GUIDs are stable, so a rebuild
    with audio updates fields in place and preserves scheduling).
    """
    lesson_audio = lesson_audio or {}
    exercise_audio = exercise_audio or {}
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
            fields=[
                f"course:{exercise.lang}:{exercise.unit}:{exercise.item_id}",
                exercise.lang,
                lesson.unit_label,
                f"c{exercise.block:02d}",
                html.escape(exercise.instruction),
                html.escape(exercise.prompt),
                exercise_solution_html(exercise),
                alts_html(exercise),
                html.escape(exercise.source_ref),
                "Hammer " + html.escape(refs_html(exercise.hammer_refs)),
                exercise.provenance,
                solution_sound,
                "", "", "",
            ],
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
