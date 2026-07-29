"""Orchestrates a grammar generation run: for each topic, generate with
Gemini, verify deterministically, persist both verdicts, then rebuild the
language's rolling grammar apkg and upsert its delivery row. Runs as an
API background task (same pattern as retts/backfills)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from .. import db
from ..settings import get_settings
from . import audio as grammar_audio
from . import generate
from .apkg import build_grammar_apkg
from .curriculum import topics_for

log = structlog.get_logger()

_state: dict[str, Any] = {"running": False}


def get_state() -> dict[str, Any]:
    return dict(_state)


async def rebuild_grammar_deck(lang: str) -> dict[str, Any]:
    """Compile ALL verified items for lang into the rolling deck and
    upsert the apkgs row (kind='grammar')."""
    items = await db.fetch_grammar_items(lang, status="verified")
    if not items:
        return {"lang": lang, "cards": 0, "skipped": "no verified items"}

    labels = {t.key: (t.label, t.symbol) for t in topics_for(lang)}
    s = get_settings()

    # Back-of-card TTS (form + pause + full sentence). Idempotent per item;
    # a TTS outage degrades those cards to text-only, retried next rebuild.
    audio_map = await grammar_audio.ensure_audio(items, lang)
    audio_dir = Path(s.data_dir) / "staged_audio" / "grammar" / lang

    apkg_root = Path(s.data_dir) / "apkgs" / lang
    apkg_root.mkdir(parents=True, exist_ok=True)
    out = apkg_root / "_grammar.apkg"

    n = await asyncio.to_thread(
        lambda: build_grammar_apkg(out_path=out, lang=lang, items=items,
                                    topic_labels=labels,
                                    audio=audio_map, audio_dir=audio_dir)
    )
    rel = out.relative_to(Path(s.data_dir))
    apkg_id = await db.upsert_pool_apkg(
        lang=lang, kind="grammar", filename=str(rel),
        size_bytes=out.stat().st_size, n_idioms=n,
    )
    log.info("grammar.deck.upserted", lang=lang, apkg_id=apkg_id, cards=n,
             with_audio=len(audio_map))
    return {"lang": lang, "cards": n, "apkg_id": apkg_id,
            "with_audio": len(audio_map)}


async def run_generation(lang: str, n_per_topic: int = 12,
                          only_topic: str | None = None) -> None:
    batch = f"{datetime.now(timezone.utc):%Y%m%d-%H%M}-{uuid.uuid4().hex[:6]}"
    topics = topics_for(lang)
    if only_topic:
        # comma-separated topic keys → generate just those units
        keys = {k.strip() for k in only_topic.split(",") if k.strip()}
        topics = [t for t in topics if t.key in keys]
    _state.clear()
    _state.update({"running": True, "lang": lang, "batch": batch,
                   "topics_total": len(topics), "topics_done": 0,
                   "accepted": 0, "rejected": 0, "errors": []})
    try:
        for topic in topics:
            try:
                accepted, rejected = await generate.generate_batch(topic, n_per_topic)
                # A retry pass for the shortfall: one extra call max, only
                # if the verifier ate more than half the batch.
                if len(accepted) < n_per_topic // 2:
                    more_a, more_r = await generate.generate_batch(topic, n_per_topic)
                    accepted += more_a
                    rejected += more_r
                ins_a = await db.insert_grammar_items(accepted, status="verified",
                                                       batch=batch)
                ins_r = await db.insert_grammar_items(rejected, status="rejected",
                                                       batch=batch)
                _state["accepted"] += ins_a
                _state["rejected"] += ins_r
            except Exception as exc:  # noqa: BLE001 — one topic must not kill the run
                log.exception("grammar.topic_failed", topic=topic.key)
                _state["errors"].append(f"{topic.key}: {exc}")
            _state["topics_done"] += 1

        result = await rebuild_grammar_deck(lang)
        _state["deck"] = result
    finally:
        _state["running"] = False
        _state["finished_at"] = datetime.now(timezone.utc).isoformat()
        log.info("grammar.run_done", **{k: v for k, v in _state.items()
                                         if k != "errors"})
