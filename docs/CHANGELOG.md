# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
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
