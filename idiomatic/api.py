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

from . import db
from .settings import get_settings
from .worker import loop as worker_loop

log = structlog.get_logger()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the worker loop on app boot; cancel on shutdown."""
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
    """Apkgs in this agent's langs that haven't been acked by this agent yet."""
    pool = await db.get_pool()
    rows = await pool.fetch(
        """
        SELECT a.id, a.lang, a.filename, a.size_bytes, a.n_idioms, a.created_at,
               v.youtube_id, v.title
        FROM apkgs a
        LEFT JOIN videos v ON v.id = a.video_id
        WHERE a.lang = ANY($1::text[])
          AND NOT EXISTS (
              SELECT 1 FROM agent_acks ak
              WHERE ak.agent_id = $2 AND ak.apkg_id = a.id
          )
        ORDER BY a.created_at
        LIMIT 50
        """,
        agent["langs"], agent["id"],
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
        ON CONFLICT (agent_id, apkg_id) DO UPDATE SET status = $3, acked_at = NOW()
        """,
        agent["id"], apkg_id, status,
    )
    return {"ok": True}


# --- health ----------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    pool = await db.get_pool()
    n = await pool.fetchval("SELECT COUNT(*) FROM videos WHERE status = 'queued'")
    return {"ok": True, "queued_videos": n}


# --- admin: backfill pool source data from existing per-video apkgs ---------
# One-shot operation triggered manually.

@app.post("/admin/backfill")
async def admin_backfill(_: None = Depends(authed_admin)) -> dict:
    """Kick off a background backfill of expression_idioms + examples + audio
    from every per-video apkg under /data/apkgs/. Returns immediately;
    poll /admin/backfill/status for progress."""
    from . import backfill
    if backfill.get_state()["running"]:
        return {"started": False, "reason": "already running"}
    asyncio.create_task(backfill.run_backfill())
    return {"started": True}


@app.get("/admin/backfill/status")
async def admin_backfill_status(
    _: None = Depends(authed_admin),
) -> dict:
    from . import backfill
    return backfill.get_state()


# --- admin: audio audit (read mp3 metadata to verify TTS output) -----------

@app.get("/admin/audio-audit")
async def admin_audio_audit(
    _: None = Depends(authed_admin),
) -> dict:
    """Walks /data/staged_audio, returns per-language file count + size
    histogram. Anything < 5 KB is almost certainly a silence placeholder."""
    import subprocess
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


# --- admin: backfill v2 (trigger sentence + explanation for existing rows) -

@app.post("/admin/backfill-v2")
async def admin_backfill_v2(_: None = Depends(authed_admin)) -> dict:
    from . import backfill_v2
    if backfill_v2.get_state()["running"]:
        return {"started": False, "reason": "already running"}
    asyncio.create_task(backfill_v2.run_backfill_v2())
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

    asyncio.create_task(_run())
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
