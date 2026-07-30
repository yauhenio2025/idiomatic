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
from ..langs import LANG_NAMES as _LANG_NAMES
from .dedup import normalize

log = structlog.get_logger()


class WrongLanguageAudio(Exception):
    """The audio track is not in the channel's language — typically a
    YouTube auto-dubbed English track that the downloader picked instead
    of the original (rolled out widely mid-2026). Extracting from a dub
    yields cards whose 'context clip from the video' is English speech."""

    def __init__(self, detected: str, expected: str):
        self.detected = detected
        self.expected = expected
        super().__init__(f"audio language {detected!r} != expected {expected!r}")


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
    # Citation/dictionary form (verbs in infinitive, nouns in singular,
    # article kept where idiomatic). Shown on the card back so the
    # learner sees 'das Sagen haben', not just as-spoken 'hat das Sagen'.
    citation_form: str = ""
    # 2-3 sentence English explanation. TTS'd into the front audio and
    # displayed on the front of the card.
    explanation_en: str = ""
    # Window of the FULL source_phrase sentence — sliced into the
    # "context clip" so the learner hears the whole utterance, not just
    # the bare expression. Sanitized in from_dict: must contain the
    # expression window and stay under 45s, else falls back to the
    # expression window padded by 6s before / 3s after.
    sentence_start: float = 0.0
    sentence_end: float = 0.0

    @classmethod
    def from_dict(cls, d: dict) -> "ExtractedPhrase":
        text = (d.get("text") or "").strip()
        audio_start = float(d.get("audio_start") or 0.0)
        audio_end = float(d.get("audio_end") or 0.0)
        try:
            s_start = float(d.get("sentence_start"))
            s_end = float(d.get("sentence_end"))
        except (TypeError, ValueError):
            s_start = s_end = -1.0
        plausible = (0 <= s_start <= audio_start
                     and s_end >= audio_end
                     and 0 < s_end - s_start <= 45.0)
        if not plausible:
            s_start = max(0.0, audio_start - 6.0)
            s_end = audio_end + 3.0
        return cls(
            text=text,
            normalized=normalize(text),
            english=(d.get("english") or "").strip(),
            audio_start=audio_start,
            audio_end=audio_end,
            source_phrase_target=(d.get("source_phrase") or "").strip(),
            source_phrase_en=(d.get("source_phrase_en") or "").strip(),
            citation_form=(d.get("citation_form") or "").strip(),
            explanation_en=(d.get("explanation") or "").strip(),
            sentence_start=s_start,
            sentence_end=s_end,
        )




PROMPT_TMPL = """You are given the audio track of a video that is SUPPOSED to be in {lang_name}.

STEP 0 — LANGUAGE CHECK (do this first): determine the primary language actually SPOKEN in the audio. Many YouTube videos now carry AI-dubbed alternative audio tracks, so the speech may be English (or another language) even though the video is from a {lang_name} channel. Judge ONLY by what is spoken — never assume. Brief foreign-language quotes inside an otherwise {lang_name} video are fine; judge by the majority of the speech.

If the primary spoken language is NOT {lang_name}, output EXACTLY this JSON object and nothing else:
{{"audio_language": "<ISO 639-1 code of the language you actually hear>"}}

Only if the primary spoken language IS {lang_name}, continue:

Identify {n_target} of the most pedagogically valuable IDIOMATIC OR IDIOMATIC-BUT-COMMON expressions used in the audio. The audience is an advanced learner (B2/C1) who already knows everyday vocabulary and wants to acquire native-feeling expressions.

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
- `citation_form`: the expression in its CITATION (dictionary) form — verbs in the infinitive, nouns in the singular, keeping any article or pronoun that is part of the fixed expression. E.g. as-spoken "hat das Sagen" → citation_form "das Sagen haben"; "nous sommes gâtés" → "être gâté". If the as-spoken form IS already the citation form, repeat it.
- `source_phrase`: the FULL {lang_name} sentence from the audio that contained this expression — verbatim, including everything around it.
- `source_phrase_en`: a natural English translation of source_phrase.
- `explanation`: 2-3 sentence English explanation of what the expression means, when it's used, and what register / collocations / pitfalls a learner should know. Written like a textbook usage note, not a dictionary entry. Use simple English; the learner is B2/C1 so they understand the target language but the explanation is in English.
- `audio_start`: start time in seconds (float) of the expression itself.
- `audio_end`: end time in seconds (float) of the expression itself.
- `sentence_start`: start time in seconds (float) of the FULL sentence you
  transcribed in `source_phrase` (it must contain the expression window).
- `sentence_end`: end time in seconds (float) of that full sentence.

Pin `audio_start`/`audio_end` tightly to where the expression is actually
uttered, and `sentence_start`/`sentence_end` to the whole spoken sentence —
both windows are used to slice the audio for flashcards (the sentence window
lets the learner hear the expression in its real context).

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
    if isinstance(raw, dict) and raw.get("audio_language"):
        detected = str(raw["audio_language"]).strip().lower()[:8]
        if detected and detected != lang:
            log.warning("extract.wrong_language", expected=lang, detected=detected)
            raise WrongLanguageAudio(detected, lang)
        # Gemini says it IS the right language but used the escape shape —
        # treat as an empty extraction rather than crashing.
        raw = []
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
