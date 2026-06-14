"""Worker loop. Polls the videos queue, runs the pipeline, writes results.

M1 status: skeleton only. The `process_video` call is a stub. The pipeline
modules in ./pipeline/ are placeholders. M2 milestone: this function
actually processes one video end-to-end via Gemini 3.5 Flash + ffmpeg.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import structlog

from . import db
from .settings import get_settings

log = structlog.get_logger()


async def process_video(video: dict) -> None:
    """End-to-end pipeline for one video. STUB for M1."""
    log.info("worker.processing", id=video["id"], yt=video["youtube_id"])

    # TODO M2: implement the pipeline:
    #   1. yt-dlp download → /tmp/<yt_id>.mp3
    #   2. gemini.extract_idiomatic_phrases(audio, lang) → list with timestamps
    #   3. dedup.filter_against_library(extracted, lang) → fresh only
    #   4. explain.generate_structured_explanations(fresh)
    #   5. audio.slice_and_render(fresh, src_mp3) → per-card audio files
    #   6. apkg.build(fresh) → /data/<slug>.apkg
    #   7. db.insert_expressions(lang, video.id, fresh)
    #   8. db.insert_apkg(...) + email signed link

    await asyncio.sleep(0.1)
    await db.mark_video_status(video["id"], "skipped", "M1 stub — pipeline not implemented")


async def loop(once: bool = False) -> None:
    settings = get_settings()
    log.info("worker.start", once=once, poll=settings.worker_poll_interval_sec)
    try:
        while True:
            video = await db.claim_next_video()
            if video is None:
                if once:
                    log.info("worker.queue_empty_exiting")
                    return
                await asyncio.sleep(settings.worker_poll_interval_sec)
                continue

            try:
                await process_video(video)
            except Exception as e:
                log.exception("worker.failed", id=video["id"], err=str(e))
                await db.mark_video_status(video["id"], "failed", str(e)[:500])

            if once:
                return
    finally:
        await db.close_pool()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true",
                    help="Process one job (or exit if queue empty) and stop")
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
