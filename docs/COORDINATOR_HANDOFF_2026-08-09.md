# Coordinator handoff — state as of 2026-08-09 late evening

> Successor: you are the COORDINATOR. The owner (flies Tuesday; gym
> daily) delegates aggressively: "make decisions as you see fit but get
> results"; keep codex saturated; owner decisions ship as interactive
> console pages, NEVER MD files; Mac work is direct-driven over SSH
> (never relay through the owner). Division of labor: codex = mechanical
> analysis/authoring; Fable agents (worktree-isolated!) = design/build;
> coordinator = review, merge, deploy, gates. Suite green before every
> push; never `pytest | tail` inside a `&&`-chain (masks failures — bit
> us twice).

## Credentials / access (all local, none in repo)
- `~/.config/idiomatic-admin.env`: IDIOMATIC_ADMIN_TOKEN (some tools
  want it re-exported as ADMIN_TOKEN), RENDER_API_KEY (full API access
  to the idiomatic Render account: env vars, deploys, logs, postgres
  connection-info), IDIOMATIC_DATABASE_URL (prod Postgres, external).
  File vars are NOT exported — use `set -a; source; set +a`.
- Mac: `ssh evgeny2026@192.168.110.65` (key auth; LAN flaps — retry
  loops; zsh quoting; never kill factory/bookscan; codex there needs
  `--skip-git-repo-check` under nohup).
- Agent token for /dj/plan etc: add-on config
  (~/.var/app/net.ankiweb.Anki/data/Anki2/addons21/idiomatic_puller/).

## DONE this weekend (all deployed on main, suite ~629 green)
1. ESTATE: collection migrated to six language roots; builders on
   anki_root(); cutover complete + documented (ANKI_ESTATE_REORG_PLAN
   COMPLETION NOTE). Rollback file collection.anki2.pre-estate-* kept.
2. LEGACY SWEEP: /legacy console (238 rows, owner verdicts PENDING);
   waves 1-3+5(geo)+6 merged (corpus 4,472+360 shadowing); local-Qwen
   voicing lane (qwen-local is LIVE primary TTS; ElevenLabs fallback
   only); English prompt audio on all exercises2.
3. HUB: models 1820180001/2 FROZEN (3 owner amendments incl. tile grid
   + context transcripts); phase-5 manifest sealed; executor rehearsed
   2x + rollback drill + independent verifier PASS; F4 adoptions (126)
   APPLIED to prod; pool guard live. AWAITING: owner cutover hour
   (phase-0 recensus on fresh copy first — corpus moves daily).
4. DJ: /dj live (observer+planner, honest budgets from measured ~59
   min/day census; pimsleur = PROVISIONAL hold pending triage; backlog
   amortization with ETAs). /triage console live (178 rows, verdicts
   PENDING). Slice 3 (add-on 0 Today materializer) commissioned
   tonight — feature-flagged OFF until armed.
5. GRAMMAR COURSE: engine + DE Kasus pilot SHIPPED AND VOICED (213
   local clips; apkg at idiomatic/grammar/data/course/book_local/,
   gitignored — book content NEVER enters the public repo). Both
   German corpora sealed in docs/research/grammar_books/ (gitignored):
   de_hammer_v1 (2,802 exercises) + de_hammer_ref_v1 (146 Hammer
   sections, join-check clean).

## RUNNING RIGHT NOW (watch for notifications / check logs)
- Corpus QA sweep (codex bg): contamination ("and"↔"und" class — the
  book's ANSWER KEY has typos; prompt is ground truth) + malformed
  fragment-construction solutions → de_hammer_v2 tarball + report.
  THEN: re-select/rebuild pilot vs v2; changed texts auto-requeue
  clips (stale mechanism); re-voice next window; rebuild --audio.
- Wave authoring runner (systemd idiomatic-wave-authoring): fancy_vocab
  (de+es done) then big_tech/cold_war remainders. Log:
  docs/research/legacy_estate/wave_authoring_run.log.
- Owner's codex window: 3-job queue (vocab authoring → fancy_vocab
  audit → HUB-C4 orphan proposals).
- Voicing: daily 09:00-11:00 window timer (idiomatic-tts-window.timer)
  + supervisor pattern for ad-hoc runs (thermal duty-cycle; CPU_TEMP_MAX
  85 — never raise, owner fan-noise rule).

## PIPELINE CHECKLIST when authoring/audit completes per topic
gate → hostile audit (cross-assigned: never audit own authoring) →
x2_wave_pipeline merge → snapshot-count test update → push (deploy) →
seed-full → voicing window → exercises2-build local_only ×5.

## OWNER GATES PENDING (his list, in his order)
1. Voiced Kasus pilot review (morning coffee).
2. Hub cutover hour (estate copy-back choreography; scripts + runbook
   in docs/research/anki_reorg_scripts/ + hub_manifest/PHASE5_*).
3. /triage taps (178 rows) → apply suspensions in the SAME collection
   window as the cutover (journaled executor).
4. /legacy verdicts (238 rows — can wait post-trip).
5. Wave-4 V1... already approved all three formats. Waves auto-flow.

## KNOWN LOOSE ENDS
- 3,041 hub orphan cards (12,367 reps) = expression-level backlog;
  C4 proposals feed an owner-gated creation wave (pilot-first).
- Shadowing (wave6) has NO builder/delivery yet (draft model only).
- Pimsleur scraper + Mandarin external builders bake old deck names.
- Media cleanup (~6.5 GiB) parked; +2 purge parked; /legacy imports
  gated. Stall-popup cap-idle false alarm fix: owner opt-in.
- DJ slice 3 must stay flag-OFF until the Italian pilot is armed.
- 105 stale QA verdicts + 177 unjudged images on the Mac (its judge
  handles at chunk boundaries); render-priority queue in C3 feeds the
  NEXT image campaign (post-trip; do NOT re-aim miners mid-trip).

## TRIP AUTOMATION CONTRACT (owner away ~10 days from Tuesday)
Desktop Anki stays OPEN (add-on = delivery + future 0 Today builder).
Miners go 24/7 from 08-10 (fan rule suspended). 09:00 voicing window
daily. DJ replans nightly. Coordinator sessions keep lanes moving and
report; owner reads summaries, taps consoles from the iPad if moved.

## LAST UPDATE (2026-08-10 ~02:30, end of predecessor's context)
- Geopolitics: repetition rewrite + independent re-audit SHIPPED
  (845ba77); 783 stale clips queued; 09:00 window voices; a monitor
  fires "run rebuild chain" → exercises2-build local_only ×5 +
  course_build_pilot de kasus --audio.
- German corpus v2 SEALED (sweep report in de_hammer_work/; splice +
  and→und repairs); Kasus pilot re-selected/rebuilt vs v2; its changed
  clips queued with the 783.
- DJ slice 3 shipped in the add-on, flag OFF; 9-step arming test plan
  in its report. Owner gates unchanged: voiced Kasus verdict, cutover
  hour, /triage taps, arm dj_today_enabled. Hammer REFERENCE prose is
  fully extracted (pass 4) — lesson authoring converts tables→SVG+
  narration per unit; extraction is NOT the bottleneck.
