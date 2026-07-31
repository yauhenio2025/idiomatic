# Codex commission H: F4 cross-language interference deck

> Work dir: /home/admin/projects/idiomatic-wt/f4 (isolated worktree).
> No git ops; `uv run pytest tests/` green at the end. Read first:
> /home/admin/projects/idiomatic-data/interference/F4_DESIGN.md (the
> commissioned design — follow its recommendation unless it conflicts
> with the constraints below), matrix.md, the f4_pairs_*.json banks
> (same data dir), idiomatic/grammar/f3.py (the pattern to mirror),
> docs/GRAMMAR_STRATEGY.md §4 (F4) + §3b (Pan 2025).

## Constraints that OVERRIDE the design doc where they conflict

1. **The pair bank is personal data and must NOT enter the public
   repo.** Mirror the F3/personal_errors pattern: pairs reach the
   server as DATA (an admin upload endpoint staging into a DB table,
   cron-side batch ingest — see idiomatic/personal_errors.py and its
   staging table for the exact containment pattern), and cards are
   built from DB rows. No pair content in grammar/data/.
2. Frozen model/templates/GUID formula. F4 cards are grammar_items
   rows (fmt='f4') in per-language units, cluster "10 …" (localized
   name your choice, e.g. "10 Interférences" — record final strings
   in unit-specs). Attested pairs need no LLM verification; if the
   design includes generated same-frame sentences around a pair, they
   go through Tier B blind-fill.
3. Direction-aware per the matrix: drill the RECEIVING language; the
   source-language form is context/distractor, never the answer.

## Deliverables

- `f4_pairs` DB table + staging (schema.sql, idempotent), upload
  endpoint + cron ingest hook, `grammar/f4.py` (selection + card
  mapping + conversion endpoint `/admin/f4-convert?lang=&n=`),
  curriculum Topics (5 langs; de only if the bank's single pair
  warrants it — else skip de and say so), tests (pure-function,
  no-DB, mirroring tests/test_f3.py), unit-specs note with final
  cluster strings + deviations.
