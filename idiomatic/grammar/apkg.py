"""Text-only grammar drill deck builder.

Model rules (docs/research/ankidroid-tech.md): the model is FROZEN —
never change field count/order/names or template count of MODEL_ID, or
every subscriber is forced into a one-way full sync. Extra1..Extra4 are
reserved for future needs. GUIDs derive from the DB primary key, so
re-imports update fields in place and preserve scheduling/FSRS state.
"""

from __future__ import annotations

import hashlib
import html
from pathlib import Path

import genanki
import structlog

log = structlog.get_logger()

MODEL_ID = 1_820_130_001
MODEL_NAME = "Idiomatic Grammar Drill v1"

FIELDS = [
    "ItemId", "Lang", "Topic", "TenseLabel", "Symbol",
    "Sentence",        # with ___ (infinitive)
    "Answer",
    "SentenceFull",    # blank replaced by <b>form</b>
    "GlossEn", "Why",
    "Extra1", "Extra2", "Extra3", "Extra4",
]

CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; background: #ffffff;
       color: #111; text-align: center; padding: 22px 14px;}
.tense-line {font-size: clamp(13px, 3vw, 17px); color: #777; margin-bottom: 18px;
             letter-spacing: 0.04em;}
.tense-line .sym {font-size: 1.2em; margin-right: 6px;}
.sentence {font-size: clamp(22px, 5vw, 34px); line-height: 1.45; margin: 10px auto;
           max-width: 620px;}
.sentence .blank {color: #0a7; font-weight: 700;}
.answer {font-size: clamp(26px, 6vw, 40px); font-weight: 700; color: #0a7;
         margin: 14px 0 6px;}
.sentence-full {font-size: clamp(18px, 4vw, 26px); line-height: 1.5;
                margin: 8px auto; max-width: 620px; color: #333;}
.sentence-full b {color: #0a7;}
.gloss {font-size: clamp(14px, 3vw, 19px); color: #666; margin-top: 12px;
        font-style: italic;}
.why {font-size: clamp(14px, 3vw, 18px); color: #444; margin: 14px auto 0;
      max-width: 560px; text-align: left; background: #f4f6f5;
      border-radius: 8px; padding: 10px 12px;}
hr#answer {border: 0; border-top: 1px solid #ccc; margin: 18px 0;}
/* Explicit night mode — without a .night_mode rule AnkiDroid heuristically
   color-inverts the whole card. */
.card.night_mode, .card.nightMode {background: #23272a; color: #e8e8e8;}
.card.night_mode .sentence-full, .card.nightMode .sentence-full {color: #ccc;}
.card.night_mode .why, .card.nightMode .why {background: #2e3438; color: #ddd;}
.card.night_mode .gloss, .card.nightMode .gloss {color: #999;}
"""

FRONT = """<div class="tense-line"><span class="sym">{{Symbol}}</span>{{TenseLabel}}</div>
<div class="sentence">{{Sentence}}</div>"""

# Extra1 holds the back audio ([sound:] — conjugated form, pause, full
# sentence). Placed after the answer so autoplay fires on reveal; the
# conditional keeps audio-less cards clean.
BACK = """<div class="tense-line"><span class="sym">{{Symbol}}</span>{{TenseLabel}}</div>
<div class="answer">{{Answer}}</div>
{{#Extra1}}<div>{{Extra1}}</div>{{/Extra1}}
<hr id="answer">
<div class="sentence-full">{{SentenceFull}}</div>
<div class="gloss">{{GlossEn}}</div>
{{#Why}}<div class="why">{{Why}}</div>{{/Why}}"""


def make_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID, MODEL_NAME,
        fields=[{"name": n} for n in FIELDS],
        templates=[{"name": "Drill", "qfmt": FRONT, "afmt": BACK}],
        css=CSS,
    )


def _guid(lang: str, item_id: int) -> str:
    return hashlib.sha1(f"idiomatic-grammar::{lang}::{item_id}".encode()
                        ).hexdigest()[:16]


def _blank_html(sentence: str, infinitive: str) -> str:
    esc = html.escape(sentence)
    return esc.replace("___", '<span class="blank">___</span>', 1)


def _full_html(sentence: str, answer: str, infinitive: str) -> str:
    """Replace `___ (infinitive)` with the bolded answer."""
    esc = html.escape(sentence)
    for pat in (f"___ ({infinitive})", f"___  ({infinitive})", "___"):
        pat_esc = html.escape(pat)
        if pat_esc in esc:
            return esc.replace(pat_esc, f"<b>{html.escape(answer)}</b>", 1)
    return esc


def build_grammar_apkg(*, out_path: Path, lang: str,
                        items: list[dict], topic_labels: dict[str, tuple[str, str]],
                        audio: dict[int, str] | None = None,
                        audio_dir: Path | None = None,
                        ) -> int:
    """items: verified grammar_items rows (dicts with id, topic, sentence,
    answer, infinitive, gloss_en, why_en). topic_labels: topic key ->
    (label, symbol). audio: item_id -> media filename inside audio_dir;
    items absent from the map ship text-only. Returns note count."""
    model = make_model()
    deck_name = f"Idiomatic Grammar {lang.upper()}"
    deck_id = 1_811_000_000 + (
        int(hashlib.sha1(f"idiomatic-grammar::{deck_name}".encode()
                          ).hexdigest()[:8], 16) % 100_000_000
    )
    deck = genanki.Deck(deck_id, deck_name)

    audio = audio or {}
    media: list[str] = []
    n = 0
    for it in items:
        label, symbol = topic_labels.get(it["topic"], (it["topic"], ""))
        sound = ""
        fname = audio.get(it["id"])
        if fname and audio_dir is not None and (audio_dir / fname).exists():
            sound = f"[sound:{fname}]"
            media.append(str(audio_dir / fname))
        deck.add_note(genanki.Note(
            model=model,
            fields=[
                str(it["id"]),
                lang,
                it["topic"],
                label,
                symbol,
                _blank_html(it["sentence"], it["infinitive"]),
                html.escape(it["answer"]),
                _full_html(it["sentence"], it["answer"], it["infinitive"]),
                html.escape(it.get("gloss_en") or ""),
                html.escape(it.get("why_en") or ""),
                sound, "", "", "",
            ],
            guid=_guid(lang, it["id"]),
            tags=["idiomatic-grammar", it["topic"]],
        ))
        n += 1

    pkg = genanki.Package(deck)
    pkg.media_files = media
    pkg.write_to_file(str(out_path))
    log.info("grammar.apkg.written", path=str(out_path), n=n,
             size_kb=round(out_path.stat().st_size / 1e3))
    return n
