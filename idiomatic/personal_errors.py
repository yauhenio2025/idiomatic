"""Personal error registry: JSONL validation + staging + cron-side ingest.

The registry (docs/commissions/CODEX_A_ERROR_REGISTRY.md schema) is
built OFFLINE on the operator's machine and uploaded as raw JSONL to
/admin/personal-errors-upload, which only validates it and does ONE
INSERT into personal_errors_staging. The CRON container parses and
batch-upserts on its next tick (ingest_staged). Rationale: two
web-process hangs during the LingQ bulk import taught us that bulk DB
writes never belong in the API process — and the cron container cannot
see /data (that mount is idiomatic-app's), so the DB is the handoff.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import structlog

from . import db

log = structlog.get_logger()

LANGS = {"fr", "pt", "es", "de", "it"}
KINDS = {"error", "reteach", "vocab_gap"}
CATEGORIES = {
    "preposition_selection", "verb_prep_regime", "gender", "agreement",
    "article_quantifier", "word_order", "negation", "pronoun_clitic",
    "relative", "tense_selection", "verb_morphology", "subjunctive",
    "passive", "case", "adjective_ending", "light_verb_collocation",
    "interference_lexical", "interference_morphological", "false_friend",
    "fixed_phrase", "derivation", "numbers_dates", "pronunciation",
    "vocabulary",
}
CONFIDENCES = {"high", "medium", "low", None}


def parse_jsonl(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate registry JSONL. Returns (rows, errors); errors carry
    line numbers. A row must satisfy the commission-A schema; unknown
    extra keys are dropped rather than rejected."""
    rows, errors = [], []
    for i, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError as e:
            errors.append(f"line {i}: bad JSON ({e})")
            continue
        lang = d.get("lang")
        kind = d.get("kind")
        cat = d.get("category")
        right = d.get("right")
        if lang not in LANGS:
            errors.append(f"line {i}: bad lang {lang!r}")
            continue
        if kind not in KINDS:
            errors.append(f"line {i}: bad kind {kind!r}")
            continue
        if cat not in CATEGORIES:
            errors.append(f"line {i}: bad category {cat!r}")
            continue
        if not right or not isinstance(right, str):
            errors.append(f"line {i}: missing right")
            continue
        if kind == "error" and not d.get("wrong"):
            errors.append(f"line {i}: kind=error without wrong")
            continue
        if d.get("confidence") not in CONFIDENCES:
            errors.append(f"line {i}: bad confidence {d.get('confidence')!r}")
            continue
        occ = d.get("occurrences")
        rows.append({
            "lang": lang, "kind": kind, "wrong": d.get("wrong"),
            "right_form": right, "gloss_en": d.get("gloss_en"),
            "category": cat, "subcategory": d.get("subcategory"),
            "why": d.get("why"),
            "interference_source": d.get("interference_source"),
            "occurrences": occ if isinstance(occ, int) and occ > 0 else 1,
            "first_seen": _date(d.get("first_seen")),
            "last_seen": _date(d.get("last_seen")),
            "sources": [s for s in (d.get("sources") or [])
                        if isinstance(s, str)],
            "unit_hint": d.get("unit_hint"),
            "confidence": d.get("confidence"),
        })
    return rows, errors


def _date(v):
    if not v or not isinstance(v, str):
        return None
    try:
        return datetime.strptime(v[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


async def ingest_staged(batch_size: int = 500) -> dict[str, Any] | None:
    """CRON-side: parse + batch-upsert every unprocessed staging row.
    Returns stats, or None when nothing is staged. A crash mid-ingest
    leaves processed_at NULL, so the next tick retries (upserts are
    idempotent). A payload that no longer validates is stamped with a
    note instead of retrying forever."""
    staged = await db.fetch_unprocessed_error_staging()
    if not staged:
        return None
    ingested = upserted = 0
    for s in staged:
        rows, errors = parse_jsonl(s["payload"])
        if errors:
            await db.mark_error_staging(
                s["id"], note=f"corrupt: {len(errors)} bad lines")
            log.warning("personal_errors.ingest_corrupt", staging_id=s["id"],
                         n_errors=len(errors), first=errors[:3])
            continue
        for i in range(0, len(rows), batch_size):
            upserted += await db.upsert_personal_errors(rows[i:i + batch_size])
        ingested += len(rows)
        await db.mark_error_staging(s["id"], note=f"ok: {len(rows)} rows")
    log.info("personal_errors.ingested", rows=ingested, upserted=upserted)
    return {"ingested": ingested, "upserted": upserted}
