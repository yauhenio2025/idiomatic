# Expression-hub migration mapping

Status: proposed migration, study only
Date: 2026-08-07
Evidence snapshot: Anki automatic backup
`backup-2026-08-07-10.18.10.colpkg`; no live collection was modified.

This document maps the expression-related estate into the two note types in
[the design](EXPRESSION_HUB_DESIGN.md). It also states which material remains
outside the hub. All counts are observations, never constants for a future
script; the script must inventory its own input backup again.

## 1. Snapshot findings that change the plan

- `Idiomatic Cloud Card v2` is not 21 fields in the collection. It has the
  documented 21-field prefix plus a trailing `StructuredHtml`, for 22 fields
  under model ID `1820120100`.
- `YouTube Expression Pool v1` has 20,231 one-note/one-card sentence notes:
  3,161 under legacy `Languages` and 17,070 under `Idiomatic`. Of these, 1,577
  have intervals over 21 days. These cards must be converted one-for-one, not
  merged into six-card notes.
- The two Idiom Audio model IDs were historically reused. They now have two
  templates and malformed card multiplicity, including duplicate cards. They
  must be frozen and suspended intact, never normalized by deleting a template.
- `IdiomId` is not `expressions.id`: Cloud per-video notes use a video-local
  ordinal; pooled Cloud notes use `expression_idioms.id`.
- The current and legacy sources yield 3,476 candidate expression identities,
  with 24 cross-generation overlaps. Cloud v1 adds no unique normalized
  expressions. Twenty-one current per-video expressions are absent from the
  current pool; 50 legacy French expressions exist only in the audio family.
- Across hub example fields, 471 unique sentence pairs have no existing
  fluency note. Those that remain canonical after reconciliation receive new
  sentence cards/schedules; any separately adopted incompatible-direction raw
  phrase also receives a new schedule rather than borrowing the old one.
- Exact normalized target-sentence overlap between the legacy and current
  fluency pools was zero in this backup. The collision policy is still required
  for later data and non-exact duplicates.

## 2. Target models and migration manifest

Target models:

| model | proposed ID | cards per note |
|---|---:|---:|
| `Idiomatic Expression Hub v1` | `1820180001` | 1 |
| `Idiomatic Expression Example v1` | `1820180002` | 1 |

Before any collection mutation, build a normalized manifest with a collection
checksum and these lossless parts:

```text
notes:
  profile_key, old_nid, old_guid, duplicate_guid_group, old_mid, old_model,
  model_schema_hash, field_names_in_order, raw_flds, raw_flds_hash, tags,
  sfld, csum, note_flags, note_data, note_mod, note_usn, media_references

cards (one row per old card):
  profile_key, old_cid, old_nid, old_deck_id, old_deck_name,
  old_template_ord, card_mod, card_usn, type, queue, due, ivl, factor,
  reps, lapses, left, odue, odid, flags, card_data, raw_card_row_hash,
  revlog_count, ordered_revlog_hash

mapping:
  old_nid, old_cid, expression_id, example_id, canonical_example_id,
  target_creation_key, target_kind, target_model, target_deck, action,
  duplicate_of_note_id,
  mapping_reason, confidence, reviewer, post_note_hash, post_card_hash

targets (including rows with no predecessor):
  target_creation_key, predecessor_nid_or_null, expression_id, example_id,
  target_guid, target_model_id, target_deck_id, target_template_ord,
  action, allocated_post_nid, allocated_post_cid, post_note_hash,
  post_card_hash, binding_status

media:
  referenced_name, source_note_ids, source_path_if_known, size, content_hash,
  target_name, target_disposition
```

Store the literal note field blob as well as parsed named fields; model names
and ordinals alone cannot reconstruct malformed legacy notes. The manifest is
the rollback/audit contract and the source for `anki_note_bindings`, whose key
is `(profile_key, note_id)`, not GUID. No migration step may proceed with an
unresolved active card, an unclassified duplicate GUID, or an unhashed media
reference. Such rows are quarantined, never guessed.

## 3. Canonical identity resolution

Resolve `ExpressionId` in this order:

1. existing server crosswalk/recomputed known GUID;
2. direct current DB join through `expression_examples.id` or
   `expression_idioms.id` when the old field is known to carry that type;
3. exact `(lang, normalized expression, normalized target sentence)` against
   current examples;
4. exact `(lang, normalized expression)` plus source YouTube ID/URL;
5. `adopted_notes` GUID and verbatim fields;
6. reviewed alias candidate, including citation form and sense check;
7. new adopted expression row if the note is genuinely expression-bearing;
8. quarantine if none is defensible.

Never copy `IdiomId` directly into `ExpressionId`. Never merge solely on
accent-stripped/citation-form equality: homographs and polysemy need a sense
check. Candidate lookup uses `(lang, normalized)` but final identity also uses
a reviewed stable `sense_key`; ambiguity is quarantined. Current as-spoken
expression IDs remain stable in phase 1; citation forms become display
text/aliases, not silent new identity.

Every legacy/orphan example must receive a durable `expression_examples.id`
before image generation or target-note creation. Existing example IDs remain
unchanged.

## 4. Scheduling and GUID rules

### 4.1 What “preserve” means

For an active, task-compatible, one-template-to-one-template fluency
conversion, preserve note ID/GUID, card ID, and every revlog row. Preserve
`type`, `queue`, `due`, `ivl`, `factor`, `reps`, `lapses`, `left`, `odue`,
`odid`, flags, and opaque `cards.data`/FSRS state byte-for-byte. The approved
deck move changes only `did`; the supported conversion changes only note
model, fields/tags, and ordinary bookkeeping clocks.

For a retired source card, suspension changes `queue` to suspended and its
archive move changes `did`. Its note/model/GUID, due/type/interval/FSRS payload,
flags, and revlog remain intact. The manifest records both sanctioned deltas.
Do not begin while a candidate card is in a filtered deck: resolve that state
and recensus first rather than disturbing `odid`/`odue`.

Export/reimport with scheduling, note merging, card reparenting, template
deletion, or reconstructed schedules cannot satisfy this contract. All hubs
and examples without a compatible predecessor are genuinely new schedules.

### 4.2 Task compatibility and duplicates

Every Hub card is new. The old Cloud/Idiom cards put explanation/gloss or
listen-and-learn material into the retrieval task, so none is a valid donor for
the new expression-only front. Suspend all of them in their frozen source
models after harvesting evidence. Even the 38 mature legacy hub cards keep
their schedules only as inactive history; schedules are never transferred
between tasks.

Resolve sentence candidates to durable example IDs first. The active
cardinality is one fluency note/card per canonical published example ID. When
two old cards represent the same `(lang, expression sense, normalized target,
normalized English)` learning object, choose the canonical example row after
review, keep the most-invested compatible sentence card active, point the
other retained row at `canonical_example_id`, and suspend its card intact.
Sentence equality alone never merges different expression senses. Telemetry
maps every archived card to its expression but never combines schedules or
pretends the duplicate was an additional distinct example.

No note or media is deleted by this migration. A later owner-approved cleanup
may consider verified unstudied duplicates from the manifest.

### 4.3 GUID outcomes and duplicate-GUID gate

| case | GUID rule | schedule |
|---|---|---|
| every new Hub note | `sha1("idiomatic-expression-hub-v1::<lang>::<expression_id>")[:16]` | new |
| compatible migrated fluency note | retain old GUID and register `(profile, note_id)` binding | retained |
| compatible EN→TL raw-phrase migration | retain old GUID and binding | retained |
| missing/new example or incompatible-direction replacement | `sha1("idiomatic-expression-example-v1::<example_id>")[:16]` | new |
| old hub/didactic or redundant studied note | retain old GUID/model; suspend | retained but inactive |
| discontinued audio note | retain old GUID/model/cards; suspend | retained but inactive |

The inspected backup already has two duplicate GUID pairs in Cloud v2:
`076136669e70b042` (`Ma che cazzo`) and `e709362866daa03b` (`Ma dai`). All four
notes are unstudied old-hub evidence, so classify and retire them by note/card
ID without rewriting their GUIDs. This is why neither the manifest nor
`anki_note_bindings` may use GUID as a primary key.

Before target creation, prove that every deterministic new GUID is absent from
the entire collection. For every GUID a target APKG will emit, require
`COUNT(all collection notes WHERE guid = target_guid) = 1` after migration,
including suspended/archive notes in that count. If a fresh census finds a
duplicate GUID involving an active fluency candidate, stop for explicit
per-note remediation; do not pick one by GUID or silently mint a schedule
replacement. The known Cloud pairs are safe only because no target release
emits those GUIDs. Later builders consult the active binding table and retain
migrated GUIDs rather than recomputing them.

## 5. Field-by-field mappings

### 5.1 `YouTube Expression Pool v1` — 7 fields

Model ID `1820114700`; 20,231 notes/cards; existing template `EN → target`
(Unicode arrow), ordinal 0. The proposed target template is separately named
`EN -> target`.

Action: for each resolved canonical winner, require a durable example ID and
approved image, then convert in place to `Idiomatic Expression Example v1`,
mapping old template 0 to new template 0. Suspend duplicate losers according
to section 4.2; unresolved/adopted content is not activated until its ID and
image exist.

| old field | target field/action |
|---|---|
| `English` | `English` |
| `Target` | `Target` |
| `EnglishAudio` | `EnglishAudio`; retain existing media reference |
| `TargetAudio` | `TargetAudio`; retain existing media reference |
| `Idiom` | resolve hub; copy reviewed display fallback to `Expression` |
| `IdiomEn` | copy fallback to `GlossEN` |
| `Source` | normalize visible title/URL into `SourceHTML`; also persist source row |
| derived | add `ExpressionId`, `ExampleId`, `Lang`, approved `Image`, `Origin`, blank spares |

The note GUID and card ID remain unchanged. Existing text-derived GUIDs are
not recomputed even if punctuation differs. The snapshot has 471 unique hub
sentence pairs with no existing fluency note; after reconciliation, each
canonical missing example gets one new ID-derived note/card and a new schedule.

### 5.2 `Idiomatic Cloud Card v2` — actual 22 fields

Model ID `1820120100`; 5,312 notes: pooled, per-video, and archive copies;
one `Idiom practice` template. These are migration evidence, not Hub donors.
Harvest every field into canonical server rows, create all Hub notes fresh,
then suspend these notes/cards in their unchanged source model.

| old field | target/action |
|---|---|
| `IdiomId` | provenance only; resolve its type by deck/source; never copy as hub ID |
| `Idiom` | `Expression` candidate/alias |
| `IdiomEn` | `GlossEN` candidate |
| `Explanation` | evidence for the one-line compression job; not copied verbatim |
| `Example1En` | resolve/create example 1 `en_text` |
| `Example1Target` | resolve/create example 1 `target_text` |
| `Example2En` | resolve/create example 2 `en_text` |
| `Example2Target` | resolve/create example 2 `target_text` |
| `Example3En` | resolve/create example 3 `en_text` |
| `Example3Target` | resolve/create example 3 `target_text` |
| `Example4En` | resolve/create example 4 `en_text` |
| `Example4Target` | resolve/create example 4 `target_text` |
| `Example5En` | resolve/create example 5 `en_text` |
| `Example5Target` | resolve/create example 5 `target_text` |
| `Example6En` | resolve/create example 6 `en_text` |
| `Example6Target` | resolve/create example 6 `target_text` |
| `SourcePhrase` | source occurrence sentence TL; retained in DB, not an automatic illustrated example |
| `SourceEn` | source occurrence sentence EN |
| `FrontAudio` | retire long stitched audio from active target; preserve in source/archive until media audit |
| `BackAudio` | same |
| `Source` | parse/deduplicate title, YouTube ID, and visible URL into source rows/`SourcesHTML` |
| `StructuredHtml` | parse citation/usage/synonym/false-friend evidence; retain full original in DB archive |

The fresh target Hub fields are compiled from canonical DB rows:
`ExpressionId`, `Lang`, `Expression`, `GlossEN`, `UsageLineEN`, optional
`KeySynonym`/`FalseFriend`, `ExamplesHTML`, `SourcesHTML`, and blank spares.
Every old note becomes a suspended alias/evidence row; any deletion remains a
separate owner-approved cleanup.

### 5.3 Legacy 21-field Idiom family

Identical field mapping to the 21-field prefix above, with no
`StructuredHtml` field:

| model ID | model | notes in snapshot |
|---:|---|---:|
| `1820114600` | `YouTube Idiom Card v2` | 171 |
| `1820114900` | `YouTube Idiom Card v3 Structured (de)` | 47 |
| `1820114701` | `YouTube Idiom Card v3 Structured (fr)` | 32 |
| `1820114702` | `YouTube Idiom Card v3 Structured (it)` | 23 |
| `1820114902` | `YouTube Idiom Card v3 Structured (it)+` | 16 |
| `1820114703` | `YouTube Idiom Card v3 Structured (pt)` | 17 |
| `1820114903` | `YouTube Idiom Card v3 Structured (pt)+` | 31 |
| `1820114704` | `YouTube Idiom Card v3 Structured (es)` | 32 |
| `1820114904` | `YouTube Idiom Card v3 Structured (es)+` | 48 |
| `1820114901` | `YouTube Idiom Card v3 Structured (fr)+` | 0 |

The word “Structured” in these model names does not add a field. Structured
content may be embedded in `Explanation`; parse it conservatively. Thirty-eight
legacy cards were mature. Preserve those schedules and revlogs intact but
inactive; the new expression-front Hub task still receives a fresh schedule.

### 5.4 Malformed 27-field experiment family

Models:

- `1820114602` `YouTube Idiom Card v2 (Piper)`: 1 note;
- `1820114603` `YouTube Idiom Card v2 (ElevenLabs Flash)`: 0 notes;
- `1820114604` `YouTube Idiom Card v2 (Gemini Flash TTS)`: 12 notes.

Like every other old hub/didactic family, these rows supply DB evidence only;
they are never converted into or used to schedule a Hub note.

Map strictly by field name, never by ordinal:

| old field | target/action |
|---|---|
| `Idiom` | `Expression` candidate |
| `IdiomEn` | `GlossEN` candidate |
| `Explanation` | compression evidence |
| `Example1En` ... `Example6En` | corresponding example English text |
| `Example1Tg` ... `Example6Tg` | fallback target text only when canonical target field is empty |
| `SourcePhrase` | source sentence TL |
| `SourceEn` | source sentence EN |
| `FrontAudio` | archive long composite |
| `BackAudio` | archive long composite |
| `Source` | source provenance |
| `Example1Target` | preferred example 1 target |
| `Example6Target` | preferred example 6 target |
| `Example3Target` | preferred example 3 target |
| `IdiomId` | local/provenance value only |
| `Example4Target` | preferred example 4 target |
| `Example2Target` | preferred example 2 target |
| `Example5Target` | preferred example 5 target |

If a `Target` and `Tg` value both exist and disagree beyond trivial HTML or
whitespace normalization, quarantine the note for review.

### 5.5 `Idiomatic Cloud Card v1` — 8 fields

Model ID `1820120000`; 201 notes; 16 studied cards.

| old field | target/action |
|---|---|
| `PhraseId` | video-local ordering only; drop from target |
| `Phrase` | expression candidate/alias |
| `English` | gloss candidate |
| `StructuredHTML` | parse labels into compression evidence; retain original |
| `ExamplesHTML` | parse ordered sentence pairs; reconcile before creating examples |
| `FrontAudio` | archive long composite |
| `BackAudio` | archive long composite |
| `Source` | source title/URL text |

This model added no unique normalized expressions in the snapshot. Its 16
studied schedules remain intact in the retired source model; its fields are
alias/compression evidence only, never schedule donors for the new Hub task.

### 5.6 Discontinued 5-field audio models

| model ID | model | notes/cards |
|---:|---|---:|
| `1820114800` | `YouTube Idiom Audio Target→EN v1` | 3,381 / 6,565 |
| `1820114801` | `YouTube Idiom Audio EN→Target v1` | 3,276 / 6,064 |

Fields:

| old field | harvest/action |
|---|---|
| `Target` | expression alias/candidate |
| `English` | gloss fallback |
| `FrontAudio` | retain only in frozen archived note/media inventory |
| `BackAudio` | retain only in frozen archived note/media inventory |
| `Source` | source provenance fallback |

Do not convert these notes. Both model IDs have two templates in the
collection, and note card counts range from one to three. Suspend every card
and move it to the retired-audio archive with all scheduling intact. Never
delete/change a template, never choose one of these cards as a hub donor, and
never resume either builder.

The 50 French expressions found only in this family are adoption candidates,
not automatic empty hubs. For each reviewed genuine expression, create the
server expression/source first, generate and approve the normal six initial
examples with new IDs/audio/images, then create fresh Hub and Example cards.
Otherwise leave the legacy audio note as archived evidence. Its old directional
schedule is never transferred in either outcome.

### 5.7 Raw legacy phrase models

| model ID | model | fields | notes |
|---:|---|---|---:|
| `1820114200` | `YouTube Audio Phrase v3` | `PhraseId`, `Target`, `English`, `TargetAudio`, `BackAudio`, `Source` | 188 |
| `1820114400` | `YouTube Audio Phrase Reverse v1` | `PhraseId`, `Target`, `English`, `EnglishAudio`, `ReverseBackAudio`, `Source` | 6 |

These are source transcript chunks, not reliably annotated trigger examples.
Run a bounded extraction job using the sentence, companion per-video idiom
notes, video/slug, and `PhraseId`. Direction is part of compatibility:

| family/field | disposition |
|---|---|
| both `PhraseId` fields | source-local provenance in manifest/source row; never `ExpressionId`/`ExampleId` |
| both `Target`, `English` | candidate target/English sentence pair; exact content stored on the resolved example |
| v3 `TargetAudio` | reusable target-sentence audio only after byte/text hash validation |
| v3 `BackAudio` | frozen composite/source media; not mapped automatically |
| Reverse `EnglishAudio` | reusable English-sentence audio after validation |
| Reverse `ReverseBackAudio` | target audio only if proved atomic and text-matched; otherwise frozen composite |
| both `Source` fields | parsed title/URL/source key plus original field retained as evidence |

- `YouTube Audio Phrase v3` tests target/audio → English, so it cannot donate
  its schedule to the required English → target fluency task. If one trigger
  is confidently identified, create/attach the example row, commission its
  image, preserve `TargetAudio` for reuse only after sentence/hash validation,
  and generate `EnglishAudio` if needed. Reuse an already active compatible
  Example binding when one exists; otherwise create one new Example note/card
  with a new schedule. Keep the old note/card suspended intact. `BackAudio`
  remains archived unless a media audit proves it is an atomic reusable
  sentence file.
- `YouTube Audio Phrase Reverse v1` is direction-compatible. If one trigger is
  confidently identified and the exact sentence, audio, example ID, and image
  all validate, convert it one-for-one and retain its GUID/card/schedule:
  `English` → `English`, `Target` → `Target`, `EnglishAudio` → `EnglishAudio`,
  and validated atomic `ReverseBackAudio` → `TargetAudio`. Otherwise archive
  the composite back audio and generate atomic target audio before conversion.
- general listening material or ambiguous rows remain unchanged and suspended
  under `zz Dormant::z-archive`, keyed in the manifest by note/card ID.

Do not create a fake hub whose “expression” is the whole transcript sentence.

Three empty historical notetypes still receive an explicit future-proof
mapping:

- `1820114000` `YouTube Audio Phrase` has `PhraseId`, `Portuguese`, `English`,
  `TargetAudio`, `EnglishAudio`, `Source`, `Target`. Treat `Target` (falling
  back to `Portuguese`) as the TL sentence; retain both atomic audio fields
  only after text/hash validation and, because no card exists, create a fresh
  EN→TL Example note only after confident expression/example resolution.
- `1820114100` `YouTube Audio Phrase v2` has `PhraseId`, `Target`, `English`,
  `TargetAudio`, `EnglishAudio`, `Source`. Apply the same fresh-note rule.
- `1820114500` `YouTube Idiom Card v1` has `IdiomId`, `Idiom`, `IdiomEn`,
  `Explanation`, three EN/Target example pairs, `SourcePhrase`, `SourceEn`,
  `FrontAudio`, `BackAudio`, `Source`. Apply the 21-field hub mapping for
  examples 1-3.

They have no cards or schedules in this snapshot and can be removed only
during the later empty-notetype estate cleanup.

### 5.8 `Idiomatic Rescue Comics v1`

Model ID `1738264931`; fields `ItemId`, `Lang`, `Idiom`, `Gloss`,
`SentenceFront`, `SentenceBack`, `Image`; 10 studied cards.

Resolve/add `rescue_items.expression_id` using `Lang` + `Idiom`. Register the
image as a `rescue_asset` by default. Promote/copy it into the example-asset
registry only when both sentence sides resolve exactly to an existing example
row and the image passes that row's asset checks; never use fuzzy sentence
matching. Keep the rescue note/card and scheduling in the language's
`7 Rescue` branch. It is not converted into a hub or base fluency card, and
its reviews do not feed expression weakness.

### 5.9 Non-hub language models

These models get deck moves only and no expression ID:

- active-language Pimsleur: German `1808125000`, Spanish Spain `1808126000`,
  Spanish Latin America `1808133000`, French `1808128000`, Italian
  `1808127000`, Portuguese `1808124000`;
- Mandarin Pimsleur `1808123000` and every Mandarin-specific model;
- grammar, Exercises v1, tenses, translation, and podcast models;
- Lex-Stage, which remains entirely untouched.

Danish, Dutch, Norwegian, and Swedish Pimsleur models move under
`zz Dormant::Pimsleur`. They are not expression-hub data.

## 6. Long explanation compression job

### 6.1 Inputs per canonical expression

- expression ID/sense key, language, display/citation/as-spoken forms, current
  gloss;
- every distinct `Explanation`/`explanation_en` candidate;
- structured JSON and parsed `StructuredHtml`/`StructuredHTML` labels;
- source sentences and every reconciled example pair (up to six per old fixed
  field note, plus any other canonical evidence);
- known-language profile, but only for concrete false-friend checks;
- source note IDs, GUIDs, field hashes, and collection checksum as evidence
  references; note ID disambiguates the known duplicate GUIDs.

### 6.2 Strict output

```json
{
  "expression_id": 439,
  "usage_line_en": "One sentence, at most 24 words.",
  "key_synonym": null,
  "false_friend_note": null,
  "confidence": "high|medium|low",
  "evidence_refs": ["note:12345:Explanation:sha256"],
  "review_reason": null
}
```

Rules:

- `usage_line_en` is exactly one English sentence, at most 24 words, saying
  when/how the expression is used or what choice the gloss alone misses;
- no literal-history paragraph, generic praise, example list, or repeated
  gloss;
- `key_synonym` appears only when naming and distinguishing it changes what
  the learner would say;
- `false_friend_note` appears only for a concrete confusion with English or
  one of the learner's known languages;
- do not invent a claim absent from the evidence. Missing/contradictory
  evidence yields low confidence and review, not fluent fabrication.

Run at temperature zero with a versioned prompt/model. Idempotency key:

```text
sha256(expression_id + sorted_input_hashes + profile_version + prompt_version)
```

Mechanical gates enforce one sentence, word limit, no unsafe HTML, and valid
JSON. Audit all low-confidence/contradictory rows plus a stratified language
sample before publication. Store outputs alongside—not over—the original long
explanations.

## 7. What leaves the active cards

| material | target disposition |
|---|---|
| long explanation paragraphs | compressed to `UsageLineEN`; originals remain DB evidence |
| full structured stylebook block | only high-value synonym/false friend rendered; full data retained for diagnosis/rescue |
| stitched `FrontAudio`/`BackAudio` | absent from new cards; frozen source notes/media retained until separate media cleanup |
| idiom-only directional audio cards | suspended/archive intact |
| per-video deck names | removed; title/URL preserved in fields and source tags |
| video-local `PhraseId`/`IdiomId` | excluded from target identity; retained in manifest/source evidence |
| source occurrence sentence | retained in DB provenance; not automatically promoted to illustrated practice |
| six fixed example fields on hub | replaced by compiled `ExamplesHTML` plus canonical subordinate example notes |
| obsolete model-specific tags | translated to stable language/expression/example/source tags; originals retained in manifest |

“Absent from the active card” is not “immediately delete the source data.” A
media deletion is a later, independently reviewed estate operation.

## 8. Deck mapping

For each language root (`DE German`, `ES Spanish`, `FR French`, `IT Italian`,
`PT Portuguese`):

| current family | destination |
|---|---|
| all active `Fluency Expressions` cards | `<root>::1 Expressions::1 Fluency` |
| all newly created Hub cards | `<root>::1 Expressions::2 Expression Focus` |
| per-video Cloud/Idioms and other old-hub cards | suspended under `zz Dormant::z-archive` |
| old target→EN Idioms Audio | suspended under `zz Dormant::Retired Idioms Audio::<LANG>::target to EN` |
| old EN→target Idioms Audio | suspended under `zz Dormant::Retired Idioms Audio::<LANG>::EN to target` |
| diagnosis practice | `<root>::4 Exercises::Diagnosed trouble spots` |
| Rescue Comics | `<root>::7 Rescue` |
| Pimsleur for that language | `<root>::8 Pimsleur` |

Source fields and `source::youtube::<id>` tags replace per-video deck branches.
This study's direction/identity review refines the estate study's generic
sentence-family move: Phrase v3 is archived or replaced with a fresh EN→TL
card, while only validated Reverse v1 can keep an active schedule.
It also supersedes the estate draft's current `EXPRESSION_MODELS` rule, which
would move old Cloud/Idiom cards into active `Expression Focus`. Before joint
execution, update that estate mapping/script to archive every old hub model and
reserve `Expression Focus` for new model `1820180001`; otherwise the two plans
conflict.

## 9. Migration phases and rollback boundaries

### Phase 0 — freeze and census

- pause every expression pool/per-video/audio builder and APKG import;
- finish one ordinary Anki sync, quarantine every other client, require no
  filtered-deck candidate, then create a new post-sync backup/copy rather than
  assuming the newest earlier automatic backup contains that sync; never open
  the live profile path from a migration script;
- record collection/database/media checksums, Anki version and schema, profile
  key, timezone/rollover settings, and a declared telemetry cutover timestamp;
- rebuild the full manifest, notetype/template inventory, duplicate-GUID
  groups, media-reference set, revlog hashes, and before-schedule rows from that
  exact copy;
- recheck that target model IDs `1820180001` and `1820180002` and all proposed
  deterministic GUIDs are unused.

Immediately before Phase 4, recalculate the authoritative desktop's note,
card, revlog, flag, and schedule fingerprints and require exact equality with
this manifest baseline. Any intervening review, edit, flag, or sync invalidates
the plan and returns to Phase 0.

Rollback: none needed; read only.

### Phase 1 — canonical server and FK staging

1. **Expand under the existing physical names.** With all mutating jobs paused,
   add nullable direct `expression_examples.expression_id`, replacement
   `source_id`/`position`, status/stable/canonical keys, source fallback/key
   columns on the still-named `expression_idioms` table,
   `expressions.sense_key`, and the new asset/binding/telemetry tables. Do not
   rename/drop anything or change an ID.
2. **Backfill and review.** Copy video title/URL and legacy text, assign a
   deterministic `source_key`, set `source_id = idiom_id` and `position = ord`,
   and derive each example's direct expression ID. Backfill current sense keys
   as `legacy-primary`; stage (but do not yet insert) any same-normalized
   polysemy split. Resolve required NULLs, duplicate positions, sense-scoped
   aliases/canonical links, and the queues for the 21 per-video-only, 50 French
   audio-only, raw-phrase, and ambiguous cases. `source_id` remains nullable
   for source-less/top-up examples.
3. **Prepare target constraints.** Build/validate unique
   `(expression_id, source_key)`, active-canonical
   `(expression_id, position)`, `(id, expression_id)` support keys, composite
   same-expression source/canonical FKs, and unique
   `(lang, normalized, sense_key)` plus a non-unique normalized lookup index.
   Target expression/source/example/canonical ownership uses
   `ON DELETE RESTRICT`; status retirement replaces deletion.
4. **Prove application readiness before contraction.** Exercise the updated
   source/example/dedup queries and the reviewed split plan against a restored
   shadow copy while every old column still exists. Deploy the target query
   code behind a DB-schema-version gate (distinct from the later Anki-profile
   marker), or use an explicitly tested compatibility view; no live writer may
   run mixed ownership schemas.
5. **Contract in one protected transaction/maintenance window.** Recheck all
   counts, then drop the old `(lang, normalized)`,
   `UNIQUE(expression_id, video_id)`, `UNIQUE(idiom_id, ord)`, `ord <= 6`, and
   cascading FKs; validate/promote the target constraints; replace the video FK
   with `ON DELETE SET NULL`; apply reviewed sense splits/reparenting; drop
   `idiom_id`/`ord`; and finally rename `expression_idioms` to
   `expression_sources`. The old cascade is never live once the new schema is
   authoritative. Flip the DB schema-version gate only after commit and before
   any writer resumes.
6. **Verify contract behavior.** Test deletion of a copied video and prove its
   source fallback text, expression, examples, and assets remain. Test that a
   source/example/expression deletion is rejected, a second reviewed sense is
   allowed, and a cross-expression source/canonical link is rejected.

Rollback boundary: take a DB checkpoint before expansion and another before
step 5. Steps 1-4 are additive/staged; the contract transaction either passes
every count or rolls back as a unit. Restore the checkpoint rather than running
old application code against a partially contracted schema.

### Phase 2 — reconcile content and all images

- resolve/adopt every migration note to an expression/example or quarantine
  it; run the reviewed one-line compression job without overwriting evidence;
- freeze and hash the illustration campaign's expected ID manifest and require
  set-equality with the ingest. Its inspected cardinality is 17,112; future
  code gates the frozen set/hash rather than hard-coding that observed count;
- ingest only a typed manifest keyed by example ID. Require exactly one row per
  expected ID, no orphan/duplicate ID, valid image bytes/MIME, content hash,
  brief hash, visual-anchor ID, and renderer/recipe fingerprint;
- copy the exact bytes to immutable content-addressed Anki media names and
  re-hash them; filename patterns and sentence matching are forbidden;
- persist/approve one pinned visual anchor per expression. If the original base
  was not retained, freeze the authored anchor/cast JSON and approve a
  reference before top-up work;
- allocate IDs and commission images for adopted legacy examples outside the
  17,112-row campaign. Do not activate any legacy/current example until it too
  has exactly one approved current image and atomic audio/text readiness.

Gate: for every accepted expression, the canonical published example set,
active fluency plan, `ExamplesHTML` IDs, approved assets, and packaged media
references are exact set-equals. Missing one asset blocks that expression; no
placeholder is allowed. Every campaign asset also has an explicit
published/projected or retained-retired disposition; a retired duplicate may
remain registered without being delivered as note media.

Rollback: staged server rows/assets can be left unpublished or removed by the
staging migration; no collection mutation has occurred.

### Phase 3 — build and verify the migration payload

- generate the two target models once from the exact ordered fields/templates
  and record their schema/template/CSS hashes;
- create stable deck IDs for `1 Fluency` and `2 Expression Focus` under every
  language root;
- build language-sharded initial manifests containing every target note and
  every referenced initial image/audio byte, including the entire initial
  image set—not merely future deltas;
- plan one fresh deterministic Hub GUID per accepted expression, one target
  Example binding per canonical published example, and explicit dispositions
  for every old note/card/media row;
- replay the whole plan twice against disposable collection copies and require
  identical output hashes plus zero unresolved rows.

Rollback: discard artifacts/copies. No live collection or release ledger has
been changed.

### Phase 4 — controlled collection-schema migration

- take another checkpoint of the authoritative desktop collection and keep all
  other clients offline;
- install the two new frozen models and target decks through the reviewed
  migration add-on/collection API, then take a post-schema checkpoint;
- treat the notetype creation/conversions as a collection schema change that
  may require a one-way full sync. Do not attempt an ordinary multi-client sync
  mid-migration.

This is the sole notetype-install window. The current broad
merge/update-always and `with_deck_configs=True` importer behavior is not
allowed for later releases.
Rollback: restore the pre-schema checkpoint while builders and clients remain
paused.

### Phase 5 — convert fluency, create missing cards, retire old tasks

- convert each compatible canonical `YouTube Expression Pool v1` winner and
  any validated Reverse-v1 winner by supported template `0 -> 0`; populate IDs,
  image, origin, source, and spare fields while retaining note GUID/card ID;
- move active converted cards to `<root>::1 Expressions::1 Fluency`; suspend
  duplicate losers without merging history;
- create new ID-GUID Example notes/schedules for the 471 reconciled missing
  pairs and any adopted/target→EN content that still has no active compatible
  Example binding after resolution;
- create every Hub note fresh under
  `<root>::1 Expressions::2 Expression Focus`; compile its all-example/image
  rail and sources only from canonical IDs;
- suspend every old Cloud/Idiom hub, both malformed Idioms Audio families, and
  incompatible/ambiguous raw phrase card in the exact archives in section 8.
  Never delete a template/card or transfer one of their schedules;
- apply the remaining approved estate deck moves only after its mapping version
  contains the hub/raw-phrase supersessions in section 8; preserve Mandarin
  internals and all Lex-Stage content.

Gate every manifest row by disposition. Converted active cards may differ only
in `did` plus note model/fields/tags/bookkeeping; retired cards may differ only
in `did`, suspended `queue`, and bookkeeping. All other card fields and ordered
revlog hashes must match. Require exactly one active Hub per expression and one
active fluency card per canonical published example; every GUID a target
release emits resolves to exactly one collection note.

Rollback: restore the phase-4 checkpoint. No server release is acknowledged.

### Phase 6 — load media, validate, and stage bindings

- install every initial media shard while the collection remains closed for
  review; verify each filename/size/hash and every note reference;
- compare note/card/model/deck totals and all post hashes with the manifest;
- run Anki's database check and media check, render sample Hub/Example cards in
  every language, and prove every canonical published example plus adopted
  asset has its referenced bytes. Every row in the frozen campaign manifest
  has either a projected reference or an explicit retained-retired
  disposition;
- replay the same migration payload and require zero new notes/cards and no
  scheduling change;
- export a signed post-migration binding manifest containing
  `(profile, nid, guid, cid, ord, expression_id, example_id, active)` for every
  target/retired mapping. Ingest it to inactive server staging and require
  set-equality with both the target-manifest rows and the migrated collection;
- write only a local `verified_pending_full_sync` marker. Do not activate
  bindings, enable builders, or record release acknowledgements yet.

Rollback: restore the pre-migration collection checkpoint and discard the
inactive binding stage. New builders/releases still refuse this profile.

### Phase 7 — full sync and pipeline cutover

- deploy the ID-based snapshot/delta builders and stop all per-video, Cloud
  didactic, long-audio, and old pool builders before reopening publication;
- make the migrated desktop authoritative and perform the expected full upload;
  then complete and verify desktop media upload. Every quarantined client
  performs both the full collection download and media sync/download, followed
  by database/media checks, before study resumes;
- after collection and media verification, transactionally activate the staged
  bindings, write the collection/profile migration marker, and record only the
  authoritative client's initial hash-verified release acknowledgement. This
  is the handoff that permits new builders;
- ordinary post-bootstrap imports must update notes, never notetypes, and never
  scheduling (`update_notes=ALWAYS`, `update_notetypes=NEVER`,
  `merge_notetypes=false`, `with_scheduling=false`,
  `with_deck_configs=false` or exact API equivalents). Fail on model hash or
  sequence/predecessor mismatch;
- verify an idempotent delta reimport and a synthetic +3 top-up on a disposable
  post-migration copy: one Hub update, exactly three new Example cards/media,
  no old schedule change;
- begin telemetry from the declared cutover with current flags as baseline.

If failure occurs before binding/marker activation, restore the checkpoint,
discard inactive bindings, and keep publication paused. After activation/full
upload, recovery is another controlled full upload from the verified backup
plus transactional revocation/replacement of the bindings, marker, and ACK;
never merge from a stale client. Deleting unstudied duplicates, old notes, or
orphan media is a later owner-approved estate operation and is not part of
this migration.

## 10. Hard failure conditions

Stop and require review if any of the following occurs:

- an existing example ID would change or disappear;
- an active target card lacks an exact expression/example ID;
- the ingest is not hash/set-equal to the frozen campaign manifest (17,112 IDs
  in the inspected snapshot), any campaign row lacks an explicit disposition,
  or any active example lacks exactly one approved current image/packaged hash;
- a Hub's `data-example-id` set differs from its canonical published example
  set, contains a duplicate, or omits an image;
- a notetype conversion changes a retained card ID, GUID, revlog row, or any
  schedule/FSRS field outside the explicit `did`/suspension exceptions;
- any GUID a target release will emit does not resolve to exactly one note
  collection-wide after migration, a deterministic new GUID already exists
  beforehand, or a legacy duplicate-GUID group is unclassified;
- an audio model template/card would be deleted;
- a source URL/title would be lost with its deck;
- a video or source deletion can still cascade to an expression/example;
- the old `(lang, normalized)` uniqueness/dedup remains authoritative, a
  reviewed same-surface sense cannot get its own stable key, or a source/
  canonical example can cross expression IDs;
- an image can be found only by fuzzy sentence matching;
- a top-up needs to reuse an old example row with materially different text;
- an initial media shard is missing, a release sequence/hash has a gap, or the
  importer would update a notetype, scheduling, or deck configuration;
- a release would be marked finalized before its content-addressed APKG and
  manifest bytes are durably committed and hash-verified;
- the signed post-migration binding set differs from either the target plan or
  actual collection IDs, or bindings/ACKs would activate before full
  collection and media sync succeeds;
- another client has unsynced changes or cannot accept the controlled full
  download;
- the new builder runs before the local migration marker is complete.
