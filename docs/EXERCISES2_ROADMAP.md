# Exercises 2.0 — topic-wave roadmap (plan of record)

> The legacy corpus (docs/research/legacy-excercises-audit.md) holds ~2,600
> shared EN prompts per language across 11 topics. Waves ship one topic at a
> time through the proven pipeline: chunk inputs → parallel codex sessions
> (EXERCISES2_BATCH_COMMISSION.md) → mechanical gate (tools/x2_batch_gate.py)
> → linguistic audit → merge to notes/ → `/admin/exercises2-build`.
> Check waves off as they ship. STATUS LINE: **Wave 1 shipped; Wave 2 staged.**

| # | Wave | Size/lang | Status | Notes |
|---|------|-----------|--------|-------|
| 1 | ✅ CONNECTING | ~400 | **SHIPPED 2026-08-04** — es 207 / fr 191 / de 179 / pt 175; it gap-fill authoring | highest C1→C2 value; format = approved pilot |
| 2 | ⏳ CONDITIONALS | 299 | **STAGED** — 15 chunk inputs + [addendum](commissions/EXERCISES2_CONDITIONALS_ADDENDUM.md) committed; awaiting user "go" | counterfactuals = documented weak spot in all 5 langs; IT included from start |
| 3 | TENSES | 300 | not started | tense sequencing, same error-mine territory; reuse the conditionals addendum pattern |
| 4 | FANCY_VOCAB | 582 | not started | academic register; biggest topic; simpler card shape — needs its own addendum (vocab-style notes) |
| 5 | vocab trio: BIG_TECH_VOCAB + COLD_WAR_VOCAB + GEOPOLITICS | 640 | not started | professional register; GEOPOLITICS keeps the term–definition shape |
| 6 | BIG_TECH_PHRASES | 90 | not started | NOT translation cards — repurpose as production/shadowing prompts |
| 7 | FALSE_FRIENDS rebuild | — | not started | verified 5-language interference matrix; ties into F4; the legacy ES deck was toxic and is NOT source material |
| — | COMMANDS / PRONOUNS / REFLEXIVE | 400 | skip/merge | largely covered by grammar drill decks — audit for gaps instead of re-authoring |

Sister deliverable shipped alongside Wave 1: **Translation decks** (grammar
drills as EN-voiced→TL translation cards, `idiomatic/grammar/translation.py`)
— extend automatically as the grammar decks grow; rebuild via
`/admin/translation-build?lang`.

Standing user directive (2026-08-04): **bug the user about returning to this
roadmap** whenever a wave finishes or a session goes idle on this project.
