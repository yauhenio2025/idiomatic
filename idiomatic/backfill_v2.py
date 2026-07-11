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

import time
from pathlib import Path

import structlog

from . import db, gemini, oxylabs_client
from .langs import LANG_NAMES as _LANG_NAMES
from .pipeline import pool as pool_mod
from .settings import get_settings

log = structlog.get_logger()


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
