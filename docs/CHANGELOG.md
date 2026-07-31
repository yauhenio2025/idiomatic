# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
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
