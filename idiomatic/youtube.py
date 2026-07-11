"""YouTube channel RSS polling. No API key required.

Duration is NOT available in RSS and is no longer fetched here — scraping
the watch page for it tripped YouTube's bot wall from datacenter IPs. The
worker checks duration after Oxylabs delivers the audio (job-status
duration_sec, ffprobe fallback) and marks out-of-window videos 'skipped'.
"""

from __future__ import annotations

from dataclasses import dataclass

import feedparser
import httpx
import structlog

log = structlog.get_logger()

RSS_TMPL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


@dataclass(slots=True)
class FeedEntry:
    youtube_id: str
    title: str
    published: str  # ISO timestamp


async def fetch_recent(channel_id: str, limit: int = 15) -> list[FeedEntry]:
    """Return the most recent N video entries for a channel."""
    url = RSS_TMPL.format(channel_id=channel_id)
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url)
        r.raise_for_status()
    parsed = feedparser.parse(r.text)
    out: list[FeedEntry] = []
    for entry in parsed.entries[:limit]:
        ytid = entry.get("yt_videoid") or entry.get("id", "").split(":")[-1]
        if not ytid:
            continue
        out.append(FeedEntry(
            youtube_id=ytid,
            title=entry.get("title", ""),
            published=entry.get("published", ""),
        ))
    return out
