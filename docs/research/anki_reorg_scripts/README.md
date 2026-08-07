# Anki estate reorganization scripts

These are draft migration and verification scripts for a disposable copy of the newest Anki backup. The present commission is study-only: do not run any `--apply` command until the owner approves the plan and the decisions. Never pass the live collection, a symlink, or a hard link to it.

The scripts require `--copy-path` to resolve to an uncompressed SQLite collection beneath `docs/research/anki_reorg_work/`. They reject the live profile name, conventional live `Anki2` collection paths, paths outside the repository work area, active SQLite WAL/journal sidecars, symlinks, and hard links to the known live database. Inputs and journals must live under the selected copy's own run directory. Mutation phases use Anki's public collection APIs; they do not export/reimport cards or change note models. Every phase checks scheduling/history invariants and atomically writes a durable phase journal.

## Inputs and evidence pass

Run commands from the repository root. Extract/decompress the newest automatic `.colpkg` backup into a new working directory as required by the commission; do not point these scripts at the `.colpkg` itself. Use a new copy and an empty journal directory for every rehearsal.

```bash
REORG_SCRIPTS=docs/research/anki_reorg_scripts
REORG_WORK=docs/research/anki_reorg_work
RUN_DIR="$REORG_WORK/rehearsal"
COLLECTION_COPY="$RUN_DIR/collection.anki2"
JOURNAL_DIR="$RUN_DIR/anki_reorg_journals"
COLLISION_MANIFEST="$RUN_DIR/duplicate_manifest.json"
OWNER_DECISIONS="$RUN_DIR/owner_decisions.json"
```

First reproduce the read-only inventory and freeze the duplicate manifest against the pristine copy:

```bash
python "$REORG_SCRIPTS/00_inventory.py" \
  --copy-path "$COLLECTION_COPY" \
  --json-out "$REORG_WORK/inventory.json" \
  --markdown-out "$REORG_WORK/inventory.md"

python "$REORG_SCRIPTS/generate_deck_map.py" \
  --copy-path "$COLLECTION_COPY" \
  --output "$REORG_WORK/deck_map.md"

python "$REORG_SCRIPTS/analyze_duplicates.py" \
  --copy-path "$COLLECTION_COPY" \
  --json-out "$COLLISION_MANIFEST" \
  --markdown-out "$REORG_WORK/duplicates.md"

cp "$REORG_SCRIPTS/odd_decisions.example.json" "$OWNER_DECISIONS"
```

Review the generated collision report and manifest without editing the manifest. It is a conservative exact target-plus-English match set; target-only and punctuation-relaxed candidates are excluded from automatic action. Phases 3 and 7 validate the manifest against the copy's note identity and semantic content. Record the owner's approved choices in `OWNER_DECISIONS`; the value passed to phase 7's `--policy` must be identical to `dedupe_policy` in that JSON.

## Ordered dry-run and apply sequence

For a future approved rehearsal, run each command once without `--apply`, inspect its output, then run the paired command with `--apply` on the same disposable copy. Do not skip or reorder phases: each apply after phase 1 requires its immediate predecessor's completed journal.

Phase 1 creates target shells. Save the journal path printed by the apply command as `BASELINE_JOURNAL`; final verification uses its pre-migration invariants.

```bash
python "$REORG_SCRIPTS/01_create_targets.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --decisions "$OWNER_DECISIONS"
python "$REORG_SCRIPTS/01_create_targets.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --decisions "$OWNER_DECISIONS" --apply
BASELINE_JOURNAL=/absolute/path/printed_01_create_targets_journal.json
```

Replace the `BASELINE_JOURNAL` placeholder with the exact journal path printed by the phase-1 apply command.

Phase 2 adds provenance tags before source deck names disappear.

```bash
python "$REORG_SCRIPTS/02_tag_provenance.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR"
python "$REORG_SCRIPTS/02_tag_provenance.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --apply
```

Phase 3 collapses legacy and per-video expression decks into Fluency and Expression Focus. It validates the frozen collision input but does not resolve duplicates yet.

```bash
python "$REORG_SCRIPTS/03_move_expressions.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --collision-manifest "$COLLISION_MANIFEST"
python "$REORG_SCRIPTS/03_move_expressions.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --collision-manifest "$COLLISION_MANIFEST" --apply
```

Phase 4 moves grammar, tenses, exercises, translation, F3 errors, and rescue cards.

```bash
python "$REORG_SCRIPTS/04_move_learning_families.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR"
python "$REORG_SCRIPTS/04_move_learning_families.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --apply
```

Phase 5 places Mandarin without changing its internal hierarchy, disaggregates Pimsleur, and collapses `z-archive`.

```bash
python "$REORG_SCRIPTS/05_place_mandarin_pimsleur_archive.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR"
python "$REORG_SCRIPTS/05_place_mandarin_pimsleur_archive.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --apply
```

Phase 6 moves retired long-form Idioms Audio cards to the dormant tree and suspends them.

```bash
python "$REORG_SCRIPTS/06_discontinue_audio.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR"
python "$REORG_SCRIPTS/06_discontinue_audio.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --apply
```

Phase 7 resolves only manifest-listed exact duplicates. The recommended policy is shown; replace it only with the owner's approved `canonical-model-first` or `keep-all` value, and update `OWNER_DECISIONS` to match.

```bash
python "$REORG_SCRIPTS/07_resolve_duplicates.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --manifest "$COLLISION_MANIFEST" --decisions "$OWNER_DECISIONS" --policy schedule-first
python "$REORG_SCRIPTS/07_resolve_duplicates.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --manifest "$COLLISION_MANIFEST" --decisions "$OWNER_DECISIONS" --policy schedule-first --apply
```

Phase 8 applies the approved `EXPERIMENTS-YT` choice.

```bash
python "$REORG_SCRIPTS/08_resolve_odds.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --decisions "$OWNER_DECISIONS"
python "$REORG_SCRIPTS/08_resolve_odds.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --decisions "$OWNER_DECISIONS" --apply
```

Phase 9 deletes only empty obsolete deck shells, deepest first. Its dry run is meaningful only after phases 1–8 have been applied to this copy; on the pristine copy it correctly refuses because source decks still hold cards.

```bash
python "$REORG_SCRIPTS/09_cleanup_empty_decks.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --decisions "$OWNER_DECISIONS"
python "$REORG_SCRIPTS/09_cleanup_empty_decks.py" --copy-path "$COLLECTION_COPY" --journal-dir "$JOURNAL_DIR" --decisions "$OWNER_DECISIONS" --apply
```

Finally, run the read-only verifier. It checks the complete journal chain, SQLite integrity, target and obsolete decks, Lex-Stage, intended suspensions, moved-card destinations, decision consistency, and hashes for notes, cards, scheduling, and review history.

```bash
python "$REORG_SCRIPTS/10_verify.py" \
  --copy-path "$COLLECTION_COPY" \
  --baseline-journal "$BASELINE_JOURNAL" \
  --journal-dir "$JOURNAL_DIR" \
  --decisions "$OWNER_DECISIONS"
```

Do not treat a successful rehearsal as authorization to run against the live profile. The deliverable remains the verified migrated copy plus its journals for owner inspection.

## Rollback and restart

`rollback.py` defaults to a dry run and refuses any journal except the newest active journal for that copy. Inspect first, then apply, and repeat strictly newest-to-oldest:

```bash
LATEST_JOURNAL=/absolute/path/to/newest_active_phase_journal.json
python "$REORG_SCRIPTS/rollback.py" --copy-path "$COLLECTION_COPY" --journal "$LATEST_JOURNAL"
python "$REORG_SCRIPTS/rollback.py" --copy-path "$COLLECTION_COPY" --journal "$LATEST_JOURNAL" --apply
```

The rollback restores journaled card moves, suspension state, added tags and their registry rows, phase-5 subtree renames, created shells, and the exact IDs/metadata of removed empty decks. It preflights every target before its first mutation and then requires the collection, deck-catalog, tag-catalog, and captured-card fingerprints to equal the phase's pre-state. Discarding the disposable copy and extracting another backup copy remains the simplest restart; never attempt recovery by touching the live collection.

## Read-only media analysis

`analyze_media.py` opens the copied database through SQLite immutable/read-only mode and only reads directory entry names and `stat` metadata from `--media-dir`. It has no deletion path. Prefer a copied media directory; if a live `collection.media` directory is supplied, the script still performs no media writes, but the result is only an orphan *estimate* and must never be used directly as a deletion list.

```bash
MEDIA_DIRECTORY=/path/to/copied/collection.media
python "$REORG_SCRIPTS/analyze_media.py" \
  --copy-path "$COLLECTION_COPY" \
  --media-dir "$MEDIA_DIRECTORY" \
  --json-out "$REORG_WORK/media.json" \
  --markdown-out "$REORG_WORK/media.md"
```
