# Anki estate migration — EXECUTION commission (fresh session)

> This is the execution counterpart to two completed, committed studies.
> Nothing here is design work: every decision is made, and as of 2026-08-07
> every script is rollback-tested on disposable copies (rehearsal_A phases
> 1–10 PASS; rehearsal_B full newest-to-oldest rollback, logically identical
> to pristine — evidence in the gitignored `docs/research/anki_reorg_work/`).
> Your job is to run the migration against the REAL collection, carefully,
> phase by phase, with the owner gating every phase.
>
> CORRECTION (2026-08-07): as originally written this commission claimed the
> scripts were already rollback-tested and that the plan documented a
> live-run override. Neither was true at commissioning time. The rehearsal
> has since been run (above), and the approved live mechanism — copy-back
> cutover, not an override — is now documented in the plan; see below.

## Read first, in this order

1. `docs/research/ANKI_ESTATE_REORG_PLAN.md` — the nine phases, the
   target tree, the builder-constant inventory, the rollback machinery.
2. `docs/research/ANKI_ESTATE_OWNER_DECISIONS.md` — VERDICTS section:
   all six decisions accepted; approved values in
   `docs/research/anki_reorg_scripts/odd_decisions.approved.json`.
3. `docs/research/EXPRESSION_HUB_DESIGN.md` — you are NOT building the
   hub, but the estate plan reserves deck destinations for it; do not
   repurpose them.
4. `docs/research/anki_reorg_scripts/README.md` — script usage. The
   scripts refuse live-profile paths unconditionally; there is no
   override. The real run uses the plan's "Live copy-back cutover"
   section: migrate a physical copy inside the work area, verify, then
   swap the verified file into the live profile while Anki is closed.
5. CLAUDE.md — the add-on (auto-import, auto-sync, cleanup.json
   single-slot caveat), SYLLABUS-ONLY policy, deploy mechanics.

## Execution order (do not reorder)

**Phase 0 — preconditions.** Fresh manual backup (File → Create Backup
AND copy the .colpkg out of the backups dir to /srv). AnkiWeb sync
clean (no pending conflict). Pause the add-on's import timer for the
duration (Tools → Idiomatic, or set the config flag it exposes) so a
rolling deck doesn't land mid-migration. Confirm the night image-miner
window (01:30–09:00) won't overlap your Anki work — Anki itself is
unaffected by the miner, but don't run migration phases while the owner
is asleep anyway: every phase gate needs their eyes.

**Phases 1–9 — the plan's own order, via the copy-back mechanism.**
Anki stays closed for the whole migration window; the scripts run on the
physical copy in the work area. After each phase's dry run: STOP and
have the owner inspect the printed diff at the terminal before apply.
Journal files land beside the copy as in the drills; never delete them.
Any mismatch → run the tested rollback for that phase, diagnose in a
fresh disposable copy, only then retry. The owner's in-Anki checkpoint
happens once, after `10_verify.py` passes and the verified file is
swapped into the live profile (the displaced original is kept as
`collection.anki2.pre-estate-<ts>` — the live-step rollback).

**Sync discipline.** After phase 9 verifies: AnkiWeb "Upload to
AnkiWeb" (full upload) once, deliberately — deck moves at this scale
can exceed incremental sync; the add-on's sync guard will nag rather
than auto-answer, which is correct. The owner confirms the iPad pulls
the new tree cleanly before you proceed to builders.

**Builder constants — repo side, AFTER Anki side is verified.** The
plan §builder-inventory lists every deck-name constant (grammar,
exercises2, translation, tenses, tenses_ex, rescue_comics, pool decks)
and the new names under the language roots. Change them in one commit,
suite green, deploy, then force one rebuild per family
(`/admin/*-build`, `/admin/rebuild-pools`) and verify the add-on
imports land INSIDE the new tree (no duplicate old-name trees). The
old empty rolling decks left behind get cleaned by the plan's final
sweep phase.

**Hand-off.** Update CLAUDE.md's deck-name references, CHANGELOG, and
append a completion note to the reorg plan. The Expression Hub build
(separate commission, not yours) starts only after this lands.

## Hard rules

- The owner is present for every phase gate. No batching phases to
  "save time"; the checkpoints ARE the safety design.
- Never run migration scripts and a rolling-deck import concurrently.
- Scheduling/review history is sacred; if any verifier reports drift,
  stop and roll back — no "probably fine".
- Coordination: the repo is shared with parallel automation (night
  image miner pulls it; TTS bridge session may deploy). Announce your
  deploy windows in CHANGELOG commits; don't deploy while another
  session's batch rides the server.
