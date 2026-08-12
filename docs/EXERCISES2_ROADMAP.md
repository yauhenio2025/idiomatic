# Exercises 2.0 — topic-wave roadmap (plan of record)

> The legacy corpus (docs/research/legacy-excercises-audit.md) holds ~2,600
> shared EN prompts per language across 11 topics. Waves ship one topic at a
> time through the proven pipeline: chunk inputs → parallel codex sessions
> (EXERCISES2_BATCH_COMMISSION.md) → mechanical gate (tools/x2_batch_gate.py)
> → linguistic audit → merge to notes/ → `/admin/exercises2-build`.
> Check waves off as they ship. STATUS LINE: **Waves 1-6 SHIPPED in all
> five languages. Latest: fancy_vocab merged ×5 2026-08-12 (1,435 notes,
> hostile audit 76/76) → corpus 6,967 EN keys → strict rebuild ×5 fully
> voiced (apkgs 1719-23, all acked ok 2026-08-12). Only Wave 7
> FALSE_FRIENDS remains — needs fresh staging (no committed inputs; the
> legacy ES deck is NOT source material).**

| # | Wave | Size/lang | Status | Notes |
|---|------|-----------|--------|-------|
| 1 | ✅ CONNECTING | ~400 | **SHIPPED 2026-08-04** — es 207 / fr 191 / de 179 / pt 175 / it 201 (apkg 1396) | highest C1→C2 value; format = approved pilot |
| 2 | ✅ CONDITIONALS | 299 | **SHIPPED 2026-08-06** — es 168 / pt 160 / fr 162 / de 163 / it 166 (apkgs 1517-21); tail-chunk pollution correctly triaged out | five languages incl. IT from the start |
| 3 | ✅ TENSES | 300 | **SHIPPED 2026-08-09** — full Waves 1+2+3 rebuilds published with local-Qwen audio incl. English prompt fronts (apkgs 1621-25) | [audit](research/legacy_estate/EXERCISES2_WAVE3_AUDIT.md); raw order incl. literary tenses; `_tenses_old` priors adapt new examples, not the source or Tenses Rescue |
| 4 | ✅ FANCY_VOCAB | 1,435 | **SHIPPED 2026-08-12** — merged ×5 (790af1b: hostile audit 76/76, 36 chunks edited / 196 edits), corpus → 6,967 EN keys; rebuilt ×5 fully voiced same day (apkgs 1719-23, acked ok) | heavy-triage prediction held; last committed topic wave in batches/output |
| 5 | ✅ vocab trio: BIG_TECH_VOCAB + COLD_WAR_VOCAB + GEOPOLITICS | 1,810 | **SHIPPED 2026-08-10→12** — geopolitics 750 merged (9116551) then de-boilerplated + re-audited 750/750 (845ba77); big_tech_vocab 476 (90a5af0, audit 20/20); cold_war_vocab 584 (bc35fd4, audit 30/30, 149 edits); all in the voiced 1719-23 rebuilds | GEOPOLITICS kept term–definition shape (V2) |
| 6 | ✅ BIG_TECH_PHRASES | 90/lang | **SHIPPED 2026-08-09** (80565b2: pt gap chunk b01 authored+audited, pilot 004 repair, pt merged — all five languages at 90 notes) | production/shadowing draft model per P1 — NOT Exercises v1 translation cards; merged notes are excluded from the frozen v1 loaders |
| 7 | FALSE_FRIENDS rebuild | — | not started | verified 5-language interference matrix; ties into F4; the legacy ES deck was toxic and is NOT source material |
| — | COMMANDS / PRONOUNS / REFLEXIVE | 400 | **GAP AUDIT COMPLETE 2026-08-08; no imports** | [language-by-language findings](research/legacy_estate/EXERCISES2_GRAMMAR_GAP_AUDIT.md); route future work to verified grammar objectives |

Sister deliverable shipped alongside Wave 1: **Translation decks** (grammar
drills as EN-voiced→TL translation cards, `idiomatic/grammar/translation.py`)
— extend automatically as the grammar decks grow; rebuild via
`/admin/translation-build?lang`.

Standing user directive (2026-08-04): **bug the user about returning to this
roadmap** whenever a wave finishes or a session goes idle on this project.
