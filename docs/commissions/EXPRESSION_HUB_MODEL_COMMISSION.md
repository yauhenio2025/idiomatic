# Expression-hub data model — design commission (codex)

> STUDY ONLY. You produce a design document + migration mapping +
> decision list. No code changes, no DB changes, no Anki changes.

## The owner's reframing (this is the brief — internalize it)

The unit of learning is the **trigger expression**, not the sentence.
Sentences are practice surfaces generated FOR an expression. The
current system inverts this in places (sentence-cards with the
expression as a field) and duplicates it in others (four pool decks
derived from the same expression row). Target: an **expression-hub**
architecture where the expression is the key; sentences, images,
audio, and context hang off it; decks/cards are projections of the hub.

Read first: CLAUDE.md (pipeline + DB schema), db/schema.sql
(expressions / expression_idioms / expression_examples / rescue_items /
factory_actors), idiomatic/pipeline/pool.py + apkg.py (current models),
docs/commissions/ILLUSTRATION_PROMPTS_COMMISSION.md (images are being
pregenerated for EVERY example sentence, keyed by example_id — your
design must slot these in), docs/ASSET_FACTORY_STRATEGY.md §5
(telemetry direction), docs/commissions/ANKI_ESTATE_REORG_COMMISSION.md
(the parallel estate study).

## Required behaviors of the target design

1. **Hub note per expression** (per language). Fields hold: expression,
   EN gloss, ONE tight usage line (not the current long explanation),
   judicious extras ONLY when high-value (key synonym, false friend
   across the user's languages), source provenance (video title/URL as
   text), and N example slots (sentence TL + EN + image). Decide N and
   the mechanism for growth (fixed spare slots vs. HTML-list field vs.
   subordinate notes) — argue the trade-offs in Anki's model (notes
   have fixed fields; one note → many cards via templates; adding
   fields to a model at scale is possible but must be planned).
2. **Card projections** from the hub:
   - Fluency cards: one per example sentence (EN front → TL back,
     sentence audio, THE IMAGE for that sentence). These keep the
     current study rhythm — the owner studies sentences.
   - Hub card (replaces the Idioms EN↔target deck): expression front →
     back shows the expression + ALL its example sentences with their
     images stacked vertically (sentence text above each image, comic
     strip feel even though images are independent).
   - The long listen-and-learn Idioms Audio cards: DISCONTINUED
     (generation already being switched off server-side). Their
     valuable content (explanation) gets compressed into the hub's
     one-line usage note during migration.
3. **Expression-level telemetry** (design the schema, not the code):
   per expression per day: reviews, lapses, flag counts, distinct
   sentences seen. Sources: the existing headless AnkiWeb revlog pull
   (rescue autopilot) + card→expression mapping (expression_id must be
   recoverable from every card — specify how: field, tag, or GUID
   scheme).
4. **The flag protocol**: plain Again/Hard on a fluency card = the
   trigger expression is weak. **Flag 1** (native Anki, Ctrl+1) on a
   card = "the difficulty was elsewhere in the sentence". Design:
   - the telemetry split (flagged lapses excluded from expression
     weakness),
   - a diagnosis queue: flagged cards go to an LLM pass that reads the
     sentence, the expression, and the user's known-language profile,
     and infers the likely trouble spot (a collocation, a tense, a
     false friend…), emitting: diagnosis + optionally 1-3 new practice
     sentences targeting THAT — where do these land? (propose: the
     language's exercises tree, tagged by diagnosis).
5. **Top-up loop**: when telemetry marks an expression weak (define the
   threshold family, tunable), the pipeline generates +3-5 new example
   sentences (existing explain.py machinery) + their images (existing
   illustration-brief pipeline) and they appear in the SAME decks with
   scheduling intact for old cards. Specify the data flow and the
   idempotency keys.
6. **Provenance without per-video decks**: the estate study eliminates
   per-video decks; your model keeps source video as data (field/tag)
   so nothing is lost.

## Deliverables (docs/research/)

1. `EXPRESSION_HUB_DESIGN.md` — the model: note types (exact fields),
   card templates (described, not pixel-perfect), deck placement per
   the estate study's language-first tree, generation-flow changes
   (which pipeline stages change, at the module level), telemetry
   schema, flag/diagnosis flow, top-up flow.
2. `EXPRESSION_HUB_MIGRATION.md` — mapping from every existing model
   (21-field Idiomatic Cloud Card v2, legacy Languages:: models — go
   read them in the collection copy from the estate study's working
   dir if present) to the hub model: field-by-field, GUID strategy
   (which notes keep GUIDs and scheduling, which are new), what gets
   compressed (long explanations → one-liners: propose the compression
   as a batch LLM job spec), what gets dropped.
3. Decision list for the owner (N examples per hub, threshold family,
   diagnosis-output destination, hub-card layout options — keep it
   short and concrete, they hate jargon).

## Hard constraints

- The 17k pregenerated images key on `expression_examples.id` — the
  design must consume them as-is.
- Scheduling preservation rules identical to the estate commission.
- Frozen-model discipline: existing shipped models never mutate
  in-place; new models + migration, or spare-field use where a model
  has spares. Study only — nothing executes.
