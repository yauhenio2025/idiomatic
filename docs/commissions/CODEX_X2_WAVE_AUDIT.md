# Codex: Exercises 2.0 hostile wave audit (any completed topic)

You are the INDEPENDENT hostile auditor for authored Exercises 2.0
chunks — the same bar Wave 3 cleared 15/15 (see
docs/research/legacy_estate/EXERCISES2_WAVE3_AUDIT.md for the standard
and report shape). You audit chunks you did NOT author; assume the
author was competent but hurried, and try to catch them out.

SCOPE: the topic(s) named when this brief is invoked. For each chunk
with a passing `_notes.json`/`_triage.json` pair under
`idiomatic/grammar/data/exercises2/batches/output/`:

1. LANGUAGE: every target-language rendering must be natural, register-
   appropriate C1+ usage — not translationese. Flag anything a native
   editor would rewrite; flag EN prompts whose meaning the rendering
   silently shifts.
2. SCHEMA/FIELD SEMANTICS per the topic's addendum (vocab vs shadowing
   — shadowing chunks must be production frames with focus_tl/focus_en,
   never translation notes).
3. TRIAGE JUDGMENT: were drops justified and keeps clean? Cross-topic
   duplicates handled per the duplicate report? Items flagged in the
   staging manifest (`expected_duplicate_drop_ids`) actually dropped?
4. INTERFERENCE TRAPS: plausible and correct (a wrong trap teaches a
   wrong rule — worst defect class; be ruthless).
5. CLOZE integrity where applicable: the blanked form is the drilled
   form; no answer leakage elsewhere on the front.

VERDICT per chunk: PASS / PASS-WITH-EDITS (list every edit as
old→new, then APPLY the edits and re-run
`.venv/bin/python tools/x2_batch_gate.py <chunk>` until green) /
FAIL (do not fix wholesale — write the defect list for re-authoring).

OUTPUT: `docs/research/legacy_estate/EXERCISES2_<TOPIC>_AUDIT.md`
per topic — per-chunk verdict table, every edit applied, defect
taxonomy summary, and the final line: chunks passed / edited / failed.
Commit per topic. Audited+green chunks are merge-eligible; the
coordinator runs the merge step.
