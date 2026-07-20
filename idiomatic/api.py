"""FastAPI app — exposes the agent-pull endpoints AND spawns the worker loop.

One service does both: FastAPI handlers serve the local Anki agent at
/apkgs/*, and an asyncio background task runs `worker.loop()` to drain the
videos queue. They share the Postgres pool and the /data disk.

M1: skeletal handlers + worker startup hook. Real implementations land in M2/M5.
"""

from __future__ import annotations

import asyncio
import contextlib
import re
import secrets
from pathlib import Path

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db
from . import ui_api
from .settings import get_settings
from .worker import loop as worker_loop

log = structlog.get_logger()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the worker loop on app boot; cancel on shutdown."""
    # Apply the idempotent schema first so new tables/columns exist before
    # the worker claims anything. Non-fatal: a hiccup here must not take
    # the delivery endpoints down (extraction_log writes are best-effort).
    try:
        await db.apply_schema()
    except Exception as e:
        log.warning("api.schema_apply_failed", err=repr(e)[:300])
    worker_task = asyncio.create_task(worker_loop(once=False))
    log.info("api.lifespan.started", worker_task=str(worker_task))
    try:
        yield
    finally:
        worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker_task
        await db.close_pool()
        log.info("api.lifespan.shutdown")


app = FastAPI(title="idiomatic", version="0.1.0", lifespan=lifespan)
app.include_router(ui_api.router)

# Strong refs for fire-and-forget admin tasks. The event loop only keeps a
# weak reference to tasks, so an unreferenced long-running backfill can be
# garbage-collected mid-run (documented asyncio pitfall).
_bg_tasks: set[asyncio.Task] = set()


def _spawn_bg(coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
    return task


# --- agent auth -------------------------------------------------------------

async def authed_agent(x_agent_token: str | None = Header(default=None)) -> dict:
    if not x_agent_token:
        raise HTTPException(401, "missing X-Agent-Token")
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT id, name, langs FROM agents WHERE token = $1", x_agent_token,
    )
    if not row:
        raise HTTPException(401, "unknown agent")
    await pool.execute("UPDATE agents SET last_seen = NOW() WHERE id = $1", row["id"])
    return dict(row)


# --- admin auth ---------------------------------------------------------------
# Separate credential from the agent tokens: an agent token only grants
# /apkgs/* (pull + ack); ADMIN_TOKEN (env) is required for /admin/*.

async def authed_admin(x_admin_token: str | None = Header(default=None)) -> None:
    admin_token = get_settings().admin_token
    if not admin_token:
        raise HTTPException(503, "admin endpoints disabled (ADMIN_TOKEN unset)")
    if not x_admin_token or not secrets.compare_digest(x_admin_token, admin_token):
        raise HTTPException(401, "bad admin token")


# --- agent endpoints --------------------------------------------------------

@app.get("/apkgs/pending")
async def list_pending(agent: dict = Depends(authed_agent)) -> list[dict]:
    """Apkgs in this agent's langs not yet delivered to this agent.

    Failed acks are transient (network blip, locked collection), so a
    failed-acked apkg is re-offered until its attempts hit the retry
    budget — only an 'ok' ack (or budget exhaustion) is final."""
    pool = await db.get_pool()
    rows = await pool.fetch(
        """
        SELECT a.id, a.lang, a.filename, a.size_bytes, a.n_idioms, a.created_at,
               v.youtube_id, v.title
        FROM apkgs a
        LEFT JOIN videos v ON v.id = a.video_id
        LEFT JOIN agent_acks ak ON ak.agent_id = $2 AND ak.apkg_id = a.id
        WHERE a.lang = ANY($1::text[])
          AND (ak.apkg_id IS NULL
               OR (ak.status = 'failed' AND ak.attempts < $3))
        ORDER BY a.created_at
        LIMIT 50
        """,
        agent["langs"], agent["id"], get_settings().ack_retry_budget,
    )
    return [dict(r) for r in rows]


@app.get("/apkgs/{apkg_id}/download")
async def download(apkg_id: int, agent: dict = Depends(authed_agent)) -> FileResponse:
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT lang, filename FROM apkgs WHERE id = $1", apkg_id,
    )
    if not row or row["lang"] not in agent["langs"]:
        raise HTTPException(404, "not found")
    settings = get_settings()
    path = Path(settings.data_dir) / row["filename"]
    if not path.exists():
        raise HTTPException(410, "file gone")
    return FileResponse(path, media_type="application/octet-stream",
                         filename=row["filename"])


@app.post("/apkgs/{apkg_id}/ack")
async def ack(apkg_id: int, status: str = "ok",
              agent: dict = Depends(authed_agent)) -> dict:
    if status not in ("ok", "failed"):
        raise HTTPException(400, "status must be ok|failed")
    pool = await db.get_pool()
    await pool.execute(
        """
        INSERT INTO agent_acks (agent_id, apkg_id, status)
        VALUES ($1, $2, $3)
        ON CONFLICT (agent_id, apkg_id) DO UPDATE SET
            status = $3,
            acked_at = NOW(),
            attempts = agent_acks.attempts + 1
        """,
        agent["id"], apkg_id, status,
    )
    return {"ok": True}


# --- health ----------------------------------------------------------------

@app.get("/agent/digest")
async def agent_digest(agent: dict = Depends(authed_agent)) -> dict:
    """Tiny liveness digest the Anki add-on polls alongside /apkgs/pending.
    'stalled' means: work is queued but nothing has been produced for 6+
    hours — the signature of a wedged worker (this exact class of outage
    has happened twice; /health alone can't see it)."""
    pool = await db.get_pool()
    queued = await pool.fetchval(
        "SELECT COUNT(*) FROM videos WHERE status = 'queued'")
    latest = await pool.fetchval("SELECT MAX(created_at) FROM apkgs")
    import datetime as _dt
    age_h = None
    if latest is not None:
        age_h = round((_dt.datetime.now(_dt.timezone.utc) - latest
                       ).total_seconds() / 3600, 1)
    return {
        "queued_videos": queued,
        "latest_apkg_age_hours": age_h,
        "stalled": bool(queued and age_h is not None and age_h > 6),
    }


@app.get("/health")
async def health() -> dict:
    pool = await db.get_pool()
    n = await pool.fetchval("SELECT COUNT(*) FROM videos WHERE status = 'queued'")
    return {"ok": True, "queued_videos": n}


# --- admin: audio audit (read mp3 metadata to verify TTS output) -----------

@app.get("/admin/audio-audit")
async def admin_audio_audit(
    _: None = Depends(authed_admin),
) -> dict:
    """Walks /data/staged_audio, returns per-language file count + size
    histogram. Anything < 5 KB is almost certainly a silence placeholder."""
    settings = get_settings()
    root = Path(settings.data_dir) / "staged_audio"
    out: dict = {}
    if not root.exists():
        return {"error": "no staged_audio dir", "root": str(root)}
    # videos table maps youtube_id → lang
    pool = await db.get_pool()
    yid_to_lang = {r["youtube_id"]: r["lang"] for r in
                   await pool.fetch("SELECT youtube_id, lang FROM videos")}
    for video_dir in sorted(root.iterdir()):
        if not video_dir.is_dir():
            continue
        lang = yid_to_lang.get(video_dir.name, "?")
        by_kind: dict = {}
        for f in sorted(video_dir.glob("*.mp3")):
            kind = (f.name.split("_")[0]
                    + ("_" + f.name.split("_")[1] if f.name.startswith("ex_")
                       else "_" + f.name.split("_")[1].rstrip(".mp3")
                       if "_" in f.name else ""))
            # crude bucketing
            if f.name.startswith("idiom_tgt_"):
                kind = "idiom_tgt"
            elif f.name.startswith("idiom_en_"):
                kind = "idiom_en"
            elif f.name.startswith("ex_") and f.name.endswith("_en.mp3"):
                kind = "ex_en"
            elif f.name.startswith("ex_") and f.name.endswith("_tgt.mp3"):
                kind = "ex_tgt"
            else:
                kind = "other"
            by_kind.setdefault(kind, [])
            by_kind[kind].append(f.stat().st_size)
        summary = {}
        for k, sizes in by_kind.items():
            sizes.sort()
            tiny = sum(1 for s in sizes if s < 5000)
            summary[k] = {
                "n": len(sizes),
                "min": sizes[0], "max": sizes[-1],
                "median": sizes[len(sizes)//2],
                "tiny_under_5kb": tiny,
            }
        out.setdefault(lang, {})[video_dir.name] = summary
    return out


# Starlette decodes %2F/%2E in path params, so these must be validated
# before they touch the filesystem — a crafted segment could otherwise
# traverse out of staged_audio.
_YTID_RE = re.compile(r"^[A-Za-z0-9_-]{5,20}$")
_AUDIO_FILE_RE = re.compile(r"^(?!.*\.\.)[A-Za-z0-9._-]+\.mp3$")


@app.get("/admin/audio-sample/{youtube_id}/{filename}")
async def admin_audio_sample(
    youtube_id: str, filename: str,
    _: None = Depends(authed_admin),
):
    """Stream a specific staged_audio file. Use to listen to a sample."""
    if not _YTID_RE.fullmatch(youtube_id) or not _AUDIO_FILE_RE.fullmatch(filename):
        raise HTTPException(400, "bad path")
    settings = get_settings()
    p = Path(settings.data_dir) / "staged_audio" / youtube_id / filename
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(p, media_type="audio/mpeg")


# --- admin: re-TTS silence placeholders in staged_audio --------------------

@app.post("/admin/retts")
async def admin_retts(_: None = Depends(authed_admin)) -> dict:
    """Re-synthesize every staged audio file that is a silence placeholder
    (< 5 KB). Background; poll /admin/retts/status. Run
    /admin/rebuild-pools per language afterwards to bake healed audio
    into the pool decks."""
    from . import retts
    if retts.get_state().get("running"):
        return {"started": False, "reason": "already running"}
    _spawn_bg(retts.run_retts())
    return {"started": True}


@app.get("/admin/retts/status")
async def admin_retts_status(_: None = Depends(authed_admin)) -> dict:
    from . import retts
    return retts.get_state()


# --- admin: backfill v2 (trigger sentence + explanation for existing rows) -

@app.post("/admin/backfill-v2")
async def admin_backfill_v2(_: None = Depends(authed_admin)) -> dict:
    from . import backfill_v2
    if backfill_v2.get_state()["running"]:
        return {"started": False, "reason": "already running"}
    _spawn_bg(backfill_v2.run_backfill_v2())
    return {"started": True}


@app.get("/admin/backfill-v2/status")
async def admin_backfill_v2_status(
    _: None = Depends(authed_admin),
) -> dict:
    from . import backfill_v2
    return backfill_v2.get_state()


@app.post("/admin/rebuild-pools")
async def admin_rebuild_pools(
    lang: str, _: None = Depends(authed_admin),
) -> dict:
    """Force a pool rebuild for one language, bypassing the 30-min
    debounce. Runs in the background (a big language re-stitches a lot of
    audio); watch the pool.* log lines for the result."""
    from .pipeline import pool as pool_mod

    async def _run() -> None:
        try:
            stats = await pool_mod.rebuild_pools(lang, force=True)
            log.info("admin.rebuild_pools.done", **stats)
        except Exception as e:
            log.warning("admin.rebuild_pools.failed", lang=lang,
                         err=repr(e)[:200])

    _spawn_bg(_run())
    return {"started": True, "lang": lang, "forced": True}


@app.get("/admin/video-info")
async def admin_video_info(
    youtube_id: str, agent: dict = Depends(authed_agent),
) -> dict:
    """Lookup by youtube_id — used by the Anki add-on's Reorganize step
    to answer 'what date should I prefix this deck with?'

    Deliberately agent-authed (not admin): the add-on calls it with its
    agent token, and it exposes nothing beyond video metadata the agent
    can already see via /apkgs/pending."""
    pool = await db.get_pool()
    row = await pool.fetchrow(
        """
        SELECT title, lang, first_seen::date AS first_seen_date
        FROM videos WHERE youtube_id = $1
        """,
        youtube_id,
    )
    if not row:
        raise HTTPException(404, "unknown youtube_id")
    return {
        "youtube_id": youtube_id,
        "title": row["title"],
        "lang": row["lang"],
        "first_seen_date": row["first_seen_date"].isoformat()
        if row["first_seen_date"] else None,
    }


# --- admin: rotate an agent's bearer token ----------------------------------

@app.post("/admin/rotate-agent-token")
async def admin_rotate_agent_token(
    body: dict, _: None = Depends(authed_admin),
) -> dict:
    """Set a new bearer token for one agent (by name). Used to kill
    tokens that leaked into git history. The add-on 401s until its local
    config.json carries the new value; failed acks retry, so a short
    window is harmless."""
    name, new_token = body.get("name"), body.get("new_token")
    if not name or not new_token or len(new_token) < 16:
        raise HTTPException(400, "need name + new_token (>= 16 chars)")
    pool = await db.get_pool()
    result = await pool.execute(
        "UPDATE agents SET token = $2 WHERE name = $1", name, new_token)
    if result.split()[-1] == "0":
        raise HTTPException(404, "unknown agent name")
    return {"ok": True, "agent": name}


# --- dashboard SPA (must be registered LAST — the catch-all would otherwise
# shadow the API routes above; FastAPI matches in registration order) --------

_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"),
              name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        """Serve the built dashboard; client-side routing gets index.html.
        Unknown API-ish paths still 404 as JSON instead of returning HTML."""
        if full_path.split("/", 1)[0] in ("ui", "apkgs", "admin", "agent",
                                           "health", "assets"):
            raise HTTPException(404, "not found")
        candidate = (_FRONTEND_DIST / full_path).resolve()
        if (full_path and candidate.is_file()
                and candidate.is_relative_to(_FRONTEND_DIST)):
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST / "index.html")
else:
    log.warning("api.frontend_dist_missing", path=str(_FRONTEND_DIST))
