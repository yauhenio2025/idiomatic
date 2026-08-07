# Expression-hub design

Status: proposed design, study only
Date: 2026-08-07
Scope: expression data, Anki projections, telemetry, Flag 1 diagnosis, and
telemetry-driven example top-ups. Nothing in this document has been executed.

## 1. Recommendation in one page

Make `expressions.id` the durable hub key. Source-video occurrences, examples,
audio, images, Anki notes, review events, diagnoses, and top-up batches all
refer to that key. Preserve every existing `expression_examples.id`; it is the
identity already used by the 17,112-sentence illustration campaign.

Use two frozen Anki note types, not one giant fixed-slot note:

- `Idiomatic Expression Hub v1`: one note and one hub card per expression.
  Its `ExamplesHTML` field is a compiled, vertically stacked list of every
  active example and image.
- `Idiomatic Expression Example v1`: one subordinate note and one fluency card
  per `expression_examples.id`.

This is still an expression-hub architecture: the database expression is the
authority and both note types are projections of it. The split is necessary
because Anki cannot turn an HTML list into independently scheduled cards, and
its supported notetype conversion cannot merge six existing sentence notes
into one note. Keeping one note per example lets the existing sentence cards
be converted one-for-one while retaining card IDs, revlog, FSRS state, and
scheduling. It also removes any hard ceiling on future top-ups.

Current DB-backed hubs normally begin with the existing six examples; adopted
legacy hubs preserve every reconciled example, and a source-only adoption must
generate the normal six before activation. A hub always displays every
canonical, published, non-retired example. Top-ups append three to five
subordinate example notes and regenerate only that hub's `ExamplesHTML`. A
compatible canonical old fluency card is converted in place, never recreated
or rescheduled; a true duplicate is retained but suspended.

Every projected note carries a plain `ExpressionId` field. Example notes also
carry `ExampleId`. Those fields are the primary telemetry join; stable GUIDs
and tags are redundant safeguards, not the only identity mechanism.

## 2. Invariants

1. `expressions.id` never changes merely because spelling, punctuation,
   citation form, gloss, or presentation changes.
2. An existing `expression_examples.id` is never reminted, including when its
   illustration is ingested.
3. Once an example has an image or a studied card, a material sentence change
   creates a new example row and retires the old row; it does not overwrite
   the old learning object.
4. Removing a source video cannot cascade-delete an expression or example.
5. A shipped Anki model is frozen. A later schema change means a new model ID
   plus an explicit migration; `Extra1`/`Extra2` are the only planned escape
   hatches in the two new models.
6. Review history is never combined, synthesized, or exported/reimported.
   For an active one-for-one fluency conversion, every card scheduling field
   stays byte-identical except the manifest-approved destination deck. For a
   retired source card, suspension deliberately changes `queue` and an archive
   move changes `did`; every other schedule/FSRS field and every revlog row
   stays intact. Those exceptions are recorded before and after by card ID.
7. Deck names are placement, not identity. Fields and the server-side binding
   table are identity.
8. New content is not published until text, audio, image, and ID mappings are
   ready. A partial batch remains a draft.

## 3. Canonical server model

### 3.1 Expression identity

The current `expressions` row is the durable hub. Add the following logical
attributes (column names are proposals, not DDL):

| attribute | purpose |
|---|---|
| `citation_form` | reviewed dictionary form when it differs from the first as-spoken form |
| `sense_key` | opaque stable discriminator for distinct meanings of the same normalized surface |
| `usage_line_en` | the single tight English usage line shown on the hub |
| `key_synonym` | nullable, compact target-language synonym plus the distinction that makes it useful |
| `false_friend_note` | nullable, a concrete warning against English or another known language |
| `content_version` | monotonic projection revision, not content identity |
| `status` | `active`, `merged`, or `retired` |
| `updated_at` | projection/change clock |

The existing `text` is the first as-spoken form and `normalized` is not
lemmatized. The live `UNIQUE(lang, normalized)` also prevents two genuine
senses of one surface from having separate hubs. Replace it with unique
`(lang, normalized, sense_key)` plus a non-unique normalized lookup index.
Backfill current rows with stable `legacy-primary`; a reviewed split gets an
opaque new sense key, not a mutable gloss slug. Dedup uses source context/gloss
to choose among candidates and quarantines ambiguity.

Phase 1 keeps every current expression ID and uses a reviewed citation form
only for display. Add sense-scoped `expression_aliases` for as-spoken,
citation, and legacy forms. In a reviewed polysemy split, the existing ID
survives for the primary sense, a new expression ID is created for the other,
and source/example rows are reparented without changing any example ID. True
duplicate hubs can later be merged through the inverse audited survivor-ID
operation. Neither split nor merge is inferred from surface equality alone.

### 3.2 Source occurrences

`expression_idioms` currently mixes canonical content with a source-video
occurrence. Its target role/name is `expression_sources`; the migration mapping
uses an expand/contract rename only after target queries and constraints pass.

Each source row should carry:

| field | rule |
|---|---|
| `id`, `expression_id` | retain current values |
| `video_id` | nullable FK; deleting a video sets it null rather than deleting learning content |
| `source_key` | durable retry key for YouTube, adopted, and legacy sources, including rows with no `video_id` |
| `source_title`, `source_url` | explicit text fallback for legacy/adopted sources |
| `surface_text` | expression as spoken in this source |
| `source_sentence_tl`, `source_sentence_en` | current `source_phrase_*` |
| `context_audio` | current source-sentence clip when available |
| `legacy_explanation_en`, `legacy_structured` | retained evidence, not directly rendered wholesale |
| `created_at` | provenance clock |

The worker must record a new source occurrence even when dedup says the
expression is already known. It should skip new teaching-content generation,
not skip provenance. The hub's `SourcesHTML` is compiled from all source rows
as visible title plus full URL text; no per-video deck is needed.

Version the source-key recipe: for example
`youtube:<video_id>:<occurrence-start-or-source-phrase-hash>`,
`anki:<profile_key>:<note_id>`, and `legacy:<model_id>:<note_id>`. Do not use
legacy GUID alone because the inspected collection contains duplicate GUIDs.

This requires a physical FK migration: first copy title/URL, backfill and gate
the direct example `expression_id`, then replace
`expression_idioms.video_id ... ON DELETE CASCADE` with `ON DELETE SET NULL`
and replace legacy example ownership with nullable `source_id ... ON DELETE
RESTRICT`; source rows retire by status rather than deletion. Direct expression
ownership is also `ON DELETE RESTRICT`. Composite source/example expression
FKs prevent cross-expression links. The old `idiom_id NOT NULL ... ON DELETE
CASCADE` cannot remain as hidden ownership. Use unique
`(expression_id, source_key)`; PostgreSQL's existing
`UNIQUE(expression_id, video_id)` does not deduplicate multiple NULL-video
legacy sources.

### 3.3 Examples

Keep the current table and every primary key, but make examples direct hub
children:

| target field | purpose |
|---|---|
| `id` | unchanged `BIGINT`; image, audio, note, and job identity |
| `expression_id` | direct non-null FK to the hub, backfilled through the current occurrence |
| `source_id` | nullable provenance occurrence; replaces the ownership semantics of `idiom_id` |
| `position` | display order within the expression; positive, not capped at six |
| `en_text`, `target_text` | immutable after publication except typo-only reviewed correction |
| `audio_en`, `audio_target` | versioned media references |
| `source_kind` | `initial`, `topup`, or `legacy_adopted` |
| `stable_key` | old rows `legacy:<id>`; new rows `topup:<batch_id>:<attempt_no>:<slot>` |
| `topup_batch_id` | nullable generation provenance |
| `status` | `draft`, `ready`, `published`, or `retired` |
| `canonical_example_id` | nullable self-FK; set when this row is a retained duplicate of another example |
| `published_at` | delivery/exposure clock |

Drop the `ord BETWEEN 1 AND 6` ceiling. Do not replace the table or cascade it
from videos. A unique `stable_key` makes retries return the same row and hence
the same example ID. When two rows represent the same learning example, keep
both IDs and assets, choose one canonical published row, set the other row's
`canonical_example_id`, and retire its projection. Thus every canonical
published example has exactly one active fluency binding and image; retained
duplicate IDs are not silently deleted or displayed twice.
Enforce both `source_id` and `canonical_example_id` with the row's
`expression_id` in composite FKs, so neither provenance nor dedup can cross an
expression sense.
A partial unique `(expression_id, position)` for non-retired canonical rows
keeps the compiled rail deterministic while allowing retained duplicates.

### 3.4 Illustration assets

The authoring contract already uses one visual anchor per expression and one
variation per `example_id`. Preserve that contract and add two typed stores:

`expression_visual_anchors`

- `expression_id`, `version`
- semantic hook, setting, cast slugs, absurd element
- typed actor links to approved `factory_actors.id` rows (slugs remain the
  portable authoring contract)
- persisted base-setting image path and content hash
- cast-sheet, style, authoring recipe, model, and renderer fingerprints
- authoring JSON/content hash, approval state, and `published` pin
- unique `(expression_id, version)` with one approved current version

`expression_example_assets` (the logical subtype; implement it in the planned
`factory_assets` registry with a typed `expression_example_id` FK rather than
creating a second competing asset ledger)

- `id`, `example_id` FK, `visual_anchor_id` FK, `anchor_version`
- `brief_hash`, `render_input_hash`, `render_recipe_version`, engine/model
- creation-tier path, immutable Anki media filename, MIME, content hash
- `draft`/`approved`/`rejected`, `is_current`, `superseded_at`, approval timestamps
- unique `(example_id, render_input_hash)` and at most one approved current
  image per example

Ingestion requires a manifest carrying `example_id`, path, byte hash, brief
hash, anchor ID, and renderer recipe; a filename is never the identity. If a
local renderer happens to emit `ex_<example_id>.jpg`, that name is only a
creation-tier convenience. Anki delivery preserves those exact bytes under a
content-addressed basename such as
`idh_ex_2503_a1b2c3d4.jpg`, so a revised image never silently reuses stale
media. Existing output is registered from the manifest and numeric ID; it is
never matched by sentence text or ordinal. Before cutover, the manifest must
cover every expected campaign ID exactly once, with no unknown/orphan ID.

`render_input_hash` is the canonical hash of the example/brief, visual-anchor
ID/version, base/reference image hash, ordered cast-sheet hashes, style,
authoring recipe, engine/model, and renderer fingerprint. Merely changing an
anchor, reference, cast, or model therefore cannot collide with or reuse an
older render.

Persisting the base setting matters. Reusing a seed is not enough to guarantee
anchor constancy after a renderer/model upgrade. Each published example asset
has a real `visual_anchor_id` FK, and the hub pins the published anchor ID. A
top-up must reuse that exact anchor, base/reference image, cast sheets, style,
and renderer fingerprints. Switching anchors requires rerendering every
published example and atomically changing the hub; mixed anchor generations
are forbidden. If the current campaign did not persist a base image, migration
freezes its authored anchor/cast JSON and establishes an approved reference
before any top-up.

`rescue_items` also gains a nullable-while-migrating `expression_id` FK. After
resolution, rescue state is another intervention attached to the hub; its
overwritten `struggle_snapshot` is not reused as the telemetry authority.

### 3.5 Projection bindings

Add `anki_note_bindings` as the profile-specific collection crosswalk:

| field | purpose |
|---|---|
| `profile_key`, `note_id` | composite primary key; note IDs disambiguate legacy duplicate GUIDs |
| `note_guid` | observed GUID; not assumed unique for retired legacy notes |
| `card_kind` | `hub`, `fluency`, `diagnosis`, or retired legacy kind |
| `model_version` | expected frozen model |
| `expression_id` | always set for hub/fluency |
| `example_id` | set for fluency |
| `legacy_model`, `legacy_guid` | migration provenance |
| `active` | whether future releases should project this binding |

Require a partial unique `(profile_key, note_guid)` for active target notes and
a hard pre-release duplicate-GUID gate. The snapshot already contains two
duplicate-GUID pairs in Cloud v2; because all Hub notes are new, those old
pairs remain retired evidence, but no target release may share their GUID.
For every GUID an APKG will emit, gate collection-wide note cardinality—not
just active bindings: zero before creating a new target note, and exactly one
after creation or for a retained migrated note. A suspended duplicate still
makes import ambiguous.
Card IDs are profile-local, so the telemetry layer separately records
`(profile_key, card_id, note_id, note_guid, template_ord)`. A separate active
content-GUID projection maps `(profile_key, card_kind, expression_id,
example_id)` to the one GUID the builder must emit. Enforce partial uniqueness
for active `(profile_key, expression_id)` Hub bindings and active
`(profile_key, example_id)` fluency bindings; do not rely on SQL NULL behavior
in one generic composite index.

## 4. Anki note types

The proposed numeric IDs were unused in the 2026-08-07 collection snapshot.
They must be rechecked immediately before implementation.

### 4.1 `Idiomatic Expression Hub v1`

Proposed model ID: `1820180001`
Sort field: `Expression`
Templates: exactly one, `Hub`

Exact fields, in order:

| # | field | contents |
|---:|---|---|
| 1 | `ExpressionId` | decimal `expressions.id`, plain text |
| 2 | `Lang` | `de`, `es`, `fr`, `it`, or `pt` |
| 3 | `Expression` | reviewed display/citation form |
| 4 | `GlossEN` | concise English gloss |
| 5 | `UsageLineEN` | one tight sentence |
| 6 | `KeySynonym` | nullable compact HTML/text; only a consequential synonym |
| 7 | `FalseFriend` | nullable compact HTML/text; may name another known language |
| 8 | `ExamplesHTML` | compiled sanitized list of every published example |
| 9 | `SourcesHTML` | visible video titles and full URL text |
| 10 | `Extra1` | frozen spare, blank in v1 |
| 11 | `Extra2` | frozen spare, blank in v1 |

`ExamplesHTML` is a projection, not an authority. Each item includes
`data-example-id`, target sentence, English sentence, and the approved image
reference. It is deterministically rebuilt from the database.

Suggested tags:

```text
idiomatic::expression-hub  lang::es  expression::439
source::youtube::<youtube_id>  hub-schema::1
```

Hub GUID (all Hub cards are new schedules; old listen-and-learn cards are
retired intact because they exposed the gloss/explanation and tested a
different task):

```text
sha1("idiomatic-expression-hub-v1::<lang>::<expression_id>")[:16]
```

No old Cloud/Idiom/Audio GUID is reused for a Hub card.

### 4.2 `Idiomatic Expression Example v1`

Proposed model ID: `1820180002`
Sort field: `Target`
Templates: exactly one, `EN -> target`

Exact fields, in order:

| # | field | contents |
|---:|---|---|
| 1 | `ExpressionId` | decimal hub ID, plain text |
| 2 | `ExampleId` | decimal `expression_examples.id`, plain text |
| 3 | `Lang` | language code |
| 4 | `English` | English prompt sentence |
| 5 | `Target` | target-language answer sentence |
| 6 | `EnglishAudio` | optional `[sound:...]` |
| 7 | `TargetAudio` | target sentence `[sound:...]` |
| 8 | `Image` | approved `<img>` reference for this exact example |
| 9 | `Expression` | compact answer-side expression reminder |
| 10 | `GlossEN` | compact answer-side gloss |
| 11 | `SourceHTML` | source title plus visible URL, or `Telemetry top-up <date>` |
| 12 | `Origin` | `initial`, `topup:<batch_id>`, or `legacy_adopted` |
| 13 | `Extra1` | frozen spare, blank in v1 |
| 14 | `Extra2` | frozen spare, blank in v1 |

Suggested tags add `example::<id>`, `origin::<kind>`, and the same expression
and language tags as the hub.

New-note GUID:

```text
sha1("idiomatic-expression-example-v1::<example_id>")[:16]
```

Existing sentence notes retain their old text-derived GUID during in-place
migration. All later content uses the ID-derived recipe.

### 4.3 Why the hybrid model wins

| option | benefit | failure |
|---|---|---|
| One note, fixed example fields/templates | literal one-note/many-card projection | hard N ceiling; roughly six fields and one template per example; merging current notes requires unsupported card reparenting; later field/template growth violates the freeze |
| One note, `ExamplesHTML` only | unlimited, simple hub strip | HTML cannot emit independently scheduled cards |
| Hub note plus subordinate example notes | unlimited growth, exact image identity, one-to-one scheduling migration | duplicates rendered example data into `ExamplesHTML`; requires deterministic rebuild discipline |

Choose the third. The database, not either Anki field bundle, prevents drift.

## 5. Card templates

### 5.1 Fluency card

Front:

- English sentence, large and centered
- English audio control when present
- no image and no expression hint, so neither leaks the answer

Back:

- target sentence and target audio
- the exact example image, tablet-width but bounded
- small expression plus gloss reminder
- compact source footer

This keeps the existing study rhythm: one English prompt, one target sentence,
one independently scheduled card. Flag 1 remains a native Anki color flag; no
custom button is required.

### 5.2 Hub card

Front:

- target-language expression only

Back, top to bottom:

1. expression and English gloss;
2. the one-line usage note;
3. key synonym and/or false-friend warning only when non-empty;
4. a single vertical rail of examples: target sentence, muted English line,
   then that sentence's image;
5. source titles and full URLs as text.

No long stitched listen-and-learn audio is carried forward. Independent
images share an expression anchor/cast, producing the intended comic-strip
rhythm without pretending they are sequential panels.

## 6. Deck placement

The relevant language-first estate branch is identical for all five active
languages:

```text
DE German                    ES Spanish
└── 1 Expressions            └── 1 Expressions
    ├── 1 Fluency                ├── 1 Fluency
    └── 2 Expression Focus       └── 2 Expression Focus

FR French                    IT Italian                  PT Portuguese
└── 1 Expressions            └── 1 Expressions            └── 1 Expressions
    ├── 1 Fluency                ├── 1 Fluency                ├── 1 Fluency
    └── 2 Expression Focus       └── 2 Expression Focus       └── 2 Expression Focus
```

Fluency examples always go to `1 Expressions::1 Fluency`; hub cards always go
to `1 Expressions::2 Expression Focus`. A top-up uses those same deck IDs and
model IDs. These labels intentionally match the parallel estate study's shared
mapping constants.
Source videos are fields/tags only.

Diagnosis drills go to:

```text
<language root>::4 Exercises::Diagnosed trouble spots
```

They do not go into Expressions, because their reviews measure the inferred
collocation/grammar problem, not mastery of the trigger expression.

## 7. Review telemetry

### 7.1 Raw, mapped, and aggregate layers

Use append-only raw facts plus rebuildable aggregates.

`anki_pull_snapshots`

- primary key `(profile_key, pull_id)` and an explicit previous completed pull
- collection/client identity, started/completed/observed timestamps, status,
  collection/snapshot hash, Anki schema/version, and cutover marker
- maximum revlog ID plus note/card/flag row counts and canonical hashes
- failed/partial pulls remain recorded but cannot advance review or flag
  watermarks; replaying the same snapshot hash is idempotent

`anki_review_events`

| field | notes |
|---|---|
| `profile_key`, `revlog_id` | composite primary key; ingestion idempotency |
| `card_id`, `note_id`, `note_guid`, `template_ord` | original Anki identity |
| `reviewed_at`, `study_date` | derive with the profile's configured timezone and Anki rollover boundary; version that rule |
| `ease`, `review_type`, `time_ms` | raw revlog values |
| `ivl`, `last_ivl`, `factor` | raw scheduling evidence |
| `observed_mapping_revision_id` | immutable mapping selected at ingest, nullable when unresolved; never rewritten on correction |

`anki_card_mapping_revisions`

- primary key `(profile_key, card_id, mapping_revision)` with one current
  revision by partial unique index
- note ID/GUID, template ordinal, model/deck, card kind, expression/example
  IDs, resolution reason/evidence, valid-from/to pulls, and `is_current`
- corrections append a revision; they never edit the raw revlog fact or erase
  the mapping used by an older aggregate

`anki_card_projection` is the current view/cache over those revisions for
operational joins. Each daily aggregate records the exact mapping revision IDs
or their canonical set hash, so both the original and corrected rollups replay.

`anki_card_flag_state`

- primary key `(profile_key, card_id)`
- last observed `cards.flags & 0b111`, monotonic transition sequence, current
  Flag-1 diagnosis epoch, last snapshot/exact-event IDs, and state version
- first/last observed timestamps and armed/consumed/clear state

`anki_card_flag_observations` retains the raw headless evidence with primary
key `(profile_key, pull_id, card_id)`, raw `cards.flags`, masked color, card
modification value, and mapping version. Transitions are derived from adjacent
completed pulls; the observation, not `cards.mod`, is the evidence.

`anki_flag_transitions`

- one row per observed transition between masked native colors (including
  clear), keyed by `(profile_key, card_id, transition_seq)`
- nullable add-on `client_event_id`/device sequence, unique per profile, or
  headless previous/current pull IDs; previous/current masked flag,
  `observed_at`, and versioned profile-rollover `study_date`

`anki_flag1_events`

- one row per transition into Flag 1, with the transition ID unique
- `(profile_key, card_id, diagnosis_epoch)` unique; the epoch increments only
  on a newly observed non-1 → 1 entry, not on its later clear transition
- candidate-review count, optional exact linked revlog ID, attribution
  status/reason, and expression/example IDs
- consumed, clear-requested/observed, diagnosis status, and expected state/
  review versions used by safe acknowledgement

`expression_daily_telemetry`

| field | definition |
|---|---|
| `profile_key`, `expression_id`, `study_date`, `aggregate_revision` | append-only primary key; one current revision by partial unique index |
| `reviews` | all mapped expression-card reviews |
| `fluency_reviews`, `hub_reviews`, `diagnosis_reviews` | separate projections |
| `fluency_again_count`, `fluency_hard_count` | raw normal-study button counts |
| `fluency_lapse_count` | Again with `revlog.type=REVLOG_REV`; relearning Again is not another lapse |
| `flag_event_counts` | counts for masked native flags 1-7 by observed date; Flag 1 also broken out |
| `flag1_count`, `flag1_unlinked_count` | new Flag-1 epochs, not days a flag remained set |
| `flagged_fluency_review_count` | all exactly linked normal fluency reviews attributed elsewhere |
| `flagged_fluency_again_count`, `flagged_fluency_hard_count` | exactly linked sentence-attributed events |
| `effective_fluency_again_count`, `effective_fluency_hard_count` | expression-attributed counts after the flag split |
| `flagged_fluency_lapse_count`, `effective_fluency_lapse_count` | raw review-Again lapses split by exact Flag-1 attribution |
| `distinct_examples_seen` | raw `COUNT(DISTINCT example_id)` on all mapped fluency reviews |
| `distinct_eligible_examples_seen` | distinct examples among policy-eligible fluency reviews |
| `eligible_fluency_reviews` | post-cutover normal learn/review/relearn fluency events, minus exact Flag-1 reattribution |
| `source_max_revlog_id`, `source_max_pull_id` | raw review/flag ingestion watermarks |
| `mapping_version`, `flag_link_version`, `study_day_version`, `input_hash`, `is_current` | aggregate reproducibility/current pointer |

Color-transition and Flag-1 event counts land on the transition's observed
study day. Review reattribution—`flagged_fluency_*`, the effective decrement,
and the eligible denominator—lands on the linked revlog event's study day,
which may be earlier. A late link appends a revision for that review day; it
does not move the review into the observation day.

Only fluency reviews feed expression weakness. Hub and diagnosis reviews stay
visible for analysis but do not trigger top-ups. “Eligible” means a mapped,
active fluency-card answer after cutover whose revlog kind is normal learning,
review, or relearning, excluding any answer exactly reattributed by Flag 1.
Manual/rescheduled and filtered/cram events are retained raw but are never
eligible. Policy floors use `distinct_eligible_examples_seen`, not the raw
distinct count. Store facts in the daily table. Compute weighted score/rate in
a separate
immutable `expression_policy_evaluations` revision keyed by profile,
expression, evaluation date, policy version, and evaluation revision:

```text
weak_score = effective_fluency_again_count
             + hard_weight * effective_fluency_hard_count
weak_rate  = weak_score / eligible_fluency_reviews
```

When the eligible denominator is zero, `weak_rate` is null/unevaluable, never
zero.

A late mapping or flag-link correction appends a daily revision; it never
overwrites the counts used by an earlier decision. Each policy evaluation
stores its exact daily-revision IDs and complete count snapshot (eligible
reviews, eligible distinct examples, raw/effective Again/Hard/lapses, score,
rate, window, and cutover) plus an input hash and one-current pointer. If a
corrected evaluation removes weakness at any pre-publication point—including
an accepted response, allocated draft IDs, or media-ready work—close the
episode, stop jobs, and retire/quarantine those IDs/assets without projecting
them. Once the atomic publication transaction commits, never retract content
or rewrite history: mark the episode `basis_corrected_after_publication`,
deliver/retain that learning content, and prevent another round unless a new
current evaluation qualifies (then rearm the episode under that evaluation).

### 7.2 Flag 1 protocol

Anki stores the user color in the low three bits: `cards.flags & 0b111`.
Revlog has no flag event or historical flag state. Consequently, joining a
current flag to all earlier reviews would corrupt the data.

Protocol at cutover:

1. The first post-deploy pull records every current flag as a baseline. It
   creates no Flag-1 event and changes no historical attribution. The inspected
   backup had 125 old Flag-1 cards, including two fluency cards, which proves
   this baseline is necessary.
2. Exact add-on events and headless observations use one transactional ingest
   path. It locks `anki_card_flag_state`, deduplicates the client event/pull,
   allocates the next transition and (only for non-1 → 1) diagnosis epoch, and
   updates state before committing. If the exact event arrives first, the next
   snapshot sees state already at 1 and creates no transition. If the snapshot
   arrives first, a later exact event may enrich that still-current epoch with
   its revlog ID, but cannot create another diagnosis.
3. Count every native color transition in raw telemetry. A non-1 → 1 entry
   queues `sentence_diagnoses` only when the card maps exactly to one active
   fluency example. Flag 1 on a Hub, diagnosis, retired legacy, or unresolved
   card is retained with `unsupported_card_kind`/quarantine status and creates
   no sentence diagnosis.
4. Exact target behavior is an add-on event carrying `(profile, card_id,
   revlog_id, masked_flag)` when Flag 1 is applied in the reviewer to that
   just-recorded answer. A browser/editor flag with no owned reviewer event is
   unlinked. With headless snapshots as fallback, link and exclude a review
   only when exactly one new eligible fluency Again/Hard exists for that card
   between the previous and current snapshots. If there are zero or multiple
   candidates, queue diagnosis with an ambiguous/unlinked reason and exclude
   none. Never manufacture a flag timestamp from `cards.mod` or proximity.
5. A linked review is counted in raw telemetry but excluded from the
   expression denominator and effective Again/Hard/lapse counts. Thus a
   flagged lapse cannot make the expression look weak. A flag that remains set
   creates no more epochs, and later reviews are not silently excluded.
6. After the server durably records and queues the diagnosis, it marks the
   event consumed and returns a clear command carrying flag-event ID, linked
   revlog ID, and expected card-state version. The add-on clears only if the
   card is still Flag 1, the latest reviewer/revlog event is still that linked
   review, and no newer flag transition or card-state mutation exists.
   Otherwise it leaves the flag set for manual reconciliation. Baseline flags
   are never auto-cleared. A later non-1 observation is required before rearm.
7. With headless fallback, the learner must leave Flag 1 set until the next
   Anki sync/pull and acknowledgement. A set-and-clear between pulls is
   invisible; it can diagnose nothing and excludes nothing.

Plain Again or Hard with no linked Flag 1 means the trigger expression was the
problem. This protocol starts only at the declared cutover timestamp. Earlier
revlog is retained and mapped for historical analysis but is not eligible for
weakness episodes, because its Flag-1 attribution cannot be reconstructed.

## 8. Diagnosis flow

`sentence_diagnoses` stores one reproducible job per Flag-1 event:

- `(profile_key, flag_event_id)` is unique; status and timestamps describe the
  queue lifecycle;
- expression ID, example ID, and the exact linked review ID when one exists;
- an immutable input snapshot containing the sentence pair, expression,
  gloss, usage line, and their content versions;
- learner-profile version plus evidence cutoffs and canonical evidence hashes;
- category, trouble span, diagnosis, likely interference language, confidence,
  prompt/model/diagnosis-policy versions, immutable accepted response, and
  validated JSON;
- lease owner/expiry/attempt and compare-and-swap state, so only the first
  accepted response can advance to practice generation.

The known-language profile is explicit and immutable by version. A
`learner_profile_versions` row records `profile_key`, version, owner approval,
Anki timezone/rollover settings, and a canonical hash. Child rows use confirmed
BCP-47 language tags and record role (`L1`, `known`, or `learning`) and
proficiency; the profile hash covers the parent and the ordered child rows.
The retrieved evidence snapshot stores the exact canonicalized, redacted
payload passed to the model, its hash, retrieval query/version, source IDs, and
`updated_at`/maximum-ID cutoffs for selected `personal_errors`, reviewed
`f4_pairs`, LingQ terms, grammar units, and structured pitfall/false-friend
facts. Source rows may later change without destroying prompt replay. Research
Markdown is not pasted wholesale into prompts.

The LLM output contract is:

```json
{
  "category": "collocation|tense_mood|agreement|word_order|false_friend|vocabulary|audio|other|unknown",
  "trouble_span": "exact span or empty",
  "diagnosis_en": "one concrete explanation",
  "why_not_expression": "short explanation",
  "interference_language": null,
  "confidence": 0.0,
  "practice": [
    {"sentence_tl": "...", "sentence_en": "...", "focus": "..."}
  ]
}
```

`interference_language`, when non-null, must be one of that profile version's
confirmed languages and must differ from the target language. It is not a
hard-coded seven-language enum. No supporting evidence means `null`.

Rules:

- emit zero to three practice sentences. An immutable diagnosis-policy version
  defines the confidence and review gates; recommended `diagnosis-balanced-v1`
  requires validated confidence at least 0.75 before automatic drills, while a
  lower score emits diagnosis-only pending review;
- target the diagnosed feature and normally omit the trigger expression, so
  drill reviews cannot contaminate expression weakness;
- validate target language, translation, focus, novelty, and safety under the
  same review discipline as grammar content;
- inferred diagnoses never enter `personal_errors`, which remains the
  teacher-attested registry.

Retries reuse the accepted diagnosis payload. A different valid response for
the same immutable input is retained as a quarantined attempt, not allowed to
overwrite the accepted result.

Do not insert these directly into `grammar_items`: its current
`UNIQUE(lang, sentence)` plus `ON CONFLICT DO NOTHING` could silently lose a
diagnosis slot, and its curriculum routing is wrong. Add
`diagnosis_practice_items` with `(diagnosis_id, slot)` unique, stable text
hashes, review status, and an optional `grammar_item_id` link when an existing
verified item tests exactly the same focus. A collision must be explicitly
linked after verification or regenerated; it is never silently dropped.

New diagnosis items still project through the frozen
`Idiomatic Grammar Drill v1` model. Use a separate GUID namespace,
`sha1("idiomatic-diagnosis::<profile_key>::<practice_item_id>")[:16]`, and put
`diagnosis-practice:<practice_item_id>` in `ItemId`. Populate all 14 frozen
fields: `Lang`; category in `Topic`; reviewed label/symbol in `TenseLabel` and
`Symbol`; English prompt in `Sentence`; target answer in `Answer` and
`SentenceFull`; concise English meaning in `GlossEn`; diagnosis in `Why`;
audio in `Extra1`; expression ID in `Extra2`; diagnosis ID in `Extra3`; and
category in `Extra4`. Repeat IDs in tags. Route only these new notes to
`4 Exercises::Diagnosed trouble spots`. When a slot is explicitly
`satisfied_by_existing`, the reused grammar item keeps its own card, deck,
GUID, and schedule; no diagnosis card or diagnosis-review telemetry is created
for that slot. Reviews of actual diagnosis cards roll up by their diagnosis
category, never by trigger-expression weakness.

## 9. Weakness policy and top-up loop

### 9.1 Tunable policy family

Policy rows are immutable versions containing the window, evidence floors,
Again/Hard weights, opening and severe thresholds, top-up sizes, cooldown,
post-delivery exposure gate, and recovery rule. Daily facts are never rewritten
when a policy changes; `expression_policy_evaluations` records the input range,
aggregate hash, result, and policy version.

Recommended `balanced-v1`:

- evaluate a rolling 14-day window only after at least 6 eligible fluency
  reviews across at least 2 example IDs;
- `weak_score = effective Again + 0.5 * effective Hard` and
  `weak_rate = weak_score / eligible fluency reviews`;
- open an episode when `weak_rate >= 0.30` and either effective Again is at
  least 3 or `weak_score >= 4`; 5 effective Agains inside the window is a
  severe override of that rate/count gate, but not of the 6-review/2-example
  evidence floor;
- request exactly 3 examples normally and exactly 5 for severe weakness or a
  later still-weak round;
- after delivery, wait at least 14 days and require at least 6 eligible reviews
  since delivery, including at least 4 reviews spread across at least 2 of the
  newly delivered examples, before another round can open;
- recover only after that exposure floor and a rolling 21-day window that
  itself contains at least 6 eligible reviews across 2 examples, with no
  effective Again and `weak_rate < 0.15`. No-study time cannot prove recovery.

The decision list also gives complete Sensitive and Conservative opening rows.
They inherit the same flag split, exact 3/5 batch sizes, exposure gate, and
recovery rule, plus the 5-Again severe override only after their own evidence
floor, so changing sensitivity does not silently change delivery or idempotency
behavior.

### 9.2 Durable episodes and batches

`expression_weakness_episodes` is profile-scoped. It stores `profile_key`,
expression ID, policy version, opening evaluation/snapshot hash, state
(`open`, `cooldown`, `recovered`, `cancelled`, `basis_corrected_after_publication`,
or `closed`), round, and delivery/recovery timestamps. A partial unique index
permits only one unresolved (`open`, `cooldown`, or corrected-after-publication)
episode per `(profile_key, expression_id)`.

`expression_topup_batches` stores episode ID/round, requested count, state,
current accepted attempt ID, and created/ready/published timestamps. Unique
`(episode_id, round)` is the decision edge. Immutable
`expression_topup_generation_attempts` rows, unique on `(batch_id, attempt_no)`,
hold request snapshot/hash, expression content version, profile/policy/prompt/
model versions, every published-and-retired exclusion ID/text hash, pinned
anchor version, raw response/hash, validation result, lease owner/expiry, and
accepted/superseded/quarantined state. A partial unique permits one current
accepted attempt per batch. `expression_topup_batch_items` is unique on
`(generation_attempt_id, slot)` and holds its allocated example ID.

A worker claims an attempt with a lease and compare-and-swap transition. The
first fully validated response for that request hash is persisted before any
row/media work. Its retry reuses it; a different response for the same request
hash is quarantined. Allocation/publication also takes one expression-scoped
writer lease and compares current `content_version` with the attempt snapshot.
Drift marks that immutable attempt superseded and creates a new numbered
attempt with a new snapshot; it never edits the old request or violates the
batch/round key. Draft IDs already allocated to a superseded attempt remain
unprojected/retired and are never reused. Two batches cannot append against the
same expression version.

### 9.3 End-to-end top-up

```text
daily Anki pull
  -> raw review/flag ingest
  -> study-day rollup + versioned policy evaluation
  -> diagnosis queues and one weakness episode edge
  -> leased generation of exactly 3 or 5 distinct examples
  -> transaction allocates all example rows and immutable IDs
  -> ID-keyed target/English audio and anchor-pinned image jobs
  -> approval gate for every text/audio/image item
  -> atomic publication of the whole batch
  -> next coalesced language delta adds examples and updates one hub
  -> authoritative profile import acknowledgement starts cooldown/exposure clock
```

The prompt receives the immutable expression content version and every
historical example—not just active ones—to avoid resurrecting a retired
sentence. It must return exactly the requested count, use a natural inflected
form of the expression, stay at B1-B2 outside the target, and pass language,
translation, exact-hash, and semantic-duplicate checks. Persist an
expression-scoped content fingerprint for every accepted pair, including
retired rows. Allocate IDs only after the complete response validates, then
generate media from those rows. One failed slot keeps all 3/5 in draft; the
system never shrinks a promised batch to the successful subset.
Publication flips every item together and increments the expression content
version in the same transaction.

Suggested idempotency keys:

| artifact | key |
|---|---|
| policy evaluation | `(profile_key, expression_id, evaluation_date, policy_version, evaluation_revision)` plus aggregate input hash |
| top-up decision | `(episode_id, round)` |
| generation attempt | `(topup_batch_id, attempt_no)` with immutable `request_hash` |
| accepted generation | one current attempt plus one accepted `response_hash` |
| generated slot | `(generation_attempt_id, slot)` |
| example | unique `stable_key`; immutable returned `example_id` |
| content duplicate gate | `(expression_id, normalized_pair_fingerprint)` across every status |
| TTS | `(example_id, text_hash, voice_fingerprint)` |
| illustration brief | `(example_id, brief_hash, anchor_version)` |
| render | `(example_id, render_input_hash)` over every pinned visual input |
| Anki note | retained migrated GUID or ID-derived new GUID |
| release | `(collection_key, lang, release_sequence)`; manifest hash is verified content |

The scheduler runs the pull, rollup, evaluation, and queue creation daily.
Generation/media workers lease independently; ready work is coalesced into at
most one ordinary release per language per day unless an operator requests an
urgent release.

## 10. Delivery without giant repeated downloads

A full pool rebuild embedding roughly 17,000 images for every top-up would be
prohibitively repetitive. Replace the overwritten pool artifact with an
ordered release ledger:

- an initial bootstrap/compaction snapshot, language-sharded to bounded sizes,
  containing every current hub/example note and every referenced initial image
  and audio asset;
- append-only language deltas containing changed hub fields, new example
  notes, and only newly referenced media;
- a monotonically increasing sequence per collection and language, a previous
  manifest hash, and a content manifest hash;
- per-client acknowledgement of every required sequence;
- occasional compaction, after which a new client installs the stated snapshot
  and every later delta.

`anki_releases` is unique on `(collection_key, lang, sequence)`; the manifest
hash proves the bytes and is not part of the idempotency key. Each signed-off
manifest lists model ID/schema/template/CSS hashes, note GUID plus field hash,
media basename/size/content hash, prior sequence/hash, and minimum migration
marker. A client refuses a gap, a predecessor-hash mismatch, an unexpected
model hash, or a reused sequence with different bytes.

Sequence allocation is serialized, not `MAX(sequence)+1`. One
`anki_release_sequence` row per `(collection_key, lang)` is locked at finalize,
and a partial unique permits only one building release for that pair.
`anki_release_items` binds each ready batch, changed Hub revision, note
operation, and media asset to one non-aborted release. A builder leases a
release and freezes its content cutoff/membership. Because only one build may
exist, it reads a candidate next sequence/predecessor without advancing the
allocator, builds idempotently, writes APKG/manifest bytes to content-addressed
temporary objects, verifies them, and durably commits them by atomic rename or
object-store finalize. Only then does a transaction relock the sequence row,
CAS the candidate/predecessor, advance the allocator, and mark the DB release
`finalized` with immutable artifact URI/hash. A crash before DB finalization
leaves only reclaimable unreferenced bytes; a finalized row can never point to
missing/unverified bytes. An aborted pre-finalization build consumes no
sequence and its items can be rebound. Daily and urgent workers therefore
coalesce or wait rather than race.

`anki_release_acknowledgements` is unique on `(release_id, client_id)` and
records profile/collection, import result, note/media verification, and time.
Each profile names one authoritative importing client. Only that client's
successful, hash-verified import marks the profile-scoped batch delivered and
starts its cooldown; secondary device acknowledgements are visibility only.
Batch delivery is derived from release-item membership plus that ACK, not from
an arbitrary first client updating a scalar timestamp.

The controlled migration is the only operation allowed to install the two new
models and convert legacy notes. Afterwards the importer uses note updates but
never notetype updates and never imports scheduling (`update_notes=ALWAYS`,
`update_notetypes=NEVER`, `merge_notetypes=false`, `with_scheduling=false`,
`with_deck_configs=false`, expressed in the concrete Anki API's equivalent
options). It gates the exact model ID, ordered fields, template count/content,
and CSS hash before touching notes. Deck moves for existing cards are performed
by the migration/add-on mapping, not trusted to APKG import behavior.

Every bootstrap shard is imported and its media verified before any migrated
card is released for review. For each hub, the set of `data-example-id` values
in `ExamplesHTML` must equal the set of canonical published, non-retired DB
examples, each exactly once; every such ID must have one approved current image
whose exact content-addressed media bytes are present. Missing media means the
hub/batch remains draft—there is no placeholder or text-only publication.

Anki collection full-sync and media sync are separate gates. Migration is not
delivered until the authoritative collection upload/download and the desktop/
client media uploads/downloads all pass their hashes and media checks.

All releases reuse stable deck IDs, model IDs, note GUIDs, and immutable media
names. A delta updates one hub field in place, creates only new example cards,
and changes no old schedule. The current `apkgs(lang, kind)` partial uniqueness
and janitor retention rules must be replaced by this ledger before rollout.

## 11. Module-level generation changes

| module | target change |
|---|---|
| `db/schema.sql` | add direct example ownership and safe FKs, source keys, anchor/assets registry, bindings, raw telemetry, profiles/diagnoses, policy evaluations, episodes/batches, and release ledger |
| `idiomatic/settings.py` | versioned policy defaults, collection/profile identity, study-day settings, model/schema hashes, release paths, and worker limits |
| `pipeline/extract.py` / dedup | keep extracting sources; dedup suppresses new teaching content but no longer discards repeat provenance |
| `idiomatic/worker.py` and `idiomatic/cron.py` | stop per-video publication; allocate IDs before media; run daily pull/rollup/evaluation queues; lease generation/media/release work and publish only complete batches |
| `idiomatic/db.py` | expose expression/example IDs and typed transactions for sources, assets, mappings, flag epochs, diagnoses, episodes/batches, and sequenced releases |
| `pipeline/explain.py` | split initial metadata, initial examples, top-up examples, diagnosis, and migration compression prompts; parameterize count and immutable exclusions |
| `pipeline/audio.py` | keep atomic sentence TTS keyed/versioned by example ID; retire explanation TTS and long stitched card audio |
| illustration tools/runner | ingest the frozen campaign ID manifest (17,112 in this snapshot), persist approved base anchors, add variations by example ID, and hash prompt/recipe/reference inputs rather than cache on file existence |
| `pipeline/pool.py` | replace all four pool builders with frozen hub/example projections and sequenced snapshot/delta packaging; include strict note/media manifests |
| `pipeline/apkg.py` | stop active per-video output; retain read-only legacy parsing/migration support until cutover, then quarantine it |
| `idiomatic/grammar/apkg.py` plus a diagnosis adapter | project `diagnosis_practice_items` through the existing frozen model, separate diagnosis GUID namespace, and Exercises destination without the curriculum query or silent sentence-conflict path |
| `rescue_autopilot.py` | ingest raw revlog once, map card IDs, observe flag transitions, build reproducible daily facts/evaluations, and feed rescue/top-up policies from those facts |
| `api.py` / `ui_api.py` | typed image ingest by example ID, release manifests/acknowledgements, binding import, and review surfaces for mappings, top-ups, and diagnoses |
| desktop add-on | run the checkpointed collection migration, emit exact future flag/review events, clear acknowledged Flag 1 safely, enforce release sequence/model hashes, and never infer identity from deck name |

The current server flag disables the two bare `Idioms Audio` builders, but
`_build_idioms_pool()` still creates the long Cloud-v2 didactic deck. All old
expression/audio builders must stop at cutover or the retired estate will be
repopulated.

## 12. Acceptance checks for a later implementation

- For every active one-for-one fluency conversion, note/card IDs and GUID,
  revlog rows, queue/type/due/odue/odid, interval/factor/reps/lapses/left,
  flags, and opaque FSRS/card data match the pre-manifest byte-for-byte; only
  the approved `did` move, note model/fields/tags, and bookkeeping clocks
  differ. For a suspended source card, only approved `did`, `queue`, and
  bookkeeping clocks differ.
- No old model definition changes. The two target model IDs and ordered
  field/template/CSS hashes match the frozen specification on every client.
- Every GUID emitted by a target release resolves to exactly one note across
  the whole collection, including suspended/archive notes in that count.
- Every active hub/fluency card resolves to exactly one expression ID; every
  fluency card resolves to exactly one existing canonical example ID. Every
  canonical published example has exactly one active fluency binding/card,
  while retained duplicates point to their canonical row and remain inactive.
- The frozen illustration campaign manifest (17,112 IDs in the inspected
  snapshot) is hash/set-equal to registered assets, with no unknown or duplicate
  ID and verified byte, anchor, brief, and renderer hashes. Future code checks
  that frozen set rather than a numeric constant. No original example ID
  changes or disappears; retained-retired assets have an explicit unprojected
  disposition rather than being mislabeled orphan media.
- For every hub, `set(ExamplesHTML[data-example-id])` equals the full canonical
  published/non-retired example set; each occurs once and joins to exactly one
  approved current image whose hashed media bytes are present in the bootstrap.
- Every initial note/media shard passes Anki database/media checks before
  reviews. Reimporting it or a delta creates zero cards, changes zero schedules,
  changes no deck configuration, and redelivers no media; sequence gaps and
  schema mismatches fail closed.
- Retrying or racing a top-up creates zero duplicate batches, examples, assets,
  notes, or releases. A +3 test atomically publishes exactly three new fluency
  cards/images, updates one hub, and leaves every old card untouched; failure
  of one asset publishes none.
- A corrected non-weak evaluation cancels every pre-publication state and
  leaves allocated draft IDs unprojected; the same correction after the atomic
  publication boundary retains/delivers content but opens no automatic round.
- A baseline Flag 1 changes no historical aggregate. One exact post-cutover
  transition creates one flag epoch and diagnosis, excludes at most its one
  linked Again/Hard, is consumed once, and cannot rearm until non-1 is observed.
  Ambiguous headless attribution excludes nothing.
- A study-day rebuild using the recorded timezone/rollover and mapping/policy
  versions reproduces the same daily facts and evaluation. Hub and diagnosis
  reviews never affect weakness, and relearning Again is not counted as a new
  lapse. A late mapping/flag link appends a new revision for the linked review
  day while the original decision remains replayable.
- Every diagnosis carries an immutable profile/evidence snapshot. Zero-to-three
  practice slots are all explicitly produced, linked, or rejected—none vanish
  through `ON CONFLICT DO NOTHING`.
- Deleting a video leaves the expression, examples, assets, and visible source
  title/URL intact. Every repeat occurrence is recorded even when teaching
  generation is deduplicated.
