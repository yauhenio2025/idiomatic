# Expression Hub build — execution commission (coordinated tranche)

> Owner directive 2026-08-09: start the Hub NOW, structured for speed.
> Flyout is Tuesday. Sunday = build day (autonomous), Monday = owner
> gate day (verdicts + rehearsals), Monday night/Tuesday morning =
> cutover IF everything is green — else the collection-touching phases
> park cleanly until return, with zero half-states.
>
> Division of labor: **codex** = long-running mechanical analysis over
> local data; **Fable build session(s)** = schema/models/executor
> (creative, ambiguous); **coordinator session** = sequencing, review,
> verification, owner comms. Nothing touches the live collection, the
> live DB schema, or delivery behavior without a coordinator-verified
> gate; the live collection additionally always requires the owner.

## Binding inputs (read before any work)

1. `docs/research/EXPRESSION_HUB_DESIGN.md` — the accepted design
   (hub note per expression; fluency examples; Flag-1 diagnosis lane).
2. `docs/research/EXPRESSION_HUB_DECISIONS.md` — four verdicts PLUS the
   two 2026-08-08 OWNER AMENDMENTS (EN→TL expression-production card;
   per-occurrence source context clip on hub/EN card backs). Amendments
   bind at model freeze — they are not optional.
3. `docs/research/EXPRESSION_HUB_MIGRATION.md` — phase structure,
   identity/direction rules, schedule-adoption boundaries.
4. `docs/research/ANKI_ESTATE_REORG_PLAN.md` — reserved destinations
   (`1 Expressions::2 Expression Focus`, `4 Exercises::Diagnosed
   trouble spots`), §Live copy-back cutover (the proven live-run
   mechanism), COMPLETION NOTE (post-estate reality).
5. `docs/RESTRUCTURE_STATUS.md` + CLAUDE.md (estate tree contract,
   anki_root, frozen-model doctrine, TTS lanes).

## Work packages

### WP-C (codex, parallel, read-only analysis)

Inputs are LOCAL: the migrated collection copy + frozen collision
manifest under `docs/research/anki_reorg_work/live_cutover_*/`, the
estate inventory, and `docs/research/legacy_estate/manifest.json`.
Outputs to `docs/research/hub_manifest/` (JSON + MD, committed).

- **C1 — sense-resolution evidence pass**: for each of the 2,665
  surface-collision groups and the 25 manual-review candidates, an
  evidence bundle (normalized surfaces, source occurrences, deck
  origins, review history) with a PROPOSED disposition:
  `same-sense-merge | distinct-senses | quarantine`. Conservative:
  any doubt → quarantine. Proposals are input to the manifest, never
  applied directly.
- **C2 — schedule-adoption dossiers**: per compatible predecessor card
  (active Pool-v1 fluency family), the exact schedule evidence needed
  by migration phase 5 (ivl/factor/due/reps/lapses + revlog shape), and
  a compatibility verdict per the migration doc's direction rules.
- **C3 — asset coverage sweep**: map every example (server DB export
  provided by coordinator) to its QA-passed illustration status;
  produce the gap list per language and a coverage table feeding the
  render-priority queue.

### WP-F (Fable build session, branch `hub-build`)

- **F1 — durable-ID server schema**: idempotent schema.sql extensions
  for canonical expression/sense/example IDs + release manifests
  (snapshot/delta), per the design doc's tables. No destructive
  changes; boot-migration style like the estate work.
- **F2 — frozen models + PILOT**: implement models `1820180001`
  (hub note: hub card + the amended EN→TL card) and `1820180002`
  (example/fluency), templates per design §5 INCLUDING the amendments
  (context clip on backs; vertical comic rail). Then build a
  **30-expression pilot apkg** (mixed languages, real data, real
  images where QA-passed, real context clips) delivered through the
  normal pipeline to a PILOT-ONLY deck for the owner's Monday verdict.
  Pilot-first is a hard rule; no bulk generation before the verdict.
- **F3 — phase-5 production executor (draft + rehearsal)**: the
  separately-reviewed executor the estate plan requires — converts
  manifest-compatible predecessors, creates ID-derived hub/example
  cards, archives incompatible tasks, applies the copy-back mechanics
  from the estate playbook. Must run + roll back on a disposable copy
  twice before it is even shown to the owner.

### Coordinator (this session)

Sequences WP-C/WP-F, reviews every deliverable before merge to main,
exports the server-DB extracts codex needs, regenerates the fresh joint
census at cutover time, runs rehearsals, and owns all owner gates.

## Owner gates (Monday)

1. **Pilot verdict** — the 30-expression hub/EN-card pilot in Anki
   (cards, images, context audio, both directions).
2. **Quarantine skim** — C1's proposed dispositions (only the
   quarantine/merge split needs eyes, not 2,665 rows).
3. **Cutover go/no-go** — only after rehearsal passes twice; the
   collection-touching phases use the estate's proven copy-back
   choreography with the owner at the keyboard. No-go → everything
   parks: schema + models + manifest are inert until executed.

## Hard rules

- Frozen-model doctrine: once the owner approves the pilot, model IDs,
  field count/order, and template count are FROZEN before bulk builds.
- No schedule is guessed: adoption only via C2 evidence + migration
  rules; everything else gets fresh schedules; revlog is never edited.
- The 09:00–11:00 TTS window and the image miner keep their lanes; any
  new audio the Hub needs goes through the local_tts queue.
- Branch `hub-build` for WP-F; coordinator merges; suite green on every
  merge; deploys announced in CHANGELOG.
- If Tuesday arrives without the cutover: ship nothing partial. The
  pilot deck is explicitly disposable; production waits for return.
