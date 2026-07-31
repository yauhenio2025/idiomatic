# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Learner error profile for Portuguese ([docs/research/error-profiles/pt.md](research/error-profiles/pt.md)): mined 4,521 xlsx rows (2019-2022, 1,098 explicit error pairs) + 1,400 Teachee notes (2023-2024); taxonomy of 19 categories — Spanish/Italian interference 54%, gender/articles 18% (the -ma/-agem/dois-duas fossil core, still remediated in 2023-24), verb+prep calques (tentar de, conseguir a, vou a), 1sg↔3sg pretérito swaps, ser/estar/ficar, future-subjunctive avoidance; 24 fossilization patterns; curriculum mapping (raise pt_preterito_perfeito + pt_futuro_subjuntivo, activate pt_clitic_placement, lower futuro/condicional; new proposed units pt_gender_core, pt_regencia_verbal, pt_ser_estar_ficar, pt_es_contrastes); 40-pair F3 seed JSON.
- Learner error profile for German ([docs/research/error-profiles/de.md](research/error-profiles/de.md)): 346 xlsx rows (9 lessons, April 2019) + 379 Teachee notes (2022–2024) mined; taxonomy of the 149 use-flagged corrections, ~28 verbatim retained errors — adjective endings/gender/case dominate and recur across both eras; verdict: build de_adj_endings first, then passive (35 teacher-supplied instances); proposes a "5 Kasus" cluster (dative verbs, n-declension, genitive) and ships a 30-pair F3 seed list.
- Learner error profile for Spanish ([docs/research/error-profiles/es.md](research/error-profiles/es.md)): mined 1,389 xlsx rows (2019-2022) + 304 Teachee notes (2022-2024); 62 verbatim error pairs categorized (cross-Romance interference 42%, muy/mucho, motion prepositions, strong preterites), 20 fossilization patterns, curriculum mapping over the 18 active es units (raise es_preterito/es_clitics_selo/es_verb_prep, new proposed units es_interferencia/es_muy_mucho/es_light_verbs/es_numeros_fechas), 40-pair F3 seed JSON.
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
