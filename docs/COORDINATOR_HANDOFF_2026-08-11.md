# Coordinator ledger — 2026-08-11 ~05:50 (+08), pre-compaction dump

> READ FIRST after context loss. Supersedes COORDINATOR_HANDOFF_2026-08-09.md
> (keep that for the weekend's history). Owner flies TODAY for 8 days
> (trip contract in the 08-09 doc still applies: desktop Anki stays
> open, miners 24/7, 09:00 voicing window daily, coordinator sessions
> keep lanes moving, owner taps consoles from iPad).

## WHAT HAPPENED 2026-08-10 → 11 (the two-day sprint)

1. **Course cards redesigned** (3 owner iterations in one morning):
   - Contract-2 enrichment sidecar per unit
     (`book_local/de_<unit>.enrichment.json`): concise task lines
     (German in `<i>` = serif italic), worked-example block, prompt
     echo on back, EN gloss (`Extra2`), Hammer-grounded why box
     (`Extra3`), and `solution_full_html` — the back DISPLAYS AND
     VOICES the complete requested sentence with insertions `<mark>`ed.
   - Validators: no-invented-German (i-span pool check), mark-span
     equality both directions; bad sidecar ABORTS build and seed.
   - Lesson sides: `EN:` display-only gloss lines under every `TL:`;
     2+ TL items render as a list; SVG geometry rules (arrows never
     cross text, heads stop 8-10px short of boxes).
   - Display and audio derive from ONE effective solution
     (`course.effective_solution_html`); seed payload substitution in
     `tools/course_seed_audio.py` means NO server-side change was
     needed for voicing to follow display.

2. **Entire 21-unit German course produced** (owner: "batch generate
   the entire course... do more german stuff on codex"):
   - Authoring: codex, one unit per `codex exec`, brief =
     `docs/commissions/CODEX_COURSE_UNIT.md` (plan schema v2:
     per-block `hammer_refs` verified against printed GGU headers,
     `:key` suffix = answer-key mode, selector self-check mandatory).
   - Enrichment: codex, brief = `docs/commissions/CODEX_COURSE_ENRICHMENT.md`,
     self-discovering runner (any `de_*.exercises.json` without a
     sidecar).
   - Coordinator review gate (ME, sentence-by-sentence hostile German
     read): 18/21 clean; edits in adjektive (1 narration line),
     modalverben (4 lines), rechtschreibung (kraft-example moved
     mid-sentence). RECURRING CODEX DEFECT: plan-internal jargon
     ("provenance-blocked", "atomic workbook block") leaking into
     SPOKEN narration — check every future lesson for it.
   - ch09 partikeln = LESSON-ONLY (all workbook sets provenance-
     flagged): empty-blocks support in `parse_exercises_payload` +
     `seed_course_audio` header check (both had `exercises[0]`
     IndexErrors — fixed, regression-tested).
   - Tooling (Fable agent, merged): DE_UNITS 21-chapter registry in
     course.py, generic `tools/course_select.py` (kasus byte-identical
     equivalence proven), `--production` deck routing →
     `anki_root('de')::2 Grammar::<unit_label>::{1 Lesson,2 Exercises}`.

3. **Production delivery built** (`POST /admin/course-apkg-upload`,
   lang+unit params, raw apkg body): rolling per-unit rows
   (kind=`course_<unit>`, unique on lang+kind), re-upload clears acks
   → add-on re-imports (client GUIDs stable). Files land in
   `DATA_DIR/apkgs/<lang>/course_<unit>.apkg`.

4. **Corpus waves finished**: big_tech_vocab (476 notes, audit 20/20)
   and cold_war_vocab (584, audit 30/30) merged ×5 → 5,532 EN keys;
   snapshot asserts in tests/test_x2_wave_pipeline.py updated twice.
   Exercises2 decks rebuilt ×5 FULLY VOICED (apkgs 1675-1679) incl.
   the geopolitics de-boilerplate rewrite.

5. **TTS policy + incidents**:
   - Owner directive: GPU is TTS's from 09:00 until queue drained or
     01:15; miners own 01:30-09:00. `idiomatic-tts-window.service`
     timeout now 58500s.
   - INCIDENT: SIGTERM-killed estate_window leaves a stale pause
     marker (`/run/user/1000/idiomatic-qwen-tts.pause` with dead
     token) → every later window dies "owned by another lifecycle" AND
     miners stay blocked (8h dual stall on 08-10). Fix: `rm` the
     marker iff no estate_window process is alive. Watchers must alert
     on THROUGHPUT STALL (completed static 30 min while queued>0),
     not just queue==0.
   - Mac Studio TTS node: fully installed (~/llms/qwen3-tts on the
     Mac; bridge `server/mac_app.py` port 8356; worker wiring in
     `worker_loop.sh` + `server/worker.env`) but qwen_tts on MPS =
     97-347s/clip vs ~3s CUDA → batches outlive the 900s lease,
     uploads discarded. STOPPED. Future: MLX port (post-trip codex
     project). Gotchas: non-login ssh needs
     `export PATH=/opt/homebrew/bin:$PATH` (ffmpeg!), token var is
     QWEN_BRIDGE_TOKEN there.

6. **/lingq console live** (e659a78): seven dormant-value concepts as
   verdict cards (dj_triage pattern, `lingq_verdicts` table,
   decisions-only). Research: docs/research/lingq/ (REPORT.md +
   LINGQ_VALUE_PROPOSAL.md committed-safe; data/ + lexicons GITIGNORED
   personal data — never commit). Key finding: LingQ = encounter log
   (95% status-0), not a graded lexicon; recommended pilot =
   C1 Second Encounter (FR, 60 cards). After owner taps: coordinator
   commissions the pilot (pilot-first doctrine).

## MECHANICS LEARNED (bit us; don't relearn)

- **Deploy race**: after `git push`, Render "live" status can precede
  the new instance actually serving; unknown /admin routes fall
  through to the SPA catch-all → HTML instead of JSON. Wait for the
  deploy of YOUR sha (or a descendant — other lanes push too:
  `git merge-base --is-ancestor`) + sleep 45-60s before admin calls.
- **`pytest -q | tail` inside `&&` masks failures** (bit us a third
  time on 08-10). Always capture rc explicitly.
- **Background `while systemctl is-active` watchers**: a oneshot
  service reports "activating" not "active" — `is-active --quiet`
  is FALSE while it runs. Check `--state` semantics or match on
  journal/log lines instead.
- **codex inside a `while read` loop eats stdin** → `< /dev/null` on
  every codex exec in runner scripts.
- **codex sandbox has no outbound network** → DB analysis jobs need
  local dumps (docs/research/lingq/data pattern).
- **codex may write outputs to its own /tmp** (lost partikeln plan) —
  demand repo-relative paths in briefs and verify files exist.
- **Course pilot-priority**: `local_tts_jobs` claims order
  `is_pilot DESC, id` — course seeds with `--pilot-priority` jump the
  queue; `--production` seeds is_pilot=false.
- **Rebuild is strict**: `/admin/local-tts/v1/exercises2/rebuild`
  refuses while ANY clip of that language's corpus is missing — no
  partial rebuilds; plan on full-drain rebuilds only.

## RUNNING / ARMED RIGHT NOW (05:50)

- 3,011 course clips queued; 09:00 window voices (~3.5h at ~15/min).
- Drain watcher (bg task bw9n12ti5): fires when queue==0 after 09:00
  → THEN: for each of the 16 undelivered units:
  `ADMIN_TOKEN=$IDIOMATIC_ADMIN_TOKEN .venv/bin/python
   tools/course_build_pilot.py de <unit> --production --audio`
  then `curl -X POST -H "X-Admin-Token: ..." --data-binary
   @book_local/course_de_<unit>.apkg
   ".../admin/course-apkg-upload?lang=de&unit=<unit>"`.
  Delivered already: kasus wortstellung praepositionen adjektive
  valenz (acks confirmed). Verify acks per upload
  (`agent_acks` rows, status ok).
- Miners own the GPU until 09:00 (illustration factory: fr→it→pt→de,
  managed by the owner's other session — do not touch).

## OPEN ITEMS

1. Course delivery tail (automated; verify acks, then update
   FEATURES/CHANGELOG delivered-state + mark Task #7 done).
2. fancy_vocab audit — owner's codex window queue; if stalled, run on
   our lane: audit brief `docs/commissions/CODEX_X2_WAVE_AUDIT.md`,
   75 chunks, then merge ×5 (expect ~+2,900 EN keys — update snapshot
   asserts), seed-full, window voices.
3. Owner gates: hub cutover hour + /triage taps (before flight or
   +8 days), /lingq taps (any time), /legacy (post-trip).
4. LingQ C1 pilot: commission AFTER owner greenlights on /lingq.
5. Post-trip parking lot: Mac MLX TTS port, hub C4 orphan wave,
   es/fr/... course languages (the factory generalizes: registry +
   corpus per language).

## CREDENTIALS / INFRA (unchanged from 08-09 doc)

`~/.config/idiomatic-admin.env` (IDIOMATIC_ADMIN_TOKEN as ADMIN_TOKEN
for tools, RENDER_API_KEY, IDIOMATIC_DATABASE_URL; `set -a; source;
set +a`). Mac: ssh evgeny2026@192.168.110.56 (wired; .65=wifi). Suite
runs `.venv/bin/python -m pytest -q` — 731 tests as of e659a78.
