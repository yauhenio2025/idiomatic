# Exercises 2.0 — topic-wave roadmap (plan of record)

> The legacy corpus (docs/research/legacy-excercises-audit.md) holds ~2,600
> shared EN prompts per language across 11 topics. Waves ship one topic at a
> time through the proven pipeline: chunk inputs → parallel codex sessions
> (EXERCISES2_BATCH_COMMISSION.md) → mechanical gate (tools/x2_batch_gate.py)
> → linguistic audit → merge to notes/ → `/admin/exercises2-build`.
> Check waves off as they ship. STATUS LINE: **Waves 1+2+3 SHIPPED in all
> five languages (3,272 notes / 6,544 cards, apkgs 1621-25, 2026-08-09) —
> full local-Qwen audio incl. NEW English prompt fronts on every Production
> card. V1/V2/P1 format verdicts APPROVED 2026-08-09 ("this looks good to
> me too - all three formats"); Waves 4-6 bulk inputs STAGED the same day
> (160 forty-row chunks, manifests wave4/wave5/wave6) — authoring begins
> via the codex lane (EXERCISES2_BATCH_COMMISSION.md + addenda).**

| # | Wave | Size/lang | Status | Notes |
|---|------|-----------|--------|-------|
| 1 | ✅ CONNECTING | ~400 | **SHIPPED 2026-08-04** — es 207 / fr 191 / de 179 / pt 175 / it 201 (apkg 1396) | highest C1→C2 value; format = approved pilot |
| 2 | ✅ CONDITIONALS | 299 | **SHIPPED 2026-08-06** — es 168 / pt 160 / fr 162 / de 163 / it 166 (apkgs 1517-21); tail-chunk pollution correctly triaged out | five languages incl. IT from the start |
| 3 | ✅ TENSES | 300 | **SHIPPED 2026-08-09** — full Waves 1+2+3 rebuilds published with local-Qwen audio incl. English prompt fronts (apkgs 1621-25) | [audit](research/legacy_estate/EXERCISES2_WAVE3_AUDIT.md); raw order incl. literary tenses; `_tenses_old` priors adapt new examples, not the source or Tenses Rescue |
| 4 | FANCY_VOCAB | 582 | **format APPROVED 2026-08-09 — bulk staging ready; authoring begins** (75 staged chunks, 15/lang × ~40 rows, `wave4` manifest) | 20 committed cross-topic copies stay staged, flagged per chunk for triage-drop; V1 pilot's 14/30 keep rate predicts heavy triage |
| 5 | vocab trio: BIG_TECH_VOCAB + COLD_WAR_VOCAB + GEOPOLITICS | 517 committed deduped prompts | **format APPROVED 2026-08-09 — bulk staging ready; authoring begins** (70 staged chunks, 14/lang: 4+6+4, `wave5` manifest) | GEOPOLITICS keeps term–definition shape (V2); the trio owns its duplicate groups — zero expected drops |
| 6 | BIG_TECH_PHRASES | 90 | **authored + hostile-audited; MERGED de/es/fr/it (90 notes each, 2026-08-09) — pt blocked on the rows 31-40 gap chunk** | production/shadowing draft model per P1 — NOT Exercises v1 translation cards; merged notes are excluded from the frozen v1 loaders. PT lane = approved 30-row pilot prefix + restaged `pt_..._b01` (rows 31-40, AWAITING codex authoring; the original bulk pt b01 double-staged the pilot rows and was never authored) + audited b02/b03; `merge pt_big_tech_phrases` composes all four once b01 lands |
| 7 | FALSE_FRIENDS rebuild | — | not started | verified 5-language interference matrix; ties into F4; the legacy ES deck was toxic and is NOT source material |
| — | COMMANDS / PRONOUNS / REFLEXIVE | 400 | **GAP AUDIT COMPLETE 2026-08-08; no imports** | [language-by-language findings](research/legacy_estate/EXERCISES2_GRAMMAR_GAP_AUDIT.md); route future work to verified grammar objectives |

Sister deliverable shipped alongside Wave 1: **Translation decks** (grammar
drills as EN-voiced→TL translation cards, `idiomatic/grammar/translation.py`)
— extend automatically as the grammar decks grow; rebuild via
`/admin/translation-build?lang`.

Standing user directive (2026-08-04): **bug the user about returning to this
roadmap** whenever a wave finishes or a session goes idle on this project.
