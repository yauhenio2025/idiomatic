# Hub phase-5: compiler + executor + rehearsal record (F3)

> Built 2026-08-09 on branch `hub-build`. Everything here ran against
> CLONES of `docs/research/anki_reorg_work/live_cutover_20260807T072826Z/
> collection.anki2` (SHA-256 `485a2849…`, the exact bytes C1 and C2
> read). No live collection, live DB, or delivery surface was touched.

## Toolchain

| piece | path |
|---|---|
| pure library (joins, manifest, field plans, verifiers) | `idiomatic/hub/phase5.py` (unit-tested in `tests/test_hub.py`) |
| manifest compiler | `docs/research/anki_reorg_scripts/hub_phase5_compile.py` |
| executor (copy-only, journaled) | `docs/research/anki_reorg_scripts/hub_phase5_execute.py` |
| standalone verifier | `docs/research/anki_reorg_scripts/hub_phase5_verify.py` |
| rollback | `docs/research/anki_reorg_scripts/hub_phase5_rollback.py` |
| input checksum pins | `compiler_expectations.json` (committed) |
| compiled manifest | `phase5_manifest.json` (13.7 MB, gitignored; content sha in `phase5_manifest.json.sha256`) |

The compiler REFUSES to run when any input's checksum differs from the
committed expectations (C1 JSON, C2 JSON, server extract);
re-recording is an explicit reviewed act. The manifest carries a
self-checksum; the executor refuses a tampered manifest, a non-pristine
copy (sha must equal C2's source sha), or any conversion card whose
live schedule row has drifted from its C2 evidence.

Server extract: the committed illustration-campaign corpus export
(3,014 expressions; checksum-pinned). The C3 extract drops in via
`--server-extract` with the same `{expressions: [...]}` shape — assets
and richer fields are an enrichment layer, never a blocker.

## Manifest (content sha `bb3c0e66a2f818b0…`)

| bucket | count |
|---|---:|
| C2 cards in scope | 20,759 |
| **convert in place** → model `1820180002` | **17,530** (de 3,990 / es 2,710 / fr 2,740 / it 4,886 / pt 3,204) |
| — of which adoptable (schedule preserved) | 807, carrying 1,627 reps |
| — of which fresh-trivial (zero reps) | 16,723 |
| **fresh hub notes** → model `1820180001` | **2,925** (de 667 / es 452 / fr 457 / it 815 / pt 534) → 5,850 cards |
| join-key quarantine (owner-ratified exclusion) | 14 cards → archived + suspended |
| C1 quarantine groups (owner-ratified) | 7 groups / members stay archived untouched |
| C1 archive evidence notes (verified untouched) | 5,438 |
| **deferred untouched** (gap, see below) | **3,215** |

### The headline gap the compiler surfaced

3,215 cards join no durable server example by exact normalized
bilingual match — **3,161 of them are ADOPTABLE studied cards carrying
12,906 reps** (it 4,974 / pt 3,095 / fr 2,329 / de 1,485 / es 1,023).
These are overwhelmingly the known server-side orphan population: cards
whose `expression_examples` rows were purged or regenerated during the
July pipeline redesign (the `adopted_notes` remediation track) plus the
legacy `Languages`-generation sentences. Their durable example rows DO
NOT EXIST yet; creating them is a **server-DB write phase** (identity
ladder steps 5-7 of the migration doc) that this executor deliberately
does not perform. They are left byte-untouched in the fluency lanes and
listed per-card in the manifest's gap section.

Conversely, 16,723 of 16,790 fresh-trivial cards (99.6%) joined
cleanly — the join method is sound; the gap is missing server rows, not
join quality.

## Rehearsals (both PASS)

| run | clone | result |
|---|---|---|
| A | `anki_reorg_work/hub_rehearsal_A/` | applied 62 s; in-run gates PASS; standalone verifier PASS (0 problems) |
| B | `anki_reorg_work/hub_rehearsal_B/` | applied 72 s; verifier PASS; then **rollback drill PASS** — after rollback, every `collection_invariants` fingerprint (note content incl. flds/sfld/csum, note identity/mid, tags catalog, schedule core, queue state, revlog, deck catalog, model schema, mature/reps counts) equals the pristine before-state |

Journals + bindings exports live beside each clone under
`anki_reorg_journals/` (prepared → complete, estate-style; the bindings
export is the phase-6 `anki_note_bindings` staging payload keyed by
`(profile_key, note_id)`).

What the executor proved, gate by gate:
- frozen models installed through Anki's own apkg importer with the
  exact IDs/field order/template counts (seed notes/decks removed;
  models verified against `idiomatic/hub/apkg.py` before any note is
  touched);
- all 17,530 conversions kept note GUID, card id, every schedule field
  and `revlog` byte-identical (before/after row compare per card, plus
  collection-level revlog/reps/mature fingerprints);
- 2,925 hub notes created with deterministic production GUIDs, each
  resolving to exactly one note collection-wide, each with exactly 2
  cards, all in `<ROOT>::1 Expressions::2 Expression Focus`;
- Expression Focus decks contain ONLY model `1820180001`; fluency lanes
  contain only converted example notes + the listed deferred Pool-v1
  cards;
- no C1 quarantine member and no join-key note carries a target model;
  join-key cards archived + suspended with prior state journaled;
- deferred cards byte-untouched (row compare per card).

## Amendment-3 re-run (2026-08-09, post-F4-apply)

Owner amendment 3 (paired context transcript behind a `<details>`
reveal, consuming the Extra1 spare) changed the frozen model's
templates/CSS, and the coordinator's F4 apply changed the manifest of
record (126 production adoptions). Both rehearsals were re-run from
fresh clones against the re-sealed manifest:

| run | result |
|---|---|
| A | **17,704 conversions (933 adopted schedules / 2,180 reps)**, 2,935 hub notes / 5,870 cards, 14 archived, 3,041 deferred untouched; gates + standalone verifier PASS (0 problems) |
| B | same; verifier PASS; **rollback drill PASS** (all invariant fingerprints back to pristine) |

Amendment-specific checks: the executor-installed hub model carries the
`<details>` transcript reveal in BOTH back templates; phase-5 `Extra1`
stays blank by design — transcript + clip ship TOGETHER at release
build from the same occurrence row, so the pairing can never split.
Compiler expectations were re-verified unchanged (same pinned inputs as
the coordinator's post-apply seal); only the manifest's amendment
annotation and timestamp moved its content sha.

## Between rehearsal-pass and live execution

1. **Server-side adoption phase** (not built): allocate durable
   `expression_examples` rows for the 3,215 deferred cards (adopted
   orphans + legacy), then recompile — the same compiler/executor run
   converts them with schedules retained. This is the only path that
   recovers the 12,906 deferred reps.
2. **C3 server extract**: swap in for the campaign export
   (`--server-extract` + one expectations re-record) to enrich hub
   GlossEN/SourcesHTML server-side instead of member-field harvest, and
   to carry image/asset references.
3. **Phase-0 recensus on a fresh post-sync copy** (migration doc
   requirement; C2 itself flags the inventory-vs-copy skew): the live
   run must recompile against the frozen fresh manifests, not these.
4. **Owner at the keyboard for the live copy-back choreography**
   (estate playbook); coordinator go/no-go after rehearsal review.
5. Media/release enrichment stays out of phase 5 by design: hub
   `ContextAudio`/`ExpressionAudio`/images ship through the release
   builder (F-future), which reads the bindings + release ledger tables
   landed in F1.
6. Recovery note: a mid-run crash leaves a `prepared` journal; rollback
   accepts it with a warning, and if hub notes were created after the
   journal's last durable write, the notetype-reference guard fails
   closed — the clean path is re-clone + re-run (rehearsal-proven).
