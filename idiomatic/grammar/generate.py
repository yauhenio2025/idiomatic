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


_PROMPT_CLOSED = """You are writing Spanish grammar drill cards for ONE advanced \
adult learner (reads Spanish news daily; interests: geopolitics, tech \
criticism, history, media). Target: {label}.

Produce {n} items as a JSON array. Each item:
{{
  "sentence": "...",   // Spanish sentence(s), 8-20 words, with ONE blank ___ \
whose content is exactly one entry from the inventory below. A two-part \
sentence (question + answer, or two clauses) is fine.
  "answer": "...",     // the blank's content, exactly one inventory entry
  "gloss_en": "...",   // natural English translation of the full text
  "why": "..."         // ONE short English line naming the rule that decides \
the answer
}}

The inventory (closed set — answers come ONLY from here): {inventory}

HARD RULES — items violating any of these are discarded by a verifier:
1. The context must make the answer UNIQUELY determined: an expert filling \
the blank without seeing your answer must arrive at exactly it. {guidance}
2. The answer must NOT also appear verbatim elsewhere in the sentence.
3. European Spanish only. Vary structures and persons; no two sentences may \
share the same opening words.
4. Real-world content must be timelessly true or clearly hypothetical.

Return ONLY the JSON array."""


def _strip_accents_eq(a: str, b: str) -> bool:
    d = lambda s: "".join(c for c in unicodedata.normalize("NFD", s)
                          if unicodedata.category(c) != "Mn")
    return d(a) == d(b)


def _norm_answer(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or "").strip().lower())
    s = s.strip(".,;:!?¡¿\"'«»")
    return " ".join(s.split())


def _bank_lines(topic: Topic, n: int) -> str:
    """Sample regime pairs from the topic's data bank into prompt lines."""
    if not topic.bank:
        return ""
    import json
    import random
    from pathlib import Path
    path = Path(__file__).parent / "data" / topic.bank
    entries = json.loads(path.read_text(encoding="utf-8"))
    picked = random.sample(entries, min(2 * n, len(entries)))
    lines = "\n".join(
        f"- {e['verb']} + {e['prep']} — {e['en']} (trap: {e['trap']})"
        for e in picked)
    return f"\n\nRegime pairs to draw from (one verb per sentence):\n{lines}"


def build_prompt(topic: Topic, n: int) -> str:
    if topic.verify == "blind":
        return _PROMPT_CLOSED.format(
            label=topic.label, n=n,
            inventory=", ".join(topic.answer_set or []) or "(open)",
            guidance=topic.guidance,
        ) + _bank_lines(topic, n)
    return _PROMPT.format(
        label=topic.label, mood=topic.mood, tense=topic.tense, n=n,
        verbs=", ".join(topic.verbs), person_mix=PERSON_MIX,
        guidance=topic.guidance,
    )


def _answer_leaks(sentence: str, answer: str) -> bool:
    """Word-boundary leak check — substring matching false-flags short
    closed-class answers ('lo' inside 'los')."""
    import re
    rest = sentence.replace("___", " ")
    return re.search(rf"(?<![\wáéíóúüñ]){re.escape(answer)}(?![\wáéíóúüñ])",
                     rest, re.IGNORECASE) is not None


def verify_item(topic: Topic, item: dict) -> tuple[bool, str]:
    """Static checks (no network). Returns (ok, reason-if-rejected).
    Blind topics additionally require verify_blind() to pass."""
    sentence = (item.get("sentence") or "").strip()
    answer = (item.get("answer") or "").strip()

    if "___" not in sentence:
        return False, "no blank in sentence"
    if not answer:
        return False, "empty answer"
    if _answer_leaks(sentence, answer):
        return False, "answer leaks in sentence"

    if topic.verify == "blind":
        if topic.answer_set is not None:
            allowed = {_norm_answer(a) for a in topic.answer_set}
            if _norm_answer(answer) not in allowed:
                return False, f"answer {answer!r} not in closed inventory"
        return True, ""

    inf = (item.get("infinitive") or "").strip().lower()
    person = (item.get("person") or "").strip().lower()
    if person not in morphology.PERSONS:
        return False, f"bad person {person!r}"
    ok, expected = morphology.verify(topic.lang, inf, topic.mood, topic.tense,
                                     person, answer)
    if expected is None:
        return False, f"verb {inf!r} not in morphology DB"
    if not ok:
        if _strip_accents_eq(answer.lower(), expected):
            return False, f"accent error: {answer!r} vs {expected!r}"
        return False, f"wrong form: {answer!r}, expected {expected!r}"
    return True, ""


_BLIND_SOLVER = """Spanish grammar exercise. Fill the blank.

Sentence: {sentence}

The blank contains exactly one of: {inventory}

Return JSON: {{"answer": "..."}} — the blank's content only, nothing else."""

BLIND_K = 3


async def verify_blind(topic: Topic, item: dict) -> tuple[bool, str]:
    """Tier-B verification: K independent solvers get the sentence and the
    inventory but NOT the answer. Unanimous agreement with the generator's
    answer required — disagreement means wrong OR ambiguous, both fatal
    for a drill card."""
    prompt = _BLIND_SOLVER.format(
        sentence=item["sentence"],
        inventory=", ".join(topic.answer_set or []) or "any Spanish word(s)",
    )
    import asyncio
    raws = await asyncio.gather(
        *(gemini.generate_text(prompt, json_mode=True, temperature=0.2)
          for _ in range(BLIND_K)),
        return_exceptions=True,
    )
    votes = []
    for r in raws:
        if isinstance(r, dict):
            votes.append(_norm_answer(str(r.get("answer", ""))))
        else:
            votes.append("<error>")
    target = _norm_answer(item["answer"])
    if all(v == target for v in votes):
        return True, ""
    return False, f"blind disagreement: votes {votes} vs {target!r}"


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

    is_blind = topic.verify == "blind"
    accepted, rejected, pending_blind = [], [], []
    seen_keys: set = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        base = {
            "lang": topic.lang, "topic": topic.key,
            "infinitive": ((item.get("infinitive") or "").strip().lower()
                           or None) if not is_blind else None,
            "mood": topic.mood or None, "tense": topic.tense or None,
            "person": ((item.get("person") or "").strip().lower()
                       or None) if not is_blind else None,
            "sentence": (item.get("sentence") or "").strip(),
            "answer": (item.get("answer") or "").strip(),
            "gloss_en": (item.get("gloss_en") or "").strip(),
            "why_en": (item.get("why") or "").strip(),
        }
        ok, reason = verify_item(topic, item)
        key = (base["sentence"].lower() if is_blind
               else (base["infinitive"], base["person"]))
        if ok and key in seen_keys:
            ok, reason = False, "duplicate in batch"
        if ok:
            seen_keys.add(key)
            (pending_blind if is_blind else accepted).append(base)
        else:
            base["reject_reason"] = reason
            rejected.append(base)

    # Tier-B: statically-OK items must also survive blind-fill agreement.
    if pending_blind:
        import asyncio
        verdicts = await asyncio.gather(
            *(verify_blind(topic, b) for b in pending_blind))
        for base, (ok, reason) in zip(pending_blind, verdicts):
            if ok:
                accepted.append(base)
            else:
                base["reject_reason"] = reason
                rejected.append(base)

    log.info("grammar.gen.batch", topic=topic.key, requested=n,
             returned=len(raw), accepted=len(accepted), rejected=len(rejected))
    return accepted, rejected
