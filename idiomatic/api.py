"""FastAPI app — exposes the agent-pull endpoints AND spawns the worker loop.

One service does both: FastAPI handlers serve the local Anki agent at
/apkgs/*, and an asyncio background task runs `worker.loop()` to drain the
videos queue. They share the Postgres pool and the /data disk.

M1: skeletal handlers + worker startup hook. Real implementations land in M2/M5.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import re
import secrets
from pathlib import Path
from typing import Any

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
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
    # Re-seed grammar_units from curriculum code (the definition source);
    # only code-owned columns are overwritten — see db.seed_grammar_units.
    try:
        from .grammar.curriculum import OBSOLETE_UNIT_KEYS, unit_seed_rows
        await db.seed_grammar_units(
            unit_seed_rows(), obsolete_keys=OBSOLETE_UNIT_KEYS,
        )
    except Exception as e:
        log.warning("api.grammar_units_seed_failed", err=repr(e)[:300])
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


@app.get("/admin/anki-guids")
async def admin_anki_guids(_: None = Depends(authed_admin)) -> dict:
    """Every note guid the CURRENT catalog generates, per kind — computed
    with the builders' own _guid/_norm code so a client can diff its
    Anki collection against the live content (orphan detection)."""
    from .pipeline import adoption
    return await adoption.current_guids()


@app.post("/admin/adopt-orphans")
async def admin_adopt_orphans(
    body: dict, _: None = Depends(authed_admin),
) -> dict:
    """Upsert studied orphan notes from the user's collection into
    adopted_notes. Body: {"notes": [{guid, lang, model, deck, fields,
    tags, reps, lapses, last_review_ms}, ...]}."""
    from .pipeline import adoption
    notes = body.get("notes")
    if not isinstance(notes, list) or not notes:
        raise HTTPException(400, "need a non-empty notes list")
    n = await adoption.adopt_notes(notes)
    return {"adopted": n, "received": len(notes)}


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


# --- admin: grammar drills (docs/GRAMMAR_STRATEGY.md) ----------------------

@app.post("/admin/f3-convert")
async def admin_f3_convert(
    lang: str, n: int = 20, _: None = Depends(authed_admin),
) -> dict:
    """Turn teacher-attested personal errors into verified F3 cards.

    This is a bounded synchronous DB operation.  Rebuilding the rolling
    grammar deck remains an explicit, separate admin action.
    """
    from .grammar import f3

    if lang not in f3.TOPIC_BY_LANG:
        raise HTTPException(400, "lang must be fr|pt|es|it|de")
    if not 1 <= n <= 200:
        raise HTTPException(400, "n must be 1..200")
    return await f3.convert(lang, n)


@app.post("/admin/f4-convert")
async def admin_f4_convert(
    lang: str, n: int = 20, _: None = Depends(authed_admin),
) -> dict:
    """Compile reviewed private interference pairs into verified F4 cards.

    Like F3 conversion, this is bounded synchronous DB work and deliberately
    does not rebuild the rolling grammar deck. German pair data may be staged,
    but its one-row bank has no curriculum unit and is not convertible yet.
    """
    from .grammar import f4

    if lang not in f4.TOPIC_BY_LANG:
        raise HTTPException(400, "lang must be es|pt|fr|it")
    if not 1 <= n <= 200:
        raise HTTPException(400, "n must be 1..200")
    return await f4.convert(lang, n)


@app.post("/admin/grammar-generate")
async def admin_grammar_generate(
    lang: str = "es", n_per_topic: int = 12, topic: str | None = None,
    _: None = Depends(authed_admin),
) -> dict:
    """Generate + verify a batch of grammar drill items and rebuild the
    lang's rolling grammar deck. Background; poll /admin/grammar-status."""
    from .grammar import service as grammar_service
    from .grammar.curriculum import topic_by_key

    if topic:
        requested = {key.strip() for key in topic.split(",") if key.strip()}
        static_topics = {
            key for key in requested
            if (unit := topic_by_key(key)) is not None
            and unit.verify in ("attested", "f4")
        }
        if static_topics:
            raise HTTPException(
                409,
                "static F3/F4 units are filled via their conversion endpoints, "
                "not LLM generation",
            )
    if not grammar_service.claim_grammar_job(lang, "generation"):
        return {"started": False, "reason": "already running",
                **grammar_service.get_state()}
    _spawn_bg(grammar_service.run_generation(
        lang, n_per_topic, topic, claimed=True))
    return {"started": True, "lang": lang, "n_per_topic": n_per_topic,
            "topic": topic}


@app.get("/admin/grammar-status")
async def admin_grammar_status(_: None = Depends(authed_admin)) -> dict:
    from .grammar import service as grammar_service
    return grammar_service.get_state()


@app.post("/admin/explainers-build")
async def admin_explainers_build(
    lang: str, _: None = Depends(authed_admin),
) -> dict:
    """TTS, stitch, and upsert one language's authored grammar-radio cards.

    Background; poll /admin/grammar-status.  Packaging/delivery deliberately
    stays a separate explicit POST to /admin/grammar-rebuild.
    """
    from .grammar import service as grammar_service
    from .grammar.explainers import SUPPORTED_LANGS

    if lang not in SUPPORTED_LANGS:
        raise HTTPException(400, "lang must be fr|pt|es|de")
    if not grammar_service.claim_explainer_build(lang):
        return {"started": False, "reason": "already running",
                **grammar_service.get_state()}
    _spawn_bg(grammar_service.run_explainer_build(lang, claimed=True))
    return {"started": True, "lang": lang, "deck_rebuild": "separate"}


@app.get("/admin/grammar-stats")
async def admin_grammar_stats(
    lang: str = "es", _: None = Depends(authed_admin),
) -> dict:
    """Per-topic verified/rejected counts — the LLM error rate per topic
    is a first-class metric here."""
    return {"lang": lang, "topics": await db.grammar_topic_stats(lang)}


@app.get("/admin/grammar-rejects")
async def admin_grammar_rejects(
    lang: str = "es", topic: str | None = None, limit: int = 50,
    _: None = Depends(authed_admin),
) -> dict:
    """Rejected items with reasons — for diagnosing weak generator units
    (e.g. the Wave-1 es_cmd_tu 15/24 rejection finding)."""
    return {"lang": lang, "topic": topic,
            "rejects": await db.fetch_grammar_rejects(lang, topic, limit)}


@app.post("/admin/grammar-rebuild")
async def admin_grammar_rebuild(
    lang: str = "es", _: None = Depends(authed_admin),
) -> dict:
    """Rebuild + re-deliver the grammar deck from existing verified items
    (no generation) — e.g. after a template change deploy. Background:
    TTS for a full deck takes minutes; poll /admin/grammar-status."""
    from .grammar import service as grammar_service
    if not grammar_service.claim_grammar_job(lang, "rebuild"):
        return {"started": False, "reason": "already running",
                **grammar_service.get_state()}

    async def _run() -> None:
        try:
            result = await grammar_service.rebuild_grammar_deck(lang)
            grammar_service._state["deck"] = result
        except Exception as e:  # noqa: BLE001
            log.warning("admin.grammar_rebuild.failed", lang=lang,
                         err=repr(e)[:200])
            grammar_service._state["error"] = repr(e)[:200]
        finally:
            grammar_service._state["running"] = False

    _spawn_bg(_run())
    return {"started": True, "lang": lang}


@app.get("/admin/grammar-deckmap")
async def admin_grammar_deckmap(agent: dict = Depends(authed_agent)) -> dict:
    """unit tag → full Anki deck name, for the add-on's one-shot
    'Reorganize grammar decks' step (cards carry their unit key as a tag;
    this is the join key). Deliberately agent-authed like /admin/video-info
    — the add-on only holds the agent token, and the map exposes nothing
    beyond deck naming."""
    from .grammar.apkg import MODEL_NAME, deck_name_for
    from .grammar.curriculum import GRAMMAR_LANGS, topics_for
    from .grammar.explainers import EXPLAINER_UNITS
    deckmap = {
        t.key: deck_name_for(lang, t.cluster)
        for lang in GRAMMAR_LANGS
        for t in topics_for(lang)
    }
    deckmap.update({
        unit.topic: deck_name_for(lang, unit.cluster)
        for lang, unit in EXPLAINER_UNITS.items()
    })
    return {"model_name": MODEL_NAME, "map": deckmap}


@app.post("/admin/grammar-unit/{key}")
async def admin_grammar_unit(
    key: str, patch: dict, _: None = Depends(authed_admin),
) -> dict:
    """Patch a unit's user-mutable state from the dashboard. Body JSON:
    {target_size?, status?, notes?}."""
    allowed = {"target_size", "status", "notes"}
    unknown = set(patch) - allowed
    if unknown:
        raise HTTPException(400, f"unknown fields: {sorted(unknown)}")
    status = patch.get("status")
    if status is not None and status not in ("active", "maintenance", "planned"):
        raise HTTPException(400, "status must be active|maintenance|planned")
    target = patch.get("target_size")
    if target is not None and not (isinstance(target, int) and 0 < target <= 100):
        raise HTTPException(400, "target_size must be an int in 1..100")
    row = await db.update_grammar_unit(
        key, target_size=target, status=status, notes=patch.get("notes"))
    if row is None:
        raise HTTPException(404, "unknown unit key")
    return {"ok": True, "unit": row}


@app.post("/admin/grammar-topup/{key}")
async def admin_grammar_topup(
    key: str, _: None = Depends(authed_admin),
) -> dict:
    """Generate target_size - current_verified items for one unit, then
    rebuild the language's deck. Background; poll /admin/grammar-status.
    The per-unit sizing knob (docs/GRAMMAR_STRATEGY.md Wave 6) — targets
    are hand-set for now, mastery-driven after Wave 5."""
    from .grammar import service as grammar_service
    from .grammar.curriculum import topic_by_key
    if grammar_service.get_state().get("running"):
        return {"started": False, "reason": "already running",
                **grammar_service.get_state()}
    topic = topic_by_key(key)
    if topic is None:
        raise HTTPException(404, "unknown unit key (planned units have no "
                                 "generator yet)")
    if topic.verify in ("attested", "f4"):
        raise HTTPException(
            409,
            "static F3/F4 units are filled via their conversion endpoints, "
            "not LLM generation",
        )
    units = await db.grammar_units_with_counts(topic.lang)
    unit = next((u for u in units if u["key"] == key), None)
    if unit is None:
        raise HTTPException(404, "unit not seeded")
    shortfall = unit["target_size"] - unit["verified"]
    if shortfall <= 0:
        return {"started": False, "reason": "at target",
                "verified": unit["verified"],
                "target_size": unit["target_size"]}
    if not grammar_service.claim_grammar_job(topic.lang, "generation"):
        return {"started": False, "reason": "already running",
                **grammar_service.get_state()}
    _spawn_bg(grammar_service.run_generation(
        topic.lang, shortfall, key, claimed=True))
    return {"started": True, "lang": topic.lang, "unit": key,
            "n_requested": shortfall}


@app.post("/admin/grammar-retire-item/{item_id}")
async def admin_grammar_retire_item(
    item_id: int, _: None = Depends(authed_admin),
) -> dict:
    """Retire one verified item. The next rebuild drops it from the deck;
    its note stays in the Anki collection until a cleanup.json purge
    (acceptable v1 — the UI says so)."""
    row = await db.retire_grammar_item(item_id)
    if row is None:
        raise HTTPException(404, "item not found or not in 'verified' state")
    return {"ok": True, **row}


# --- admin: LingQ vocabulary mirror ----------------------------------------

@app.post("/admin/lingq-token")
async def admin_lingq_token(body: dict, _: None = Depends(authed_admin)) -> dict:
    """Store the LingQ API token (kv_store, never the repo/env — the repo
    is public). Body: {"token": "..."}."""
    token = (body.get("token") or "").strip()
    if not token or len(token) < 20:
        raise HTTPException(400, "body must be {'token': '<lingq api token>'}")
    await db.set_external_token("lingq", token)
    return {"ok": True}


@app.post("/admin/lingq-sync")
async def admin_lingq_sync(
    langs: str | None = None, _: None = Depends(authed_admin),
) -> dict:
    """Pull the user's LingQ vocabulary into lingq_terms. Background;
    poll /admin/lingq-status. langs: optional comma-separated subset
    (default: every language on the LingQ account)."""
    from . import lingq
    if not get_settings().lingq_web_sync_enabled:
        raise HTTPException(
            409, "lingq sync runs in the cron container (self-healing: it "
                 "fetches any missing/incomplete language on each 2h tick); "
                 "set LINGQ_WEB_SYNC_ENABLED=true only for emergencies")
    if lingq.get_state().get("running"):
        return {"started": False, "reason": "already running",
                **lingq.get_state()}
    lang_list = [s.strip() for s in langs.split(",")] if langs else None
    _spawn_bg(lingq.run_sync(lang_list))
    return {"started": True, "langs": lang_list or "all"}


@app.get("/admin/lingq-status")
async def admin_lingq_status(_: None = Depends(authed_admin)) -> dict:
    from . import lingq
    return {**lingq.get_state(),
            "last_sync": await db.get_kv("lingq_last_sync"),
            "stats": await db.lingq_stats()}


@app.get("/admin/lingq-sample")
async def admin_lingq_sample(
    lang: str, n: int = 20, max_status: int = 2,
    _: None = Depends(authed_admin),
) -> dict:
    """Random sample of studied terms — for local agents (codex) that
    build exercises and want to weave in the learner's vocabulary."""
    if n < 1 or n > 200:
        raise HTTPException(400, "n must be 1..200")
    return {"lang": lang,
            "terms": await db.sample_lingq_terms(lang, n, max_status)}


@app.post("/admin/personal-errors-upload")
async def admin_personal_errors_upload(
    request: Request, _: None = Depends(authed_admin),
) -> dict:
    """Stage the personal-error registry (raw JSONL body, commission-A
    schema) for CRON-side ingestion. This endpoint validates and does
    ONE blob insert into personal_errors_staging — the batched upserts
    deliberately run in the cron container (LingQ web-process-hang
    lesson; and cron can't see /data, so the DB is the handoff)."""
    from . import personal_errors as pe
    body = (await request.body()).decode("utf-8", errors="replace")
    if len(body) > 50_000_000:
        raise HTTPException(413, "too large")
    rows, errors = pe.parse_jsonl(body)
    if errors:
        raise HTTPException(400, {"n_errors": len(errors),
                                  "first_errors": errors[:10]})
    if not rows:
        raise HTTPException(400, "no rows")
    staging_id = await db.stage_personal_errors(body, len(rows))
    return {"staged": len(rows), "staging_id": staging_id,
            "note": "ingested by the cron container on its next tick "
                    "(top of the even hour)"}


@app.get("/admin/personal-errors-status")
async def admin_personal_errors_status(_: None = Depends(authed_admin)) -> dict:
    pool = await db.get_pool()
    pending = await pool.fetchval(
        "SELECT COUNT(*) FROM personal_errors_staging WHERE processed_at IS NULL")
    last = await pool.fetchrow(
        """SELECT uploaded_at, processed_at, n_rows, note
           FROM personal_errors_staging ORDER BY id DESC LIMIT 1""")
    return {"staging_pending": pending,
            "last_upload": dict(last) if last else None,
            "stats": await db.personal_errors_stats()}


@app.post("/admin/f4-pairs-upload")
async def admin_f4_pairs_upload(
    request: Request, _: None = Depends(authed_admin),
) -> dict:
    """Validate and stage one private F4 JSON-array bank for cron ingest.

    The API process performs exactly one blob insert. Pair upserts and registry
    attestation checks remain isolated in the cron process.
    """
    from .grammar import f4

    raw = await request.body()
    if len(raw) > 10_000_000:
        raise HTTPException(413, "too large")
    try:
        body = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "body must be valid UTF-8") from exc
    rows, errors = f4.parse_pair_bank(body)
    if errors:
        raise HTTPException(
            400, {"n_errors": len(errors), "first_errors": errors[:10]}
        )
    if not rows:
        raise HTTPException(400, "no rows")
    staging_id = await db.stage_f4_pairs(body, len(rows))
    return {
        "staged": len(rows),
        "staging_id": staging_id,
        "target_lang": rows[0]["target_lang"],
        "note": "ingested by the cron container on its next tick",
    }


@app.get("/admin/f4-pairs-status")
async def admin_f4_pairs_status(_: None = Depends(authed_admin)) -> dict:
    """Return F4 ingest progress and aggregate counts without pair content."""
    pool = await db.get_pool()
    pending = await pool.fetchval(
        "SELECT COUNT(*) FROM f4_pairs_staging WHERE processed_at IS NULL"
    )
    last = await pool.fetchrow(
        """SELECT uploaded_at, processed_at, n_rows, note
           FROM f4_pairs_staging ORDER BY id DESC LIMIT 1"""
    )
    return {
        "staging_pending": pending,
        "last_upload": dict(last) if last else None,
        "stats": await db.f4_pairs_stats(),
    }


@app.post("/admin/podcasts-build")
async def admin_podcasts_build(_: None = Depends(authed_admin)) -> dict:
    """Render the grammar-walks season to numbered MP3s (design:
    unit-specs/PODCASTS_DESIGN.md — plain files, not cards). Background;
    poll /admin/grammar-status. Idempotent via the clip cache."""
    from .grammar import podcasts
    from .grammar import service as grammar_service
    if not grammar_service.claim_grammar_job("podcasts", "podcasts"):
        return {"started": False, "reason": "already running"}

    async def _run() -> None:
        try:
            result = await podcasts.build_podcasts()
            grammar_service._state["podcasts"] = result
        except Exception as e:  # noqa: BLE001
            log.warning("admin.podcasts_build.failed", err=repr(e)[:200])
            grammar_service._state["error"] = repr(e)[:200]
        finally:
            grammar_service._state["running"] = False

    _spawn_bg(_run())
    return {"started": True}


@app.get("/admin/podcasts-list")
async def admin_podcasts_list(_: None = Depends(authed_admin)) -> dict:
    from .grammar import podcasts
    return {"episodes": podcasts.list_episodes(),
            "note": "stream/download via /ui/api/audio/grammar/podcasts/"
                    "<file>?token=<admin token>"}


@app.post("/admin/podcast-cards-build")
async def admin_podcast_cards_build(
    lang: str, episode: int, _: None = Depends(authed_admin),
) -> dict:
    """Render and package one podcast-card episode in the background."""
    from .grammar import podcast_cards
    from .grammar import service as grammar_service

    if lang not in ("de", "es", "fr", "it", "pt"):
        raise HTTPException(400, "lang must be de|es|fr|it|pt")
    if episode < 1:
        raise HTTPException(400, "episode must be >= 1")
    claim_key = f"podcast-cards-{lang}"
    if not grammar_service.claim_grammar_job(claim_key, "podcast_cards"):
        return {"error": "busy", **grammar_service.get_state()}

    async def _run() -> None:
        try:
            result = await podcast_cards.build_episode(lang, episode)
            grammar_service._state["podcast_cards"] = result
        except Exception as e:  # noqa: BLE001
            log.warning("admin.podcast_cards_build.failed", lang=lang,
                        episode=episode, err=repr(e)[:200])
            grammar_service._state["error"] = repr(e)[:200]
        finally:
            grammar_service._state["running"] = False

    _spawn_bg(_run())
    return {"started": True, "lang": lang, "episode": episode}


@app.get("/admin/podcast-cards-list")
async def admin_podcast_cards_list(_: None = Depends(authed_admin)) -> dict:
    """List authored podcast-card sources and staged side assets."""
    from .grammar import podcast_cards
    return {"episodes": podcast_cards.list_episode_sources()}


@app.post("/admin/exercises2-build")
async def admin_exercises2_build(
    lang: str, _: None = Depends(authed_admin),
) -> dict:
    """Build one language's Exercises 2.0 deck (TTS + APKG) in the background."""
    from .grammar import exercises2
    from .grammar import service as grammar_service

    if lang not in exercises2.SUPPORTED_LANGS:
        raise HTTPException(400, "lang must be de|es|fr|it|pt")
    if not grammar_service.claim_grammar_job(f"exercises2-{lang}", "exercises2"):
        return {"error": "busy", **grammar_service.get_state()}

    async def _run() -> None:
        try:
            result = await exercises2.build_language(lang)
            grammar_service._state["exercises2"] = result
        except Exception as e:  # noqa: BLE001
            log.warning("admin.exercises2_build.failed", lang=lang,
                        err=repr(e)[:200])
            grammar_service._state["error"] = repr(e)[:200]
        finally:
            grammar_service._state["running"] = False

    _spawn_bg(_run())
    return {"started": True, "lang": lang}


@app.get("/admin/exercises2-list")
async def admin_exercises2_list(_: None = Depends(authed_admin)) -> dict:
    """List reviewed exercises2 notes files with validation state."""
    from .grammar import exercises2
    return {"sources": exercises2.list_sources()}


@app.post("/admin/translation-build")
async def admin_translation_build(
    lang: str, _: None = Depends(authed_admin),
) -> dict:
    """Build one language's translation deck (EN TTS + APKG) in the background."""
    from .grammar import service as grammar_service
    from .grammar import translation

    if lang not in translation.SUPPORTED_LANGS:
        raise HTTPException(400, "lang must be de|es|fr|it|pt")
    if not grammar_service.claim_grammar_job(f"translation-{lang}", "translation"):
        return {"error": "busy", **grammar_service.get_state()}

    async def _run() -> None:
        try:
            result = await translation.build_language(lang)
            grammar_service._state["translation"] = result
        except Exception as e:  # noqa: BLE001
            log.warning("admin.translation_build.failed", lang=lang,
                        err=repr(e)[:200])
            grammar_service._state["error"] = repr(e)[:200]
        finally:
            grammar_service._state["running"] = False

    _spawn_bg(_run())
    return {"started": True, "lang": lang}


@app.post("/admin/tenses-build")
async def admin_tenses_build(
    lang: str, _: None = Depends(authed_admin),
) -> dict:
    """Build one language's Tenses Rescue decks (production + exercises,
    TTS + 2 APKGs) in the background. Content: grammar/data/tenses/."""
    from .grammar import service as grammar_service
    from .grammar import tenses

    if lang not in tenses.SUPPORTED_LANGS:
        raise HTTPException(400, "lang must be de|es|fr|it|pt")
    if not grammar_service.claim_grammar_job(f"tenses-{lang}", "tenses"):
        return {"error": "busy", **grammar_service.get_state()}

    async def _run() -> None:
        try:
            result = await tenses.build_language(lang)
            grammar_service._state["tenses"] = result
        except Exception as e:  # noqa: BLE001
            log.warning("admin.tenses_build.failed", lang=lang,
                        err=repr(e)[:200])
            grammar_service._state["error"] = repr(e)[:200]
        finally:
            grammar_service._state["running"] = False

    _spawn_bg(_run())
    return {"started": True, "lang": lang}


@app.get("/admin/tenses-list")
async def admin_tenses_list(_: None = Depends(authed_admin)) -> dict:
    """Tenses content inventory: per verb×tense, drilled slots vs items."""
    from .grammar import tenses
    return {"content": tenses.list_content()}


@app.post("/admin/tenses-voice-audition")
async def admin_tenses_voice_audition(
    body: dict | None = None, _: None = Depends(authed_admin),
) -> dict:
    """Render one Spanish sample sentence in every candidate ElevenLabs
    voice (the user vetoed George for the tenses decks). Synchronous —
    a few seconds. Body (optional): {"text": "..."}."""
    from .grammar import tenses
    text = (body or {}).get("text")
    return await tenses.voice_audition("es", text)


@app.get("/admin/disk-usage")
async def admin_disk_usage(
    path: str = "", _: None = Depends(authed_admin),
) -> dict:
    """With ?path=<relative dir>: per-file listing (top 60 by size) instead
    of the tree scan — for drilling into a heavy directory."""
    if path:
        root = Path(get_settings().data_dir)
        target = (root / path).resolve()
        if not str(target).startswith(str(root.resolve())):
            raise HTTPException(400, "path escapes data dir")
        if not target.is_dir():
            raise HTTPException(404, "no such directory")

        def listing() -> dict:
            files = []
            for p in target.iterdir():
                try:
                    if p.is_file():
                        stat = p.stat()
                        files.append((stat.st_size, p.name,
                                      int(stat.st_mtime)))
                except OSError:
                    continue
            files.sort(reverse=True)
            return {"dir": path, "files": [
                {"name": name, "mb": round(size / 1e6, 1), "mtime": mtime}
                for size, name, mtime in files[:60]
            ]}

        return await asyncio.to_thread(listing)
    return await _disk_tree_scan()


async def _disk_tree_scan() -> dict:
    """Read-only /data usage report: filesystem totals + per-directory bytes
    (depth 2). Built for the 2026-08-04 ENOSPC incident — see also the
    worker janitor, which only covers media_stage + delivered video apkgs."""
    import shutil as _shutil

    import os as _os

    def scan() -> dict:
        root = Path(get_settings().data_dir)
        total, used, free = _shutil.disk_usage(root)
        # One os.walk pass, bytes bucketed by <top>/<sub> relative to root.
        buckets: dict[str, int] = {}
        root_str = str(root)
        for dirpath, _dirnames, filenames in _os.walk(root_str):
            rel = _os.path.relpath(dirpath, root_str)
            parts = [] if rel == "." else rel.split(_os.sep)
            key = "/".join(parts[:2]) if parts else "_root_files"
            for name in filenames:
                try:
                    buckets[key] = buckets.get(key, 0) + _os.path.getsize(
                        _os.path.join(dirpath, name))
                except OSError:
                    continue
        top = dict(sorted(
            ((k, round(v / 1e6, 1)) for k, v in buckets.items()),
            key=lambda kv: -kv[1],
        )[:40])
        return {
            "disk_gb": {"total": round(total / 1e9, 2),
                        "used": round(used / 1e9, 2),
                        "free": round(free / 1e9, 2)},
            "dirs_mb": top,
        }

    return await asyncio.to_thread(scan)


@app.get("/admin/translation-list")
async def admin_translation_list(_: None = Depends(authed_admin)) -> dict:
    """Per-language translation-deck inventory: eligible items, TL audio, EN cache."""
    from .grammar import translation
    return {"languages": await translation.language_inventory()}


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


# --- admin: backfill context clips (pre-2026-07-20 idioms) ------------------

@app.post("/admin/backfill-context")
async def admin_backfill_context(
    limit: int | None = None, rebuild: bool = True,
    _: None = Depends(authed_admin),
) -> dict:
    """Re-download source audio for done videos whose idioms lack
    audio_context, locate each stored sentence via Gemini, slice + stage
    the clips. `limit` caps the number of videos (pilot runs);
    `rebuild=false` skips the final pool rebuilds. Background; poll
    /admin/backfill-context/status. Resumable — re-POST continues."""
    from . import backfill_context
    if backfill_context.get_state()["running"]:
        return {"started": False, "reason": "already running"}
    _spawn_bg(backfill_context.run_backfill_context(
        limit=limit, rebuild=rebuild))
    return {"started": True, "limit": limit, "rebuild": rebuild}


@app.get("/admin/backfill-context/status")
async def admin_backfill_context_status(
    _: None = Depends(authed_admin),
) -> dict:
    from . import backfill_context
    return backfill_context.get_state()


@app.post("/admin/clear-context")
async def admin_clear_context(
    body: dict, _: None = Depends(authed_admin),
) -> dict:
    """NULL out audio_context for the given expression_idioms ids — used
    to prune backfilled clips that failed the offline whisper
    verification (clip transcribes to a different sentence). The staged
    file is left on disk (unreferenced, ~100 KB each)."""
    ids = body.get("ids")
    if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        raise HTTPException(400, "body must be {\"ids\": [int, ...]}")
    if not ids:
        return {"cleared": 0}
    pool = await db.get_pool()
    result = await pool.execute(
        "UPDATE expression_idioms SET audio_context = NULL WHERE id = ANY($1::bigint[])",
        ids,
    )
    return {"cleared": int(result.split()[-1])}


@app.get("/admin/citation-todo")
async def admin_citation_todo(
    _: None = Depends(authed_admin),
    limit: int = 500,
) -> dict:
    """Idioms still lacking a citation (dictionary) form. Consumed by the
    local codex backfill; write back via POST /admin/citation-forms."""
    pool = await db.get_pool()
    rows = await pool.fetch(
        """SELECT id, lang, idiom_text, english_gloss, source_phrase_target
           FROM expression_idioms
           WHERE citation_form IS NULL
           ORDER BY id LIMIT $1""",
        max(1, min(limit, 2000)))
    total = await pool.fetchval(
        "SELECT COUNT(*) FROM expression_idioms WHERE citation_form IS NULL")
    return {"remaining": total, "items": [dict(r) for r in rows]}


@app.post("/admin/citation-forms")
async def admin_citation_forms(
    body: dict, _: None = Depends(authed_admin),
) -> dict:
    """Bulk-set citation forms: {"forms": {"<idiom_id>": "<citation form>"}}.
    Empty/whitespace values are rejected per-row (kept NULL for retry)."""
    forms = body.get("forms")
    if not isinstance(forms, dict) or not forms:
        raise HTTPException(400, 'need {"forms": {"<id>": "<form>", ...}}')
    pairs = []
    for k, v in forms.items():
        try:
            i = int(k)
        except (TypeError, ValueError):
            raise HTTPException(400, f"non-integer id {k!r}")
        v = (v or "").strip()
        if v:
            pairs.append((i, v[:300]))
    pool = await db.get_pool()
    updated = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            for i, v in pairs:
                r = await conn.execute(
                    "UPDATE expression_idioms SET citation_form = $2 WHERE id = $1",
                    i, v)
                updated += int(r.split()[-1])
    return {"ok": True, "updated": updated, "skipped_empty": len(forms) - len(pairs)}


@app.post("/admin/purge-video")
async def admin_purge_video(
    body: dict, _: None = Depends(authed_admin),
) -> dict:
    """Purge every artifact of a video whose audio turned out to be a
    wrong-language track (e.g. a YouTube auto-dub the downloader picked):
    expression rows, per-video apkg row + file, staged audio, R2 object.
    Returns the Anki deck name + note GUIDs for the add-on's cleanup.json.
    body: {"youtube_id": "...", "requeue": bool} — requeue resets the video
    to queued/attempts=0 so the fixed downloader re-fetches the original
    track. Pool apkgs are NOT rebuilt here; call /admin/rebuild-pools?lang=…
    once after a batch of purges."""
    import shutil as _shutil

    from . import oxylabs_client
    from .langs import LANG_NAMES
    from .pipeline.apkg import _guid as _video_guid
    from .pipeline.pool import _guid as _pool_guid
    from .pipeline.pool import _norm as _pool_norm

    youtube_id = body.get("youtube_id")
    requeue = bool(body.get("requeue"))
    if not isinstance(youtube_id, str) or not youtube_id.strip():
        raise HTTPException(400, "need youtube_id")
    youtube_id = youtube_id.strip()
    pool = await db.get_pool()
    v = await pool.fetchrow(
        "SELECT id, lang, title, first_seen::date AS d FROM videos WHERE youtube_id = $1",
        youtube_id)
    if not v:
        raise HTTPException(404, "unknown youtube_id")

    idioms = await pool.fetch(
        "SELECT id, idiom_text, expression_id FROM expression_idioms WHERE video_id = $1",
        v["id"])
    idiom_ids = [r["id"] for r in idioms]
    examples = await pool.fetch(
        "SELECT idiom_id, target_text FROM expression_examples WHERE idiom_id = ANY($1::bigint[])",
        idiom_ids) if idiom_ids else []

    # Expressions that exist ONLY in this video — their pool notes must go
    # too. Shared expressions keep their pool notes (rebuilt from the
    # surviving occurrence).
    expr_ids = list({r["expression_id"] for r in idioms
                     if r["expression_id"] is not None})
    orphaned: set = set()
    if expr_ids:
        rows = await pool.fetch(
            """SELECT e.id FROM expressions e
               WHERE e.id = ANY($1::bigint[])
                 AND NOT EXISTS (SELECT 1 FROM expression_idioms ei
                                 WHERE ei.expression_id = e.id
                                   AND ei.video_id <> $2)""",
            expr_ids, v["id"])
        orphaned = {r["id"] for r in rows}

    date_prefix = v["d"].isoformat() if v["d"] else "0000-00-00"
    deck_name = (f"Idiomatic::{LANG_NAMES.get(v['lang'], v['lang'].upper())}"
                 f"::{date_prefix} · {v['title']}")
    guids = [_video_guid(youtube_id, (r["idiom_text"] or "").lower().strip())
             for r in idioms]
    ex_by_idiom: dict = {}
    for r in examples:
        ex_by_idiom.setdefault(r["idiom_id"], []).append(r["target_text"])
    for r in idioms:
        if r["expression_id"] in orphaned:
            it = r["idiom_text"] or ""
            guids.append(_pool_guid(f"yt-idiom-pool::{v['lang']}", _pool_norm(it)))
            guids.append(_pool_guid("yt-pool-t2e", _pool_norm(it)))
            guids.append(_pool_guid("yt-pool-e2t", _pool_norm(it)))
            for tg in ex_by_idiom.get(r["id"], []):
                guids.append(_pool_guid("yt-pool", _pool_norm(it), _pool_norm(tg or "")))

    # --- deletions, FK-safe order -------------------------------------------
    if idiom_ids:
        await pool.execute(
            "DELETE FROM expression_examples WHERE idiom_id = ANY($1::bigint[])",
            idiom_ids)
        await pool.execute(
            "DELETE FROM expression_idioms WHERE video_id = $1", v["id"])
    if orphaned:
        await pool.execute(
            "DELETE FROM expressions WHERE id = ANY($1::bigint[])",
            list(orphaned))
    apkg_rows = await pool.fetch(
        "SELECT id, filename FROM apkgs WHERE video_id = $1", v["id"])
    settings = get_settings()
    for r in apkg_rows:
        (Path(settings.data_dir) / r["filename"]).unlink(missing_ok=True)
    if apkg_rows:
        ids = [r["id"] for r in apkg_rows]
        await pool.execute(
            "DELETE FROM agent_acks WHERE apkg_id = ANY($1::int[])", ids)
        await pool.execute(
            "DELETE FROM apkgs WHERE id = ANY($1::int[])", ids)
    _shutil.rmtree(Path(settings.data_dir) / "staged_audio" / youtube_id,
                   ignore_errors=True)
    await oxylabs_client.cleanup_r2(youtube_id)

    if requeue:
        # first_seen=NOW(): (a) survives the 7-day queue expiry, (b) sorts
        # to the front of the newest-first claim order so the re-download
        # with the original track happens promptly.
        await pool.execute(
            """UPDATE videos SET status='queued', attempts=0, picked_at=NULL,
               finished_at=NULL, first_seen=NOW(),
               status_msg='purged wrong-language artifacts; requeued'
               WHERE id = $1""", v["id"])
    else:
        await pool.execute(
            """UPDATE videos SET status='skipped',
               status_msg='purged: wrong-language audio track'
               WHERE id = $1""", v["id"])

    return {"ok": True, "youtube_id": youtube_id, "lang": v["lang"],
            "deck_name": deck_name, "note_guids": guids,
            "idioms_purged": len(idiom_ids),
            "expressions_orphaned": len(orphaned),
            "apkgs_deleted": len(apkg_rows), "requeued": requeue}


# --- admin: Rescue Lab (docs/commissions/RESCUE_LAB_COMMISSION.md) ----------
# The dashboard's /rescue pages mutate ONLY through these endpoints —
# the same exception pattern the Grammar section established.

def _parse_jsonb(value):
    """asyncpg returns jsonb as str unless a codec is registered."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


def _rescue_item_dict(row) -> dict:
    """Row → JSON-friendly dict (items AND assets: parses the jsonb
    columns, floats the NUMERIC cost)."""
    d = dict(row)
    for jsonb_col in ("struggle_snapshot", "params"):
        if jsonb_col in d:
            d[jsonb_col] = _parse_jsonb(d.get(jsonb_col))
    if d.get("cost_usd") is not None:
        d["cost_usd"] = float(d["cost_usd"])
    return d


@app.post("/admin/rescue/struggles")
async def admin_rescue_struggles(
    request: Request, _: None = Depends(authed_admin),
) -> dict:
    """Upload a struggle snapshot (computed off-server from the AnkiWeb
    pull — see docs/research/ANKI_STATS_POC.md). Body: JSON list of
    {lang, idiom, gloss?, fails_today, fails_14d, failed_sentences[]}.
    Upserts rescue_items as candidates; an existing item keeps its
    status/strike/anchor and gets a fresh snapshot."""
    from . import rescue
    try:
        payload = json.loads((await request.body()).decode("utf-8"))
    except ValueError:
        raise HTTPException(400, "body must be JSON")
    rows, errors = rescue.validate_struggles(payload)
    if errors:
        raise HTTPException(400, {"n_errors": len(errors),
                                  "first_errors": errors[:10]})
    pool = await db.get_pool()
    inserted = updated = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            for r in rows:
                row = await conn.fetchrow(
                    """
                    INSERT INTO rescue_items (lang, idiom, gloss,
                                              struggle_snapshot)
                    VALUES ($1, $2, $3, $4::jsonb)
                    ON CONFLICT (lang, idiom) DO UPDATE SET
                        gloss = COALESCE(EXCLUDED.gloss, rescue_items.gloss),
                        struggle_snapshot = EXCLUDED.struggle_snapshot,
                        updated_at = NOW()
                    RETURNING (xmax = 0) AS inserted
                    """,
                    r["lang"], r["idiom"], r["gloss"],
                    json.dumps(r["snapshot"], ensure_ascii=False))
                if row["inserted"]:
                    inserted += 1
                else:
                    updated += 1
    return {"ok": True, "inserted": inserted, "updated": updated}


@app.post("/admin/rescue/generate")
async def admin_rescue_generate(
    body: dict, _: None = Depends(authed_admin),
) -> dict:
    """Generate one image asset for an item. Body: {item_id, format,
    provider, prompt?, params?}. Without a prompt, the format template
    is filled from the item's fields (idiomatic/rescue.py — templates
    seeded from the approved pilot prompts). Stages the file under
    /data/rescue_assets/, inserts a draft rescue_assets row AND a
    gen_ledger row (cost from the genmedia registry at call time).

    Synchronous on purpose: one image is bounded (~5-15 s) and the
    dashboard wants the draft back for immediate review."""
    from . import genmedia, rescue

    item_id = body.get("item_id")
    fmt = body.get("format")
    provider = body.get("provider")
    prompt = str(body.get("prompt") or "").strip()
    params = body.get("params") if isinstance(body.get("params"), dict) else {}
    if not isinstance(item_id, int):
        raise HTTPException(400, "need item_id (int)")
    if fmt not in rescue.ALL_FORMATS:
        raise HTTPException(400, f"format must be one of {rescue.ALL_FORMATS}"
                                 " (video does not exist here)")
    if fmt not in rescue.IMAGE_FORMATS:
        raise HTTPException(400, f"format {fmt!r} is authored manually, "
                                 "not generated through image providers")
    if provider not in genmedia.PROVIDERS:
        raise HTTPException(400, f"provider must be one of "
                                 f"{sorted(genmedia.PROVIDERS)}")

    pool = await db.get_pool()
    item = await pool.fetchrow(
        "SELECT * FROM rescue_items WHERE id = $1", item_id)
    if not item:
        raise HTTPException(404, "unknown item")
    senses = [dict(r) for r in await pool.fetch(
        "SELECT label, gloss, example_tl, example_en, ord "
        "FROM rescue_senses WHERE item_id = $1 ORDER BY ord", item_id)]
    if not prompt:
        try:
            prompt = rescue.fill_template(fmt, _rescue_item_dict(item), senses)
        except ValueError as e:
            raise HTTPException(409, str(e))

    from . import rescue_ops
    try:
        asset = await rescue_ops.generate_asset(
            item_id, fmt, provider, prompt, params)
    except genmedia.UnknownProvider as e:
        raise HTTPException(400, str(e))
    except Exception as e:  # noqa: BLE001 — surface provider failures as 502
        log.warning("admin.rescue_generate.failed", item_id=item_id,
                    fmt=fmt, provider=provider, err=repr(e)[:300])
        raise HTTPException(502, f"generation failed: {str(e)[:300]}")
    return {"ok": True, "asset": _rescue_item_dict(asset)}


@app.post("/admin/genmedia-render")
async def admin_genmedia_render(
    body: dict, _: None = Depends(authed_admin),
) -> Response:
    """Raw cloud-image render for factory asset production (cast sheets,
    settings): {provider, prompt, image_b64?, size?, model_override?}.
    Returns the PNG bytes; writes a gen_ledger row (no item/asset — the
    artifact lives on the render client, e.g. the laptop's factory dirs).
    The provider keys live only in this service's env, so cloud renders
    route through here rather than shipping keys to clients."""
    from . import genmedia

    provider = body.get("provider") or genmedia.DEFAULT_PROVIDER
    prompt = str(body.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(400, "need prompt")
    if provider not in genmedia.PROVIDERS:
        raise HTTPException(400, f"provider must be one of "
                                 f"{sorted(genmedia.PROVIDERS)}")
    params: dict = {}
    for k in ("image_b64", "size", "model_override"):
        if body.get(k):
            params[k] = body[k]
    try:
        image, cost = await genmedia.generate_image(
            provider, prompt, params=params)
    except Exception as e:  # noqa: BLE001 — surface provider failures as 502
        log.warning("admin.genmedia_render.failed", provider=provider,
                    err=repr(e)[:300])
        raise HTTPException(502, f"generation failed: {str(e)[:300]}")
    pool = await db.get_pool()
    await pool.execute(
        """
        INSERT INTO gen_ledger (provider, model, kind, units, unit_kind,
                                cost_usd, item_id, asset_id)
        VALUES ($1, $2, 'image', 1, 'image', $3, NULL, NULL)
        """,
        provider, str(params.get("model_override", "") or
                      genmedia.provider_info(provider)["model"]), cost)
    return Response(content=image, media_type="image/png",
                    headers={"X-Cost-USD": str(cost)})


def _factory_cast_dir(slug: str) -> Path:
    root = (Path(get_settings().data_dir) / "factory_cast").resolve()
    d = (root / slug).resolve()
    if not d.is_relative_to(root):
        raise HTTPException(400, "bad slug")
    return d


_SLUG_RE = re.compile(r"^[a-z0-9_]{2,64}$")


@app.post("/admin/factory/cast-upsert")
async def admin_factory_cast_upsert(
    request: Request, _: None = Depends(authed_admin),
) -> dict:
    """Upsert one cast character (Cast Review panel backend; reusable for
    future cast additions). Multipart form: slug (required), meta (JSON:
    real_name, lang, role_key, famous_source, survival_prior, prompt_desc,
    exclusion_checked, exclusion_verdict), ref (image file, optional),
    sheet (image file, optional). Files land under /data/factory_cast/
    <slug>/. A new sheet on an approved actor demotes it to candidate
    (famous-cast §2.5 staleness rule)."""
    form = await request.form()
    slug = str(form.get("slug") or "").strip()
    if not _SLUG_RE.fullmatch(slug):
        raise HTTPException(400, "need slug [a-z0-9_]{2,64}")
    try:
        meta = json.loads(str(form.get("meta") or "{}"))
    except ValueError:
        raise HTTPException(400, "meta must be JSON")
    d = _factory_cast_dir(slug)
    d.mkdir(parents=True, exist_ok=True)
    ref_path = sheet_path = sheet_hash = None
    ref = form.get("ref")
    if ref is not None and hasattr(ref, "read"):
        data = await ref.read()
        (d / "ref.jpg").write_bytes(data)
        ref_path = f"{slug}/ref.jpg"
    sheet = form.get("sheet")
    if sheet is not None and hasattr(sheet, "read"):
        data = await sheet.read()
        (d / "sheet.png").write_bytes(data)
        sheet_path = f"{slug}/sheet.png"
        sheet_hash = hashlib.sha256(data).hexdigest()[:16]
    pool = await db.get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO factory_actors (slug, real_name, lang, role_key,
            famous_source, survival_prior, exclusion_checked,
            exclusion_verdict, prompt_desc, ref_photo_path, sheet_path,
            sheet_hash)
        VALUES ($1, $2, $3, $4, $5, $6, COALESCE($7, FALSE), $8, $9,
                $10, $11, $12)
        ON CONFLICT (slug) DO UPDATE SET
            real_name = COALESCE(EXCLUDED.real_name, factory_actors.real_name),
            lang = COALESCE(EXCLUDED.lang, factory_actors.lang),
            role_key = COALESCE(EXCLUDED.role_key, factory_actors.role_key),
            famous_source = COALESCE(EXCLUDED.famous_source,
                                     factory_actors.famous_source),
            survival_prior = COALESCE(EXCLUDED.survival_prior,
                                      factory_actors.survival_prior),
            exclusion_checked = factory_actors.exclusion_checked
                                OR EXCLUDED.exclusion_checked,
            exclusion_verdict = COALESCE(EXCLUDED.exclusion_verdict,
                                         factory_actors.exclusion_verdict),
            prompt_desc = COALESCE(EXCLUDED.prompt_desc,
                                   factory_actors.prompt_desc),
            ref_photo_path = COALESCE(EXCLUDED.ref_photo_path,
                                      factory_actors.ref_photo_path),
            sheet_path = COALESCE(EXCLUDED.sheet_path,
                                  factory_actors.sheet_path),
            sheet_hash = COALESCE(EXCLUDED.sheet_hash,
                                  factory_actors.sheet_hash),
            status = CASE WHEN EXCLUDED.sheet_hash IS NOT NULL
                               AND EXCLUDED.sheet_hash IS DISTINCT FROM
                                   factory_actors.sheet_hash
                               AND factory_actors.status = 'approved'
                          THEN 'candidate' ELSE factory_actors.status END,
            review_flag = CASE WHEN EXCLUDED.sheet_hash IS NOT NULL
                                    AND EXCLUDED.sheet_hash IS DISTINCT FROM
                                        factory_actors.sheet_hash
                               THEN NULL ELSE factory_actors.review_flag END,
            updated_at = NOW()
        RETURNING *
        """,
        slug, meta.get("real_name"), meta.get("lang"), meta.get("role_key"),
        meta.get("famous_source"), meta.get("survival_prior"),
        meta.get("exclusion_checked"), meta.get("exclusion_verdict"),
        meta.get("prompt_desc"), ref_path, sheet_path, sheet_hash)
    return {"ok": True, "actor": {k: (v.isoformat() if hasattr(v, "isoformat")
                                      else v) for k, v in dict(row).items()}}


@app.post("/admin/factory/cast/{slug}/review")
async def admin_factory_cast_review(
    slug: str, body: dict, _: None = Depends(authed_admin),
) -> dict:
    """Review verdict from the Cast Review panel. Body: any of
    {flag: 'ok'|'remake'|None, note, status: candidate|approved|retired}."""
    sets, args = [], []
    if "flag" in body:
        if body["flag"] not in (None, "ok", "remake"):
            raise HTTPException(400, "flag must be ok|remake|null")
        args.append(body["flag"])
        sets.append(f"review_flag = ${len(args)}")
    if "note" in body:
        args.append(str(body["note"] or "") or None)
        sets.append(f"review_note = ${len(args)}")
    if "status" in body:
        if body["status"] not in ("candidate", "approved", "retired"):
            raise HTTPException(400, "bad status")
        args.append(body["status"])
        sets.append(f"status = ${len(args)}")
    if not sets:
        raise HTTPException(400, "nothing to set")
    args.append(slug)
    pool = await db.get_pool()
    row = await pool.fetchrow(
        f"UPDATE factory_actors SET {', '.join(sets)}, updated_at = NOW() "
        f"WHERE slug = ${len(args)} RETURNING slug", *args)
    if not row:
        raise HTTPException(404, "unknown slug")
    return {"ok": True}


@app.post("/admin/factory/cast/{slug}/ref")
async def admin_factory_cast_ref(
    slug: str, request: Request, _: None = Depends(authed_admin),
) -> dict:
    """Replacement reference photo from the review panel (multipart field
    'ref'). Stored as the actor's ref; the sheet is untouched — flag the
    actor 'remake' and re-render from the new ref."""
    form = await request.form()
    ref = form.get("ref")
    if ref is None or not hasattr(ref, "read"):
        raise HTTPException(400, "need file field 'ref'")
    data = await ref.read()
    if not data or len(data) > 30_000_000:
        raise HTTPException(400, "empty or too large")
    pool = await db.get_pool()
    exists = await pool.fetchval(
        "SELECT 1 FROM factory_actors WHERE slug = $1", slug)
    if not exists:
        raise HTTPException(404, "unknown slug")
    d = _factory_cast_dir(slug)
    d.mkdir(parents=True, exist_ok=True)
    (d / "ref.jpg").write_bytes(data)
    await pool.execute(
        "UPDATE factory_actors SET ref_photo_path = $2, updated_at = NOW() "
        "WHERE slug = $1", slug, f"{slug}/ref.jpg")
    return {"ok": True, "ref_photo_path": f"{slug}/ref.jpg"}


@app.post("/admin/rescue/asset/{asset_id}/verdict")
async def admin_rescue_asset_verdict(
    asset_id: int, body: dict, _: None = Depends(authed_admin),
) -> dict:
    """Approve or reject one asset. Body: {status: approved|rejected,
    note?}. Enforces the polysemy rule (a polysemy_map cannot be
    approved for an item with < 2 senses) and glyph permanence
    (approving a glyph pins rescue_items.glyph_asset_id; a second glyph
    can't be approved while an approved one is pinned)."""
    from . import rescue
    status = body.get("status")
    note = str(body.get("note") or "").strip() or None
    if status not in ("approved", "rejected"):
        raise HTTPException(400, "status must be approved|rejected")
    pool = await db.get_pool()
    asset = await pool.fetchrow(
        "SELECT * FROM rescue_assets WHERE id = $1", asset_id)
    if not asset:
        raise HTTPException(404, "unknown asset")
    item_id = asset["item_id"]

    if status == "approved":
        n_senses = await pool.fetchval(
            "SELECT COUNT(*) FROM rescue_senses WHERE item_id = $1", item_id)
        err = rescue.polysemy_approval_error(asset["format"], n_senses)
        if err:
            raise HTTPException(409, err)
        if asset["format"] == "glyph":
            current = await pool.fetchrow(
                """
                SELECT i.glyph_asset_id, a.status AS glyph_status
                FROM rescue_items i
                LEFT JOIN rescue_assets a ON a.id = i.glyph_asset_id
                WHERE i.id = $1
                """, item_id)
            if (current and current["glyph_asset_id"] not in (None, asset_id)
                    and current["glyph_status"] == "approved"):
                raise HTTPException(
                    409, "the glyph is permanent — this item already has an "
                         f"approved glyph (asset {current['glyph_asset_id']}); "
                         "reject that one first if it truly must change")

    async with pool.acquire() as conn:
        async with conn.transaction():
            updated = await conn.fetchrow(
                """
                UPDATE rescue_assets SET status = $2, verdict_note = $3
                WHERE id = $1 RETURNING *
                """, asset_id, status, note)
            if asset["format"] == "glyph":
                if status == "approved":
                    await conn.execute(
                        """UPDATE rescue_items SET glyph_asset_id = $2,
                           updated_at = NOW() WHERE id = $1""",
                        item_id, asset_id)
                else:
                    await conn.execute(
                        """UPDATE rescue_items SET glyph_asset_id = NULL,
                           updated_at = NOW()
                           WHERE id = $1 AND glyph_asset_id = $2""",
                        item_id, asset_id)
    return {"ok": True, "asset": _rescue_item_dict(updated)}


@app.post("/admin/rescue/item/{item_id}")
async def admin_rescue_item_patch(
    item_id: int, patch: dict, _: None = Depends(authed_admin),
) -> dict:
    """Patch an item's mutable state from the dashboard. Body JSON:
    {status?, strike?, anchor?, gloss?, senses?}. senses replaces the
    whole list; every sense must carry label + gloss + example_tl +
    example_en (the data-level polysemy rule)."""
    from . import rescue
    allowed = {"status", "strike", "anchor", "gloss", "senses"}
    unknown = set(patch) - allowed
    if unknown:
        raise HTTPException(400, f"unknown fields: {sorted(unknown)}")
    status = patch.get("status")
    if status is not None and status not in ("candidate", "active", "retired"):
        raise HTTPException(400, "status must be candidate|active|retired")
    strike = patch.get("strike")
    if strike is not None and not (isinstance(strike, int) and 1 <= strike <= 3):
        raise HTTPException(400, "strike must be an int in 1..3")
    senses_rows = None
    if "senses" in patch:
        senses_rows, errors = rescue.validate_senses(patch["senses"])
        if errors:
            raise HTTPException(400, {"n_errors": len(errors),
                                      "first_errors": errors[:10]})

    pool = await db.get_pool()
    sets, args = ["updated_at = NOW()"], [item_id]

    def arg(v) -> str:
        args.append(v)
        return f"${len(args)}"

    if status is not None:
        sets.append(f"status = {arg(status)}")
    if strike is not None:
        sets.append(f"strike = {arg(strike)}")
    for field in ("anchor", "gloss"):
        if field in patch:
            value = str(patch[field] or "").strip() or None
            sets.append(f"{field} = {arg(value)}")

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                f"UPDATE rescue_items SET {', '.join(sets)} "
                f"WHERE id = $1 RETURNING *", *args)
            if row is None:
                raise HTTPException(404, "unknown item")
            if senses_rows is not None:
                await conn.execute(
                    "DELETE FROM rescue_senses WHERE item_id = $1", item_id)
                for s in senses_rows:
                    await conn.execute(
                        """INSERT INTO rescue_senses
                           (item_id, label, gloss, example_tl, example_en, ord)
                           VALUES ($1, $2, $3, $4, $5, $6)""",
                        item_id, s["label"], s["gloss"], s["example_tl"],
                        s["example_en"], s["ord"])
    senses = [dict(r) for r in await pool.fetch(
        "SELECT id, label, gloss, example_tl, example_en, ord "
        "FROM rescue_senses WHERE item_id = $1 ORDER BY ord", item_id)]
    return {"ok": True, "item": _rescue_item_dict(row), "senses": senses}


@app.post("/admin/rescue/autopilot-run")
async def admin_rescue_autopilot_run(
    _: None = Depends(authed_admin),
) -> dict:
    """Force an autopilot run now (pull → struggle refresh → draft
    generation under budget). Runs in the background; read the result at
    /ui/api/rescue/autopilot when it lands."""
    from . import rescue_autopilot

    async def _run() -> None:
        try:
            await rescue_autopilot.run_autopilot(force=True)
        except Exception as e:  # noqa: BLE001
            log.warning("admin.rescue_autopilot.failed", err=repr(e)[:300])

    _spawn_bg(_run())
    return {"started": True}


@app.get("/admin/rescue/export/{item_id}")
async def admin_rescue_export(
    item_id: int, _: None = Depends(authed_admin),
) -> dict:
    """Bundle one item's approved assets + senses + snapshot sentences
    as JSON — the future deck-builder's input (building the apkg itself
    is out of scope here)."""
    pool = await db.get_pool()
    item = await pool.fetchrow(
        "SELECT * FROM rescue_items WHERE id = $1", item_id)
    if not item:
        raise HTTPException(404, "unknown item")
    senses = [dict(r) for r in await pool.fetch(
        "SELECT label, gloss, example_tl, example_en, ord "
        "FROM rescue_senses WHERE item_id = $1 ORDER BY ord", item_id)]
    assets = [_rescue_item_dict(r) for r in await pool.fetch(
        """
        SELECT id, format, provider, model, prompt, params, file_path,
               mime, cost_usd, verdict_note, created_at
        FROM rescue_assets
        WHERE item_id = $1 AND status = 'approved'
        ORDER BY format, created_at
        """, item_id)]
    for a in assets:
        a["params"] = _parse_jsonb(a.get("params"))
    return {"item": _rescue_item_dict(item), "senses": senses,
            "approved_assets": assets}


# --- admin: rotate an agent's bearer token ----------------------------------

@app.post("/admin/reset-acks")
async def admin_reset_acks(
    body: dict, _: None = Depends(authed_admin),
) -> dict:
    """Delete acks so the add-on re-imports those apkgs on its next poll.
    The recovery path for decks that were imported into the wrong Anki
    profile (add-ons are installation-global) and acked from there."""
    agent_id, apkg_ids = body.get("agent_id"), body.get("apkg_ids")
    if not isinstance(agent_id, int) or not isinstance(apkg_ids, list) \
            or not apkg_ids or not all(isinstance(i, int) for i in apkg_ids):
        raise HTTPException(400, "need agent_id (int) + apkg_ids (non-empty int list)")
    pool = await db.get_pool()
    result = await pool.execute(
        "DELETE FROM agent_acks WHERE agent_id = $1 AND apkg_id = ANY($2::int[])",
        agent_id, apkg_ids)
    return {"ok": True, "deleted": int(result.split()[-1])}


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
