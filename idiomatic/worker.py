"""Worker loop. Drains the videos queue and produces apkgs.

Runs as an asyncio task inside the same process as the FastAPI app (see
api.py:lifespan). Single producer, single consumer — Postgres SKIP LOCKED
gives us correct claim semantics if we ever scale to multiple instances.
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import structlog
from slugify import slugify  # python-slugify pkg, slugify module

from . import db
from . import oxylabs_client
from .pipeline import audio as audio_mod
from .pipeline import connectives
from .pipeline.apkg import build_apkg
from .pipeline.dedup import normalize
from .pipeline.explain import enrich_one
from .pipeline.extract import extract_from_audio
from .settings import get_settings

log = structlog.get_logger()


# ---- one-video helpers ----------------------------------------------------

async def _download_audio(youtube_id: str, dst_dir: Path) -> Path:
    """Fetch the audio track via Oxylabs YouTube Downloader → Cloudflare R2.

    Idempotent. Returns the audio file path (extension depends on what
    Oxylabs returns — typically .aac or .m4a; Gemini and ffmpeg accept both).
    Oxylabs eats the bot-wall fight on their side.
    """
    # Fast path: if we already pulled it locally, reuse it (worker may retry
    # this video).
    for existing in dst_dir.glob("source.*"):
        if existing.is_file() and existing.stat().st_size > 0:
            return existing
    dst_dir.mkdir(parents=True, exist_ok=True)
    job_id = await oxylabs_client.submit_audio_job(youtube_id)
    await oxylabs_client.wait_for_done(job_id)
    out = await oxylabs_client.download_audio(youtube_id, job_id, dst_dir)
    # Best-effort R2 cleanup so the bucket doesn't grow forever.
    await oxylabs_client.cleanup_r2(youtube_id)
    return out


async def _filter_fresh(extracted: list, lang: str) -> list:
    """Drop phrases already in the expression library."""
    existing = await db.existing_normalized_for_lang(lang)
    fresh = [p for p in extracted if p.normalized not in existing]
    log.info("worker.dedup", n_extracted=len(extracted), n_fresh=len(fresh))
    return fresh


# ---- daily cap check ------------------------------------------------------

async def _under_daily_cap(lang: str) -> bool:
    settings = get_settings()
    pool = await db.get_pool()
    n_today = await pool.fetchval(
        """
        SELECT COUNT(*) FROM apkgs
        WHERE lang = $1 AND created_at >= date_trunc('day', NOW())
        """,
        lang,
    )
    return n_today < settings.max_new_apkgs_per_lang_per_day


# ---- main per-video pipeline ----------------------------------------------

async def process_video(video: dict) -> None:
    settings = get_settings()
    youtube_id = video["youtube_id"]
    lang = video["lang"]
    title = video["title"] or youtube_id

    log.info("worker.processing", id=video["id"], yt=youtube_id, lang=lang,
             title=title[:60])

    work_root = Path(tempfile.gettempdir()) / "idiomatic" / youtube_id
    work_root.mkdir(parents=True, exist_ok=True)
    try:
        # 1. Download audio via Oxylabs → R2 (returns .m4a; Gemini + ffmpeg
        # both accept it directly, no re-encode needed).
        source_audio = await _download_audio(youtube_id, work_root)

        # 2. Extract idiomatic phrases via Gemini 3.5 Flash audio understanding
        extracted = await extract_from_audio(
            source_audio, lang, n_target=settings.target_idioms_per_video,
        )
        if not extracted:
            await db.mark_video_status(video["id"], "skipped", "no idioms extracted")
            return

        # 3. Dedup vs existing expression library
        fresh = await _filter_fresh(extracted, lang)
        if not fresh:
            await db.mark_video_status(video["id"], "skipped", "all dedupes")
            return

        # 4. Enrich each fresh phrase (examples + structured explanation)
        narration_root = Path(settings.data_dir) / "narration"
        await connectives.ensure_cached(narration_root, voice_en="Kore")

        # Pre-create the silence cache files. silence_mp3() checks `exists()`
        # then ffmpegs to the path — racy under parallel idioms (two writers
        # produce a corrupt file, breaking the later -c copy concat with
        # ffmpeg exit code 183). Do them serially up front.
        for ms in (300, 700, 1200, 1500):
            audio_mod.silence_mp3(narration_root, ms)

        video_audio_dir = work_root / "audio"
        video_audio_dir.mkdir(parents=True, exist_ok=True)

        import time as _time
        sem = asyncio.Semaphore(settings.idiom_parallelism)

        async def _one(i: int, phrase) -> tuple | None:
            async with sem:
                t0 = _time.monotonic()
                log.info("worker.idiom.start", i=i, of=len(fresh),
                         phrase=phrase.text[:50])
                try:
                    en = await enrich_one(phrase.text, phrase.english, lang)
                    log.info("worker.idiom.enriched", i=i,
                             dt=round(_time.monotonic() - t0, 1))
                    front, back = await audio_mod.render_card_audio(
                        idx=i, enriched=en, lang=lang,
                        source_mp3=source_audio,
                        audio_start=phrase.audio_start, audio_end=phrase.audio_end,
                        video_audio_dir=video_audio_dir,
                        narration_root=narration_root,
                    )
                    log.info("worker.idiom.done", i=i,
                             dt=round(_time.monotonic() - t0, 1))
                    return (en, front, back)
                except Exception as e:
                    import traceback
                    log.warning("worker.idiom.failed",
                                 i=i, phrase=phrase.text[:40], err=repr(e),
                                 dt=round(_time.monotonic() - t0, 1),
                                 tb=traceback.format_exc()[-400:])
                    return None

        results = await asyncio.gather(
            *[_one(i, p) for i, p in enumerate(fresh, 1)]
        )
        enriched_tuples = [r for r in results if r is not None]

        if not enriched_tuples:
            await db.mark_video_status(video["id"], "failed",
                                        "all enrichments failed")
            return

        # 5. Build apkg
        slug = slugify(title)[:60] or youtube_id
        apkg_dir = Path(settings.data_dir) / "apkgs" / lang
        apkg_dir.mkdir(parents=True, exist_ok=True)
        apkg_filename = f"{lang}/{slug}-{youtube_id}.apkg"
        apkg_path = Path(settings.data_dir) / "apkgs" / apkg_filename

        build_apkg(
            out_path=apkg_path,
            deck_name=f"Idiomatic::{lang}::{title}",
            youtube_id=youtube_id,
            video_title=title,
            video_url=f"https://www.youtube.com/watch?v={youtube_id}",
            idioms=enriched_tuples,
            stage_dir=Path(settings.data_dir) / "media_stage",
        )

        # 6. Record + insert expressions
        pool = await db.get_pool()
        apkg_id = await pool.fetchval(
            """
            INSERT INTO apkgs (video_id, lang, filename, size_bytes, n_idioms)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            video["id"], lang, "apkgs/" + apkg_filename,
            apkg_path.stat().st_size, len(enriched_tuples),
        )
        log.info("worker.apkg_inserted", id=apkg_id, n=len(enriched_tuples))

        # Insert new expressions into the library (one row per fresh phrase
        # that actually made it into the deck)
        kept_phrases = [p for p, _, _ in enriched_tuples]
        ext_for_db = [
            {"text": e.phrase, "normalized": normalize(e.phrase),
             "english": e.english}
            for e in kept_phrases
        ]
        await db.insert_expressions(lang, video["id"], ext_for_db)

        await db.mark_video_status(video["id"], "done")
        log.info("worker.done", id=video["id"], n_idioms=len(enriched_tuples))

    finally:
        # Tidy local workdir; /data/apkgs stays.
        shutil.rmtree(work_root, ignore_errors=True)


# ---- the loop -------------------------------------------------------------

async def loop(once: bool = False) -> None:
    settings = get_settings()
    log.info("worker.start", once=once, poll=settings.worker_poll_interval_sec)
    try:
        while True:
            try:
                video = await db.claim_next_video()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Transient DB issue (schema not yet applied, connection
                # reset, etc.). Don't let it kill the unobserved task —
                # just log + back off and try again.
                log.warning("worker.claim_failed", err=str(e)[:200])
                await asyncio.sleep(settings.worker_poll_interval_sec)
                if once:
                    return
                continue
            if video is None:
                if once:
                    return
                await asyncio.sleep(settings.worker_poll_interval_sec)
                continue

            # Soft daily cap. If we're at the cap for this video's language,
            # release it back to queued and look for another.
            if not await _under_daily_cap(video["lang"]):
                log.info("worker.daily_cap_hit", lang=video["lang"])
                await db.mark_video_status(video["id"], "queued",
                                            f"cap hit; retry tomorrow")
                if once:
                    return
                # Avoid hot-spinning if every language is capped
                await asyncio.sleep(60)
                continue

            try:
                await process_video(video)
            except asyncio.CancelledError:
                # Lifespan shutdown — release the claim so another instance
                # can pick it up.
                await db.mark_video_status(video["id"], "queued", "shutdown")
                raise
            except Exception as e:
                log.exception("worker.failed", id=video["id"], err=str(e))
                await db.mark_video_status(video["id"], "failed", str(e)[:500])

            if once:
                return
    finally:
        if once:
            await db.close_pool()


# ---- standalone CLI for local testing -------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true",
                    help="Process one job and stop (or exit if queue empty)")
    args = ap.parse_args()

    structlog.configure(processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ])

    try:
        asyncio.run(loop(once=args.once))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
