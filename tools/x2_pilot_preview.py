#!/usr/bin/env python3
"""Render the three gated Exercises2 new-format pilots for owner review.

The preview is intentionally static and audio-free.  It validates each full
input/notes/triage artifact set through the normal batch gate, re-parses the
kept rows with the card model's schema, and writes only the explicitly named
HTML output.  It never builds an APKG, calls TTS, or delivers content.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from idiomatic.grammar import exercises2 as x2  # noqa: E402
from idiomatic.grammar import exercises2_shadowing as shadow  # noqa: E402
from tools import x2_batch_gate as gate  # noqa: E402

BATCH_DIR = REPO / "idiomatic" / "grammar" / "data" / "exercises2" / "batches"


class PreviewError(ValueError):
    """A commissioned pilot is incomplete or unsafe to preview."""


@dataclass(frozen=True)
class PilotSpec:
    chunk: str
    gate_name: str
    title: str
    format: Literal["production", "definition", "shadowing"]
    category: frozenset[str]


PILOTS = (
    PilotSpec(
        chunk="es_fancy_vocab_pilot_b01",
        gate_name="V1",
        title="ES FANCY_VOCAB",
        format="production",
        category=frozenset(
            {
                "lexical-verb",
                "lexical-noun",
                "lexical-adjective",
                "lexical-adverb",
                "lexical-expression",
            }
        ),
    ),
    PilotSpec(
        chunk="es_geopolitics_pilot_b01",
        gate_name="V2",
        title="ES GEOPOLITICS",
        format="definition",
        category=frozenset({"term-definition"}),
    ),
    PilotSpec(
        chunk="pt_big_tech_phrases_pilot_b01",
        gate_name="P1",
        title="PT BIG_TECH_PHRASES",
        format="shadowing",
        category=shadow.CATEGORIES,
    ),
)

_EXPECTED_INPUTS = 30
_AUDIO_ANSWER = "Local Qwen · answer clip pending owner voicing clearance"
_AUDIO_EXAMPLE = "Local Qwen · example clip pending owner voicing clearance"
_AUDIO_SHADOW = "Local Qwen · full-sentence clip pending owner voicing clearance"


@dataclass(frozen=True)
class PilotData:
    spec: PilotSpec
    notes: tuple[dict, ...]
    triage: tuple[dict, ...]
    stats: dict
    source_hashes: tuple[tuple[str, str], ...]


def _load_array(path: Path) -> list[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreviewError(f"{path.name}: cannot read JSON: {exc}") from exc
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise PreviewError(f"{path.name}: expected an array of objects")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pilot_paths(batch_dir: Path, chunk: str) -> tuple[Path, Path, Path]:
    return (
        batch_dir / "input" / f"{chunk}.json",
        batch_dir / "output" / f"{chunk}_notes.json",
        batch_dir / "output" / f"{chunk}_triage.json",
    )


def _validate_format(spec: PilotSpec, notes: list[dict]) -> None:
    lang, topic = gate._chunk_lang_topic(spec.chunk)
    if spec.format == "shadowing":
        try:
            parsed = shadow.parse_notes_data(
                notes, lang=lang, source_name=f"{spec.chunk}_notes.json"
            )
        except shadow.ShadowSourceError as exc:
            raise PreviewError(str(exc)) from exc
        categories = {note.category for note in parsed}
    else:
        parsed_x2: list[x2.Ex2Note] = []
        for raw in notes:
            try:
                parsed_x2.append(
                    x2._parse_note(Path(f"{lang}_{topic}.json"), lang, topic, raw)
                )
            except x2.Ex2SourceError as exc:
                raise PreviewError(str(exc)) from exc
        categories = {note.category for note in parsed_x2}

    outside_contract = categories - spec.category
    if outside_contract:
        raise PreviewError(
            f"{spec.chunk}: categories outside {spec.gate_name} contract: "
            f"{sorted(outside_contract)}"
        )
    if spec.format == "definition":
        without_definition = [
            str(row.get("id", "<missing>"))
            for row in notes
            if not isinstance(row.get("note"), str) or not row["note"].strip()
        ]
        if without_definition:
            raise PreviewError(
                f"{spec.chunk}: corrected definition missing from note: "
                f"{without_definition[:5]}"
            )


def load_pilots(batch_dir: Path = BATCH_DIR) -> tuple[PilotData, ...]:
    """Load all commissioned pilots, refusing any artifact that fails its gate."""
    batch_dir = Path(batch_dir)
    result: list[PilotData] = []
    for spec in PILOTS:
        ok, problems, stats = gate.gate_chunk(spec.chunk, batch_dir=batch_dir)
        if not ok:
            details = "; ".join(problems)
            raise PreviewError(f"{spec.chunk}: mechanical gate failed: {details}")
        if stats.get("inputs") != _EXPECTED_INPUTS:
            raise PreviewError(
                f"{spec.chunk}: expected {_EXPECTED_INPUTS} pilot inputs, "
                f"found {stats.get('inputs')}"
            )
        input_path, notes_path, triage_path = _pilot_paths(batch_dir, spec.chunk)
        notes = _load_array(notes_path)
        triage = _load_array(triage_path)
        if not notes:
            raise PreviewError(f"{spec.chunk}: no kept notes to render")
        _validate_format(spec, notes)
        source_hashes = tuple(
            (path.name, _sha256(path))
            for path in (input_path, notes_path, triage_path)
        )
        result.append(
            PilotData(
                spec=spec,
                notes=tuple(notes),
                triage=tuple(triage),
                stats=stats,
                source_hashes=source_hashes,
            )
        )
    return tuple(result)


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _audio_placeholder(text: str) -> str:
    return f'<div class="audio-placeholder" role="note">{_e(text)}</div>'


def _alts(values: object) -> str:
    if not isinstance(values, list) or not values:
        return ""
    return '<div class="alts">' + "".join(
        f"<span>{_e(value)}</span>" for value in values
    ) + "</div>"


def _optional_block(css_class: str, label: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    return (
        f'<div class="{css_class}"><strong>{_e(label)}</strong>'
        f"<p>{_e(value)}</p></div>"
    )


def _card(title: str, side: str, body: str) -> str:
    return (
        '<article class="card">'
        f'<div class="card-heading"><span>{_e(title)}</span><span>{_e(side)}</span></div>'
        f"{body}</article>"
    )


def _metadata(topic: str, category: object) -> str:
    return f'<div class="meta">{_e(topic)} · {_e(category)}</div>'


def _production_cards(raw: dict, *, definition: bool) -> str:
    topic = "Geopolítica" if definition else "Vocabulario académico"
    meta = _metadata(topic, raw.get("category", ""))
    production_front = (
        f"{meta}<div class=\"prompt\">{_e(raw.get('en', ''))}</div>"
        '<div class="hint">→ español</div>'
    )
    definition_block = (
        _optional_block(
            "definition",
            "Corrected definition (from audit note)",
            raw.get("note", ""),
        )
        if definition
        else ""
    )
    production_back = (
        f"{meta}<div class=\"answer\">{_e(raw.get('tl', ''))}</div>"
        f"{_audio_placeholder(_AUDIO_ANSWER)}{_alts(raw.get('alts'))}"
        f'<div class="register">{_e(raw.get("register", ""))}</div>'
        f'{_optional_block("trap", "Interference trap", raw.get("trap", ""))}'
        f"{definition_block}<hr>"
        f'<div class="example">{x2.example_tl_html(str(raw.get("cloze", "")))}</div>'
        f"{_audio_placeholder(_AUDIO_EXAMPLE)}"
        f'<div class="translation">{_e(raw.get("example_en", ""))}</div>'
    )
    cloze_front = (
        f"{meta}<div class=\"cloze\">"
        f"{x2.cloze_front_html(str(raw.get('cloze', '')))}</div>"
        f'<div class="hint">{_e(raw.get("en", ""))}</div>'
    )
    cloze_back = (
        f"{meta}<div class=\"example\">"
        f"{x2.example_tl_html(str(raw.get('cloze', '')))}</div>"
        f"{_audio_placeholder(_AUDIO_EXAMPLE)}"
        f'<div class="answer compact">{_e(raw.get("tl", ""))}</div>'
        f"{_alts(raw.get('alts'))}{definition_block}<hr>"
        f'<div class="translation">{_e(raw.get("example_en", ""))}</div>'
    )
    return '<div class="card-grid">' + "".join(
        (
            _card("Production", "question", production_front),
            _card("Production", "answer", production_back),
            _card("Cloze", "question", cloze_front),
            _card("Cloze", "answer", cloze_back),
        )
    ) + "</div>"


def _highlight_focus(tl: object, focus: object) -> str:
    tl_text = str(tl)
    focus_text = str(focus)
    match = re.search(re.escape(focus_text), tl_text, flags=re.IGNORECASE)
    if match is None:
        # The schema gate should make this unreachable, but escaping the full
        # target remains the safe rendering if the contract changes later.
        return _e(tl_text)
    return (
        _e(tl_text[: match.start()])
        + f"<mark>{_e(tl_text[match.start() : match.end()])}</mark>"
        + _e(tl_text[match.end() :])
    )


def _shadowing_cards(raw: dict) -> str:
    meta_shadow = _metadata("BIG_TECH_PHRASES · listen, then shadow", raw.get("category", ""))
    meta_cue = _metadata("BIG_TECH_PHRASES · produce, then compare", raw.get("category", ""))
    listen_front = f"{meta_shadow}{_audio_placeholder(_AUDIO_SHADOW)}"
    listen_back = (
        f'{meta_shadow}<div class="answer">'
        f'{_highlight_focus(raw.get("tl", ""), raw.get("focus_tl", ""))}</div>'
        f'<div class="focus">{_e(raw.get("focus_tl", ""))}</div>'
        f'<div class="prompt compact">{_e(raw.get("en", ""))}</div>'
        f'{_optional_block("trap", "Interference trap", raw.get("trap", ""))}'
        f'{_optional_block("audit-note", "Audit note", raw.get("note", ""))}'
    )
    cue_front = (
        f'{meta_cue}<div class="prompt">{_e(raw.get("en", ""))}</div>'
        f'<div class="focus">{_e(raw.get("focus_en", ""))}</div>'
    )
    cue_back = (
        f'{meta_cue}<div class="answer">'
        f'{_highlight_focus(raw.get("tl", ""), raw.get("focus_tl", ""))}</div>'
        f"{_audio_placeholder(_AUDIO_SHADOW)}"
        f'<div class="focus">{_e(raw.get("focus_tl", ""))}</div>'
        f'<div class="register">{_e(raw.get("register", ""))}</div>'
        f'{_optional_block("trap", "Interference trap", raw.get("trap", ""))}'
    )
    return '<div class="card-grid">' + "".join(
        (
            _card("Listen & Shadow", "question", listen_front),
            _card("Listen & Shadow", "answer", listen_back),
            _card("Cue & Produce", "question", cue_front),
            _card("Cue & Produce", "answer", cue_back),
        )
    ) + "</div>"


def _dropped_rows(triage: tuple[dict, ...]) -> str:
    dropped = [row for row in triage if row.get("verdict") == "drop"]
    if not dropped:
        return ""
    rows = "".join(
        "<tr>"
        f'<td><code>{_e(row.get("id", ""))}</code></td>'
        f'<td>{_e(row.get("en", ""))}</td>'
        f'<td>{_e(row.get("reason", ""))}</td>'
        "</tr>"
        for row in dropped
    )
    return (
        '<details class="dropped"><summary>'
        f"{len(dropped)} triaged source rows not rendered as cards"
        "</summary><table><thead><tr><th>ID</th><th>Source</th><th>Reason</th>"
        f"</tr></thead><tbody>{rows}</tbody></table></details>"
    )


def _pilot_section(data: PilotData) -> str:
    spec = data.spec
    rendered_notes = []
    for index, raw in enumerate(data.notes, start=1):
        cards = (
            _shadowing_cards(raw)
            if spec.format == "shadowing"
            else _production_cards(raw, definition=spec.format == "definition")
        )
        rendered_notes.append(
            '<section class="note">'
            f'<h3><span>{index:02d}</span> {_e(raw.get("id", ""))}</h3>{cards}</section>'
        )
    hash_rows = "".join(
        f"<li><code>{_e(name)}</code> <code>{_e(digest)}</code></li>"
        for name, digest in data.source_hashes
    )
    return (
        f'<section class="pilot" id="{_e(spec.gate_name.lower())}">'
        f'<header><span class="gate">Gate {_e(spec.gate_name)}</span>'
        f"<h2>{_e(spec.title)}</h2>"
        f'<p class="status">Mechanical gate passed · {data.stats["inputs"]} audited · '
        f'{data.stats["keep"]} rendered · {data.stats["drop"]} dropped</p></header>'
        '<details class="provenance"><summary>Validated source hashes</summary>'
        f"<ul>{hash_rows}</ul></details>"
        f"{''.join(rendered_notes)}{_dropped_rows(data.triage)}</section>"
    )


_CSS = """
:root { color-scheme: light dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  background: #151515; color: #ece9e2; }
* { box-sizing: border-box; }
body { margin: 0; background: #151515; }
main { width: min(1500px, 100%); margin: auto; padding: 36px 24px 80px; }
h1 { font-family: Georgia, serif; font-size: clamp(34px, 6vw, 72px); margin: 0 0 12px; }
.lede { color: #b9b4aa; max-width: 780px; font-size: 18px; line-height: 1.55; }
nav { display: flex; flex-wrap: wrap; gap: 10px; margin: 28px 0 48px; }
nav a, .gate { border: 1px solid #6f675b; color: #e7d5af; padding: 7px 12px;
  border-radius: 999px; text-decoration: none; font-size: 13px; letter-spacing: .05em; }
.pilot { border-top: 1px solid #49453f; padding-top: 42px; margin-top: 54px; }
.pilot > header h2 { font-family: Georgia, serif; font-size: clamp(30px, 4vw, 48px);
  margin: 14px 0 6px; }
.status { color: #a9c7a6; }
.provenance, .dropped { color: #aaa49a; margin: 18px 0; }
.provenance code { overflow-wrap: anywhere; }
.note { margin: 38px 0 64px; }
.note h3 { color: #cbc5b9; font-size: 14px; font-weight: 500; letter-spacing: .06em; }
.note h3 span { color: #8d867b; margin-right: 8px; }
.card-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.card { background: #f6f6f3; color: #1f2023; border-radius: 14px; min-height: 310px;
  padding: 20px; text-align: center; box-shadow: 0 8px 30px #0005; }
.card-heading { display: flex; justify-content: space-between; color: #77736d;
  border-bottom: 1px solid #e0ddd5; padding-bottom: 10px; margin-bottom: 22px;
  font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }
.meta { color: #77736d; text-transform: uppercase; letter-spacing: .08em; font-size: 12px; }
.prompt, .answer, .example, .cloze { font-family: Georgia, serif; line-height: 1.42;
  font-size: clamp(21px, 2.4vw, 31px); max-width: 680px; margin: 20px auto 10px; }
.answer { color: #9e2b33; }
.compact { font-size: clamp(17px, 1.8vw, 23px); }
.hint, .translation, .register { color: #67645f; margin: 10px auto; max-width: 650px; }
.focus { font-weight: 700; margin: 12px auto; max-width: 640px; }
.alts span { display: inline-block; border: 1px solid #d8d3c9; border-radius: 999px;
  padding: 3px 9px; margin: 3px; }
.audio-placeholder { border: 1px dashed #90723d; color: #755b2e; background: #f7eedc;
  border-radius: 8px; width: fit-content; max-width: 100%; padding: 7px 10px; margin: 14px auto;
  font-size: 13px; }
.trap, .definition, .audit-note { text-align: left; max-width: 650px; margin: 16px auto;
  padding: 10px 14px; border-radius: 0 8px 8px 0; }
.trap { background: #f5eedd; border-left: 3px solid #8c6a1d; }
.definition { background: #e9f0f6; border-left: 3px solid #356b91; }
.audit-note { background: #eeece8; border-left: 3px solid #77736d; }
.trap p, .definition p, .audit-note p { margin: 6px 0 0; line-height: 1.45; }
mark { background: #f4dfe0; color: inherit; padding: 0 3px; border-radius: 3px; }
.blank { display: inline-block; min-width: 3.2em; height: .85em;
  border-bottom: 2px solid #9e2b33; }
hr { border: 0; border-top: 1px solid #ddd8ce; margin: 20px 0; }
table { border-collapse: collapse; width: 100%; margin-top: 12px; color: #d5d0c7; }
th, td { border-bottom: 1px solid #45413c; padding: 9px; text-align: left; vertical-align: top; }
@media (max-width: 850px) { .card-grid { grid-template-columns: 1fr; } main { padding: 24px 14px; } }
""".strip()


def render_html(pilots: Sequence[PilotData]) -> str:
    """Return byte-stable HTML for already validated pilot data."""
    if tuple(data.spec for data in pilots) != PILOTS:
        raise PreviewError("preview requires V1, V2, and P1 in commissioned order")
    nav = "".join(
        f'<a href="#{_e(spec.gate_name.lower())}">{_e(spec.gate_name)} · '
        f"{_e(spec.title)}</a>"
        for spec in PILOTS
    )
    sections = "".join(_pilot_section(data) for data in pilots)
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Exercises2 new-format pilot review</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n<main>\n"
        "<h1>Exercises2 pilot review</h1>\n"
        '<p class="lede">Three format gates, rendered from mechanically validated '
        "authoring artifacts. Audio panels are local-Qwen placeholders only: this "
        "preview does not synthesize, build, deliver, or record an owner verdict.</p>\n"
        f"<nav>{nav}</nav>\n{sections}\n</main>\n</body>\n</html>\n"
    )


def write_preview(output: Path, *, batch_dir: Path = BATCH_DIR) -> int:
    """Validate all artifacts and deterministically write one explicit output."""
    pilots = load_pilots(batch_dir)
    rendered = render_html(pilots)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8", newline="")
    return sum(len(pilot.notes) for pilot in pilots)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="static HTML output path")
    parser.add_argument(
        "--batch-dir",
        type=Path,
        default=BATCH_DIR,
        help="Exercises2 batches root (default: repository corpus)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        count = write_preview(args.output, batch_dir=args.batch_dir)
    except (PreviewError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {args.output}: {count} kept notes across V1, V2, and P1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
