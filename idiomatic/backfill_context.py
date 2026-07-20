"""One-shot backfill of context clips (audio_context) for idioms
harvested before 2026-07-20, when sentence-level slicing landed.

For each done video that still has idioms without audio_context:

  1. Re-fetch its audio via Oxylabs → R2 (R2-reuse aware).
  2. ONE Gemini audio call: here are the numbered source sentences we
     already transcribed for this video — return start/end seconds for
     each. We never stored the original expression timestamps, so if
     Gemini can't locate a sentence there is no fallback window: that
     idiom is skipped rather than given a wrong clip.
  3. Slice each located sentence (±0.25/0.35s padding, same as the live
     path) → stage as staged_audio/<youtube_id>/context_bf_<idiom_id>.mp3
     → UPDATE expression_idioms.audio_context.
  4. Drop the R2 object and the local work dir (127 videos × ~15 MB
     would otherwise fill /tmp).
  5. After all videos: force-rebuild pools for every touched language so
     the pool decks pick up the clips.

Idempotent + resumable: the video query only returns videos that still
have clip-less idioms, and each UPDATE is per-idiom — a mid-run restart
(deploy, crash) just continues where it left off on the next POST.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import structlog

from . import db, gemini, oxylabs_client
from .langs import LANG_NAMES as _LANG_NAMES
from .pipeline import audio as audio_mod
from .settings import get_settings

log = structlog.get_logger()

_MAX_CLIP_SEC = 45.0
_MIN_CLIP_SEC = 1.0

_PROMPT = """You are listening to a {lang_name} video. Below are {n} numbered sentences that were transcribed from this audio earlier. For EACH sentence, find where it is actually spoken and return its precise time window.

Output a JSON OBJECT mapping the sentence NUMBER (as a string) to an object:
  - "start": start time in seconds (float) of the first word of the sentence.
  - "end": end time in seconds (float) of the last word of the sentence.

Pin the window to the spoken sentence itself — it will be sliced out of the audio for a language-learning flashcard. If a sentence appears more than once, pick the clearest occurrence. If you cannot find a sentence in the audio, map its number to null.

Sentences:
{sentences}

Output ONLY the JSON object, no preamble."""


async def _locate_sentences(*, source_audio: Path, lang: str,
                             idioms: list[dict]) -> dict[int, tuple[float, float]]:
    """idiom_id → (start, end) for every sentence Gemini could locate
    with a plausible window."""
    lang_name = _LANG_NAMES.get(lang, lang.upper())
    numbered = [(n, i) for n, i in enumerate(idioms, 1)]
    sentences = "\n".join(
        f"  {n}. {i['source_phrase_target']}" for n, i in numbered)
    raw = await gemini.generate_from_audio(
        _PROMPT.format(lang_name=lang_name, n=len(numbered),
                        sentences=sentences),
        source_audio, json_mode=True, temperature=0.2,
    )
    if not isinstance(raw, dict):
        log.warning("backfill_context.unexpected_shape",
                     got=type(raw).__name__)
        return {}
    out: dict[int, tuple[float, float]] = {}
    for n, idiom in numbered:
        w = raw.get(str(n))
        if not isinstance(w, dict):
            continue
        try:
            start, end = float(w["start"]), float(w["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if start < 0 or not (_MIN_CLIP_SEC <= end - start <= _MAX_CLIP_SEC):
            continue
        out[idiom["id"]] = (start, end)
    return out


async def _backfill_one_video(video: dict) -> dict:
    settings = get_settings()
    youtube_id = video["youtube_id"]
    lang = video["lang"]
    pool = await db.get_pool()
    idioms = [dict(r) for r in await pool.fetch(
        """
        SELECT id, idiom_text, source_phrase_target
        FROM expression_idioms
        WHERE video_id = $1 AND audio_context IS NULL
          AND COALESCE(source_phrase_target, '') <> ''
        ORDER BY id
        """,
        video["id"],
    )]
    if not idioms:
        return {"youtube_id": youtube_id, "lang": lang, "clips": 0,
                "skipped": "no clip-less idioms with sentences"}

    work_root = Path("/tmp") / "idiomatic_ctx_backfill" / youtube_id
    work_root.mkdir(parents=True, exist_ok=True)
    try:
        try:
            source_audio, _dur = await oxylabs_client.fetch_audio(
                youtube_id, work_root)
        except oxylabs_client.OxylabsPermanentVideoFailure as e:
            return {"youtube_id": youtube_id, "lang": lang, "clips": 0,
                    "error": f"video gone: {str(e)[:120]}"}
        except Exception as e:
            return {"youtube_id": youtube_id, "lang": lang, "clips": 0,
                    "error": f"oxylabs: {str(e)[:200]}"}

        try:
            windows = await _locate_sentences(
                source_audio=source_audio, lang=lang, idioms=idioms)
        except Exception as e:
            return {"youtube_id": youtube_id, "lang": lang, "clips": 0,
                    "error": f"gemini: {str(e)[:200]}"}

        stage_dir = Path(settings.data_dir) / "staged_audio" / youtube_id
        stage_dir.mkdir(parents=True, exist_ok=True)
        clips = 0
        for idiom in idioms:
            w = windows.get(idiom["id"])
            if not w:
                continue
            start, end = w
            out = stage_dir / f"context_bf_{idiom['id']}.mp3"
            try:
                audio_mod.slice_clip(source_audio, max(0.0, start - 0.25),
                                      end + 0.35, out)
            except Exception as e:
                log.warning("backfill_context.slice_failed",
                             idiom_id=idiom["id"], err=repr(e)[:150])
                continue
            if not out.exists() or out.stat().st_size < 2000:
                out.unlink(missing_ok=True)
                continue
            await pool.execute(
                "UPDATE expression_idioms SET audio_context = $2 WHERE id = $1",
                idiom["id"], f"{youtube_id}/{out.name}",
            )
            clips += 1

        # The video finished long ago — drop the R2 object we just
        # (re)paid for instead of orphaning it.
        try:
            await oxylabs_client.cleanup_r2(youtube_id)
        except Exception as e:
            log.warning("backfill_context.r2_cleanup_failed",
                         err=repr(e)[:150])
        return {"youtube_id": youtube_id, "lang": lang,
                "n_idioms": len(idioms), "located": len(windows),
                "clips": clips}
    finally:
        shutil.rmtree(work_root, ignore_errors=True)


# ---- orchestration ---------------------------------------------------------

_STATE: dict = {"running": False, "total": 0, "done": 0, "clips": 0,
                 "current": None, "stats": [], "started_at": None,
                 "finished_at": None, "error": None}


def get_state() -> dict:
    return dict(_STATE)


async def run_backfill_context(limit: int | None = None,
                                rebuild: bool = True) -> None:
    if _STATE["running"]:
        return
    _STATE.update(running=True, total=0, done=0, clips=0, current=None,
                   stats=[], started_at=time.time(), finished_at=None,
                   error=None)
    try:
        pool = await db.get_pool()
        videos = [dict(r) for r in await pool.fetch(
            """
            SELECT v.id, v.youtube_id, v.lang, v.title
            FROM videos v
            WHERE v.status = 'done' AND EXISTS (
                SELECT 1 FROM expression_idioms i
                WHERE i.video_id = v.id AND i.audio_context IS NULL
                  AND COALESCE(i.source_phrase_target, '') <> '')
            ORDER BY v.id
            """,
        )]
        if limit:
            videos = videos[:limit]
        _STATE["total"] = len(videos)
        langs_touched: set[str] = set()
        for v in videos:
            _STATE["current"] = v["youtube_id"]
            log.info("backfill_context.video_start", yt=v["youtube_id"],
                     lang=v["lang"], title=(v["title"] or "")[:50])
            stats = await _backfill_one_video(v)
            _STATE["stats"].append(stats)
            _STATE["done"] += 1
            _STATE["clips"] += stats.get("clips", 0)
            log.info("backfill_context.video_done", **stats)
            if stats.get("clips"):
                langs_touched.add(v["lang"])
        _STATE["current"] = None

        if rebuild and langs_touched:
            from .pipeline import pool as pool_mod
            for lang in sorted(langs_touched):
                try:
                    r = await pool_mod.rebuild_pools(lang, force=True)
                    log.info("backfill_context.pools_rebuilt", lang=lang,
                             **(r or {}))
                except Exception as e:
                    log.warning("backfill_context.pool_rebuild_failed",
                                 lang=lang, err=repr(e)[:200])
    except Exception as e:
        _STATE["error"] = repr(e)[:300]
        log.exception("backfill_context.failed", err=str(e))
    finally:
        _STATE["running"] = False
        _STATE["finished_at"] = time.time()
