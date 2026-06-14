"""Build a single Anki .apkg containing one card per enriched idiom.

Card layout — display fields for visual reference, audio carries the
pedagogical load. Same template philosophy as pimsleur's
"YouTube Idiom Card v3 Structured".

GUID: yt-idiom-cloud::<youtube_id>::<normalized phrase> — stable so
re-imports update in place if a video gets re-processed.
"""

from __future__ import annotations

import hashlib
import html
import os
import shutil
from pathlib import Path

import genanki
import structlog

from .explain import Enriched

log = structlog.get_logger()


# Stable model_id distinct from pimsleur's 1820114600/700/800/900 ranges.
MODEL_ID = 1_820_120_000
MODEL_NAME = "Idiomatic Cloud Card v1"


# Field labels for the structured-explanation sections (English).
EXPL_LABELS = {
    "usage":               "Usage",
    "collocations":        "Typical collocations",
    "synonyms_formal":     "More formal alternative",
    "synonyms_neutral":    "Close synonym",
    "synonyms_colloquial": "More casually",
    "antonyms":            "Opposite",
    "register_note":       "Register",
    "metaphor":            "Image / etymology",
    "pitfall":             "Grammatical pitfall",
    "false_friend":        "False-friend warning",
}


# ---- HTML helpers ---------------------------------------------------------

def _vocab_table_html(structured: dict[str, str]) -> str:
    if not structured:
        return ""
    rows = []
    for k, v in structured.items():
        label = EXPL_LABELS.get(k, k.replace("_", " ").title())
        rows.append(
            f'<div class="expl-section">'
            f'<div class="expl-label">{html.escape(label)}</div>'
            f'<div class="expl-text">{html.escape(v)}</div>'
            f'</div>'
        )
    return "".join(rows)


def _examples_html(examples: list[dict]) -> str:
    if not examples:
        return ""
    blocks = []
    for ex in examples:
        blocks.append(
            f'<div class="example-block">'
            f'<div class="ex-tgt">{html.escape(ex.get("target",""))}</div>'
            f'<div class="ex-en">{html.escape(ex.get("en",""))}</div>'
            f'</div>'
        )
    return "".join(blocks)


# ---- model ---------------------------------------------------------------

FRONT_TMPL = """<div class="idiom">{{Phrase}}</div>
<div class="en">{{English}}</div>
<div class="audio-row">{{FrontAudio}}</div>"""

BACK_TMPL = """<div class="idiom">{{Phrase}}</div>
<div class="en">{{English}}</div>
<div class="audio-row">{{FrontAudio}}</div>
<hr id="answer">

{{#StructuredHTML}}
{{StructuredHTML}}
{{/StructuredHTML}}

{{#ExamplesHTML}}
<div class="prompt-label">Examples</div>
{{ExamplesHTML}}
{{/ExamplesHTML}}

<div class="prompt-label">Drill</div>
<div class="audio-row">{{BackAudio}}</div>

<div class="footer">{{Source}}</div>"""

CSS = """
.card {font-family: -apple-system, system-ui, "Noto Sans CJK SC", sans-serif;
       background:#fff; color:#000; text-align:center; padding:16px 12px;}
.idiom {font-size: clamp(32px, 7vw, 56px); font-weight:600;
        margin:20px 0 6px; color:#111; line-height:1.2;}
.en {font-size: clamp(16px, 3.4vw, 20px); color:#555;
     max-width:580px; margin:0 auto 16px; line-height:1.4;}
.audio-row {margin:12px 0;}
hr#answer {border:0; border-top:1px solid #ccc; margin:20px 0;}
.prompt-label {font-size: clamp(11px, 2.4vw, 14px); color:#888;
               letter-spacing:0.06em; text-transform:uppercase;
               margin-top:22px; margin-bottom:8px;}

.expl-section {text-align: left; max-width: 580px;
               margin: 12px auto 0; padding: 0 4px;}
.expl-label {font-size: clamp(11px, 2.4vw, 14px); color: #888;
             letter-spacing: 0.06em; text-transform: uppercase;
             margin-top: 14px; margin-bottom: 4px;}
.expl-text {font-size: clamp(14px, 3vw, 18px); color: #222; line-height:1.45;}

.example-block {max-width:580px; margin:10px auto 0; padding:8px 4px 0;
                text-align:left; border-top:1px dashed #e3e3e3;}
.example-block:first-of-type {border-top:0;}
.example-block .ex-tgt {font-size: clamp(18px, 4vw, 24px); font-weight:600;
                        color:#111; line-height:1.3;}
.example-block .ex-en {font-size: clamp(13px, 2.8vw, 16px); color:#555;
                       margin-top:3px;}

.footer {margin-top:24px; font-size: clamp(10px, 2vw, 13px); color:#999;}
.replay-button svg {width:44px; height:44px;}
"""


def make_model() -> genanki.Model:
    fields = [
        "PhraseId", "Phrase", "English", "StructuredHTML", "ExamplesHTML",
        "FrontAudio", "BackAudio", "Source",
    ]
    return genanki.Model(
        MODEL_ID, MODEL_NAME,
        fields=[{"name": n} for n in fields],
        templates=[{"name": "Idiom", "qfmt": FRONT_TMPL, "afmt": BACK_TMPL}],
        css=CSS,
    )


# ---- build ----------------------------------------------------------------

def _guid(youtube_id: str, normalized: str) -> str:
    return hashlib.sha1(
        f"yt-idiom-cloud::{youtube_id}::{normalized}".encode()
    ).hexdigest()[:16]


def build_apkg(*, out_path: Path, deck_name: str, youtube_id: str,
                video_title: str, video_url: str,
                idioms: list[tuple[Enriched, Path, Path]],
                stage_dir: Path) -> Path:
    """Pack one apkg.

    idioms: list of (enriched, front_mp3, back_mp3) tuples.
    stage_dir: where to hardlink media under unique names to avoid global
               Anki-media collisions when many videos sit side-by-side.
    """
    model = make_model()
    deck_id = 1_810_000_000 + (
        int(hashlib.sha1(f"idiomatic-cloud::{deck_name}".encode()).hexdigest()[:8], 16)
        % 100_000_000
    )
    deck = genanki.Deck(deck_id, deck_name)
    stage_dir.mkdir(parents=True, exist_ok=True)
    media: list[str] = []

    def _stage(fname: str, src: Path) -> str:
        prefixed = f"idc_{youtube_id}__{fname}"
        dst = stage_dir / prefixed
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            dst.unlink(missing_ok=True)
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy(src, dst)
        return prefixed

    for i, (e, front, back) in enumerate(idioms, 1):
        if not front.exists() or not back.exists():
            log.warning("apkg.skip_missing_audio", idx=i, phrase=e.phrase[:40])
            continue
        f_name = _stage(f"front_{i:03d}.mp3", front)
        b_name = _stage(f"back_{i:03d}.mp3", back)
        media += [str(stage_dir / f_name), str(stage_dir / b_name)]

        # We don't have a per-phrase normalized field on Enriched (the
        # caller has it via the extract step). Use the phrase text as a
        # stable proxy.
        norm = e.phrase.lower().strip()
        deck.add_note(genanki.Note(
            model=model,
            fields=[
                f"{i:03d}",
                e.phrase,
                e.english,
                _vocab_table_html(e.structured),
                _examples_html(e.examples),
                f"[sound:{f_name}]",
                f"[sound:{b_name}]",
                f'from <a href="{html.escape(video_url)}">{html.escape(video_title)}</a>',
            ],
            guid=_guid(youtube_id, norm),
            tags=["youtube", youtube_id, "idiomatic-cloud"],
        ))

    pkg = genanki.Package(deck)
    pkg.media_files = media
    pkg.write_to_file(str(out_path))
    log.info("apkg.written", path=str(out_path), n=len(idioms),
             size_mb=round(out_path.stat().st_size / 1e6, 1))
    return out_path
