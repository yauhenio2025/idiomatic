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


async def langs_at_daily_cap(cap: int) -> list[str]:
    """Languages that already shipped >= cap video apkgs today."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT lang FROM apkgs
        WHERE kind = 'video' AND created_at >= date_trunc('day', NOW())
        GROUP BY lang
        HAVING COUNT(*) >= $1
        """,
        cap,
    )
    return [r["lang"] for r in rows]


async def claim_next_video(exclude_langs: list[str] | None = None) -> dict[str, Any] | None:
    """Atomic claim of the next queued video.

    exclude_langs keeps capped languages out of the claim entirely —
    otherwise a capped video at the head of the global FIFO is claimed,
    requeued, and re-claimed every cycle, starving every other language
    behind it for the rest of the day.
    """
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        UPDATE videos
        SET status = 'processing', picked_at = NOW(), attempts = attempts + 1
        WHERE id = (
            SELECT id FROM videos
            WHERE (status = 'queued'
                   -- reaper: reclaim rows wedged in 'processing' by a
                   -- non-graceful death (OOM, hard deploy)
                   OR (status = 'processing'
                       AND picked_at < NOW() - INTERVAL '2 hours'))
              AND attempts < $1
              AND NOT (lang = ANY($2::text[]))
            ORDER BY first_seen
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        )
        RETURNING id, youtube_id, channel_id, lang, title, duration_sec, attempts
        """,
        get_settings().worker_max_attempts,
        exclude_langs or [],
    )
    return dict(row) if row else None


async def fail_exhausted_stale_processing(max_attempts: int) -> int:
    """Stale 'processing' rows that already burned all attempts can't be
    reclaimed by claim_next_video — mark them failed so they're visible
    instead of wedged forever. Returns number of rows failed."""
    pool = await get_pool()
    result = await pool.execute(
        """
        UPDATE videos
        SET status = 'failed', finished_at = NOW(),
            status_msg = 'worker died mid-processing; attempts exhausted'
        WHERE status = 'processing'
          AND picked_at < NOW() - INTERVAL '2 hours'
          AND attempts >= $1
        """,
        max_attempts,
    )
    return int(result.split()[-1])


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


async def set_video_duration(video_id: int, duration_sec: int) -> None:
    """Fill duration_sec once the worker has the audio (cron enqueues blind)."""
    pool = await get_pool()
    await pool.execute(
        "UPDATE videos SET duration_sec = $2 WHERE id = $1",
        video_id, duration_sec,
    )


async def requeue_for_retry(video_id: int, msg: str | None = None) -> None:
    """Release a video back to the queue KEEPING the attempt it just burned.
    Used for transient failures — the attempts < worker_max_attempts filter
    in claim_next_video bounds the retries."""
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE videos
        SET status = 'queued', status_msg = $2, picked_at = NULL
        WHERE id = $1
        """,
        video_id, msg,
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

async def existing_normalized_for_lang(lang: str,
                                        exclude_video_id: int | None = None,
                                        ) -> set[str]:
    """Normalized expressions already in the library.

    exclude_video_id leaves out expressions first seen in that video, so
    a crashed-and-retried video isn't dedup-trapped by its own previous
    attempt's inserts (which would mark it 'skipped' with the pool data
    never persisted)."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT normalized FROM expressions
        WHERE lang = $1 AND first_video_id IS DISTINCT FROM $2
        """,
        lang, exclude_video_id,
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
    structured: dict | None = None,
) -> int:
    """One row per enriched idiom in a video. Returns expression_idioms.id."""
    import json
    pool = await get_pool()
    return await pool.fetchval(
        """
        INSERT INTO expression_idioms
            (expression_id, video_id, lang, idiom_text, english_gloss,
             audio_idiom_tgt, audio_idiom_en,
             source_phrase_target, source_phrase_en, explanation_en,
             structured)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
        ON CONFLICT (expression_id, video_id) DO UPDATE SET
            idiom_text = EXCLUDED.idiom_text,
            english_gloss = EXCLUDED.english_gloss,
            audio_idiom_tgt = EXCLUDED.audio_idiom_tgt,
            audio_idiom_en = EXCLUDED.audio_idiom_en,
            source_phrase_target = EXCLUDED.source_phrase_target,
            source_phrase_en = EXCLUDED.source_phrase_en,
            explanation_en = EXCLUDED.explanation_en,
            structured = EXCLUDED.structured
        RETURNING id
        """,
        expression_id, video_id, lang, idiom_text, english_gloss,
        audio_idiom_tgt, audio_idiom_en,
        source_phrase_target, source_phrase_en, explanation_en,
        json.dumps(structured) if structured else None,
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
               i.structured,
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
    import json
    out = []
    for r in rows:
        d = dict(r)
        # asyncpg hands jsonb back as a string unless a codec is registered
        if isinstance(d.get("structured"), str):
            try:
                d["structured"] = json.loads(d["structured"])
            except ValueError:
                d["structured"] = None
        d["examples"] = by_idiom.get(r["id"], [])
        out.append(d)
    return out


# ---- pool rebuild debounce ---------------------------------------------------

async def pool_rebuilt_within(lang: str, minutes: int) -> bool:
    pool = await get_pool()
    return bool(await pool.fetchval(
        """
        SELECT EXISTS (
            SELECT 1 FROM pool_rebuild_state
            WHERE lang = $1
              AND last_rebuilt_at > NOW() - make_interval(mins => $2)
        )
        """,
        lang, minutes,
    ))


async def mark_pool_rebuilt(lang: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO pool_rebuild_state (lang, last_rebuilt_at)
        VALUES ($1, NOW())
        ON CONFLICT (lang) DO UPDATE SET last_rebuilt_at = NOW()
        """,
        lang,
    )


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
        ON CONFLICT (video_id) WHERE kind = 'video' DO UPDATE SET
            filename = EXCLUDED.filename,
            size_bytes = EXCLUDED.size_bytes,
            n_idioms = EXCLUDED.n_idioms
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
