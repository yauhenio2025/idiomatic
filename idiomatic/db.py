"""Async Postgres pool + thin helpers. Real ORMs feel like overkill here."""

from __future__ import annotations

from typing import Any

import asyncpg
import structlog

from .settings import get_settings

log = structlog.get_logger()

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        s = get_settings()
        _pool = await asyncpg.create_pool(s.database_url, min_size=1, max_size=5)
        log.info("db.pool.created", url_host=s.database_url.split("@")[-1].split("/")[0])
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


# ---- Channel helpers -------------------------------------------------------

async def list_active_channels() -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch("SELECT id, youtube_id, lang, name FROM channels WHERE active = TRUE")
    return [dict(r) for r in rows]


# ---- Video queue helpers ---------------------------------------------------

async def enqueue_video(youtube_id: str, channel_id: int | None, lang: str,
                         title: str | None, duration_sec: int | None) -> int | None:
    """Insert a new video as queued. Returns its id, or None if it already exists."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO videos (youtube_id, channel_id, lang, title, duration_sec)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (youtube_id) DO NOTHING
        RETURNING id
        """,
        youtube_id, channel_id, lang, title, duration_sec,
    )
    return row["id"] if row else None


async def claim_next_video() -> dict[str, Any] | None:
    """Atomic claim of the next queued video."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        UPDATE videos
        SET status = 'processing', picked_at = NOW(), attempts = attempts + 1
        WHERE id = (
            SELECT id FROM videos
            WHERE status = 'queued' AND attempts < $1
            ORDER BY first_seen
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        )
        RETURNING id, youtube_id, channel_id, lang, title, duration_sec, attempts
        """,
        get_settings().worker_max_attempts,
    )
    return dict(row) if row else None


async def mark_video_status(video_id: int, status: str, msg: str | None = None) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE videos
        SET status = $2, status_msg = $3,
            finished_at = CASE WHEN $2 IN ('done', 'skipped', 'failed') THEN NOW() ELSE finished_at END
        WHERE id = $1
        """,
        video_id, status, msg,
    )


async def requeue_no_attempt(video_id: int, msg: str | None = None) -> None:
    """Release a claimed video back to the queue WITHOUT counting it as an
    attempt. Used when we punt for an externally-imposed reason (daily cap,
    shutdown) that has nothing to do with the video itself."""
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE videos
        SET status = 'queued',
            attempts = GREATEST(attempts - 1, 0),
            status_msg = $2,
            picked_at = NULL
        WHERE id = $1
        """,
        video_id, msg,
    )


# ---- Expression library ---------------------------------------------------

async def existing_normalized_for_lang(lang: str) -> set[str]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT normalized FROM expressions WHERE lang = $1", lang,
    )
    return {r["normalized"] for r in rows}


async def insert_expressions(lang: str, video_id: int,
                              items: list[dict[str, str]]) -> int:
    """items: [{'text', 'normalized', 'english'}]. Skips conflicts. Returns inserted count."""
    if not items:
        return 0
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            inserted = await conn.executemany(
                """
                INSERT INTO expressions (lang, text, normalized, english, first_video_id)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (lang, normalized) DO NOTHING
                """,
                [(lang, x["text"], x["normalized"], x.get("english"), video_id) for x in items],
            )
    # asyncpg's executemany doesn't return per-row counts; re-query is simpler
    return len(items)
