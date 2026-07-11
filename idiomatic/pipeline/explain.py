"""Per-expression structured explanation + 6 example sentences.

Two Gemini text calls per expression:

1. `generate_examples` — 6 example sentence pairs (target + English), HSK-style.
   First 3 are "teach" (front of card), last 3 are "drill" (back, with
   think-pause).

2. `generate_structured_explanation` — categorical notes (usage, collocations,
   antonyms, formal/colloquial synonyms, register, metaphor, pitfall,
   false-friend). Same shape as pimsleur's structured-explanation v2 — the
   playback layer turns each non-null field into "English connective tissue →
   target-language content" alternations.

Both run as a pair via `enrich_one` since they're tightly coupled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from .. import gemini
from ..langs import LANG_NAMES as _LANG_NAMES

log = structlog.get_logger()


# ---- example sentences -----------------------------------------------------

EXAMPLES_PROMPT = """You are creating 6 example sentences for an Anki card teaching the {lang_name} expression «{phrase}» (meaning: {english_gloss}).

Generate exactly 6 example sentences. Each one MUST:
- Use the expression «{phrase}» (or a natural conjugated/inflected form of it).
- Be at B1-B2 vocabulary level — testing comprehension of the EXPRESSION, not introducing new hard words.
- Reflect real spoken or written {lang_name} you'd actually encounter.
- Be DISTINCT from the others (different subjects, different contexts).

The first 3 will be played on the FRONT of the card (teach mode — paired with the translation). The last 3 will be played on the BACK (drill mode — learner translates, then hears the answer).

Output a JSON OBJECT:
{{
  "examples": [
    {{"target": "<{lang_name} sentence>", "en": "<English translation>"}},
    ... 6 entries total
  ]
}}

Output only the JSON object."""


# ---- structured explanation ------------------------------------------------

STRUCTURED_PROMPT = """You are writing a structured stylebook entry for the {lang_name} expression «{phrase}» (rough meaning: {english_gloss}).

The entry will be played back as audio on a flashcard: each non-null field is read in {lang_name} after a short English connective phrase ("a note on usage", "more casually", "the opposite would be"). So the structure matters — it's a series of discrete categorical notes, not a paragraph.

Output a JSON OBJECT. Fill ONLY fields where you have content GENUINELY USEFUL to a B2/C1 learner. Generic filler ("this is a useful phrase") is forbidden. Skip a field by setting it to null.

  "usage":               string|null — One sentence in {lang_name}, ≤30 words, what the expression does pragmatically. ALWAYS include.
  "collocations":        string|null — Typical {lang_name} subjects/objects/verbs in a tight sentence.
  "synonyms_formal":     string|null — Elevated/formal {lang_name} alternative, NAMED.
  "synonyms_neutral":    string|null — Neutral near-equivalent in {lang_name}, NAMED. Skip if obvious.
  "synonyms_colloquial": string|null — Colloquial/spoken {lang_name} variant, NAMED.
  "antonyms":            string|null — {lang_name} antonym(s), NAMED in a short sentence.
  "register_note":       string|null — One sentence on where it fits / where it'd jar.
  "metaphor":            string|null — One sentence on the image's origin, ONLY if pedagogically interesting.
  "pitfall":             string|null — One sentence on a real grammatical trap (case, gender, conjugation, separable prefix). Not generic.
  "false_friend":        string|null — Warning about a misleading English cognate, ONLY if there is one.

Rules:
- Every populated field is IN {lang_name} (no English mixed in).
- One sentence per field.
- Typical: 4-6 fields. Trivial expressions: 2-3. Rich ones: 7-8. Never fill all 10 just to fill.
- Output ONLY the JSON object."""


@dataclass(slots=True)
class Enriched:
    phrase: str
    english: str
    examples: list[dict]                # [{'target', 'en'}, ...] of length up to 6
    structured: dict[str, str]          # {'usage': '...', 'collocations': '...', ...}
    # Passed through from the source ExtractedPhrase by the worker so the
    # card layer can render them without re-querying.
    source_phrase_target: str = ""
    source_phrase_en: str = ""
    explanation_en: str = ""


async def generate_examples(phrase: str, english_gloss: str, lang: str) -> list[dict]:
    lang_name = _LANG_NAMES.get(lang, lang.upper())
    prompt = EXAMPLES_PROMPT.format(
        lang_name=lang_name, phrase=phrase, english_gloss=english_gloss,
    )
    raw = await gemini.generate_text(prompt, json_mode=True, temperature=0.6)
    if isinstance(raw, dict) and isinstance(raw.get("examples"), list):
        out: list[dict] = []
        for ex in raw["examples"][:6]:
            if not isinstance(ex, dict):
                continue
            tgt = (ex.get("target") or "").strip()
            en = (ex.get("en") or "").strip()
            if tgt and en:
                out.append({"target": tgt, "en": en})
        return out
    log.warning("explain.examples.unexpected_shape", phrase=phrase[:40])
    return []


async def generate_structured_explanation(phrase: str, english_gloss: str,
                                            lang: str) -> dict[str, str]:
    lang_name = _LANG_NAMES.get(lang, lang.upper())
    prompt = STRUCTURED_PROMPT.format(
        lang_name=lang_name, phrase=phrase, english_gloss=english_gloss,
    )
    raw = await gemini.generate_text(prompt, json_mode=True, temperature=0.4)
    if not isinstance(raw, dict):
        return {}
    keys = ["usage", "collocations", "synonyms_formal", "synonyms_neutral",
            "synonyms_colloquial", "antonyms", "register_note", "metaphor",
            "pitfall", "false_friend"]
    return {k: (raw.get(k) or "").strip() for k in keys
            if (raw.get(k) or "").strip()}


async def enrich_one(phrase: str, english_gloss: str, lang: str, *,
                      source_phrase_target: str = "",
                      source_phrase_en: str = "",
                      explanation_en: str = "") -> Enriched:
    """Run both LLM calls in parallel and return the bundle.

    Pass-through args (source_phrase_*, explanation_en) come from the
    upstream ExtractedPhrase and don't trigger new LLM calls — they were
    already obtained in the audio-extraction step.
    """
    import asyncio
    examples, structured = await asyncio.gather(
        generate_examples(phrase, english_gloss, lang),
        generate_structured_explanation(phrase, english_gloss, lang),
    )
    return Enriched(
        phrase=phrase, english=english_gloss,
        examples=examples, structured=structured,
        source_phrase_target=source_phrase_target,
        source_phrase_en=source_phrase_en,
        explanation_en=explanation_en,
    )
