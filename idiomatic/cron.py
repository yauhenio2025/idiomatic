"""Cron entrypoint — polled by Render every 2h.

Walks every active channel, fetches its RSS, enqueues every unseen video.
No per-video watch-page fetches: those tripped YouTube's bot wall. The
duration window is enforced by the worker after the audio download (see
worker._check_duration), where the length is known for free.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

from . import db
from .settings import get_settings
from .youtube import fetch_recent

log = structlog.get_logger()


async def cleanup_delivered_apkgs() -> None:
    """Delete video apkg FILES that are past retention and fully delivered
    (ok-acked by every subscribed agent). The DB row stays — a download of
    a reaped file returns 410. Keeps the 10 GB /data disk from filling
    (~12 MB per video apkg, forever, before this)."""
    settings = get_settings()
    eligible = await db.video_apkgs_eligible_for_cleanup(
        settings.apkg_retention_days)
    n = freed = 0
    for row in eligible:
        path = Path(settings.data_dir) / row["filename"]
        if path.exists():
            size = path.stat().st_size
            try:
                path.unlink()
            except OSError as e:
                log.warning("cron.cleanup_unlink_failed",
                             file=row["filename"], err=str(e)[:100])
                continue
            n += 1
            freed += size
    if n:
        log.info("cron.cleanup", n_files=n, freed_mb=round(freed / 1e6, 1))


async def run() -> None:
    channels = await db.list_active_channels()
    log.info("cron.start", n_channels=len(channels))

    enqueued = skipped_known = 0
    for i, ch in enumerate(channels):
        # YouTube's RSS feed rate-limits / load-sheds when hit back-to-back.
        # 1.5s between channels makes a 24-channel walk take ~36s instead of
        # ~5s, but our hit-rate jumps from ~60% to near-100%.
        if i > 0:
            await asyncio.sleep(1.5)
        try:
            entries = await fetch_recent(ch["youtube_id"], limit=10)
        except Exception as e:
            log.warning("cron.rss_failed", channel=ch["youtube_id"],
                         err=str(e)[:200])
            continue

        for e in entries:
            vid = await db.enqueue_video(
                youtube_id=e.youtube_id,
                channel_id=ch["id"],
                lang=ch["lang"],
                title=e.title,
                duration_sec=None,  # unknown until the worker downloads it
            )
            if vid is None:
                skipped_known += 1
            else:
                enqueued += 1
                log.info("cron.enqueued", id=vid, yt=e.youtube_id,
                          lang=ch["lang"], title=e.title[:60])

    log.info("cron.done", enqueued=enqueued, skipped_known=skipped_known)

    try:
        await cleanup_delivered_apkgs()
    except Exception as e:
        log.warning("cron.cleanup_failed", err=repr(e)[:200])

    await db.close_pool()


if __name__ == "__main__":
    asyncio.run(run())
