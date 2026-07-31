"""LLM item generation + deterministic verification for grammar drills.

One Gemini call per (topic, batch); every returned item is checked
against morphology.py before it may be persisted. Rejected items are
persisted too (status='rejected') so the dashboard can show the LLM's
error rate per topic — that number is itself a finding.
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache

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
    "de": {"language": "German", "variety": "standard German",
           "person_mix": "all persons freely"},
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


_PROMPT_CLOSED = """You are writing {language} grammar drill cards for ONE \
advanced adult learner (reads {language} news daily; interests: geopolitics, \
tech criticism, history, media). Target: {label}.

Produce {n} items as a JSON array. Each item:
{{
  "sentence": "...",   // {language} sentence(s), 8-20 words, with ONE blank ___ \
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
3. Use {variety}. Vary structures and persons; no two sentences may share the \
same opening words.
4. Real-world content must be timelessly true or clearly hypothetical.
5. Preserve literal spacing at the blank boundary. If the answer ends in an \
apostrophe, put the blank immediately against the following word \
(`___énergie`, never `___ énergie`) so insertion produces valid elision.

Return ONLY the JSON array."""


def _strip_accents_eq(a: str, b: str) -> bool:
    d = lambda s: "".join(c for c in unicodedata.normalize("NFD", s)
                          if unicodedata.category(c) != "Mn")
    return d(a) == d(b)


def _norm_answer(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or "").strip().lower())
    # A trailing apostrophe is grammatical content in French/Italian answers
    # such as d' and l'; do not strip it as generic quote punctuation.
    s = s.strip(".,;:!?¡¿\"«»")
    if len(s) > 1 and s.startswith("'") and s.endswith("'"):
        s = s[1:-1].strip()
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


_PROMPT_DE_NP = """You are writing GERMAN adjective-ending drill cards for ONE \
advanced adult learner (reads German news daily; interests: geopolitics, tech \
criticism, history, media). Target: {label}.

Produce {n} items as a JSON array. Each item:
{{
  "sentence": "...",       // German sentence, 8-20 words, with exactly ONE \
blank and the adjective lemma as a hint. target=article_adjective uses \
"___ (hart) Konkurrent"; target=adjective uses "der ___ (hart) Konkurrent".
  "noun": "...",           // nominative surface for the requested number: \
singular citation form for sg, nominative plural form for pl
  "case": "...",           // nom | akk | dat | gen
  "number": "...",         // sg | pl
  "definiteness": "...",   // definite | indefinite | none | kein | mein
  "adjective": "...",      // uninflected adjective or prepared degree stem
  "target": "...",         // article_adjective | adjective
  "answer": "...",         // exactly the material represented by ___
  "gloss_en": "...",       // natural English translation
  "why": "..."             // one short English line naming the pattern/ending
}}

HARD RULES — decline_np() deterministically checks the complete noun phrase:
1. {guidance}
2. The noun must be banked: singulars come from the gender/weak-noun tables; \
plural metadata comes exactly from this approved nominative-plural inventory: \
{plural_nouns}. Write its correctly declined surface immediately after the \
parenthesized adjective hint.
3. With target=adjective, put the correct declined determiner immediately before \
the blank. Use target=article_adjective for no-article strong forms. Plural mixed \
forms use kein or mein, never indefinite.
4. Cover all three patterns across the batch: weak after a definite article, \
mixed after ein/kein/mein, and strong with no article. Vary case and number.
5. The context and parenthesized lemma must make one answer possible. Real-world \
content must be timelessly true or clearly hypothetical.

Return ONLY the JSON array."""


_PROMPT_DE_PASSIV = """You are writing GERMAN process-passive drill cards for \
ONE advanced adult learner (reads German news daily; interests: geopolitics, \
tech criticism, history, media). Target: {label}.

Produce {n} items as a JSON array. Choose lexical verbs from: {verbs}
Each item:
{{
  "sentence": "...",       // 8-20 words ending in a subordinate clause whose \
complete clause-final passive predicate is ___ followed by the infinitive hint, \
e.g. "..., dass der Bericht morgen ___ (veröffentlichen)."
  "infinitive": "...",     // lexical infinitive from the list
  "participle": "...",     // exact Partizip II of that infinitive
  "person": "...",         // 1s | 2s | 3s | 1p | 2p | 3p
  "tense": "...",          // present | preterite | perfect | modal
  "modal": null,            // for modal only: müssen | können | sollen | dürfen
  "answer": "...",         // complete predicate in subordinate-clause order
  "gloss_en": "...",       // natural English translation
  "why": "..."             // one short English line naming the passive form
}}

Required answer shapes:
- present: "veröffentlicht wird"
- preterite: "veröffentlicht wurde"
- perfect: "veröffentlicht worden ist" (NEVER "geworden")
- modal: "veröffentlicht werden muss"

HARD RULES — finite auxiliaries are table-checked and known participles are \
dictionary-checked:
1. {guidance}
2. The explicit subordinate-clause subject must agree with person. For modal \
items, set modal to the infinitive whose present form ends the answer; otherwise \
set modal to null.
3. The answer is one contiguous predicate and appears nowhere outside the blank. \
Use exactly one blank, immediately followed by " (infinitive)" at clause end.
4. Mix all four tense values. Real-world content must be timelessly true or \
clearly hypothetical.

Return ONLY the JSON array."""


_PROMPT_BANK = """You are writing {language} grammar drill cards for ONE \
advanced adult learner (reads {language} news daily; interests: geopolitics, \
tech criticism, history, media). Target: {label}.

Produce {n} items as a JSON array. Each item:
{{
{metadata_fields}
  "sentence": "...",   // {language} text, 8-20 words, with exactly ONE ___
  "answer": "...",     // the blank's complete content only
  "gloss_en": "...",   // natural English translation of the completed text
  "why": "..."         // ONE short English line naming the deciding rule
}}

HARD RULES — deterministic bank checks reject invalid metadata and answers:
1. {guidance}
2. Copy every bank-key metadata value exactly from ONE authoritative bank row
below; use any declared target enum exactly as described.
3. The sentence must make that row's answer uniquely correct. Do not reveal the
answer elsewhere in the sentence, and do not add a second blank.
4. Use {variety}. Real-world content must be timelessly true or clearly
hypothetical. Vary structures across the batch.
5. Preserve literal spacing at the blank boundary. If the answer ends in an
apostrophe, put the blank immediately against the following word
(`___énergie`, never `___ énergie`) so insertion produces valid elision.

Return ONLY the JSON array."""


_BANK_PROMPT_FIELDS = {
    "fr_prep_lieux": (
        '  "place": "...",      // exact bank place key (including any stored article)'
    ),
    "fr_genre_noyau": (
        '  "noun": "...",       // exact bank noun; answer is un or une'
    ),
    "pt_gender_core": (
        '  "noun_or_frame": "...", // exact bank key\n'
        '  "target": "...",     // definite | indefinite for m/f noun rows; '
        'bank for supplied frames'
    ),
    "pt_regencia_verbal": (
        '  "verb": "...",       // exact bank verb\n'
        '  "pattern": "...",    // exact bank pattern (pins the sense)'
    ),
    "it_genere_plurali": (
        '  "noun": "...",       // exact bank noun\n'
        '  "target": "...",     // singular_phrase | plural_phrase | plural'
    ),
    "it_reggenze_verbali": (
        '  "verb": "...",       // exact bank verb\n'
        '  "pattern": "...",    // exact bank pattern (pins the sense)'
    ),
    "de_dativ_verben": (
        '  "verb": "...",       // exact bank verb\n'
        '  "case": "dat",       // copy the bank case; always dat in this unit'
    ),
}


# Finite forms needed to construct a clause-final process passive. Keeping
# these closed tables here makes auxiliary verification independent of an LLM.
_DE_WERDEN_PRESENT = {
    "1s": "werde", "2s": "wirst", "3s": "wird",
    "1p": "werden", "2p": "werdet", "3p": "werden",
}
_DE_WERDEN_PRETERITE = {
    "1s": "wurde", "2s": "wurdest", "3s": "wurde",
    "1p": "wurden", "2p": "wurdet", "3p": "wurden",
}
_DE_SEIN_PRESENT = {
    "1s": "bin", "2s": "bist", "3s": "ist",
    "1p": "sind", "2p": "seid", "3p": "sind",
}
_DE_MODAL_PRESENT = {
    "müssen": {
        "1s": "muss", "2s": "musst", "3s": "muss",
        "1p": "müssen", "2p": "müsst", "3p": "müssen",
    },
    "können": {
        "1s": "kann", "2s": "kannst", "3s": "kann",
        "1p": "können", "2p": "könnt", "3p": "können",
    },
    "sollen": {
        "1s": "soll", "2s": "sollst", "3s": "soll",
        "1p": "sollen", "2p": "sollt", "3p": "sollen",
    },
    "dürfen": {
        "1s": "darf", "2s": "darfst", "3s": "darf",
        "1p": "dürfen", "2p": "dürft", "3p": "dürfen",
    },
}


def _join_article_noun(article: str, noun: str) -> str:
    """Italian l' joins directly; other articles take a space."""
    return f"{article}{noun}" if article.endswith("'") else f"{article} {noun}"


def _bank_entries(topic: Topic) -> list[dict]:
    if not topic.bank:
        return []
    import json
    from pathlib import Path
    path = Path(__file__).parent / "data" / topic.bank
    entries = json.loads(path.read_text(encoding="utf-8"))
    # Wave-7 banks carry provenance as element zero. Legacy banks do not,
    # so filter by shape instead of unconditionally discarding the first row.
    entries = [e for e in entries
               if isinstance(e, dict) and "_meta" not in e]
    # German prep bank: wechsel unit gets only two-way preps, fest the rest.
    if topic.key == "de_prep_wechsel":
        entries = [e for e in entries if e.get("case") == "wechsel"]
    elif topic.key == "de_prep_fest":
        entries = [e for e in entries if e.get("case") != "wechsel"]
    return entries


def _bank_lines(topic: Topic, n: int) -> str:
    """Sample authoritative rows into compact, schema-specific prompt lines."""
    entries = _bank_entries(topic)
    if not entries:
        return ""
    import random
    count = min(2 * n, len(entries))
    # Specs mark these leading rows as anchors that must be available before
    # broader pattern expansion. Keep them first, then sample the remainder.
    anchor_count = {
        "fr_prep_lieux": 12,
        "fr_genre_noyau": 19,
        "pt_regencia_verbal": 4,
        "it_reggenze_verbali": 4,
        "es_muy_mucho": 7,
    }.get(topic.key, 0)
    anchors = entries[:min(anchor_count, count)]
    remainder = entries[len(anchors):]
    picked = anchors + random.sample(remainder, count - len(anchors))
    lines = []
    for e in picked:
        if "verb" in e and "pattern" in e:
            # es/pt/it regime schema. `example_es` intentionally contains
            # the target language in the Portuguese and Italian banks.
            lines.append(
                f"- {e['verb']} + {e['prep']} — {e['en']} "
                f"(trap: {e['trap']}; pattern: {e['pattern']}; "
                f"example: {e['example_es']})"
            )
        elif "example_frame" in e:
            lines.append(
                f"- {e['verb']} (+{e['case']}) — {e['example_frame']} "
                f"→ {e['example_answer']}"
            )
        elif "place" in e:
            lines.append(
                f"- {e['place']} ({e['place_type']}, {e['gender']}) "
                f"→ {e['correct_prep']} (example: {e['example']})"
            )
        elif "noun_or_frame" in e:
            lines.append(
                f"- {e['noun_or_frame']} → {e['gender_or_correct']} "
                f"(trap: {e['trap_reason']}; example: {e['example']})"
            )
        elif "plural" in e and "article_sg" in e:
            sg = _join_article_noun(e["article_sg"], e["singular"])
            pl = _join_article_noun(e["article_pl"], e["plural"])
            lines.append(
                f"- {e['noun']} ({e['gender']}) → singular {sg}; "
                f"plural {pl}; plural-only {e['plural']} "
                f"(trap: {e['trap_reason']})"
            )
        elif "noun" in e and "gender" in e:
            lines.append(
                f"- {e['noun']} → {e['gender']} "
                f"(trap: {e['trap_reason']}; example: {e['example']})"
            )
        elif "frame" in e and "correct" in e:
            detail = e.get("rule_en") or e.get("trap") or "banked form"
            trap = f"; trap: {e['trap']}" if e.get("trap") else ""
            lines.append(
                f"- {e['frame']} → {e['correct']} "
                f"(rule: {detail}{trap})"
            )
        elif "prep" in e and "case" in e:
            lines.append(
                f"- {e['prep']} (+{e['case']}) — {e['en']} "
                f"(trap: {e['trap']})"
            )
        else:  # Defensive: a new schema should fail visibly in its prompt.
            lines.append(f"- unsupported bank row: {e!r}")
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
    prof = LANG_PROFILE.get(topic.lang, LANG_PROFILE["es"])
    if topic.verify == "de_np":
        return _PROMPT_DE_NP.format(
            label=topic.label, n=n, guidance=topic.guidance,
            plural_nouns=", ".join(sorted(_load_de_adj_plural_nouns())),
        ) + _vocab_lines(extra_vocab)
    if topic.verify == "de_passiv":
        return _PROMPT_DE_PASSIV.format(
            label=topic.label, n=n, guidance=topic.guidance,
            verbs=", ".join(topic.verbs),
        ) + _vocab_lines(extra_vocab)
    if topic.verify in ("de_art", "de_art_blind"):
        return _PROMPT_DE_ART.format(
            label=topic.label, n=n, guidance=topic.guidance,
        ) + _bank_lines(topic, n) + _vocab_lines(extra_vocab)
    if topic.verify in ("bank_blind", "fr_gender", "pt_gender", "it_noun"):
        return _PROMPT_BANK.format(
            language=prof["language"], variety=prof["variety"],
            label=topic.label, n=n, guidance=topic.guidance,
            metadata_fields=_BANK_PROMPT_FIELDS[topic.key],
        ) + _bank_lines(topic, n) + _vocab_lines(extra_vocab)
    if topic.verify == "blind":
        return _PROMPT_CLOSED.format(
            language=prof["language"], variety=prof["variety"],
            label=topic.label, n=n,
            inventory=", ".join(topic.answer_set or []) or "(open)",
            guidance=topic.guidance,
        ) + _bank_lines(topic, n) + _vocab_lines(extra_vocab)
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


_NEW_BANK_KEYS = {
    "fr_quantites_de", "fr_prep_lieux", "fr_genre_noyau", "fr_an_annee",
    "pt_gender_core", "pt_regencia_verbal", "it_genere_plurali",
    "it_reggenze_verbali", "es_muy_mucho", "de_dativ_verben",
    "pt_clitic_placement", "it_clitici_ci_ne",
}

_BANK_META_FIELDS = {
    "fr_prep_lieux": ("place",),
    "fr_genre_noyau": ("noun", "target"),
    "pt_gender_core": ("noun_or_frame", "target"),
    "pt_regencia_verbal": ("verb", "pattern"),
    "it_genere_plurali": ("noun", "target"),
    "it_reggenze_verbali": ("verb", "pattern"),
    "de_dativ_verben": ("verb", "case"),
}

_SPECIAL_META_FIELDS = {
    "de_adj_endings": (
        "noun", "case", "number", "definiteness", "adjective", "target",
    ),
    "de_passiv": (
        "infinitive", "participle", "person", "tense", "modal",
    ),
}


def _norm_key(value: object) -> str:
    return " ".join(unicodedata.normalize(
        "NFC", str(value or "").strip()).casefold().split())


def _item_text(value: object) -> str:
    """Trim an LLM text field; non-text JSON is an invalid empty field."""
    return value.strip() if isinstance(value, str) else ""


@lru_cache(maxsize=1)
def _load_de_adj_plural_nouns() -> frozenset[str]:
    """Approved nominative plurals for deterministic adjective cards."""
    import json
    from pathlib import Path

    path = Path(__file__).parent / "data" / "de_adj_plural_nouns.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not all(isinstance(noun, str) for noun in raw):
        raise ValueError("de_adj_plural_nouns.json must be a list of nouns")
    if len(raw) != len(set(raw)):
        raise ValueError("de_adj_plural_nouns.json contains duplicate nouns")
    return frozenset(raw)


@lru_cache(maxsize=1)
def _load_de_participles() -> dict[str, str]:
    """Curated Partizip-II facts used by the deterministic passive path."""
    import json
    from pathlib import Path

    path = Path(__file__).parent / "data" / "de_participles.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {_norm_key(inf): _norm_key(part) for inf, part in raw.items()}


_DE_PASSIVE_TENSE_ALIASES = {
    "present": "present", "present tense": "present",
    "präsens": "present", "praesens": "present",
    "preterite": "preterite", "simple past": "preterite",
    "präteritum": "preterite", "praeteritum": "preterite",
    "perfect": "perfect", "present perfect": "perfect",
    "perfekt": "perfect",
    "modal": "modal", "modal passive": "modal",
    "modal+infinitive": "modal", "modal infinitive": "modal",
}


def _de_passive_tense(value: object) -> str | None:
    return _DE_PASSIVE_TENSE_ALIASES.get(_norm_key(value))


def _de_passive_needs_blind(item: dict) -> bool:
    """Whether lexical Partizip II lacks an independent dictionary fact.

    Known entries take the deterministic Tier-A path only. An unknown lemma
    is allowed through static auxiliary/order checks, but this predicate sends
    that individual item — not the whole topic — to K=3 blind verification.
    """
    infinitive = _norm_key(item.get("infinitive"))
    return bool(infinitive and infinitive not in _load_de_participles())


def _de_np_surfaces(item: dict) -> tuple[str, str, str]:
    """Return (determiner, declined adjective, declined noun) from the engine."""
    for field in ("noun", "case", "number", "definiteness", "adjective"):
        if not isinstance(item.get(field), str):
            raise ValueError(f"{field} must be text")
    noun = unicodedata.normalize("NFC", item["noun"].strip())
    adjective = unicodedata.normalize("NFC", item["adjective"].strip())
    if not noun or not adjective:
        raise ValueError("noun and adjective are required")

    case_aliases = {
        "nom": "nom", "nominative": "nom", "nominativ": "nom",
        "akk": "akk", "accusative": "akk", "akkusativ": "akk",
        "dat": "dat", "dative": "dat", "dativ": "dat",
        "gen": "gen", "genitive": "gen", "genitiv": "gen",
    }
    number_aliases = {
        "sg": "sg", "singular": "sg", "sing": "sg",
        "pl": "pl", "plural": "pl",
    }
    case = case_aliases.get(_norm_key(item.get("case")))
    number = number_aliases.get(_norm_key(item.get("number")))
    definiteness = _norm_key(item.get("definiteness"))
    if case is None:
        raise ValueError(f"bad case {item.get('case')!r}")
    if number is None:
        raise ValueError(f"bad number {item.get('number')!r}")
    if not definiteness:
        raise ValueError("definiteness is required")
    if number == "pl" and noun not in _load_de_adj_plural_nouns():
        raise ValueError(f"plural noun is not in adjective bank: {noun!r}")

    full_np = morphology.decline_np(
        noun, case=case, number=number, definiteness=definiteness,
        adjective=adjective,
    )
    bare_np = morphology.decline_np(
        noun, case=case, number=number, definiteness=definiteness,
    )
    if not isinstance(full_np, str) or not isinstance(bare_np, str):
        raise ValueError("decline_np returned no surface form")
    full_np, bare_np = full_np.strip(), bare_np.strip()
    if not full_np or not bare_np:
        raise ValueError("decline_np returned an empty surface form")

    declined_noun = bare_np.rsplit(" ", 1)[-1]
    noun_suffix = f" {declined_noun}"
    if full_np == declined_noun or not full_np.endswith(noun_suffix):
        raise ValueError("declined adjective phrase has an unexpected shape")
    full_prefix = full_np[:-len(noun_suffix)].strip()
    if bare_np == declined_noun:
        determiner = ""
    elif bare_np.endswith(noun_suffix):
        determiner = bare_np[:-len(noun_suffix)].strip()
    else:
        raise ValueError("declined bare phrase has an unexpected shape")

    if determiner:
        marker = f"{determiner} "
        if not full_prefix.startswith(marker):
            raise ValueError("declined determiner does not match adjective phrase")
        declined_adjective = full_prefix[len(marker):].strip()
    else:
        declined_adjective = full_prefix
    if not declined_adjective:
        raise ValueError("declined adjective is empty")
    return determiner, declined_adjective, declined_noun


_DE_DETERMINER_SURFACES = frozenset({
    "der", "die", "das", "den", "dem", "des",
    "ein", "eine", "einen", "einem", "einer", "eines",
    "kein", "keine", "keinen", "keinem", "keiner", "keines",
    "mein", "meine", "meinen", "meinem", "meiner", "meines",
    "dein", "deine", "deinen", "deinem", "deiner", "deines",
    "sein", "seine", "seinen", "seinem", "seiner", "seines",
    "ihr", "ihre", "ihren", "ihrem", "ihrer", "ihres",
    "unser", "unsere", "unseren", "unserem", "unserer", "unseres",
    "euer", "eure", "euren", "eurem", "eurer", "eures",
})


def _verify_de_np(item: dict, sentence: str,
                  answer: str) -> tuple[bool, str]:
    target = _norm_key(item.get("target"))
    if target not in ("article_adjective", "adjective"):
        return False, f"bad adjective target {target!r}"
    try:
        determiner, declined_adjective, declined_noun = _de_np_surfaces(item)
    except (KeyError, TypeError, ValueError) as exc:
        return False, f"cannot decline noun phrase: {exc}"
    adjective = unicodedata.normalize("NFC", item["adjective"].strip())

    import re
    if target == "article_adjective":
        expected = " ".join(p for p in (determiner, declined_adjective) if p)
        placement_pattern = re.escape(
            f"___ ({adjective}) {declined_noun}"
        ) + r"(?!\w)"
        # This target owns the determiner inside the blank. A visible article
        # immediately before it would produce e.g. *der der härteste* even
        # though the shorter placement substring happens to match.
        prefix = sentence.split("___", 1)[0]
        visible = re.search(r"([^\W\d_]+)\s*$", prefix, re.UNICODE)
        if visible and visible.group(1).casefold() in _DE_DETERMINER_SURFACES:
            return False, "target='article_adjective' has a visible determiner"
    else:
        if not determiner:
            return False, "target='adjective' requires a visible determiner"
        expected = declined_adjective
        initial_determiner = determiner[:1].upper() + determiner[1:]
        determiner_pattern = "|".join(
            re.escape(value) for value in dict.fromkeys(
                (determiner, initial_determiner)
            )
        )
        placement_pattern = (
            rf"(?:{determiner_pattern}) "
            + re.escape(f"___ ({adjective}) {declined_noun}")
            + r"(?!\w)"
        )

    # Hint and noun case stay exact because card/audio replacement is exact.
    # Only a visible sentence-initial determiner may capitalize its first letter.
    if re.search(placement_pattern, sentence) is None:
        return False, "blank/hint is not in the expected declined noun phrase"
    if not _bank_answer_matches(sentence, answer, expected):
        return False, f"wrong noun-phrase answer: {answer!r}, expected {expected!r}"
    return True, ""


def _verify_de_passive(topic: Topic, item: dict, sentence: str,
                       answer: str) -> tuple[bool, str]:
    for field in ("infinitive", "participle", "person", "tense"):
        if not isinstance(item.get(field), str):
            return False, f"passive {field} must be text"
    if item.get("modal") is not None and not isinstance(item.get("modal"), str):
        return False, "passive modal must be text or null"
    raw_infinitive = unicodedata.normalize("NFC", item["infinitive"].strip())
    infinitive = _norm_key(item.get("infinitive"))
    participle = _norm_key(item.get("participle"))
    person = _norm_key(item.get("person"))
    tense = _de_passive_tense(item.get("tense"))
    modal = _norm_key(item.get("modal"))
    if not infinitive:
        return False, "passive infinitive is required"
    if not participle or " " in participle:
        return False, "passive participle must be one word"
    if person not in morphology.PERSONS:
        return False, f"bad person {person!r}"
    if tense is None:
        return False, f"bad passive tense {item.get('tense')!r}"
    if raw_infinitive != infinitive:
        return False, "passive infinitive must use its lowercase citation form"
    if infinitive not in {_norm_key(verb) for verb in topic.verbs}:
        return False, f"passive infinitive is outside topic inventory: {infinitive!r}"

    hint = f"___ ({infinitive})"
    if hint not in sentence:
        return False, "blank is not followed by the stated infinitive hint"
    prefix, tail = sentence.split(hint, 1)
    if tail.strip(" \t\r\n.,;:!?…'\"»”"):
        return False, "passive predicate blank must be clause-final"

    # The answer uses subordinate-clause word order, so a preceding explicit
    # subordinator is part of the statically enforced exercise template.
    import re
    subordinate = list(re.finditer(
        r"[,;:]\s*(?:dass|weil|obwohl|wenn|falls|ob|da|indem|nachdem|"
        r"bevor|sobald|während|als)\b",
        prefix,
        flags=re.IGNORECASE,
    ))
    if not subordinate:
        return False, "passive predicate is not in a subordinate clause"

    # Catch explicit-pronoun/person contradictions without pretending to parse
    # arbitrary German noun phrases. Noun subjects remain prompt-constrained.
    clause_start = prefix[subordinate[-1].end():]
    pronoun = re.match(r"\s*(ich|du|er|sie|es|wir|ihr)\b", clause_start,
                       flags=re.IGNORECASE)
    allowed_by_pronoun = {
        "ich": {"1s"}, "du": {"2s"}, "er": {"3s"},
        "sie": {"3s", "3p"}, "es": {"3s"}, "wir": {"1p"},
        "ihr": {"2p"},
    }
    if (pronoun and person not in allowed_by_pronoun[pronoun.group(1).casefold()]):
        return False, "passive subject pronoun does not match person metadata"

    known = _load_de_participles().get(infinitive)
    if known is not None and participle != known:
        return False, (f"wrong participle: {participle!r}, expected {known!r} "
                       f"for {infinitive!r}")

    if tense == "present":
        if modal:
            return False, "modal metadata is only valid for modal passive"
        expected = f"{participle} {_DE_WERDEN_PRESENT[person]}"
    elif tense == "preterite":
        if modal:
            return False, "modal metadata is only valid for modal passive"
        expected = f"{participle} {_DE_WERDEN_PRETERITE[person]}"
    elif tense == "perfect":
        if modal:
            return False, "modal metadata is only valid for modal passive"
        expected = f"{participle} worden {_DE_SEIN_PRESENT[person]}"
    else:
        forms = _DE_MODAL_PRESENT.get(modal)
        if forms is None:
            return False, f"unsupported modal {modal or '<missing>'!r}"
        expected = f"{participle} werden {forms[person]}"

    if _norm_answer(answer) != _norm_answer(expected):
        return False, f"wrong passive: {answer!r}, expected {expected!r}"
    return True, ""


def _find_bank_row(topic: Topic, **fields: object) -> dict | None:
    """Find one row by stable schema keys, with Unicode/case normalization."""
    if not fields or any(not _norm_key(v) for v in fields.values()):
        return None
    for row in _bank_entries(topic):
        if all(_norm_key(row.get(k)) == _norm_key(v)
               for k, v in fields.items()):
            return row
    return None


def _answer_case_text(value: str) -> str:
    """Whitespace/punctuation normalization that preserves meaningful case."""
    value = unicodedata.normalize("NFC", (value or "").strip())
    value = value.strip(".,;:!?¡¿\"«»")
    if len(value) > 1 and value.startswith("'") and value.endswith("'"):
        value = value[1:-1].strip()
    return " ".join(value.split())


def _blank_starts_sentence(sentence: str) -> bool:
    """True when only opening punctuation precedes the blank in its clause."""
    prefix = sentence.split("___", 1)[0].rstrip()
    if not prefix:
        return True
    # Treat a blank immediately after sentence-ending punctuation and optional
    # opening quotes/inverted punctuation as sentence-initial too.
    import re
    tail = re.split(r"[.!?:]\s*", prefix)[-1]
    return not any(ch.isalnum() for ch in tail)


def _bank_answer_matches(sentence: str, answer: str, expected: str) -> bool:
    got = _answer_case_text(answer)
    want = _answer_case_text(expected)
    if got == want:
        return True
    return (_blank_starts_sentence(sentence)
            and got.casefold() == want.casefold())


def _sentence_surface_answer(sentence: str, answer: str) -> str:
    """Capitalize the first letter when a bank answer starts the sentence."""
    if not _blank_starts_sentence(sentence):
        return answer
    for index, char in enumerate(answer):
        if char.isalpha():
            return answer[:index] + char.upper() + answer[index + 1:]
    return answer


def _wrong_bank_answer(answer: str, expected: str) -> tuple[bool, str]:
    return False, f"wrong bank answer: {answer!r}, expected {expected!r}"


def _mentions(sentence: str, value: str) -> bool:
    import re
    return re.search(rf"(?<!\w){re.escape(value)}(?!\w)", sentence,
                     re.IGNORECASE) is not None


def _blank_before(sentence: str, value: str) -> bool:
    import re
    return re.search(rf"___\s+{re.escape(value)}(?!\w)", sentence,
                     re.IGNORECASE) is not None


def _citation_after_blank(sentence: str) -> str:
    """Return a citation hint in the exact ``___ (phrase)`` format."""
    import re
    match = re.search(r"___ \(([^()\n]+)\)", sentence)
    return match.group(1) if match else ""


def _verify_fr_gender(topic: Topic, item: dict,
                      sentence: str, answer: str) -> tuple[bool, str]:
    noun = (item.get("noun") or "").strip()
    row = _find_bank_row(topic, noun=noun)
    if row is None:
        return False, f"noun {noun!r} not in bank"
    gender = row["gender"]
    target = (item.get("target") or "").strip().lower()
    if not target:
        target = "indefinite"
    expected_by_target = {
        "indefinite": {"m": "un", "f": "une"}[gender],
        "un_une": {"m": "un", "f": "une"}[gender],
    }
    expected = expected_by_target.get(target)
    if expected is None:
        return False, f"bad gender target {target!r}"
    if not _blank_before(sentence, noun):
        return False, "blank is not directly before the stated noun"
    if not _bank_answer_matches(sentence, answer, expected):
        return _wrong_bank_answer(answer, expected)
    return True, ""


def _verify_pt_gender(topic: Topic, item: dict,
                      sentence: str, answer: str) -> tuple[bool, str]:
    key = (item.get("noun_or_frame") or item.get("noun") or "").strip()
    row = _find_bank_row(topic, noun_or_frame=key)
    if row is None:
        return False, f"noun/frame {key!r} not in bank"
    fact = row["gender_or_correct"]
    if fact in ("m", "f"):
        target = (item.get("target") or "definite").strip().lower()
        expected_by_target = {
            "definite": {"m": "o", "f": "a"}[fact],
            "indefinite": {"m": "um", "f": "uma"}[fact],
        }
        expected = expected_by_target.get(target)
        if expected is None:
            return False, f"bad gender target {target!r}"
        if not _blank_before(sentence, key):
            return False, "blank is not directly before the stated noun"
    else:
        target = (item.get("target") or "bank").strip().lower()
        if target != "bank":
            return False, f"bank frame requires target='bank', got {target!r}"
        expected = fact
        if _answer_leaks(sentence, answer):
            return False, "answer leaks in sentence"
    if not _bank_answer_matches(sentence, answer, expected):
        return _wrong_bank_answer(answer, expected)
    return True, ""


def _pt_gender_uses_bank_frame(topic: Topic, item: dict) -> bool:
    """True for full-phrase PT rows whose novel context needs Tier B."""
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    key = (item.get("noun_or_frame") or item.get("noun")
           or meta.get("noun_or_frame") or meta.get("noun") or "").strip()
    row = _find_bank_row(topic, noun_or_frame=key)
    return bool(row and row.get("gender_or_correct") not in ("m", "f"))


def _verify_it_noun(topic: Topic, item: dict,
                    sentence: str, answer: str) -> tuple[bool, str]:
    noun = (item.get("noun") or "").strip()
    row = _find_bank_row(topic, noun=noun)
    if row is None:
        return False, f"noun {noun!r} not in bank"
    target = (item.get("target") or "plural").strip().lower()
    expected_by_target = {
        "plural": row["plural"],
        "singular_phrase": _join_article_noun(
            row["article_sg"], row["singular"]),
        "plural_phrase": _join_article_noun(
            row["article_pl"], row["plural"]),
    }
    expected = expected_by_target.get(target)
    if expected is None:
        return False, f"bad noun target {target!r}"
    if not _mentions(sentence.replace("___", " "), noun):
        return False, "stated noun does not appear outside the blank"
    # Strip the "(citation noun)" hint before the leak check: invariant
    # plurals (la città / le città) legitimately repeat the hint word in
    # the answer and must not be false-flagged.
    if _answer_leaks(sentence.replace(f"({noun})", " "), answer):
        return False, "answer leaks in sentence"
    if not _bank_answer_matches(sentence, answer, expected):
        return _wrong_bank_answer(answer, expected)
    return True, ""


def _verify_bank_blind(topic: Topic, item: dict,
                       sentence: str, answer: str) -> tuple[bool, str]:
    if topic.key == "fr_prep_lieux":
        place = (item.get("place") or "").strip()
        row = _find_bank_row(topic, place=place)
        if row is None:
            return False, f"place {place!r} not in bank"
        surface = place[3:] if place.startswith(("Le ", "La ")) else place
        expected = row["correct_prep"]
        if expected.endswith("'"):
            import re
            placed = re.search(rf"___{re.escape(surface)}(?!\w)", sentence,
                               re.IGNORECASE)
        else:
            placed = _blank_before(sentence, surface)
        if not placed:
            return False, "blank is not immediately before the stated place"
        if not _bank_answer_matches(sentence, answer, expected):
            return _wrong_bank_answer(answer, expected)
        return True, ""

    if topic.key in ("pt_regencia_verbal", "it_reggenze_verbali"):
        verb = (item.get("verb") or "").strip()
        pattern = (item.get("pattern") or "").strip()
        row = _find_bank_row(topic, verb=verb, pattern=pattern)
        if row is None:
            return False, f"verb/pattern {verb!r}, {pattern!r} not in bank"
        expected = row["prep"]
        if not _bank_answer_matches(sentence, answer, expected):
            return _wrong_bank_answer(answer, expected)
        return True, ""

    if topic.key == "de_dativ_verben":
        verb = (item.get("verb") or "").strip()
        row = _find_bank_row(topic, verb=verb)
        if row is None:
            return False, f"verb {verb!r} not in bank"
        case = (item.get("case") or "").strip().lower()
        if case != row["case"]:
            return False, (f"verb {verb!r} governs {row['case']}, "
                           f"item says {case or '<missing>'}")
        # The approved v1 has no general NP-inflection engine. Pinning the
        # visible citation phrase to the selected bank row lets novel contexts
        # reuse that row's fully declined answer without pretending to parse
        # arbitrary German noun phrases. Tier B still checks the new context.
        citation = _citation_after_blank(sentence)
        if not citation:
            return False, "missing parenthesized citation phrase after blank"
        bank_citation = _citation_after_blank(row["example_frame"])
        if citation != bank_citation:
            return False, (f"citation phrase {citation!r} does not match "
                           f"bank row {bank_citation!r}")
        expected = row["example_answer"]
        if not _bank_answer_matches(sentence, answer, expected):
            return _wrong_bank_answer(answer, expected)
        return True, ""

    return False, f"unsupported bank-blind topic {topic.key!r}"


def verify_item(topic: Topic, item: dict) -> tuple[bool, str]:
    """Static checks (no network). Returns (ok, reason-if-rejected).
    Tier-B topics/items additionally require verify_blind() to pass."""
    sentence = _item_text(item.get("sentence"))
    answer = _item_text(item.get("answer"))

    if "___" not in sentence:
        return False, "no blank in sentence"
    if not answer:
        return False, "empty answer"
    if topic.key == "pt_clitic_placement":
        person = (item.get("person") or "").strip().lower()
        if person in ("2s", "2p"):
            return False, ("tu/vós forms excluded — Brazilian drills use "
                           "você (3s) / vocês (3p)")
        import re
        non_br = re.search(
            r"(?<!\w)(?:tu|vós|te|vos|contigo|convosco|"
            r"teu|tua|teus|tuas|vosso|vossa|vossos|vossas)(?!\w)",
            f"{sentence} {answer}", re.IGNORECASE,
        )
        if non_br:
            return False, ("tu/vós forms excluded — Brazilian drills use "
                           "você/vocês and proclisis defaults")
    if (topic.key in _NEW_BANK_KEYS
            or topic.verify in ("de_np", "de_passiv")) \
            and sentence.count("___") != 1:
        return False, "sentence must contain exactly one blank"
    if (topic.key in _NEW_BANK_KEYS and _answer_case_text(answer).endswith("'")
            and sentence.split("___", 1)[1].startswith(" ")):
        return False, "apostrophe answer must join the following word"
    # Leak check skipped for German article topics: the same article form
    # legitimately appears for other nouns in almost any sentence.
    if (topic.verify not in ("de_art", "de_art_blind", "fr_gender",
                             "pt_gender", "it_noun")
            and _answer_leaks(sentence, answer)):
        return False, "answer leaks in sentence"

    if topic.verify == "de_np":
        return _verify_de_np(item, sentence, answer)

    if topic.verify == "de_passiv":
        return _verify_de_passive(topic, item, sentence, answer)

    if topic.verify == "blind":
        if topic.answer_set is not None:
            if not any(_bank_answer_matches(sentence, answer, allowed)
                       for allowed in topic.answer_set):
                return False, f"answer {answer!r} not in closed inventory"
        if topic.key == "fr_an_annee":
            import re
            if (re.search(r"\bNouvel\s+___", sentence, re.IGNORECASE)
                    and _answer_case_text(answer) != "An"):
                return _wrong_bank_answer(answer, "An")
        # Exact bank frames additionally retain their curated answer and case.
        # Novel contexts cannot have row identity, so Tier B handles them.
        if topic.key in _NEW_BANK_KEYS:
            row = next((e for e in _bank_entries(topic)
                        if _norm_key(e.get("frame")) == _norm_key(sentence)), None)
            if row is not None and not _bank_answer_matches(
                    sentence, answer, row["correct"]):
                return _wrong_bank_answer(answer, row["correct"])
        return True, ""

    if topic.verify == "bank_blind":
        return _verify_bank_blind(topic, item, sentence, answer)

    if topic.verify == "fr_gender":
        return _verify_fr_gender(topic, item, sentence, answer)

    if topic.verify == "pt_gender":
        return _verify_pt_gender(topic, item, sentence, answer)

    if topic.verify == "it_noun":
        return _verify_it_noun(topic, item, sentence, answer)

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


_BLIND_SOLVER = """{language} grammar exercise. Fill the blank.

Sentence: {sentence}

The blank contains exactly one of: {inventory}

If Ø is listed, it is the literal answer marker for a grammatically bare slot
(no preposition); return Ø rather than an empty string.

Return JSON: {{"answer": "..."}} — the blank's content only, nothing else."""

_BLIND_SOLVER_DE_DATIV = """German grammar exercise. Fill the blank.

Sentence: {sentence}

The phrase immediately after ___ in parentheses is a NOMINATIVE citation-form
hint. The hint is removed from the completed sentence. Infer the grammatical
case required by the sentence, inflect that entire phrase accordingly, and
return the COMPLETE phrase, including its determiner, adjectives, and noun.
Never return only the article or determiner.

Citation phrase: {citation}

Return JSON: {{"answer": "..."}} — the blank's complete content only, nothing
else."""

_PT_FRAME_CONTEXT_SOLVER = """Brazilian Portuguese grammar check.

Sentence with blank: {sentence}
Candidate blank content: {answer}
Completed sentence: {completed}

Does the candidate form a grammatically integrated, natural phrase in this
specific completed sentence? Judge grammatical and semantic fit, not whether
some different phrase could also replace it. Return JSON: {{"valid": true}} or
{{"valid": false}} only."""

BLIND_K = 3
BLIND_MAX_ATTEMPTS_PER_VOTE = 2


async def verify_blind(topic: Topic, item: dict,
                        inventory: list[str] | None = None) -> tuple[bool, str]:
    """Tier-B verification with K independent, unanimous solver votes.

    Blind-fill topics hide the answer and require all solvers to reproduce it;
    disagreement means wrong or ambiguous, both fatal for a drill card. Full-
    phrase PT gender rows have an exact deterministic answer already, so their
    solvers instead judge whether that phrase fits the novel context. `inventory`
    overrides the topic's answer_set for per-item candidate pairs.
    """
    inv = inventory if inventory is not None else topic.answer_set
    prof = LANG_PROFILE.get(topic.lang, LANG_PROFILE["es"])
    if (topic.key == "pt_gender_core"
            and _pt_gender_uses_bank_frame(topic, item)):
        surface_answer = _sentence_surface_answer(
            item["sentence"], _answer_case_text(item["answer"]))
        prompt = _PT_FRAME_CONTEXT_SOLVER.format(
            sentence=item["sentence"],
            answer=surface_answer,
            completed=item["sentence"].replace("___", surface_answer, 1),
        )
    elif topic.key == "de_dativ_verben":
        prompt = _BLIND_SOLVER_DE_DATIV.format(
            sentence=item["sentence"],
            citation=_citation_after_blank(item["sentence"]),
        )
    else:
        # prof["variety"] not ["language"]: the promoted units need
        # variety-pinned solvers (BR Portuguese) — commission K.
        prompt = _BLIND_SOLVER.format(
            language=prof["variety"],
            sentence=item["sentence"],
            inventory=", ".join(inv or []) or "the missing word(s)",
        )
    import asyncio

    if (topic.key == "pt_gender_core"
            and _pt_gender_uses_bank_frame(topic, item)):
        async def _validity_vote() -> bool | None:
            for _ in range(BLIND_MAX_ATTEMPTS_PER_VOTE):
                try:
                    raw = await gemini.generate_text(
                        prompt, json_mode=True, temperature=0.2)
                except Exception:  # noqa: BLE001 — bounded, fail-closed retry
                    continue
                if isinstance(raw, dict) and isinstance(raw.get("valid"), bool):
                    return raw["valid"]
            return None

        context_votes = await asyncio.gather(
            *(_validity_vote() for _ in range(BLIND_K)))
        if all(vote is True for vote in context_votes):
            return True, ""
        return False, f"context disagreement: votes {context_votes}"

    async def _valid_vote() -> str:
        # A transport/malformed-response failure is not linguistic evidence.
        # Refill that solver slot, but fail closed unless all K slots produce
        # valid answers within the bounded attempt count.
        for _ in range(BLIND_MAX_ATTEMPTS_PER_VOTE):
            try:
                raw = await gemini.generate_text(
                    prompt, json_mode=True, temperature=0.2)
            except Exception:  # noqa: BLE001 — bounded retry then fail closed
                continue
            if isinstance(raw, dict):
                answer = raw.get("answer")
                if isinstance(answer, str):
                    vote = _answer_case_text(answer)
                    if vote:
                        return vote
        return "<error>"

    votes = await asyncio.gather(*(_valid_vote() for _ in range(BLIND_K)))
    target = _answer_case_text(item["answer"])
    if all(_bank_answer_matches(item["sentence"], v, target) for v in votes):
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
    topic_needs_blind = topic.verify in (
        "blind", "de_art_blind", "bank_blind")
    accepted, rejected, pending_blind = [], [], []
    seen_keys: set = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        # Non-verb clozes can also reuse `infinitive` as their citation hint:
        # the card/audio pipeline removes "___ (hint)" after filling it.
        hint = None
        if is_morph:
            hint = _item_text(item.get("infinitive")).lower() or None
        elif topic.verify == "it_noun":
            hint = _item_text(item.get("noun")) or None
        elif topic.key == "de_dativ_verben":
            hint = _citation_after_blank(item.get("sentence") or "") or None
        elif topic.verify == "de_np":
            hint = _item_text(item.get("adjective")) or None
        elif topic.verify == "de_passiv":
            hint = _item_text(item.get("infinitive")).lower() or None
        item_tense = (_de_passive_tense(item.get("tense"))
                      if topic.verify == "de_passiv" else None)
        base = {
            "lang": topic.lang, "topic": topic.key,
            "infinitive": hint,
            "mood": topic.mood or None,
            "tense": item_tense or topic.tense or None,
            "person": (_item_text(item.get("person")).lower()
                       or None) if (is_morph or topic.verify == "de_passiv")
                      else None,
            "sentence": _item_text(item.get("sentence")),
            "answer": _item_text(item.get("answer")),
            "gloss_en": _item_text(item.get("gloss_en")),
            "why_en": _item_text(item.get("why")),
        }
        if topic.verify in ("de_art", "de_art_blind"):
            base["meta"] = {k: item.get(k)
                            for k in ("noun", "prep", "case", "definite")}
        elif topic.key in _BANK_META_FIELDS:
            base["meta"] = {k: item.get(k)
                            for k in _BANK_META_FIELDS[topic.key]}
        elif topic.key in _SPECIAL_META_FIELDS:
            base["meta"] = {k: item.get(k)
                            for k in _SPECIAL_META_FIELDS[topic.key]}
        ok, reason = verify_item(topic, item)
        if ok and topic.key in _NEW_BANK_KEYS:
            base["answer"] = _sentence_surface_answer(
                base["sentence"], base["answer"])
        key = ((base["infinitive"], base["person"]) if is_morph
               else base["sentence"].lower())
        if ok and key in seen_keys:
            ok, reason = False, "duplicate in batch"
        if ok:
            seen_keys.add(key)
            # Passive is hybrid per item: known participles finish at
            # Tier A; unknown lexical participles fall back to K=3 blind.
            item_needs_blind = (
                topic_needs_blind
                or (topic.key == "pt_gender_core"
                    and _pt_gender_uses_bank_frame(topic, item))
                or (topic.verify == "de_passiv"
                    and _de_passive_needs_blind(item))
            )
            (pending_blind if item_needs_blind else accepted).append(
                (base, item) if item_needs_blind else base)
        else:
            base["reject_reason"] = reason
            rejected.append(base)

    # Tier B: statically-OK items must also survive their solver check.
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
