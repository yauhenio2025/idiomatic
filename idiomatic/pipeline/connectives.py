"""Cached English connective phrases that introduce each section of a
structured explanation. Same shape as pimsleur's EXPLANATION_CONNECTIVES.

Each list = variants of a short English phrase. The renderer picks one
deterministically per (idiom, key) so different cards sound varied without
being random across re-renders. The Sarah-equivalent voice (Kore via
Gemini Flash TTS) reads each variant exactly once, and we cache the mp3
on disk so subsequent decks reuse them.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .. import gemini

EXPLANATION_CONNECTIVES: dict[str, list[str]] = {
    "usage": [
        "A note on usage.",
        "Here's what it actually does.",
        "Some context.",
        "First, what it really means.",
    ],
    "collocations": [
        "It typically appears with these words.",
        "Common collocations.",
        "Words that often turn up alongside it.",
        "Watch for these companion words.",
    ],
    "synonyms_formal": [
        "A more formal alternative.",
        "In elevated speech.",
        "A higher-register variant.",
        "If you want to sound more polished.",
    ],
    "synonyms_neutral": [
        "A close synonym.",
        "Another way to put it.",
        "A near-equivalent.",
    ],
    "synonyms_colloquial": [
        "More casually.",
        "In everyday speech.",
        "A colloquial variant.",
    ],
    "antonyms": [
        "The opposite.",
        "An antonym.",
        "Now flip it.",
        "If you wanted to say the opposite.",
    ],
    "register_note": [
        "A note on register.",
        "Where this fits — and where it doesn't.",
        "On tone.",
    ],
    "metaphor": [
        "Where the image comes from.",
        "The picture behind it.",
        "A note on the metaphor.",
    ],
    "pitfall": [
        "Watch out.",
        "A common trap.",
        "A grammatical pitfall.",
        "Mind this one.",
    ],
    "false_friend": [
        "Don't confuse it with the English.",
        "A false-friend warning.",
        "Watch the English cognate.",
    ],
}


# Narration cues used outside the structured-explanation section.
GENERAL_NARRATION: dict[str, str] = {
    "listen_context":  "Let's listen to this expression in context.",
    "here_it_is":      "Here's the expression, on its own.",
    "meaning":         "In English, that means:",
    "examples_intro":  "Now listen to some examples.",
    "practice_intro":  "Now let's practice. Listen to the English, think of the {lang_name} translation, then hear the answer.",
    "sentence_1":      "Sentence one.",
    "sentence_2":      "Sentence two.",
    "sentence_3":      "Sentence three.",
}


def cache_path(narration_root: Path, key: str, text: str) -> Path:
    h = hashlib.sha1(text.encode()).hexdigest()[:10]
    return narration_root / f"narr_{key}_{h}.mp3"


def pick_connective(narration_root: Path, key: str, seed: str) -> tuple[str, Path]:
    """Deterministic per-card pick. Returns (text, expected_mp3_path)."""
    variants = EXPLANATION_CONNECTIVES.get(key, [])
    if not variants:
        return "", None  # type: ignore[return-value]
    idx = int(hashlib.sha1(f"{key}::{seed}".encode()).hexdigest()[:8], 16) % len(variants)
    text = variants[idx]
    return text, cache_path(narration_root, f"expl_{key}", text)


async def ensure_cached(narration_root: Path, voice_en: str = "Kore") -> None:
    """Pre-render every connective variant + general-narration cue once.

    Idempotent — only TTSes a path if its mp3 isn't already on disk.
    Call this at worker startup so audio rendering for individual cards
    never blocks on connective TTS round-trips.
    """
    narration_root.mkdir(parents=True, exist_ok=True)

    # Connective variants (multiple per key)
    for key, variants in EXPLANATION_CONNECTIVES.items():
        for v in variants:
            p = cache_path(narration_root, f"expl_{key}", v)
            if not p.exists():
                await gemini.synthesize(v, voice=voice_en, out=p)

    # General narration cues (one per key, but with {lang_name} placeholder
    # left raw because we render per-language at use time)
    for key, text in GENERAL_NARRATION.items():
        if "{lang_name}" in text:
            continue  # filled in at use site
        p = cache_path(narration_root, f"gen_{key}", text)
        if not p.exists():
            await gemini.synthesize(text, voice=voice_en, out=p)
