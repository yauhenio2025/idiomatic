# Grammar Exercises in idiomatic — Strategy

> Status: v1, 2026-07-28. Synthesized from four commissioned research
> reports (raw findings with citations in `research/`):
> [community wisdom](research/anki-grammar-community.md) ·
> [data sources](research/grammar-data-sources.md) ·
> [SLA pedagogy](research/sla-pedagogy.md) ·
> [AnkiDroid tech](research/ankidroid-tech.md)

Goal: a systematic, personalized, LLM-driven grammar curriculum for
es / pt / fr / it / de, delivered as Anki decks through the existing
idiomatic pipeline, studyable text-first on Android tablets at the gym,
with audio drills later.

## 1. Constraints & context

- Study environment: elliptical machine, Android tablet → AnkiDroid.
  Text-first; no typing-heavy interactions while running. Big fonts,
  one decision per card.
- Learner profile: advanced-ish in all 5 languages (reads news, studies
  idioms from native video), morphology decayed after ~5-6 years without
  drilling. Simultaneous study of 4 Romance languages + German →
  interference is a first-class design problem, not an edge case.
- Delivery: must ride the existing apkg → add-on → AnkiWeb → AnkiDroid
  path. No new apps.

## 2. Audit of what already exists (collection inspected 2026-07-28)

- `_tenses_old/*` (5 decks, ~1.3-2k notes/lang): verb + tense tag on the
  front, the ENTIRE 6-person paradigm dumped on the back. 178,942
  reviews, last review 2022-08-20. Heavily used, then abandoned.
  Diagnosis: recognition-only, all-forms-at-once (no single retrieval
  target), ugly, no sentences, no context.
- `EXCERCISES/{DE,ES,FR,IT,PT}/*` (Aug 2023, ~2.6-2.8k notes/lang,
  GPT-generated EN→target translation sentences themed around the
  user's interests): essentially unstudied — only PT accumulated ~1.4k
  reviews, last 2024-03. Autopsy (why it failed): plain Basic notes with
  a wall of 200+ due per subdeck, no grading of difficulty, no
  progression, no explanations, full-sentence translation is too slow
  and too compound a task per rep (tests vocab+grammar+everything), and
  at least one known empty-answer defect. Lesson: raw LLM sentence dumps
  ≠ curriculum.
- `_errors/*` decks: hand-made cards from the user's OWN production
  errors ("my actual error: mucho de moda" → "muy de moda"), with TTS
  audio. Actually used for years. Lesson: error-driven, minimal-pair
  cards work for this learner. These decks are also a seed corpus for
  the diagnostic phase.

## 3. Curriculum scope (per language)

⏳ to be finalized against CEFR grammar syllabi from research.

Working taxonomy (topic → subtopics, frequency-ordered within):

1. Verb morphology: person×tense×mood forms, frequency-first AND
   pattern-complete — KOFI's key insight: ~70 well-chosen verbs cover
   ALL conjugation pattern groups of a Romance language (Spanish: 39
   patterns), so drilling those verbs transfers to every other verb.
   SUBTLEX per-form frequencies rank which tense×person cells matter.
2. Tense/mood SELECTION (harder and more valuable than forms):
   preterite vs imperfect (es/pt/fr/it), subjunctive triggers, conditional
   chains, future subjunctive (pt), passato remoto recognition (it),
   Konjunktiv I/II (de).
3. Prepositions: verb+preposition regimes, por/para, a/en, seit/vor, etc.
4. Articles & gender; German case system (article declension is the
   backbone of de grammar).
5. Clitic/object pronouns: placement, combination, contraction (pt/es/it/fr).
6. Agreement: participle agreement (fr/it), ser/estar (es/pt).
7. Connectives & word order: German V2/verb-final; subjunctive-forcing
   conjunctions in Romance.
8. Contrastive cross-language cards (es vs pt vs it faux amis of grammar)
   as a dedicated topic, since 4-Romance interference is guaranteed.

## 3b. Pedagogical principles (from the SLA research synthesis)

The evidence base, distilled to rules we build by (full citations in
the research annex):

- **Production requires production practice** (skill specificity,
  DeKeyser 1997): recognition-only cards won't transfer to speaking/
  writing. But **covert retrieval = overt** (Smith/Roediger/Karpicke
  2013): mentally producing the form then grading yourself is as good
  as typing it. Think-then-reveal production cards are therefore the
  workhorse format — perfect for the elliptical.
- **Interleave confusable forms; don't block** (Pan 2019 — literally on
  Spanish preterite/imperfect; Nakata & Suzuki 2019; Pan et al. 2025
  across 7 tenses in 2 Romance languages). Brief blocked warm-up only
  for genuinely new material. Pan 2025 Exp. 4: interleaving TWO Romance
  languages improved learners' ability to keep them apart — deliberate
  cross-language contrast cards are supported, not risky.
- **No mechanical drills** (Wong & VanPatten 2003, consensus): every
  item must require processing MEANING to answer. "Conjugate hablar in
  3sg preterite" is out; "Ayer María ___ (hablar) con su jefe" is in.
- **Structured-input / referential cards are a validated second genre**
  (VanPatten PI; Henshaw 2012): items where the FORM is the only cue to
  meaning ("Juan hablaba" — habitual or completed?) build the
  interpretation side that production cards don't.
- **Metalinguistic, error-specific feedback beats right/wrong**
  (Heift ICALL work): the back of the card should say WHY, briefly —
  exactly the user's instinct about explanations in English.
- **Mastery criterion**: Serfaty & Serrano 2024 — durable productive
  knowledge after two error-free sessions; use that as the topic
  retirement rule instead of an arbitrary interval.
- **Timing**: short lags early (proceduralization, Suzuki & DeKeyser
  2017), expanding later — FSRS approximates this. Add progressive
  TIME PRESSURE at later stages (automatization needs speeded meaningful
  production); answer latency (and its coefficient of variation) is a
  real automatization signal, distinct from accuracy.
- **Diagnostic-then-targeted beats a linear syllabus** for an advanced
  learner (fossilization literature + ITS tradition, VanLehn 2011):
  CEFR inventories serve as a CHECKLIST of candidate gaps, not a
  sequence to march through.
- **LLM role boundaries** (GEC/tutoring evals): LLMs are strong at
  explanation and item generation (with verification), but unreliable
  at unaided error DETECTION — so the learner model must be driven by
  Anki button/latency data aggregated per skill, with the LLM
  interpreting aggregates, not diagnosing raw answers.
- **FSRS models item memory, not rule mastery** — nothing in the SRS
  world schedules "the rule" across its many cards. Duolingo's
  half-life regression (Settles & Meeder 2016) is the precedent: track
  morphological-feature tags (e.g. `V;SBJV;PRS;3;SG` + verb class) as
  skills across items. That's what `grammar_topics`+GUID telemetry
  gives us.

## 4. Exercise formats

Grounded in §3b and in the community's proven designs. The single most
important external reference is the **KOFI "Ultimate Conjugation"
method** (Lisardo's decks for es/fr/it/pt — see community annex §1):
one (verb, tense, person) per card, presented as a cloze inside a short
target-language sentence, with tense/person signaled by IN-LANGUAGE
cues ("L'année dernière…", "Fue sorprendente que…") plus symbols
(⊙ present, → future, 〰 subjunctive) — never the metalinguistic label
"3rd person plural future". Self-graded mental production, no typing.
Its design rationale matches the SLA evidence point for point (one
retrieval target, production practice, no "song" recitation of
paradigms). We adopt the format and generate our own content.

The format set:

- **F1 sentence cloze, single target form** (the workhorse, KOFI-style):
  one blank, in-language cue + symbol, infinitive shown as hint.
  Back: the form, EN gloss, 1-line WHY when non-obvious ("pop-up
  grammar" — explanation on back only). HARD RULE from the community's
  #1 cloze complaint: the sentence + cue must UNIQUELY determine the
  answer; the verifier rejects items where a competing tense also fits.
- **F2 contrast/interpretation cards** (structured input, referential):
  the form is the only cue to meaning — "María pintaba un cuadro" →
  was it finished? Or minimal pairs: same frame, fuera vs fue, what
  changes? Directly targets selection topics (the hard 20%).
- **F3 error-correction**: a WRONG sentence (seeded from the user's own
  `_errors` decks + documented typical advanced-learner errors), find
  and fix mentally; back shows correction + rule. (Prompts > recasts:
  the card elicits self-correction before showing the answer.)
- **F4 cross-language contrast**: es/pt/it faux-amis of grammar
  ("in Spanish it's subjunctive here, in Portuguese future
  subjunctive"). Supported by Pan 2025 Exp. 4 — mixing Romance
  languages IMPROVES keeping them apart.
- **F5 landmark paradigm cards** (small number): a full table with 2-3
  cells blanked, for orientation in heavily syncretic corners (German
  declension). Community middle-ground (Scott / A Mind for Language)
  between "never show tables" and the old `_tenses_old` dump.
- Later, audio: **A1 beep-cloze** (server-stitched mp3 with beep over
  the blank → back plays the full sentence; zero JS needed) and
  **A2 anticipation drills** (EN prompt or TL frame → pause → answer
  audio), reusing `pipeline/audio.py` stitching + ElevenLabs voices.

Deck/scheduling decisions (community-informed):

- Grammar decks get their OWN FSRS preset, optimized separately —
  mixing easy grammar reps into vocab decks skews FSRS parameters, and
  conjugation reportedly decays fast past ~1-month intervals → higher
  desired retention (0.92-0.95) for this preset.
- No typing on the tablet (KOFI's choice too); typed variants are an
  optional desk-mode addition later via `{{type:nc:}}`.
- TL→TL where feasible (advanced-learner norm), EN only in explanations.
- Pacing: ~7-10 new grammar cards/day/language ceiling; small decks,
  short sessions — the EXCERCISES autopsy says walls of due cards kill
  the habit.

## 5. Data & generation

Design principle: **LLM generates, deterministic sources verify.**
Every generated conjugated form is checked against a morphology
database before it can enter a deck. Failed verification → regenerate,
never ship. This is evidence-backed, not paranoia: published evals
(MultiBLiMP 2025, MORPHOGEN, ALBA 2026) show frontier LLMs are
near-ceiling on high-resource conjugation but reliably fail on
(a) gender agreement in Romance, (b) variety defaults — LLMs need
explicit variety pinning either way (NB 2026-07-29: the user wants
**Brazilian** Portuguese, so the documented LLM drift toward BP is
benign here; the verifier still pins persons — tu/vós rejected), (c) rare literary tenses
(passato remoto irregulars), (d) regressions introduced by
post-training.

Chosen stack (license-clean, all verified 2026-07):

- **Morphology truth**: kaikki.org Wiktionary extracts (CC BY-SA,
  updated weekly, full paradigms all 5 langs) + **UniMorph 4.0**
  (CC BY-SA TSV; uniform feature schema `V;IND;PST;3;SG` across
  languages — ideal for the verifier). Per-language backstops: Fred
  Jehle DB (es, hand-curated gold set), Lefff (fr, LGPL-LR — also has
  verb valency for preposition exercises), Morph-it! (it), LABEL-LEX
  (pt, GPL, European-PT oriented), DWDSmor open edition (de, GPLv2,
  incl. case/article declension). `verbecc` (fr/es/it/pt Python
  conjugator) as a runtime library option, GPL caveat noted.
- **Sentences**: Tatoeba (CC BY + CC0 subset, weekly TSV, 440k-980k
  sentences per language with EN translation links) as the
  redistributable sentence base; own Gemini-generated sentences
  (themed to the user's interests, like the idiom pipeline) as the
  main source, verified. OpenSubtitles only as frequency signal, never
  verbatim (copyright-grey).
- **Frequency ordering**: SUBTLEX per-language + wordfreq +
  FrequencyWords. SUBTLEX is per-FORM, so tense/person frequency (which
  tenses to teach first, which persons dominate) is computable directly.
- **Curriculum taxonomy**: Spanish PCIC grammar inventories (free,
  clean HTML per CEFR level — best scrapeable taxonomy of the five);
  Portuguese Referencial Camões (free PDF + interactive inventories);
  Kwiziq public topic trees (fr/es, level-tagged); German Grammar
  Profile (KONVENS 2025) for de. Italian has NO open CEFR grammar
  dataset — triangulate from Kwiziq-style lists + CELI syllabi + the
  es/fr taxonomies (Romance structure transfers).
- **CC exercise prose to adapt**: COERLL materials (CC BY: Français
  interactif, Grimm Grammar de, Spanish Grammar in Context).
- Attribution/share-alike note: CC BY-SA data layers (kaikki, UniMorph,
  Tatoeba-BY) need an attribution note in the deck footer — plan a
  `Source` field on the note model from day one.
- Prior art to read before building the cloze generator:
  `jacopofar/grammar-quiz` (FOSS cloze generator over Tatoeba) and
  MultiBLiMP's UD+UniMorph minimal-pair pipeline (replicable for
  auto-generating distractor forms).

## 5b. Technical ground rules (verified against Anki/AnkiDroid docs, 2026-07)

Since AnkiDroid 2.17 (2024) the Rust backend from desktop Anki does all
template rendering/scheduling on Android too — template behavior is
byte-identical to desktop. Rules that follow:

- **Prefer backend features over JS**: cloze (`{{c1::ans::hint}}`,
  nested since 2.1.56, per-cloze conditionals `{{#c1}}…{{/c1}}`),
  type-answer with `{{type:nc:Field}}` (diacritic-insensitive — matters
  for all 5 langs), conditional sections, bundled `[sound:]` mp3s.
  These work identically on the tablet with zero hacks.
- **One cloze per note** for us: the server regenerates/updates items,
  and single-cloze notes give clean GUID-based updates + independent
  scheduling (no sibling-burying surprises).
- **Stable GUIDs from our DB primary keys** (subclass
  `genanki.Note.guid` — the default hashes all fields, so any text fix
  would mint a duplicate note). Frozen `model_id`. Re-importing an apkg
  with the same GUIDs updates fields WITHOUT touching scheduling/FSRS
  state — i.e. we can hotfix shipped cards safely.
- **Never change field count/order/names or template count** of a
  shipped note type — that forces a full one-way sync (poison for a
  tablet reviewer). Reserve `Extra1..ExtraN` spare fields from day one.
  Schema evolution = new model_id + new GUIDs + cleanup.json purge of
  the old deck.
- **Night mode**: include `.night_mode`/`.nightMode` rules explicitly,
  else AnkiDroid color-inverts heuristically.
- **Typing answers**: possible (`{{type:nc:}}`) but Android IME
  autocorrect interferes; and typing on an elliptical is a non-starter —
  keep typed cards an optional desk-mode variant, not the default.
- **Telemetry**: revlog schema gives button (Again/Hard/Good/Easy),
  answer time (ms, capped 60s), interval, and FSRS
  difficulty/stability via `card.memory_state`. The add-on exports
  incrementally (`revlog.id > last_seen` joined to `notes.guid`) — note
  GUID is the stable join key between server-side items and review
  outcomes. Avoid bulk `card_stats_data` (400ms/card).
- **Beep-cloze audio needs no JS**: front = server-stitched mp3 with a
  beep over the blank (we already own ffmpeg stitching), back = full
  answer mp3 placed after `{{FrontSide}}` (front audio doesn't
  auto-replay on the back). `{{tts es_ES:cloze-only:Text}}` is a
  zero-cost on-device alternative for the answer side.
- Self-scored multiple-choice with buttons that press ease keys exists
  via the AnkiDroid JS API (0.0.3, async, Android-only) — a progressive
  enhancement only; desktop must degrade gracefully.
- Prior art: no mature "adaptive grammar" tool exists; closest is
  AnkiAIUtils' cron pattern (read revlog → select struggling cards →
  LLM regenerate). Our server-side loop fills a real gap.

## 6. Architecture in idiomatic

New, parallel to the video pipeline (nothing about videos changes):

- DB: `grammar_topics` (lang, topic key, CEFR-ish level, prerequisite
  edges, status), `grammar_items` (one exercise: format, prompt fields,
  answer, explanation, verification status, topic FK, generation batch),
  `grammar_batches` (LLM run metadata, model, prompt hash, cost).
- `apkgs.kind` gains `grammar` (one deck per (lang, topic-cluster) or a
  rolling per-lang deck — decision pending community research on deck
  granularity). Delivery/ack/cleanup: unchanged add-on mechanics.
- Generator: a new worker path (or admin-triggered job) that takes a
  topic + count + difficulty band, calls the LLM, verifies morphology,
  builds apkg via a new genanki model (text-only v1).
- Telemetry (the personalization loop's input): the add-on grows a
  `push_stats` step — after each poll cycle it POSTs per-card revlog
  rows (note GUID, button pressed, time-taken, FSRS
  difficulty/stability) for idiomatic-owned decks to a new
  `/agent/revlog` endpoint. GUIDs encode (lang, topic, item id), so the
  server can aggregate error rates per topic without seeing the whole
  collection.
- Tutor/planner: a scheduled job (cron or manual "plan next block")
  hands the aggregated stats to a strong model (Fable 5 / Opus) with the
  topic graph and returns: diagnosis (weak topics, confusion pairs,
  leech clusters) + the next generation orders. Every diagnosis is
  stored (`grammar_plans`) so the curriculum is inspectable on the
  dashboard.

## 7. Personalization loop

The skill-tracking precedent is Duolingo's half-life regression: treat
morphological FEATURE BUNDLES (e.g. `V;SBJV;PRS;3;SG` × verb class),
not individual cards, as the skills being tracked — FSRS handles item
memory; our layer aggregates over items per skill/topic.

1. Cold start: a diagnostic deck per language (~100 items stratified
   across the taxonomy, weighted toward what the `_errors` decks and
   the idiom-pipeline languages suggest) + one planner run on the
   results.
2. Steady state: weekly planner run (Fable 5 / Opus) receives per-topic
   aggregates and returns diagnosis + generation orders for 2-3 active
   topics per language. Every plan is stored and inspectable on the
   dashboard.
3. Signals (all from revlog via the add-on): again/hard rate per skill,
   answer latency AND its coefficient of variation (the automatization
   signal — falling CV + falling RT = genuinely automatized, not just
   memorized), leech flags, FSRS difficulty/stability distributions,
   confusion matrices on F2 contrast cards.
4. Retirement: Serfaty & Serrano's empirical mastery criterion — an
   item retires after two error-free sessions; a TOPIC goes to
   maintenance when its skill aggregate stabilizes, and the planner goes
   deeper (rarer verbs, subtler triggers) instead of wider.
5. LLM boundary (per the GEC literature): the planner interprets
   aggregated statistics and writes the next orders; it never diagnoses
   from raw answers, and generated items always pass the deterministic
   verifier.

## 8. Roadmap — WAVE PLAN (agreed with user 2026-07-29; CURRENT)

STATUS AT LAST UPDATE (2026-07-31): Waves 1-4 and 6 shipped. Five decks
live (es 222 / de 50 / fr 83 / it 84 / pt 82 cards, 42 units), all with
ElevenLabs back audio, studied in the SYLLABUS Anki profile. Wave 6
added per-cluster subdecks, the grammar_units curriculum table, and the
dashboard /grammar section (see commission brief). Pipeline:
`idiomatic/grammar/` + `/admin/grammar-*` endpoints. Resume from the
wave below that isn't checked off (Wave 5 is next). RESOLVED FINDING (Wave 1 → 2): the es_cmd_tu 15/24
rejection rate was NOT an LLM weakness — every reject was the OLD
substring leak-check false-flagging short tú imperatives against their
own infinitive hint (ten⊂tener, pon⊂poner, sal⊂salir…) and against
ordinary words (da⊂datos). The LLM's forms were morphologically
correct. Fixed by the word-boundary leak check (Wave 2); unit
regenerated after the fix. Lesson recorded: when one unit's rejection
rate is an outlier, read `/admin/grammar-rejects` BEFORE concluding the
model is weak — the verifier can be the bug.

KNOWN LIMITATION of blind-fill verification: solvers currently run on
the SAME model family as the generator (Gemini Flash), so correlated
errors can pass unanimously. Acceptable for v1 (rejection rate on
closed-class units: 1/72); upgrade path = one solver vote from a
different provider (codex/OpenAI) when wiring cross-provider calls is
worth it.

The build order falls out of ONE question: how is each answer type
VERIFIED? Verification tiers:

- **Tier A — table lookup** (existing): verb forms vs morphology DB
  (Jehle for es; kaikki/verbecc for others), German noun gender +
  article/adjective declension, preposition case-government (de).
- **Tier B — blind-fill agreement** (to build in Wave 2): for
  closed-class answers with no lookup table (clitics, por/para,
  prepositions, ser/estar). K independent solver calls get the sentence
  with the blank and NO answer; unanimous convergence required, else
  reject. Verifies correctness AND uniqueness (the #1 cloze failure
  mode) in one mechanism. Plus hard-coded rules where they exist
  (le+lo→se lo). Retrofit onto verb decks too — pennies per batch.

Waves:

- [x] **Wave 1 — Spanish depth, morphology-only** (SHIPPED 2026-07-29,
  batch 20260729-0323): commands tú/usted/ustedes affirmative+negative,
  complex/past conditionals. 57 accepted / 15 rejected (all rejects in
  es_cmd_tu — see FINDING above).
- [x] **Wave 2 — blind-fill verifier + Spanish closed-class units**
  (SHIPPED 2026-07-29, batch 20260729-0346): K=3 blind-fill agreement
  in `generate.verify_blind`; units es_clitics_dir/ind/selo, es_por_para,
  es_verb_prep (60-regime bank by codex, review-validated, in
  grammar/data/es_verb_prep.json). 59/60 accepted. Deck at 210 cards /
  18 units, all with audio (apkg 897). Register drills shipped in Wave 1
  (es_cmd_tu/usted/neg).
- [x] **Wave 3 — German first new language** (SHIPPED 2026-07-29,
  batches 20260729-0412/-0417): de_gender, de_prep_fest,
  de_prep_wechsel — deck "Idiomatic Grammar DE", 50 cards with audio
  (apkg 901). Noun-gender table = gambolputty/german-nouns (82,944
  unambiguous non-weak nouns, cross-gender homographs dropped); prep
  bank by codex (37 preps, validated); article matrix hardcoded.
  LESSON (rhymes with es_cmd_tu): first run rejected 10 common nouns
  because the table was frequency-filtered on SUBTITLE data + a careless
  stopword list ('macht' killed Macht) — verification tables should be
  maximal, filters minimal; second run 24/24. STILL OPEN from Wave 3
  scope: adjective endings unit; German verb core.
- [x] **Wave 4 — pt/fr/it verb cores** (SHIPPED 2026-07-29): decks
  FR 73 / IT 77 / PT 70 cards, 7 units each, all with audio. Verbecc
  tables (150 verbs/lang); two verifier refinements post-launch:
  agreement-tolerant comparison for fr/it compounds (masc-default
  table vs legitimate feminine agreement) and the pt-'eu'-pronoun /
  fr-'eu'-participle strip collision fix. Clone of es pilot; work =
  morphology DB ingestion per lang (kaikki or verbecc). PT variety =
  **BRAZILIAN Portuguese** (user directive 2026-07-29 — the earlier EP
  framing was an unchecked assumption of mine, never the user's ask;
  você/vocês-based drills, tu/vós hard-rejected by the verifier).
- [ ] **Wave 5 — telemetry + planner** (unchanged from §7): add-on
  pushes revlog keyed by note GUID; weekly strong-model planner picks
  the 2-3 active units per language.
- [x] **Wave 6 — dashboard grammar section + deck taxonomy**
  (SHIPPED 2026-07-31, brief:
  docs/commissions/GRAMMAR_FRONTEND_COMMISSION.md): subdecks per topic
  cluster (final cluster map in the brief; apkg builds one genanki deck
  per cluster, deck ids hashed from full names, GUIDs untouched),
  grammar_units DB table (code-owned cols re-seeded on boot; per-unit
  target_size/status/notes mutable; planned units = what's-next),
  /grammar + /grammar/unit/:key dashboard pages with
  Top-up/Rebuild/retire controls wrapping /admin/grammar-*, add-on
  one-shot "Reorganize grammar decks" (col.set_deck by unit tag via
  agent-authed /admin/grammar-deckmap; FSRS preset stays on the PARENT
  deck only — subdecks inherit).
- [ ] **Wave 7 (PROPOSED 2026-07-31)** — leverage the personal error
  mine: five per-language profiles in docs/research/error-profiles/
  (10,314 spreadsheet rows + 3,502 Teachee notes analyzed); synthesis
  + phased plan in docs/commissions/ERROR_PROFILE_PROPOSAL.md
  (target retuning, personal_errors registry + F3 error-correction
  format, evidence-based new units, F4 interference deck, error-aware
  generation, grammar explainers). Awaiting user decisions (§4 of the
  proposal).
- [ ] Later: beep-cloze audio fronts (error-correction format is now
  Wave 7's F3, seeded from the real error mine instead of guesses).

Volume rule (lesson of the 2023 EXCERCISES failure): generation is
on-demand per unit, 2-3 active units per language at any time, mastered
units retire. Never bulk-dump a full syllabus into the deck.

## 8b. Division of labor — codex for heavy lifting (user directive, 2026-07-29)

`codex` CLI is installed and authenticated on the user's machine
(`codex exec "<prompt>"` runs headless; user has ample credits).
STANDING RULE for this whole project: bulk, low-intelligence work goes
to codex, NOT to the primary (Fable/Opus) session — sentence/example
generation at volume, drafting per-unit item batches, scraping/
formatting taxonomies, data-file wrangling, boilerplate test writing.
The primary model does: architecture, verification design, curriculum
decisions, code review of codex output, anything user-facing. Server-
side runtime generation stays on Gemini Flash (already cheap); codex is
for dev-time/offline workloads. Verify codex-generated items through
the same deterministic/blind-fill verifiers as everything else.

## 9. Cost guardrails

- Text-only generation: ~1-2k tokens per item on Gemini Flash →
  well under €1 per thousand cards; even 5 langs × 10/day is noise.
- Weekly planner: one strong-model call (~50-100k tokens in, few k
  out) → cents to ~€1/week.
- One-time data ingestion (kaikki/UniMorph/Tatoeba parsing) runs
  locally/cron, no API spend.
- Audio phase: ElevenLabs at ~$0.05/1k chars → roughly $0.01-0.02 per
  card-with-audio, inside the existing Pro-plan credits. The July-2026
  TTS lesson stands: never route bulk TTS through Gemini preview.

## 10. Commissioned deep-dives (ready-to-paste codex prompts)

Our research could not crawl Reddit (blocked) and left two open gaps.
Paste these into codex (free credits) as separate sessions; drop the
outputs into `docs/research/` and I'll fold them in:

1. **Reddit sweep** — "Search Reddit (r/Anki, r/languagelearning,
   r/Spanish, r/French, r/German, r/italianlearning, r/Portuguese) for
   threads on practicing grammar/conjugation with Anki. I want: which
   formats people stuck with for >6 months, why people quit
   conjugation decks, opinions on the 'Ultimate Spanish/French/Italian
   Conjugation' (KOFI) decks, experiences generating grammar cards
   with LLMs, and cloze vs basic debates. Quote posts with links.
   Raw findings, organized, no product advice."
2. **Advanced-learner error inventories** — "For each of Spanish,
   Brazilian Portuguese, French, Italian, German: compile the 50-80
   most persistent grammar errors of ADVANCED (B2-C1) adult learners
   whose other languages include English and several Romance languages
   — drawing on learner-corpus research (e.g. CEDEL2, Lang-8 studies,
   MERLIN for German), teacher write-ups, and exam-rater reports.
   For each error: wrong form → right form, one-line why, and which
   cross-language interference causes it. Machine-readable markdown
   table."
3. **Italian grammar taxonomy** — "Build a CEFR-tagged (A2-C1) grammar
   topic tree for Italian in machine-readable YAML: topic, subtopics,
   level, prerequisite topics, 2 example sentences each. Base it on
   the CELI/CILS exam syllabi, Kwiziq-style topic lists for sibling
   languages, and any published Profilo della lingua italiana
   summaries. Mark uncertain level assignments."

## 11. Research annex

Full raw findings with citations:

- [Community wisdom on Anki grammar practice](research/anki-grammar-community.md)
- [Data sources & licenses](research/grammar-data-sources.md)
- [SLA pedagogy evidence](research/sla-pedagogy.md)
- [AnkiDroid/genanki technical constraints](research/ankidroid-tech.md)
