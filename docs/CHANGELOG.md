# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Learner error profile for Italian ([docs/research/error-profiles/it.md](research/error-profiles/it.md)): mined the 2019 xlsx/Anki `_it_errors` data (133 rows, only 11 recorded production errors), taxonomy + F3 seed pairs + curriculum mapping; documents the Teachee gap and proposes a live error-capture path via the add-on.
- **Wave 6 — grammar subdecks + dashboard grammar section** ([commission](commissions/GRAMMAR_FRONTEND_COMMISSION.md)): grammar apkgs now build one Anki subdeck per topic cluster (`Idiomatic Grammar {LANG}::{cluster}`, [idiomatic/grammar/apkg.py](../idiomatic/grammar/apkg.py)); `grammar_units` table (cluster/label/symbol re-seeded from curriculum code on boot, status/target_size/notes DB-mutable, `planned` units listed for what's-next); dashboard **Grammar** pages `/grammar` + `/grammar/unit/:key` ([frontend/src/pages/Grammar.tsx](../frontend/src/pages/Grammar.tsx), [GrammarUnit.tsx](../frontend/src/pages/GrammarUnit.tsx)) with Top-up/Rebuild/retire/unit-edit controls; new endpoints `/ui/api/grammar/*`, `/admin/grammar-deckmap` (agent-authed), `/admin/grammar-unit/{key}`, `/admin/grammar-topup/{key}`, `/admin/grammar-retire-item/{id}`; add-on gained a one-shot "Reorganize grammar decks" migration (local, `col.set_deck` by unit tag — review history preserved).
- Commission brief for the dashboard grammar section + subdeck taxonomy ([docs/commissions/GRAMMAR_FRONTEND_COMMISSION.md](commissions/GRAMMAR_FRONTEND_COMMISSION.md)); Wave 6 added to the plan of record.
- Wave plan (grammar roadmap of record) in [docs/GRAMMAR_STRATEGY.md](GRAMMAR_STRATEGY.md) §8, plus codex-delegation working rule (§8b, CLAUDE.md).
- Grammar drill pipeline, Spanish pilot ([idiomatic/grammar/](../idiomatic/grammar/)): Gemini-generated one-form-per-card conjugation cloze items, verified against the vendored Jehle verb DB (wrong/unverifiable forms are persisted as `rejected`, never shipped); rolling `kind='grammar'` apkg per language delivered through the existing add-on path; admin endpoints `grammar-generate/status/stats/rebuild`; `grammar_items` table; deterministic tests in [tests/test_grammar.py](../tests/test_grammar.py).
- `docs/` structure: feature inventory ([docs/FEATURES.md](FEATURES.md)) and this changelog.
- Grammar-exercise strategy document ([docs/GRAMMAR_STRATEGY.md](GRAMMAR_STRATEGY.md)) — research-backed plan for LLM-generated, personalized grammar drills across es/pt/fr/it/de.
- Research annex ([docs/research/](research/)): four commissioned reports (community wisdom, data sources & licenses, SLA pedagogy, AnkiDroid/genanki tech) grounding the grammar strategy.

---

## [2026-07-27]

### Added
- Worker-side disk janitor: media_stage sweep + delivered-apkg reaper (`idiomatic/worker.py`).
- Queue auto-expiry: queued news older than 7 days expires (cron).

### Changed
- TTS: ElevenLabs turbo v2.5 primary; Gemini TTS preview demoted to fallback.
