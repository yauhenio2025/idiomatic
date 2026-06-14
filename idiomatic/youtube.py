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


async def fetch_metadata(youtube_id: str) -> dict:
    """Use yt-dlp --dump-json (subprocess) to get duration + accurate title.

    Defer to a subprocess for stability; the youtube_dl/yt-dlp internal API
    drifts between releases.
    """
    import asyncio, json, shutil
    yt_dlp = shutil.which("yt-dlp") or "yt-dlp"
    proc = await asyncio.create_subprocess_exec(
        yt_dlp, "--dump-json", "--skip-download",
        f"https://www.youtube.com/watch?v={youtube_id}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp metadata failed for {youtube_id}: {stderr.decode()[:200]}")
    meta = json.loads(stdout.decode())
    return {
        "youtube_id": youtube_id,
        "title": meta.get("title"),
        "duration_sec": int(meta.get("duration") or 0),
        "channel_name": meta.get("uploader"),
    }
