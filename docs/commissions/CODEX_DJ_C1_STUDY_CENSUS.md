# Codex DJ-C1: study-telemetry census (read-only)

Calibration evidence for the Personal Study DJ's planner
(docs/commissions/PERSONAL_DJ_COMMISSION.md — read its "brain" section
first). ANALYSIS ONLY: write nothing outside
`docs/research/dj_census/` (create it).

## Inputs (local, read-only; open SQLite `mode=ro&immutable=1`)

- `docs/research/anki_reorg_work/live_cutover_20260807T072826Z/collection.anki2`
  — the current account, post-estate tree, full revlog (62,554 rows
  through 2026-08-07). Deck lanes follow `<XX Language>::<N Lane>` —
  map every card to (language, population) via its deck path; the
  populations: 1 Expressions / 2 Grammar / 3 Tenses / 4 Exercises /
  5 Translation / 6 My Errors / 7 Rescue / 8 Pimsleur / lessons
  (podcast tags) / other.
- The `_tenses_old` corpus and +2 legacy snapshot evidence under
  docs/research/ (tenses-profiles, legacy_estate) — HISTORICAL context
  only where cheap; the current account is the primary source.

## Deliverables (JSON + MD in docs/research/dj_census/)

1. SECONDS-PER-REP: per (language, population): median/p25/p75 of
   revlog.time (capped at Anki's 60s default where relevant — note the
   cap's effect), rep counts, and a recommended planning constant per
   cell (with a global fallback table where cells are thin).
2. SESSION ANATOMY: cluster revlog timestamps into study sessions
   (gap-based, document the gap threshold): sessions/day, session
   length distribution, time-of-day pattern, languages per session,
   how language-interleaved real sessions are. The owner believes he
   studies ~2-3h/day in gym blocks — measure what the data actually
   shows, including variance across the last 90 days.
3. MIX HISTORY: per day over the last 60 days: minutes and reps per
   (language, population) — the baseline "what I actually study" that
   the /dj panel's plan-vs-actual view needs; note populations that get
   systematically starved.
4. RATING PROFILE: again/hard/good/easy distribution per (language,
   population) and per maturity band — the raw material for later
   weakness weighting (compute and report; propose nothing).

## Rules

Deterministic, no network, no LLM judgment — this is counting. Where
deck-lane mapping is ambiguous (cards outside the estate lanes),
bucket as `other` and report the count rather than guessing. Every
table in both machine JSON and a readable MD with a short methods
section. Finish with a one-paragraph summary: the measured daily study
reality vs the owner's 2-3h/20-30min-per-language model.
