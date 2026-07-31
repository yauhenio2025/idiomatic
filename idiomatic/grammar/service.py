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
from . import explainers
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
    clusters = {t.key: t.cluster for t in topics_for(lang)}
    if lang in explainers.EXPLAINER_UNITS:
        listening = explainers.EXPLAINER_UNITS[lang]
        labels[listening.topic] = (listening.label, listening.symbol)
        clusters[listening.topic] = listening.cluster
    s = get_settings()
    audio_dir = Path(s.data_dir) / "staged_audio" / "grammar" / lang

    # Back-of-card TTS (form + pause + full sentence). Idempotent per item;
    # a TTS outage degrades those cards to text-only, retried next rebuild.
    # Authored explainers already have a fully stitched content-addressed MP3;
    # never replace it with the ordinary answer+sentence drill audio.
    drill_items = [item for item in items if item.get("fmt") != "explainer"]
    audio_map = await grammar_audio.ensure_audio(drill_items, lang)
    audio_map.update(explainers.prebuilt_audio_map(items, audio_dir))

    apkg_root = Path(s.data_dir) / "apkgs" / lang
    apkg_root.mkdir(parents=True, exist_ok=True)
    out = apkg_root / "_grammar.apkg"

    n = await asyncio.to_thread(
        lambda: build_grammar_apkg(out_path=out, lang=lang, items=items,
                                    topic_labels=labels,
                                    audio=audio_map, audio_dir=audio_dir,
                                    topic_clusters=clusters)
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


def claim_grammar_job(lang: str, mode: str) -> bool:
    """Atomically claim the web process's single grammar job slot.

    Admin handlers call this synchronously before scheduling their task, so a
    second request cannot slip into the check-to-first-coroutine-tick window.
    """
    if _state.get("running"):
        return False
    _state.clear()
    _state.update({"running": True, "lang": lang, "mode": mode,
                   "errors": []})
    return True


def claim_explainer_build(lang: str) -> bool:
    return claim_grammar_job(lang, "explainers")


async def run_explainer_build(lang: str, *, claimed: bool = False) -> None:
    """Render/upsert one language's authored lessons without rebuilding.

    Uses the grammar status state so generation, rebuild, and explainer TTS
    cannot overlap in the web process.  The explicit grammar-rebuild endpoint
    remains the only operation that packages and delivers a new deck.
    """
    if not claimed and not claim_explainer_build(lang):
        return
    try:
        result = await explainers.build_language(lang)
        _state["explainers"] = result
        _state["errors"] = list(result["failed"])
    except Exception as exc:  # noqa: BLE001 - background status must retain failure
        log.exception("grammar.explainers_build.failed", lang=lang)
        _state["errors"] = [repr(exc)[:500]]
    finally:
        _state["running"] = False
        _state["finished_at"] = datetime.now(timezone.utc).isoformat()


async def run_generation(lang: str, n_per_topic: int = 12,
                          only_topic: str | None = None, *,
                          claimed: bool = False) -> None:
    batch = f"{datetime.now(timezone.utc):%Y%m%d-%H%M}-{uuid.uuid4().hex[:6]}"
    # Personal-error F3 units contain teacher-attested pairs and are filled
    # only by grammar.f3.convert; they must never trigger generation or an
    # LLM verification call. Rebuilds still include them via topics_for().
    topics = [t for t in topics_for(lang) if t.verify != "attested"]
    if only_topic:
        # comma-separated topic keys → generate just those units
        keys = {k.strip() for k in only_topic.split(",") if k.strip()}
        topics = [t for t in topics if t.key in keys]
    if not claimed and not claim_grammar_job(lang, "generation"):
        return
    _state.clear()
    _state.update({"running": True, "lang": lang, "mode": "generation",
                   "batch": batch,
                   "topics_total": len(topics), "topics_done": 0,
                   "accepted": 0, "rejected": 0, "errors": []})
    try:
        for topic in topics:
            try:
                # Fresh LingQ vocab sample per topic — optional sentence
                # material so grammar reps double as vocab reminders.
                # Empty table / any failure → plain generation.
                try:
                    vocab = await db.sample_lingq_terms(lang, 15)
                except Exception:  # noqa: BLE001
                    vocab = []
                accepted, rejected = await generate.generate_batch(
                    topic, n_per_topic, extra_vocab=vocab)
                # A retry pass for the shortfall: one extra call max, only
                # if the verifier ate more than half the batch.
                if len(accepted) < n_per_topic // 2:
                    more_a, more_r = await generate.generate_batch(
                        topic, n_per_topic, extra_vocab=vocab)
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
