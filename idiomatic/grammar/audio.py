"""Back-of-card audio for grammar drills: the answer, a beat of silence,
then the corrected sentence — target-language ElevenLabs voice via
gemini.synthesize (Gemini TTS fallback, same as the idiom pipeline).

Files persist under /data/staged_audio/grammar/<lang>/ (the janitor only
sweeps media_stage, so these survive) and are re-used across rebuilds:
only items without a good mp3 get TTS'd. Media filename = idg_<lang>_<id>
— if an item's TEXT ever changes after audio exists, bump the `rev` in
the filename instead of overwriting (media sync detects changes by
filename only).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

from .. import gemini
from ..pipeline.audio import LANG_VOICE, concat_mp3s, silence_mp3
from ..settings import get_settings

log = structlog.get_logger()


def full_sentence_text(sentence: str, answer: str, infinitive: str,
                       fmt: str = "cloze") -> str:
    """Return the corrected sentence spoken after the answer.

    Existing cloze callers replace the blank as before. An F3 front is the
    learner's wrong phrase and deliberately has no blank, so its corrected
    sentence is the answer itself.
    """
    if fmt == "f3":
        return answer
    for pat in (f"___ ({infinitive})", f"___  ({infinitive})", "___"):
        if pat in sentence:
            return sentence.replace(pat, answer, 1)
    return sentence


def _item_sentence_text(item: dict) -> str:
    """Correct sentence spoken after the answer for any grammar format."""
    return full_sentence_text(item["sentence"], item["answer"],
                              item.get("infinitive") or "",
                              item.get("fmt") or "cloze")


def _media_name(lang: str, item_id: int) -> str:
    return f"idg_{lang}_{item_id}.mp3"


async def ensure_item_audio(item: dict, lang: str) -> Path | None:
    """Build (or reuse) the back-audio mp3 for one item. Returns the file
    path, or None if TTS degraded to silence (caller ships the card
    text-only; a later rebuild retries)."""
    s = get_settings()
    stage = Path(s.data_dir) / "staged_audio" / "grammar" / lang
    stage.mkdir(parents=True, exist_ok=True)
    final = stage / _media_name(lang, item["id"])
    if final.exists() and final.stat().st_size > 1000:
        return final

    voice = LANG_VOICE.get(lang, "Charon")
    work = stage / "_work"
    work.mkdir(exist_ok=True)
    answer_mp3 = work / f"{item['id']}_answer.mp3"
    sentence_mp3 = work / f"{item['id']}_sentence.mp3"
    sentence = _item_sentence_text(item)

    await asyncio.gather(
        gemini.synthesize(item["answer"], voice=voice, out=answer_mp3, lang=lang),
        gemini.synthesize(sentence, voice=voice, out=sentence_mp3, lang=lang),
    )
    # synthesize never raises; failures become flagged silence placeholders.
    if (gemini.silence_marker(answer_mp3).exists()
            or gemini.silence_marker(sentence_mp3).exists()):
        log.warning("grammar.audio.silence_skip", item=item["id"], lang=lang)
        return None

    gap = await asyncio.to_thread(silence_mp3, work, 700)
    await asyncio.to_thread(concat_mp3s, [answer_mp3, gap, sentence_mp3], final)
    return final


async def ensure_audio(items: list[dict], lang: str) -> dict[int, str]:
    """TTS all items missing audio. Returns {item_id: media_filename} for
    every item that has a usable mp3. Concurrency is bounded by the global
    TTS semaphore inside gemini.synthesize."""
    results: dict[int, str] = {}

    async def _one(it: dict) -> None:
        try:
            p = await ensure_item_audio(it, lang)
            if p is not None:
                results[it["id"]] = p.name
        except Exception as e:  # noqa: BLE001 — audio must never block the deck
            log.warning("grammar.audio.failed", item=it["id"], err=repr(e)[:200])

    await asyncio.gather(*(_one(it) for it in items))
    log.info("grammar.audio.done", lang=lang, with_audio=len(results),
             total=len(items))
    return results
