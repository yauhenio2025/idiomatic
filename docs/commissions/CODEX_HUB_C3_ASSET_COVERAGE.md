# Codex WP-C3: asset coverage sweep (read-only)

Work package C3 of docs/commissions/HUB_BUILD_EXECUTION_COMMISSION.md.
ANALYSIS ONLY: write nothing outside `docs/research/hub_manifest/`.

PRECONDITION: `docs/research/hub_manifest/C3_server_examples_extract.json`
must exist (the coordinator's server extract: every idiom with its
examples and context-audio status). If absent, STOP and report.

## Inputs (read-only)

- The server extract above (idiom_id, expression_id, lang, surfaces,
  has_context, examples[] with example_id).
- The LOCAL illustration corpus + QA state on this box:
  `~/llms/qwen-image/` — rendered images (per-chunk output dirs keyed
  by example_id — discover the exact layout, do not assume), the QA
  ledger `qa/verdicts.jsonl` (content-hash keyed pass/fail verdicts),
  `qa/human_overrides.jsonl` (beats the judge), and the chunk→machine
  PARTITION assignment in the repo
  (`idiomatic/grammar/data/illustration_prompts/PARTITION.json`) —
  Mac-owned chunks may have no local files; report them as
  `remote-unverified`, never as missing.
- Illustration brief outputs in
  `idiomatic/grammar/data/illustration_prompts/output/*.json` (which
  example_ids have authored briefs at all).

## Task

Produce the per-example asset ledger the Hub manifest compiler will
consume:

1. For every example_id in the extract: brief authored? rendered?
   QA verdict (pass / fail / pending / human-override) with the
   verdict's content hash? local file present + byte size, or
   Mac-owned? Final status ∈
   {qa-passed, rendered-unjudged, brief-only, no-brief, remote-unverified}.
2. Context-audio coverage per idiom (from the extract's has_context) —
   cross-tabbed by language.
3. Aggregates per language: counts by status, QA pass-rate, and the
   render-priority queue — the ordered list of example_ids whose
   expressions have the HIGHEST study activity but no qa-passed image
   (join study weight from
   `docs/research/hub_manifest/C2_schedule_dossiers.json` adoptable
   reps via the bilingual join keys; where the join is ambiguous, note
   it and order by language coverage need instead).

## Outputs (only these)

- `docs/research/hub_manifest/C3_asset_coverage.json` (machine ledger)
- `docs/research/hub_manifest/C3_asset_coverage.md` (per-language
  tables, the top-50 render-priority list, methodology, anomalies)

## Rules

Deterministic, no network, no image opening beyond stat/hash, no
renders triggered, nothing deleted. The QA ledger is authoritative for
verdicts; a file on disk without a pass verdict is NEVER counted as
qa-passed (the estate's hard rule: only pass-verdict images may ship).
Finish with a one-paragraph summary: totals by status per language and
the size of the qa-passed pool available to the Hub today.
