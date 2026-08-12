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

## COMPLETION NOTE (2026-08-11 ~13:15)

COURSE DELIVERED END TO END: all 21 units acked `ok` by the add-on —
the complete voiced German grammar course is imported in the owner's
collection under `DE German::2 Grammar::<unit>`. (Repair en route:
wortbildung + zahlen were initially uploaded audio-less — their seeds
had been skipped in the review rush; caught by the identical-123KB
anomaly, re-seeded, topped-off, re-uploaded with audio_pending=0.
16,491 clips voiced lifetime.) Task #7 CLOSED. Open: fancy_vocab
audit, owner gates, LingQ pilot post-verdict.

## UPDATE 2026-08-12 ~05:40 (owner in Rome; token-critical session end)

- OXYLABS OUTAGE since 08-11 midday: youtube_download jobs fault
  (~420 failed; probe reproduces live). NOT our config (auth/submit
  ok). Recovery timer `oxylabs-recovery.timer` probes every 2h via
  ~/llms/oxylabs_recovery_probe.sh; on first success auto-requeues
  failures from last 4 days + disarms itself. Log:
  ~/llms/oxylabs_recovery.log. Needs prod env at
  scratchpad/prod.env (session-local! if scratchpad is gone, rebuild
  from Render env-vars API) — CHECK THE TIMER STILL WORKS in a new
  session; if scratchpad wiped, rewrite probe to source Render env
  directly. If outage >48h: owner should file an Oxylabs ticket.
- MINING: 24/7 mode confirmed real (496 images noon→dawn); owner
  re-blessed daytime mining from Rome. Nothing to change.
- FLAGGED-REVIEW LANE (new owner ask): 140 in-review flagged cards
  pulled headlessly (rescue_autopilot._pull_collection_blocking +
  ANKIWEB_HKEY). Split: 17 EUROPEAN pipeline cards (13 pool + 4
  grammar drill — audio/grammar defects; THE actionable set) + 123
  Mandarin (external builders — parked). Manifests in
  docs/research/flagged_reviews/; commission =
  docs/commissions/FLAGGED_REVIEWS_REMEDIATION.md. Codex diagnosis
  running (unit idiomatic-flag-diagnosis). NEXT SESSION: review
  DIAGNOSIS.md, execute phase-2 fixes (re-TTS/corpus fixes/pool
  rebuild), decide flag-clearing mechanism with owner (add-on
  cleanup.json extension vs manual). Make the flag pull a recurring
  session routine.
- Consoles still untouched: /lingq 0 verdicts, /triage 0/178.
  fancy_vocab audit still unrun (owner's codex window died with
  laptop) — next session should take it over per OPEN ITEMS.

## UPDATE 2026-08-12 ~15:45 (coordinator session, owner in Rome day 2)

- OXYLABS: still down (probe faults every 2h, result code 112; ~26h at
  session start). Probe HARDENED: env now at ~/.config/idiomatic-prod.env
  (durable; was a session-scratchpad path that silently no-op'd the probe
  if wiped), missing-env logs loudly, log lines carry timestamps again.
  >48h threshold = 08-13 midday → owner files ticket.
- FLAGGED-REVIEW PHASE 2 EXECUTED (13 of 17 live; delivery verified):
  - 6 (b) pool notes (4 pt + 2 es): audio nulled → seeded → voiced in an
    ad-hoc TTS window (inside the 09:00-01:15 ownership; queue was
    drained so the window had exited — restarted it, 17 clips, minutes).
    One suspect pre-flag local completion (job 396) force-requeued
    instead of silently reused — WATCH FOR THIS CLASS: seed-missing-only
    reuses completed jobs even when the completed clip is the bad one.
  - 3 text fixes: pt jogo-combinado board-game example replaced
    (GUID migrates), pt champanhe EN tautology rewritten (GUID stable),
    es dar-la-curva example rewritten INTO ITS SOURCE DOMAIN (San Fermín
    encierro) — the codex diagnosis's blanket tomar-la-curva was
    over-broad: the source phrase itself is encierro commentary.
    Pre-edit backup: docs/research/flagged_reviews/phase2_pre_edit_backup.json.
  - 4 IT grammar drills (text correct, audio bad): NEW audio_rev
    mechanism (meta.audio_rev → idg_it_<id>_r1.mp3; grammar/audio.py,
    translation.py, ui_api.py) — rebuilt, all 4 revved clips verified
    resolving. pt/es pools + it grammar apkgs all ACKED ok 15:13.
  - 4 flagged notes are ORPHANS (3 IT pool + es palanquear): source
    videos/idiom rows gone (slug-era). OWNER-GATED: recommend deletion
    via cleanup.json ('guarda caso' is re-taught by a live card;
    figuraccia/fruire would be lost — could re-enter via legacy lane;
    palanquear is wrong Spanish, should die).
  - cleanup.json STAGED in the add-on dir (profile-pinned syllabus) for
    the 2 migrated GUIDs — fires on next Anki restart.
  - RECURRING LANE TOOLED: tools/pull_flagged_cards.py (headless pull +
    flag extract + baseline diff). Ran 15:30: 140 flags, 0 new.
  - OWNER DECISIONS still open: orphan deletion; the 5 sibling
    dar-la-curva vehicle examples (standard is tomar la curva — full
    migration retires 6 cards' scheduling; I fixed only the flagged one);
    flag-clearing mechanism (add-on clear_flags extension vs manual).
- MANDATE 1 (course completeness, second pass) — AUDIT DONE, verdict:
  - Hammer coverage COMPLETE: 146 sections mapped, the only 21 uncited
    are unnumbered chapter headers. Zero material gaps.
  - Hygiene gate killed exactly 1 item course-wide — NOT over-strict;
    thin units are Pass-2 provenance-starved (partikeln 0/50 sets
    usable, wortbildung 6 kept, rechtschreibung 3, zahlen 15).
  - Remediation: ORIGINAL exercises, llm-generated provenance UNLOCKED
    (course.py PROVENANCES; card back renders {{Provenance}} visibly).
    Pilot-first: partikeln authoring running on codex
    (docs/commissions/CODEX_COURSE_ORIGINAL_EXERCISES.md). After my
    hostile review: enrich → seed → voice → build → upload, then batch
    wortbildung/rechtschreibung/zahlen the same way.
  - Data: docs/research/grammar_books/course_audit/ (machine-local).
- MANDATE 2 (Romance books) — DONE, report machine-local at
  docs/research/grammar_books/ROMANCE_BOOK_EQUIVALENTS.md: FR Towell/
  Lamy/Hawkins 5e 2025 + Practising French 5e (HIGH); ES Butt&Benjamin
  6e 2019 + Practising Spanish 4e (HIGH; 6e RENUMBERED vs 5e — get 6e);
  IT Maiden/Robustelli 2e + Practising Italian 1e (HIGH identity,
  MEDIUM extraction — pre-digital PDFs); PT: no Routledge pair EXISTS —
  Modern Brazilian Portuguese Grammar + Workbook 3e 2023 (MEDIUM-HIGH,
  BP-vs-EP is an owner call; 'Portuguese: A Comprehensive Grammar'
  retail listings are unpublished vaporware). Unit registries sketched
  per language in the report (17/24/21/24 units).
- fancy_vocab hostile audit RUNNING on our codex lane (76 chunks:
  es=16, others 15; log docs/research/legacy_estate/
  fancy_vocab_audit_run.log). Next: review → merge ×5 (update snapshot
  asserts) → seed-full → tomorrow's window voices.
- Consoles: /lingq 0 verdicts, /triage 0/178 — still awaiting owner taps.

## UPDATE 2026-08-12 ~15:40 — PARTIKELN PILOT DELIVERED

Original-exercises pilot (Mandate 1 remediation) went end to end in one
session: codex authored 44 items / 8 blocks (CODEX_COURSE_ORIGINAL_
EXERCISES.md), coordinator hostile review PASS-WITH-EDITS (11 ALT
additions where choice-bank contexts could not honestly exclude the
competing particle — codex's alternatives policy was principled but
under-inclusive; 2 wording fixes: bemerkt-Luftzug collocation, Klingle
imperative), enrichment sidecar generated + validated, 44 solution
clips voiced in an ad-hoc window, apkg built VOICED (8.3 MB, correct
L1..L10 interleave), uploaded as course_partikeln (apkg 1711, acks
cleared). PILOT-FIRST HOLD: wortbildung/rechtschreibung/zahlen originals
wait for the owner's reaction to the partikeln exercise cards (new
content class: llm-generated provenance, visibly marked on-card).

## UPDATE 2026-08-12 ~19:25 — FANCY_VOCAB WAVE SHIPPED

Audit 76/76 (36 PASS-WITH-EDITS, 196 edits, gate green) → merged ×5
(1,435 notes; corpus 5,532 → 6,967 EN keys; snapshot asserts updated,
suite 732 green) → seed-full 4,305 clips → window voiced everything by
19:19 (4,366 clips today incl. partikeln + flagged) → strict rebuild ×5
ALL FULLY VOICED (clips_missing=0): apkgs 1719-1723 (de 1406 / es 1289 /
fr 1289 / it 1280 / pt 1253 notes). Ack watcher armed. Exercises2
corpus waves: fancy_vocab was the last committed topic wave in
batches/output — the roadmap's remaining topics need fresh staging
(see docs/EXERCISES2_ROADMAP.md).
ACK CONFIRMATION ~19:40: all five exercises2 apkgs (1719-1723) acked ok
— the fancy_vocab wave is in the collection. Day's deliveries: 3
flagged-fix apkgs + course_partikeln + 5 exercises2 decks, all acked.
