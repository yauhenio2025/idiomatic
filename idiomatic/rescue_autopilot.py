"""Rescue autopilot — the loop that flies the Rescue Lab on its own.

Once per `rescue_autopilot_interval_hours` (worker-scheduled, or forced
via POST /admin/rescue/autopilot-run):

  1. PULL   — headless download-only AnkiWeb sync (the iPad's reviews;
              recipe proven in docs/research/ANKI_STATS_POC.md). Never
              uploads; a scratch collection in a temp dir, deleted after.
  2. DIFF   — compute the struggle list from revlog (sentence-level
              pool_expr cards, ≥ rescue_struggle_min_fails_14d Agains in
              14 days), upsert rescue_items snapshots.
  3. TEND   — auto-activate up to rescue_autopilot_max_new_items worst
              new candidates; for active items, draft the missing ladder
              assets (glyph for everyone; strike-1 comic where the
              template can be filled — comics need an authored anchor,
              so fresh auto-detected items get a "needs authoring" note
              instead of a bad comic). Providers: autopilot-flagged only
              (Chinese models — user directive 2026-08-05); hard budget
              stop per run. Everything lands as a DRAFT for the user's
              verdict — the autopilot never approves.
  4. REPORT — one JSON report to kv_store('rescue_autopilot_last'),
              served at /ui/api/rescue/autopilot and shown on the
              dashboard overview.

Strikes 2/3 stay manual until failure-type diagnosis ships (see
RESCUE_PILOT.md ladder); the report lists what it would have done.
"""

from __future__ import annotations

import asyncio
import json
import re
import sqlite3
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from . import db, genmedia, rescue, rescue_ops
from .settings import get_settings

log = structlog.get_logger()

KV_LAST = "rescue_autopilot_last"
KV_LAST_RUN_TS = "rescue_autopilot_last_run_ts"

_LANGS = ("es", "pt", "it", "de", "fr")
_MAX_ATTEMPTS_PER_FORMAT = 3   # incl. rejected drafts — then stop trying


# ---------------------------------------------------------------------------
# 1. PULL — download-only AnkiWeb sync (blocking anki-lib work in a thread)
# ---------------------------------------------------------------------------

def _pull_collection_blocking(workdir: str) -> str:
    from anki.collection import Collection
    from anki.sync import SyncAuth

    s = get_settings()
    colpath = str(Path(workdir) / "collection.anki2")
    col = Collection(colpath)
    auth = SyncAuth(hkey=s.ankiweb_hkey, endpoint=s.ankiweb_endpoint)
    out = col.sync_collection(auth, sync_media=False)
    from anki.sync_pb2 import SyncCollectionResponse as R
    if out.new_endpoint:
        auth = SyncAuth(hkey=s.ankiweb_hkey, endpoint=out.new_endpoint)
    if out.required in (R.FULL_DOWNLOAD, R.FULL_SYNC):
        col.close_for_full_sync()
        # upload=False is load-bearing: this scratch collection must
        # never overwrite the account.
        col.full_upload_or_download(
            auth=auth, server_usn=out.server_media_usn or None, upload=False)
    elif out.required == R.FULL_UPLOAD:
        raise RuntimeError("AnkiWeb wants an upload — refusing (download-only)")
    try:
        col.close()
    except Exception:  # noqa: BLE001 — some paths leave it already closed
        pass
    return colpath


# ---------------------------------------------------------------------------
# 2. DIFF — struggle list from revlog
# ---------------------------------------------------------------------------

def _clean_field(f: str) -> str:
    return re.sub(r"<[^>]+>|\[sound:[^\]]+\]", "", f).strip()


def compute_struggles(colpath: str, min_fails_14d: int,
                      now_ms: int | None = None) -> list[dict]:
    """Sentence-level pool_expr cards (7-field notes) failed in the last
    14 days, aggregated per idiom. Pure sqlite — unit-testable."""
    now_ms = now_ms or int(time.time() * 1000)
    cutoff = now_ms - 14 * 86400 * 1000
    today = datetime.fromtimestamp(now_ms / 1000).strftime("%Y-%m-%d")
    con = sqlite3.connect(f"file:{colpath}?mode=ro", uri=True)
    con.create_collation(
        "unicase", lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
    agg: dict[tuple[str, str], dict] = {}
    for flds, tags, ease, rid in con.execute(
            """SELECT n.flds, n.tags, r.ease, r.id
               FROM revlog r JOIN cards c ON c.id = r.cid
               JOIN notes n ON n.id = c.nid
               WHERE r.id > ?""", (cutoff,)):
        fields = flds.split("\x1f")
        if len(fields) > 8:            # only sentence-level pool_expr notes
            continue
        taglist = tags.split()
        lang = next((t for t in taglist if t in _LANGS), None)
        if lang is None or len(fields) < 6:
            continue
        idiom = _clean_field(fields[4])
        if not idiom:
            continue
        a = agg.setdefault((lang, idiom), {
            "lang": lang, "idiom": idiom,
            "gloss": _clean_field(fields[5]),
            "fails_today": 0, "fails_14d": 0, "seen_14d": 0,
            "failed_sentences": []})
        a["seen_14d"] += 1
        if ease == 1:
            a["fails_14d"] += 1
            if datetime.fromtimestamp(rid / 1000).strftime("%Y-%m-%d") == today:
                a["fails_today"] += 1
            sent = _clean_field(fields[1])
            if sent and sent not in a["failed_sentences"]:
                a["failed_sentences"].append(sent)
    con.close()
    out = [a for a in agg.values() if a["fails_14d"] >= min_fails_14d]
    out.sort(key=lambda a: (-a["fails_14d"], -a["fails_today"]))
    for a in out:
        a["failed_sentences"] = a["failed_sentences"][:5]
    return out


async def _upsert_struggles(rows: list[dict]) -> tuple[int, int]:
    pool = await db.get_pool()
    inserted = updated = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            for r in rows:
                snapshot = {k: r[k] for k in
                            ("fails_today", "fails_14d", "seen_14d",
                             "failed_sentences")}
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
                    r["lang"], r["idiom"], r["gloss"] or None,
                    json.dumps(snapshot, ensure_ascii=False))
                inserted += 1 if row["inserted"] else 0
                updated += 0 if row["inserted"] else 1
    return inserted, updated


# ---------------------------------------------------------------------------
# 3. TEND — plan + generate missing ladder assets
# ---------------------------------------------------------------------------

def plan_generations(items: list[dict], assets_by_item: dict[int, list[dict]],
                     budget_usd: float, cost_per_image: float,
                     ) -> tuple[list[dict], list[str]]:
    """Pure planner: which (item, format) drafts to generate under the
    budget. Glyph for every active item without one; strike-1 comic where
    an anchor exists. Rejected attempts count toward the retry cap."""
    plan: list[dict] = []
    notes: list[str] = []
    spend = 0.0
    for it in items:
        if it["status"] != "active":
            continue
        have = assets_by_item.get(it["id"], [])

        def _n(fmt: str, live_only: bool = False) -> int:
            return sum(1 for a in have if a["format"] == fmt and
                       (a["status"] in ("draft", "approved") or not live_only))

        for fmt in ("glyph", "comic"):
            if fmt == "comic" and int(it.get("strike") or 1) != 1:
                continue
            if _n(fmt, live_only=True) > 0:
                continue
            if _n(fmt) >= _MAX_ATTEMPTS_PER_FORMAT:
                notes.append(f"{it['lang']}/{it['idiom']}: {fmt} retry cap "
                             f"reached ({_MAX_ATTEMPTS_PER_FORMAT}) — needs a "
                             "human look")
                continue
            if fmt == "comic" and not (it.get("anchor") or "").strip():
                notes.append(f"{it['lang']}/{it['idiom']}: comic needs an "
                             "authored anchor — skipped")
                continue
            if spend + cost_per_image > budget_usd:
                notes.append(f"budget stop at ${spend:.2f}: skipped "
                             f"{it['lang']}/{it['idiom']} {fmt} (and later)")
                return plan, notes
            spend += cost_per_image
            plan.append({"item_id": it["id"], "lang": it["lang"],
                         "idiom": it["idiom"], "format": fmt})
    return plan, notes


async def _auto_activate(max_new: int) -> list[str]:
    pool = await db.get_pool()
    rows = await pool.fetch(
        """
        UPDATE rescue_items SET status = 'active', strike = 1,
                                updated_at = NOW()
        WHERE id IN (
            SELECT id FROM rescue_items WHERE status = 'candidate'
            ORDER BY (struggle_snapshot->>'fails_14d')::int DESC NULLS LAST
            LIMIT $1)
        RETURNING lang, idiom
        """, max_new)
    return [f"{r['lang']}/{r['idiom']}" for r in rows]


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

async def run_autopilot(force: bool = False) -> dict:
    s = get_settings()
    report: dict[str, Any] = {
        "ran_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pull": None, "struggles": None, "activated": [],
        "generated": [], "notes": [], "errors": [], "spent_usd": 0.0,
    }
    if not s.rescue_autopilot_enabled and not force:
        report["notes"].append("autopilot disabled (rescue_autopilot_enabled)")
        return report

    # -- 1. PULL + 2. DIFF -------------------------------------------------
    if not s.ankiweb_hkey:
        report["errors"].append("ANKIWEB_HKEY not configured — no pull; "
                                "struggle data is stale")
    else:
        try:
            with tempfile.TemporaryDirectory(prefix="rescue-ap-") as wd:
                colpath = await asyncio.to_thread(_pull_collection_blocking, wd)
                struggles = compute_struggles(
                    colpath, s.rescue_struggle_min_fails_14d)
                ins, upd = await _upsert_struggles(struggles)
                report["pull"] = "ok"
                report["struggles"] = {"found": len(struggles),
                                       "new_items": ins, "refreshed": upd}
        except Exception as e:  # noqa: BLE001 — keep flying on stale data
            report["errors"].append(f"pull/diff failed: {repr(e)[:200]}")
            log.warning("rescue_autopilot.pull_failed", err=repr(e)[:300])

    # -- 3. TEND -----------------------------------------------------------
    report["activated"] = await _auto_activate(s.rescue_autopilot_max_new_items)

    provider = s.rescue_autopilot_provider
    if provider not in genmedia.autopilot_providers():
        report["errors"].append(
            f"provider {provider!r} is not autopilot-approved "
            f"({genmedia.autopilot_providers()}) — no generation")
        provider = None

    if provider:
        pool = await db.get_pool()
        items = [dict(r) for r in await pool.fetch(
            "SELECT * FROM rescue_items WHERE status = 'active' "
            "ORDER BY (struggle_snapshot->>'fails_14d')::int DESC NULLS LAST")]
        assets_by_item: dict[int, list[dict]] = {}
        for a in await pool.fetch(
                "SELECT id, item_id, format, status FROM rescue_assets"):
            assets_by_item.setdefault(a["item_id"], []).append(dict(a))
        cost = genmedia.estimate_image_cost(provider)
        plan, notes = plan_generations(
            items, assets_by_item, s.rescue_autopilot_budget_usd, cost)
        report["notes"].extend(notes)

        by_id = {it["id"]: it for it in items}
        for step in plan:
            it = by_id[step["item_id"]]
            senses = [dict(r) for r in await pool.fetch(
                "SELECT label, gloss, example_tl, example_en, ord "
                "FROM rescue_senses WHERE item_id = $1 ORDER BY ord",
                step["item_id"])]
            try:
                prompt = rescue.fill_template(step["format"], it, senses)
            except ValueError as e:
                report["notes"].append(
                    f"{step['lang']}/{step['idiom']}: {step['format']} "
                    f"template refused: {str(e)[:120]}")
                continue
            try:
                asset = await rescue_ops.generate_asset(
                    step["item_id"], step["format"], provider, prompt)
                report["generated"].append(
                    {"item": f"{step['lang']}/{step['idiom']}",
                     "format": step["format"], "asset_id": asset["id"],
                     "cost_usd": float(asset["cost_usd"])})
                report["spent_usd"] = round(
                    report["spent_usd"] + float(asset["cost_usd"]), 4)
            except Exception as e:  # noqa: BLE001 — one failure ≠ dead run
                report["errors"].append(
                    f"{step['lang']}/{step['idiom']} {step['format']}: "
                    f"{repr(e)[:200]}")
                log.warning("rescue_autopilot.generate_failed",
                            item=step["idiom"], err=repr(e)[:300])

    # -- 4. REPORT ---------------------------------------------------------
    await db.kv_set(KV_LAST, json.dumps(report, ensure_ascii=False))
    await db.kv_set(KV_LAST_RUN_TS, str(int(time.time())))
    log.info("rescue_autopilot.done",
             generated=len(report["generated"]),
             spent_usd=report["spent_usd"],
             errors=len(report["errors"]))
    return report


async def maybe_run_autopilot() -> None:
    """Worker hook: run if the interval elapsed. Never raises."""
    try:
        s = get_settings()
        if not s.rescue_autopilot_enabled:
            return
        last = await db.kv_get(KV_LAST_RUN_TS)
        if last and time.time() - int(last) < \
                s.rescue_autopilot_interval_hours * 3600:
            return
        await run_autopilot()
    except Exception as e:  # noqa: BLE001 — the worker loop must survive
        log.warning("rescue_autopilot.crashed", err=repr(e)[:300])
