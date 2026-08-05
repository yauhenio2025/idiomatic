"""Dashboard read-only JSON API — everything under /ui/api/*.

Serves the React dashboard mounted at /. Strictly read-only SQL, always
parametrized. Auth: X-Admin-Token header (same constant-time check as
/admin/*); the audio endpoint additionally accepts ?token= because
<audio> tags can't set headers.

Nothing here is on the pipeline's critical path — the worker, cron, and
agent delivery endpoints never call into this module.
"""

from __future__ import annotations

import json
import re
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from fastapi.responses import FileResponse

from . import db
from .langs import LANG_NAMES
from .settings import get_settings

router = APIRouter(prefix="/ui/api")


# --- auth --------------------------------------------------------------------

def _check_token(token: str | None) -> None:
    admin_token = get_settings().admin_token
    if not admin_token:
        raise HTTPException(503, "dashboard disabled (ADMIN_TOKEN unset)")
    if not token or not secrets.compare_digest(token, admin_token):
        raise HTTPException(401, "bad admin token")


async def authed_ui(x_admin_token: str | None = Header(default=None)) -> None:
    _check_token(x_admin_token)


@router.get("/auth/check")
async def auth_check(_: None = Depends(authed_ui)) -> dict:
    """Login screen validates the pasted token against this."""
    return {"ok": True}


# --- shared SQL fragments ------------------------------------------------------

# Classify videos.status_msg into the funnel's skip-reason buckets.
# Prefix-matching per the message formats in cron.py / worker.py.
REASON_CLASS_SQL = """
    CASE
      WHEN v.status_msg LIKE '%(cron pre-filter%' THEN 'duration-pre-filter'
      WHEN v.status_msg LIKE 'duration %'         THEN 'duration-post-check'
      WHEN v.status_msg LIKE 'expired:%'          THEN 'expired-stale'
      WHEN v.status_msg LIKE 'oxylabs permanent%' THEN 'oxylabs-permanent'
      WHEN v.status_msg LIKE 'wrong channel%'     THEN 'wrong-channel'
      WHEN v.status_msg = 'all dedupes'           THEN 'all-duplicates'
      WHEN v.status_msg = 'no idioms extracted'   THEN 'no-idioms'
      WHEN v.status_msg IS NULL OR v.status_msg = '' THEN 'none'
      ELSE 'other'
    END
"""

_CURATED_PREFIX = "Curated ·"


def _parse_structured(value) -> dict | None:
    """asyncpg returns jsonb as str unless a codec is registered."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


# --- overview ------------------------------------------------------------------

@router.get("/overview")
async def overview(_: None = Depends(authed_ui)) -> dict:
    pool = await db.get_pool()
    settings = get_settings()

    status_counts = {
        r["status"]: r["n"] for r in await pool.fetch(
            "SELECT status, COUNT(*) AS n FROM videos GROUP BY status")
    }
    latest_apkg = await pool.fetchrow(
        """
        SELECT created_at,
               EXTRACT(EPOCH FROM NOW() - created_at) / 3600 AS age_hours
        FROM apkgs ORDER BY created_at DESC LIMIT 1
        """)
    age_h = round(float(latest_apkg["age_hours"]), 1) if latest_apkg else None
    queued = status_counts.get("queued", 0)

    processing_now = [dict(r) for r in await pool.fetch(
        """
        SELECT v.id, v.youtube_id, v.title, v.lang, v.duration_sec,
               v.picked_at, c.name AS channel_name
        FROM videos v LEFT JOIN channels c ON c.id = v.channel_id
        WHERE v.status = 'processing' ORDER BY v.picked_at
        """)]

    builds_today = [dict(r) for r in await pool.fetch(
        """
        SELECT lang, COUNT(*) AS built
        FROM apkgs
        WHERE kind = 'video' AND created_at >= date_trunc('day', NOW())
        GROUP BY lang ORDER BY lang
        """)]

    throughput = [dict(r) for r in await pool.fetch(
        """
        SELECT created_at::date AS day, lang, COUNT(*) AS n
        FROM apkgs
        WHERE kind = 'video' AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY 1, 2 ORDER BY 1, 2
        """)]

    growth = [dict(r) for r in await pool.fetch(
        """
        SELECT day::date AS day, lang,
               SUM(n) OVER (PARTITION BY lang ORDER BY day) AS total
        FROM (
            SELECT added_at::date AS day, lang, COUNT(*) AS n
            FROM expressions GROUP BY 1, 2
        ) daily
        ORDER BY day, lang
        """)]

    funnel = [dict(r) for r in await pool.fetch(
        f"""
        SELECT v.status, {REASON_CLASS_SQL} AS reason_class, COUNT(*) AS n
        FROM videos v
        WHERE v.first_seen >= NOW() - INTERVAL '7 days'
        GROUP BY 1, 2 ORDER BY 3 DESC
        """)]

    dedup_7d = await pool.fetchrow(
        """
        SELECT COUNT(*) FILTER (WHERE verdict = 'fresh')     AS fresh,
               COUNT(*) FILTER (WHERE verdict = 'duplicate') AS duplicates
        FROM extraction_log
        WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
    log_since = await pool.fetchval("SELECT MIN(created_at) FROM extraction_log")

    expressions_total = [dict(r) for r in await pool.fetch(
        "SELECT lang, COUNT(*) AS n FROM expressions GROUP BY lang ORDER BY lang")]

    return {
        "health": {
            "queued_videos": queued,
            "processing": processing_now,
            "latest_apkg_age_hours": age_h,
            "stalled": bool(queued and age_h is not None and age_h > 6),
            "status_counts": status_counts,
            "daily_cap": settings.max_new_apkgs_per_lang_per_day,
            "builds_today": builds_today,
        },
        "throughput_30d": throughput,
        "library_growth": growth,
        "funnel_7d": funnel,
        "dedup_7d": dict(dedup_7d) if dedup_7d else {},
        "extraction_log_since": log_since,
        "expressions_by_lang": expressions_total,
        "lang_names": LANG_NAMES,
    }


# --- videos ---------------------------------------------------------------------

@router.get("/videos")
async def videos(
    _: None = Depends(authed_ui),
    lang: str | None = None,
    status: str | None = None,
    channel_id: int | None = None,
    q: str | None = None,
    curated: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    conds, args = [], []

    def arg(v) -> str:
        args.append(v)
        return f"${len(args)}"

    if lang:
        conds.append(f"v.lang = {arg(lang)}")
    if status:
        conds.append(f"v.status = {arg(status)}")
    if channel_id is not None:
        conds.append(f"v.channel_id = {arg(channel_id)}")
    if q:
        conds.append(f"v.title ILIKE {arg('%' + q + '%')}")
    if curated is True:
        conds.append(f"c.name LIKE {arg(_CURATED_PREFIX + '%')}")
    elif curated is False:
        conds.append(
            f"(c.name IS NULL OR c.name NOT LIKE {arg(_CURATED_PREFIX + '%')})")
    if date_from:
        conds.append(f"v.first_seen >= {arg(date_from)}::date")
    if date_to:
        conds.append(f"v.first_seen < ({arg(date_to)}::date + 1)")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""

    pool = await db.get_pool()
    total = await pool.fetchval(
        f"SELECT COUNT(*) FROM videos v LEFT JOIN channels c ON c.id = v.channel_id {where}",
        *args)
    rows = await pool.fetch(
        f"""
        SELECT v.id, v.youtube_id, v.title, v.lang, v.duration_sec,
               v.status, v.status_msg, {REASON_CLASS_SQL} AS reason_class,
               v.attempts, v.first_seen, v.finished_at, v.processing_seconds,
               c.id AS channel_id, c.name AS channel_name,
               COALESCE(c.name LIKE {arg(_CURATED_PREFIX + '%')}, FALSE) AS curated,
               a.id AS apkg_id, a.created_at AS apkg_built_at, a.n_idioms,
               ack.delivered_at,
               el.n_extracted, el.n_fresh, el.n_duplicates
        FROM videos v
        LEFT JOIN channels c ON c.id = v.channel_id
        LEFT JOIN apkgs a ON a.video_id = v.id AND a.kind = 'video'
        LEFT JOIN LATERAL (
            SELECT MAX(acked_at) AS delivered_at FROM agent_acks
            WHERE apkg_id = a.id AND status = 'ok') ack ON TRUE
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS n_extracted,
                   COUNT(*) FILTER (WHERE verdict = 'fresh') AS n_fresh,
                   COUNT(*) FILTER (WHERE verdict = 'duplicate') AS n_duplicates
            FROM extraction_log WHERE video_id = v.id) el ON TRUE
        {where}
        ORDER BY v.first_seen DESC
        LIMIT {arg(limit)} OFFSET {arg(offset)}
        """,
        *args)
    return {"total": total, "rows": [dict(r) for r in rows]}


@router.get("/videos/{video_id}")
async def video_detail(video_id: int, _: None = Depends(authed_ui)) -> dict:
    pool = await db.get_pool()
    v = await pool.fetchrow(
        f"""
        SELECT v.*, {REASON_CLASS_SQL} AS reason_class,
               c.name AS channel_name,
               COALESCE(c.name LIKE '{_CURATED_PREFIX}%', FALSE) AS curated,
               a.id AS apkg_id, a.created_at AS apkg_built_at,
               a.n_idioms, a.size_bytes AS apkg_size_bytes,
               ack.delivered_at
        FROM videos v
        LEFT JOIN channels c ON c.id = v.channel_id
        LEFT JOIN apkgs a ON a.video_id = v.id AND a.kind = 'video'
        LEFT JOIN LATERAL (
            SELECT MAX(acked_at) AS delivered_at FROM agent_acks
            WHERE apkg_id = a.id AND status = 'ok') ack ON TRUE
        WHERE v.id = $1
        """,
        video_id)
    if not v:
        raise HTTPException(404, "unknown video")

    idioms = await pool.fetch(
        """
        SELECT i.id, i.expression_id, i.idiom_text, i.english_gloss,
               i.source_phrase_target, i.source_phrase_en, i.explanation_en,
               i.structured, i.audio_idiom_tgt, i.audio_idiom_en,
               i.audio_explanation, i.audio_context, i.created_at
        FROM expression_idioms i WHERE i.video_id = $1 ORDER BY i.id
        """,
        video_id)
    idiom_list = []
    for r in idioms:
        d = dict(r)
        d["structured"] = _parse_structured(d.get("structured"))
        idiom_list.append(d)
    if idiom_list:
        examples = await pool.fetch(
            """
            SELECT idiom_id, ord, en_text, target_text, audio_en, audio_target
            FROM expression_examples
            WHERE idiom_id = ANY($1::bigint[]) ORDER BY idiom_id, ord
            """,
            [d["id"] for d in idiom_list])
        by_idiom: dict[int, list] = {}
        for ex in examples:
            by_idiom.setdefault(ex["idiom_id"], []).append(dict(ex))
        for d in idiom_list:
            d["examples"] = by_idiom.get(d["id"], [])

    extraction = [dict(r) for r in await pool.fetch(
        """
        SELECT el.id, el.phrase, el.english, el.verdict, el.created_at,
               el.duplicate_of,
               e.text AS duplicate_text,
               fv.id AS first_video_id, fv.title AS first_video_title,
               fv.youtube_id AS first_video_youtube_id
        FROM extraction_log el
        LEFT JOIN expressions e ON e.id = el.duplicate_of
        LEFT JOIN videos fv ON fv.id = e.first_video_id
        WHERE el.video_id = $1 ORDER BY el.id
        """,
        video_id)]

    return {"video": dict(v), "idioms": idiom_list, "extraction_log": extraction}


# --- expressions (library browser) ----------------------------------------------

@router.get("/expressions")
async def expressions(
    _: None = Depends(authed_ui),
    lang: str | None = None,
    q: str | None = None,
    channel_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=30, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    conds, args = [], []

    def arg(v) -> str:
        args.append(v)
        return f"${len(args)}"

    if lang:
        conds.append(f"i.lang = {arg(lang)}")
    if q:
        p = arg("%" + q + "%")
        conds.append(f"(i.idiom_text ILIKE {p} OR i.english_gloss ILIKE {p}"
                     f" OR i.explanation_en ILIKE {p})")
    if channel_id is not None:
        conds.append(f"v.channel_id = {arg(channel_id)}")
    if date_from:
        conds.append(f"i.created_at >= {arg(date_from)}::date")
    if date_to:
        conds.append(f"i.created_at < ({arg(date_to)}::date + 1)")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""

    pool = await db.get_pool()
    total = await pool.fetchval(
        f"""
        SELECT COUNT(*) FROM expression_idioms i
        LEFT JOIN videos v ON v.id = i.video_id {where}
        """,
        *args)
    rows = await pool.fetch(
        f"""
        SELECT i.id, i.expression_id, i.lang, i.idiom_text, i.english_gloss,
               i.explanation_en, i.audio_idiom_tgt, i.audio_idiom_en,
               i.audio_context, i.created_at,
               v.id AS video_id, v.youtube_id, v.title AS video_title,
               c.id AS channel_id, c.name AS channel_name,
               dup.n_reencounters
        FROM expression_idioms i
        LEFT JOIN videos v ON v.id = i.video_id
        LEFT JOIN channels c ON c.id = v.channel_id
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS n_reencounters FROM extraction_log
            WHERE duplicate_of = i.expression_id) dup ON TRUE
        {where}
        ORDER BY i.created_at DESC, i.id DESC
        LIMIT {arg(limit)} OFFSET {arg(offset)}
        """,
        *args)
    return {"total": total, "rows": [dict(r) for r in rows]}


@router.get("/expressions/{idiom_id}")
async def expression_detail(idiom_id: int, _: None = Depends(authed_ui)) -> dict:
    pool = await db.get_pool()
    r = await pool.fetchrow(
        """
        SELECT i.*, v.youtube_id, v.title AS video_title,
               c.id AS channel_id, c.name AS channel_name,
               e.added_at AS first_seen_at
        FROM expression_idioms i
        LEFT JOIN videos v ON v.id = i.video_id
        LEFT JOIN channels c ON c.id = v.channel_id
        LEFT JOIN expressions e ON e.id = i.expression_id
        WHERE i.id = $1
        """,
        idiom_id)
    if not r:
        raise HTTPException(404, "unknown idiom")
    d = dict(r)
    d["structured"] = _parse_structured(d.get("structured"))

    d["examples"] = [dict(x) for x in await pool.fetch(
        """
        SELECT ord, en_text, target_text, audio_en, audio_target
        FROM expression_examples WHERE idiom_id = $1 ORDER BY ord
        """,
        idiom_id)]

    # Duplicates map: which videos re-encountered this expression later.
    d["reencounters"] = [dict(x) for x in await pool.fetch(
        """
        SELECT el.created_at, el.phrase,
               v.id AS video_id, v.title AS video_title, v.youtube_id
        FROM extraction_log el
        LEFT JOIN videos v ON v.id = el.video_id
        WHERE el.duplicate_of = $1
        ORDER BY el.created_at DESC
        """,
        d["expression_id"])]
    return d


# --- channels --------------------------------------------------------------------

@router.get("/channels")
async def channels(_: None = Depends(authed_ui)) -> dict:
    pool = await db.get_pool()
    rows = await pool.fetch(
        """
        SELECT c.id, c.youtube_id, c.lang, c.name, c.active, c.priority,
               c.title_filter, c.min_duration_sec, c.max_duration_sec,
               c.added_at,
               COALESCE(vs.n_seen, 0)     AS videos_seen,
               COALESCE(vs.n_done, 0)     AS videos_done,
               COALESCE(vs.n_skipped, 0)  AS videos_skipped,
               COALESCE(vs.n_failed, 0)   AS videos_failed,
               COALESCE(vs.n_queued, 0)   AS videos_queued,
               vs.last_video_at,
               COALESCE(iy.n_idioms, 0)   AS idioms_yielded
        FROM channels c
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS n_seen,
                   COUNT(*) FILTER (WHERE status = 'done')    AS n_done,
                   COUNT(*) FILTER (WHERE status = 'skipped') AS n_skipped,
                   COUNT(*) FILTER (WHERE status = 'failed')  AS n_failed,
                   COUNT(*) FILTER (WHERE status IN ('queued', 'processing'))
                       AS n_queued,
                   MAX(first_seen) AS last_video_at
            FROM videos WHERE channel_id = c.id) vs ON TRUE
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS n_idioms
            FROM expression_idioms i
            JOIN videos v ON v.id = i.video_id
            WHERE v.channel_id = c.id) iy ON TRUE
        ORDER BY c.lang, c.name
        """)
    return {"rows": [dict(r) for r in rows]}


# --- delivery --------------------------------------------------------------------

@router.get("/delivery")
async def delivery(
    _: None = Depends(authed_ui),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    pool = await db.get_pool()
    settings = get_settings()
    total = await pool.fetchval("SELECT COUNT(*) FROM apkgs")
    rows = await pool.fetch(
        """
        SELECT a.id, a.lang, a.kind, a.filename, a.size_bytes, a.n_idioms,
               a.created_at,
               v.id AS video_id, v.title AS video_title, v.youtube_id,
               ack.status AS ack_status, ack.attempts AS ack_attempts,
               ack.acked_at, ag.name AS agent_name
        FROM apkgs a
        LEFT JOIN videos v ON v.id = a.video_id
        LEFT JOIN LATERAL (
            SELECT status, attempts, acked_at, agent_id FROM agent_acks
            WHERE apkg_id = a.id ORDER BY acked_at DESC LIMIT 1) ack ON TRUE
        LEFT JOIN agents ag ON ag.id = ack.agent_id
        ORDER BY a.created_at DESC
        LIMIT $1 OFFSET $2
        """,
        limit, offset)
    agents = [dict(r) for r in await pool.fetch(
        "SELECT id, name, langs, last_seen, created_at FROM agents")]
    return {
        "total": total,
        "rows": [dict(r) for r in rows],
        "agents": agents,
        "ack_retry_budget": settings.ack_retry_budget,
    }


# --- grammar (Wave 6: curriculum tree + unit detail) -------------------------

def _grammar_audio_rel(lang: str, item_id: int) -> str | None:
    """Relative path for the frontend audio player, or None when the item
    has no usable mp3 (TTS degraded to silence — ships text-only)."""
    p = (Path(get_settings().data_dir) / "staged_audio" / "grammar" / lang
         / f"idg_{lang}_{item_id}.mp3")
    if p.is_file() and p.stat().st_size > 1000:
        return f"grammar/{lang}/{p.name}"
    return None


@router.get("/grammar/overview")
async def grammar_overview(_: None = Depends(authed_ui)) -> dict:
    """The whole curriculum tree: per language → clusters → units with
    verified-vs-target counts, reject rates, last batch, plus the rolling
    deck's apkg + ack state (same join as the Delivery page) and the live
    generation-run state for button gating."""
    from .grammar import service as grammar_service
    from .grammar.curriculum import GRAMMAR_LANGS

    units = await db.grammar_units_with_counts()
    pool = await db.get_pool()
    decks = {r["lang"]: dict(r) for r in await pool.fetch(
        """
        SELECT a.id AS apkg_id, a.lang, a.size_bytes, a.n_idioms AS cards,
               a.created_at AS built_at,
               ack.status AS ack_status, ack.attempts AS ack_attempts,
               ack.acked_at, ag.name AS agent_name
        FROM apkgs a
        LEFT JOIN LATERAL (
            SELECT status, attempts, acked_at, agent_id FROM agent_acks
            WHERE apkg_id = a.id ORDER BY acked_at DESC LIMIT 1) ack ON TRUE
        LEFT JOIN agents ag ON ag.id = ack.agent_id
        WHERE a.kind = 'grammar'
        """)}

    langs = []
    for lang in GRAMMAR_LANGS:
        # Group by cluster NAME (units of one cluster are not necessarily
        # adjacent in sort_order — es_perfecto joined "1 Tiempos" late);
        # clusters sort by their numeric prefix ("1 …" < "2 …").
        by_cluster: dict[str, list[dict]] = {}
        for u in units:
            if u["lang"] == lang:
                by_cluster.setdefault(u["cluster"], []).append(u)
        langs.append({"lang": lang, "deck": decks.get(lang),
                      "clusters": [{"cluster": c, "units": by_cluster[c]}
                                   for c in sorted(by_cluster)]})
    return {"langs": langs, "lang_names": LANG_NAMES,
            "run": grammar_service.get_state()}


@router.get("/grammar/units/{key}")
async def grammar_unit_detail(key: str, _: None = Depends(authed_ui)) -> dict:
    """Unit meta + generation guidance + every verified item as card data
    (with audio availability) + the rejects with reasons — the LLM-error
    diagnostic that has caught every pipeline bug so far."""
    from .grammar.apkg import deck_name_for
    from .grammar.curriculum import topic_by_key

    units = await db.grammar_units_with_counts()
    unit = next((u for u in units if u["key"] == key), None)
    if unit is None:
        raise HTTPException(404, "unknown unit key")
    lang = unit["lang"]
    topic = topic_by_key(key)

    pool = await db.get_pool()
    items = [dict(r) for r in await pool.fetch(
        """
        SELECT id, infinitive, person, sentence, answer, gloss_en, why_en,
               batch, created_at
        FROM grammar_items
        WHERE lang = $1 AND topic = $2 AND status = 'verified'
        ORDER BY id
        """,
        lang, key)]
    for it in items:
        it["audio"] = _grammar_audio_rel(lang, it["id"])

    return {
        "unit": unit,
        "guidance": topic.guidance if topic else None,
        "deck_name": deck_name_for(lang, unit["cluster"]),
        "items": items,
        "rejects": await db.fetch_grammar_rejects(lang, key, limit=200),
    }


@router.get("/audio/grammar/{lang}/{filename}")
async def grammar_audio(
    lang: str, filename: str,
    x_admin_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    """Stream one grammar drill mp3 from staged_audio/grammar/<lang>/.
    Same auth + strict path validation as the idiom audio route."""
    _check_token(x_admin_token or token)
    # 'podcasts' rides the grammar audio tree as a pseudo-language: the
    # season MP3s live in staged_audio/grammar/podcasts/.
    if (not re.fullmatch(r"[a-z]{2}|podcasts", lang)
            or not _AUDIO_FILE_RE.fullmatch(filename)):
        raise HTTPException(400, "bad path")
    p = (Path(get_settings().data_dir) / "staged_audio" / "grammar"
         / lang / filename)
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(p, media_type="audio/mpeg")


# --- rescue lab (read-only; mutations go through /admin/rescue/*) ------------

def _rescue_json(d: dict) -> dict:
    for col in ("struggle_snapshot", "params"):
        if col in d:
            d[col] = _parse_structured(d.get(col))
    for col in ("cost_usd", "spend"):
        if d.get(col) is not None:
            d[col] = float(d[col])
    return d


@router.get("/rescue/items")
async def rescue_items(
    _: None = Depends(authed_ui),
    lang: str | None = None,
    status: str | None = None,
) -> dict:
    conds, args = [], []

    def arg(v) -> str:
        args.append(v)
        return f"${len(args)}"

    if lang:
        conds.append(f"i.lang = {arg(lang)}")
    if status:
        conds.append(f"i.status = {arg(status)}")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    pool = await db.get_pool()
    rows = await pool.fetch(
        f"""
        SELECT i.id, i.lang, i.idiom, i.gloss, i.anchor, i.status, i.strike,
               i.glyph_asset_id, i.struggle_snapshot, i.created_at,
               i.updated_at,
               a.n_assets, a.n_approved, a.n_draft,
               COALESCE(l.spend, 0) AS spend,
               s.n_senses
        FROM rescue_items i
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS n_assets,
                   COUNT(*) FILTER (WHERE status = 'approved') AS n_approved,
                   COUNT(*) FILTER (WHERE status = 'draft') AS n_draft
            FROM rescue_assets WHERE item_id = i.id) a ON TRUE
        LEFT JOIN LATERAL (
            SELECT SUM(cost_usd) AS spend
            FROM gen_ledger WHERE item_id = i.id) l ON TRUE
        LEFT JOIN LATERAL (
            SELECT COUNT(*) AS n_senses
            FROM rescue_senses WHERE item_id = i.id) s ON TRUE
        {where}
        ORDER BY (i.status = 'retired'), i.updated_at DESC
        """,
        *args)
    return {"rows": [_rescue_json(dict(r)) for r in rows],
            "lang_names": LANG_NAMES}


@router.get("/rescue/item/{item_id}")
async def rescue_item_detail(
    item_id: int, _: None = Depends(authed_ui),
) -> dict:
    from . import rescue
    pool = await db.get_pool()
    row = await pool.fetchrow(
        """
        SELECT i.*, COALESCE(l.spend, 0) AS spend
        FROM rescue_items i
        LEFT JOIN LATERAL (
            SELECT SUM(cost_usd) AS spend
            FROM gen_ledger WHERE item_id = i.id) l ON TRUE
        WHERE i.id = $1
        """, item_id)
    if not row:
        raise HTTPException(404, "unknown item")
    item = _rescue_json(dict(row))
    senses = [dict(r) for r in await pool.fetch(
        "SELECT id, label, gloss, example_tl, example_en, ord "
        "FROM rescue_senses WHERE item_id = $1 ORDER BY ord", item_id)]
    assets = [_rescue_json(dict(r)) for r in await pool.fetch(
        "SELECT * FROM rescue_assets WHERE item_id = $1 "
        "ORDER BY format, created_at DESC", item_id)]

    # Server-side canonical template fill for the Generate panel's
    # prefill — the same code path the generate endpoint uses, so what
    # the user sees is what would run.
    prompts: dict[str, dict] = {}
    for fmt in rescue.IMAGE_FORMATS:
        try:
            prompts[fmt] = {"prompt": rescue.fill_template(fmt, item, senses)}
        except ValueError as e:
            prompts[fmt] = {"error": str(e)}
    return {"item": item, "senses": senses, "assets": assets,
            "prompts": prompts, "lang_names": LANG_NAMES}


@router.get("/rescue/costs")
async def rescue_costs(_: None = Depends(authed_ui)) -> dict:
    """Cost aggregates off gen_ledger — every paid call, including ones
    whose asset was later discarded (asset_id NULL after delete)."""
    pool = await db.get_pool()
    totals = await pool.fetchrow(
        """
        SELECT COALESCE(SUM(cost_usd), 0) AS all_time,
               COALESCE(SUM(cost_usd) FILTER (
                   WHERE created_at >= date_trunc('month', NOW())), 0)
                   AS this_month,
               COUNT(*) AS n_calls
        FROM gen_ledger
        """)
    by_day = [dict(r) for r in await pool.fetch(
        """
        SELECT created_at::date AS day, SUM(cost_usd) AS usd, COUNT(*) AS n
        FROM gen_ledger
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY 1 ORDER BY 1
        """)]
    by_provider = [dict(r) for r in await pool.fetch(
        """
        SELECT provider, model, SUM(cost_usd) AS usd, COUNT(*) AS n,
               SUM(cost_usd) FILTER (
                   WHERE created_at >= date_trunc('month', NOW())) AS usd_month
        FROM gen_ledger GROUP BY 1, 2 ORDER BY 3 DESC
        """)]
    by_format = [dict(r) for r in await pool.fetch(
        """
        SELECT COALESCE(a.format, 'discarded') AS format,
               SUM(g.cost_usd) AS usd, COUNT(*) AS n
        FROM gen_ledger g
        LEFT JOIN rescue_assets a ON a.id = g.asset_id
        GROUP BY 1 ORDER BY 2 DESC
        """)]

    def _f(rows: list[dict]) -> list[dict]:
        for r in rows:
            for k in ("usd", "usd_month"):
                if k in r:
                    r[k] = float(r[k] or 0)
        return rows

    return {
        "this_month": float(totals["this_month"]),
        "all_time": float(totals["all_time"]),
        "n_calls": totals["n_calls"],
        "by_day": _f(by_day),
        "by_provider": _f(by_provider),
        "by_format": _f(by_format),
    }


@router.get("/rescue/formats")
async def rescue_formats(_: None = Depends(authed_ui)) -> dict:
    """The format taxonomy + provider registry, for the Formats page and
    the Generate panel (provider dropdown with per-image cost estimates
    shown BEFORE the call)."""
    from . import genmedia, rescue
    formats = [
        {"key": key, **{k: v for k, v in spec.items()},
         "placeholders": rescue.format_placeholders(key)}
        for key, spec in rescue.FORMATS.items()
    ]
    providers = [
        {"key": key, "api": info["api"], "model": info["model"],
         "label": info["label"], "usd_per_image": info["usd_per_image"]}
        for key, info in genmedia.PROVIDERS.items()
    ]
    return {"formats": formats, "providers": providers,
            "image_formats": list(rescue.IMAGE_FORMATS)}


@router.get("/rescue/asset-file/{asset_id}")
async def rescue_asset_file(
    asset_id: int,
    x_admin_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    """Stream one rescue asset file (same auth pattern as the audio
    streamer: header or ?token= for direct <img>/<a> links)."""
    _check_token(x_admin_token or token)
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT file_path, mime FROM rescue_assets WHERE id = $1", asset_id)
    if not row or not row["file_path"]:
        raise HTTPException(404, "not found")
    root = (Path(get_settings().data_dir) / "rescue_assets").resolve()
    p = (root / row["file_path"]).resolve()
    if not p.is_relative_to(root):
        raise HTTPException(400, "bad path")
    if not p.is_file():
        raise HTTPException(404, "file gone")
    return FileResponse(p, media_type=row["mime"] or "application/octet-stream")


# --- context-clip upload (local alignment pipeline) -------------------------

@router.post("/upload-context/{idiom_id}")
async def upload_context(
    idiom_id: int,
    request: Request,
    _: None = Depends(authed_ui),
) -> dict:
    """Store a locally-aligned context clip for one idiom and point
    audio_context at it. Body: raw mp3 bytes (Content-Type: audio/mpeg).
    Used by the offline whisper-alignment runner — Gemini's audio
    timestamps proved too noisy for backfilling old videos, so the clips
    are cut on the operator's machine from whisper word timestamps and
    pushed up here."""
    pool = await db.get_pool()
    row = await pool.fetchrow(
        """
        SELECT i.id, v.youtube_id FROM expression_idioms i
        JOIN videos v ON v.id = i.video_id WHERE i.id = $1
        """,
        idiom_id)
    if not row:
        raise HTTPException(404, "unknown idiom")
    body = await request.body()
    if len(body) < 2000 or len(body) > 8_000_000:
        raise HTTPException(400, "clip size out of range")
    if not (body[:3] == b"ID3" or body[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
        raise HTTPException(400, "not an mp3")
    stage_dir = (Path(get_settings().data_dir) / "staged_audio"
                 / row["youtube_id"])
    stage_dir.mkdir(parents=True, exist_ok=True)
    name = f"context_lc_{idiom_id}.mp3"
    (stage_dir / name).write_bytes(body)
    rel = f"{row['youtube_id']}/{name}"
    await pool.execute(
        "UPDATE expression_idioms SET audio_context = $2 WHERE id = $1",
        idiom_id, rel)
    return {"ok": True, "audio_context": rel}


# --- audio streaming ---------------------------------------------------------------

# Same strict validation pattern as /admin/audio-sample: Starlette decodes
# %2F/%2E in path params, so these must be checked before touching the fs.
_YTID_RE = re.compile(r"^[A-Za-z0-9_-]{5,20}$")
_AUDIO_FILE_RE = re.compile(r"^(?!.*\.\.)[A-Za-z0-9._-]+\.mp3$")


@router.get("/audio/{youtube_id}/{filename}")
async def audio(
    youtube_id: str, filename: str,
    x_admin_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    """Stream one staged per-card mp3. Accepts the admin token either as
    the X-Admin-Token header or as ?token= (browser <audio> elements can't
    set headers)."""
    _check_token(x_admin_token or token)
    if not _YTID_RE.fullmatch(youtube_id) or not _AUDIO_FILE_RE.fullmatch(filename):
        raise HTTPException(400, "bad path")
    p = Path(get_settings().data_dir) / "staged_audio" / youtube_id / filename
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(p, media_type="audio/mpeg")
