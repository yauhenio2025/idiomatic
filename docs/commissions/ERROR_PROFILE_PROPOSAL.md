# Proposal: leveraging the personal error mine (5-language deficiency profile)

> Written 2026-07-31, synthesizing the five commissioned per-language
> profiles in `docs/research/error-profiles/{fr,pt,es,de,it}.md`.
> Sources mined: the "Language Courses - errors" spreadsheet (10,314
> teacher-marked rows, 2019–2022: 4,662 grammar/usage, 3,615 vocab,
> 1,181 pronunciation) + 141 Teachee lesson decks (3,502 notes,
> 2022–2024) + the `_errors::*` Anki decks (confirmed to be the
> imported copy of the spreadsheet — no double counting). Read the
> per-language files for counts, verbatim examples, and the
> machine-readable F3 seed JSON blocks (§7 of each).

## 1. The learner profile, in one page

Five findings hold across languages and change what the grammar
initiative should build next:

1. **The error mass is in SELECTION and AGREEMENT, not conjugation.**
   The shipped decks are verb-tense-heavy; the recorded errors are
   preposition choice, gender/agreement, articles/quantifiers, word
   order, and calques. French is the extreme case: verb-tense
   selection ≈ 2% of 2,523 classified grammar errors, while categories
   with **no unit at all** carry ~55%. The curriculum is inverted
   relative to the evidence, and the new `/grammar` target_size knobs
   + new units are the fix.
2. **Cross-language interference is the #1 systemic weakness** — and
   has zero coverage. es: 42% of verbatim errors are pt/it/en
   transfer; pt: 54% are es/it transfer; fr shows an Italian layer
   (missing `pas`, che→que) plus ~47 invented pan-Romance verbs
   (insérir, gestir, mostrer); de shows Russian-L1 signatures (цель→
   "Meine Ziel" gender transfer, "nach Türkei" article drop). The
   strategy doc's F4 cross-language format (§4) was designed for
   exactly this and never built. Italian is the learner's strongest
   language and mostly the interference SOURCE, not victim (user
   confirmed 2026-07-31 — no special Italian error capture needed).
3. **The fossils are known, named, and countable.** `beaucoup des`
   138×, an/année 102×, "les premières deux semaines" ~90×, `en
   Berlin` 36×, `là` for `y` 22× (fr); -ma masculines and -agem
   feminines re-taught for six years, fiz/fez person confusion ×29
   (pt); `sobre control`→`bajo control` verbatim twice 19 months
   apart, muy/mucho ×7 (es); adjective-ending × gender × case errors
   spanning 2019→2024 (de). These are not open-ended categories —
   they're drillable closed lists.
4. **Some units are refuted by the evidence — but read absences
   carefully.** Zero recorded por/para errors + user confirmation
   ("I understand the difference") → genuinely lower. Zero recorded
   es subjunctive errors → NOT lowered: the user's own caveat
   (2026-07-31) is that absence there may mean avoidance, unmarked
   errors, or native-like slips — so the subjunctive family keeps its
   targets, and near-zero-evidence synthetic futures/conditionals
   (which he replaces with periphrasis) get small-not-gutted targets.
5. **Gender is a per-learner closed list.** fr: 297 gender rows
   concentrate on ~40 nouns (période, fois, méthode, vie, moyen…);
   pt: 225 rows on -ma/-agem + a short noun list. Drilling *his*
   nouns beats drilling gender in general.

Pronunciation inventories (for a later audio wave): fr nasals/liaison,
pt ti/di affrication + sem/sim + mas/mais, de [ç]/ü — see §5 of each
profile.

## 2. Leverage plan (proposed Wave 7, phased)

### Phase 0 — today, no code: retune the dials
Using the new /grammar UI (target_size + status per unit):
- **Raise**: pt_preterito_perfeito, pt_futuro_subjuntivo,
  fr_present_irreguliers, es_clitics_selo, de_gender.
- **Lower**: fr_futur_simple, fr_conditionnel_present, pt_futuro_simples,
  pt_condicional_presente, es_futuro, es_condicional, es_perfecto,
  es_cond_perf, es_plusc_subj.
- **Promote planned → build next**: de_adj_endings (strongest verified
  class in de; Tier A verifiable today), fr_pronoms_y_en (27+ direct
  errors), pt_clitic_placement (~21), it_clitici_ci_ne (74-row teacher
  remedial block), es_ser_estar (activate SMALL — 1 error in 6 years;
  estar+participle focus only).

### Phase 1 — the personal error registry + F3 error-correction format
New table `personal_errors` (lang, wrong, right, category, why,
occurrences, first/last_seen, source, status), seeded from the ~190
curated F3 pairs in the five profiles (§7 blocks) and expandable from
the full extracts. Then the **F3 format** (strategy §4; the format the
learner's hand-made `_errors` decks proved works for him):
- Card: front = his verbatim wrong sentence marked "⚠ my error";
  answer = the correction; Why = the one-line rule. **Fits the frozen
  14-field model as-is** (Sentence/Answer/SentenceFull/Why; Symbol=⚠) —
  no model change, GUIDs from grammar_items ids, same subdeck
  mechanics (cluster per language, e.g. "9 Meus erros" / "9 Mes
  erreurs").
- Verification: seed pairs are teacher-attested (no LLM verification
  needed); LLM-generated VARIATIONS of a pattern go through the
  existing Tier B blind-fill.
- This is the highest-leverage single build: every card is a
  documented personal failure, not a guess about one.

### Phase 2 — new units the evidence justifies (per-language shortlist)
Full tables in the profiles; the priority picks:
- **fr** (new clusters 5 Prépositions / 6 Genre & accord / 7 Articles
  & quantités / 8 Ordre des mots): fr_quantites_de (161 rows, #1
  single error), fr_prep_lieux (`en Berlin` 36×), fr_genre_noyau (his
  40-noun list), fr_an_annee (102 rows), fr_ordre_mots, fr_prep_verbes
  (mirror of es_verb_prep; Lefff valency data already earmarked).
- **pt**: pt_gender_core (225 rows — biggest addressable category,
  trivially Tier A with a small answer bank → ship first),
  pt_regencia_verbal, pt_ser_estar_ficar.
- **es**: es_muy_mucho (closed class, es_por_para-shaped),
  es_light_verbs (tomar/cometer/hacer collocations),
  es_numeros_fechas (deterministically verifiable).
- **de**: de_passiv (~35 teacher-supplied passives, zero spontaneous
  production), then a "5 Kasus" cluster (de_dativ_verben,
  de_n_deklination, de_genitiv); scope de_verb_core to passive/KII —
  present/perfect agreement is NOT his gap.
- **it**: SELF-REPORTED profile supersedes the thin 2019 data (user,
  2026-07-31): weaknesses = prepositions, congiuntivo, passato remoto
  ("so complex I never use it" — classic avoidance), articles +
  gender, especially gendered PLURAL endings. Actions: raise
  it_congiuntivo_presente + it_passato_remoto targets; build
  it_reggenze_verbali (prep regimes; also 5 of the 11 recorded errors)
  and a new it_genere_plurali unit (articles il/lo/la, -o/-a/-e/-i
  plural endings, irregular plurals il problema/i problemi, la mano/
  le mani, l'uovo/le uova); it_clitici_ci_ne stays promoted. Level:
  upper-intermediate, not "no work needed".

### Phase 3 — interference contrast deck (F4)
One cross-Romance deck built FROM the attested interference pairs
(todavia≠todavía, contento→contente, fato≠feito, inserir→insertar,
che→que…): same-frame cards that force the two languages apart. Pan
2025 Exp. 4 says deliberate mixing helps, and 54% of pt errors say
it's needed. Delivery: its own apkg kind or a cluster inside each
grammar deck (decision point §4).

### Phase 4 — error-aware generation everywhere
Feed each unit's generator prompt a "known errors in this category"
block from `personal_errors` (e.g. es_verb_prep gets: "learner says
*en/para* after motion verbs — build items that force *a*"). Cheap
(prompt-only), compounds forever. Same registry becomes the Wave 5
planner's prior: the planner starts from documented deficits instead
of a cold revlog.

### Phase 5 — grammar explainers (the "readings/listening" ask)
For each fossil cluster, one 2–4 minute audio essay (ElevenLabs, same
stitching pipeline): "Why it's *beaucoup de*, never *beaucoup des*" —
the metalinguistic-feedback evidence (Heift; strategy §3b) says
explanation + examples beats bare correction for structural repeats.
Delivered as a small "Grammar radio" deck (front: topic card, audio
autoplays) or plain mp3s. Pairs each explainer with its F3 cards.

## 3. Outside-the-box options (ranked by leverage/effort)

1. **Fossil surveillance**: a fossil that stops erring isn't proven
   dead — schedule probe items (fresh sentences, same trap) per fossil
   every N weeks; two clean sessions retire it (Serfaty & Serrano
   criterion applied to PATTERNS, not cards).
2. **Live capture going forward**: lessons continue weekly. Lightest
   path: a `/admin/lesson-errors` endpoint + dashboard paste box (or
   photo→Gemini extraction) that appends to `personal_errors` after
   each lesson; new errors auto-feed F3 generation. (Skip Italian.)
3. **Interference direction matrix**: the profiles show direction —
   it→es, es→pt, it→fr — build the F4 deck asymmetrically (drill the
   RECEIVING language's form; the source language is the distractor).
4. **Error-seeded idiom examples**: the idiom pipeline's 6 example
   sentences per expression could deliberately exercise his weak
   structures (beaucoup de, quando+subjuntivo) — passive exposure
   aligned with deficits, zero extra decks.
5. **Deterministic verifiers for cheap wins**: numbers/dates (es), an/
   année (fr), gender banks (pt/fr) are verifiable without any LLM —
   these units are nearly free to run at high volume.
6. **Compound-noun routing (de)**: the 22 compound corrections are a
   circumlocution habit, not grammar — route to the vocab/idiom side.

## 4. Decision points — RESOLVED (user delegated, 2026-07-31)

User: "take the decisions you think are necessary… start formulating
commissions… give codex a pretty substantial task." Decisions taken:
1. Phase-0 retuning APPLIED via /admin/grammar-unit (raises to 18:
   pt_preterito_perfeito, pt_futuro_subjuntivo, fr_present_irreguliers,
   es_clitics_selo, de_gender, it_congiuntivo_presente,
   it_passato_remoto; lowers to 8: fr_futur_simple,
   fr_conditionnel_present, pt_futuro_simples, pt_condicional_presente,
   es_por_para; mild lowers to 10: es_futuro, es_condicional,
   es_perfecto; es subjunctive family kept at 12 per the avoidance
   caveat). Top-ups run for the raised units.
2. F3 placement: cluster inside each grammar deck ("9 Mes erreurs" /
   "9 Meus erros" / …), no new deck kind.
3. Order: registry (codex commission A, RUNNING) → F3 → new units
   (banks prepared by codex commission B, RUNNING) → F4 → explainers.
4. Live capture: deferred until after Wave 5 telemetry.
5. Raw corpus + registry stay OUT of the public repo (repo must stay
   public for Render; personal lesson data lives in
   `~/projects/idiomatic-data/errmine/`, loaded into the DB via admin
   endpoint when Phase 1 ships).

## 4b. Original decision points (for reference)

1. Approve Phase 0 retuning now? (I can apply the target_size changes
   via the dashboard/DB in minutes; reversible.)
2. F3 subdeck naming/placement: per-language cluster "9 Mes erreurs"
   inside the existing grammar decks vs a separate deck. (Recommend:
   cluster inside — same delivery, no new deck type.)
3. Phase order: registry+F3 (1) before new units (2), or interleave
   per language? (Recommend: 1 → 2, because F3 seeds are ready today
   and new units need generator+verifier work per unit.)
4. Live capture (outside-the-box #2): worth building now, or after
   Wave 5 telemetry?
5. Grammar explainers: wanted early (they're cheap and directly
   answer the "readings/listening" ask) or after F3?

## 5. Commission for the deeper follow-up study (ready to run)

> For a fresh session with ample budget. Inputs: this file, the five
> profiles, the extracts (regenerate via the openpyxl/apkg scripts in
> this session's history if the scratchpad is gone — sources:
> `~/Downloads/Language Courses - errors.xlsx`, `~/Downloads/teachee/`).

Tasks:
1. **Validate + normalize**: re-run the five agents' categorizations
   with a second independent pass (different categorizer prompts);
   reconcile disagreements; produce one merged `personal_errors.jsonl`
   (schema in Phase 1) with dedup across xlsx/Teachee eras and
   per-error occurrence counts. Target: every entry has lang, wrong,
   right, category, why, occurrences, dates, confidence.
2. **Design review**: `personal_errors` schema + F3 generation/
   verification flow + fossil-surveillance scheduling, as a concrete
   implementation plan against this repo (grammar/ module layout,
   endpoints, dashboard surface).
3. **Interference matrix study**: from the merged registry, compute
   the direction matrix (source lang × target lang × category, with
   counts) and design the F4 contrast deck from the top cells.
4. **Vocabulary side**: the 3,615 vocab rows + Teachee vocab cards
   were only lightly used here — cluster them (domains, collocation
   types) and propose how the idiom/pool pipeline should absorb them
   (they are pre-validated "words he reached for and lacked").
5. Report back as `docs/research/error-profiles/SYNTHESIS_V2.md` +
   an updated wave plan proposal for GRAMMAR_STRATEGY §8.

## 6. Cost note

Phases 0–1 are near-free (seeds are teacher-attested; no verification
LLM spend). New units cost the same as existing ones (~pennies per
batch on Gemini Flash). Explainer audio ≈ $0.05/1k chars ElevenLabs.
The deep-study commission is one heavy session of analysis, no prod
risk.
