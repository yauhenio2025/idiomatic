# LingQ Dormant Value — Product Proposal

> Creative-design deliverable, 2026-08-10. Numbers below are MEASURED
> directly from `lingq_terms` (read-only psql sampling this session),
> not estimates, except where marked. The parallel codex inventory job
> (`inventory.json` / `overlap.json` / `REPORT.md`) had not landed at
> drafting time — only `data/lingq_terms.json` and the run log existed;
> reconcile numbers when it does.

## 1. Thesis — where the dormant value actually is

The value is NOT where the owner thinks it is. The "knowledge levels"
are almost empty — 49,256 of 51,826 terms (95%) sit at status 0 "New";
only ~2,570 ever advanced (de 994 at status ≥2, everything else in the
low hundreds) — so this is not a graded lexicon, it is an **encounter
log**: eleven years of "words and expressions I met in real texts I
chose to read, with the exact sentence I met them in." That reframes
the asset into four exploitable layers, in descending order of value:
(1) the **fragments as episodic anchors** — 97.6% of terms carry the
original sentence, 36% (18,910) tagged with Kindle book provenance
down to the month (`kindle_mar_2019_*`), and ~18k arrive PRE-CLOZED by
LingQ's own `[[[ w:::::::n ]]]` markup, which preserves the inflected
surface form's first and last letters — a free, mechanically verifiable
cloze corpus; (2) the **5,455 multi-word expressions in the five active
languages** (de 1,593 / fr 1,510 / it 905 / pt 775 / es 672), attested
in native text by construction, essentially none of which have ever
been drilled — overlap with the idiom pipeline's `expressions` table is
~101 terms total, under 0.3%; (3) the **union lexicon as a generation
constraint** — the one thing that makes owner-personalized sentence
generation mechanically checkable rather than vibes; (4) the owner's
own **hints as sense disambiguators** (which sense of a polysemous word
they actually met). The levels themselves, and the srs_due_date column
(present on all rows, auto-set, meaningless), are dead weight.

## 2. Data quality — what sampling actually showed

| lang | terms | w/ fragment | multiword | clean full sentences* | clozed `[[[…]]]` |
|------|------:|------:|------:|------:|------:|
| de | 16,302 | 16,187 | 1,593 | 1,501 | 9,796 |
| sv | 6,381 | 5,670 | 1,582 | 163 | 167 |
| fr | 6,203 | 6,174 | 1,510 | 646 | 2,596 |
| nl | 5,514 | 5,375 | 925 | 111 | 571 |
| pt | 4,329 | 4,290 | 775 | 246 | 2,243 |
| es | 4,199 | 4,193 | 672 | 295 | 2,522 |
| zh | 3,168 | 2,952 | 314 | 1 | 0 |
| it | 3,032 | 3,024 | 905 | 373 | 146 |
| da | 1,597 | 1,595 | 230 | 116 | 0 |
| no | 1,101 | 1,100 | 197 | 63 | 0 |

\* strict filter: >40 chars, no leading/trailing `...`, no cloze markup.
The loose usable set is much larger because clozed fragments are
restorable (see below) and mid-truncated ones are often still complete
clauses.

Surprises that shape the concepts:

- **Levels are a mirage.** 95% status 0. Any concept premised on "drill
  by knowledge level" dies on contact with the data. The small status≥2
  stratum (de 994, fr 327, es 138, it 74, pt 195) is useful only as a
  priority seed.
- **The cloze markup is a gift, not contamination.** `[[[ w:::::::n ]]]`
  marks the term's slot in the sentence and preserves first + last
  letter of the *inflected surface form* (term "weise" → slot `w…n` →
  surface "weisen"). Restoration is LLM-cheap and MECHANICALLY
  verifiable (must match the letters, must be a form of the stored
  term). ~17.5k fragments across active langs carry it; de alone 9,796.
- **Terms are inflected surface forms, not lemmas** ("rememora",
  "maßgeblicher", "heimgesucht"). Lexicon-constraint use requires a
  one-time lemmatization pass; dedup by lemma will shrink effective
  counts ~10-20% (estimate).
- **Multiword quality varies sharply by language.** fr samples were
  genuinely idiomatic ("se creuser la tête", "tous azimuts"); it/pt
  samples were heavy on arbitrary reading chunks ("l'ambito in cui si
  sentiva", "se apressarão sem dúvida em") and even typos ("svianare").
  A triage classifier is non-optional and per-lang keep rates will
  differ a lot (fr maybe 60%, pt maybe 30% — estimates).
- **Kindle provenance is displayable.** 18,910 terms carry
  `kindle_<month>_<year>_<loc>` tags — "you met this in a book, March
  2019" is a legitimate card element and a memory cue in itself.
- **Hints are the owner's own glosses** but ~700 terms have none, some
  are dictionary-noisy ("n. feat, exploit, deed; performance"), and a
  few are wrong-register ("concita" → "enjoy"). Glosses need a cheap
  verification pass before they front a card.
- **The `notes` column is empty** (1 row in 51,826). No hidden essay
  corpus there.
- **sv is the #2 lexicon** (6,381 terms, 1,582 multiword — more
  multiword than fr!). Dormant by directive, but it is the single
  richest future-activation asset; every pipeline below should be
  lang-parameterized so sv/nl/da/no/zh activate by flipping a list.

## 3. Product concepts

Killed before ranking: *sense-duel recognition cards* (recognition-only,
weak production value), *level-driven scheduling import* (levels are
empty — see above), *personal i+1 graded reader as cards* (wall-of-text
violation; LingQ itself is already the reading surface). What remains I
would defend.

---

### C1 — SECOND ENCOUNTER (expression reactivation) ★ winner

**Insight.** 5,455 attested multi-word expressions the owner personally
met, remembers meeting, and has never once produced. The original
fragment is a retrieval cue no generic deck can have: it reactivates
the episodic memory of the first encounter and attaches production
practice to it. This is the "own unique brand of flashcards" — no other
learner could be sent this deck.

**Card (atomic — one expression, production recall).**
- FRONT: owner's EN gloss (verified) + the original fragment with the
  expression slotted out (`…évite d'avoir à ______.`) + provenance
  chip ("Kindle · Mar 2019" or "news").
- BACK: the expression (surface + citation form), the fragment
  restored, ONE fresh example sentence woven from the owner's own
  lexicon (see C2 — the Weaver is this card's example engine), Qwen
  audio of expression + both sentences.

**Lane.** `anki_root(lang)::1 Expressions::3 Second Encounter` (new
subdeck; `1 Expressions::2 Expression Focus` stays reserved for the Hub).

**Data.** `lingq_terms` multiword rows with usable fragment (clean or
cloze-restorable) + hint; triage classifier verdict = expression.

**Generation + verification.**
1. Triage (codex lane, bulk): lexicalized-expression vs reading-chunk
   vs junk/typo. Owner calibrates the threshold on 12 samples in the
   console (§6).
2. Fragment restore: mechanical gate (cloze letters + term match).
3. Gloss check: blind Gemini translation of the expression compared to
   the owner's hint; mismatch → console flag, never auto-ship.
4. Fresh example: lexicon-constraint mechanical gate (every content
   word ∈ owner lemma set ∪ top-2k frequency) + blind back-translation
   agreement. Expression itself needs no attestation check — it IS the
   attestation.
5. Hostile audit of the full pilot before publish (exercises2 practice).

**Cost.** ~3 Gemini calls/card (≪¢1); TTS local Qwen = $0; no images
in base version.

**DJ impact.** Expressions population prior 8 s/rep; a new card costs
~20 s day one (×2.5 factor). 8/day ≈ 3 min/day inside the language's
25-min budget — displaces part of the exercises2 waves 4-6 new-card
inflow, which is the right trade: this content is personal, that
content is generic.

**Risk.** Triage keep-rate uncertainty (it/pt chunk-heavy); truncated
fragments producing ugly fronts (gated); the episodic-anchor hypothesis
itself is untested — measured explicitly in the pilot (§5).

---

### C2 — OWN-WORDS WEAVER (known-vocab-constrained production)

**Insight.** The owner's explicit wish: "generate sentences with
expressions that I know." The union lexicon (lemmatized) turns
generation from open-ended (unverifiable style risk) into a
CONSTRAINED problem with a mechanical acceptance test — every content
word must be a word the owner has met. Sentences read as eerily
familiar because every piece is theirs.

**Card (atomic — one target term per card).**
- FRONT: EN sentence (Qwen EN audio, exercises2-Production style).
- BACK: TL sentence containing the target term + 1-2 co-woven frontier
  words as supporting cast + audio. Target term highlighted; the
  supporting words are comprehension support, never the graded target.

**Lane.** `anki_root(lang)::4 Exercises::Own Words`.

**Data.** Lemmatized lexicon per lang (one-time codex pass over
`lingq_terms.term`); target list = status≥2 stratum first (de 994,
fr 327…), then high-value status-0 singles.

**Generation + verification.** Gemini generates EN+TL pair under the
lexicon constraint; MECHANICAL lexicon gate (script, not LLM); blind
back-translation agreement for meaning; word-boundary leak check
(grammar Wave-2 lesson). This is the strongest verification story of
any generative concept in the estate because the acceptance test is a
set-membership check.

**Cost.** ~2-3 Gemini calls/card; TTS $0.

**DJ impact.** Exercises prior 20 s/rep → 50 s/new-card day one; 5/day
≈ 4 min. Must stay capped — this concept can generate infinitely, so
the reservoir is owner-throttled per week, not open-ended.

**Risk.** Pedagogically fuzzier than C1 (what exactly does one card
teach? — answer: production of the single target term; the discipline
must be enforced or it degrades into "nice sentences"); constraint may
force stilted sentences in small lexicons (pt/es) — mitigated by the
top-2k frequency union.

---

### C3 — READING RELICS (pre-clozed episodic recall)

**Insight.** ~17.5k fragments are ALREADY cloze cards — LingQ's SRS
markup did the authoring. Cheapest possible conversion of reading
history into recall practice: near-zero generation, near-zero risk.

**Card (atomic — one cloze).**
- FRONT: fragment with LingQ's own slot (`Die Ministerin ist
  [ü…t]: Ohne klare Regeln…`) + first/last-letter scaffold + provenance
  chip.
- BACK: surface form + lemma + owner's gloss + Qwen audio of the full
  restored sentence.

**Lane.** `anki_root(lang)::4 Exercises::Reading Relics`.

**Data.** Clozed-fragment rows, filtered to complete-clause fragments;
priority order = status≥2 first, then Kindle-book terms.

**Generation + verification.** Restoration mechanically verified
(letters + term); NO generated target-language content at all beyond
TTS of an attested sentence. The only concept with a zero-LLM-risk
core.

**Cost.** ~$0 text; TTS $0. The cheapest concept per card by an order
of magnitude.

**DJ impact.** The danger is volume: 17.5k candidates would eat every
budget. Ship as a CAPPED drip (e.g. 5/day/lang from the priority
order), owner-throttled. ~10 s/rep prior → ~2 min/day.

**Risk.** Single words, receptive-leaning — lower ceiling than C1/C2;
many fragments are news ephemera the owner won't remember (the
provenance chip and the status/Kindle priority order are the filter);
truncated fragments must be gated or restored.

---

### C4 — MORPH SLOT (inflection restore from own sentences)

**Insight.** Terms are inflected surface forms and the cloze preserves
the slot: given lemma + sentence context, produce the correct form
("weise" + `w…n` slot → "weisen"). That is a grammar-morphology drill
whose answers come with built-in mechanical verification, harvested
from the owner's own reading instead of synthetic paradigms — a direct
personal complement to the grammar decks and `grammar/morphology.py`.

**Card (atomic — one form).** FRONT: fragment with slot + lemma prompt
("weisen — richtige Form?"). BACK: surface form + why (person/tense/
case one-liner) + audio.

**Lane.** `anki_root(lang)::4 Exercises::Morph Slot` (kept out of
`2 Grammar`, whose subdecks are curriculum-cluster-owned).

**Generation + verification.** Restoration gate (letters + lemma,
mechanical) + Tier-A table lookup for the form where morphology tables
exist; the "why" line is Gemini, gated by the same lookup.

**Cost.** ~1 Gemini call/card; TTS $0.

**DJ impact.** Tenses-like, fast (7-10 s/rep). Tiny capped drip; only
worth minutes in de (9,796 clozed fragments), where morphology pain is
real.

**Risk.** Overlaps conceptually with C3 (same raw rows); ship as C3's
production-mode sibling only if C3 lands, not independently. Ranked,
but explicitly second-wave.

---

### C5 — POLYGLOT MIRROR (cross-language retrieval pairs) — the one nobody asked for

**Insight.** This is a TEN-language encounter log from one brain. Match
terms across languages by gloss/lemma equivalence and drill sideways
retrieval: "you know this in German — say it in French." Interference
is the owner's documented enemy (IT-deck-was-French, false-friends
history); sideways retrieval is the drill that builds the partition,
and no off-the-shelf product can build it because it needs the owner's
own parallel lexicons.

**Card (atomic — one pair, one direction).** FRONT: term in lang A +
its fragment snippet + "→ FR?". BACK: the French term THEY met + its
own fragment + audio. One direction per card; reverse is a separate
card.

**Lane.** Under the RETRIEVED language's root:
`anki_root('fr')::4 Exercises::Polyglot Mirror`.

**Data.** Gloss-text matching + lemma-translation equivalence across
`lingq_terms` langs; needs a codex matching pass with conservative
precision (false pairs are toxic here).

**Generation + verification.** No generated TL content — both sides are
attested owner terms; the RISK is the pairing itself → verify by
bidirectional blind translation agreement (A→EN→B must land on B's
gloss) and ship only high-confidence pairs. False-friend pairs get
flagged, not dropped — they are the most valuable cards, with an
explicit warning line (feeds the F7 FALSE_FRIENDS wave).

**Cost.** Matching is a one-time codex batch; per-card ~$0 + TTS $0.

**DJ impact.** Small by construction (high-precision matching will
yield maybe 300-800 pairs across the five active langs — estimate).
2-3/day/lang ≈ 1 min.

**Risk.** Pair precision; pedagogical novelty (no precedent in the
estate — exactly why it must be piloted at 20 cards, not 200). Extends
most naturally to sv/nl/da/no later — the mirror gets more valuable
with every activated language.

---

### C6 — FRONTIER PODCAST (weekly own-words narrative)

**Insight.** Weave 15-20 frontier terms per language into a 4-5 minute
weekly narrative episode — re-encounter in fresh context, the closest
thing to "more reading" without competing for card minutes. Rides the
existing `podcast_lesson` machinery and the `idiomatic-podcast` DJ
population (90 s/rep listens).

**Card.** One episode = one lesson card (existing podcast_lesson
shape); terms listed on the back with glosses. Atomicity holds at the
lesson-card level as already accepted for podcasts.

**Lane.** Existing podcast_lesson delivery lane; builder =
`grammar/podcasts.py` + `podcast_cards.py` pattern with a lexicon-
constrained script generator.

**Verification.** Script passes the C2 lexicon gate + blind
back-translation of each embedded term's sentence; podcast v1
postmortem requirements apply (memory: pilot-first, one episode).

**Cost.** ~1 long Gemini call + local TTS $0.

**DJ impact.** 5 min/week/lang, listening-shaped — the least
displacing concept on the sheet.

**Risk.** Podcast v1 history demands the postmortem checklist be
satisfied; narrative quality with constrained lexicon is harder than
card-length text. Pilot = ONE French episode.

---

### C7 — PICTURE THIS IDIOM (image-anchored expressions)

**Insight.** The owner explicitly floated "decks with images." Concrete
figurative idioms ("se creuser la tête" — digging into one's head) are
the one card population where an image is a cue, not decoration.
Asset Factory cloud lane exists and is priced.

**Card (atomic).** FRONT: image rendering the idiom's literal scene +
EN gloss. BACK: expression + fragment + audio. Strictly a VARIANT of
C1 for the ~top-10% most imageable expressions, same lane.

**Generation + verification.** Image via `genmedia.py`
qwen-image-3.0-pro at $0.037/image; imageability triage by LLM, image
QA via the Q-Judger loop (currently DISARMED pending owner spot-review
— a real dependency, not hand-waving). Text side inherits C1's gates.

**Cost.** $0.037/image → a 60-card image pilot ≈ $2.20 + retries.

**DJ impact.** None beyond C1 (same cards, richer front).

**Risk.** Image QA loop disarmed; images can mislead (wrong literal
scene teaches wrong mental model) — Q-Judger + owner spot-check
mandatory. Do NOT lead with this; offer as C1's v2 toggle.

---

## 4. Scoring and winner

Scale 1-5; build cost inverted (5 = cheapest). Weights equal; the
tie-breakers are verification strength and pilot-first fit.

| Concept | Pedagogical value | Owner-fit | Build cost | Risk (5=low) | Σ |
|---|---:|---:|---:|---:|---:|
| **C1 Second Encounter** | 5 | 5 | 4 | 4 | **18** |
| C2 Own-Words Weaver | 4 | 5 | 4 | 3 | 16 |
| C3 Reading Relics | 3 | 4 | 5 | 4 | 16 |
| C5 Polyglot Mirror | 4 | 3 | 3 | 3 | 13 |
| C6 Frontier Podcast | 3 | 3 | 4 | 3 | 13 |
| C4 Morph Slot | 3 | 3 | 4 | 3 | 13 |
| C7 Picture This Idiom | 3 | 4 | 3 | 2 | 12 |

**Winner: C1 Second Encounter, with C2 embedded as its example
engine.** It exploits the two strongest asset layers at once (attested
never-drilled expressions + episodic fragments), it is the most
"unique brand" of the sheet, its content is owner-sourced so the
verification burden concentrates on small generated surfaces, and the
pilot doubles as a live test of BOTH top concepts (the woven back-side
example is C2's mechanism, verdictable separately in the console).
C3 ships second as a capped drip if the episodic-anchor hypothesis
survives the pilot; C5 is the dark horse to pilot at 20 cards next.

## 5. The pilot — FR Second Encounter, 60 cards

Smallest honest version: one language, one week of study, both
hypotheses instrumented.

**Why fr:** best-quality multiword sample (genuinely idiomatic), 1,510
candidates, 2,596 restorable clozed fragments, mid-size lexicon — and
de's 9,796-cloze mass stays in reserve for the batch phase.

**Scope.** 60 cards ≈ 8-9 new/day for 7 days ≈ 3 min/day of the fr
25-min DJ budget (8 s/rep expressions prior × 2.5 new-card factor).
Displaces a slice of exercises2 wave-4/5 new-card inflow for one week.

**Selection.** From fr multiword rows: triage keep verdicts, ranked by
(status DESC, fragment usability, Kindle/news provenance mix ~50/50,
gloss present). Target pool after triage ~750 (est.); pilot takes the
top 60.

**Build plan (real modules).**
1. `idiomatic/grammar/lingq_revival.py` — new builder module, reusing
   exercises2's genanki model/deck-id pattern, the local-TTS audio lane
   (`local_tts.py` chain: qwen-local → ElevenLabs → Gemini), and
   `anki_tree.anki_root()` for the deck path
   `FR French::1 Expressions::3 Second Encounter`.
2. Tables: `lingq_revival_items` (term_id FK, triage verdict, restored
   fragment, verified gloss, woven example, audit state, owner verdict)
   via `db/schema.sql` idempotent boot migration.
3. Endpoints (api.py, admin-authed, grammar-endpoint pattern):
   `POST /admin/lingq-revival-triage?lang=fr` (bulk classify + gates,
   background, status poll), `POST /admin/lingq-revival-build?lang=fr`
   (publish rolling apkg, `apkgs.kind='lingq_revival'` — one per lang
   via the existing partial-unique index),
   `GET /admin/lingq-revival-status`.
4. Bulk labor (triage classification, lemmatization pass, hostile
   audit) → codex lane per the standing delegation directive; premium
   session designs prompts and audits samples.
5. Delivery: standard `/apkgs/pending` → add-on auto-import into the
   syllabus profile. No add-on changes needed.

**Verification design (per card, all gates must pass).**
- Expression: attested by construction (source fragment stored).
- Fragment restore: mechanical — cloze first/last letters + term match;
  unrestorable → card dropped.
- Gloss: blind Gemini translation vs owner hint; disagreement → console
  flag queue, human-resolved, never auto-shipped.
- Woven example: mechanical lexicon gate (content lemmas ∈ owner
  lexicon ∪ top-2k frequency, word-boundary matching per the Wave-2
  leak-check lesson) + blind back-translation agreement.
- Whole pilot: hostile audit pass (codex, exercises2 audit brief
  pattern) before `-build` is called.

**Success criteria (owner verdicts, console §6 + one week of study).**
- Pre-ship sample review: ≥80% Keep on 20 sampled cards.
- Episodic hypothesis: on the same 20, owner taps "I remember the
  source" — ≥40% validates the anchor premise; <20% falsifies it and
  C3 dies with it (that is the honest kill-switch).
- Weaver hypothesis: back-side examples verdicted separately —
  "natural" ≥70%, zero lexicon-gate escapes found by the owner.
- Post-week telemetry (DJ observations): again-rate <30%, secs/rep
  ≤12 s, fr budget not overflowed.
- Final tap: Batch it (weekly drip ×N/lang) / Adjust / Kill.

## 6. Owner decision console — `/lingq` (decision surface, not docs)

Dashboard page in the allowed-mutation family (grammar / rescue / cast
/ dj / triage precedent). Verdicts land in `lingq_verdicts` via
`POST /admin/lingq-verdict` (dj_triage pattern: page records decisions;
builds apply them; reseeds never touch verdict columns). Three zones,
phone-friendly targets:

1. **Concept bake-off** (one-time): C1, C2, C3 each rendered as 8 REAL
   cards from live `lingq_terms` (front/back flip, playable Qwen
   audio, provenance chips). Per-concept verdict bar: `Ship pilot` /
   `Not this` / `Later` + optional note. C5/C6/C7 appear as one-line
   teasers with a `Show me 8` tap so the page stays scannable.
2. **Triage calibration** (per lang): 12 multiword samples with the
   classifier's verdict (expression / chunk / junk); owner taps
   agree/override. Sets the keep threshold before any bulk codex run —
   the cheap insurance against the it/pt chunk problem.
3. **Pilot review** (after build, before/while studying): the 60 cards
   as a list — per card `Keep` / `Fix gloss` / `Junk source` / `Kill`,
   plus the two hypothesis taps (`Remembered the source?` yes/no,
   example `Natural?` yes/no). Sticky bar: keep-rate, remember-rate,
   and the final verdict buttons `Batch weekly` (with a per-lang N
   picker) / `Adjust format` / `Stop here`.

Everything the pilot needs from the owner is a tap on this page;
nothing requires reading a markdown file.

## 7. Dormant languages

sv/nl/da/no/zh stay import-only per directive. Design consequences
honored above: every pipeline is lang-parameterized; sv's 1,582
multiword terms make it the first activation candidate for C1; C5
Polyglot Mirror compounds in value with each activation; zh (avg term
2.6 chars, 1 clean sentence) needs its own card shapes and is out of
scope for all current concepts.
