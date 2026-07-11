"""Re-TTS silence placeholders left in /data/staged_audio.

TTS failures write ~600 B silent mp3s (see gemini.synthesize); before the
.silence-sidecar fix those were permanent and every pool rebuild baked
them in. This admin job walks the DB's audio references (the filename
alone doesn't say what text it should contain), finds staged files under
the silence-size threshold, and re-synthesizes them in place. Run
/admin/rebuild-pools?lang=… afterwards to bake healed audio into the
pool decks.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

from . import db, gemini
from .pipeline.audio import EN_VOICE, LANG_VOICE
from .settings import get_settings

log = structlog.get_logger()

# Anything smaller is a silence placeholder (real TTS output starts ~15 KB;
# the ffmpeg anullsrc stub is ~600 B). Same threshold as /admin/audio-audit.
SILENCE_MAX_BYTES = 5000

_state: dict = {"running": False}


def get_state() -> dict:
    return dict(_state)


async def _work_items() -> list[tuple[str, str, str]]:
    """(rel_audio_path, text, voice) for every audio reference in the DB."""
    pool = await db.get_pool()
    items: list[tuple[str, str, str]] = []
    idioms = await pool.fetch(
        """
        SELECT lang, idiom_text, english_gloss, audio_idiom_tgt, audio_idiom_en
        FROM expression_idioms
        """)
    for r in idioms:
        tgt_voice = LANG_VOICE.get(r["lang"], "Charon")
        if r["audio_idiom_tgt"]:
            items.append((r["audio_idiom_tgt"], r["idiom_text"], tgt_voice))
        if r["audio_idiom_en"]:
            items.append((r["audio_idiom_en"], r["english_gloss"], EN_VOICE))
    examples = await pool.fetch(
        """
        SELECT i.lang, e.en_text, e.target_text, e.audio_en, e.audio_target
        FROM expression_examples e
        JOIN expression_idioms i ON i.id = e.idiom_id
        """)
    for r in examples:
        tgt_voice = LANG_VOICE.get(r["lang"], "Charon")
        if r["audio_en"]:
            items.append((r["audio_en"], r["en_text"], EN_VOICE))
        if r["audio_target"]:
            items.append((r["audio_target"], r["target_text"], tgt_voice))
    return items


async def run_retts() -> dict:
    _state.update(running=True, scanned=0, silent=0, healed=0,
                  still_silent=0, errors=0)
    root = Path(get_settings().data_dir) / "staged_audio"
    try:
        items = await _work_items()
        _state["scanned"] = len(items)

        async def _one(rel: str, text: str, voice: str) -> None:
            p = root / rel
            if not (p.exists() and 0 < p.stat().st_size < SILENCE_MAX_BYTES):
                return
            _state["silent"] += 1
            # Synthesize to a sibling temp name and swap in only on success
            # — a crash mid-heal must not lose the existing staged file.
            tmp = p.with_name(".retts_" + p.name)
            try:
                tmp.unlink(missing_ok=True)
                await gemini.synthesize(text, voice=voice, out=tmp)
                if tmp.exists() and tmp.stat().st_size >= SILENCE_MAX_BYTES:
                    import os
                    os.replace(tmp, p)
                    gemini.silence_marker(p).unlink(missing_ok=True)
                    _state["healed"] += 1
                else:
                    _state["still_silent"] += 1
            except Exception as e:
                _state["errors"] += 1
                log.warning("retts.failed", path=rel, err=repr(e)[:150])
            finally:
                gemini.silence_marker(tmp).unlink(missing_ok=True)
                tmp.unlink(missing_ok=True)

        # gemini's TTS semaphore bounds actual API concurrency.
        await asyncio.gather(*[_one(*it) for it in items])
        log.info("retts.done", **{k: v for k, v in _state.items()
                                  if k != "running"})
        return get_state()
    finally:
        _state["running"] = False
