# Codex WP-C1: sense-resolution evidence pass (read-only)

You are executing work package C1 of
docs/commissions/HUB_BUILD_EXECUTION_COMMISSION.md. Read that file and
docs/research/EXPRESSION_HUB_MIGRATION.md §identity/direction rules
first. This is ANALYSIS ONLY: you must not modify any collection file,
any DB, or any file outside `docs/research/hub_manifest/`.

## Inputs (local, read-only)

- Collection copy: `docs/research/anki_reorg_work/live_cutover_20260807T072826Z/collection.anki2`
  (open SQLite `mode=ro&immutable=1` ONLY).
- Frozen collision manifest: same dir, `duplicate_manifest.json`
  (2,665 exact surface groups + metadata) and `duplicates.md`
  (incl. the 25 manual-review candidates).
- Estate inventory for deck-origin context: same dir, `inventory.json`.

## Task

For EVERY collision group and every manual-review candidate produce an
evidence bundle and ONE proposed disposition:

- `same-sense-merge` — the candidates demonstrably express one
  expression-sense (same lemma set, compatible glosses, contexts that
  paraphrase the same sense). List the proposed survivor identity
  (normalized surface + gloss) and every member note id.
- `distinct-senses` — surface equality but distinguishable senses or
  task identities; explain the distinction in one sentence each.
- `quarantine` — ANY doubt, mixed evidence, damaged text, or
  cross-generation ambiguity. Doubt ALWAYS wins: prefer quarantine.

Evidence per bundle: normalized target+EN surfaces; member note ids,
GUIDs, models, current decks; source-video ids/titles where the note
carries them (tags/fields); per-member review stats (reps, lapses, last
review, ivl) aggregated from the copy's revlog; and which members are
suspended archive tasks vs active fluency cards.

## Outputs (the only files you may write)

- `docs/research/hub_manifest/C1_sense_resolution.json` — machine
  manifest: {generated_at_source_sha, groups: [{group_id, disposition,
  confidence, survivor?, members: [...], evidence: {...}}]}. Include the
  collection copy's SHA-256 you actually read.
- `docs/research/hub_manifest/C1_sense_resolution.md` — human summary:
  counts by disposition, the full quarantine list with one-line
  reasons, and the 25 manual-review candidates each with a paragraph.

## Rules

- Deterministic and reproducible: no network, no LLM-of-your-own calls
  for linguistic judgment beyond your own reasoning; when linguistic
  judgment is uncertain, quarantine.
- Proposals never merge anything: phase 5 applies them only after the
  owner's Monday skim.
- Print a final one-paragraph summary with the three counts.
