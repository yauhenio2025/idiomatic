"""Cron entrypoint — polled by Render every 2h.

Walks every active channel, fetches its RSS, enqueues unseen videos that
fall inside the duration window. Duration is checked lazily via yt-dlp
because RSS doesn't include it.
"""

from __future__ import annotations

import asyncio

import structlog

from . import db
from .settings import get_settings
from .youtube import fetch_metadata, fetch_recent

log = structlog.get_logger()


async def run() -> None:
    settings = get_settings()
    channels = await db.list_active_channels()
    log.info("cron.start", n_channels=len(channels))

    enqueued = skipped_dur = skipped_known = 0
    for i, ch in enumerate(channels):
        # YouTube's RSS feed rate-limits / load-sheds when hit back-to-back.
        # 1.5s between channels makes a 24-channel walk take ~36s instead of
        # ~5s, but our hit-rate jumps from ~60% to near-100%.
        if i > 0:
            await asyncio.sleep(1.5)
        try:
            entries = await fetch_recent(ch["youtube_id"], limit=15)
        except Exception as e:
            log.warning("cron.rss_failed", channel=ch["youtube_id"], err=str(e)[:200])
            continue

        for e in entries:
            try:
                meta = await fetch_metadata(e.youtube_id)
            except Exception as ex:
                log.warning("cron.meta_failed", yt=e.youtube_id, err=str(ex))
                continue

            dur = meta["duration_sec"]
            if dur < settings.min_duration_sec or dur > settings.max_duration_sec:
                skipped_dur += 1
                continue

            vid = await db.enqueue_video(
                youtube_id=e.youtube_id,
                channel_id=ch["id"],
                lang=ch["lang"],
                title=meta["title"],
                duration_sec=dur,
            )
            if vid is None:
                skipped_known += 1
            else:
                enqueued += 1
                log.info("cron.enqueued", id=vid, yt=e.youtube_id, lang=ch["lang"],
                         dur=dur, title=meta["title"][:60])

    log.info("cron.done", enqueued=enqueued, skipped_duration=skipped_dur,
             skipped_known=skipped_known)
    await db.close_pool()


if __name__ == "__main__":
    asyncio.run(run())
