# Session handoff memo — 2026-08-06 (Exercises 2.0 / Asset Factory orchestrator)

> Supersedes the 2026-08-03 memo (git history keeps it). Written at
> context exhaustion by the session that ran 2026-08-03→06: legacy audit
> → Exercises 2.0 waves 1+2 → translation decks → comic pipeline →
> Asset Factory strategy → famous cast. Read this + CLAUDE.md +
> auto-memory (legacy-excercises, exercises2-roadmap) and you can take
> over completely. Everything below is committed unless marked.

## Where everything stands (all shipped & verified)

- **Exercises 2.0**: Waves 1 (CONNECTING) + 2 (CONDITIONALS) live in all
  five languages — 1,772 notes / 3,544 cards (apkgs through 1521).
  Machinery: `idiomatic/grammar/exercises2.py`, content in
  `data/exercises2/notes/<lang>_<topic>.json`, per-chunk codex authoring
  via `docs/commissions/EXERCISES2_BATCH_COMMISSION.md` (+ CONDITIONALS
  addendum), gate `tools/x2_batch_gate.py`, `/admin/exercises2-build`.
- **Translation decks** ×5 (732 cards, sentence-only back audio):
  `idiomatic/grammar/translation.py`, `/admin/translation-build`.
- **Delivery**: SYLLABUS-ONLY policy (add-on `_IMPORT_PROFILES`
  allowlist; +2 profile is legacy, purge FIRED 2026-08-06 — old account
  clean). Render disk upsized to 26 GB (16.8 free). ENOSPC-era fixes:
  orphan-apkg janitor sweep, 12-day retention, `/admin/disk-usage`.
- **Asset Factory**: strategy + famous-cast amendment committed
  (`docs/ASSET_FACTORY_STRATEGY.md`, `…_FAMOUS_CAST.md`), **cast v1
  APPROVED 30/30** (`docs/ASSET_FACTORY_CAST_V1.md` — incl. user
  write-ins Juju/Capital Bra/Elodie/Fedez/Kevinho/Neubauer/Haddad; all
  exclusion-checked vs the Mandarin palace; Capital Bra added last —
  spot-check it with the famous-cast doc §1.3 checker before sheets).
- **Comic pipeline (proven on the Fedora box)**: t2i settings →
  Edit-2511 character insertion (sheet as image2) → bubbles TYPESET IN
  CODE (never model-rendered — this rule is load-bearing) → PIL stitch.
  ~4.5 min/strip, $0. Stack doc: `~/llms/qwen-image/LOCAL_QWEN_IMAGE.md`
  (read before any generation; batch-by-model, `/free` after, OOM
  history). Artifacts: worked examples …7e47d809…, head-to-head
  …f78fffec…, cast console …37ccf0c7….

## The task queue for the successor (dependency order)

1. **Swapfile on the Fedora box** — the ONE undone user item; blocks
   unattended overnights. Nag once:
   `sudo fallocate -l 32G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile && echo '/swapfile none swap defaults 0 0' | sudo tee -a /etc/fstab`
2. **Cast sheets**: ~45 faces (30 slots + wings). Max-quality mode
   (no-LoRA, 40 steps, ~7 min/face), refs from Wikimedia into
   `/srv/ai-models/outputs/factory/refs/` (MACHINE-LOCAL, never
   uploaded/committed — living-person policy, famous-cast doc §1.4).
   Gate: user names each face cold; 2 fails → recast (approved rule).
   Falco already failed the fast tier; retry only at max-quality.
3. **Mac Studio second node** (specs in CAST_V1 doc; 96 GB unified = no
   OOM problem): install ComfyUI + the same GGUFs, benchmark s/image,
   then run the same pull-based runner. **The user is AWAY ~10-11 days
   soon** — both machines should pregenerate maximally in that window:
   settings library (~70 views incl. BOTH Brazil AND Portugal
   pt-flavors), cast sheets, then corpus strips.
4. **Factory build-out**: commissions A–H in ASSET_FACTORY_STRATEGY §7,
   amended by user verdicts: NO per-comic approval (model-judge QA,
   N-best allowed), rescue deck DAILY + comic on back, combined back
   APPROVED, escalation 10 videos/mo cap, weirdness 1-in-6. Registry
   backend (B) first — it also fixes rescue's lease/history defects.
5. **Telemetry system** (user: "a must!!!"): per-topic review metrics
   from real Anki results driving generation targets; European langs
   first; a SEPARATE deeper Mandarin version later. Also the
   prerequisite of the comics→video escalation clock.
6. **Podcast eps 2/10**: scripts already have per-line `TL: [lang]`
   markers; `podcasts.py` hard-skips `lang: x` — build mixed-language
   parser/voice switching, render 2 MP3s, author 10 cards + 20 SVGs.
7. **Wave 3 TENSES**: verdict = RAW lapse order INCL. literary tenses
   (user explicitly wants passato remoto mastery). Needs its own
   addendum (like conditionals), canonical tense/person adapters, and
   morphology revalidation — the mined priors contain corrupt forms
   (STATE_OF_PLAY open loop 10). Then the same 15-chunk codex run.
8. **Rescue autopilot**: fix the no-lease concurrency bug; comic drafts
   migrate to the local pipeline "in the next few days" (user). Don't
   pause it; don't let it double-spend.

## Mechanics a successor must know (hard-won)

- **Codex delegation works**: 30+ chunks authored, 100% gate pass, zero
  linguistic errors found in sampling. Commission files + per-chunk
  `codex exec -s workspace-write` + orchestrator audit. Sessions REVISE
  landed outputs — always re-merge idempotently from latest outputs,
  never append.
- **Gate false-positives**: Romance elisions (l'/d') and circumflexes
  trip the wrong-language heuristic on it/pt — adjudicate by reading;
  the gate over-flags by design.
- **Never let a diffusion model render sentence text.** Typeset it.
- **Batch by model** (all t2i, then all edits), `/free` between phases;
  check `curl :8199/queue` before using the shared ComfyUI server —
  other sessions use it too. The server dies with its terminal; restart
  via `~/llms/qwen-image/start_comfy.sh`.
- **Decision flow with the user**: they hate typing AND hate jargon —
  plain human language only. The working pattern: clickable artifact
  console → `downloads` capability saves `idiomatic-verdicts*.json` to
  ~/Downloads → watch with the Monitor tool (NOT bash sleep loops —
  those get killed). Files sometimes land between watchers: CHECK
  ~/Downloads DIRECTLY before assuming nothing arrived. Screenshots of
  the console are readable as a fallback.
- **cleanup.json is single-slot** and was displaced TWICE by other
  sessions' jobs — verify existence before relying on it; queued
  cleanups are a commission-B deliverable.
- **The repo is the only shared brain** — the user runs many parallel
  sessions. Write everything durable into auto-memory, CHANGELOG,
  and the roadmap docs immediately.
- **Mandarin stays in mandarin-videos** (user directive): it is the
  primary Mandarin entry point; don't pull Mandarin work into
  idiomatic. Its sentence-format work is parked pending format
  decisions; its actor registry is the CAST EXCLUSION LIST here.

## Open user decisions

None blocking. Corpus-walk SCALE is decided after Mac integration
(model-judge QA + N-best already pre-authorized). All verdict rounds
are recorded in memory + CHANGELOG — do NOT re-ask answered questions.

## Quick verification commands

- Suite: `.venv/bin/python -m pytest tests/ -q` (374 green at handoff)
- Prod: `/admin/grammar-status`, `/admin/exercises2-list`,
  `/admin/disk-usage` (token: `source ~/.config/idiomatic-admin.env`)
- Batch gate: `.venv/bin/python tools/x2_batch_gate.py <chunks>`
- Exclusion check: script embedded in ASSET_FACTORY_FAMOUS_CAST.md §1.3
