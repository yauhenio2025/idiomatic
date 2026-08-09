# Grammar Course system — commission (owner vision, 2026-08-09)

> Owner dictation, captured verbatim in intent: grammar as SEQUENCED
> AUDIO LESSONS with interleaved exercises and telemetry-driven
> remediation — "gradual exposure, where we listen to grammar and do
> exercises as we go along," then exercises dominate and lessons only
> resurface "unless our answer pattern suggests that we need to
> relisten... and maybe we'll commission a new lesson." Book-grounded,
> not LLM-freestyle. This is the next major initiative AFTER the Hub
> cutover lands; the Mac book-structuring lane starts immediately.

## The design in one paragraph

A grammar UNIT (e.g. "Italian plurals") = ~10 two-sided pure-lesson
cards ("twenty slides"): audio explanation in English with TL examples,
SVG diagrams where they earn their place — the podcast_lesson format
(`Ep 7 · 1 · it` cards) is the proven embryo, including its house SVG
style. NO exercises on lesson cards. Exercise cards live WITH the unit
(same deck or `1 Lesson`/`2 Exercises` subdecks — open decision) but as
a distinct card population. First exposure is SEQUENCED: lesson slides
and exercise blocks interleaved (2 slides → ~20 exercises → 2 slides →
…) — we control this exactly because we mint the apkg: new-card due
POSITIONS encode the interleave; no add-on changes needed. After the
unit is consumed, exercises circulate on normal scheduling and lessons
naturally space out — UNLESS the telemetry lane says comprehension is
missing.

## The telemetry loop (the new part)

Nightly/daily, from synced revlogs (the proven headless AnkiWeb pull —
anki-study-data POC): per unit, per lesson-slide span, compute exercise
failure clustering. Escalation ladder:
1. Healthy → nothing.
2. Failure cluster on a unit → RESURFACE its lesson cards (reschedule/
   unsuspend via delivery, never by editing revlog).
3. Cluster persists after re-listen → COMMISSION new content via LLM:
   a remedial lesson variant (different angle) and/or more exercises,
   through the normal generate→verify→build pipeline.
All decisions surface on a dashboard panel (read + sanctioned-mutation
like /grammar): unit health board, resurface/commission queue, owner
override. Differentiating populations: card-type/tags are the primary
key (flags are user-mutable and stay owner-owned; if used, flag 7/8 as
a VISUAL convenience only, never as the data key).

## Book-grounded authoring (the anti-hallucination spine)

Existing books are the templates. First corpus: **Hammer's German
Grammar and Usage** (Durrell, 7th ed., EPUB) + its official workbook
**Practising German Grammar** (Kaiser & Kohl, PDF, native text layer —
verified 2026-08-09) on the Mac (~/Downloads). A Mac codex lane
structures them: exercises matched to their answer key, full solution
sentences reconstructed (card back = full sentence with the inserted
answer highlighted, not the bare key), Hammer §-references preserved,
ambiguity flagged never guessed. Output feeds this system as verified
exercise seed data + lesson outlines per Hammer chapter. Other
languages follow the same pattern with their reference grammars.

## Design decisions — TAKEN by coordinator under owner delegation
(2026-08-09: "a lot of the decisions will be obvious and you can take
them too"; anything genuinely needing the owner ships as an interactive
console page — multiple choice + comment boxes — NEVER an MD to read.)

1. Layout: `1 Lesson` / `2 Exercises` subdecks per unit (consistent
   with the estate tree's numbered-lane doctrine; flags stay visual-only).
2. Interleave default: 2 lesson slides → ~20 exercises, encoded in
   new-card due positions.
3. Escalation thresholds: start at the Hub's Balanced policy values.
4. Provenance: book-derived items tagged as ground truth, LLM items
   tagged generated; book beats LLM on conflict.
5. No interactive card elements in v1 (owner: "maybe we don't need it").

OWNER-RATIFIED PRINCIPLE (2026-08-09, binds all formats): exercises are
atomic individually-graded cards, never embedded inside lesson cards —
measurement granularity = card granularity ("once we flip the card,
we're not measuring anything" otherwise). Existing podcast decks that
mix exercise moments into lesson audio stay as-is for listening value,
but their measurable successors follow this split.

The Grammar Course serves sessions THROUGH the Personal Study DJ
(PERSONAL_DJ_COMMISSION.md) — the umbrella orchestrator.

## (superseded) Open design decisions

1. Same-deck flags vs `1 Lesson`/`2 Exercises` subdecks per unit.
2. Interleave granularity default (2 slides / ~20 exercises was the
   dictated sketch).
3. Escalation thresholds (reuse the Hub's Balanced weakness style as
   the starting point).
4. Where book-derived exercises meet LLM-generated ones (provenance
   tags; book items are ground truth).
5. Whether interactive elements on lesson cards are wanted at all
   (owner: "maybe we don't need it") — default NO for v1.

## Relationship to existing systems

- podcast_lessons: becomes the lesson-card engine (music-bed overlap
  glitch noted by owner — fix during adoption, not a blocker).
- grammar drills / exercises2 / tenses: existing exercise engines keep
  their lanes; new units reference, not duplicate.
- Hub telemetry (Flag-1, weakness policies): shared analysis machinery.
- Local TTS: all lesson/exercise audio through the qwen-local lane.

## Workload structure

- Mac codex: book structuring (prompt in
  GRAMMAR_BOOKS_MAC_CODEX_PROMPT.md beside this file) — runs now.
- Fable design session: full design doc + pilot unit (ONE unit,
  pilot-first: Italian plurals or German cases) — after Hub cutover.
- Coordinator: sequencing, review, owner gates.
