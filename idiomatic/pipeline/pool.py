"""Per-language pool decks aggregated across every processed video.

Two pool kinds, three apkgs per language:

  - Fluency Expressions Pool (kind=pool_expr)
      One card per example sentence. Front: EN sentence + audio.
      Back: target sentence + audio, idiom hint, source video.
      Hundreds of cards per language once a few videos have landed.

  - Idiom Audio Pool (kind=pool_idiom_t2e and pool_idiom_e2t)
      One card per idiom, bare expression only, two directions:
        t2e — front: target audio + text, back: English audio + text
        e2t — front: English audio + text, back: target audio + text
      ~12 cards per video × N videos.

Source data: expression_idioms + expression_examples (written by the
worker after each per-video build) and the audio files persisted under
/data/staged_audio/<youtube_id>/.

Rebuild triggered from worker.process_video at the end of each video.
Each rebuild deletes the existing pool apkg row (cascade-deletes
agent_acks) and inserts a new one — agents re-pull the next time they
poll. genanki stable GUIDs make re-import in Anki an UPDATE not a dup.
"""

from __future__ import annotations

import hashlib
import html
import os
import shutil
import unicodedata
from pathlib import Path

import genanki
import structlog

from .. import db
from ..settings import get_settings
from . import audio as audio_mod
from . import apkg as apkg_mod
from . import connectives

log = structlog.get_logger()


# ============================================================================
# Note types (identical to pimsleur's so the user can merge collections later)
# ============================================================================

POOL_EXPR_MODEL_ID = 1820114700
POOL_EXPR_MODEL_NAME = "YouTube Expression Pool v1"

POOL_T2E_MODEL_ID = 1820114800
POOL_T2E_MODEL_NAME = "YouTube Idiom Audio Target→EN v1"

POOL_E2T_MODEL_ID = 1820114801
POOL_E2T_MODEL_NAME = "YouTube Idiom Audio EN→Target v1"


_EXPR_CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; background: #fff; color: #000;
       text-align: center; padding: 24px 16px;}
.sentence {font-size: clamp(22px, 4.8vw, 34px); font-weight: 600;
           line-height: 1.35; margin: 14px auto; max-width: 640px;}
.sentence-en {color: #111;}
.sentence-tgt {color: #0b4a7a;}
.idiom-hint {font-size: clamp(14px, 3vw, 18px); color: #666; margin-top: 20px;}
.idiom-hint .idiom-word {font-weight: 600; color: #111;}
hr#answer {border: 0; border-top: 1px solid #bbb; margin: 18px auto; max-width: 640px;}
.footer {margin-top: 20px; font-size: clamp(10px, 2vw, 13px); color: #888;}
.replay-button svg {width: 44px; height: 44px;}
"""

_EXPR_FRONT = """<div class="sentence sentence-en">{{English}}</div>
<div>{{EnglishAudio}}</div>"""

_EXPR_BACK = """<hr id="answer">
<div class="sentence sentence-tgt">{{Target}}</div>
<div>{{TargetAudio}}</div>
<div class="idiom-hint">
  Expression: <span class="idiom-word">{{Idiom}}</span>
  <br><span style="color: #999;">({{IdiomEn}})</span>
</div>
<div class="footer">{{Source}}</div>"""


_AUDIO_CSS = """
.card {font-family: -apple-system, system-ui, sans-serif; background: #fff; color: #000;
       text-align: center; padding: 28px 16px;}
.idiom-text {font-size: clamp(24px, 5.5vw, 42px); font-weight: 700; line-height: 1.25;
             margin: 14px auto; max-width: 680px; color: #111;}
.idiom-text.en {color: #0b4a7a; font-weight: 500;}
.prompt-label {font-size: clamp(12px, 2.5vw, 16px); color: #888; margin-top: 16px;
               letter-spacing: 0.05em; text-transform: uppercase;}
hr#answer {border: 0; border-top: 1px solid #bbb; margin: 16px auto; max-width: 680px;}
.footer {margin-top: 22px; font-size: clamp(10px, 2vw, 13px); color: #888;}
.replay-button svg {width: 44px; height: 44px;}
"""

_T2E_FRONT = """<div class="prompt-label">Listen</div>
<div>{{FrontAudio}}</div>
<div class="idiom-text">{{Target}}</div>"""

_T2E_BACK = """<hr id="answer">
<div class="idiom-text en">{{English}}</div>
<div>{{BackAudio}}</div>
<div class="footer">{{Source}}</div>"""

_E2T_FRONT = """<div class="prompt-label">Listen (English)</div>
<div>{{FrontAudio}}</div>
<div class="idiom-text en">{{English}}</div>"""

_E2T_BACK = """<hr id="answer">
<div class="idiom-text">{{Target}}</div>
<div>{{BackAudio}}</div>
<div class="footer">{{Source}}</div>"""


# ============================================================================
# Helpers
# ============================================================================

_LANG_NAMES = {
    "de": "German", "fr": "French", "it": "Italian",
    "pt": "Portuguese", "es": "Spanish", "zh": "Mandarin",
}


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s)
                if not unicodedata.combining(c))
    return "".join(c for c in s if c.isalnum())


def _guid(*parts: str) -> str:
    key = "::".join(parts)
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def _deck_id(name: str) -> int:
    h = hashlib.sha1(f"pool-deck::{name}".encode()).hexdigest()
    return 1_820_000_000 + (int(h[:8], 16) % 100_000_000)


def _model_id(seed: str) -> int:
    """Deck-naming helper for the pool decks (NOT note model id)."""
    return _deck_id(seed)


def _expr_model() -> genanki.Model:
    return genanki.Model(
        POOL_EXPR_MODEL_ID, POOL_EXPR_MODEL_NAME,
        fields=[{"name": n} for n in
                ("English", "Target", "EnglishAudio", "TargetAudio",
                 "Idiom", "IdiomEn", "Source")],
        templates=[{"name": "EN → target", "qfmt": _EXPR_FRONT,
                    "afmt": _EXPR_BACK}],
        css=_EXPR_CSS,
    )


def _t2e_model() -> genanki.Model:
    return genanki.Model(
        POOL_T2E_MODEL_ID, POOL_T2E_MODEL_NAME,
        fields=[{"name": n} for n in
                ("Target", "English", "FrontAudio", "BackAudio", "Source")],
        templates=[{"name": "target → EN", "qfmt": _T2E_FRONT,
                    "afmt": _T2E_BACK}],
        css=_AUDIO_CSS,
    )


def _e2t_model() -> genanki.Model:
    return genanki.Model(
        POOL_E2T_MODEL_ID, POOL_E2T_MODEL_NAME,
        fields=[{"name": n} for n in
                ("Target", "English", "FrontAudio", "BackAudio", "Source")],
        templates=[{"name": "EN → target", "qfmt": _E2T_FRONT,
                    "afmt": _E2T_BACK}],
        css=_AUDIO_CSS,
    )


def _stage_media(src: Path, stage: Path, prefix: str) -> str:
    """Hardlink src into stage under {prefix}__{basename}; return basename."""
    prefixed = f"{prefix}__{src.name}"
    dst = stage / prefixed
    if not dst.exists() or dst.stat().st_size != src.stat().st_size:
        dst.unlink(missing_ok=True)
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
    return prefixed


def _source_html(idiom_text: str, video_title: str | None,
                  youtube_id: str | None) -> str:
    bits: list[str] = []
    if idiom_text:
        bits.append(f"<i>{html.escape(idiom_text)}</i>")
    if video_title:
        bits.append(html.escape(video_title))
    if youtube_id:
        bits.append(f'<a href="https://www.youtube.com/watch?v={youtube_id}">'
                    f'youtube.com/watch?v={youtube_id}</a>')
    return " — ".join(bits)


# ============================================================================
# The three builders
# ============================================================================

def _build_expression_pool(lang: str, idioms: list[dict],
                            stage_dir: Path, out: Path) -> int:
    """Returns card count."""
    deck_name = f"Idiomatic::{_LANG_NAMES.get(lang, lang.upper())}::Fluency Expressions"
    deck = genanki.Deck(_deck_id(deck_name), deck_name)
    model = _expr_model()
    media_files: list[str] = []
    n_cards = 0
    seen: set[str] = set()
    for idiom in idioms:
        idiom_text = idiom["idiom_text"]
        idiom_en = idiom["english_gloss"]
        youtube_id = idiom.get("youtube_id")
        video_title = idiom.get("video_title")
        source = _source_html(idiom_text, video_title, youtube_id)
        for ex in idiom["examples"]:
            en_text = ex["en_text"]
            tg_text = ex["target_text"]
            guid = _guid("yt-pool", _norm(idiom_text), _norm(tg_text))
            if guid in seen:
                continue
            seen.add(guid)
            en_src = ex.get("audio_en")
            tg_src = ex.get("audio_target")
            en_field = ""
            tg_field = ""
            if en_src:
                src = Path(get_settings().data_dir) / "staged_audio" / en_src
                if src.exists():
                    name = _stage_media(src, stage_dir, youtube_id or "noid")
                    media_files.append(str(stage_dir / name))
                    en_field = f"[sound:{name}]"
            if tg_src:
                src = Path(get_settings().data_dir) / "staged_audio" / tg_src
                if src.exists():
                    name = _stage_media(src, stage_dir, youtube_id or "noid")
                    media_files.append(str(stage_dir / name))
                    tg_field = f"[sound:{name}]"
            deck.add_note(genanki.Note(
                model=model,
                fields=[en_text, tg_text, en_field, tg_field,
                        idiom_text, idiom_en, source],
                guid=guid,
                tags=["youtube", lang, "fluency-pool"],
            ))
            n_cards += 1
    out.parent.mkdir(parents=True, exist_ok=True)
    pkg = genanki.Package(deck)
    pkg.media_files = list(set(media_files))
    pkg.write_to_file(str(out))
    return n_cards


def _build_idiom_audio_pool(lang: str, idioms: list[dict],
                             stage_dir: Path, out: Path,
                             direction: str) -> int:
    """direction is 't2e' or 'e2t'."""
    assert direction in ("t2e", "e2t")
    suffix = "(target → EN)" if direction == "t2e" else "(EN → target)"
    deck_name = (f"Idiomatic::{_LANG_NAMES.get(lang, lang.upper())}::"
                 f"Idioms Audio {suffix}")
    deck = genanki.Deck(_deck_id(deck_name), deck_name)
    model = _t2e_model() if direction == "t2e" else _e2t_model()
    media_files: list[str] = []
    n_cards = 0
    seen: set[str] = set()
    for idiom in idioms:
        idiom_text = idiom["idiom_text"]
        idiom_en = idiom["english_gloss"]
        youtube_id = idiom.get("youtube_id")
        video_title = idiom.get("video_title")
        source = _source_html(idiom_text, video_title, youtube_id)
        tgt_src = idiom.get("audio_idiom_tgt")
        en_src = idiom.get("audio_idiom_en")
        if not (tgt_src and en_src):
            continue  # no audio → no card
        guid = _guid(f"yt-pool-{direction}", _norm(idiom_text))
        if guid in seen:
            continue
        seen.add(guid)
        # Stage media
        tgt_path = Path(get_settings().data_dir) / "staged_audio" / tgt_src
        en_path = Path(get_settings().data_dir) / "staged_audio" / en_src
        if not (tgt_path.exists() and en_path.exists()):
            continue
        tgt_name = _stage_media(tgt_path, stage_dir, youtube_id or "noid")
        en_name = _stage_media(en_path, stage_dir, youtube_id or "noid")
        media_files.append(str(stage_dir / tgt_name))
        media_files.append(str(stage_dir / en_name))
        if direction == "t2e":
            front_audio = f"[sound:{tgt_name}]"
            back_audio = f"[sound:{en_name}]"
        else:
            front_audio = f"[sound:{en_name}]"
            back_audio = f"[sound:{tgt_name}]"
        deck.add_note(genanki.Note(
            model=model,
            fields=[idiom_text, idiom_en, front_audio, back_audio, source],
            guid=guid,
            tags=["youtube", lang, "idiom-audio", direction],
        ))
        n_cards += 1
    out.parent.mkdir(parents=True, exist_ok=True)
    pkg = genanki.Package(deck)
    pkg.media_files = list(set(media_files))
    pkg.write_to_file(str(out))
    return n_cards


# ============================================================================
# 4th builder: per-language Idioms didactic deck (mirrors apkg.py model)
# ============================================================================

def _stitch_pool_card_audio(*, lang: str, idiom: dict, narration_root: Path,
                              stage_dir: Path, youtube_id: str) -> tuple[Path, Path] | None:
    """Restitch front + back per-card audio for the pool deck using the
    persisted per-card mp3s + cached narration. Returns (front, back) or
    None if essential pieces are missing.

    Front layout (pimsleur shape):
      here_it_is → idiom_tgt → meaning → idiom_en
      → how_to_use → explanation_en TTS → examples_intro
      → ex1_en → sh → ex1_tgt → md → ex2_en → sh → ex2_tgt → md → ex3_en → sh → ex3_tgt

    Back layout:
      practice_intro → sentence_1 → ex4_en → think → ex4_tgt → lg
      → sentence_2 → ex5_en → think → ex5_tgt → lg
      → sentence_3 → ex6_en → think → ex6_tgt

    Note: the original-video snippet is OMITTED from pool cards — that
    snippet is per-video and doesn't fit a cross-video aggregation.
    """
    data_root = Path(get_settings().data_dir) / "staged_audio"
    seed = f"pool::{lang}::{idiom['id']}"
    sh = audio_mod.silence_mp3(narration_root, 300)
    md = audio_mod.silence_mp3(narration_root, 700)
    lg = audio_mod.silence_mp3(narration_root, 1200)
    think = audio_mod.silence_mp3(narration_root, 1500)
    lang_name = _LANG_NAMES.get(lang, lang.upper())

    def _narr(key: str, lang_filled: bool = False) -> Path | None:
        text, p = connectives.pick_general(
            narration_root, key, seed,
            lang_name=(lang_name if lang_filled else None),
        )
        if not p or not p.exists():
            return None
        return p

    # Resolve per-card audio paths
    tgt = idiom.get("audio_idiom_tgt")
    en = idiom.get("audio_idiom_en")
    if not (tgt and en):
        return None
    idiom_tgt = data_root / tgt
    idiom_en = data_root / en
    if not (idiom_tgt.exists() and idiom_en.exists()):
        return None

    listen_context = _narr("listen_context")
    here_it_is = _narr("here_it_is")
    meaning = _narr("meaning")
    how_to_use = _narr("how_to_use")
    examples_intro = _narr("examples_intro")
    practice_intro = _narr("practice_intro", lang_filled=True)
    sentence_leads = [_narr(f"sentence_{i}") for i in (1, 2, 3)]

    # Examples
    examples = idiom.get("examples") or []
    ex_files: list[tuple[Path | None, Path | None]] = []
    for ex in examples:
        ae = ex.get("audio_en")
        at = ex.get("audio_target")
        p_en = data_root / ae if ae else None
        p_tg = data_root / at if at else None
        ex_files.append((
            p_en if p_en and p_en.exists() else None,
            p_tg if p_tg and p_tg.exists() else None,
        ))

    teach = ex_files[:3]
    drill = ex_files[3:6]

    # Front audio: connectives are SKIPPED if missing (degrade gracefully)
    front_pieces: list[Path] = []
    if here_it_is: front_pieces += [here_it_is, sh]
    front_pieces += [idiom_tgt, md]
    if meaning: front_pieces += [meaning, sh]
    front_pieces += [idiom_en, md]
    # Explanation paragraph if available
    explanation_text = (idiom.get("explanation_en") or "").strip()
    if explanation_text:
        # We didn't pre-TTS the explanation. For pool cards we can either
        # TTS it inline (slow) or skip. Skip for now — text is shown on
        # the card; the lesson audio still works without it.
        pass
    if teach and any(en and tg for en, tg in teach):
        if examples_intro: front_pieces += [examples_intro, sh]
        for i, (en_p, tgt_p) in enumerate(teach):
            if not (en_p and tgt_p):
                continue
            if i > 0: front_pieces.append(md)
            front_pieces += [en_p, sh, tgt_p]

    # Back audio
    back_pieces: list[Path] = []
    if practice_intro: back_pieces += [practice_intro, md]
    drilled = 0
    for i, (en_p, tgt_p) in enumerate(drill):
        if not (en_p and tgt_p):
            continue
        if drilled > 0: back_pieces.append(lg)
        lead = sentence_leads[i] if i < 3 else None
        if lead: back_pieces += [lead, sh]
        back_pieces += [en_p, think, tgt_p]
        drilled += 1

    out_front = stage_dir / f"pool_{youtube_id}_idiom_{idiom['id']}_front.mp3"
    out_back = stage_dir / f"pool_{youtube_id}_idiom_{idiom['id']}_back.mp3"
    if not front_pieces or not back_pieces:
        return None
    audio_mod.concat_mp3s(front_pieces, out_front)
    audio_mod.concat_mp3s(back_pieces, out_back)
    return out_front, out_back


def _build_idioms_pool(lang: str, idioms: list[dict],
                       narration_root: Path,
                       stage_dir: Path, out: Path) -> int:
    """Build the per-language Idioms didactic pool deck."""
    deck_name = f"Idiomatic::{_LANG_NAMES.get(lang, lang.upper())}::Idioms"
    deck = genanki.Deck(_deck_id(deck_name), deck_name)
    model = apkg_mod.make_model()
    media_files: list[str] = []
    seen: set[str] = set()
    n_cards = 0
    for idiom in idioms:
        idiom_text = idiom["idiom_text"]
        idiom_en = idiom["english_gloss"]
        youtube_id = idiom.get("youtube_id") or "noid"
        video_title = idiom.get("video_title") or ""
        guid = _guid(f"yt-idiom-pool::{lang}", _norm(idiom_text))
        if guid in seen:
            continue
        seen.add(guid)

        stitched = _stitch_pool_card_audio(
            lang=lang, idiom=idiom, narration_root=narration_root,
            stage_dir=stage_dir, youtube_id=youtube_id,
        )
        if not stitched:
            log.info("pool.idioms.skip_no_audio", idiom_id=idiom["id"])
            continue
        front_path, back_path = stitched

        # Stage the front/back audio (already in stage_dir; just register)
        front_name = front_path.name
        back_name = back_path.name
        media_files.append(str(front_path))
        media_files.append(str(back_path))

        # Stage individual example audios for the card display? No — the
        # display uses text fields only; only front/back audio is needed.

        examples = idiom.get("examples") or []
        example_fields: list[str] = []
        for k in range(apkg_mod.EXAMPLES_PER_IDIOM):
            example_fields.append(
                examples[k]["en_text"] if k < len(examples) else "")
            example_fields.append(
                examples[k]["target_text"] if k < len(examples) else "")

        source_html_str = _source_html(idiom_text, video_title, youtube_id)
        deck.add_note(genanki.Note(
            model=model,
            fields=[
                f"{n_cards + 1:03d}",
                idiom_text, idiom_en,
                idiom.get("explanation_en") or "",
                *example_fields,
                idiom.get("source_phrase_target") or "",
                idiom.get("source_phrase_en") or "",
                f"[sound:{front_name}]",
                f"[sound:{back_name}]",
                source_html_str,
                apkg_mod.structured_html(idiom.get("structured")),
            ],
            guid=guid,
            tags=["youtube", lang, "idiomatic-pool"],
        ))
        n_cards += 1

    out.parent.mkdir(parents=True, exist_ok=True)
    pkg = genanki.Package(deck)
    pkg.media_files = list({m for m in media_files})
    pkg.write_to_file(str(out))
    return n_cards


# ============================================================================
# Top-level: rebuild every pool apkg for a language
# ============================================================================

async def rebuild_pools(lang: str, force: bool = False) -> dict:
    """Builds ALL four pool apkgs for the language and upserts their rows
    in the apkgs table. Returns a stats dict.

    Debounced: skipped when the language was already rebuilt within the
    last `pool_rebuild_debounce_min` minutes, unless force=True
    (/admin/rebuild-pools). A skipped rebuild is harmless — the next
    non-debounced one reads the full DB and picks everything up.
    """
    settings = get_settings()
    if not force and await db.pool_rebuilt_within(
            lang, settings.pool_rebuild_debounce_min):
        log.info("pool.skip_debounced", lang=lang,
                 window_min=settings.pool_rebuild_debounce_min)
        return {"lang": lang, "debounced": True}
    idioms = await db.fetch_pool_idioms(lang)
    if not idioms:
        log.info("pool.skip_empty", lang=lang)
        return {"lang": lang, "n_idioms": 0,
                "idioms_cards": 0, "expr_cards": 0,
                "t2e_cards": 0, "e2t_cards": 0}

    apkg_root = Path(settings.data_dir) / "apkgs" / lang
    apkg_root.mkdir(parents=True, exist_ok=True)
    stage_root = Path(settings.data_dir) / "_pool_stage" / lang
    # Clean the stage dir each rebuild so leftover media from removed
    # videos don't bloat the apkgs.
    if stage_root.exists():
        shutil.rmtree(stage_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    narration_root = Path(settings.data_dir) / "narration"

    idioms_apkg = apkg_root / "_pool_idioms.apkg"
    expr_apkg = apkg_root / "_pool_expressions.apkg"
    t2e_apkg = apkg_root / "_pool_idioms_t2e.apkg"
    e2t_apkg = apkg_root / "_pool_idioms_e2t.apkg"

    idioms_n = _build_idioms_pool(lang, idioms, narration_root,
                                    stage_root, idioms_apkg)
    expr_n = _build_expression_pool(lang, idioms, stage_root, expr_apkg)
    t2e_n = _build_idiom_audio_pool(lang, idioms, stage_root, t2e_apkg, "t2e")
    e2t_n = _build_idiom_audio_pool(lang, idioms, stage_root, e2t_apkg, "e2t")

    for kind, path, n in (
        ("pool_idioms", idioms_apkg, idioms_n),
        ("pool_expr", expr_apkg, expr_n),
        ("pool_idiom_t2e", t2e_apkg, t2e_n),
        ("pool_idiom_e2t", e2t_apkg, e2t_n),
    ):
        if n == 0:
            continue
        rel = path.relative_to(Path(settings.data_dir))
        apkg_id = await db.upsert_pool_apkg(
            lang=lang, kind=kind, filename=str(rel),
            size_bytes=path.stat().st_size, n_idioms=n,
        )
        log.info("pool.upserted", lang=lang, kind=kind,
                 apkg_id=apkg_id, n=n, size=path.stat().st_size)

    # Stamp only after a successful rebuild so a failed one isn't debounced.
    await db.mark_pool_rebuilt(lang)

    return {"lang": lang, "n_idioms": len(idioms),
            "idioms_cards": idioms_n,
            "expr_cards": expr_n,
            "t2e_cards": t2e_n,
            "e2t_cards": e2t_n}
