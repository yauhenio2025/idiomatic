# Legacy EXCERCISES deck audit (old Anki account) + revival proposal

> Audited 2026-08-03 directly from the `evgeny.morozov+2@gmail.com`
> collection (read-only SQLite copy). Scope: the `EXCERCISES::{DE,ES,FR,IT,PT}`
> tree — 13,377 notes, all on the 2-field `_Basic` model, created Aug 2023
> with an early-LLM + MT pipeline. Companion decision doc for bringing this
> material into the main (evgeny@the-syllabus.com) profile properly.

## 1. What the corpus is

~2,600 **shared English prompts** rendered into each of the 5 languages
(identical topic structure and counts per language — the same source set
was translated five times). Topics per language:

| Topic | Cards | What it drills |
|---|---|---|
| FANCY_VOCAB | 582 | academic/abstract verbs & adjectives |
| CONNECTING | 401 | discourse connectors, hedges, argument moves |
| TENSES | 300 | tense sequencing incl. pluperfect/perfect contrast |
| CONDITIONALS | 299 | full conditional ladder incl. counterfactuals |
| COLD_WAR_VOCAB | 245 | political/historical register |
| GEOPOLITICS | 150 | term + one-line definition pairs |
| PRONOUNS / REFLEXIVE | 300 | clitic placement, object pronouns |
| BIG_TECH_VOCAB | 145 | tech-criticism terminology |
| COMMANDS | 100 | imperatives + clitics |
| BIG_TECH_PHRASES | 90 | long sentence-openers ("In light of…") |
| FALSE_FRIENDS | ES 94 / PT 225 only | cross-language interference |

Direction is EN→TL (production). Study history: **only PT was ever
studied** (1,419 reps / 580 cards, 2023-08 → 2024-03). ES/DE/FR/IT: zero
reviews ever.

## 2. Audit findings

### 2.1 The Italian deck does not exist (critical)

All **2,612/2,612 IT cards have backs byte-identical to the FR deck** —
verified by exact cross-match on shared (topic, front) keys. The "Italian"
deck is a full copy-paste of the French export; Italian translations were
never generated. Never studied, so no damage — but there is nothing to
migrate for IT except the English fronts.

### 2.2 Spanish contamination in PT (the half-remembered bug)

`PT::BIG_TECH_PHRASES`: **30 of 91 backs are Spanish** (byte-identical to
the ES deck). The remaining 61 are genuine (Brazilian) Portuguese. This is
in the one language tree that WAS studied. Nothing else in PT is
contaminated (ES↔PT vocab matches like "Capitalismo de plataforma" are
legitimate identical cognates).

### 2.3 ES::FALSE_FRIENDS is pedagogically toxic

~half of the 94 cards carry **factually wrong glosses about the other
target languages**, e.g.: PT *atum* glossed "garlic" (= tuna); PT *rato*
glossed "a short time" (= mouse; the ES word has that sense); PT *êxito*
glossed "exit" (= success); PT *selo* glossed "jealousy" (= stamp); IT
*parare* glossed "to prepare" (= to parry); IT *delitto* glossed "murder"
(= crime); FR *tentation* glossed "attempt" (= temptation); FR *débattre*
glossed "to beat" (= to debate). Plus incoherent entries (*lentejas →
lente*), non-false-friends ("Same meaning in Spanish"), and duplicate
fronts with contradictory answers (*éxito* twice). For a 5-language
learner this deck actively teaches interference errors. **Do not migrate;
rebuild from scratch.** PT::FALSE_FRIENDS (225, PT→EN format) is mostly
sound, occasionally strained ("Cadeira ≠ cadaver").

### 2.4 Baseline quality of the clean material

Stratified samples (~45/language) of DE/FR/ES/PT main decks: solid
DeepL-era translationese, grammatically correct in the large majority of
cards, but with a real defect rate (~5-10%) and systematic weaknesses:

- Mistranslations: ES "Nuclear fallout" → *La caída nuclear* (should be
  *lluvia radiactiva*); FR "to fail" → *pour échouer* (spurious *pour*);
  ES "They've instructed us…" → *Nos **ha** pedido…* (wrong number).
- Subject drift: PT "**They** have been championing…" → *Os senhores têm
  defendido…* (turns "they" into formal "you").
- Register inconsistency: ES COMMANDS are all *usted*, ES PRONOUNS are
  *tú*; PT COMMANDS mix imperative and bare infinitive.
- Weak glosses: PT "Accordingly" → *De acordo* (wrong sense);
  single-translation answers where 2-3 alternatives are equally right.
- Machine-English fronts: "the Technological solutionism", "Recommend her
  that documentary!", "The professor will explain her the theory"
  (ungrammatical EN source).
- Hygiene: 21-60 duplicated fronts per language (some with conflicting
  backs), 1 empty back (ES TENSES), deck-name typos (EXCERCISES,
  RELFEXIVE/REFLEXIV/REFLEXIVE).

### 2.5 Verdict

The **English prompt set is the durable asset** — 2,600 prompts perfectly
aligned with the user's professional register (tech criticism, Cold War,
geopolitics, academic argument). The translations are disposable: partly
missing (IT), partly contaminated (PT), uniformly flat (one context-free
answer, no audio, no alternatives, 2-field model). Migrating the decks
as-is would import known errors into the main profile.

## 3. Usefulness ranking for advanced competence

- **High**: CONNECTING (discourse-level fluency is the C1→C2 bottleneck);
  FANCY_VOCAB (academic register); CONDITIONALS + TENSES (counterfactuals
  and tense sequencing = the user's documented error hotspots — cross-ref
  error-mine profiles); GEOPOLITICS/COLD_WAR/BIG_TECH vocab (the exact
  register the user speaks/writes professionally).
- **Medium**: COMMANDS, PRONOUNS, REFLEXIVE (clitic mechanics; overlaps
  Wave 1-6 grammar decks — dedupe against them).
- **Negative as-is**: ES FALSE_FRIENDS (§2.3). The *concept* is excellent
  for this user (5 interfering Romance/Germanic languages) but needs a
  verified rebuild as a cross-language interference deck.
- Format caveat: BIG_TECH_PHRASES full-sentence translation cards are poor
  SRS items (too long, one "correct" answer among many). Reuse as
  production/shadowing prompts, not as-is.

## 4. Proposal: "Exercises 2.0" in the main profile (pilot-first)

Treat the English prompt set as a curriculum seed and rerun it through the
existing grammar-initiative machinery rather than importing old cards:

1. **Extract + curate prompts** (codex-delegable): dump fronts, dedupe,
   fix ungrammatical EN, tag by topic; drop/repair junk.
2. **Regenerate translations with current models**, 5 languages incl. the
   missing Italian, with the grammar initiative's verification discipline:
   Tier-B blind-fill/back-translation agreement + a trivial language-ID
   gate (would have caught both §2.1 and §2.2 automatically).
3. **Rich note model** (grammar-deck style, not `_Basic`): EN prompt, TL
   answer, accepted alternatives, register note, contrastive trap note
   (feed error-mine profiles here), example-in-context, ElevenLabs audio
   both directions; card types = EN→TL production, TL→EN, audio-only.
   Connectors become cloze-in-context rather than isolated glosses.
4. **Delivery** through the standard rolling-apkg + add-on path into the
   syllabus profile, one subdeck per topic, mirroring the grammar decks.
5. **Old account**: leave untouched except (user decision) deleting the
   French "Italian" deck and the 30 Spanish PT cards to prevent future
   accidental study. PT scheduling history is 2+ years stale — start
   fresh, don't migrate scheduling.

Per the pilot-first rule: build **one pilot deck (suggest ES CONNECTING,
~40 cards)** for approval before batching anything.
