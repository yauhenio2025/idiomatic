# Codex HUB-C4: orphan expression-creation proposals (read-only)

The Hub's F4 phase left 3,047 studied cards deferred as
`no-expression-match` (3,041 adoptable, 12,367 reps): their idiom
surfaces don't exist among server expressions — the legacy
EXPRESSION-level backlog. Converting them later requires creating new
expressions (owner-gated, pilot-first). Your job: the complete
evidence + proposal manifest that creation wave will consume. Write
only to `docs/research/hub_manifest/C4_*`.

## Inputs (read-only)

- `docs/research/hub_manifest/ADOPTION_PLAN.md` + the local
  `adoption_plan.json` (the deferred list with note ids).
- `docs/research/anki_reorg_work/live_cutover_20260807T072826Z/collection.anki2`
  (`mode=ro&immutable=1`) — the deferred notes' full fields (idiom
  surface, gloss, example sentence pairs) and per-card schedule
  evidence.
- `docs/research/hub_manifest/C1_sense_resolution.json` normalization
  conventions — reuse the estate normalization exactly.

## Task

1. Cluster the 3,041 cards' notes by normalized (lang, idiom surface)
   → candidate expressions. Within a cluster, group distinct example
   sentences; reps/lapses aggregate per candidate.
2. Per candidate expression: {lang, surface_as_spoken, proposed
   citation_form?, gloss candidates (from the notes' own English),
   example sentences present (TL+EN pairs from the notes), member
   note/card ids with schedule evidence, total reps at stake,
   sense-risk flag where members' glosses diverge (quarantine-style:
   flag, never merge divergent senses)}.
3. Rank by reps at stake — the creation wave will be pilot-first and
   should start where the learning investment is.
4. Aggregates: candidates per language, reps recovered per 100
   candidates created, the long tail (candidates with 1 card / 0-2
   reps — propose `low-value-defer` for those; the owner decides).

## Outputs

- `docs/research/hub_manifest/C4_orphan_expressions.json` (machine)
- `docs/research/hub_manifest/C4_orphan_expressions.md` (per-language
  tables, top-50 by reps, sense-risk list, methodology)

Deterministic, no network, proposals only — nothing is created by
this pass. One-paragraph final summary with candidate counts and the
reps-at-stake curve.
