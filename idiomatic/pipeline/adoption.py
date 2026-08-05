"""Anki-collection reconciliation support.

The user's Anki collection can hold idiomatic-generated notes whose
source rows no longer exist in the DB (video purges, example
regeneration — imports never delete). Two admin surfaces deal with
this:

  GET  /admin/anki-guids     — every note guid the CURRENT DB content
                               generates, computed with the exact same
                               _guid/_norm code the builders use, so a
                               client can diff its collection against
                               the live catalog with zero recipe drift.
  POST /admin/adopt-orphans  — upsert studied orphan notes (full field
                               content + study stats) into the
                               adopted_notes table so the remediation
                               pipeline can still target them.

Orphan policy (user directive 2026-08-05): studied orphans are adopted
back into the DB; never-studied orphans are deleted from the collection
via the add-on's cleanup.json mechanism.
"""

from __future__ import annotations

import json

from .. import db
from .apkg import _guid as _video_guid
from .pool import _guid as _pool_guid, _norm


async def current_guids() -> dict:
    """Flat set of every guid the current catalog would emit, per kind."""
    langs = await db.expression_langs()
    kinds: dict[str, set[str]] = {
        "video": set(), "pool_idioms": set(),
        "pool_expr": set(), "pool_idiom_t2e": set(), "pool_idiom_e2t": set(),
    }
    for lang in langs:
        idioms = await db.fetch_pool_idioms(lang)
        for it in idioms:
            idiom_text = it["idiom_text"]
            n = _norm(idiom_text)
            if it.get("youtube_id"):
                kinds["video"].add(
                    _video_guid(it["youtube_id"], idiom_text.lower().strip()))
            kinds["pool_idioms"].add(_pool_guid(f"yt-idiom-pool::{lang}", n))
            kinds["pool_idiom_t2e"].add(_pool_guid("yt-pool-t2e", n))
            kinds["pool_idiom_e2t"].add(_pool_guid("yt-pool-e2t", n))
            for ex in it.get("examples", []):
                kinds["pool_expr"].add(
                    _pool_guid("yt-pool", n, _norm(ex["target_text"])))
    return {
        "langs": langs,
        "counts": {k: len(v) for k, v in kinds.items()},
        "guids": {k: sorted(v) for k, v in kinds.items()},
    }


async def adopt_notes(notes: list[dict]) -> int:
    """Upsert orphan notes; returns number of rows written."""
    cleaned = []
    for n in notes:
        guid = n.get("guid")
        if not guid or not isinstance(n.get("fields"), list):
            continue
        cleaned.append({
            "guid": guid,
            "lang": n.get("lang"),
            "model": n.get("model") or "unknown",
            "deck": n.get("deck"),
            "fields": json.dumps(n["fields"]),
            "tags": n.get("tags") or [],
            "reps": int(n.get("reps") or 0),
            "lapses": int(n.get("lapses") or 0),
            "last_review_ms": n.get("last_review_ms"),
        })
    if not cleaned:
        return 0
    return await db.upsert_adopted_notes(cleaned)
