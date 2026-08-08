# Exercises 2.0 — topic-wave roadmap (plan of record)

> The legacy corpus (docs/research/legacy-excercises-audit.md) holds ~2,600
> shared EN prompts per language across 11 topics. Waves ship one topic at a
> time through the proven pipeline: chunk inputs → parallel codex sessions
> (EXERCISES2_BATCH_COMMISSION.md) → mechanical gate (tools/x2_batch_gate.py)
> → linguistic audit → merge to notes/ → `/admin/exercises2-build`.
> Check waves off as they ship. STATUS LINE: **Waves 1+2 shipped in all five
> languages (1,772 notes / 3,544 cards). Wave 3 TENSES is content-complete,
> audited, and merged (1,500 more notes / 3,000 cards; 3,272 / 6,544 authored
> totals), but its audio build and release wait for the APKG 1615 local-Qwen
> listening verdict.**

| # | Wave | Size/lang | Status | Notes |
|---|------|-----------|--------|-------|
| 1 | ✅ CONNECTING | ~400 | **SHIPPED 2026-08-04** — es 207 / fr 191 / de 179 / pt 175 / it 201 (apkg 1396) | highest C1→C2 value; format = approved pilot |
| 2 | ✅ CONDITIONALS | 299 | **SHIPPED 2026-08-06** — es 168 / pt 160 / fr 162 / de 163 / it 166 (apkgs 1517-21); tail-chunk pollution correctly triaged out | five languages incl. IT from the start |
| 3 | TENSES | 300 | **CONTENT COMPLETE 2026-08-08** — 15/15 chunks independently audited and gated; five 300-note files merged; audio/build/release owner-gated | [audit](research/legacy_estate/EXERCISES2_WAVE3_AUDIT.md); raw order incl. literary tenses; `_tenses_old` priors adapt new examples, not the source or Tenses Rescue |
| 4 | FANCY_VOCAB | 582 | **Audited 30-row ES pilot: 14 keep / 16 drop; owner gate V1 open** | no bulk outputs until generic vocab format verdict |
| 5 | vocab trio: BIG_TECH_VOCAB + COLD_WAR_VOCAB + GEOPOLITICS | 517 committed deduped prompts | **Audited 30-row ES GEOPOLITICS pilot: 30 keep; owner gate V2 open** | V1 also gates BIG_TECH/COLD_WAR vocab; GEOPOLITICS keeps term–definition shape |
| 6 | BIG_TECH_PHRASES | 90 | **Audited 30-row PT shadowing pilot: 30 keep; owner gate P1 open** | separate draft model only; no bulk output/build/TTS |
| 7 | FALSE_FRIENDS rebuild | — | not started | verified 5-language interference matrix; ties into F4; the legacy ES deck was toxic and is NOT source material |
| — | COMMANDS / PRONOUNS / REFLEXIVE | 400 | **GAP AUDIT COMPLETE 2026-08-08; no imports** | [language-by-language findings](research/legacy_estate/EXERCISES2_GRAMMAR_GAP_AUDIT.md); route future work to verified grammar objectives |

Sister deliverable shipped alongside Wave 1: **Translation decks** (grammar
drills as EN-voiced→TL translation cards, `idiomatic/grammar/translation.py`)
— extend automatically as the grammar decks grow; rebuild via
`/admin/translation-build?lang`.

Standing user directive (2026-08-04): **bug the user about returning to this
roadmap** whenever a wave finishes or a session goes idle on this project.
