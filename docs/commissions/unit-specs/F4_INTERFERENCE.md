# F4 cross-language interference units

F4 turns a reviewed, private contrast bank into ordinary verified
`grammar_items` with `fmt='f4'`. The source pairs never enter this public
repository. An authenticated admin upload places each raw bank in a database
staging row with one cheap insert; cron validates and batch-upserts it into the
private `f4_pairs` table. A separate bounded conversion action compiles selected
rows into cards. Deck rebuild and delivery continue through the existing grammar
pipeline.

## Final curriculum strings

These strings are final once a deck ships:

| Receiving language | Topic key | Label | Cluster | Symbol |
|---|---|---|---|---|
| Spanish | `es_interference_f4` | Contrastes entre lenguas | `10 Interferencias` | ⇄ |
| Portuguese | `pt_interference_f4` | Contrastes entre línguas | `10 Interferência` | ⇄ |
| French | `fr_interference_f4` | Contrastes entre langues | `10 Interférences` | ⇄ |
| Italian | `it_interference_f4` | Contrasti tra lingue | `10 Interferenze` | ⇄ |

Each topic has empty mood and tense, no verb inventory, and verification mode
`f4`. It is appended after that language's F3 personal-error topic. Generation
and top-up flows must treat `f4` as a static conversion mode and never send it
to an LLM.

There is no German F4 topic in this release. The reviewed evidence has only one
eligible receiving-language row, below the threshold for a useful standalone
cluster. Its data may remain uploadable and ready in the database, but no German
card is converted until more evidence arrives or product policy explicitly
accepts a one-card unit.

## Card and identity contract

The existing `Idiomatic Grammar Drill v1` model remains frozen: the model ID,
single template, 14 field names and order, CSS, and GUID formula do not change.
F4 cards use the receiving language as `Lang`, the receiving-language F4 topic,
the compiled prompt as `Sentence`, and the exact reviewed target form as
`Answer`. Stable integer `grammar_items.id` values therefore continue to produce
stable grammar GUIDs.

Pair identity is independent of mutable evidence and presentation metadata. It
is the specified SHA-256 digest of the canonical, NFC comparison tuple containing
schema version, receiving language, false target form, and correct target form.
Re-uploads preserve that identity and its linked grammar item. The external
registry's stable integer ID must also survive personal-error ingestion so a
declared projection can be checked against the named source row and its verbatim
substrings; a database-local serial ID is not an equivalent provenance key.

The reviewed bank is compiled deterministically into the approved A, B, or C
front shape. A and B use the frozen Unicode signature and uniqueness rules.
Shape C shows the two unmarked reviewed candidates in pair-key-derived order.
Every compiled `Sentence` contains exactly one `___`, and the receiving-language
form is always the answer; source-language material is context or distraction
only. No new same-frame sentence text is generated in this release, so Tier B
blind-fill verification is not invoked.

## Bank revisions and retirement

One staged JSON array is one source revision for one receiving language; mixed
receiving languages are invalid. Cron parses and attests the complete payload,
then submits the whole bank to one database transaction. It must not split a
bank into independently committed prefixes: a deterministic failure writes no
pairs, and the staging row is marked corrupt without logging private forms.
Unexpected database failures leave the staging row pending for retry.

An accepted revision marks every active pair for that receiving language dirty,
because adding one answer may invalidate an otherwise unchanged whole-bank
production signature. The compiler copies the pair row's `updated_at` revision
into private item metadata as `source_revision`; the item upsert compares that
token and all presentation-bearing fields again while holding the pair-row lock.
A converter working from an older revision therefore cannot clear the newer
revision's dirty flag. A linked F4 grammar item is withheld from deck rebuilds
while its pair remains dirty, so a failed or only partially completed bounded
conversion cannot publish a stale signature.

Bank uploads are additive upserts, not replacement snapshots. A pair absent
from a later upload remains active; omission is never a deletion or retirement
signal. Once a pair has produced a card, retirement is explicit through
`POST /admin/grammar-retire-item/{item_id}`, which retires the linked
`grammar_item` and `f4_pairs` row in the same transaction. An unconverted pair
likewise requires an explicit operator-controlled `status='retired'` update;
changing or omitting a private source file alone has no lifecycle effect.

## Deployment order

Production rollout is ordered because projection attestation depends on the
external registry IDs introduced with F4:

1. Apply the database schema, including `personal_errors.registry_id`, its
   partial unique index, and the F4 tables.
2. Re-upload the complete private personal-error registry so existing rows gain
   their stable external registry IDs.
3. Let cron ingest that registry upload and verify its staging status before
   uploading any F4 bank.
4. Upload each private F4 bank, then let cron validate its attestation and
   perform the atomic bank upsert.
5. Convert and rebuild only Spanish, Portuguese, French, and Italian. A German
   bank may be ingested for data readiness, but it has no public curriculum
   topic and must not be converted or delivered in this release.

## Deviations and assumptions

- Shape C routing uses the exact v1 category values `verb_prep_regime`,
  `preposition_selection`, `relative_pronoun`, `negation`, and `word_order`.
  Any A/B item that cannot obtain a non-revealing unique signature also falls
  back to C. Publication of the reviewed bank is treated as the human approval
  that its two C candidates instantiate the same frame.
- Shape B is a deterministic presentation of an attested leak, not an additional
  duplicate card for every pair. In v1, “high occurrence” is frozen at five or
  more represented rows. The one-pair-to-one-item source link remains the
  idempotency boundary.
- Selection is deterministic: attested rows precede family extensions, then
  represented-row count and pair key break priority ties. The private ten-field
  schema has no rollout-priority field, so the design draft's named low-frequency
  Phase-1 inclusions are not hard-coded in public code; an admin may convert a
  larger batch, or a future private schema version may add reviewed priority.
- Optional provenance fields in the frozen model remain empty unless they can be
  populated without changing the model or exposing private source material.
- F4 is text-only in this release. The existing grammar audio path would read a
  mixed-language filled front in the receiving-language voice; target-answer-only
  audio can be added later without moving audio out of frozen `Extra1`.
- German is deliberately omitted at the current one-row evidence level. Adding
  it later requires a final cluster decision before first delivery.
- Tests and documentation use synthetic records only. No reviewed pair payload,
  snapshot, fixture, or verbatim private-bank content belongs in the repository.
