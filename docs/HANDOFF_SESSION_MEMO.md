# Session handoff memo — 2026-08-08 evening (image factory / QA loop / estate)

> Supersedes the 2026-08-06 memo (git history keeps it). Read this +
> CLAUDE.md + auto-memory and take over. Everything below is committed
> or machine-local at the stated paths. The user flew out the morning
> of 2026-08-11 for ~8 days (iPad studying only; machines pregenerate).
> STANDING DIRECTIVE: both boxes mint 24/7 until the brief queue is
> exhausted — no quiet-hours pauses while the user is away.

## What shipped since the last memo (all user-approved)

- **Estate cutover COMPLETE** — live collection migrated to the six
  language roots, builders compose from `anki_tree.anki_root()`,
  video/didactic/audio deliveries retired. Tree contract in CLAUDE.md.
- **Hub + estate decisions ALL CLOSED** (docs/research/*_DECISIONS.md).
  Hub BUILD not started; user inserted a pre-Hub priority: the legacy
  estate sweep (LEGACY_ESTATE_AUDIT_COMMISSION — partial: legacy_estate
  table + /legacy page live via another session).
- **Cast: 49 sheets, cloud lane (Qwen-Image 3.0 via /admin/
  genmedia-render), /cast review panel.** Remake loop proven.
- **Corpus illustration campaign**: ES briefs authored+gated through
  b18 (~1,300 of 2,712 sentences; chunks b19+ NOT yet authored — keep
  the codex conveyor going, then de/fr/it/pt exports). Renders on both
  machines, split by PARTITION.json (mac: b01-06+b10-18; fedora: rest).
- **Image QA loop ARMED 2026-08-08** after user calibration+demo:
  rubric v2 = hard fails ONLY people-integrity (count/gender/
  merge/duplicate) + anatomy; surrealism/action = soft ("surrealism
  doesn't matter" — user). Repairs live: judge work orders (tagged
  one-liners) → Edit-2511; 2 strikes → qa/human_review. Approved demos:
  qa_mirror/repair_demo.html. Morning report: qa_mirror/DAILY.md.
- **TTS**: qwen-local is the LIVE default on Render (bridge on this box,
  Tailscale Funnel). ElevenLabs = fallback. Rollback = env pin.

## Successor task queue

0. **Render order (user 2026-08-10): es → fr → it → pt, GERMAN LAST.**
   The `hold-es-first` entries in PARTITION.json stay in place — with
   de held, Fedora rolls through fr/it/pt automatically in glob order;
   no action needed at ES completion. Release the German hold (delete
   the entries, commit) only when giving de to a renderer — natural
   moment: as the Mac's next queue when its b19-26 chain runs dry
   (assign de chunks to mac in PARTITION + a run_queue script chained
   on the box — pattern: run_queue_b19_26.sh), or on Fedora after pt.
   ALL briefs are authored+committed (255 chunks, 5 langs) — rendering
   is the only remaining stage.

1. **Mornings**: read /srv/ai-models/outputs/factory/qa_mirror/DAILY.md;
   fix systemic failure modes at the RENDERER (prompt), not by softening
   the judge. human_review is NO LONGER the owner's job (directive
   2026-08-12): the cloud arbiter (qa-arbiter-daily.timer, 08:15) clears
   or upholds escalations — check qa_mirror/arbiter_log.jsonl instead.
2. **Prompt conveyor**: author ES b19-b38 (codex, 4 parallel, gate must
   PASS), then export/chunk/author de,fr,it,pt
   (/admin/corpus-export?lang=X → tools/illu_chunk.py → codex). Update
   PARTITION.json when assigning chunks to the Mac (24/7 node gets the
   bulk); commit so the Fedora miner sees it.
3. **Aug 10**: confirm Fedora miner went 24/7 (miner_stop no-ops from
   that date). Both boxes then pregenerate through the trip.
4. **After legacy sweep verdicts**: the Expression Hub build (its own
   commission needed; design docs are complete) — includes embedding
   images into cards (images key on expression_examples.id — restructure
   safe) and the Flag-1 telemetry.
5. Rescue Comics deck: rolling kind='rescue_comics', rebuild via
   ~/llms/qwen-image/factory/build_rescue_comics_deck.py (GUID-stable
   in-place updates).

## Hard-won mechanics (violate at your peril)

- **Mac**: ssh evgeny2026@192.168.110.56 — WIRED since 2026-08-11
  (ventilated room + Ethernet; 192.168.110.65 = its Wi-Fi, mac.lan =
  mDNS, both fallbacks). Renders/QA live in ~/llms/factory-node/. **Reboot recovery
  is AUTOMATED since 2026-08-10** (2nd kernel panic that day):
  launchd `com.idiomatic.boot-recover` runs
  ~/llms/factory-node/boot_recover.sh at login — clears stranded
  PAUSE_BOOKSCAN + judge lock, starts comfy, relaunches the queue
  chain (idempotent; log logs/boot_recover.log). Manual checklist
  only if that agent is broken. Bookscan does NOT auto-restart —
  owner starts it.
- **PAUSE_BOOKSCAN flag = the only way to pause bookscan.** NEVER
  SIGSTOP its driver (wedges children; cost 5h once). Judge batches
  raise/release it themselves and won't release a hold they didn't
  create.
- **Memory discipline on the Mac**: one giant at a time (mint ~50GB /
  judge 54GB / gemma 34GB in 96GB). Judge scripts unload ollama + need
  a 66GB cushion — a kernel panic (WindowServer starvation) taught
  this. Don't lower the cushion. ALSO (2026-08-08 incident): the judge
  tick now defers while `mac_render_chunk.py` is alive — a start-window
  check alone let an 11h judge/mint overlap fill 32GB swap and knock
  the box off the LAN in waves. If the Mac goes "slow but online" +
  SSH times out, check `vm.swapusage` FIRST, not the network.
- **Fedora night window** 01:30-09:00 (systemd user timers qwen-miner-*)
  until Aug 10 — the fans annoy the user; don't mint days before then.
  /tmp is RAM: don't park big files there (a 3.5GB tarball once ate the
  render headroom).
- **Don't deploy idiomatic-app while a cloud batch rides the server**
  (502s it). Announce deploys via CHANGELOG commits.
- **Edit-model prompting**: one change per edit pass, no
  "keep-everything" hedging alongside a structural change; never
  describe objects "like a <being>" (draws the being); second inserts
  must say IN-ADDITION/don't-duplicate/don't-replace.
- **User's working style**: plain language, no jargon; clickable local
  HTML consoles for decisions (pattern: page → verdict JSON to
  ~/Downloads → watcher applies); show files/paths for every claim;
  pilot-first before batching; they will call out lazy demos — pick the
  dramatic example.
- The repo is the shared brain across many parallel sessions — commit
  docs/CHANGELOG as you land things; coordinate via commissions.

## Live watchers/automation at handoff

- **Mac memory watchdog** (since 2026-08-12): launchd
  `com.idiomatic.memwatch` auto-kills the judge (L1 swap>25G rising)
  and repair walk + comfy /free (L2 >35G) during swap storms; alert =
  `qa/MEM_ALERT` (mirrored to qa_mirror by qa-sync, auto-clears when
  healthy). Check it whenever the Mac misbehaves — it may have already
  acted.


Fedora: qwen-miner timers; qa-sync.timer (30 min). Mac: launchd judge
tick (15 min) + minting queue chain (b10-18 pending). Rescue autopilot
daily on Render. No unfulfilled promises to other sessions.
