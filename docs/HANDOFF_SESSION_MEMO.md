# Session handoff memo — idiomatic grammar initiative (as of 2026-08-03)

> Paste this into a fresh session to replace the 2026-07-31→08-03
> marathon session. Read CLAUDE.md alongside; auto-memory files exist
> under the project memory dir and largely agree with this memo. Where
> they conflict, this memo is newer.

## What this project is

Cloud service (Render) turning YouTube into Anki idiom decks, extended
since 2026-07 into a personalized 5-language GRAMMAR system
(es/de/fr/it/pt). Plan of record: docs/GRAMMAR_STRATEGY.md §8 (wave
checklist). The user studies grammar in the evgeny@the-syllabus.com
Anki profile; idioms live in evgeny.morozov+2@gmail.com; the add-on
delivers to whichever profile is open.

## Current state (all live in prod)

- **Decks**: es 288 / fr 185 / pt 165 / it 146 / de 101 = 885 cards,
  all with audio except F4 (text-only by design). One subdeck per
  topic cluster (`Idiomatic Grammar ES::1 Tiempos`; cluster strings
  FINAL — renaming orphans user subdecks). Cluster conventions:
  0 = listening ("0 Écoute"...), 9 = the user's own errors (F3),
  10 = interference (F4).
- **Curriculum**: 67 active units + 4 F4 units in grammar_units
  (code-owned cols re-seeded on boot from curriculum.py; status/
  target_size/notes are DB-mutable; PLANNED_UNITS is empty — all
  promoted). Card formats: F1 cloze, F3 attested-error (fmt='f3',
  from personal_errors), F4 interference (fmt='f4', DB-staged private
  pairs), explainer audio cards (fmt='explainer'). F2 interpretation
  is DESIGNED with 5×50-item banks (f2_*.json + F2_DESIGN.md) but NOT
  implemented.
- **Personal data layer** (~/projects/idiomatic-data/, NEVER in the
  public repo): errmine/ (personal_errors.jsonl registry, 11,481
  rows — also ingested into the DB), interference/ (F4 pair banks +
  matrix), vocab/ (clusters/goldlists/weave lists — weave lists match
  generate.py's extra_vocab shape, not yet wired), tuning/ (reject
  dumps), podcasts/ (local MP3 copies).
- **Podcasts**: 10 scripts in grammar/data/podcasts/. Episodes
  1,4,5,6,7,8,9 are v1 format (user REJECTED it: wall-of-text, LLM
  register — see memory content-pilot-first.md); ep03 (fr quantities)
  is the v2 PILOT: teacher voice, ear-training for de/des/du,
  3 practice rounds with [THINK:ms] piano under 6-8 s answer gaps,
  [CHIME] sections, [MUSIC:intro|outro] (CC BY assets in
  grammar/data/audio_assets/, attribution in LICENSES.md). Episodes
  2+10 (lang: x) need per-line TL-language markers before synthesis.
  v2 pilot AWAITS USER VERDICT; only after approval do the other nine
  get rewritten. NEXT CONCEPT (commissioned, not built):
  docs/commissions/PODCAST_CARDS_COMMISSION.md — episodes as ~10-card
  Anki lessons with generated images.
- **Renderer capabilities** (grammar/explainers.py, shared by
  explainer cards + podcasts.py): TL:-routed dual-voice TTS
  (ElevenLabs primary — overage billing ON, so Gemini-TTS fallback
  only fires on outages), [PAUSE:ms], [THINK:ms], [CHIME],
  [MUSIC:intro|outro], content-addressed clip cache, all ffmpeg via
  to_thread.
- **Other live systems**: LingQ mirror (~52k terms, cron-synced,
  woven into generation prompts); SUBTLEX freq weights
  (freq_weights_*.json, NOT yet consumed by generate.py); CEFR
  roadmap + Italian taxonomy (docs/research/CURRICULUM_ROADMAP.md,
  ~90 candidate units); grammar reader (docs/reader/, ~32 CC-BY
  chapters); dashboard /grammar + /grammar/unit/:key (the ONE
  dashboard surface allowed to mutate; admin token in
  ~/.config/idiomatic-admin.env).

## How work gets done here (user directives)

1. **codex fleet pattern**: bulk work → `codex exec` at
   `-c model_reasoning_effort="ultra"` ("ultra" IS the top tier, not
   xhigh). Write the full spec as docs/commissions/CODEX_X_*.md, run
   codex against it (code in isolated git worktrees under
   ~/projects/idiomatic-wt/, data in ~/projects/idiomatic-data/,
   `--skip-git-repo-check` outside git), NO git ops for codex, the
   supervising session reviews EVERYTHING and merges. Commissions A-R
   all shipped this way; review catches real bugs every time.
2. **Pilot-first** (user directive after the podcast v1 failure): ONE
   pilot of any new content format → approval → batch. Never batch
   unapproved formats again.
3. Premium session does: architecture, verification design, merges/
   review, incident response, user-facing content craft.

## Ops rules — each learned the hard way

- NEVER git-push while a grammar run is live (redeploy kills it;
  check /admin/grammar-status). Docs-only pushes count.
- Wait for deploys to SETTLE before calling new endpoints — the old
  instance's SPA fallback answers unknown /admin paths with HTML 200.
- Event loop: no synchronous ffmpeg/bulk work in the web process
  (docs/incidents/2026-07-31-web-hangs.md — this caused 3 outages;
  fixed with to_thread + per-lang rebuild locks + per-card stitch
  try/except).
- Bulk DB writes go cron-side: web stages ONE blob row, cron ingests
  (personal_errors + f4_pairs pattern). The cron container cannot see
  /data (only idiomatic-app mounts it).
- .gitignore `*.mp3` and `/data/` silently swallow new assets —
  scoped negations needed (bit us twice: Jehle DB, music assets).
- Disk: 10 GB, filled twice. Janitor sweeps media_stage + _pool_stage
  + delivered apkgs and logs disk usage each cycle; pool rebuilds
  clean their stage dir. Watch janitor.disk logs if adding big media.
- Pool rebuilds legitimately take 30-45 min/lang and run alongside a
  live API; a push during one kills it (harmless, next rebuild
  redoes it).
- The verifier-is-the-bug pattern: when a unit's rejection rate is an
  outlier, READ /admin/grammar-rejects before blaming the model
  (es_cmd_tu, de noun table, it_genere_plurali all verifier bugs;
  zero bad cards have ever shipped).
- Frozen model: `Idiomatic Grammar Drill v1` (MODEL_ID 1_820_130_001,
  14 fields) must NEVER change fields/templates; GUIDs =
  sha1("idiomatic-grammar::{lang}::{item_id}")[:16]. New content
  types get NEW models.
- Render MCP workspace "caii" (tea-cvnpo9c9c44c73agogo0); web
  srv-d8nbs7reo5us73epeehg, cron crn-d8nbs7reo5us73epeeh0, DB
  dpg-d8nbrtjeo5us73epe49g-a (read-only SQL via MCP works; NEVER
  restart the DB). Agent token: only in DB + add-on config.json
  (readable locally for testing agent-authed endpoints).

## Open threads, in priority order

1. **Podcast v2 pilot verdict** (user listening) → then: rewrite the
   other 9 episodes to v2 (codex vs approved template), mark TL lines
   in eps 2+10, and/or jump straight to the card-lesson concept
   (PODCAST_CARDS_COMMISSION.md — likely supersedes plain episodes).
2. **Wave 5 telemetry + planner** — the last unbuilt strategy pillar:
   add-on pushes revlog (note GUID keyed) → planner adjusts targets.
   Design notes in GRAMMAR_STRATEGY §6-7. The add-on is LOCAL code
   (not in git): ~/.var/app/net.ankiweb.Anki/data/Anki2/addons21/
   idiomatic_puller/__init__.py.
3. **F2 implementation** (banks + design ready).
4. Wire freq weights + vocab weave lists into generate.py prompts.
5. pt_regencia/pt_clitic verifier strictness: read rejects, tune à la
   commission J (dumps pattern in idiomatic-data/tuning/).
6. CEFR roadmap → next new-unit batches (N's ~90 candidates).
7. Explainer/podcast season 2 from reader chapters (flagged in
   docs/reader/README.md).

## Style notes for the successor

The user: thinks big, delegates decisions ("take the decisions you
think are necessary"), wants idle codex capacity USED, gives frank
content feedback (act on it, record it in memory), timezone +08. Be
direct, lead with outcomes, verify everything before claiming it
works — this session's credibility came from catching codex/self
mistakes before the user did (three prod incidents root-caused, wrong
theories revised in public). Commit+push frequently (respecting the
live-run rule); update CHANGELOG/FEATURES; keep personal data out of
the public repo.
