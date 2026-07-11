"""Build per-video Anki .apkg in the pimsleur didactic shape.

23-field model mirroring scraper/idioms.py from the pimsleur project:
  IdiomId, Idiom, IdiomEn, Explanation,
  Example1En, Example1Target .. Example6En, Example6Target,
  SourcePhrase, SourceEn, FrontAudio, BackAudio, Source

GUID: yt-idiom-cloud::<youtube_id>::<normalized phrase>. Same as before,
so re-imports update in place.
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


# Bumped from the 8-field 1_820_120_000 model. Old notes with that model
# stay in Anki but won't share fields with these.
MODEL_ID = 1_820_120_100
MODEL_NAME = "Idiomatic Cloud Card v2"

# Examples expected per idiom (3 teach on front, 3 drill on back).
EXAMPLES_PER_IDIOM = 6

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


def structured_html(structured: dict[str, str] | None) -> str:
    """Render the non-empty structured-explanation fields as labelled
    sections (same look as the v1 card's structured block)."""
    if not structured:
        return ""
    rows = []
    for k, v in structured.items():
        v = (v or "").strip()
        if not v:
            continue
        label = EXPL_LABELS.get(k, k.replace("_", " ").title())
        rows.append(
            f'<div class="expl-section">'
            f'<div class="expl-label">{html.escape(label)}</div>'
            f'<div class="expl-text">{html.escape(v)}</div>'
            f'</div>'
        )
    return "".join(rows)


# ---- HTML + CSS ----------------------------------------------------------

IDIOM_CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; background: #ffffff; color: #000;
       text-align: center; padding: 20px 14px;}
.prompt-label {font-size: clamp(13px, 3vw, 18px); color: #666; margin: 14px 0 6px;
               letter-spacing: 0.05em; text-transform: uppercase;}
.idiom {font-size: clamp(24px, 5.5vw, 42px); font-weight: 700; line-height: 1.25;
        margin: 6px 0 12px; color: #111;}
.en-hint {font-size: clamp(16px, 3.5vw, 22px); color: #555; margin-bottom: 8px;}
.explanation {font-size: clamp(14px, 3vw, 18px); color: #333; margin: 14px 12px;
              text-align: left; line-height: 1.5; max-width: 580px;
              margin-left: auto; margin-right: auto;}
.example-row {text-align: left; max-width: 560px; margin: 6px auto;
              font-size: clamp(14px, 3vw, 18px); line-height: 1.4;}
.example-row .en-line {color: #555;}
.example-row .tgt-line {color: #111; font-weight: 600; margin-top: 2px;}
hr#answer {border: 0; border-top: 1px solid #bbb; margin: 18px 0;}
.footer {margin-top: 22px; font-size: clamp(10px, 2vw, 13px); color: #888;
         max-width: 580px; margin-left: auto; margin-right: auto; text-align: left;}
.footer .src-pair {margin: 6px 0;}
.footer .src-en {color: #999; font-style: italic;}
.footer .src-tgt {color: #555;}
.expl-section {text-align: left; max-width: 560px;
               margin: 12px auto 0; padding: 0 4px;}
.expl-label {font-size: clamp(11px, 2.4vw, 14px); color: #888;
             letter-spacing: 0.06em; text-transform: uppercase;
             margin-top: 14px; margin-bottom: 4px;}
.expl-text {font-size: clamp(14px, 3vw, 18px); color: #222; line-height: 1.45;}
.replay-button svg {width: 44px; height: 44px;}
"""

# Front: idiom + en gloss + English explanation + audio + 3 EN-only drill
# prompts (the things heard on the back). Examples 4–6 are the drill set.
IDIOM_FRONT_TMPL = """<div class="idiom">{{Idiom}}</div>
<div class="en-hint">{{IdiomEn}}</div>
<div class="explanation">{{Explanation}}</div>
<div class="prompt-label" style="margin-top: 16px;">Listen and learn</div>
<div>{{FrontAudio}}</div>
<div class="prompt-label" style="margin-top: 18px;">Now translate these in your head:</div>
<div class="example-row"><div class="en-line">1. {{Example4En}}</div></div>
<div class="example-row"><div class="en-line">2. {{Example5En}}</div></div>
<div class="example-row"><div class="en-line">3. {{Example6En}}</div></div>"""

# Back: verify-translation audio + drill pairs (examples 4–6) + teaching
# examples (1–3) shown for reference + trigger sentence + video link.
IDIOM_BACK_TMPL = """<hr id="answer">
<div class="prompt-label">Verify your translation</div>
<div>{{BackAudio}}</div>
<div class="example-row">
  <div class="en-line">1. {{Example4En}}</div>
  <div class="tgt-line">→ {{Example4Target}}</div>
</div>
<div class="example-row">
  <div class="en-line">2. {{Example5En}}</div>
  <div class="tgt-line">→ {{Example5Target}}</div>
</div>
<div class="example-row">
  <div class="en-line">3. {{Example6En}}</div>
  <div class="tgt-line">→ {{Example6Target}}</div>
</div>
{{StructuredHtml}}
<div class="prompt-label" style="margin-top: 18px; color: #999;">Teaching examples (heard on front):</div>
<div class="example-row" style="opacity: 0.75;">
  <div class="en-line">· {{Example1En}}</div>
  <div class="tgt-line">→ {{Example1Target}}</div>
</div>
<div class="example-row" style="opacity: 0.75;">
  <div class="en-line">· {{Example2En}}</div>
  <div class="tgt-line">→ {{Example2Target}}</div>
</div>
<div class="example-row" style="opacity: 0.75;">
  <div class="en-line">· {{Example3En}}</div>
  <div class="tgt-line">→ {{Example3Target}}</div>
</div>
<div class="footer">
  <div class="src-pair">
    <div class="src-tgt">{{SourcePhrase}}</div>
    <div class="src-en">{{SourceEn}}</div>
  </div>
  {{Source}}
</div>"""


def make_model() -> genanki.Model:
    fields = ["IdiomId", "Idiom", "IdiomEn", "Explanation"]
    for i in range(1, EXAMPLES_PER_IDIOM + 1):
        fields += [f"Example{i}En", f"Example{i}Target"]
    # StructuredHtml is appended LAST so the field list stays a prefix-
    # compatible extension of the shipped v2 model — the add-on imports
    # with update_notetypes=ALWAYS, which adds the new field in place
    # without breaking same-GUID note updates.
    fields += ["SourcePhrase", "SourceEn", "FrontAudio", "BackAudio", "Source",
               "StructuredHtml"]
    return genanki.Model(
        MODEL_ID, MODEL_NAME,
        fields=[{"name": n} for n in fields],
        templates=[{"name": "Idiom practice",
                    "qfmt": IDIOM_FRONT_TMPL, "afmt": IDIOM_BACK_TMPL}],
        css=IDIOM_CSS,
    )


# ---- build ----------------------------------------------------------------

def _guid(youtube_id: str, normalized: str) -> str:
    return hashlib.sha1(
        f"yt-idiom-cloud::{youtube_id}::{normalized}".encode()
    ).hexdigest()[:16]


def _ex(examples: list[dict], i: int, key: str) -> str:
    """Return examples[i][key] or empty string."""
    if i < len(examples):
        return examples[i].get(key, "") or ""
    return ""


def build_apkg(*, out_path: Path, deck_name: str, youtube_id: str,
                video_title: str, video_url: str,
                idioms: list[tuple[Enriched, Path, Path]],
                stage_dir: Path) -> Path:
    """idioms: list of (enriched, front_mp3, back_mp3) tuples."""
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

        norm = e.phrase.lower().strip()
        examples = e.examples or []
        example_fields: list[str] = []
        for k in range(EXAMPLES_PER_IDIOM):
            example_fields.append(_ex(examples, k, "en"))
            example_fields.append(_ex(examples, k, "target"))

        deck.add_note(genanki.Note(
            model=model,
            fields=[
                f"{i:03d}",                      # IdiomId
                e.phrase,                         # Idiom
                e.english,                        # IdiomEn
                getattr(e, "explanation_en", "") or "",  # Explanation paragraph
                *example_fields,                  # Example1En..Example6Target
                getattr(e, "source_phrase_target", "") or "",  # SourcePhrase
                getattr(e, "source_phrase_en", "") or "",      # SourceEn
                f"[sound:{f_name}]",              # FrontAudio
                f"[sound:{b_name}]",              # BackAudio
                f'from <a href="{html.escape(video_url)}">{html.escape(video_title)}</a>',
                structured_html(getattr(e, "structured", None)),
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
