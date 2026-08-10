# Codex: /lingq decision console (owner verdict surface)

Build the owner-facing decision console for the LingQ dormant-value
initiative, following the ESTABLISHED house pattern end to end. Owner
decisions ship as interactive console pages, never MD files.

## Templates to copy (read all three first)

- `idiomatic/dj_triage.py` + its endpoints in `idiomatic/api.py`
  (`/admin/triage-verdict`, `/admin/triage-verdict-bulk`) and
  `idiomatic/ui_api.py` (`GET /ui/api/triage`) — the seed-once /
  verdict-preserving table pattern, validation style, and the
  read-only vs sanctioned-mutation split.
- `frontend/src/pages/Triage.tsx` — the Cast-Review-style phone-first
  page: rows, rationale chips, 44px one-tap verdict buttons, note
  field, sticky progress bar, explicit nothing-is-applied banner.
- `db/schema.sql` — additive-table style with boot-migration
  discipline.

## Content to serve

Source documents (read both): the technical inventory
`docs/research/lingq/REPORT.md` (+ aggregate numbers in
`docs/research/lingq/inventory.json`, committed-safe: aggregates only)
and the ranked proposal
`docs/research/lingq/LINGQ_VALUE_PROPOSAL.md` (7 concepts C1-C7, one
recommended pilot).

Console rows = the SEVEN CONCEPTS. Each row carries: concept key
(c1_second_encounter … c7_picture_idiom), name, one-paragraph pitch
(distilled from the proposal — your distillation, tight), the key
sizing numbers (from the inventory: e.g. per-lang dormant multiword
counts, fragment coverage), estimated study-minutes/day impact, and
the proposal's rank. Verdict options per row:
`greenlight-pilot | interested-later | not-for-me | defer`, plus an
optional owner note. Exactly the dj_triage seed rules: seed only while
the table is empty; verdicts and notes survive reseeds; a banner
states that verdicts trigger NOTHING automatically — the coordinator
reads them and commissions work.

## Deliverables

1. `db/schema.sql`: additive `lingq_verdicts` table (concept_key
   unique, payload jsonb for the row content, owner_verdict TEXT NULL,
   owner_note TEXT NULL, verdicted_at TIMESTAMPTZ NULL, seeded_at).
2. `idiomatic/lingq_console.py`: row definitions (the seven concepts,
   content inline as code constants — numbers hardcoded from the two
   research docs, cite the doc in a comment), boot seed (empty-only),
   list + verdict functions, validation (known keys, known verdicts).
3. `idiomatic/api.py`: `POST /admin/lingq-verdict` (admin bearer,
   single row: {concept_key, verdict?, note?} — note-only saves
   allowed). Boot seed hook wherever dj_triage hooks its own.
4. `idiomatic/ui_api.py`: `GET /ui/api/lingq` (admin bearer,
   read-only rows + progress summary).
5. `frontend/src/pages/Lingq.tsx` + route + nav entry exactly where
   /triage registers its own (find the router; match its style).
   Page title: "LingQ — dormant value". Top summary strip: the
   headline numbers (51,826 terms · 95% status-0 encounter log ·
   5,455 never-drilled multiword expressions in active langs ·
   ~18k pre-clozed fragments). Then the seven concept cards with
   verdict buttons; recommended pilot (C1) visually flagged with the
   proposal's reasoning.
6. Tests following tests/test_dj_triage.py style: seed idempotence +
   verdict preservation, unknown key/verdict rejection, note-only
   save, endpoint auth. Frontend must pass the repo's typecheck/build
   (`cd frontend && npm run build` — check how CI/Dockerfile invokes
   it and match).

Run the FULL python suite and the frontend build; both must be green.
Do NOT commit — the coordinator reviews and merges. Print: files
created/changed, row content summary (the seven pitches), test tail
lines for python and frontend.
