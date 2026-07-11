"""Cached English narration cues (deck connective tissue).

Each list = variants of a short English phrase. The renderer picks one
deterministically per (idiom, key) so different cards sound varied without
being random across re-renders. Kore via Gemini Flash TTS reads each
variant exactly once; the mp3 is cached on disk and reused by every deck.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .. import gemini

# Multi-variant so the same card-build picks one deterministically by seed
# but different cards sound varied. Matches pimsleur's NARRATION shape.
GENERAL_NARRATION: dict[str, list[str]] = {
    "listen_context": [
        "Let's listen to this expression in context.",
        "Here it is in the original clip.",
        "First, let's hear it in the interview.",
        "Listen to the original.",
    ],
    "here_it_is": [
        "Here's the expression, on its own.",
        "And here is the expression by itself.",
        "Now, the expression alone.",
        "On its own:",
    ],
    "meaning": [
        "In English, that means:",
        "In English:",
        "That is to say, in English:",
        "Or in English:",
    ],
    "how_to_use": [
        "Here's how to use it.",
        "A quick note on usage.",
        "How it works.",
        "Some context for using it.",
    ],
    "examples_intro": [
        "Now listen to some examples.",
        "Here are some examples.",
        "Let's hear it used in a few sentences.",
        "Some examples to anchor it.",
    ],
    "practice_intro": [
        "Now let's practice. Listen to the English sentence, think of how to say it in {lang_name}, then hear the answer.",
        "Time to drill. Listen to each English sentence, mentally translate, then verify.",
        "Practice round. Hear the English, translate in your head, then check.",
    ],
    "sentence_1": ["Sentence one.", "Number one.", "First one."],
    "sentence_2": ["Sentence two.", "Number two.", "Next."],
    "sentence_3": ["Sentence three.", "Number three.", "And the last."],
}


def pick_general(narration_root: Path, key: str, seed: str,
                  lang_name: str | None = None) -> tuple[str, Path]:
    """Deterministic per-card pick for a general-narration cue."""
    variants = GENERAL_NARRATION.get(key, [])
    if not variants:
        return "", None  # type: ignore[return-value]
    idx = int(hashlib.sha1(f"gen::{key}::{seed}".encode()).hexdigest()[:8], 16) % len(variants)
    text = variants[idx]
    if lang_name and "{lang_name}" in text:
        text = text.replace("{lang_name}", lang_name)
    return text, cache_path(narration_root, f"gen_{key}", text)


def cache_path(narration_root: Path, key: str, text: str) -> Path:
    h = hashlib.sha1(text.encode()).hexdigest()[:10]
    return narration_root / f"narr_{key}_{h}.mp3"


async def ensure_lang_cached(narration_root: Path, lang_name: str,
                              voice_en: str = "Kore") -> None:
    """Pre-render the {lang_name}-substituted variants of practice_intro.
    Called once per language at process_video start."""
    narration_root.mkdir(parents=True, exist_ok=True)
    for v in GENERAL_NARRATION.get("practice_intro", []):
        if "{lang_name}" not in v:
            continue
        text = v.replace("{lang_name}", lang_name)
        p = cache_path(narration_root, "gen_practice_intro", text)
        if not p.exists():
            await gemini.synthesize(text, voice=voice_en, out=p)


async def ensure_cached(narration_root: Path, voice_en: str = "Kore") -> None:
    """Pre-render every general-narration cue once.

    Idempotent — only TTSes a path if its mp3 isn't already on disk.
    Call this at worker startup so audio rendering for individual cards
    never blocks on narration TTS round-trips.
    """
    narration_root.mkdir(parents=True, exist_ok=True)

    # General narration cues — render every variant of each. Skip the
    # practice_intro variants with {lang_name} placeholder, they're rendered
    # per-language at use-site via pick_general(..., lang_name=...).
    for key, variants in GENERAL_NARRATION.items():
        for v in variants:
            if "{lang_name}" in v:
                continue
            p = cache_path(narration_root, f"gen_{key}", v)
            if not p.exists():
                await gemini.synthesize(v, voice=voice_en, out=p)
