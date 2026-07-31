# Codex commission C: F3 error-correction card format (Wave 7 Phase 1)

> Work dir: /home/admin/projects/idiomatic-wt/f3 (an isolated git
> worktree of the repo). Edit code there ONLY. No commits, no pushes —
> the supervising session reviews and merges. `uv run pytest tests/`
> must pass at the end. Read for context: docs/commissions/
> ERROR_PROFILE_PROPOSAL.md, docs/GRAMMAR_STRATEGY.md §4 (F3),
> idiomatic/grammar/ (whole module), idiomatic/db.py (personal_errors +
> grammar_items functions), db/schema.sql.

## What F3 is

Cards built from the learner's OWN teacher-attested errors (the
`personal_errors` DB table, 11,481 rows, seeded 2026-07-31). Front:
the wrong phrase he actually produced, marked as an error. He mentally
corrects, reveals; back: the correction + one-line why. No LLM
generation, no verification needed — every pair is teacher-attested.

## Architecture (DECIDED — implement, don't redesign)

1. F3 items are ordinary `grammar_items` rows: `fmt='f3'`,
   `status='verified'`, `topic` = one per-language unit key:
   fr_mes_erreurs / pt_meus_erros / es_mis_errores / it_miei_errori /
   de_meine_fehler. Add these 5 Topics to curriculum (symbol "⚠",
   mood/tense "", verify="attested", cluster: "9 Mes erreurs" /
   "9 Meus erros" / "9 Mis errores" / "9 I miei errori" /
   "9 Meine Fehler"). They ride the existing rebuild/delivery/subdeck
   machinery untouched.
2. Field mapping into the FROZEN 14-field model (NEVER touch MODEL_ID,
   fields, or templates): Sentence = the wrong phrase as plain text
   (apkg.py already escapes + renders it; no ___ blank needed — the
   whole phrase is the challenge); Answer = the corrected phrase;
   SentenceFull = corrected full sentence (right + gloss context);
   GlossEn = the pair's gloss_en or category; Why = the why field.
   TenseLabel = per-lang label like "Corrige : ce que j'ai dit" (pick
   natural per-language phrasings). Audio: the existing
   grammar/audio.py ensure_audio works unchanged (TTS of answer +
   corrected sentence).
3. Conversion pipeline `grammar/f3.py`:
   - `select_candidates(lang, n)` — from personal_errors: kind='error',
     status='active', confidence='high', f3_item_id IS NULL, wrong is a
     usable free-standing phrase (implement a suitability filter: ≥2
     words or a known closed-class single word; skip bare lemma pairs
     like 'insérir→insérer'? NO — single-word derivation/false-friend
     pairs ARE usable, format as 'X' → 'Y'; skip only unusable
     fragments like bracket-mangled text). Rank by occurrences DESC,
     then last_seen DESC.
   - `convert(lang, n)` — insert grammar_items rows (db.insert_grammar_items
     with fmt — extend that function to accept fmt, default 'cloze'),
     write back personal_errors.f3_item_id (new column — add to
     schema.sql idempotently: `ALTER TABLE personal_errors ADD COLUMN
     IF NOT EXISTS f3_item_id BIGINT`), so re-runs never duplicate.
     Sentence uniqueness: grammar_items UNIQUE(lang, sentence) — prefix
     the wrong phrase with nothing; if a collision happens, skip + log.
4. Endpoint `POST /admin/f3-convert` (lang, n=20, authed_admin) in
   api.py: runs select+convert synchronously (it's pure DB, fast),
   returns {converted, skipped, examples: first 3}. Rebuild is NOT
   triggered automatically — the user tops up via the existing
   /admin/grammar-rebuild when ready (volume rule: small batches).
5. `grammar_units` seeding: the 5 new Topics enter unit_seed_rows()
   automatically (status active, sort after existing units — they're
   appended to each lang's topic list, so index order handles it).
   target_size default 12 is fine.

## Deliverables

- grammar/f3.py, api.py endpoint, curriculum.py 5 Topics + clusters,
  db.py fmt param + f3 helpers, schema.sql column.
- tests (tests/test_f3.py): suitability filter cases (usable phrase,
  single-word pair, mangled fragment), field mapping into the frozen
  model via build_grammar_apkg (assert model still 14 fields, F3 note
  renders wrong phrase + answer), dedup via f3_item_id (mock/fake db
  layer or restructure pure functions to be testable without DB — the
  existing tests are no-DB; keep that property: pure functions for
  selection/mapping, thin DB glue).
- A short DESIGN_NOTES.md in docs/commissions/unit-specs/ describing
  what you built + anything you flagged.

## Hard rules

- Model/templates FROZEN. GUID formula untouched. No git ops. No
  network calls. `uv run pytest tests/` green. Do not modify files
  outside: idiomatic/grammar/, idiomatic/api.py, idiomatic/db.py,
  db/schema.sql, tests/, docs/commissions/unit-specs/.
