"""Extract idiomatic expressions + timestamps from a video's audio.

Ported from pimsleur/scraper/idioms.py but: (1) single Gemini call against
the audio rather than transcribe-then-extract, (2) returns timestamps in
seconds so we can slice the source mp3 for per-card audio.

M1 — stub. M2 — implement against `gemini-3.5-flash` with `inlineData`
audio input.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ExtractedPhrase:
    text: str           # the wording exactly as spoken
    normalized: str     # lowercased + whitespace-collapsed for dedup
    english: str        # rough gloss for the dedup library
    audio_start: float  # seconds
    audio_end: float    # seconds


async def extract_from_audio(audio_path, lang: str, n_target: int = 12) -> list[ExtractedPhrase]:
    """Send the mp3 to Gemini 3.5 Flash. Get back idiomatic phrases + timestamps."""
    raise NotImplementedError("M2")
