"""LLM item generation + deterministic verification for grammar drills.

One Gemini call per (topic, batch); every returned item is checked
against morphology.py before it may be persisted. Rejected items are
persisted too (status='rejected') so the dashboard can show the LLM's
error rate per topic — that number is itself a finding.
"""

from __future__ import annotations

import unicodedata

import structlog

from .. import gemini
from .curriculum import Topic
from . import morphology

log = structlog.get_logger()

PERSON_LABEL = {
    "1s": "yo", "2s": "tú", "3s": "él/ella/usted",
    "1p": "nosotros", "2p": "vosotros", "3p": "ellos/ustedes",
}

# 2p (vosotros) is real but rare in the user's input diet; weight it down
# by simply asking for fewer of them.
PERSON_MIX = "1s, 2s, 3s, 1p, 3p freely; at most one vosotros (2p) item per batch"

_PROMPT = """You are writing Spanish conjugation drill cards for ONE advanced \
adult learner (reads Spanish news daily; interests: geopolitics, tech \
criticism, history, media). Target: {label} — mood "{mood}", tense "{tense}".

Produce {n} items as a JSON array. Each item:
{{
  "infinitive": "...",          // pick from: {verbs}
  "person": "...",              // one of 1s 2s 3s 1p 2p 3p ({person_mix})
  "sentence": "...",            // Spanish sentence, 7-16 words, with the verb \
replaced by ___ followed by the infinitive in parentheses: "Ayer el ministro \
___ (negar) las acusaciones."
  "answer": "...",              // the conjugated form alone, e.g. "negó"
  "gloss_en": "...",            // natural English translation of the full sentence
  "why": "..."                  // ONE short English line: why this tense/form \
here. Empty string if obvious.
}}

HARD RULES — items violating any of these are discarded by a verifier:
1. The sentence context must make the tense UNAMBIGUOUS: include a time \
expression or trigger so that no other tense fits naturally. {guidance}
2. The subject/person must be explicit or unambiguous in the sentence \
(pronoun, name, or noun phrase) — the reader must be able to derive the \
person without guessing.
3. "answer" must be exactly the single conjugated form for that mood/tense/\
person (compound tenses: include the auxiliary, e.g. "ha negado").
4. Every sentence about real-world content must be generic enough to be \
timelessly true or clearly hypothetical — no invented breaking news presented \
as fact.
5. Vary subjects, verbs, and persons across the batch; no two sentences with \
the same verb+person.
6. Content in Spanish only (European Spanish; use vosotros only when person \
is 2p).

Return ONLY the JSON array."""


def _strip_accents_eq(a: str, b: str) -> bool:
    d = lambda s: "".join(c for c in unicodedata.normalize("NFD", s)
                          if unicodedata.category(c) != "Mn")
    return d(a) == d(b)


def build_prompt(topic: Topic, n: int) -> str:
    return _PROMPT.format(
        label=topic.label, mood=topic.mood, tense=topic.tense, n=n,
        verbs=", ".join(topic.verbs), person_mix=PERSON_MIX,
        guidance=topic.guidance,
    )


def verify_item(topic: Topic, item: dict) -> tuple[bool, str]:
    """Deterministic checks. Returns (ok, reason-if-rejected)."""
    inf = (item.get("infinitive") or "").strip().lower()
    person = (item.get("person") or "").strip().lower()
    sentence = (item.get("sentence") or "").strip()
    answer = (item.get("answer") or "").strip()

    if person not in morphology.PERSONS:
        return False, f"bad person {person!r}"
    if "___" not in sentence:
        return False, "no blank in sentence"
    if not answer:
        return False, "empty answer"

    ok, expected = morphology.verify(topic.lang, inf, topic.mood, topic.tense,
                                     person, answer)
    if expected is None:
        return False, f"verb {inf!r} not in morphology DB"
    if not ok:
        if _strip_accents_eq(answer.lower(), expected):
            return False, f"accent error: {answer!r} vs {expected!r}"
        return False, f"wrong form: {answer!r}, expected {expected!r}"

    # The answer must not also appear verbatim outside the blank (a cue
    # that gives the answer away, or a duplicated verb).
    if answer.lower() in sentence.lower().replace("___", " "):
        return False, "answer leaks in sentence"
    return True, ""


async def generate_batch(topic: Topic, n: int) -> tuple[list[dict], list[dict]]:
    """Returns (accepted, rejected); each item dict is augmented with
    mood/tense/topic keys ready for DB insert."""
    raw = await gemini.generate_text(build_prompt(topic, n), json_mode=True,
                                     temperature=0.7)
    if isinstance(raw, dict):        # model wrapped the array in an object
        raw = next((v for v in raw.values() if isinstance(v, list)), [])
    if not isinstance(raw, list):
        log.warning("grammar.gen.bad_payload", topic=topic.key, type=str(type(raw)))
        return [], []

    accepted, rejected = [], []
    seen_keys: set[tuple[str, str]] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        base = {
            "lang": topic.lang, "topic": topic.key,
            "infinitive": (item.get("infinitive") or "").strip().lower(),
            "mood": topic.mood, "tense": topic.tense,
            "person": (item.get("person") or "").strip().lower(),
            "sentence": (item.get("sentence") or "").strip(),
            "answer": (item.get("answer") or "").strip(),
            "gloss_en": (item.get("gloss_en") or "").strip(),
            "why_en": (item.get("why") or "").strip(),
        }
        ok, reason = verify_item(topic, item)
        key = (base["infinitive"], base["person"])
        if ok and key in seen_keys:
            ok, reason = False, "duplicate verb+person in batch"
        if ok:
            seen_keys.add(key)
            accepted.append(base)
        else:
            base["reject_reason"] = reason
            rejected.append(base)

    log.info("grammar.gen.batch", topic=topic.key, requested=n,
             returned=len(raw), accepted=len(accepted), rejected=len(rejected))
    return accepted, rejected
