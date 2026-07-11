"""One-shot backfill for the new schema columns and the pimsleur-shape audio.

For each of the existing N videos:

  1. Re-fetch its audio from Oxylabs into /tmp (cached).
  2. Send the audio + the list of THIS video's known idioms to Gemini
     in ONE call. Gemini fills in (for each idiom):
       - source_phrase_target: the verbatim sentence where it occurred
       - source_phrase_en:    its English translation
       - explanation_en:      a 2-3 sentence learner-oriented explanation
     We DON'T re-extract idioms — that would risk picking different
     idioms than the existing rows. We give Gemini the idiom list and
     ask it to look them up in the audio.
  3. Update expression_idioms rows.
  4. TTS the explanation_en paragraph for each idiom → stage_audio.
  5. Re-stitch front_NNN.mp3 + back_NNN.mp3 from the persisted per-card
     mp3s + the cached narration cues, using the new pimsleur shape.
  6. After all videos: rebuild pool apkgs (now includes the 4th
     per-language Idioms deck) per language.

Idempotent: row inserts use ON CONFLICT or pre-checks; TTS skips on
existing non-empty files; stitched mp3s overwrite cleanly.
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from pathlib import Path

import structlog

from . import db, gemini, oxylabs_client
from .pipeline import audio as audio_mod
from .pipeline import connectives
from .pipeline import pool as pool_mod
from .pipeline.audio import EN_VOICE, LANG_VOICE
from .pipeline.dedup import normalize
from .settings import get_settings

log = structlog.get_logger()


_LANG_NAMES = {
    "de": "German", "fr": "French", "it": "Italian",
    "pt": "Portuguese", "es": "Spanish", "zh": "Mandarin",
}


# ---- Gemini call: trigger sentences + explanations for one video ----------

_BACKFILL_PROMPT = """You are listening to a {lang_name} video. I will give you a list of {n} expressions that appear in the audio. For EACH listed expression, do the following:

1. Find the FULL {lang_name} sentence from the audio that actually contains this expression — verbatim, including everything around it. If the expression appears more than once, pick the most pedagogically clear occurrence.
2. Translate that sentence into natural English.
3. Write a 2-3 sentence English explanation of what the expression means, when to use it, and any notable register / collocation / grammatical pitfall a B2/C1 learner should know. Plain English. Like a textbook usage note, not a dictionary entry.

Output a JSON OBJECT with one key per expression. The key is the expression EXACTLY as I gave it. The value is an object with keys:
  - "source_phrase": the full {lang_name} sentence (verbatim from the audio).
  - "source_phrase_en": its English translation.
  - "explanation": the 2-3 sentence English explanation.

If you cannot find an expression in the audio, return null for that key.

Expressions to look up:
{idiom_list}

Output ONLY the JSON object, no preamble."""


async def _backfill_video_via_gemini(*, source_audio: Path, lang: str,
                                       idioms: list[dict]) -> dict[str, dict]:
    """Returns a dict mapping idiom_text → {source_phrase, source_phrase_en,
    explanation}."""
    lang_name = _LANG_NAMES.get(lang, lang.upper())
    idiom_list = "\n".join(f"  - {i['idiom_text']}" for i in idioms)
    prompt = _BACKFILL_PROMPT.format(
        lang_name=lang_name, n=len(idioms), idiom_list=idiom_list,
    )
    raw = await gemini.generate_from_audio(
        prompt, source_audio, json_mode=True, temperature=0.2,
    )
    if not isinstance(raw, dict):
        log.warning("backfill_v2.unexpected_shape", got=type(raw).__name__)
        return {}
    return raw


# ---- Re-stitch one card's front/back audio --------------------------------

async def _restitch_card(*, idiom_row: dict, stage_dir: Path,
                          narration_root: Path, lang: str) -> tuple[Path, Path] | None:
    """Rebuild front/back mp3s for an existing card. Uses the persisted
    per-card mp3s + the narration cache + (optionally) a freshly TTS'd
    explanation paragraph. Returns (front, back) paths or None."""
    voice_tgt = LANG_VOICE.get(lang, "Charon")
    lang_name = _LANG_NAMES.get(lang, lang.upper())
    idiom_id = idiom_row["id"]
    seed = f"backfill::{lang}::{idiom_id}"

    sh = audio_mod.silence_mp3(narration_root, 300)
    md = audio_mod.silence_mp3(narration_root, 700)
    lg = audio_mod.silence_mp3(narration_root, 1200)
    think = audio_mod.silence_mp3(narration_root, 1500)

    def _narr(key: str, lang_filled: bool = False) -> Path | None:
        text, p = connectives.pick_general(
            narration_root, key, seed,
            lang_name=(lang_name if lang_filled else None),
        )
        if not p or not p.exists():
            return None
        return p

    data_root = Path(get_settings().data_dir) / "staged_audio"

    tgt_rel = idiom_row.get("audio_idiom_tgt")
    en_rel = idiom_row.get("audio_idiom_en")
    if not (tgt_rel and en_rel):
        return None
    idiom_tgt = data_root / tgt_rel
    idiom_en = data_root / en_rel
    if not (idiom_tgt.exists() and idiom_en.exists()):
        return None

    # Per-idiom explanation TTS goes into the SAME staged_audio dir.
    youtube_id = (idiom_row.get("youtube_id")
                  or (idiom_row.get("audio_idiom_tgt") or "").split("/", 1)[0])
    per_video_stage = data_root / youtube_id
    per_video_stage.mkdir(parents=True, exist_ok=True)
    explanation_audio: Path | None = None
    expl_text = (idiom_row.get("explanation_en") or "").strip()
    if expl_text:
        explanation_audio = per_video_stage / f"explanation_{idiom_id}.mp3"
        await gemini.synthesize(expl_text, voice=EN_VOICE,
                                  out=explanation_audio)

    # Examples
    examples = idiom_row.get("examples") or []
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

    listen_context = _narr("listen_context")
    here_it_is = _narr("here_it_is")
    meaning = _narr("meaning")
    how_to_use = _narr("how_to_use")
    examples_intro = _narr("examples_intro")
    practice_intro = _narr("practice_intro", lang_filled=True)
    s1, s2, s3 = (_narr(f"sentence_{i}") for i in (1, 2, 3))

    # FRONT — no per-video snippet for backfilled cards (we don't have
    # the source.aac persisted), so we lead with here_it_is.
    front_pieces: list[Path] = []
    if here_it_is: front_pieces += [here_it_is, sh]
    front_pieces += [idiom_tgt, md]
    if meaning: front_pieces += [meaning, sh]
    front_pieces += [idiom_en, md]
    if explanation_audio:
        if how_to_use: front_pieces += [how_to_use, sh]
        front_pieces += [explanation_audio, md]
    if any(en and tg for en, tg in teach):
        if examples_intro: front_pieces += [examples_intro, sh]
        first = True
        for en_p, tgt_p in teach:
            if not (en_p and tgt_p):
                continue
            if not first: front_pieces.append(md)
            front_pieces += [en_p, sh, tgt_p]
            first = False

    front = stage_dir / f"backfill_idiom_{idiom_id}_front.mp3"
    audio_mod.concat_mp3s(front_pieces, front)

    # BACK
    back_pieces: list[Path] = []
    if practice_intro: back_pieces += [practice_intro, md]
    leads = [s1, s2, s3]
    drilled = 0
    for i, (en_p, tgt_p) in enumerate(drill):
        if not (en_p and tgt_p):
            continue
        if drilled > 0: back_pieces.append(lg)
        if leads[i]: back_pieces += [leads[i], sh]
        back_pieces += [en_p, think, tgt_p]
        drilled += 1
    back = stage_dir / f"backfill_idiom_{idiom_id}_back.mp3"
    if back_pieces and drilled > 0:
        audio_mod.concat_mp3s(back_pieces, back)
    else:
        audio_mod.concat_mp3s([sh], back, normalize_loudness=False)
    return front, back


# ---- Backfill one video ---------------------------------------------------

async def backfill_one_video_v2(*, video: dict) -> dict:
    """video: row from videos table. Returns stats."""
    settings = get_settings()
    youtube_id = video["youtube_id"]
    lang = video["lang"]

    # All the existing idiom rows for this video
    pool = await db.get_pool()
    idioms = await pool.fetch(
        """
        SELECT id, idiom_text, english_gloss,
               audio_idiom_tgt, audio_idiom_en,
               source_phrase_target, source_phrase_en, explanation_en
        FROM expression_idioms
        WHERE video_id = $1 AND lang = $2
        ORDER BY id
        """,
        video["id"], lang,
    )
    idioms = [dict(r) for r in idioms]
    if not idioms:
        return {"youtube_id": youtube_id, "n_idioms": 0, "skipped": "no idioms"}

    # 1. Fetch source audio (cached in R2 from Oxylabs; reusing the
    # same flow as the worker's _download_audio)
    work_root = Path("/tmp") / "idiomatic_backfill" / youtube_id
    work_root.mkdir(parents=True, exist_ok=True)
    source_audio = None
    for existing in work_root.glob("source.*"):
        if existing.stat().st_size > 0:
            source_audio = existing
            break
    if source_audio is None:
        try:
            # R2-reuse aware; only submits (and pays for) a new job when
            # the bucket has nothing for this video.
            source_audio, _dur = await oxylabs_client.fetch_audio(
                youtube_id, work_root,
            )
        except Exception as e:
            return {"youtube_id": youtube_id, "error": f"oxylabs: {e}"}

    # 2. One Gemini call to fill in trigger + explanation for ALL idioms
    needs_gemini = [i for i in idioms
                    if not (i.get("source_phrase_target") and
                            i.get("source_phrase_en") and
                            i.get("explanation_en"))]
    gemini_result: dict[str, dict] = {}
    if needs_gemini:
        try:
            gemini_result = await _backfill_video_via_gemini(
                source_audio=source_audio, lang=lang, idioms=needs_gemini,
            )
        except Exception as e:
            log.warning("backfill_v2.gemini_failed",
                         youtube_id=youtube_id, err=repr(e)[:200])

    # 3. Update DB
    updated = 0
    for row in idioms:
        if row["source_phrase_target"] and row["source_phrase_en"] and row["explanation_en"]:
            continue
        g = gemini_result.get(row["idiom_text"])
        if not isinstance(g, dict):
            continue
        await pool.execute(
            """
            UPDATE expression_idioms SET
              source_phrase_target = COALESCE($2, source_phrase_target),
              source_phrase_en     = COALESCE($3, source_phrase_en),
              explanation_en       = COALESCE($4, explanation_en)
            WHERE id = $1
            """,
            row["id"],
            (g.get("source_phrase") or "").strip() or None,
            (g.get("source_phrase_en") or "").strip() or None,
            (g.get("explanation") or "").strip() or None,
        )
        updated += 1

    # These videos are long done — drop the R2 object we just (re)bought
    # instead of orphaning it (backfill_v2 previously never cleaned up).
    try:
        await oxylabs_client.cleanup_r2(youtube_id)
    except Exception as e:
        log.warning("backfill_v2.r2_cleanup_failed", err=repr(e)[:150])

    return {
        "youtube_id": youtube_id, "lang": lang,
        "n_idioms": len(idioms),
        "needed_gemini": len(needs_gemini),
        "updated": updated,
    }


# ---- Top-level orchestration ----------------------------------------------

_STATE: dict = {"running": False, "stats": [], "started_at": None,
                 "finished_at": None, "error": None}


async def run_backfill_v2() -> dict:
    if _STATE["running"]:
        return {"error": "already running"}
    _STATE.update(running=True, stats=[], started_at=time.time(),
                   finished_at=None, error=None)
    try:
        pool = await db.get_pool()
        videos = await pool.fetch(
            "SELECT id, youtube_id, lang, title FROM videos WHERE status = 'done' ORDER BY id"
        )
        langs_touched: set[str] = set()
        for v in videos:
            v = dict(v)
            log.info("backfill_v2.video_start", **v)
            stats = await backfill_one_video_v2(video=v)
            _STATE["stats"].append(stats)
            log.info("backfill_v2.video_done", **stats)
            if "lang" in stats:
                langs_touched.add(stats["lang"])
        for lang in sorted(langs_touched):
            log.info("backfill_v2.rebuild_pool_start", lang=lang)
            res = await pool_mod.rebuild_pools(lang)
            _STATE["stats"].append({"pool_rebuild": res})
            log.info("backfill_v2.rebuild_pool_done", **res)
    except Exception as e:
        _STATE["error"] = repr(e)[:300]
        log.exception("backfill_v2.crashed")
    finally:
        _STATE["running"] = False
        _STATE["finished_at"] = time.time()
    return _STATE


def get_state() -> dict:
    s = dict(_STATE)
    s["n_completed"] = len([x for x in s["stats"] if "youtube_id" in x])
    return s
