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


_LEN_RE = re.compile(rb'"lengthSeconds":"(\d+)"')
_TITLE_RE = re.compile(rb'<meta property="og:title" content="([^"]*)"')
_CHANNEL_RE = re.compile(rb'"author":"([^"]+)"')

# Absolute ceiling per page. lengthSeconds typically sits ~670 KB in;
# 1 MB gives slack without unbounding. 240 calls × 1 MB = ~240 MB worst
# case if we never exit early — but the streaming search below DOES exit
# early as soon as all three fields are found, which is usually around
# 700-800 KB.
_PAGE_BYTE_CEILING = 1_048_576


async def fetch_metadata(youtube_id: str,
                         client: httpx.AsyncClient | None = None) -> dict:
    """Scrape duration + title from the YouTube watch page HTML.

    Streams chunks and runs the regexes incrementally — drops the request
    as soon as all three fields are found, instead of buffering the whole
    1-2 MB page. Keeps the cron's per-walk memory well under 512 MB.

    Pass a shared httpx.AsyncClient to reuse the connection pool.
    """
    url = f"https://www.youtube.com/watch?v={youtube_id}"
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=20, follow_redirects=True,
                                    headers={"User-Agent": "Mozilla/5.0"})

    duration_sec: int | None = None
    title: str | None = None
    channel_name: str | None = None
    try:
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            tail = b""  # overlap so a marker straddling a chunk boundary still hits
            seen = 0
            async for chunk in r.aiter_bytes(chunk_size=65_536):
                buf = tail + chunk
                if duration_sec is None:
                    m = _LEN_RE.search(buf)
                    if m:
                        duration_sec = int(m.group(1))
                if title is None:
                    m = _TITLE_RE.search(buf)
                    if m:
                        title = m.group(1).decode(errors="replace")
                if channel_name is None:
                    m = _CHANNEL_RE.search(buf)
                    if m:
                        channel_name = m.group(1).decode(errors="replace")
                if duration_sec is not None and title is not None:
                    break  # got the must-haves; channel_name is optional
                # Keep the last 256 bytes so a regex match spanning a chunk
                # boundary isn't missed.
                tail = buf[-256:]
                seen += len(chunk)
                if seen >= _PAGE_BYTE_CEILING:
                    break
    finally:
        if own_client:
            await client.aclose()

    if duration_sec is None:
        raise RuntimeError(f"no lengthSeconds within {_PAGE_BYTE_CEILING}B "
                           f"for {youtube_id}")
    return {
        "youtube_id": youtube_id,
        "title": title or youtube_id,
        "duration_sec": duration_sec,
        "channel_name": channel_name,
    }
