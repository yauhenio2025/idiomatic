"""Cron entrypoint — polled by Render every 2h.

Walks every active channel, fetches its RSS, pre-filters unseen videos
by duration via the official Data API (no bot wall, ~5 quota units per
walk), and enqueues only in-window ones. Out-of-window videos are stored
as 'skipped' rows so later walks treat them as known. If the API key is
missing or errors, videos are enqueued blind and the worker's
post-download ffprobe gate filters instead (at the cost of one Oxylabs
job per rejected video).
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

import structlog

from . import db
from .settings import get_settings
from .youtube import fetch_durations, fetch_recent

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


async def expire_stale_queued() -> int:
    """Freshness-first queue policy: a queued video that waited longer
    than queue_expiry_days is news that went stale — expire it instead of
    letting the backlog grow forever (inflow outruns the daily build
    caps). Priority/curated channels never expire."""
    settings = get_settings()
    if not settings.queue_expiry_days:
        return 0
    pool = await db.get_pool()
    result = await pool.execute(
        """
        UPDATE videos v SET status = 'skipped',
            status_msg = 'expired: queued longer than ' || $1 || ' days',
            finished_at = NOW()
        FROM (
            SELECT v2.id FROM videos v2
            LEFT JOIN channels c ON c.id = v2.channel_id
            WHERE v2.status = 'queued'
              AND v2.first_seen < NOW() - make_interval(days => $1)
              AND COALESCE(c.priority, 0) < 10
              AND COALESCE(c.name, '') NOT LIKE 'Curated ·%'
        ) stale
        WHERE v.id = stale.id
        """,
        settings.queue_expiry_days,
    )
    return int(result.split()[-1])


async def run() -> None:
    settings = get_settings()
    channels = await db.list_active_channels()
    log.info("cron.start", n_channels=len(channels))

    try:
        n_expired = await expire_stale_queued()
        if n_expired:
            log.info("cron.expired_stale", n=n_expired,
                     days=settings.queue_expiry_days)
    except Exception as e:
        log.warning("cron.expiry_failed", err=repr(e)[:200])

    # Phase 1 — RSS walk. YouTube's feed endpoint load-sheds when hit
    # back-to-back; 1.5s between channels keeps the hit-rate near 100%.
    candidates: list[tuple] = []          # (FeedEntry, channel row)
    for i, ch in enumerate(channels):
        if i > 0:
            await asyncio.sleep(1.5)
        try:
            entries = await fetch_recent(ch["youtube_id"], limit=10)
        except Exception as e:
            log.warning("cron.rss_failed", channel=ch["youtube_id"],
                         err=str(e)[:200])
            continue
        # Per-channel title filter (case-insensitive regex) — e.g. only
        # 'caracciolo' videos from a general talk-show channel.
        flt = ch.get("title_filter")
        if flt:
            rx = re.compile(flt, re.IGNORECASE)
            # Match against title OR description: e.g. full Otto e mezzo
            # episodes carry Caracciolo's name only in the description.
            entries = [e for e in entries
                       if rx.search((e.title or "") + " "
                                    + (e.description or ""))]
        candidates.extend((e, ch) for e in entries)

    # Phase 2 — drop videos we already have a row for (one DB round-trip),
    # plus in-walk duplicates (the same video can appear in two feeds).
    known = await db.existing_youtube_ids(
        [e.youtube_id for e, _ in candidates])
    seen_in_walk: set[str] = set()
    fresh: list[tuple] = []
    for e, ch in candidates:
        if e.youtube_id in known or e.youtube_id in seen_in_walk:
            continue
        seen_in_walk.add(e.youtube_id)
        fresh.append((e, ch))

    # Phase 3 — duration pre-filter via the official Data API (cheap:
    # 1 quota unit per 50 ids). On ANY API problem we fall back to blind
    # enqueueing — the worker's post-download ffprobe gate still filters,
    # it just costs an Oxylabs job per out-of-window video.
    durations: dict[str, int] = {}
    if settings.youtube_api_key and fresh:
        try:
            durations = await fetch_durations(
                [e.youtube_id for e, _ in fresh], settings.youtube_api_key)
        except Exception as e:
            log.warning("cron.duration_api_failed", err=str(e)[:200])

    enqueued = pre_skipped = 0
    for e, ch in fresh:
        dur = durations.get(e.youtube_id)
        lo = ch.get("min_duration_sec") or settings.min_duration_sec
        hi = ch.get("max_duration_sec") or settings.max_duration_sec
        in_window = dur is None or lo <= dur <= hi
        if not in_window:
            await db.enqueue_video(
                youtube_id=e.youtube_id, channel_id=ch["id"],
                lang=ch["lang"], title=e.title, duration_sec=dur,
                status="skipped",
                status_msg=(f"duration {dur}s outside "
                            f"[{lo}, {hi}] (cron pre-filter)"),
            )
            pre_skipped += 1
            continue
        vid = await db.enqueue_video(
            youtube_id=e.youtube_id, channel_id=ch["id"],
            lang=ch["lang"], title=e.title, duration_sec=dur,
        )
        if vid is not None:
            enqueued += 1
            log.info("cron.enqueued", id=vid, yt=e.youtube_id,
                      lang=ch["lang"], dur=dur, title=e.title[:60])

    log.info("cron.done", enqueued=enqueued, pre_skipped=pre_skipped,
             skipped_known=len(candidates) - len(fresh))

    try:
        await cleanup_delivered_apkgs()
    except Exception as e:
        log.warning("cron.cleanup_failed", err=repr(e)[:200])

    await db.close_pool()


if __name__ == "__main__":
    asyncio.run(run())
