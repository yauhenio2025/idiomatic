"""Extract idiomatic expressions + timestamps from a video's audio.

ONE Gemini 3.5 Flash call with the mp3 inlined gets us:
  - the wording exactly as spoken
  - audio_start / audio_end timestamps (seconds)
  - a rough English gloss (for the dedup library)

Replaces the pimsleur Whisper + Gemini-regroup + Gemini-idiom-extract chain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import structlog

from .. import gemini
from .dedup import normalize

log = structlog.get_logger()


@dataclass(slots=True)
class ExtractedPhrase:
    text: str
    normalized: str
    english: str
    audio_start: float
    audio_end: float
    # Trigger sentence — the full sentence from the audio where the
    # expression appeared, both langs. Surfaced on the back of the card.
    source_phrase_target: str = ""
    source_phrase_en: str = ""
    # 2-3 sentence English explanation. TTS'd into the front audio and
    # displayed on the front of the card.
    explanation_en: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ExtractedPhrase":
        text = (d.get("text") or "").strip()
        return cls(
            text=text,
            normalized=normalize(text),
            english=(d.get("english") or "").strip(),
            audio_start=float(d.get("audio_start") or 0.0),
            audio_end=float(d.get("audio_end") or 0.0),
            source_phrase_target=(d.get("source_phrase") or "").strip(),
            source_phrase_en=(d.get("source_phrase_en") or "").strip(),
            explanation_en=(d.get("explanation") or "").strip(),
        )


_LANG_NAMES = {
    "de": "German", "fr": "French", "it": "Italian",
    "pt": "Portuguese", "es": "Spanish", "zh": "Mandarin",
    "nl": "Dutch", "sv": "Swedish", "no": "Norwegian", "da": "Danish",
}


PROMPT_TMPL = """You are listening to a {lang_name} video. Identify {n_target} of the most pedagogically valuable IDIOMATIC OR IDIOMATIC-BUT-COMMON expressions used in the audio. The audience is an advanced learner (B2/C1) who already knows everyday vocabulary and wants to acquire native-feeling expressions.

PREFER expressions that are:
- Set phrases, idioms, fixed collocations
- Non-obvious constructions (e.g. {lang_name}-specific grammar patterns)
- Function words used in non-trivial ways
- Vocabulary at B2/C1 level — challenging but not obscure literary register
- Phrases that recur in everyday speech, news, op-eds — not nonce expressions

AVOID:
- Trivial sentences (basic verbs + pronouns)
- Pure literary/classical register
- Proper-noun-heavy phrases
- Host filler ("welcome", "thanks for watching")
- Near-duplicates of each other

For EACH chosen expression, output:
- `text`: the expression itself as spoken in the audio, in the natural {lang_name} script. Just the expression, not the surrounding sentence.
- `english`: a brief English gloss (≤10 words).
- `source_phrase`: the FULL {lang_name} sentence from the audio that contained this expression — verbatim, including everything around it.
- `source_phrase_en`: a natural English translation of source_phrase.
- `explanation`: 2-3 sentence English explanation of what the expression means, when it's used, and what register / collocations / pitfalls a learner should know. Written like a textbook usage note, not a dictionary entry. Use simple English; the learner is B2/C1 so they understand the target language but the explanation is in English.
- `audio_start`: start time in seconds (float) of the expression itself.
- `audio_end`: end time in seconds (float) of the expression itself.

Pin the timestamps tightly to where the expression is actually uttered — they
will be used to slice the audio for flashcards.

Output a JSON ARRAY of {n_target} objects. ONLY the array, no preamble."""


async def extract_from_audio(
    audio_path: Path, lang: str, n_target: int = 12,
) -> list[ExtractedPhrase]:
    """Send the mp3 to Gemini 3.5 Flash. Returns extracted phrases."""
    lang_name = _LANG_NAMES.get(lang, lang.upper())
    prompt = PROMPT_TMPL.format(lang_name=lang_name, n_target=n_target)
    log.info("extract.calling_gemini", audio=str(audio_path), lang=lang,
             n_target=n_target, size_mb=round(audio_path.stat().st_size / 1e6, 2))

    raw = await gemini.generate_from_audio(prompt, audio_path,
                                            json_mode=True, temperature=0.3)
    if not isinstance(raw, list):
        log.warning("extract.unexpected_shape", got=type(raw).__name__)
        return []

    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            p = ExtractedPhrase.from_dict(item)
        except Exception as e:
            log.warning("extract.bad_item", item=item, err=str(e))
            continue
        if not p.text or p.audio_end <= p.audio_start:
            continue
        out.append(p)

    log.info("extract.done", n_returned=len(raw), n_valid=len(out))
    return out


def to_serializable(phrases: list[ExtractedPhrase]) -> list[dict]:
    """For JSON dumping / db inserts."""
    return [asdict(p) for p in phrases]
