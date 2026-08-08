"""Async Postgres pool + thin helpers. Real ORMs feel like overkill here."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import json
import secrets
import time

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


async def apply_schema() -> None:
    """Execute db/schema.sql (fully idempotent — IF NOT EXISTS everywhere).

    Called from the API lifespan at boot so new tables/columns exist before
    the worker loop starts. Replaces manual psql migrations: prod DB
    credentials never leave Render."""
    from pathlib import Path
    schema_path = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(sql)
    log.info("db.schema_applied", path=str(schema_path))


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


# ---- Legacy-estate audit ---------------------------------------------------

async def seed_legacy_estate(
    rows: list[dict[str, Any]], *, source_sha256: str, audited_at: datetime,
) -> None:
    """Idempotently seed audit-owned columns while preserving owner verdicts.

    The manifest is committed, but the owner gate happens later and writes to
    Postgres.  Consequently the conflict update intentionally excludes
    ``owner_verdict`` and ``owner_note``.
    """

    def _dt(value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("legacy estate review timestamps must include timezone")
        return parsed

    values = [
        (
            row["deck_path"],
            row["source_deck_id"],
            row["parent_path"],
            row["depth"],
            row["top_level"],
            row["lang"],
            row["direct_notes"],
            row["direct_cards"],
            row["direct_mature"],
            row["direct_reps"],
            row["direct_reviews"],
            row["direct_audio_notes"],
            row["direct_sound_tags"],
            _dt(row["direct_last_review"]),
            row["subtree_notes"],
            row["subtree_cards"],
            row["subtree_mature"],
            row["subtree_reps"],
            row["subtree_reviews"],
            row["subtree_audio_notes"],
            row["subtree_sound_tags"],
            _dt(row["subtree_last_review"]),
            json.dumps(row["note_models"], ensure_ascii=False),
            json.dumps(row["quality_flags"], ensure_ascii=False),
            json.dumps(row["overlap"], ensure_ascii=False),
            row["proposed_verdict"],
            row["proposal_reason"],
            source_sha256,
            audited_at,
        )
        for row in rows
    ]
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO legacy_estate (
                  deck_path, source_deck_id, parent_path, depth, top_level, lang,
                  direct_notes, direct_cards, direct_mature, direct_reps,
                  direct_reviews, direct_audio_notes, direct_sound_tags,
                  direct_last_review,
                  subtree_notes, subtree_cards, subtree_mature, subtree_reps,
                  subtree_reviews, subtree_audio_notes, subtree_sound_tags,
                  subtree_last_review,
                  note_models, quality_flags, overlap,
                  proposed_verdict, proposal_reason, source_sha256, audited_at
                ) VALUES (
                  $1, $2, $3, $4, $5, $6,
                  $7, $8, $9, $10, $11, $12, $13, $14,
                  $15, $16, $17, $18, $19, $20, $21, $22,
                  $23::jsonb, $24::jsonb, $25::jsonb,
                  $26, $27, $28, $29
                )
                ON CONFLICT (deck_path) DO UPDATE SET
                  source_deck_id = EXCLUDED.source_deck_id,
                  parent_path = EXCLUDED.parent_path,
                  depth = EXCLUDED.depth,
                  top_level = EXCLUDED.top_level,
                  lang = EXCLUDED.lang,
                  direct_notes = EXCLUDED.direct_notes,
                  direct_cards = EXCLUDED.direct_cards,
                  direct_mature = EXCLUDED.direct_mature,
                  direct_reps = EXCLUDED.direct_reps,
                  direct_reviews = EXCLUDED.direct_reviews,
                  direct_audio_notes = EXCLUDED.direct_audio_notes,
                  direct_sound_tags = EXCLUDED.direct_sound_tags,
                  direct_last_review = EXCLUDED.direct_last_review,
                  subtree_notes = EXCLUDED.subtree_notes,
                  subtree_cards = EXCLUDED.subtree_cards,
                  subtree_mature = EXCLUDED.subtree_mature,
                  subtree_reps = EXCLUDED.subtree_reps,
                  subtree_reviews = EXCLUDED.subtree_reviews,
                  subtree_audio_notes = EXCLUDED.subtree_audio_notes,
                  subtree_sound_tags = EXCLUDED.subtree_sound_tags,
                  subtree_last_review = EXCLUDED.subtree_last_review,
                  note_models = EXCLUDED.note_models,
                  quality_flags = EXCLUDED.quality_flags,
                  overlap = EXCLUDED.overlap,
                  proposed_verdict = EXCLUDED.proposed_verdict,
                  proposal_reason = EXCLUDED.proposal_reason,
                  source_sha256 = EXCLUDED.source_sha256,
                  audited_at = EXCLUDED.audited_at,
                  seeded_at = NOW()
                """,
                values,
            )


# ---- Channel helpers -------------------------------------------------------

async def list_active_channels() -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT id, youtube_id, lang, name, title_filter,
                  min_duration_sec, max_duration_sec
           FROM channels WHERE active = TRUE""")
    return [dict(r) for r in rows]


# ---- Video queue helpers ---------------------------------------------------

async def enqueue_video(youtube_id: str, channel_id: int | None, lang: str,
                         title: str | None, duration_sec: int | None,
                         status: str = "queued",
                         status_msg: str | None = None) -> int | None:
    """Insert a new video row. Returns its id, or None if it already exists.

    status defaults to 'queued'; the cron's duration pre-filter inserts
    out-of-window videos directly as 'skipped' so they're never claimed
    (and never re-checked on later walks — the row makes them "known")."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO videos (youtube_id, channel_id, lang, title, duration_sec,
                            status, status_msg)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (youtube_id) DO NOTHING
        RETURNING id
        """,
        youtube_id, channel_id, lang, title, duration_sec, status, status_msg,
    )
    return row["id"] if row else None


async def existing_youtube_ids(ids: list[str]) -> set[str]:
    """Which of these youtube_ids already have a videos row (any status)."""
    if not ids:
        return set()
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT youtube_id FROM videos WHERE youtube_id = ANY($1::text[])",
        ids,
    )
    return {r["youtube_id"] for r in rows}


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
            SELECT v.id FROM videos v
            LEFT JOIN channels c ON c.id = v.channel_id
            WHERE (v.status = 'queued'
                   -- reaper: reclaim rows wedged in 'processing' by a
                   -- non-graceful death (OOM, hard deploy)
                   OR (v.status = 'processing'
                       AND v.picked_at < NOW() - INTERVAL '2 hours'))
              AND v.attempts < $1
              -- capped languages are excluded, EXCEPT priority channels
              -- (e.g. Caracciolo sources) which bypass the daily cap
              AND (NOT (v.lang = ANY($2::text[]))
                   OR COALESCE(c.priority, 0) >= 10)
            -- newest-first: decks track fresh news at ~0 lag; the queue
            -- expiry reaps the old tail instead of the worker chasing it
            ORDER BY COALESCE(c.priority, 0) DESC, v.first_seen DESC
            FOR UPDATE OF v SKIP LOCKED
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
            await conn.executemany(
                """
                INSERT INTO expressions (lang, text, normalized, english, first_video_id)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (lang, normalized) DO NOTHING
                """,
                [(lang, x["text"], x["normalized"], x.get("english"), video_id) for x in items],
            )
    # asyncpg's executemany doesn't return per-row counts; re-query is simpler
    return len(items)


async def expression_ids_by_normalized(lang: str,
                                         normalized: list[str],
                                         ) -> dict[str, int]:
    """normalized → expressions.id map for the given language."""
    if not normalized:
        return {}
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, normalized FROM expressions
        WHERE lang = $1 AND normalized = ANY($2::text[])
        """,
        lang, normalized,
    )
    return {r["normalized"]: r["id"] for r in rows}


async def log_extractions(video_id: int, lang: str,
                           entries: list[dict]) -> None:
    """entries: [{'phrase','normalized','english','verdict','duplicate_of'}].
    Upserts on (video_id, normalized) so a retried video refreshes its own
    rows instead of duplicating them."""
    if not entries:
        return
    pool = await get_pool()
    rows = [
        (video_id, lang, e["phrase"], e["normalized"], e.get("english"),
         e["verdict"], e.get("duplicate_of"))
        for e in entries
    ]
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO extraction_log
                    (video_id, lang, phrase, normalized, english,
                     verdict, duplicate_of)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (video_id, normalized) DO UPDATE SET
                    english = EXCLUDED.english,
                    verdict = EXCLUDED.verdict,
                    duplicate_of = EXCLUDED.duplicate_of,
                    created_at = NOW()
                """,
                rows,
            )


async def set_processing_seconds(video_id: int, seconds: int) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE videos SET processing_seconds = $2 WHERE id = $1",
        video_id, seconds,
    )


# ---- Pool-deck source data (per-idiom + per-example) -----------------------

async def insert_idiom_record(
    *, expression_id: int, video_id: int, lang: str,
    idiom_text: str, english_gloss: str,
    audio_idiom_tgt: str | None, audio_idiom_en: str | None,
    source_phrase_target: str | None = None,
    source_phrase_en: str | None = None,
    explanation_en: str | None = None,
    structured: dict | None = None,
    audio_explanation: str | None = None,
    audio_context: str | None = None,
    citation_form: str | None = None,
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
             structured, audio_explanation, audio_context, citation_form)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12, $13, $14)
        ON CONFLICT (expression_id, video_id) DO UPDATE SET
            idiom_text = EXCLUDED.idiom_text,
            english_gloss = EXCLUDED.english_gloss,
            audio_idiom_tgt = EXCLUDED.audio_idiom_tgt,
            audio_idiom_en = EXCLUDED.audio_idiom_en,
            source_phrase_target = EXCLUDED.source_phrase_target,
            source_phrase_en = EXCLUDED.source_phrase_en,
            explanation_en = EXCLUDED.explanation_en,
            structured = EXCLUDED.structured,
            audio_explanation = EXCLUDED.audio_explanation,
            audio_context = EXCLUDED.audio_context,
            citation_form = COALESCE(EXCLUDED.citation_form,
                                     expression_idioms.citation_form)
        RETURNING id
        """,
        expression_id, video_id, lang, idiom_text, english_gloss,
        audio_idiom_tgt, audio_idiom_en,
        source_phrase_target, source_phrase_en, explanation_en,
        json.dumps(structured) if structured else None,
        audio_explanation,
        audio_context,
        citation_form,
    )


async def set_idiom_explanation_audio(idiom_id: int, rel_path: str) -> None:
    """Record a TTS-on-miss explanation audio produced during a pool rebuild."""
    pool = await get_pool()
    await pool.execute(
        "UPDATE expression_idioms SET audio_explanation = $2 WHERE id = $1",
        idiom_id, rel_path,
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
               i.audio_idiom_tgt, i.audio_idiom_en, i.audio_explanation,
               i.audio_context, i.citation_form,
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


async def kv_get(key: str) -> str | None:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT value FROM kv_store WHERE key = $1", key)
    return row["value"] if row else None


async def kv_set(key: str, value: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO kv_store (key, value) VALUES ($1, $2)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value,
                                        updated_at = NOW()
        """, key, value)


async def kv_claim_interval(key: str, interval_seconds: int) -> bool:
    """Atomically stamp `key` with the current epoch and report whether the
    caller won the slot: True iff the previous stamp was absent, garbled, or
    older than `interval_seconds`. Concurrent callers serialize on the row —
    the upsert's WHERE re-checks against the winner's committed value, so
    exactly one of an overlapping pair proceeds (the rescue-autopilot
    double-run fix)."""
    pool = await get_pool()
    now = int(time.time())
    row = await pool.fetchrow(
        """
        INSERT INTO kv_store (key, value) VALUES ($1, $2)
        ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = NOW()
            WHERE CASE WHEN kv_store.value ~ '^[0-9]+$'
                       THEN kv_store.value::bigint <= $3
                       ELSE TRUE END
        RETURNING key
        """, key, str(now), now - interval_seconds)
    return row is not None


async def expression_langs() -> list[str]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT DISTINCT lang FROM expression_idioms ORDER BY lang")
    return [r["lang"] for r in rows]


async def upsert_adopted_notes(rows: list[dict]) -> int:
    """Upsert re-adopted orphan notes from the user's Anki collection."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO adopted_notes
              (guid, lang, model, deck, fields, tags, reps, lapses,
               last_review_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8,
                    to_timestamp($9::double precision / 1000.0))
            ON CONFLICT (guid) DO UPDATE SET
              lang = EXCLUDED.lang, model = EXCLUDED.model,
              deck = EXCLUDED.deck, fields = EXCLUDED.fields,
              tags = EXCLUDED.tags, reps = EXCLUDED.reps,
              lapses = EXCLUDED.lapses,
              last_review_at = EXCLUDED.last_review_at,
              adopted_at = NOW()
            """,
            [(r["guid"], r["lang"], r["model"], r["deck"], r["fields"],
              r["tags"], r["reps"], r["lapses"], r["last_review_ms"])
             for r in rows],
        )
    return len(rows)


async def video_apkgs_eligible_for_cleanup(retention_days: int) -> list[dict[str, Any]]:
    """Video apkgs older than the retention window whose file can be
    deleted: every agent subscribed to the language has acked ok, and at
    least one ok ack exists (guards the no-agents edge case)."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT a.id, a.filename FROM apkgs a
        WHERE a.kind = 'video'
          AND a.created_at < NOW() - make_interval(days => $1)
          AND EXISTS (
              SELECT 1 FROM agent_acks ak
              WHERE ak.apkg_id = a.id AND ak.status = 'ok')
          AND NOT EXISTS (
              SELECT 1 FROM agents ag
              WHERE a.lang = ANY(ag.langs)
                AND NOT EXISTS (
                    SELECT 1 FROM agent_acks ak
                    WHERE ak.agent_id = ag.id AND ak.apkg_id = a.id
                      AND ak.status = 'ok'))
        """,
        retention_days,
    )
    return [dict(r) for r in rows]


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
    (cascade-deletes agent_acks) so agents re-pull the new version.
    'grammar' rides the same one-row-per-(lang,kind) mechanics."""
    assert kind in ("pool_idioms", "pool_expr", "pool_idiom_t2e",
                    "pool_idiom_e2t", "grammar", "podcast_lesson", "exercises2",
                    "exercises2_pilot", "translation", "tenses", "tenses_ex",
                    "rescue_comics")
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


# ---------------------------------------------------------------------------
# Versioned local-only TTS queue (legacy-estate Part C)
# ---------------------------------------------------------------------------

async def seed_local_tts_jobs(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Idempotently seed local TTS work.

    ``source_key`` is the durable identity.  Re-seeding identical content
    preserves its status, lease and completed clip.  Any contract/content/path
    change resets that identity to a clean queued job; this is what makes an
    authored text edit self-healing without minting duplicate work.
    """
    if not rows:
        return {"total": 0, "inserted": 0, "reset": 0, "unchanged": 0}
    source_keys = [row.get("source_key") for row in rows]
    if any(not isinstance(key, str) or not key for key in source_keys):
        raise ValueError("every local TTS row needs a source_key")
    if len(source_keys) != len(set(source_keys)):
        raise ValueError("duplicate local TTS source_key in seed batch")

    pool = await get_pool()
    result = await pool.fetchrow(
        """
        WITH incoming AS (
          SELECT * FROM jsonb_to_recordset($1::jsonb) AS x(
            contract_version smallint,
            source_kind text,
            source_key text,
            lang text,
            note_key text,
            clip_kind text,
            text text,
            voice_version text,
            content_hash text,
            staged_path text,
            is_pilot boolean
          )
        ), classified AS (
          SELECT i.*,
                 CASE
                   WHEN j.id IS NULL THEN 'inserted'
                   WHEN j.content_hash IS DISTINCT FROM i.content_hash
                     OR j.staged_path IS DISTINCT FROM i.staged_path
                   THEN 'reset'
                   ELSE 'unchanged'
                 END AS seed_action
          FROM incoming i
          LEFT JOIN local_tts_jobs j ON j.source_key = i.source_key
        ), upserted AS (
          INSERT INTO local_tts_jobs
            (contract_version, source_kind, source_key, lang, note_key,
             clip_kind, text, voice_version, content_hash, staged_path,
             is_pilot)
          SELECT contract_version, source_kind, source_key, lang, note_key,
                 clip_kind, text, voice_version, content_hash, staged_path,
                 is_pilot
          FROM classified
          ON CONFLICT (source_key) DO UPDATE SET
            contract_version = EXCLUDED.contract_version,
            source_kind = EXCLUDED.source_kind,
            lang = EXCLUDED.lang,
            note_key = EXCLUDED.note_key,
            clip_kind = EXCLUDED.clip_kind,
            text = EXCLUDED.text,
            voice_version = EXCLUDED.voice_version,
            content_hash = EXCLUDED.content_hash,
            staged_path = EXCLUDED.staged_path,
            is_pilot = local_tts_jobs.is_pilot OR EXCLUDED.is_pilot,
            status = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN 'queued' ELSE local_tts_jobs.status END,
            attempts = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN 0 ELSE local_tts_jobs.attempts END,
            lease_token = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN NULL ELSE local_tts_jobs.lease_token END,
            worker_id = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN NULL ELSE local_tts_jobs.worker_id END,
            lease_started_at = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN NULL ELSE local_tts_jobs.lease_started_at END,
            lease_expires_at = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN NULL ELSE local_tts_jobs.lease_expires_at END,
            last_error = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN NULL ELSE local_tts_jobs.last_error END,
            last_failed_at = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN NULL ELSE local_tts_jobs.last_failed_at END,
            audio_size_bytes = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN NULL ELSE local_tts_jobs.audio_size_bytes END,
            audio_sha256 = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN NULL ELSE local_tts_jobs.audio_sha256 END,
            completed_at = CASE WHEN
              local_tts_jobs.content_hash IS DISTINCT FROM EXCLUDED.content_hash
              OR local_tts_jobs.staged_path IS DISTINCT FROM EXCLUDED.staged_path
              THEN NULL ELSE local_tts_jobs.completed_at END,
            updated_at = NOW()
          RETURNING source_key
        )
        SELECT COUNT(*)::int AS total,
               COUNT(*) FILTER (WHERE seed_action = 'inserted')::int AS inserted,
               COUNT(*) FILTER (WHERE seed_action = 'reset')::int AS reset,
               COUNT(*) FILTER (WHERE seed_action = 'unchanged')::int AS unchanged,
               (SELECT COUNT(*) FROM upserted)::int AS written
        FROM classified
        """,
        json.dumps(rows, ensure_ascii=False),
    )
    if result is None:
        raise RuntimeError("local TTS seed returned no result")
    return {key: int(result[key]) for key in ("total", "inserted", "reset", "unchanged")}


async def claim_local_tts_jobs(
    *, worker_id: str, limit: int = 8, lease_seconds: int = 900,
    contract_version: int = 1,
) -> dict[str, Any]:
    """Atomically lease a small batch, reclaiming expired leases.

    One opaque token covers the returned batch.  Every fail/upload mutation
    additionally checks the job id, live lease and token, so a stale local
    worker cannot overwrite a later worker's result.
    """
    if not isinstance(worker_id, str) or not worker_id or len(worker_id) > 100:
        raise ValueError("worker_id must be 1..100 characters")
    if limit < 1 or limit > 16:
        raise ValueError("limit must be 1..16")
    if lease_seconds < 60 or lease_seconds > 3600:
        raise ValueError("lease_seconds must be 60..3600")
    lease_token = secrets.token_urlsafe(32)
    pool = await get_pool()
    rows = await pool.fetch(
        """
        WITH picked AS (
          SELECT id
          FROM local_tts_jobs
          WHERE contract_version = $1
            AND (status = 'queued'
                 OR (status = 'leased' AND lease_expires_at <= NOW()))
          ORDER BY is_pilot DESC, id
          FOR UPDATE SKIP LOCKED
          LIMIT $2
        )
        UPDATE local_tts_jobs j
        SET status = 'leased',
            lease_token = $3,
            worker_id = $4,
            lease_started_at = NOW(),
            lease_expires_at = NOW() + make_interval(secs => $5),
            attempts = j.attempts + 1,
            updated_at = NOW()
        FROM picked
        WHERE j.id = picked.id
        RETURNING j.id, j.contract_version, j.source_kind, j.source_key,
                  j.lang, j.note_key, j.clip_kind, j.text, j.voice_version,
                  j.content_hash, j.staged_path, j.is_pilot, j.attempts,
                  j.lease_expires_at
        """,
        contract_version, limit, lease_token, worker_id, lease_seconds,
    )
    return {"lease_token": lease_token, "jobs": [dict(row) for row in rows]}


async def fail_local_tts_job(
    job_id: int, *, lease_token: str, error: str, requeue: bool = True,
) -> dict[str, Any] | None:
    """Release a live lease after local synthesis failure.

    Requeue is the default Part-C policy: bridge contention or a bad clip
    waits for the next local window and never falls through to a paid TTS
    provider.  ``requeue=False`` is an explicit operator quarantine.
    """
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        UPDATE local_tts_jobs
        SET status = CASE WHEN $3 THEN 'queued' ELSE 'failed' END,
            lease_token = NULL,
            lease_started_at = NULL,
            lease_expires_at = NULL,
            last_error = LEFT($4, 1000),
            last_failed_at = NOW(),
            updated_at = NOW()
        WHERE id = $1 AND status = 'leased' AND lease_token = $2
          AND lease_expires_at > NOW()
        RETURNING id, status, attempts
        """,
        job_id, lease_token, requeue, error,
    )
    return dict(row) if row else None


async def leased_local_tts_job(
    job_id: int, *, lease_token: str,
) -> dict[str, Any] | None:
    """Resolve a live lease before accepting its upload."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, contract_version, source_key, lang, note_key, clip_kind,
               text, voice_version, content_hash, staged_path, attempts
        FROM local_tts_jobs
        WHERE id = $1 AND status = 'leased' AND lease_token = $2
          AND lease_expires_at > NOW()
        """,
        job_id, lease_token,
    )
    return dict(row) if row else None


async def complete_local_tts_job(
    job_id: int, *, lease_token: str, audio_size_bytes: int, audio_sha256: str,
) -> dict[str, Any] | None:
    """Mark a validated, atomically staged upload complete under its lease."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        UPDATE local_tts_jobs
        SET status = 'completed',
            lease_token = NULL,
            lease_started_at = NULL,
            lease_expires_at = NULL,
            audio_size_bytes = $3,
            audio_sha256 = $4,
            completed_at = NOW(),
            last_error = NULL,
            updated_at = NOW()
        WHERE id = $1 AND status = 'leased' AND lease_token = $2
          AND lease_expires_at > NOW()
        RETURNING id, status, staged_path, audio_size_bytes, audio_sha256,
                  completed_at
        """,
        job_id, lease_token, audio_size_bytes, audio_sha256,
    )
    return dict(row) if row else None


async def completed_local_tts_jobs(source_keys: list[str]) -> list[dict[str, Any]]:
    """Completed current rows used by the strict local Exercises2 builder."""
    if not source_keys:
        return []
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, source_key, content_hash, staged_path, audio_size_bytes,
               audio_sha256, completed_at
        FROM local_tts_jobs
        WHERE source_key = ANY($1::text[]) AND status = 'completed'
        """,
        source_keys,
    )
    return [dict(row) for row in rows]


async def local_tts_status(contract_version: int = 1) -> dict[str, Any]:
    """Aggregate queue state without returning authored text."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT status, is_pilot, COUNT(*)::int AS n
        FROM local_tts_jobs
        WHERE contract_version = $1
        GROUP BY status, is_pilot
        ORDER BY status, is_pilot DESC
        """,
        contract_version,
    )
    expired = await pool.fetchval(
        """
        SELECT COUNT(*)::int FROM local_tts_jobs
        WHERE contract_version = $1 AND status = 'leased'
          AND lease_expires_at <= NOW()
        """,
        contract_version,
    )
    counts: dict[str, int] = {}
    pilot_counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + int(row["n"])
        if row["is_pilot"]:
            pilot_counts[row["status"]] = int(row["n"])
    return {
        "contract_version": contract_version,
        "counts": counts,
        "pilot_counts": pilot_counts,
        "total": sum(counts.values()),
        "expired_leases": int(expired or 0),
    }


# ---------------------------------------------------------------------------
# Grammar items (docs/GRAMMAR_STRATEGY.md)
# ---------------------------------------------------------------------------

async def _insert_grammar_item(
    conn: asyncpg.Connection, item: dict[str, Any], *, status: str,
    batch: str, fmt: str,
) -> int | None:
    """Insert one grammar item, returning its id or None on sentence conflict."""
    return await conn.fetchval(
        """
        INSERT INTO grammar_items
            (lang, topic, fmt, infinitive, mood, tense, person,
             sentence, answer, gloss_en, why_en,
             status, reject_reason, batch, meta)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
        ON CONFLICT (lang, sentence) DO NOTHING
        RETURNING id
        """,
        item["lang"], item["topic"], fmt, item.get("infinitive"),
        item.get("mood"), item.get("tense"), item.get("person"),
        item["sentence"], item["answer"], item.get("gloss_en"),
        item.get("why_en"), status, item.get("reject_reason"), batch,
        json.dumps(item["meta"]) if item.get("meta") else None,
    )


async def insert_grammar_items(items: list[dict[str, Any]], *, status: str,
                                batch: str, fmt: str = "cloze") -> int:
    """Bulk insert grammar items. ON CONFLICT (lang, sentence) DO NOTHING —
    a regenerated near-duplicate sentence silently drops instead of erroring
    the whole batch. Returns rows actually inserted."""
    if not items:
        return 0
    pool = await get_pool()
    inserted = 0
    async with pool.acquire() as conn:
        for it in items:
            row = await _insert_grammar_item(
                conn, it, status=status, batch=batch, fmt=fmt,
            )
            if row is not None:
                inserted += 1
    return inserted


async def upsert_explainer_item(item: dict[str, Any], *, batch: str) -> int:
    """Insert/update one authored explainer by stable ``(lang, meta.slug)``.

    The row id is deliberately preserved on source edits.  APKG explainers
    use a slug-derived GUID as an additional frozen identity guarantee, while
    the stable database row keeps operational references and stats coherent.
    """
    meta = item.get("meta")
    slug = meta.get("slug") if isinstance(meta, dict) else None
    if item.get("fmt") != "explainer" or not isinstance(slug, str) or not slug:
        raise ValueError("explainer item requires fmt='explainer' and meta.slug")
    pool = await get_pool()
    item_id = await pool.fetchval(
        """
        INSERT INTO grammar_items
            (lang, topic, fmt, infinitive, mood, tense, person,
             sentence, answer, gloss_en, why_en,
             status, reject_reason, batch, meta)
        VALUES ($1,$2,'explainer',NULL,NULL,NULL,NULL,$3,$4,$5,$6,
                'verified',NULL,$7,$8)
        ON CONFLICT (lang, (meta->>'slug')) WHERE fmt = 'explainer'
        DO UPDATE SET
            topic = EXCLUDED.topic,
            sentence = EXCLUDED.sentence,
            answer = EXCLUDED.answer,
            gloss_en = EXCLUDED.gloss_en,
            why_en = EXCLUDED.why_en,
            status = 'verified',
            reject_reason = NULL,
            batch = EXCLUDED.batch,
            meta = EXCLUDED.meta
        RETURNING id
        """,
        item["lang"], item["topic"], item["sentence"], item["answer"],
        item.get("gloss_en"), item.get("why_en"), batch, json.dumps(meta),
    )
    return int(item_id)


async def fetch_grammar_items(lang: str, status: str = "verified",
                               ) -> list[dict[str, Any]]:
    """Fetch deck-eligible grammar rows.

    A linked F4 note is withheld while its private source row is dirty.  Bank
    additions can invalidate a whole-bank production signature, so serving the
    previously verified note before reconversion would expose a stale prompt.
    """
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT i.id, i.lang, i.topic, i.fmt, i.infinitive, i.mood, i.tense,
               i.person, i.sentence, i.answer, i.gloss_en, i.why_en,
               CASE
                 WHEN i.fmt = 'f3' AND source.category IS NOT NULL THEN
                   COALESCE(i.meta, '{}'::jsonb) || jsonb_strip_nulls(
                     jsonb_build_object(
                       'source_category', source.category,
                       'source_subcategory', source.subcategory,
                       'source_unit_hint', source.unit_hint))
                 ELSE i.meta
               END AS meta
        FROM grammar_items i
        LEFT JOIN LATERAL (
            SELECT p.category, p.subcategory, p.unit_hint
            FROM personal_errors p
            WHERE p.f3_item_id = i.id
            ORDER BY p.id
            LIMIT 1
        ) source ON TRUE
        WHERE i.lang = $1 AND i.status = $2
          AND NOT EXISTS (
              SELECT 1 FROM f4_pairs p
              WHERE p.grammar_item_id = i.id
                AND (p.status <> 'active' OR p.needs_conversion)
          )
        ORDER BY i.topic, i.id
        """,
        lang, status,
    )
    result = [dict(r) for r in rows]
    # asyncpg returns JSON/JSONB as text unless a custom codec is installed.
    # Normalize here so deck assembly is independent of pool configuration.
    for item in result:
        if isinstance(item.get("meta"), str):
            try:
                item["meta"] = json.loads(item["meta"])
            except json.JSONDecodeError:
                item["meta"] = None
    return result


async def grammar_topic_stats(lang: str) -> list[dict[str, Any]]:
    """Per-topic verified/rejected counts — the dashboard's view of both
    curriculum size and LLM error rate."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT topic,
               count(*) FILTER (WHERE status = 'verified') AS verified,
               count(*) FILTER (WHERE status = 'rejected') AS rejected
        FROM grammar_items WHERE lang = $1 GROUP BY topic ORDER BY topic
        """,
        lang,
    )
    return [dict(r) for r in rows]


async def seed_grammar_units(rows: list[dict[str, Any]], *,
                             obsolete_keys: tuple[str, ...] = ()) -> None:
    """Boot-time upsert from curriculum code (the definition source).
    Code-owned columns (lang, cluster, label, symbol, sort_order) are
    overwritten; user-mutable state (status, target_size, notes,
    updated_at) is left alone — except a 'planned' row whose unit now
    exists in code gets promoted to 'active'. Explicit ``obsolete_keys`` are
    deleted because code is the curriculum definition source. rows: dicts
    with key, lang, cluster, label, symbol, status, sort_order."""
    if not rows and not obsolete_keys:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        if obsolete_keys:
            await conn.execute(
                "DELETE FROM grammar_units WHERE key = ANY($1::text[])",
                list(obsolete_keys),
            )
        for r in rows:
            await conn.execute(
                """
                INSERT INTO grammar_units
                    (key, lang, cluster, label, symbol, status, sort_order)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (key) DO UPDATE SET
                    lang = EXCLUDED.lang,
                    cluster = EXCLUDED.cluster,
                    label = EXCLUDED.label,
                    symbol = EXCLUDED.symbol,
                    sort_order = EXCLUDED.sort_order,
                    status = CASE
                        WHEN grammar_units.status = 'planned'
                             AND EXCLUDED.status = 'active'
                        THEN 'active'
                        ELSE grammar_units.status
                    END
                """,
                r["key"], r["lang"], r["cluster"], r["label"],
                r["symbol"], r["status"], r["sort_order"],
            )


async def grammar_units_with_counts(lang: str | None = None,
                                     ) -> list[dict[str, Any]]:
    """Every curriculum unit with its live item counts and last-batch
    info — the /grammar tree's data. Batch ids start YYYYMMDD-HHMM, so
    MAX(batch) is also the most recent one."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT u.key, u.lang, u.cluster, u.label, u.symbol, u.status,
               u.target_size, u.sort_order, u.notes, u.updated_at,
               COALESCE(c.verified, 0) AS verified,
               COALESCE(c.rejected, 0) AS rejected,
               COALESCE(c.retired, 0)  AS retired,
               c.last_item_at, c.last_batch
        FROM grammar_units u
        LEFT JOIN LATERAL (
            SELECT count(*) FILTER (WHERE status = 'verified') AS verified,
                   count(*) FILTER (WHERE status = 'rejected') AS rejected,
                   count(*) FILTER (WHERE status = 'retired')  AS retired,
                   MAX(created_at) AS last_item_at,
                   MAX(batch)      AS last_batch
            FROM grammar_items i
            WHERE i.topic = u.key AND i.lang = u.lang) c ON TRUE
        WHERE $1::text IS NULL OR u.lang = $1
        ORDER BY u.lang, u.sort_order
        """,
        lang,
    )
    return [dict(r) for r in rows]


async def update_grammar_unit(key: str, *, target_size: int | None = None,
                               status: str | None = None,
                               notes: str | None = None,
                               ) -> dict[str, Any] | None:
    """Patch the user-mutable columns; None = leave unchanged. Returns the
    updated row, or None for an unknown key."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        UPDATE grammar_units SET
            target_size = COALESCE($2, target_size),
            status      = COALESCE($3, status),
            notes       = COALESCE($4, notes),
            updated_at  = NOW()
        WHERE key = $1
        RETURNING key, lang, cluster, label, symbol, status, target_size,
                  sort_order, notes, updated_at
        """,
        key, target_size, status, notes,
    )
    return dict(row) if row else None


async def retire_grammar_item(item_id: int) -> dict[str, Any] | None:
    """Kill one bad card: verified → retired. The next deck rebuild drops
    it from the apkg (its note stays in Anki until a cleanup.json purge).
    A linked F4 source pair is retired in the same transaction so a later
    conversion cannot silently recreate a card the operator removed.
    Returns {id, lang, topic} or None if the item wasn't verified."""
    pool = await get_pool()
    async with pool.acquire() as conn, conn.transaction():
        # Conversion locks pair → grammar item. Use the same order here to
        # prevent a concurrent refresh/retirement deadlock.
        f4_pair_id = await conn.fetchval(
            """SELECT id FROM f4_pairs
               WHERE grammar_item_id = $1 FOR UPDATE""",
            item_id,
        )
        row = await conn.fetchrow(
            """
            UPDATE grammar_items SET status = 'retired'
            WHERE id = $1 AND status = 'verified'
            RETURNING id, lang, topic
            """,
            item_id,
        )
        if row is None:
            return None
        if f4_pair_id is not None:
            await conn.execute(
                """UPDATE f4_pairs
                   SET status = 'retired', needs_conversion = FALSE,
                       updated_at = NOW()
                   WHERE id = $1""",
                f4_pair_id,
            )
        return dict(row)


async def fetch_grammar_rejects(lang: str, topic: str | None = None,
                                 limit: int = 50) -> list[dict[str, Any]]:
    """Rejected items with reasons — the diagnostic view for tuning
    generator prompts per unit."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, topic, infinitive, person, sentence, answer,
               reject_reason, batch, created_at
        FROM grammar_items
        WHERE lang = $1 AND status = 'rejected'
          AND ($2::text IS NULL OR topic = $2)
        ORDER BY id DESC LIMIT $3
        """,
        lang, topic, limit,
    )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# LingQ vocabulary mirror + kv store (idiomatic/lingq.py)
# ---------------------------------------------------------------------------

async def set_kv(key: str, value: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO kv_store (key, value) VALUES ($1, $2)
           ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()""",
        key, value)


async def get_kv(key: str) -> str | None:
    pool = await get_pool()
    return await pool.fetchval("SELECT value FROM kv_store WHERE key = $1", key)


async def set_external_token(name: str, token: str) -> None:
    await set_kv(f"token:{name}", token)


async def get_external_token(name: str) -> str | None:
    return await get_kv(f"token:{name}")


async def upsert_lingq_terms(rows: list[dict[str, Any]]) -> int:
    """One transaction per page: row-by-row autocommit at ~52k rows put
    visible write pressure on the basic-256mb Postgres during the first
    full sync (2026-07-31 outage suspect — the web app shares that DB)."""
    if not rows:
        return 0
    pool = await get_pool()
    n = 0
    async with pool.acquire() as conn, conn.transaction():
        for r in rows:
            await conn.execute(
                """
                INSERT INTO lingq_terms
                    (lingq_id, lang, term, fragment, hints, status,
                     extended_status, notes, tags, srs_due_date)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,
                        NULLIF($10, '')::timestamptz)
                ON CONFLICT (lingq_id) DO UPDATE SET
                    term = EXCLUDED.term,
                    fragment = EXCLUDED.fragment,
                    hints = EXCLUDED.hints,
                    status = EXCLUDED.status,
                    extended_status = EXCLUDED.extended_status,
                    notes = EXCLUDED.notes,
                    tags = EXCLUDED.tags,
                    srs_due_date = EXCLUDED.srs_due_date,
                    updated_at = NOW()
                """,
                r["lingq_id"], r["lang"], r["term"], r.get("fragment"),
                json.dumps(r.get("hints") or []), r.get("status"),
                r.get("extended_status"), r.get("notes"),
                r.get("tags") or [], r.get("srs_due_date") or "",
            )
            n += 1
    return n


async def lingq_stats() -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT lang, count(*) AS terms,
                  count(*) FILTER (WHERE status < 3) AS learning,
                  MAX(updated_at) AS last_updated
           FROM lingq_terms GROUP BY lang ORDER BY terms DESC""")
    return [dict(r) for r in rows]


async def upsert_personal_errors(rows: list[dict[str, Any]]) -> int:
    """One transaction per batch (same write-pressure lesson as
    upsert_lingq_terms). Re-uploads refresh the mutable analysis fields
    but never clobber status='retired' — retirement is user state."""
    if not rows:
        return 0
    pool = await get_pool()
    n = 0
    async with pool.acquire() as conn, conn.transaction():
        for r in rows:
            await conn.execute(
                """
                INSERT INTO personal_errors
                    (registry_id, lang, kind, wrong, right_form, gloss_en, category,
                     subcategory, why, interference_source, occurrences,
                     first_seen, last_seen, sources, unit_hint, confidence)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
                ON CONFLICT (lang, COALESCE(wrong, ''), right_form)
                DO UPDATE SET
                    registry_id = COALESCE(
                        EXCLUDED.registry_id, personal_errors.registry_id),
                    kind = EXCLUDED.kind,
                    gloss_en = EXCLUDED.gloss_en,
                    category = EXCLUDED.category,
                    subcategory = EXCLUDED.subcategory,
                    why = EXCLUDED.why,
                    interference_source = EXCLUDED.interference_source,
                    occurrences = EXCLUDED.occurrences,
                    first_seen = EXCLUDED.first_seen,
                    last_seen = EXCLUDED.last_seen,
                    sources = EXCLUDED.sources,
                    unit_hint = EXCLUDED.unit_hint,
                    confidence = EXCLUDED.confidence
                """,
                r.get("registry_id"), r["lang"], r["kind"], r.get("wrong"),
                r["right_form"], r.get("gloss_en"), r["category"],
                r.get("subcategory"), r.get("why"),
                r.get("interference_source"), r.get("occurrences", 1),
                r.get("first_seen"), r.get("last_seen"),
                r.get("sources") or [], r.get("unit_hint"),
                r.get("confidence"),
            )
            n += 1
    return n


async def fetch_f3_candidates(lang: str) -> list[dict[str, Any]]:
    """Eligible personal errors, ranked for F3 conversion.

    ``sentence_collision`` lets the conversion layer count and log existing
    grammar sentence conflicts while continuing farther down the ranked list.
    The unique constraint remains the final guard against a concurrent insert
    after this read.
    """
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT p.id, p.lang, p.kind, p.status, p.confidence, p.f3_item_id,
               p.wrong, p.right_form, p.gloss_en, p.category,
               p.subcategory, p.unit_hint, p.why, p.occurrences,
               p.first_seen, p.last_seen,
               EXISTS (
                   SELECT 1
                   FROM grammar_items i
                   WHERE i.lang = p.lang
                     AND i.sentence = REGEXP_REPLACE(
                         BTRIM(p.wrong), '[[:space:]]+', ' ', 'g'
                     )
               ) AS sentence_collision
        FROM personal_errors p
        WHERE p.lang = $1
          AND p.kind = 'error'
          AND p.status = 'active'
          AND p.confidence = 'high'
          AND p.f3_item_id IS NULL
          AND p.wrong IS NOT NULL
        ORDER BY p.occurrences DESC, p.last_seen DESC NULLS LAST, p.id
        """,
        lang,
    )
    return [dict(r) for r in rows]


async def insert_f3_grammar_item(
    personal_error_id: int, item: dict[str, Any], *, batch: str,
) -> int | None:
    """Atomically convert one still-eligible personal error into an F3 item.

    The source row is locked and rechecked because candidate selection and
    conversion are separate calls. Returns the grammar_items id, or None when
    the source was already linked/became ineligible or its sentence collided.
    """
    pool = await get_pool()
    async with pool.acquire() as conn, conn.transaction():
        source = await conn.fetchrow(
            """
            SELECT id, lang, wrong, right_form, gloss_en, category,
                   subcategory, unit_hint, why
            FROM personal_errors
            WHERE id = $1
              AND kind = 'error'
              AND status = 'active'
              AND confidence = 'high'
              AND f3_item_id IS NULL
              AND wrong IS NOT NULL
            FOR UPDATE
            """,
            personal_error_id,
        )
        if source is None:
            return None

        # Never link an item to a different source pair accidentally. F3's
        # mapping normalizes whitespace but otherwise preserves the
        # teacher-attested text verbatim.
        def clean(value: Any) -> str:
            return " ".join(str(value or "").strip().split())

        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        if (item.get("lang") != source["lang"]
                or clean(item.get("sentence")) != clean(source["wrong"])
                or clean(item.get("answer")) != clean(source["right_form"])
                or clean(item.get("gloss_en"))
                != (clean(source["gloss_en"]) or clean(source["category"]))
                or clean(item.get("why_en")) != clean(source["why"])
                or clean(meta.get("source_category")) != clean(source["category"])
                or clean(meta.get("source_subcategory"))
                != clean(source["subcategory"])
                or clean(meta.get("source_unit_hint")) != clean(source["unit_hint"])):
            return None

        item_id = await _insert_grammar_item(
            conn, item, status="verified", batch=batch, fmt="f3",
        )
        if item_id is None:
            return None
        await conn.execute(
            "UPDATE personal_errors SET f3_item_id = $2 WHERE id = $1",
            personal_error_id, item_id,
        )
        return item_id


async def stage_personal_errors(payload: str, n_rows: int) -> int:
    """One blob INSERT from the web process; cron does the real work."""
    pool = await get_pool()
    return await pool.fetchval(
        """INSERT INTO personal_errors_staging (payload, n_rows)
           VALUES ($1, $2) RETURNING id""",
        payload, n_rows)


async def fetch_unprocessed_error_staging() -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT id, payload FROM personal_errors_staging
           WHERE processed_at IS NULL ORDER BY id""")
    return [dict(r) for r in rows]


async def mark_error_staging(staging_id: int, *, note: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """UPDATE personal_errors_staging
           SET processed_at = NOW(), note = $2, payload = ''
           WHERE id = $1""",
        staging_id, note)


async def personal_errors_stats() -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT lang, kind, category, count(*) AS n,
                  SUM(occurrences) AS occurrences
           FROM personal_errors
           GROUP BY lang, kind, category ORDER BY lang, n DESC""")
    return [dict(r) for r in rows]


async def stage_f4_pairs(payload: str, n_rows: int) -> int:
    """Stage one private F4 bank with a single web-process INSERT."""
    pool = await get_pool()
    return await pool.fetchval(
        """INSERT INTO f4_pairs_staging (payload, n_rows)
           VALUES ($1, $2) RETURNING id""",
        payload, n_rows,
    )


async def fetch_unprocessed_f4_staging() -> list[dict[str, Any]]:
    """Return pending F4 payloads oldest-first for cron-side ingestion."""
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT id, payload FROM f4_pairs_staging
           WHERE processed_at IS NULL ORDER BY id"""
    )
    return [dict(r) for r in rows]


async def mark_f4_staging(staging_id: int, *, note: str) -> None:
    """Finish a staged F4 payload and erase its private raw contents."""
    pool = await get_pool()
    await pool.execute(
        """UPDATE f4_pairs_staging
           SET processed_at = NOW(), note = $2, payload = ''
           WHERE id = $1""",
        staging_id, note,
    )


async def _resolve_f4_personal_error(
    conn: asyncpg.Connection, row: dict[str, Any],
) -> int | None:
    """Resolve an attested F4 row to its local personal-errors source.

    Exact pairs use the registry's unique target/wrong/right identity.  A
    reviewed projection must name the private registry's stable external id;
    both selected forms are then checked as case-sensitive, verbatim
    substrings.  This function is called for every row before its batch writes
    begin, so a deterministic validation error cannot leave a partial batch.
    """
    pair_key = str(row.get("pair_key") or "")
    projection_id = row.get("projection_registry_id")
    if not row.get("attested"):
        if projection_id is not None:
            raise ValueError(
                f"F4 pair {pair_key}: unattested pair declares a projection"
            )
        return None

    if projection_id is None:
        source = await conn.fetchrow(
            """SELECT id
               FROM personal_errors
               WHERE lang = $1 AND kind = 'error'
                 AND wrong = $2 AND right_form = $3""",
            row["target_lang"], row["false_form"], row["correct_target"],
        )
        if source is None:
            raise ValueError(
                f"F4 pair {pair_key}: no exact personal-error match"
            )
        return int(source["id"])

    source = await conn.fetchrow(
        """SELECT id, lang, wrong, right_form
           FROM personal_errors
           WHERE registry_id = $1 AND kind = 'error'""",
        projection_id,
    )
    if source is None:
        raise ValueError(
            f"F4 pair {pair_key}: unknown projection registry id"
        )
    wrong = source["wrong"] or ""
    right = source["right_form"] or ""
    if (source["lang"] != row["target_lang"]
            or row["false_form"] not in wrong
            or row["correct_target"] not in right):
        raise ValueError(
            f"F4 pair {pair_key}: projection does not match registry row"
        )
    return int(source["id"])


async def upsert_f4_pairs(rows: list[dict[str, Any]]) -> int:
    """Validate and upsert one F4 batch atomically.

    All attestation links are resolved before the first INSERT. Every accepted
    target-bank upload conservatively marks that target's active rows dirty:
    adding one answer can change the uniqueness certificate of otherwise
    unchanged A/B cards. Existing grammar_items ids and user-owned retirement
    state are never overwritten by an upload.
    """
    if not rows:
        return 0
    pool = await get_pool()
    async with pool.acquire() as conn, conn.transaction():
        validated: list[tuple[dict[str, Any], int | None]] = []
        for row in rows:
            personal_error_id = await _resolve_f4_personal_error(conn, row)
            validated.append((row, personal_error_id))

        # Conflict updates take row locks. A stable order prevents two
        # concurrently uploaded banks from acquiring the same locks in
        # opposite orders.
        validated.sort(key=lambda value: value[0]["pair_key"])
        for row, personal_error_id in validated:
            pair_id = await conn.fetchval(
                """
                INSERT INTO f4_pairs
                    (schema_version, pair_key, target_lang, source_lang,
                     concept_en, correct_target, false_form, source_form,
                     category, why, occurrences, attested, personal_error_id)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                ON CONFLICT (pair_key) DO UPDATE SET
                    source_lang = EXCLUDED.source_lang,
                    concept_en = EXCLUDED.concept_en,
                    source_form = EXCLUDED.source_form,
                    category = EXCLUDED.category,
                    why = EXCLUDED.why,
                    occurrences = EXCLUDED.occurrences,
                    attested = EXCLUDED.attested,
                    personal_error_id = EXCLUDED.personal_error_id,
                    needs_conversion = f4_pairs.needs_conversion OR
                        ROW(f4_pairs.source_lang,
                            f4_pairs.concept_en,
                            f4_pairs.source_form,
                            f4_pairs.category,
                            f4_pairs.why,
                            f4_pairs.occurrences,
                            f4_pairs.attested,
                            f4_pairs.personal_error_id)
                        IS DISTINCT FROM
                        ROW(EXCLUDED.source_lang,
                            EXCLUDED.concept_en,
                            EXCLUDED.source_form,
                            EXCLUDED.category,
                            EXCLUDED.why,
                            EXCLUDED.occurrences,
                            EXCLUDED.attested,
                            EXCLUDED.personal_error_id),
                    updated_at = NOW()
                WHERE f4_pairs.schema_version = EXCLUDED.schema_version
                  AND f4_pairs.target_lang = EXCLUDED.target_lang
                RETURNING id
                """,
                row["schema_version"], row["pair_key"], row["target_lang"],
                row["source_lang"], row["concept_en"],
                row["correct_target"], row["false_form"],
                row["source_form"], row["category"], row["why"],
                row["occurrences"], row["attested"], personal_error_id,
            )
            if pair_id is None:
                # The SHA-256 identity was reused for different immutable
                # inputs.  Raising here rolls back every write in this batch.
                raise ValueError(
                    f"F4 pair {row['pair_key']}: pair-key identity mismatch"
                )
        # A production signature is certified against the whole active target
        # bank, not just the changed row. Recompile every linked row for each
        # target represented in this accepted upload while retaining its id.
        await conn.execute(
            """UPDATE f4_pairs
               SET needs_conversion = TRUE,
                   updated_at = GREATEST(
                       clock_timestamp(), updated_at + INTERVAL '1 microsecond'
                   )
               WHERE status = 'active' AND target_lang = ANY($1::text[])""",
            sorted({row["target_lang"] for row in rows}),
        )
    return len(rows)


async def fetch_active_f4_pairs(target_lang: str) -> list[dict[str, Any]]:
    """Return every active pair for one receiving language.

    Callers need the whole target bank, including already-converted rows, to
    certify production-signature uniqueness before selecting dirty cards.
    """
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT id, schema_version, pair_key, target_lang, source_lang,
                  concept_en, correct_target, false_form, source_form,
                  category, why, occurrences, attested, personal_error_id,
                  grammar_item_id, needs_conversion, status, created_at,
                  updated_at, converted_at
           FROM f4_pairs
           WHERE target_lang = $1 AND status = 'active'
           ORDER BY attested DESC, occurrences DESC, pair_key""",
        target_lang,
    )
    return [dict(r) for r in rows]


async def upsert_f4_grammar_item(
    f4_pair_id: int, item: dict[str, Any], *, batch: str,
) -> int | None:
    """Atomically create or refresh the stable grammar item for one F4 pair.

    The pair row is locked and eligibility plus the identity-bearing mapped
    fields are rechecked.  Existing grammar rows are updated in place so their
    integer ItemId and Anki GUID never change.  ``None`` means the pair was no
    longer dirty/active or its compiled ``(lang, sentence)`` collided.
    """
    pool = await get_pool()
    async with pool.acquire() as conn, conn.transaction():
        source = await conn.fetchrow(
            """SELECT id, pair_key, target_lang, source_lang, concept_en,
                      correct_target, false_form, source_form, category, why,
                      occurrences, attested, grammar_item_id, updated_at
               FROM f4_pairs
               WHERE id = $1 AND status = 'active' AND needs_conversion
               FOR UPDATE""",
            f4_pair_id,
        )
        if source is None:
            return None

        expected_topic = f"{source['target_lang']}_interference_f4"
        meta = item.get("meta")
        if (item.get("fmt") != "f4"
                or item.get("lang") != source["target_lang"]
                or item.get("topic") != expected_topic
                or item.get("answer") != source["correct_target"]
                or item.get("gloss_en") != source["concept_en"]
                or item.get("why_en") != source["why"]
                or not isinstance(item.get("sentence"), str)
                or item["sentence"].count("___") != 1
                or not isinstance(meta, dict)
                or meta.get("pair_key") != source["pair_key"]
                or meta.get("source_lang") != source["source_lang"]
                or meta.get("source_form") != source["source_form"]
                or meta.get("false_form") != source["false_form"]
                or meta.get("category") != source["category"]
                or meta.get("attested") != source["attested"]
                or meta.get("occurrences") != source["occurrences"]
                or meta.get("source_revision")
                != source["updated_at"].isoformat()):
            return None

        grammar_item_id = source["grammar_item_id"]
        if grammar_item_id is None:
            grammar_item_id = await _insert_grammar_item(
                conn, item, status="verified", batch=batch, fmt="f4",
            )
            if grammar_item_id is None:
                return None
        else:
            linked = await conn.fetchrow(
                """SELECT id, lang, topic, fmt, meta
                   FROM grammar_items WHERE id = $1 FOR UPDATE""",
                grammar_item_id,
            )
            linked_meta = linked["meta"] if linked is not None else None
            if isinstance(linked_meta, str):
                try:
                    linked_meta = json.loads(linked_meta)
                except (TypeError, ValueError):
                    linked_meta = None
            if (linked is None
                    or linked["fmt"] != "f4"
                    or linked["lang"] != source["target_lang"]
                    or linked["topic"] != expected_topic
                    or not isinstance(linked_meta, dict)
                    or linked_meta.get("pair_key") != source["pair_key"]):
                return None
            collision = await conn.fetchval(
                """SELECT id FROM grammar_items
                   WHERE lang = $1 AND sentence = $2 AND id <> $3
                   LIMIT 1""",
                item["lang"], item["sentence"], grammar_item_id,
            )
            if collision is not None:
                return None
            try:
                # The nested transaction is a savepoint: an insert racing the
                # collision read can still trip the unique constraint without
                # aborting the outer transaction or clearing the dirty flag.
                async with conn.transaction():
                    updated = await conn.fetchval(
                        """UPDATE grammar_items SET
                               lang = $2, topic = $3, fmt = 'f4',
                               infinitive = $4, mood = $5, tense = $6,
                               person = $7, sentence = $8, answer = $9,
                               gloss_en = $10, why_en = $11,
                               batch = $12, meta = $13
                           WHERE id = $1
                           RETURNING id""",
                        grammar_item_id, item["lang"], item["topic"],
                        item.get("infinitive"), item.get("mood"),
                        item.get("tense"), item.get("person"),
                        item["sentence"], item["answer"],
                        item.get("gloss_en"), item.get("why_en"), batch,
                        json.dumps(meta) if meta else None,
                    )
            except asyncpg.UniqueViolationError:
                return None
            if updated is None:
                return None

        await conn.execute(
            """UPDATE f4_pairs
               SET grammar_item_id = $2, needs_conversion = FALSE,
                   converted_at = NOW(), updated_at = NOW()
               WHERE id = $1""",
            f4_pair_id, grammar_item_id,
        )
        return int(grammar_item_id)


async def f4_pairs_stats() -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT target_lang, status, count(*) AS pairs,
                  count(*) FILTER (WHERE attested) AS attested,
                  count(*) FILTER (WHERE needs_conversion) AS needs_conversion,
                  COALESCE(SUM(occurrences), 0) AS occurrences,
                  MAX(updated_at) AS last_updated
           FROM f4_pairs
           GROUP BY target_lang, status
           ORDER BY target_lang, status"""
    )
    return [dict(r) for r in rows]


async def sample_lingq_terms(lang: str, n: int = 20,
                              max_status: int = 2) -> list[dict[str, Any]]:
    """Random sample of still-being-learned terms for prompt injection.
    max_status 2 = exclude 'known' (status 3); pass 3 to include all."""
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT term, hints, status FROM lingq_terms
           WHERE lang = $1 AND COALESCE(status, 0) <= $2
           ORDER BY random() LIMIT $3""",
        lang, max_status, n)
    out = []
    for r in rows:
        hints = json.loads(r["hints"]) if isinstance(r["hints"], str) else (r["hints"] or [])
        gloss = next((h.get("text") for h in hints if h.get("text")), None)
        out.append({"term": r["term"], "gloss": gloss, "status": r["status"]})
    return out
