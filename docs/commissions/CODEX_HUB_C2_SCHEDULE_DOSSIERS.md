# Codex WP-C2: schedule-adoption dossiers (read-only)

Work package C2 of docs/commissions/HUB_BUILD_EXECUTION_COMMISSION.md.
Read that file and docs/research/EXPRESSION_HUB_MIGRATION.md's
identity/direction/schedule-adoption rules first. ANALYSIS ONLY: write
nothing outside `docs/research/hub_manifest/`.

## Inputs (local, read-only)

- Collection copy: `docs/research/anki_reorg_work/live_cutover_20260807T072826Z/collection.anki2`
  (SQLite `mode=ro&immutable=1` ONLY).
- Estate inventory (same dir, `inventory.json`) for deck context.

## Task

The Hub's phase 5 may let a new ID-derived fluency Example card ADOPT
the schedule of its compatible predecessor instead of starting fresh.
Build the complete evidence base for that decision:

1. Enumerate every ACTIVE `YouTube Expression Pool v1` card (the
   post-estate Fluency lanes `* ::1 Expressions::1 Fluency`).
2. Per card, a dossier: note id/GUID, deck, queue/type, due, ivl,
   factor, reps, lapses, revlog row count + first/last review, and the
   note's normalized target+EN surfaces (these are the join keys to
   the future example manifest).
3. A compatibility verdict per the migration doc's direction rules:
   `adoptable` (EN→TL production task, healthy row) vs
   `fresh-schedule` (anything else, incl. zero-rep new cards where
   adoption is meaningless — mark those `fresh-trivial`).
4. Aggregate table: per language — adoptable / fresh / fresh-trivial
   counts, mature-card counts, total reps at stake.

## Outputs (only these)

- `docs/research/hub_manifest/C2_schedule_dossiers.json`
  (machine: {source_sha256, cards: [...]}, one object per card)
- `docs/research/hub_manifest/C2_schedule_dossiers.md`
  (human: the aggregate table + methodology + any anomalies found)

## Rules

Deterministic, no network. Never propose editing a revlog. Anomalies
(cards in Fluency lanes with non-Pool-v1 models, filtered-deck residue,
suspended cards inside active lanes) are REPORTED, not resolved.
Finish with a one-paragraph summary incl. the per-language counts.
