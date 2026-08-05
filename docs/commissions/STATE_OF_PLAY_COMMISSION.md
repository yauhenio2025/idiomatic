# Commission: State of Play — 10-day audit of the idiomatic project

> For a codex CLI session. Produce ONE report the user can absorb in ten
> minutes that restores their complete mental picture: what shipped in the
> last 10 days, what is live where, what is half-finished, what can be
> generated next, and which decisions are parked on them. The orchestrating
> session's own knowledge is embedded in §Prior-knowledge below — VERIFY
> each claim against the repo and live state; flag anything that
> contradicts it. Then go beyond it: find what it forgot.

## Deliverable

`docs/STATE_OF_PLAY.md` — dated header (2026-08-05), structured exactly:

1. **Executive summary** — ≤12 lines, plain sentences.
2. **Shipped, last 10 days** — grouped by area (pipeline/infra, grammar
   initiative, podcast cards, Exercises 2.0, translation decks,
   incidents), each item one line with numbers and commit/apkg refs.
3. **Live inventory** — table: deck family × language → notes/cards,
   latest apkg id, which Anki profile holds it
   (evgeny@the-syllabus.com = grammar/exercises/translation/podcast;
   evgeny.morozov+2@gmail.com = idiom/video/pool decks).
4. **Open loops & unfinished business** — THE CORE. Ranked by value.
   Each: what it is · why it's parked · concrete next action · rough
   effort. Verify every candidate in §Prior-knowledge and hunt for more
   (grep TODOs, read docs/commissions/* for unexecuted commissions,
   docs/GRAMMAR_STRATEGY.md §8 wave plan checkboxes,
   docs/EXERCISES2_ROADMAP.md, docs/incidents/*, CHANGELOG Unreleased).
5. **Generation capacity map** — where MORE content can be produced on
   demand today: grammar units below target_size (live stats), staged
   Exercises waves, translation-deck auto-growth, explainer/podcast
   episodes not yet built, error-profile-proposed units never created.
6. **Risks & watch items** — with current numbers (disk!).
7. **Decisions owed by the user** — compact numbered list, each one
   sentence + what unblocks.

## Method

- `git log --since="2026-07-26" --oneline --stat` (and read the diffs
  that matter); `docs/CHANGELOG.md` [Unreleased]; `docs/FEATURES.md`;
  every file in `docs/commissions/` (which commissions were executed?
  which never ran?); `docs/research/error-profiles/*` curriculum
  proposals vs what exists; `docs/GRAMMAR_STRATEGY.md` §8.
- LIVE state (read-only GETs only; `source ~/.config/idiomatic-admin.env`
  for `$ADMIN_TOKEN`, header `X-Admin-Token`, base
  https://idiomatic-app.onrender.com — NEVER paste the token itself into
  the report or logs):
  `/admin/grammar-stats`, `/admin/grammar-status`, `/admin/exercises2-list`,
  `/admin/translation-list`, `/admin/podcast-cards-list`,
  `/admin/podcasts-list`, `/admin/disk-usage`, `/health`.
- DB truth where endpoints fall short: none available to you — note the
  gap instead of guessing.

## Prior-knowledge from the orchestrating session (verify, then extend)

**Shipped (believed complete):**
- Exercises 2.0: legacy-corpus audit (docs/research/legacy-excercises-audit.md);
  IT corpus rebuild (2,589 renderings, data/exercises2/it_rebuild/);
  CONNECTING Wave 1 in 5 langs — es 207 / fr 191 / de 179 / pt 175 / it
  201 notes (2 cards each), apkgs ≥1337…1396; delivery wiring
  (idiomatic/grammar/exercises2.py, frozen model 1_820_150_001).
- Translation decks ×5 (idiomatic/grammar/translation.py, model
  1_820_160_001): es 250 / fr 146 / it 130 / pt 127 / de 79 cards;
  sentence-only back audio since apkgs 1390-94.
- Podcast cards eps 1, 3-9 shipped earlier (eps 2 & 10 PARKED —
  cross-language, need per-line language markers).
- ENOSPC incident fixed (docs/incidents/2026-08-04-enospc.md): orphan
  apkg janitor sweep, retention 30→12d, /admin/disk-usage endpoint.
- Wrong-profile delivery incident resolved: reset-acks recovery,
  profile-guarded cleanup.json in the local add-on (fires on next open
  of the +2 profile: purges fake-Italian legacy decks, 30 Spanish PT
  notes, and misdelivered copies).
- add-on hardening: _safe_refresh guard (NoneType.sched race).

**Open loops (verify status of each):**
1. CONDITIONALS Wave 2 staged — 15 chunk inputs + addendum committed;
   awaiting the user's "go". (docs/EXERCISES2_ROADMAP.md)
2. Roadmap waves 3-7: TENSES, FANCY_VOCAB, vocab trio, BIG_TECH_PHRASES
   as production prompts, FALSE_FRIENDS interference-matrix rebuild.
3. Old-account purge: has cleanup.json actually FIRED yet? (check
   whether ~/.var/app/net.ankiweb.Anki/data/Anki2/addons21/
   idiomatic_puller/cleanup.json still exists = not fired).
4. Legacy ES FALSE_FRIENDS deck (94 cards, ~half factually wrong) —
   purge never approved; decision pending.
5. Podcast eps 2 & 10 (cross-language) — blocked on per-line language
   markers in the explainer segment format.
6. Error-profile follow-through: proposed-but-never-created units
   (es_interferencia, es_muy_mucho, es_light_verbs, es_numeros_fechas,
   pt_gender_core, pt_regencia_verbal, pt_ser_estar_ficar,
   pt_es_contrastes, fr cluster-5-9 additions, de "5 Kasus" cluster
   pieces) — cross-check docs/research/error-profiles/*.md proposals
   against live curriculum units.
7. Grammar top-ups: units below target_size (live grammar-stats) — free
   generation capacity.
8. Pool-deck growth vs 10 GB disk (~4 GB pools, ~1.5 GB free before the
   IT/exercises builds): delta-pool redesign or paid disk upsize —
   undecided.
9. Two-agent per-profile delivery routing (kind-based) — offered,
   undecided; current single agent serves both Anki profiles and caused
   the misdelivery incident.
10. Mandarin/Memory-Palace commission (commit 86124c8, user-authored) —
    committed but never engaged by anyone.
11. ~6 demoted-but-delivered orphan cards linger in FR/DE exercises
    decks (harmless; cleanup.json candidate).
12. Videos marked failed during the ENOSPC window may need requeue
    (status='failed', 2026-08-04) — flag count if determinable from
    admin endpoints, else note as a DB check for the orchestrator.

## Hard rules

- Strictly read-only: no git writes, no POST admin calls, no file
  changes except writing `docs/STATE_OF_PLAY.md`.
- Never reproduce secrets/tokens in the report.
- Where you cannot verify a claim, mark it ⚠ unverified rather than
  asserting it.
- Sign off with a "what this report could not see" section (DB-only
  facts, other repos, the user's local Anki state).
