"""LingQ vocabulary sync (Wave: vocab-aware generation).

Pulls the user's saved vocabulary ("cards"/LingQs) from the LingQ API v2
— officially undocumented these days but fully alive — into the
`lingq_terms` table, so exercise generation can weave the learner's own
studied vocabulary into grammar drills (and any local agent can pull
samples via /admin/lingq-sample).

Auth: a long-lived API token stored in `external_tokens` (name
'lingq'), set once via POST /admin/lingq-token. NEVER in the repo/env —
the repo is public.

Sync strategy: full paginated re-fetch per language, upsert on
lingq_id. ~52k terms / ~270 requests across 10 languages — cheap enough
that incremental diffing isn't worth the states it would add. The cron
triggers a sync when the last one is older than settings.
lingq_sync_interval_hours (new LingQs "will not happen a lot" — user).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog

from . import db

log = structlog.get_logger()

_BASE = "https://www.lingq.com/api/v2"
_PAGE_SIZE = 200
_STATE: dict[str, Any] = {"running": False}


def get_state() -> dict[str, Any]:
    return dict(_STATE)


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Token {token}"}


async def _get_json(client: httpx.AsyncClient, url: str, token: str,
                    tries: int = 3) -> dict:
    for attempt in range(tries):
        try:
            r = await client.get(url, headers=_headers(token), timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001 — retry any transient failure
            if attempt == tries - 1:
                raise
            log.warning("lingq.retry", url=url[:80], err=repr(e)[:120])
            await asyncio.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def _row_from_card(lang: str, c: dict) -> dict | None:
    term = (c.get("term") or "").strip()
    pk = c.get("pk")
    if not term or pk is None:
        return None
    hints = [{"locale": h.get("locale"), "text": h.get("text")}
             for h in (c.get("hints") or []) if h.get("text")]
    return {
        "lingq_id": pk,
        "lang": lang,
        "term": term,
        "fragment": (c.get("fragment") or "").strip() or None,
        "hints": hints,
        "status": c.get("status"),
        "extended_status": c.get("extended_status"),
        "notes": (c.get("notes") or "").strip() or None,
        "tags": c.get("tags") or [],
        "srs_due_date": c.get("srs_due_date"),
    }


async def discover_languages(token: str) -> list[str]:
    async with httpx.AsyncClient() as client:
        data = await _get_json(
            client, f"{_BASE}/contexts/?page_size=50", token)
    rows = data.get("results", data if isinstance(data, list) else [])
    return [r["language"]["code"] for r in rows
            if r.get("language", {}).get("code")]


async def sync_language(client: httpx.AsyncClient, token: str,
                        lang: str) -> tuple[int, int]:
    """Returns (fetched, upserted)."""
    fetched = upserted = 0
    url = f"{_BASE}/{lang}/cards/?page_size={_PAGE_SIZE}"
    while url:
        data = await _get_json(client, url, token)
        rows = [r for r in (_row_from_card(lang, c)
                            for c in data.get("results", [])) if r]
        fetched += len(data.get("results", []))
        upserted += await db.upsert_lingq_terms(rows)
        url = data.get("next")
        _STATE["progress"] = f"{lang}: {fetched}"
        # Politeness to LingQ AND breathing room for our own shared DB /
        # event loop — the web app serving /health lives in this process.
        await asyncio.sleep(1.0)
    return fetched, upserted


async def run_sync(langs: list[str] | None = None) -> None:
    token = await db.get_external_token("lingq")
    if not token:
        _STATE.update({"running": False,
                       "error": "no lingq token stored "
                                "(POST /admin/lingq-token first)"})
        return
    _STATE.clear()
    _STATE.update({"running": True, "started_at":
                   datetime.now(timezone.utc).isoformat(), "langs": {}})
    try:
        targets = langs or await discover_languages(token)
        async with httpx.AsyncClient() as client:
            for lang in targets:
                try:
                    fetched, upserted = await sync_language(client, token, lang)
                    _STATE["langs"][lang] = {"fetched": fetched,
                                             "upserted": upserted}
                except Exception as e:  # noqa: BLE001 — one lang must not kill the run
                    log.warning("lingq.lang_failed", lang=lang,
                                err=repr(e)[:200])
                    _STATE["langs"][lang] = {"error": repr(e)[:200]}
        await db.set_kv("lingq_last_sync",
                        datetime.now(timezone.utc).isoformat())
    finally:
        _STATE["running"] = False
        _STATE["finished_at"] = datetime.now(timezone.utc).isoformat()
        log.info("lingq.sync_done", langs=_STATE.get("langs"))
