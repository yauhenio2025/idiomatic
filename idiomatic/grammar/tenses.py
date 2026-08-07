"""Tenses Rescue decks — per-person conjugation drills mined from the
old account's 2015-2022 struggle data (docs/research/tenses-profiles/).

Two rolling apkgs per language, zero add-on changes:

- kind='tenses'     "Idiomatic Tenses {LANG}::{verb}" — EN→form
  production: front = EN sentence + lang/tense/person chips; back = the
  form big, the TL sentence with the form marked, the FULL paradigm with
  the drilled row highlighted (the glance-drill), trap/fork notes and
  the learner's own lapse history.
- kind='tenses_ex'  "Idiomatic Tenses Exercises {LANG}::{verb}" —
  fill-the-blank: front = the same TL sentence with the form blanked +
  the EN as meaning support; back = same as production. Sentences and
  audio are RECYCLED verbatim from the production notes (user directive).

Content: data/tenses/batch*.json. Every drilled form is verified at
build time — against grammar/morphology.py truth tables where the verb
is covered ("verify": {mood, tense}), otherwise against the corpus's own
attested paradigm ("verify": "attested"); a form that appears nowhere in
its item sentence fails the build. Audio: ElevenLabs via the shared
synthesize chain; Spanish uses settings.tenses_es_voice_id (the user
vetoed the house George voice for these decks — audition endpoint:
/admin/tenses-voice-audition).
"""

from __future__ import annotations

import asyncio
import hashlib
import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

import genanki
import structlog

from .. import db, gemini
from ..anki_tree import anki_root
from ..settings import get_settings
from . import morphology
from .explainers import leveled_speech_clip

log = structlog.get_logger()

SOURCE_DIR = Path(__file__).parent / "data" / "tenses"
SUPPORTED_LANGS = ("de", "es", "fr", "it", "pt")

MODEL_ID_PROD = 1_820_170_001
MODEL_ID_EX = 1_820_170_002
MODEL_NAME_PROD = "Idiomatic Tenses v1"
MODEL_NAME_EX = "Idiomatic Tenses Exercises v1"

# FROZEN — never change count or order (spares Extra1-2 remain).
FIELDS = [
    "ItemId", "Lang", "Verb", "Gloss", "Tense", "Pronoun", "Form", "EN",
    "TL", "TLBlank", "Paradigm", "Trap", "Fork", "History",
    "AudioAnswer", "AudioSentence", "Extra1", "Extra2",
]

# ElevenLabs voice audition candidates for /admin/tenses-voice-audition.
# George is the house voice the user dislikes for Spanish — kept in the
# lineup as the baseline to beat.
ES_VOICE_CANDIDATES = {
    "george-current": "JBFqnCBsd6RMkjVDRZzb",
    "jessica": "cgSgspJ2msm6clMCkdW9",
    "lily": "pFZP5JQG7iQjIQuC4Bku",
    "eric": "cjVigY5qzO86Huf0OWal",
    "alice": "Xb7hH8MSUJpSbSDYk0k2",
    "brian": "nPczCjzI2devNBz1zQrb",
}


class TensesSourceError(ValueError):
    pass


@dataclass(frozen=True)
class ParadigmRow:
    key: str
    pronoun: str
    form: str
    drill: bool
    archaic: bool = False


@dataclass(frozen=True)
class TenseItem:
    person: str
    en: str
    tl: str
    trap: str = ""


@dataclass(frozen=True)
class TenseVerb:
    lang: str
    verb: str
    gloss: str
    tense_key: str
    tense_label: str
    fork: str
    history: dict
    paradigm: tuple[ParadigmRow, ...]
    items: tuple[TenseItem, ...]
    answer_prefix: str = ""
    answer_note: str = ""

    @property
    def is_imperative(self) -> bool:
        return "imperativ" in self.tense_key


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise TensesSourceError(msg)


def _form_in_sentence(form: str, sentence: str) -> bool:
    return re.search(rf"(?<![\w'])({re.escape(form)})(?![\w'])",
                     sentence, re.IGNORECASE) is not None


def load_batches(lang: str | None = None, *,
                 source_dir: Path | None = None) -> list[TenseVerb]:
    """Parse + validate every batch file (optionally filtered by lang)."""
    root = source_dir if source_dir is not None else SOURCE_DIR
    verbs: list[TenseVerb] = []
    for path in sorted(root.glob("batch*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for raw in data.get("verbs", []):
            v = _parse_verb(path.name, raw)
            if lang is None or v.lang == lang:
                verbs.append(v)
    return verbs


def _parse_verb(src: str, raw: dict) -> TenseVerb:
    lang = raw.get("lang")
    _require(lang in SUPPORTED_LANGS, f"{src}: bad lang {lang!r}")
    verb = (raw.get("verb") or "").strip()
    tense_key = (raw.get("tense_key") or "").strip()
    _require(bool(verb) and bool(tense_key),
             f"{src}: verb/tense_key required")
    where = f"{src}:{lang}:{verb}:{tense_key}"

    rows: list[ParadigmRow] = []
    seen_keys: set[str] = set()
    for r in raw.get("paradigm", []):
        key = r.get("key")
        _require(key not in seen_keys, f"{where}: duplicate person {key}")
        seen_keys.add(key)
        form = (r.get("form") or "").strip()
        _require(bool(form), f"{where}: empty form for {key}")
        rows.append(ParadigmRow(
            key=key, pronoun=(r.get("pronoun") or "").strip(), form=form,
            drill=bool(r.get("drill", True)),
            archaic=bool(r.get("archaic", False))))
    _require(len(rows) >= 4, f"{where}: paradigm too small")
    _require(not any(r.archaic and r.drill for r in rows),
             f"{where}: archaic rows must not be drilled")

    # Form verification: truth table when covered, attested otherwise.
    verify = raw.get("verify")
    if isinstance(verify, dict):
        for r in rows:
            expected = morphology.lookup(
                lang, verb, verify["mood"], verify["tense"], r.key)
            _require(expected is not None,
                     f"{where}: {r.key} not in the {lang} truth table — "
                     "use verify='attested' or fix mood/tense")
            _require(expected == morphology._norm(r.form),
                     f"{where}: {r.key} form {r.form!r} != table {expected!r}")
    else:
        _require(verify == "attested",
                 f"{where}: verify must be 'attested' or {{mood, tense}}")

    by_key = {r.key: r for r in rows}
    items: list[TenseItem] = []
    seen_persons: set[str] = set()
    for it in raw.get("items", []):
        person = it.get("person")
        _require(person in by_key, f"{where}: item person {person!r} unknown")
        _require(person not in seen_persons,
                 f"{where}: duplicate item for {person}")
        seen_persons.add(person)
        row = by_key[person]
        _require(row.drill, f"{where}: item for non-drilled person {person}")
        en = (it.get("en") or "").strip()
        tl = (it.get("tl") or "").strip()
        _require(bool(en) and bool(tl), f"{where}: {person} needs en+tl")
        _require(_form_in_sentence(row.form, tl),
                 f"{where}: {person} sentence lacks the exact form "
                 f"{row.form!r}: {tl!r}")
        items.append(TenseItem(person=person, en=en, tl=tl,
                               trap=(it.get("trap") or "").strip()))

    return TenseVerb(
        lang=lang, verb=verb, gloss=(raw.get("gloss") or "").strip(),
        tense_key=tense_key,
        tense_label=(raw.get("tense_label") or tense_key).strip(),
        fork=(raw.get("fork") or "").strip(),
        history=raw.get("history") or {},
        paradigm=tuple(rows), items=tuple(items),
        answer_prefix=(raw.get("answer_prefix") or "").strip(),
        answer_note=(raw.get("answer_note") or "").strip(),
    )


def missing_items(verbs: list[TenseVerb]) -> list[str]:
    """Drilled persons without an authored sentence (build refuses them)."""
    out = []
    for v in verbs:
        have = {i.person for i in v.items}
        for r in v.paradigm:
            if r.drill and r.key not in have:
                out.append(f"{v.lang}:{v.verb}:{v.tense_key}:{r.key}")
    return out


# --- Anki plumbing ----------------------------------------------------------

def tenses_guid(kind: str, lang: str, verb: str, tense_key: str,
                person: str) -> str:
    assert kind in ("prod", "ex")
    payload = f"idio-tenses-{kind}::{lang}::{verb}::{tense_key}::{person}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def deck_name_for(kind: str, lang: str, verb: str) -> str:
    lane = "1 Production" if kind == "prod" else "2 Exercises"
    return f"{anki_root(lang)}::3 Tenses::{lane}::{verb}"


def _deck_id(name: str) -> int:
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
    return 2_020_000_000 + int(digest[:12], 16) % 60_000_000


def first_pronoun(pronoun: str) -> str:
    return pronoun.split("/")[0].strip()


def spoken_answer(v: TenseVerb, row: ParadigmRow) -> str:
    if v.is_imperative:
        return f"{row.form}!"
    head = f"{v.answer_prefix} " if v.answer_prefix else ""
    return f"{head}{first_pronoun(row.pronoun)} {row.form}"


def blank_sentence(tl: str, form: str) -> str:
    """The exercises front: exact form → underscores (case-insensitive,
    word-bounded, first occurrence only)."""
    out, n = re.subn(rf"(?<![\w'])({re.escape(form)})(?![\w'])", "＿＿＿",
                     tl, count=1, flags=re.IGNORECASE)
    if n != 1:
        raise TensesSourceError(f"cannot blank {form!r} in {tl!r}")
    return out


def paradigm_html(v: TenseVerb, drilled_key: str) -> str:
    rows = []
    for r in v.paradigm:
        cls = "hit" if r.key == drilled_key else ("arch" if r.archaic else "")
        rows.append(
            f'<tr class="{cls}"><td class="pr">{html.escape(r.pronoun)}</td>'
            f'<td class="fm">{html.escape(r.form)}</td></tr>')
    return f'<table class="para">{"".join(rows)}</table>'


def sentence_html(tl: str, form: str) -> str:
    out, n = re.subn(rf"(?<![\w'])({re.escape(form)})(?![\w'])",
                     r"<b>\1</b>", tl, count=1, flags=re.IGNORECASE)
    if n != 1:
        raise TensesSourceError(f"cannot mark {form!r} in {tl!r}")
    return out


def history_line(v: TenseVerb) -> str:
    h = v.history
    if not h.get("reps"):
        return ""
    return (f"your record with this paradigm: {h.get('lapses', '?')} lapses / "
            f"{h.get('reps', '?')} reviews since 2015")


_CSS = """
.card { background: #151a24; color: #e8e6e0; font-family: Georgia, "Iowan Old Style", serif;
  font-size: 21px; line-height: 1.45; text-align: left; padding: 18px 20px; }
.chips { margin-bottom: 12px; }
.chip { font: 600 12px/1 ui-monospace, Menlo, monospace; letter-spacing: .06em;
  padding: 4px 8px; border-radius: 999px; border: 1px solid #2a3140;
  color: #98a0ae; margin-right: 5px; }
.chip.p { color: #e8a13c; border-color: #6d5220; }
.chip.t { color: #7cc7d2; border-color: #2e5a62; }
.en { font-size: 22px; }
.en-sub { font-size: 16px; color: #98a0ae; margin-top: 10px; }
.bigform { font-size: 30px; color: #e8a13c; margin: 6px 0 10px; }
.tl { margin-bottom: 12px; }
.tl b { color: #e8a13c; }
.blank { font-size: 23px; margin-bottom: 6px; }
.para { border-collapse: collapse; margin-top: 10px; border-top: 1px solid #2a3140;
  padding-top: 8px; width: 100%; }
.para td { padding: 2px 14px 2px 0; font-size: 17px; }
.para .pr { font: 500 13px/1.6 ui-monospace, Menlo, monospace; color: #98a0ae; }
.para tr.hit td { color: #e8a13c; font-weight: 700; }
.para tr.arch td { opacity: .38; }
.note { font-size: 14px; color: #7cc7d2; border-top: 1px dashed #2a3140;
  margin-top: 10px; padding-top: 8px; }
.fork { font-size: 14px; color: #98a0ae; border-top: 1px dashed #2a3140;
  margin-top: 10px; padding-top: 8px; }
.hist { font: 11px/1.5 ui-monospace, Menlo, monospace; color: #5b6270; margin-top: 10px; }
"""

_FRONT_PROD = """
<div class="chips"><span class="chip">{{Lang}}</span><span class="chip t">{{Tense}}</span><span class="chip p">{{Pronoun}}</span><span class="chip">{{Gloss}}</span></div>
<div class="en">{{EN}}</div>
"""
_BACK_SHARED = """
<div class="bigform">{{Form}}</div>
<div class="tl">{{TL}}</div>
{{AudioAnswer}} {{AudioSentence}}
{{Paradigm}}
{{#Trap}}<div class="note">{{Trap}}</div>{{/Trap}}
{{#Fork}}<div class="fork">{{Fork}}</div>{{/Fork}}
{{#History}}<div class="hist">{{History}}</div>{{/History}}
"""
_FRONT_EX = """
<div class="chips"><span class="chip">{{Lang}}</span><span class="chip t">{{Tense}}</span><span class="chip">{{Verb}} · {{Gloss}}</span></div>
<div class="blank">{{TLBlank}}</div>
<div class="en-sub">{{EN}}</div>
"""


def make_model(kind: str) -> genanki.Model:
    assert kind in ("prod", "ex")
    front = _FRONT_PROD if kind == "prod" else _FRONT_EX
    return genanki.Model(
        MODEL_ID_PROD if kind == "prod" else MODEL_ID_EX,
        MODEL_NAME_PROD if kind == "prod" else MODEL_NAME_EX,
        fields=[{"name": f} for f in FIELDS],
        templates=[{
            "name": "Produce" if kind == "prod" else "Fill",
            "qfmt": front,
            "afmt": front + '<hr id="answer">' + _BACK_SHARED,
        }],
        css=_CSS,
    )


# --- audio ------------------------------------------------------------------

def voice_override(lang: str, settings: Any) -> str | None:
    """Per-deck ElevenLabs voice id override (None = house voice)."""
    if lang == "es":
        return settings.tenses_es_voice_id or None
    return None


def audio_cache_key(text: str, lang: str, settings: Any) -> str:
    marker = voice_override(lang, settings) or f"house:{lang}"
    return hashlib.sha256(
        f"{marker}::{text}".encode("utf-8")).hexdigest()[:16]


def audio_filename(lang: str, digest: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{16}", digest):
        raise ValueError("digest must be 16 lowercase hex characters")
    return f"idt_{lang}_{digest}.mp3"


@dataclass(frozen=True)
class ItemAudio:
    answer: Path | None
    sentence: Path | None


async def _synthesize_audio(
    verbs: list[TenseVerb], *, lang: str, settings: Any,
    synthesize_fn: Callable[..., Awaitable[None]] | None = None,
    level_fn: Callable[[Path], Path] | None = None,
) -> tuple[dict[tuple[str, str, str], ItemAudio], int, int]:
    """Two leveled clips per item through the shared cache (exercises2
    stance: a silence-marked failure ships text-only, never fails the
    build). Keyed by (verb, tense_key, person)."""
    synthesize_fn = synthesize_fn or gemini.synthesize
    level_fn = level_fn or leveled_speech_clip
    work_dir = Path(settings.data_dir) / "staged_audio" / "grammar" / "tenses" / lang
    work_dir.mkdir(parents=True, exist_ok=True)
    override = voice_override(lang, settings)

    wanted: dict[tuple[str, str, str], tuple[str, str]] = {}
    for v in verbs:
        rows = {r.key: r for r in v.paradigm}
        for it in v.items:
            wanted[(v.verb, v.tense_key, it.person)] = (
                spoken_answer(v, rows[it.person]), it.tl)

    clip_paths: dict[str, Path] = {}
    pending: dict[Path, str] = {}
    for answer, sentence in wanted.values():
        for text in (answer, sentence):
            clip = work_dir / audio_filename(
                lang, audio_cache_key(text, lang, settings))
            clip_paths[text] = clip
            if not (clip.exists() and clip.stat().st_size > 0
                    and not gemini.silence_marker(clip).exists()):
                pending[clip] = text

    await asyncio.gather(
        *(synthesize_fn(text, voice="Kore", out=clip, lang=lang,
                        eleven_voice_id=override)
          for clip, text in pending.items()))

    usable: dict[str, Path] = {}
    failed = 0
    for text, clip in clip_paths.items():
        if (clip.exists() and clip.stat().st_size > 0
                and not gemini.silence_marker(clip).exists()):
            usable[text] = clip
        else:
            failed += 1
    leveled_list = await asyncio.gather(
        *(asyncio.to_thread(level_fn, clip) for clip in usable.values()))
    leveled = dict(zip(usable, leveled_list, strict=True))

    result = {
        key: ItemAudio(answer=leveled.get(a), sentence=leveled.get(s))
        for key, (a, s) in wanted.items()
    }
    return result, len(pending), failed


# --- apkg build -------------------------------------------------------------

def build_tenses_apkg(
    *, kind: str, out_path: Path, lang: str, verbs: list[TenseVerb],
    audio: dict[tuple[str, str, str], ItemAudio] | None = None,
) -> int:
    assert kind in ("prod", "ex")
    model = make_model(kind)
    audio = audio or {}
    decks: dict[str, genanki.Deck] = {}
    media: list[str] = []
    media_seen: set[str] = set()
    n_notes = 0

    for v in verbs:
        if v.lang != lang:
            raise ValueError(f"{v.verb}: lang {v.lang!r} != {lang!r}")
        rows = {r.key: r for r in v.paradigm}
        deck_name = deck_name_for(kind, lang, v.verb)
        deck = decks.get(deck_name)
        if deck is None:
            deck = decks[deck_name] = genanki.Deck(_deck_id(deck_name), deck_name)

        for it in v.items:
            row = rows[it.person]
            record = audio.get((v.verb, v.tense_key, it.person)) \
                or ItemAudio(None, None)
            sounds = []
            for clip in (record.answer, record.sentence):
                if clip is None:
                    sounds.append("")
                    continue
                clip = Path(clip)
                if not clip.exists() or clip.stat().st_size <= 0:
                    raise ValueError(f"missing tenses media: {clip}")
                sounds.append(f"[sound:{clip.name}]")
                key = str(clip.resolve())
                if key not in media_seen:
                    media.append(str(clip))
                    media_seen.add(key)

            item_id = f"{lang}:{v.verb}:{v.tense_key}:{it.person}"
            trap = it.trap
            if v.answer_note:
                trap = f"{trap} · {v.answer_note}" if trap else v.answer_note
            deck.add_note(genanki.Note(
                model=model,
                fields=[
                    item_id, lang.upper(), html.escape(v.verb),
                    html.escape(v.gloss), html.escape(v.tense_label),
                    html.escape(row.pronoun),
                    html.escape(spoken_answer(v, row)),
                    html.escape(it.en),
                    sentence_html(it.tl, row.form),
                    html.escape(blank_sentence(it.tl, row.form)),
                    paradigm_html(v, it.person),
                    html.escape(trap),
                    html.escape(v.fork),
                    html.escape(history_line(v)),
                    sounds[0], sounds[1], "", "",
                ],
                guid=tenses_guid(kind, lang, v.verb, v.tense_key, it.person),
                tags=["idiomatic-tenses",
                      f"idiomatic-tenses::{lang}::{v.verb}"],
            ))
            n_notes += 1

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(sorted(decks.values(), key=lambda d: d.name))
    package.media_files = media
    package.write_to_file(str(out_path))
    return n_notes


async def build_language(
    lang: str, *,
    synthesize_fn: Callable[..., Awaitable[None]] | None = None,
    level_fn: Callable[[Path], Path] | None = None,
) -> dict[str, Any]:
    """Build BOTH rolling apkgs (production + exercises) for one language."""
    if lang not in SUPPORTED_LANGS:
        raise ValueError("lang must be de|es|fr|it|pt")
    verbs = load_batches(lang)
    if not verbs:
        raise ValueError(f"no tenses content for lang {lang!r}")
    gaps = missing_items(verbs)
    if gaps:
        raise TensesSourceError(
            f"{len(gaps)} drilled persons lack sentences: {gaps[:6]}")
    settings = get_settings()
    audio, synthesized, failed = await _synthesize_audio(
        verbs, lang=lang, settings=settings,
        synthesize_fn=synthesize_fn, level_fn=level_fn)

    apkg_root = Path(settings.data_dir) / "apkgs" / lang
    apkg_root.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "lang": lang,
        "verbs": sorted({f"{v.verb}·{v.tense_label}" for v in verbs}),
        "clips_synthesized": synthesized, "clips_failed": failed,
    }
    for kind, db_kind, fname in (("prod", "tenses", "_tenses.apkg"),
                                 ("ex", "tenses_ex", "_tenses_ex.apkg")):
        out = apkg_root / fname
        n = await asyncio.to_thread(
            build_tenses_apkg, kind=kind, out_path=out, lang=lang,
            verbs=verbs, audio=audio)
        apkg_id = await db.upsert_pool_apkg(
            lang=lang, kind=db_kind,
            filename=str(out.relative_to(Path(settings.data_dir))),
            size_bytes=out.stat().st_size, n_idioms=n)
        result[db_kind] = {"apkg_id": apkg_id, "notes": n}
    log.info("grammar.tenses.built", **{k: v for k, v in result.items()
                                        if k != "verbs"})
    return result


def list_content() -> list[dict[str, Any]]:
    """Admin inventory: per (lang, verb, tense) — items vs drilled slots."""
    rows: list[dict[str, Any]] = []
    try:
        verbs = load_batches()
    except TensesSourceError as exc:
        return [{"valid": False, "error": str(exc)[:300]}]
    for v in verbs:
        drilled = [r.key for r in v.paradigm if r.drill]
        rows.append({
            "valid": True, "lang": v.lang, "verb": v.verb,
            "tense": v.tense_label, "drilled": len(drilled),
            "items": len(v.items),
            "missing": sorted(set(drilled) - {i.person for i in v.items}),
            "history": v.history,
        })
    return rows


async def voice_audition(lang: str = "es",
                         text: str | None = None) -> dict[str, Any]:
    """Render one sample sentence in every candidate voice so the user
    can pick by ear. Files land in staged_audio/grammar/{lang}/ as
    audition_{name}.mp3 — streamable through the existing grammar audio
    route with ?token=."""
    if lang != "es":
        raise ValueError("audition currently targets the Spanish voice hunt")
    sample = text or ("No creo que la plataforma sepa distinguir una "
                      "noticia de un anuncio.")
    settings = get_settings()
    out_dir = Path(settings.data_dir) / "staged_audio" / "grammar" / lang
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, voice_id in ES_VOICE_CANDIDATES.items():
        out = out_dir / f"audition_{name}.mp3"
        out.unlink(missing_ok=True)
        gemini.silence_marker(out).unlink(missing_ok=True)
        try:
            await gemini.synthesize(sample, voice="Kore", out=out, lang=lang,
                                    eleven_voice_id=voice_id)
            ok = out.exists() and not gemini.silence_marker(out).exists()
        except Exception as exc:  # noqa: BLE001 — report per-voice failures
            log.warning("tenses.audition_failed", voice=name,
                        err=repr(exc)[:150])
            ok = False
        results[name] = {
            "voice_id": voice_id, "ok": ok,
            "url": f"/ui/api/audio/grammar/{lang}/audition_{name}.mp3",
        }
    return {"sample_text": sample, "voices": results,
            "note": "append ?token=<admin token> to stream; set "
                    "TENSES_ES_VOICE_ID to the winner and rebuild es"}
