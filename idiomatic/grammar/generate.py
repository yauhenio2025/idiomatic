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

# Per-language prompt profile for the verb-morphology template. person_mix
# controls the 2p problem: vosotros is rare in the user's es input diet,
# vós is archaic in EP (hard-rejected by the verifier), voi/vous are normal.
LANG_PROFILE = {
    "es": {"language": "Spanish", "variety": "European Spanish",
           "person_mix": "1s, 2s, 3s, 1p, 3p freely; at most one vosotros "
                         "(2p) item per batch"},
    "fr": {"language": "French", "variety": "standard European French",
           "person_mix": "all persons freely; vous (2p) is normal"},
    "it": {"language": "Italian", "variety": "standard Italian",
           "person_mix": "all persons freely; voi (2p) is normal"},
    "pt": {"language": "Portuguese",
           "variety": "BRAZILIAN Portuguese — você/vocês for address "
                      "(3s/3p conjugation), 'estar + gerúndio' (estou "
                      "falando), Brazilian vocabulary and usage",
           "person_mix": "1s, 3s (você/ele/ela), 1p, 3p (vocês/eles); NEVER "
                         "tu (2s) or vós (2p)"},
}

PERSON_MIX = LANG_PROFILE["es"]["person_mix"]  # kept for backward reference

_PROMPT = """You are writing {language} conjugation drill cards for ONE advanced \
adult learner (reads {language} news daily; interests: geopolitics, tech \
criticism, history, media). Target: {label} — mood "{mood}", tense "{tense}".

Produce {n} items as a JSON array. Each item:
{{
  "infinitive": "...",          // pick from: {verbs}
  "person": "...",              // one of 1s 2s 3s 1p 2p 3p ({person_mix})
  "sentence": "...",            // {language} sentence, 7-16 words, with the \
verb replaced by ___ followed by the infinitive in parentheses (format \
example from Spanish: "Ayer el ministro ___ (negar) las acusaciones.")
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
6. Content in {language} only ({variety}).

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


_PROMPT_DE_ART = """You are writing GERMAN grammar drill cards for ONE advanced \
adult learner (reads German news daily; interests: geopolitics, tech \
criticism, history, media). Target: {label}.

Produce {n} items as a JSON array. Each item:
{{
  "sentence": "...",   // German sentence, 7-16 words, with ONE blank ___ \
standing for an ARTICLE, immediately followed by its noun: "Er kam mit ___ Zug."
  "noun": "...",       // that noun, exactly as written in the sentence, \
singular, nominative surface form (e.g. "Zug")
  "prep": "...",       // the governing preposition if the blank follows one, \
else null
  "case": "...",       // nom | akk | dat | gen — the case of the article
  "definite": true,    // definite (der/die/das…) or indefinite (ein…) article
  "answer": "...",     // the article alone, e.g. "dem"
  "gloss_en": "...",   // natural English translation
  "why": "..."         // ONE short English line naming the rule (e.g. "mit \
always takes dative; Zug is masculine → dem")
}}

HARD RULES — a deterministic verifier checks gender, case government, and \
the article table; violations are discarded:
1. {guidance}
2. Use common nouns (the verifier knows ~4000 frequent nouns; obscure or \
compound-rare nouns get rejected). Singular only. The noun's surface form \
must not change in the chosen case (no weak nouns like Student/Junge/Herr).
3. Vary gender, case, and definiteness across the batch; no two sentences \
with the same noun.
4. Real-world content must be timelessly true or clearly hypothetical.

Return ONLY the JSON array."""


def _bank_entries(topic: Topic) -> list[dict]:
    if not topic.bank:
        return []
    import json
    from pathlib import Path
    path = Path(__file__).parent / "data" / topic.bank
    entries = json.loads(path.read_text(encoding="utf-8"))
    # German prep bank: wechsel unit gets only two-way preps, fest the rest.
    if topic.key == "de_prep_wechsel":
        entries = [e for e in entries if e.get("case") == "wechsel"]
    elif topic.key == "de_prep_fest":
        entries = [e for e in entries if e.get("case") != "wechsel"]
    return entries


def _bank_lines(topic: Topic, n: int) -> str:
    """Sample bank entries into prompt lines (schema-tolerant: es regime
    pairs use 'verb', the de prep bank doesn't)."""
    entries = _bank_entries(topic)
    if not entries:
        return ""
    import random
    picked = random.sample(entries, min(2 * n, len(entries)))
    lines = []
    for e in picked:
        head = (f"{e['verb']} + {e['prep']}" if "verb" in e
                else f"{e['prep']} (+{e['case']})")
        lines.append(f"- {head} — {e['en']} (trap: {e['trap']})")
    return ("\n\nPairs to draw from (one per sentence):\n" + "\n".join(lines))


def _vocab_lines(extra_vocab: list[dict] | None) -> str:
    """LingQ terms the learner is studying, offered to the generator as
    OPTIONAL sentence material — vocabulary reinforcement riding along
    with grammar drills ("we study vocabulary even as we study grammar"
    — user, 2026-07-31). Never a constraint: the grammar target rules
    stay absolute, and terms that don't fit are skipped."""
    if not extra_vocab:
        return ""
    lines = "\n".join(
        f"- {t['term']}" + (f" — {t['gloss']}" if t.get("gloss") else "")
        for t in extra_vocab)
    return ("\n\nOPTIONAL vocabulary to weave in: the learner is studying "
            "these words/phrases on LingQ. Where one fits NATURALLY into a "
            "sentence (as ordinary content, never as the blank), prefer it "
            "over generic vocabulary — aim to use several across the batch, "
            "and skip any that don't fit:\n" + lines)


def build_prompt(topic: Topic, n: int,
                 extra_vocab: list[dict] | None = None) -> str:
    if topic.verify in ("de_art", "de_art_blind"):
        return _PROMPT_DE_ART.format(
            label=topic.label, n=n, guidance=topic.guidance,
        ) + _bank_lines(topic, n) + _vocab_lines(extra_vocab)
    if topic.verify == "blind":
        return _PROMPT_CLOSED.format(
            label=topic.label, n=n,
            inventory=", ".join(topic.answer_set or []) or "(open)",
            guidance=topic.guidance,
        ) + _bank_lines(topic, n) + _vocab_lines(extra_vocab)
    prof = LANG_PROFILE.get(topic.lang, LANG_PROFILE["es"])
    return _PROMPT.format(
        label=topic.label, mood=topic.mood, tense=topic.tense, n=n,
        verbs=", ".join(topic.verbs), person_mix=prof["person_mix"],
        language=prof["language"], variety=prof["variety"],
        guidance=topic.guidance,
    ) + _vocab_lines(extra_vocab)


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
    # Leak check skipped for German article topics: the same article form
    # legitimately appears for other nouns in almost any sentence.
    if (topic.verify not in ("de_art", "de_art_blind")
            and _answer_leaks(sentence, answer)):
        return False, "answer leaks in sentence"

    if topic.verify == "blind":
        if topic.answer_set is not None:
            allowed = {_norm_answer(a) for a in topic.answer_set}
            if _norm_answer(answer) not in allowed:
                return False, f"answer {answer!r} not in closed inventory"
        return True, ""

    if topic.verify in ("de_art", "de_art_blind"):
        # Deterministic German article check: gender table × case × matrix.
        # NB: no leak check here — German sentences legitimately contain
        # the same article form for OTHER nouns; the table already pins
        # the answer.
        noun = (item.get("noun") or "").strip()
        case = (item.get("case") or "").strip().lower()
        prep = (item.get("prep") or "").strip().lower() or None
        definite = bool(item.get("definite", True))
        if case not in morphology.DE_CASES:
            return False, f"bad case {case!r}"
        gender = morphology.de_gender(noun)
        if gender is None:
            return False, f"noun {noun!r} not in gender DB"
        if f"___ {noun}" not in sentence.replace("___  ", "___ "):
            return False, "blank is not directly before the stated noun"
        if topic.key == "de_prep_fest":
            got = morphology.de_prep_case(prep) if prep else None
            if got is None:
                return False, f"prep {prep!r} not in bank"
            if got == "wechsel":
                return False, f"two-way prep {prep!r} in fixed-prep unit"
            if got != case:
                return False, f"prep {prep!r} governs {got}, item says {case}"
            if case == "gen" and gender in ("m", "n"):
                return False, "genitive with m/n noun (surface form changes)"
        if topic.key == "de_prep_wechsel":
            if morphology.de_prep_case(prep) != "wechsel":
                return False, f"prep {prep!r} is not a Wechselpräposition"
            if case not in ("akk", "dat"):
                return False, f"wechsel case must be akk/dat, got {case}"
        if topic.key == "de_gender" and case != "nom":
            return False, "de_gender items must be nominative"
        expected = morphology.de_article(case, gender, definite)
        if expected is None:
            return False, f"no article for case={case} gender={gender}"
        if _norm_answer(answer) != expected:
            return False, (f"wrong article: {answer!r}, expected {expected!r} "
                           f"({noun}={gender}, {case})")
        return True, ""

    inf = (item.get("infinitive") or "").strip().lower()
    person = (item.get("person") or "").strip().lower()
    if person not in morphology.PERSONS:
        return False, f"bad person {person!r}"
    if topic.lang == "pt" and person in ("2s", "2p"):
        return False, ("tu/vós forms excluded — Brazilian drills use "
                       "você (3s) / vocês (3p)")
    ok, expected = morphology.verify(topic.lang, inf, topic.mood, topic.tense,
                                     person, answer)
    if expected is None:
        return False, f"verb {inf!r} not in morphology DB"
    if not ok and _agreement_variant_ok(topic.lang, expected, answer):
        return True, ""
    if not ok:
        if _strip_accents_eq(answer.lower(), expected):
            return False, f"accent error: {answer!r} vs {expected!r}"
        return False, f"wrong form: {answer!r}, expected {expected!r}"
    return True, ""


def _agreement_variant_ok(lang: str, expected: str, answer: str) -> bool:
    """fr/it compound tenses: the table stores the MASCULINE participle,
    but feminine/plural agreement is equally correct French/Italian
    ('elle est allée'). Accept answers whose only deviation is a valid
    agreement inflection of the participle; auxiliary must match exactly
    (so 'a monté' vs 'est monté' is still rejected)."""
    if lang not in ("fr", "it") or " " not in (expected or ""):
        return False
    exp_parts = expected.split()
    ans_parts = _norm_answer(answer).split()
    if len(exp_parts) != len(ans_parts) or exp_parts[:-1] != ans_parts[:-1]:
        return False
    base, got = exp_parts[-1], ans_parts[-1]
    if lang == "fr":
        return got in (base + "e", base + "s", base + "es")
    # it: masc sg -o → fem sg -a; masc pl -i → fem pl -e
    if base.endswith("o"):
        return got in (base[:-1] + "a", base[:-1] + "i", base[:-1] + "e")
    if base.endswith("i"):
        return got == base[:-1] + "e"
    return False


_BLIND_SOLVER = """Spanish grammar exercise. Fill the blank.

Sentence: {sentence}

The blank contains exactly one of: {inventory}

Return JSON: {{"answer": "..."}} — the blank's content only, nothing else."""

BLIND_K = 3


async def verify_blind(topic: Topic, item: dict,
                        inventory: list[str] | None = None) -> tuple[bool, str]:
    """Tier-B verification: K independent solvers get the sentence and the
    inventory but NOT the answer. Unanimous agreement with the generator's
    answer required — disagreement means wrong OR ambiguous, both fatal
    for a drill card. `inventory` overrides the topic's answer_set (used
    for per-item candidate pairs, e.g. Wechselpräposition akk/dat)."""
    inv = inventory if inventory is not None else topic.answer_set
    prompt = _BLIND_SOLVER.format(
        sentence=item["sentence"],
        inventory=", ".join(inv or []) or "the missing word(s)",
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


async def generate_batch(topic: Topic, n: int,
                          extra_vocab: list[dict] | None = None,
                          ) -> tuple[list[dict], list[dict]]:
    """Returns (accepted, rejected); each item dict is augmented with
    mood/tense/topic keys ready for DB insert. extra_vocab: LingQ terms
    offered to the prompt as optional sentence material."""
    raw = await gemini.generate_text(build_prompt(topic, n, extra_vocab),
                                     json_mode=True,
                                     temperature=0.7)
    if isinstance(raw, dict):        # model wrapped the array in an object
        raw = next((v for v in raw.values() if isinstance(v, list)), [])
    if not isinstance(raw, list):
        log.warning("grammar.gen.bad_payload", topic=topic.key, type=str(type(raw)))
        return [], []

    is_morph = topic.verify == "morph"
    needs_blind = topic.verify in ("blind", "de_art_blind")
    accepted, rejected, pending_blind = [], [], []
    seen_keys: set = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        base = {
            "lang": topic.lang, "topic": topic.key,
            "infinitive": ((item.get("infinitive") or "").strip().lower()
                           or None) if is_morph else None,
            "mood": topic.mood or None, "tense": topic.tense or None,
            "person": ((item.get("person") or "").strip().lower()
                       or None) if is_morph else None,
            "sentence": (item.get("sentence") or "").strip(),
            "answer": (item.get("answer") or "").strip(),
            "gloss_en": (item.get("gloss_en") or "").strip(),
            "why_en": (item.get("why") or "").strip(),
        }
        if topic.verify in ("de_art", "de_art_blind"):
            base["meta"] = {k: item.get(k)
                            for k in ("noun", "prep", "case", "definite")}
        ok, reason = verify_item(topic, item)
        key = ((base["infinitive"], base["person"]) if is_morph
               else base["sentence"].lower())
        if ok and key in seen_keys:
            ok, reason = False, "duplicate in batch"
        if ok:
            seen_keys.add(key)
            (pending_blind if needs_blind else accepted).append(
                (base, item) if needs_blind else base)
        else:
            base["reject_reason"] = reason
            rejected.append(base)

    # Tier-B: statically-OK items must also survive blind-fill agreement.
    if pending_blind:
        import asyncio

        def _inventory(it: dict) -> list[str] | None:
            if topic.verify != "de_art_blind":
                return None                      # topic answer_set applies
            g = morphology.de_gender((it.get("noun") or "").strip())
            definite = bool(it.get("definite", True))
            return [a for a in (morphology.de_article("akk", g, definite),
                                 morphology.de_article("dat", g, definite))
                    if a]

        verdicts = await asyncio.gather(
            *(verify_blind(topic, b, inventory=_inventory(it))
              for b, it in pending_blind))
        for (base, _it), (ok, reason) in zip(pending_blind, verdicts):
            if ok:
                accepted.append(base)
            else:
                base["reject_reason"] = reason
                rejected.append(base)

    log.info("grammar.gen.batch", topic=topic.key, requested=n,
             returned=len(raw), accepted=len(accepted), rejected=len(rejected))
    return accepted, rejected
