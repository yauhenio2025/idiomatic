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


# ---- Pool-deck source data (per-idiom + per-example) -----------------------

async def insert_idiom_record(
    *, expression_id: int, video_id: int, lang: str,
    idiom_text: str, english_gloss: str,
    audio_idiom_tgt: str | None, audio_idiom_en: str | None,
    source_phrase_target: str | None = None,
    source_phrase_en: str | None = None,
    explanation_en: str | None = None,
) -> int:
    """One row per enriched idiom in a video. Returns expression_idioms.id."""
    pool = await get_pool()
    return await pool.fetchval(
        """
        INSERT INTO expression_idioms
            (expression_id, video_id, lang, idiom_text, english_gloss,
             audio_idiom_tgt, audio_idiom_en,
             source_phrase_target, source_phrase_en, explanation_en)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id
        """,
        expression_id, video_id, lang, idiom_text, english_gloss,
        audio_idiom_tgt, audio_idiom_en,
        source_phrase_target, source_phrase_en, explanation_en,
    )


async def insert_examples(idiom_id: int, examples: list[dict]) -> None:
    """examples: ord-indexed dicts with en_text/target_text/audio_en/audio_target."""
    if not examples:
        return
    pool = await get_pool()
    rows = [
        (idiom_id, ex["ord"], ex["en_text"], ex["target_text"],
         ex.get("audio_en"), ex.get("audio_target"))
        for ex in examples
    ]
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO expression_examples
                    (idiom_id, ord, en_text, target_text, audio_en, audio_target)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (idiom_id, ord) DO NOTHING
                """,
                rows,
            )


async def get_expression_id(lang: str, normalized: str) -> int | None:
    pool = await get_pool()
    return await pool.fetchval(
        "SELECT id FROM expressions WHERE lang = $1 AND normalized = $2",
        lang, normalized,
    )


async def fetch_pool_idioms(lang: str) -> list[dict]:
    """All idiom records for a language, with their examples nested."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT i.id, i.idiom_text, i.english_gloss,
               i.audio_idiom_tgt, i.audio_idiom_en,
               i.source_phrase_target, i.source_phrase_en, i.explanation_en,
               v.youtube_id, v.title AS video_title
        FROM expression_idioms i
        LEFT JOIN videos v ON v.id = i.video_id
        WHERE i.lang = $1
        ORDER BY i.id
        """,
        lang,
    )
    idiom_ids = [r["id"] for r in rows]
    examples = await pool.fetch(
        """
        SELECT idiom_id, ord, en_text, target_text, audio_en, audio_target
        FROM expression_examples
        WHERE idiom_id = ANY($1::bigint[])
        ORDER BY idiom_id, ord
        """,
        idiom_ids,
    )
    by_idiom: dict[int, list[dict]] = {i: [] for i in idiom_ids}
    for ex in examples:
        by_idiom[ex["idiom_id"]].append(dict(ex))
    out = []
    for r in rows:
        d = dict(r)
        d["examples"] = by_idiom.get(r["id"], [])
        out.append(d)
    return out


# ---- apkgs upsert helpers --------------------------------------------------

async def insert_video_apkg(
    *, video_id: int, lang: str, filename: str,
    size_bytes: int, n_idioms: int,
) -> int:
    pool = await get_pool()
    return await pool.fetchval(
        """
        INSERT INTO apkgs (video_id, lang, filename, size_bytes, n_idioms, kind)
        VALUES ($1, $2, $3, $4, $5, 'video')
        RETURNING id
        """,
        video_id, lang, filename, size_bytes, n_idioms,
    )


async def upsert_pool_apkg(
    *, lang: str, kind: str, filename: str,
    size_bytes: int, n_idioms: int,
) -> int:
    """Replace the existing pool apkg for (lang, kind). Old row is deleted
    (cascade-deletes agent_acks) so agents re-pull the new version."""
    assert kind in ("pool_idioms", "pool_expr", "pool_idiom_t2e", "pool_idiom_e2t")
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM apkgs WHERE lang = $1 AND kind = $2",
                lang, kind,
            )
            return await conn.fetchval(
                """
                INSERT INTO apkgs (video_id, lang, filename, size_bytes, n_idioms, kind)
                VALUES (NULL, $1, $2, $3, $4, $5)
                RETURNING id
                """,
                lang, filename, size_bytes, n_idioms, kind,
            )
