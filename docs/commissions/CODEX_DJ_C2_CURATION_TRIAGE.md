# Codex DJ-C2: study-worthiness triage evidence (read-only)

The owner's directive (2026-08-09): "we need to go through everything
and figure out what is really worth studying given my level of current
knowledge" — batch-imported content (Pimsleur was the first casualty)
pollutes the due backlog. Produce the EVIDENCE for a per-subtree
disposition console; propose, never apply. Write only to
`docs/research/dj_census/` (triage_* files).

## Inputs (read-only, `mode=ro&immutable=1`)

- `docs/research/anki_reorg_work/live_cutover_20260807T072826Z/collection.anki2`
  (current account, estate tree, full revlog).
- Cross-reference `docs/research/dj_census/` outputs if DJ-C1 has
  landed (secs/rep, rating profiles); recompute locally if not.

## Task

For every studyable subtree (each `<XX Language>::<lane>` and its
first-level subdecks; plus zz Dormant summarized in one line each —
already retired, listed only for completeness):

EVIDENCE per subtree: card count, due now, new reservoir; provenance
(pipeline-minted vs batch-imported vs hand-made — infer from note
models + estate origin tags); study depth (reps, distinct studied
cards, last-touch date); DIFFICULTY SIGNAL where studied: easy-rate,
again-rate, median ivl of mature cards — a high easy-rate + high ivl
means beneath level; never-studied bulk means never opted in.

PROPOSED DISPOSITION per subtree, conservative:
- `keep-active` — clearly in the study path (pipeline lanes, recent
  study, healthy difficulty mix).
- `suspend-reference` — keep but suspend: beneath level or never
  opted in (the Pimsleur pattern); reversible, preserves everything.
- `sample-hardest` — bulk suspend BUT propose keeping the N hardest
  items active (evidence: per-card lapse/again data); state N.
- `owner-review` — evidence genuinely mixed; one-line reason.
Nothing is ever deleted; suspension is the strongest proposal allowed.

## Outputs

- `docs/research/dj_census/triage_evidence.json` — machine, per
  subtree: all evidence fields + proposal + one-line rationale.
- `docs/research/dj_census/triage_report.md` — per-language tables
  sorted by due-load impact, with the projected due-backlog per
  language if all proposals were accepted (before → after minutes,
  using DJ secs/rep constants).

The JSON feeds an interactive console page (multiple-choice per
subtree) — write rationales as the one-line labels an owner will read
on a phone. Deterministic, no network, no dispositions applied.
