"""FastAPI app — exposes the agent-pull endpoints AND spawns the worker loop.

One service does both: FastAPI handlers serve the local Anki agent at
/apkgs/*, and an asyncio background task runs `worker.loop()` to drain the
videos queue. They share the Postgres pool and the /data disk.

M1: skeletal handlers + worker startup hook. Real implementations land in M2/M5.
"""

from __future__ import annotations

import asyncio
import contextlib
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
