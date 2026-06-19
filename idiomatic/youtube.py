"""YouTube channel RSS polling. No API key required."""

from __future__ import annotations

import re
from dataclasses import dataclass

import feedparser
import httpx
import structlog

log = structlog.get_logger()

RSS_TMPL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
DURATION_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


@dataclass(slots=True)
class FeedEntry:
    youtube_id: str
    title: str
    published: str  # ISO timestamp
    # NB: feed doesn't include duration. We fetch that on enqueue via yt-dlp.


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


_LEN_RE = re.compile(r'"lengthSeconds":"(\d+)"')
_TITLE_RE = re.compile(r'<meta property="og:title" content="([^"]*)"')
_CHANNEL_RE = re.compile(r'"author":"([^"]+)"')


async def fetch_metadata(youtube_id: str) -> dict:
    """Scrape duration + title from the YouTube watch page HTML.

    No auth, no yt-dlp, no bot wall — the public watch page embeds enough
    JSON for our needs (`"lengthSeconds":"…"` and og:title meta). Used by
    the cron at enqueue time to filter by duration window.
    """
    url = f"https://www.youtube.com/watch?v={youtube_id}"
    async with httpx.AsyncClient(timeout=20, follow_redirects=True,
                                  headers={"User-Agent": "Mozilla/5.0"}) as client:
        r = await client.get(url)
        r.raise_for_status()
    html = r.text
    len_m = _LEN_RE.search(html)
    title_m = _TITLE_RE.search(html)
    chan_m = _CHANNEL_RE.search(html)
    if not len_m:
        raise RuntimeError(f"no lengthSeconds in watch page for {youtube_id}")
    return {
        "youtube_id": youtube_id,
        "title": (title_m.group(1) if title_m else youtube_id),
        "duration_sec": int(len_m.group(1)),
        "channel_name": (chan_m.group(1) if chan_m else None),
    }
