# Codex commission J: verifier tuning from live reject evidence

> Work dir: /home/admin/projects/idiomatic-wt/tuning (isolated
> worktree). No git ops; `uv run pytest tests/` green. Evidence:
> /home/admin/projects/idiomatic-data/tuning/rejects_*.json — the
> actual rejected items from the first live batches (pt_gender_core
> 14/24 rejected, fr_quantites_de 9/24, de_dativ_verben 5/12). Read:
> idiomatic/grammar/generate.py (the verify paths + prompts),
> curriculum.py (guidances), docs/commissions/unit-specs/README.md
> (IMPLEMENTED + Deviations sections), and the project rule in
> docs/GRAMMAR_STRATEGY.md §8 STATUS ("when one unit's rejection rate
> is an outlier, read the rejects BEFORE concluding the model is
> weak — the verifier can be the bug").

## Task

For each of the three units, classify every reject in the dumps:
(a) genuinely bad item — verifier correct; (b) good item killed by an
over-strict rule; (c) good item killed because the PROMPT never told
the generator the rule it was checked against. Then fix (b) by
loosening the verifier surgically and (c) by hardening the prompt/
guidance (the it_genere_plurali citation-noun-hint fix in git history,
commit 511a19b~1 area, is the house pattern). Known suspects from the
first pass: pt_gender_core's "bank frame must use its canonical
sentence" and "blank is not directly before the stated noun" rules;
fr_quantites_de's inventory strictness vs elision variants;
de_dativ_verben unknown — diagnose from the dump.

Principles: NEVER loosen so far that a wrong answer passes (add a
regression test per loosened rule proving a wrong item still rejects);
prompts state hard rules the verifier enforces; when in doubt keep
strict and document. Deliverables: generate.py/curriculum.py edits,
per-unit before/after analysis appended to unit-specs/README.md,
tests for every changed rule (accept the formerly-good rejects,
reject wrong answers — use real sentences from the dumps).
