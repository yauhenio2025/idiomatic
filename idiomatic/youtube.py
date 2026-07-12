"""YouTube channel RSS polling + Data API v3 duration lookup.

RSS (no key needed) lists a channel's recent videos but carries no
duration. Durations come from the official Data API v3 videos.list
endpoint (`fetch_durations`) — 1 quota unit per call of up to 50 ids,
no bot wall, unlike the watch-page scraping that got the Render IP
blocked in June. If no API key is configured the cron enqueues blind
and the worker's post-download ffprobe gate does the filtering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import feedparser
import httpx
import structlog

log = structlog.get_logger()

RSS_TMPL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
_API_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

# ISO 8601 duration as YouTube emits it: PT#H#M#S (P#D only for >24h edge
# cases; live streams can return P0D which parses to 0).
_ISO_DUR_RE = re.compile(
    r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$"
)


@dataclass(slots=True)
class FeedEntry:
    youtube_id: str
    title: str
    published: str  # ISO timestamp


def parse_iso8601_duration(s: str) -> int | None:
    """'PT12M42S' → 762. Returns None on anything unparseable."""
    m = _ISO_DUR_RE.match(s or "")
    if not m:
        return None
    d, h, mi, sec = (int(g) if g else 0 for g in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + sec


async def fetch_durations(video_ids: list[str],
                           api_key: str) -> dict[str, int]:
    """Batch-resolve durations via the Data API (50 ids per request).

    Returns {youtube_id: seconds}. Ids missing from the result are
    deleted/private/unavailable videos — callers should treat absence as
    'unknown', not 'zero'. Raises httpx.HTTPStatusError on quota/auth
    problems so the caller can fall back to blind enqueueing.
    """
    out: dict[str, int] = {}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(_API_VIDEOS_URL, params={
                "part": "contentDetails",
                "id": ",".join(chunk),
                "key": api_key,
                "maxResults": 50,
            })
        r.raise_for_status()
        for item in r.json().get("items", []):
            sec = parse_iso8601_duration(
                (item.get("contentDetails") or {}).get("duration", ""))
            if sec is not None:
                out[item["id"]] = sec
    return out


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
