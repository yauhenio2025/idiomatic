# Feature Inventory

> Auto-maintained by Claude Code. Last updated: 2026-08-07

## Ingestion

### Channel polling (cron)
- **Status**: Active
- **Description**: Every 2h, walks `channels` RSS feeds, enqueues unseen videos; per-channel title filters and duration overrides; queue auto-expiry (7 days).
- **Entry Points**:
  - `idiomatic/cron.py` - cron entrypoint
- **Dependencies**: YouTube Data API (duration pre-filter), YouTube RSS
- **Added**: pre-2026-07 | **Modified**: 2026-07-27

### Audio acquisition
- **Status**: Active
- **Description**: Oxylabs YouTube Downloader → Cloudflare R2 → worker downloads .aac.
- **Entry Points**:
  - `idiomatic/oxylabs_client.py` - job submit/poll/download
- **Dependencies**: Oxylabs, R2

## Processing pipeline

### Per-video idiom pipeline
- **Status**: Active
- **Description**: Claim → download → duration check → Gemini idiom extraction → enrichment (6 example pairs) → pimsleur-shape audio stitching → 21-field apkg → pool persistence.
- **Entry Points**:
  - `idiomatic/worker.py:278` - `process_video`, the whole per-video pipeline
  - `idiomatic/db.py:111` - `claim_next_video` (incl. stale-row reaper, daily-cap exclusion)
  - `idiomatic/pipeline/extract.py` - Gemini audio extraction
  - `idiomatic/pipeline/explain.py` - example-pair + structured-field enrichment
  - `idiomatic/pipeline/audio.py:144` - `render_card_audio` pimsleur stitching
  - `idiomatic/pipeline/apkg.py:193` - `build_apkg` (Idiomatic Cloud Card v2 model)
- **Dependencies**: Gemini 3.5 Flash, TTS provider chain (see below), ffmpeg

### TTS provider chain (qwen-local bridge)
- **Status**: Active
- **Description**: All TTS flows through `gemini.synthesize`: qwen-local (self-hosted Qwen3-TTS bridge on the home box, per-language clones of the ElevenLabs deck voices, cost 0) → ElevenLabs turbo v2.5 → Gemini TTS preview → silence marker. Memoized ~60 s health probe gives per-batch (not per-clip) failover; a 503 from the bridge's etiquette gate (ComfyUI rendering, thermals, VRAM) defers the batch to ElevenLabs. qwen usage writes cost-0 `gen_ledger` rows. Explicit `eleven_voice_id` callers (tenses decks, voice bake-offs) always go to ElevenLabs. Default flip to qwen-local gated on the acceptance drills in `docs/commissions/LOCAL_TTS_BRIDGE_COMMISSION.md`; rollback = `TTS_PROVIDER=elevenlabs`. Bridge itself is machine-local (`~/llms/qwen3-tts/server/`, systemd user service `qwen-tts-bridge`, Tailscale Funnel `https://fedora.tail363ee5.ts.net`).
- **Entry Points**:
  - `idiomatic/gemini.py:542` - bridge section (`QwenLocalDown`, `_qwen_healthy_url`, `_qwen_local_tts`, `_qwen_serves`)
  - `idiomatic/gemini.py:660` - `synthesize` provider chain
  - `idiomatic/settings.py:51` - `tts_provider` + `qwen_tts_*` knobs
  - `tests/test_tts_routing.py` - routing + failover-memo coverage
- **Dependencies**: Qwen3-TTS bridge (machine-local), ElevenLabs, Gemini TTS
- **Added**: 2026-08-07

### Language pools (4 decks per language)
- **Status**: Active
- **Description**: `pool_expr` (→ `<ROOT>::1 Expressions::1 Fluency`) rebuilt per language with 30-min debounce; `pool_idioms` + audio pools gated off since the 2026-08-07 estate cutover (settings flags).
- **Entry Points**:
  - `idiomatic/pipeline/pool.py:563` - `rebuild_pools`
- **Dependencies**: staged per-card mp3s in `/data/staged_audio/`

### Disk janitor
- **Status**: Active
- **Description**: Worker-side sweep of `/data/media_stage` (>2 days) and delivered video apkgs past retention.
- **Entry Points**:
  - `idiomatic/worker.py:172` - `run_janitor`
- **Added**: 2026-07-27

## Delivery

### Agent API + Anki add-on
- **Status**: Active
- **Description**: Add-on (local, not in git) polls `/apkgs/pending`, downloads, imports on Qt main thread, acks; one-shot `cleanup.json` purge mechanism. Since 2026-08-05 the add-on also auto-syncs with AnkiWeb programmatically (after every import batch + every 30 min, full-sync conflicts never auto-answered) — desktop Anki needs no manual open/close.
- **Entry Points**:
  - `idiomatic/api.py:109` - `/apkgs/pending`
  - `idiomatic/api.py:135` - `/apkgs/{id}/download`
  - `idiomatic/api.py:151` - `/apkgs/{id}/ack`
- **Dependencies**: agent bearer token (DB `agents` row)
- **Added**: pre-2026-07 | **Modified**: 2026-08-05

### Anki collection reconciliation (orphan adoption)
- **Status**: Active
- **Description**: Diff the user's Anki collection against the live catalog and re-adopt studied orphan notes (cards whose server rows were purged/superseded) into `adopted_notes`; never-studied orphans are deleted via the add-on's cleanup.json. Feeds the adaptive-study initiative (docs/research/ANKI_STATS_POC.md).
- **Entry Points**:
  - `idiomatic/api.py:317` - `GET /admin/anki-guids` (current guid export per kind)
  - `idiomatic/api.py:326` - `POST /admin/adopt-orphans`
  - `idiomatic/pipeline/adoption.py` - guid computation + adoption logic
  - `idiomatic/db.py:468` - `upsert_adopted_notes`
- **Dependencies**: `ADMIN_TOKEN` env; `adopted_notes` table (db/schema.sql)
- **Added**: 2026-08-05

### Flagged-review remediation lane (recurring)
- **Status**: Active
- **Description**: Owner flags problem cards during reviews; each coordinator session pulls the collection headlessly, diffs flags against the committed manifest, and feeds NEW European pipeline cards through diagnosis (codex, read-only) → phase-2 fixes (audio nulls + expression-pool seed + rebuild; grammar `audio_rev` bumps; text corrections with GUID migration via cleanup.json). Mandarin flags are parked for the external builders' repos. Commission: docs/commissions/FLAGGED_REVIEWS_REMEDIATION.md.
- **Entry Points**:
  - `tools/pull_flagged_cards.py` - one-command headless pull + flag extraction + baseline diff (needs `ANKIWEB_HKEY`)
  - `docs/research/flagged_reviews/` - manifests, DIAGNOSIS.md, phase-2 pre-edit row backup
  - `idiomatic/rescue_autopilot.py:60` - `_pull_collection_blocking` (download-only sync guard)
- **Dependencies**: anki lib in .venv, prod env file (`~/.config/idiomatic-prod.env`), local-TTS queue for re-voicing
- **Added**: 2026-08-12

### Rescue autopilot (autonomous struggle → draft-asset loop)
- **Status**: Active
- **Description**: Daily worker-scheduled loop: headless download-only AnkiWeb pull on Render → struggle list from revlog (≥3 Agains/14d) → snapshot upsert + auto-activation → ladder-driven draft generation (glyph + strike-1 comic) on autopilot-approved Chinese image providers under a hard per-run budget → report to kv_store + dashboard Autopilot card. Never approves assets; never uploads to AnkiWeb.
- **Entry Points**:
  - `idiomatic/rescue_autopilot.py` - pull, struggle computer, planner, run loop
  - `idiomatic/rescue_ops.py` - shared generate-and-store path (endpoint + autopilot)
  - `idiomatic/genmedia.py` - provider registry incl. qwen-image-3.0-pro (default, $0.037), qwen-image-2.0, qwen-image-2.0-pro, seedream-5.0-pro; Nano Banana manual-only
  - `idiomatic/worker.py:592` - scheduling hook (janitor cadence)
  - `idiomatic/api.py` - `POST /admin/rescue/autopilot-run`
  - `idiomatic/ui_api.py` - `GET /ui/api/rescue/autopilot`
  - `frontend/src/pages/RescueLab.tsx` - Autopilot card
- **Dependencies**: `ANKIWEB_HKEY`/`ANKIWEB_ENDPOINT`, `DASHSCOPE_API_KEY`, `ARK_API_KEY` (Render env); `anki` pip package
- **Added**: 2026-08-05

### Personal Study DJ (slices 1-3: observer + planner + add-on materializer)
- **Status**: Active
- **Description**: Daily worker-scheduled loop (reusing the rescue autopilot's headless download-only AnkiWeb pull): classifies every card into a population by estate deck lane (`1 Expressions` … `8 Pimsleur`, plus the `idiomatic-podcast` tag), computes due backlog / new-card reservoir / observed median secs-per-rep (priors where thin) / last-7-days study distribution, then builds a per-language daily SESSION PLAN — due reviews first (overflow flagged, never dropped), remaining budget to a weighted new-card mix (v1 curriculum-forward weights; weakness-clustering hook wired but identity). Plan JSON schema v1 in the module docstring. Slice 3 (2026-08-09, in the MACHINE-LOCAL add-on, not in this repo): on profile open + Tools → Idiomatic → "Rebuild 0 Today", gated by add-on config `dj_today_enabled` (default false until the Italian pilot is armed at the owner gate), fetches `GET /dj/plan` and materializes one filtered deck per language under `0 Today::<Root>` — term 1 = plan due.search (order due, limit due.limit), term 2 = `cid:` union of the new mix in authored due-position order (never shuffled), reschedule on; stale-language decks emptied+deleted; stale plan day still materializes with a "(yesterday's plan)" toast.
- **Entry Points**:
  - `/home/admin/.var/app/net.ankiweb.Anki/data/Anki2/addons21/idiomatic_puller/__init__.py` - `_dj_materialize_today` + helpers (slice-3 materializer; machine-local)
  - `idiomatic/dj.py:236` - `compute_observations` (observer over the pulled snapshot)
  - `idiomatic/dj.py:364` - `build_plan` (pure planner)
  - `idiomatic/dj.py:335` - `weakness_weights` (the v1-identity weakness hook)
  - `idiomatic/dj.py:568` - `run_dj` (pull → observe → plan → report)
  - `idiomatic/worker.py:605` - scheduling hook (janitor cadence, daily self-gate)
  - `idiomatic/api.py:2130` - `POST /admin/dj-budgets` (sanctioned mutation)
  - `idiomatic/api.py:2144` - `POST /admin/dj-run` (force a run)
  - `idiomatic/api.py:2162` - `GET /dj/plan` (agent token — the slice-3 feed)
  - `idiomatic/ui_api.py:874` - `GET /ui/api/dj/overview` + `/ui/api/dj/plan`
  - `frontend/src/pages/DJ.tsx` - the /dj dashboard page
  - `db/schema.sql` - `dj_plans` table (one plan per day)
- **Dependencies**: `ANKIWEB_HKEY`/`ANKIWEB_ENDPOINT` (Render env; without them plans build from cached observations), `anki` pip package, kv_store (`dj_budgets`, `dj_observations_last`, `dj_last_report`, `dj_last_run_ts`); slice 3: the idiomatic_puller add-on + its agent token
- **Added**: 2026-08-09 | **Modified**: 2026-08-09 (slice 3 materializer)

### DJ-C2 curation triage console (decisions only — executor lane applies)
- **Status**: Active
- **Description**: Owner verdict surface over the committed DJ-C2 census (178 subtrees incl. per-level Pimsleur): `/triage` page grouped language → lane with rationale, evidence chips, census proposal pre-highlighted, one-tap verdicts (accept-proposal / keep-active / suspend-reference / sample-hardest / defer) + notes, bulk accept-all, sticky per-language due-minutes projection recomputed under current verdicts (most-specific wins, lane cascades, undecided unchanged — validated to reproduce the census projections exactly). Boot seeds `dj_triage` only while empty; reseeds never touch owner verdict columns (legacy_estate doctrine). NOTHING here applies dispositions to any collection — the executor lane does, owner-present.
- **Entry Points**:
  - `idiomatic/dj_triage.py:45` - `load_evidence` (census loader/validator + row flattener)
  - `idiomatic/dj_triage.py:157` - `resolve_disposition` (verdict cascade rule)
  - `idiomatic/dj_triage.py:199` - `project_languages` (per-language minutes under verdicts)
  - `idiomatic/db.py:173` - `seed_dj_triage` (upsert, owner columns excluded)
  - `idiomatic/db.py:267` - `seed_dj_triage_if_empty` (boot path)
  - `idiomatic/api.py:2180` - `POST /admin/triage-verdict` (single verdict/note)
  - `idiomatic/api.py:2217` - `POST /admin/triage-verdict-bulk` (accept-all-unverdicted)
  - `idiomatic/ui_api.py:920` - `GET /ui/api/triage` (rows + summary + projections)
  - `frontend/src/pages/Triage.tsx` - the /triage console page
  - `db/schema.sql:997` - `dj_triage` table
  - `docs/research/dj_census/triage_evidence.json` - committed census evidence (seed source)
- **Dependencies**: DJ-C2 census artifact (committed), admin token
- **Added**: 2026-08-09

### Admin API + dashboard
- **Status**: Active
- **Description**: Admin-token endpoints (backfills, retts, rebuild-pools, rotate-agent-token) + React SPA dashboard with read-only `/ui/api/*`.
- **Entry Points**:
  - `idiomatic/api.py:194` - admin endpoints start (`/admin/audio-audit` …)
  - `idiomatic/ui_api.py` - dashboard JSON API
  - `frontend/` - React SPA
- **Dependencies**: `ADMIN_TOKEN` env

## Expression Hub (build track — branch `hub-build`, not deployed)

### Durable-ID schema staging + frozen hub models (owner-approved) + phase-5 toolchain
- **Status**: Active on branch `hub-build` (models FROZEN by owner verdict 2026-08-09; live cutover coordinator/owner-gated)
- **Description**: F1-F3 of the Hub build — additive boot-migration staging for canonical expression/sense/example identities, the note-binding crosswalk, and the snapshot/delta release ledger; owner-approved frozen Anki models `1820180001` (hub note, 2 cards: TL-front tile-grid card + amended EN→TL production card, context clips on both backs) and `1820180002` (EN→target fluency example); checksummed phase-5 manifest compiler (C1+C2+server extract) and the copy-only journaled executor/verifier/rollback, rehearsed twice + rollback-drilled on live-cutover clones. Design of record: `docs/research/EXPRESSION_HUB_DESIGN.md` + `EXPRESSION_HUB_DECISIONS.md` (OWNER VERDICT section).
- **Entry Points**:
  - `db/schema.sql:643-950` - EXPRESSION HUB durable-ID staging block (identity columns/backfills, aliases, bindings, release ledger)
  - `idiomatic/hub/identity.py` - frozen GUID/source-key/stable-key/media-name recipes (pilot GUIDs in a separate namespace)
  - `idiomatic/hub/apkg.py` - frozen models + tile-grid templates + `build_hub_apkg()` (production decks from `anki_root`; pilot routes under `ZZ Hub Pilot (disposable)`)
  - `idiomatic/hub/phase5.py` - join normalization, manifest compile/load (self-checksummed), conversion field plans, connection-level verifiers, bindings export
  - `docs/research/anki_reorg_scripts/hub_phase5_compile.py` - expectations-gated manifest compiler
  - `docs/research/anki_reorg_scripts/hub_phase5_execute.py` - copy-only executor (model install via Anki importer, in-place conversions, hub creation, quarantine archive, gates)
  - `docs/research/anki_reorg_scripts/hub_phase5_verify.py` - standalone gate re-run
  - `docs/research/anki_reorg_scripts/hub_phase5_rollback.py` - journal-driven rollback to logical pristine
  - `tools/build_hub_pilot.py` - pilot selection (admin API) + media staging + offline rebuild (`--out hub_pilot_v2.apkg`)
  - `idiomatic/hub/adoption.py` - F4 adoption plan builder (C2 join parity, deterministic anki:v1 keys), INSERT-only applier SQL, results export, extract merge
  - `docs/research/anki_reorg_scripts/hub_adoption_analyze.py` - read-only adoption analyzer (fresh corpus + collection copy -> checksummed plan)
  - `tools/hub_adoption_apply.py` - triple-gated INSERT-only applier (plan sha, F1 staging probes, --apply + coordinator go-token)
  - `tools/hub_adoption_rehearse.py` - full adopt->recompile loop on ephemeral Postgres
  - `docs/research/hub_manifest/PHASE5_REHEARSAL.md` + `F4_ADOPTION_RECORD.md` - rehearsal records + gap analysis
  - `tests/test_hub.py` - recipes, frozen shapes, grid, apkg round-trips, phase-5 compiler, adoption matrix, asset enrichment, ephemeral-Postgres schema staging
- **Dependencies**: genanki, anki (executor), asyncpg (tests/applier), admin API + QA verdicts store (pilot/analyzer refresh only)
- **Added**: 2026-08-09 | **Modified**: 2026-08-09

## Grammar

### Grammar drill pipeline (5 languages)
- **Status**: Active
- **Description**: LLM-generated grammar drills (verb morphology + closed-class), deterministically or blind-fill verified, compiled into one rolling `kind='grammar'` apkg per language with **one subdeck per topic cluster** (`<ROOT>::2 Grammar::{cluster}` since the 2026-08-07 estate cutover; `9 …` error clusters → `<ROOT>::6 My Errors`; roots from `idiomatic/anki_tree.py`). Strategy: `docs/GRAMMAR_STRATEGY.md`.
- **Entry Points**:
  - `idiomatic/grammar/morphology.py` - conjugation truth tables + verifier (Jehle es, verbecc fr/it/pt, german-nouns de)
  - `idiomatic/grammar/curriculum.py` - 61 active units across es/de/fr/it/pt; `cluster` per Topic (`CLUSTER_BY_KEY`), `PLANNED_UNITS`, `unit_seed_rows()`
  - `idiomatic/grammar/f4.py` - strict private-bank validation, Unicode answer signatures, deterministic A/B/C card mapping, staged ingest, and conversion for es/pt/fr/it
  - `idiomatic/api.py` - admin-only `/admin/f4-pairs-upload|status` and `/admin/f4-convert`; cron performs the private bulk ingest
  - `idiomatic/grammar/generate.py` - Gemini batch generation + item verification (Tier A morph / Tier B blind-fill)
  - `idiomatic/grammar/apkg.py` - frozen 14-field `Idiomatic Grammar Drill v1` model, GUIDs from DB ids; `deck_name_for()` + per-cluster genanki decks
  - `idiomatic/grammar/service.py` - orchestration + rolling deck rebuild
  - `idiomatic/api.py:330-518` - `/admin/grammar-generate|status|stats|rejects|rebuild`, `/admin/grammar-deckmap` (agent-authed, add-on reorganize), `/admin/grammar-unit/{key}`, `/admin/grammar-topup/{key}`, `/admin/grammar-retire-item/{id}`
  - `db/schema.sql` - `grammar_items` (verified/rejected/retired), `grammar_units` (cluster, status, target_size — code-owned cols re-seeded on boot), and private `f4_pairs` + staging
  - `tests/test_grammar.py` - morphology, verifier, apkg/GUID stability, subdeck split, seed completeness, audio_rev naming
  - `idiomatic/grammar/audio.py` - back-audio TTS + `audio_rev` media naming: `meta.audio_rev` on a row renames its clip `idg_<lang>_<id>_r<rev>.mp3`, forcing regeneration + Anki media update for unchanged text (drills, translation decks, and the dashboard unit page all resolve the revved name)
- **Dependencies**: Gemini text model, genanki, pinned `regex` grapheme segmentation, vendored morphology DBs
- **Added**: 2026-07-28 | **Modified**: 2026-08-12

### Grammar dashboard section
- **Status**: Active
- **Description**: `/grammar` curriculum tree (per-language clusters → units with verified-vs-target progress, reject rates, Top up / Rebuild controls, live run polling) + `/grammar/unit/:key` detail (settings editor, verified mini-cards with audio + retire, rejects diagnostics). First dashboard surface allowed to mutate state (grammar only).
- **Entry Points**:
  - `idiomatic/ui_api.py` - `/ui/api/grammar/overview`, `/ui/api/grammar/units/{key}`, `/ui/api/audio/grammar/{lang}/{file}`
  - `frontend/src/pages/Grammar.tsx` - curriculum tree page
  - `frontend/src/pages/GrammarUnit.tsx` - unit detail page
  - `frontend/src/api.ts` - `adminCall()` (admin-token actions from the SPA)
- **Dependencies**: Admin API + dashboard
- **Added**: 2026-07-31

### Podcast lesson cards (pilot: fr episode 3 — format approved)
- **Status**: Active (episode 3 shipped + user-approved; batching episodes 1, 4-9 is next)
- **Description**: Grammar-walk episodes decomposed into ~5 two-sided Anki notes: each side has its own stitched narration (shared explainer clip cache), big-font HTML, and an authored SVG diagram inlined into the field (night-mode themed via shared `s-*` CSS palette, no JS/media; generated images remain a per-side `IMG:` option for mood scenes). Spoken flip/next-card cues chain the sides; practice answers are audio-only (`TL-:`). Own frozen 14-field `Idiomatic Podcast Lesson v1` model; delivered as `apkgs.kind='podcast_lesson'` per lang into `<ROOT>::2 Grammar::0 <listening>::NN <title>` subdecks with zero add-on changes.
- **Entry Points**:
  - `idiomatic/grammar/podcast_cards.py` - markup parser ([CARD]/[SIDE]/TITLE:/SHOW:/TL-:/SVG:/IMG:), side HTML, `load_side_svg` sanitizer, audio/visual staging, model + apkg build, `build_episode()`
  - `idiomatic/grammar/data/podcast_cards/fr_quantity-system.md` - authored pilot source (5 cards × 2 sides)
  - `idiomatic/grammar/data/podcast_cards/svg/` - 10 authored diagram sidecars (episode 3)
  - `idiomatic/gemini.py:203-286` - `generate_image()` (Nano-Banana-Pro-class, atomic write, fail-loud, no placeholders)
  - `idiomatic/api.py:758-792` - `POST /admin/podcast-cards-build?lang&episode`, `GET /admin/podcast-cards-list`
  - `tests/test_podcast_cards.py` - parser/HTML/GUID/apkg/SVG-sanitizer/image-cache coverage
- **Dependencies**: explainer renderer + clip cache (`idiomatic/grammar/explainers.py`), season-1 podcast sources/stage dir (`idiomatic/grammar/podcasts.py`), `gemini_image_model` setting (`gemini-3-pro-image-preview`), genanki
- **Added**: 2026-08-03 | **Modified**: 2026-08-03

### Grammar Course units (pilot: de kasus — format approved; audio lane live; card redesign 2026-08-10)
- **Status**: Active (engine + DE Kasus pilot built 2026-08-09; owner approved format same day and ordered audio — narration lane implemented; voicing window + `--audio` rebuild run by coordinator. 2026-08-10 owner-driven card redesign: contract-2 enrichment sidecar `book_local/<lang>_<unit>.enrichment.json` — concise task lines with italic-serif German, worked-example block, prompt echo, EN gloss, Hammer-grounded why box, and full requested solution sentences displayed AND voiced via effective-solution substitution (no server change); lesson sides render TL example lists with display-only `EN:` glosses (narration segments byte-identical) and re-laid SVGs. Validators: no-invented-German i-span pool check, mark-span equality rules; bad sidecar aborts build/seed.)
- **Description**: Book-grounded course units per docs/commissions/GRAMMAR_COURSE_COMMISSION.md: ~10 two-sided lesson cards (audio-first EN narration + TL examples, authored SVG diagrams, per-side Hammer `REF:` Sources footer) plus a distinct population of ATOMIC book-derived exercise cards (German prompt → full solution with `<mark>` highlight + §-refs). Two frozen models: `Idiomatic Course Lesson v1` (1_820_190_001, 14 fields) and `Idiomatic Book Exercise v1` (1_820_190_002, 15 fields). First exposure sequenced by new-card due positions (lesson card → its exercise block); units land at `<ROOT>::2 Grammar::<unit>::{1 Lesson,2 Exercises}`, pilots under a disposable root. Book content (Practising German Grammar / Hammer corpora) confined to gitignored `data/course/book_local/` — the public repo never carries it. Telemetry keys are tags (`idiomatic-course-block::<lang>::<unit>::cNN`, `idiomatic-course-src::<provenance>`). Design of record: docs/GRAMMAR_COURSE_DESIGN.md; pilot review sheet: docs/GRAMMAR_COURSE_PILOT_NOTES.md.
- **Entry Points**:
  - `idiomatic/grammar/course.py` - frozen models, lesson parser (`[CARD]`/`[SIDE]`/`TITLE:`/`REF:`/`SVG:`/`SHOW:`/`TL:`), exercise loader + structural hygiene gate, `interleave_plan()`, `build_course_apkg()`
  - `idiomatic/grammar/data/course/lessons/de_kasus.md` - authored 10-card Kasus lesson (Hammer ch. 2 grounded)
  - `idiomatic/grammar/data/course/lessons/svg/` - 9 authored diagram sidecars (house `s-*` palette)
  - `tools/course_select.py` - generic plan-driven sealed-corpus selector (2026-08-10; kasus one-off retired, byte-identical output proven); plans in `idiomatic/grammar/data/course/plans/`; DE_UNITS registry (21 chapters) in `idiomatic/grammar/course.py`; `--production` builds route to `anki_root('de')::2 Grammar::<unit_label>`
  - `tools/course_build_pilot.py` - disposable-pilot APKG build; `--audio` resolves the unit's clips via the admin API (strict checksums, graceful audio-pending), stitches sides, drops the pending tag per voiced note
  - `tools/course_seed_audio.py` - POSTs the unit's seeding request (exercises as payload)
  - `idiomatic/local_tts.py` - course seeding contract: `course_lesson_job_rows` (one job per speech segment, `segNNN`, per-segment voice routing), `course_exercise_job_rows` (`solution` clips), `seed_course_audio`, `course_audio_status`, `match_course_completions`, `course_staged_path`
  - `idiomatic/grammar/course.py` - `stitch_side_narration` (house leveling/pauses/gaps, uniform 24 kHz transcode), `solution_spoken_text`, `parse_exercises_payload`
  - `idiomatic/api.py` - `POST /admin/local-tts/v1/course/seed`, `GET /admin/local-tts/v1/course/status`, `GET /admin/local-tts/v1/clip`
  - `db/schema.sql` - `local_tts_jobs.clip_kind` CHECK extended (`solution`, `seg[0-9]{3}`) via the DO-block boot migration
  - `tests/test_course.py`, `tests/test_course_audio.py` - frozen shape, GUIDs, interleave arithmetic, build output, copyright gitignore guard; seeding contract, spoken-text rules, stitch plan, partial-voicing build
- **Dependencies**: `explainers._segments` narration routing + leveling helpers, `pipeline/audio.py` silence/concat, `anki_tree.anki_root`, genanki (per-note `due`); extracted `docs/research/grammar_books/de_hammer_v1` + `de_hammer_ref_v1` corpora (machine-local); local-Qwen queue (worker untouched — clip_kind opaque, lang drives voice)
- **Completeness (2026-08-12 second-pass audit)**: all 146 Hammer sections cross-mapped against plan `hammer_refs` + lesson `REF:`s — every real numbered subsection is taught; hygiene gate killed exactly 1 item course-wide; thin units (partikeln/wortbildung/rechtschreibung/zahlen) are Pass-2-provenance-starved, remediated by ORIGINAL exercises under the now-unlocked `llm-generated` provenance (visibly rendered by the card's cx-refs line; pilot: partikeln). Audit data machine-local in `docs/research/grammar_books/course_audit/`; commissions: `CODEX_COURSE_COVERAGE_AUDIT.md`, `CODEX_COURSE_ORIGINAL_EXERCISES.md`.
- **Added**: 2026-08-09 | **Modified**: 2026-08-12

### Exercises 2.0 (rich EN→TL usage notes; pilot: es connecting — format approved)
- **Status**: Active (Waves 1–3 shipped in all five languages with local-Qwen audio, apkgs 1621-25; Waves 4–6 formats owner-approved 2026-08-09 — Wave 6 BIG_TECH_PHRASES merged de/es/fr/it at 90 shadowing notes each via the topic-dispatched merge lane, pt blocked on the staged rows 31-40 gap chunk; Waves 4–5 authoring in flight)
- **Description**: Revival of the 2023 legacy EXCERCISES corpus (see docs/research/legacy-excercises-audit.md) as rich notes: EN prompt → TL main rendering + accepted alternatives, register line, interference trap, in-register example, pre-rendered cloze. Content is codex-authored against commissions, independently audited, mechanically gated, and committed as JSON under `data/exercises2/notes/<lang>_<topic>.json`. The normal builder retains the configured provider/cache path; the explicit owner-gated `local_only=true` lane instead resolves a current verified local-Qwen clip first, safely reuses a valid conventional cache clip second, refuses any unresolved clip, and never calls a provider. Both paths package the frozen 17-field `Idiomatic Exercises v1` model (2 templates: Production, Cloze) into `<ROOT>::4 Exercises::{Topic}` subdecks and publish the rolling `apkgs.kind='exercises2'` row. Waves 1–2 account for 1,772 shipped notes / 3,544 cards; Wave 3 adds five merged 300-note TENSES files, bringing authored totals to 3,272 / 6,544 without publishing an APKG yet.
- **Entry Points**:
  - `idiomatic/grammar/exercises2.py` - schema validation, GUID/deck naming, cloze→mark/blank HTML, TTS cache + leveling, model + apkg build, `build_language()`
  - `idiomatic/local_tts.py` - missing-only queue resolver, exact-revision media validation/requeue, strict hybrid local rebuild
  - `idiomatic/grammar/data/exercises2/notes/*_tenses.json` - Wave 3's five audited 300-note merges
  - `idiomatic/grammar/data/exercises2/it_rebuild/` - IT corpus rebuild inputs/outputs (2,589 EN prompts with es/fr/pt/de refs)
  - `idiomatic/api.py` - `POST /admin/exercises2-build?lang[&local_only=true]`, `GET /admin/exercises2-list`, versioned local-queue endpoints
  - `tools/x2_wave_pipeline.py`, `tools/x2_batch_gate.py` - source-hashed staging (incl. bulk plans `wave4`/`wave5`/`wave6`, 40-row chunks, schema-v2 manifests with expected duplicate drops), duplicate checks, strict batch gate, topic-dispatched merge verification (shadowing topics validate under the P1 contract; pilot-prefix composition for pt big_tech_phrases)
  - `idiomatic/grammar/data/exercises2/batches/` - staged chunk inputs + per-plan manifests; Waves 4–6 bulk inputs staged 2026-08-09
  - `idiomatic/grammar/exercises2.py` - `SHADOWING_TOPICS` exclusion: frozen v1 loaders (`load_notes`) skip merged shadowing notes; `list_sources` inventories them via `exercises2_shadowing`
  - `idiomatic/grammar/data/exercises2/notes/*_big_tech_phrases.json` - Wave 6 merged shadowing corpora (de/es/fr/it, 90 each; draft model only — no builder/delivery)
  - `docs/EXERCISES2_ROADMAP.md`, `docs/research/legacy_estate/EXERCISES2_WAVE3_AUDIT.md` - wave accounting and final Wave 3 evidence
  - `docs/commissions/EXERCISES2_PILOT_COMMISSION.md`, `docs/commissions/EXERCISES2_IT_REBUILD_COMMISSION.md` - codex authoring contracts
  - `tools/it_rebuild_driver.sh` - resumable parallel codex driver for the IT rebuild
  - `tests/test_exercises2.py`, `tests/test_local_tts.py`, `tests/test_x2_wave_pipeline.py` - model/content, provider-free local lane, and pipeline/gate coverage
- **Dependencies**: normal route: configured `gemini.synthesize` provider chain + cache; local-only route: versioned `local_tts_jobs` queue and validated staged MP3s; both: `leveled_speech_clip`, voice fingerprints, genanki; codex CLI for authoring
- **Added**: 2026-08-04 | **Modified**: 2026-08-09

### Local Qwen estate-voicing queue
- **Status**: Pilot delivered; post-pilot adapters deployed but disarmed pending owner verdict (`LOCAL_TTS_EXERCISES2_PILOT_APPROVED=false`)
- **Description**: Durable, versioned, lease-based queue for cost-0 machine-local Qwen synthesis. The cloud accepts and validates canonical MP3 uploads but never synthesizes a queue job. Full Exercises2 seeding queues only audio missing from both current local completions and the conventional cache. The expression-pool adapter similarly covers target idiom, English gloss, English explanation, and both target/English example audio, leaves source-video `audio_context` untouched, overlays results on copied rows, and refuses a local-only Fluency rebuild while anything is missing. Invalid completed clips return to the queue under exact content-hash/path guards. No provider fallback, source-row mutation, bulk seed/build, service, or timer is active before the owner gate.
- **Entry Points**:
  - `idiomatic/local_tts.py` - queue identities, resolvers, missing-only seeders, upload validation, strict builders
  - `idiomatic/db.py` - idempotent seed, lease/claim/fail/complete, exact-revision completed-job requeue
  - `idiomatic/api.py` - `/admin/local-tts/v1/*`, `POST /admin/exercises2-build?local_only=true`, `POST /admin/rebuild-pools?local_only=true`
  - `idiomatic/pipeline/pool.py` - ephemeral expression-row audio overlay and provider-free strict rebuild
  - `docs/LOCAL_TTS_WORKER_API.md` - worker and operator contract
  - `tests/test_local_tts.py` - queue, validation, hybrid resolution, API gate, and expression-pool coverage
- **Dependencies**: loopback machine-local Qwen3-TTS bridge and worker; server-side staged-audio store; owner listening verdict before any bulk action
- **Added**: 2026-08-08

### Translation-exercise decks (repurposed grammar drills)
- **Status**: Active (code merged; first builds pending)
- **Description**: Verified grammar drill sentences repurposed as EN→TL translation cards: FRONT = the drill's `gloss_en` spoken by the English narrator (new cached leveled TTS under `staged_audio/grammar/translation_en/<lang>/`), BACK = the TL sentence with the drilled form bolded, reusing the existing drill back-audio clip (`idg_<lang>_<id>.mp3`) — zero new TL synthesis (reuse-only guarantee; clip-less items are skipped + counted). Selection excludes f3/f4/explainer formats, sentences under 4 words, and duplicate sentences (first wins, decided before the audio check so GUIDs never flip with disk state). Own frozen 14-field `Idiomatic Translation v1` model (one "Translate" template, id 1_820_160_001); `<ROOT>::5 Translation::{cluster}` subdecks share the grammar deck's cluster strings; rolling `apkgs.kind='translation'` per language — zero add-on changes.
- **Entry Points**:
  - `idiomatic/grammar/translation.py` - selection filters, EN TTS cache, model + apkg build, `build_language()`, `language_inventory()`
  - `idiomatic/api.py:831-863` - `POST /admin/translation-build?lang`, `GET /admin/translation-list`
  - `idiomatic/db.py:543-545` - `'translation'` in the `upsert_pool_apkg` kind whitelist
  - `docs/commissions/TRANSLATION_DECKS_COMMISSION.md` - the code commission
  - `tests/test_translation.py` - model/GUID/selection/bolding/cache/apkg/silence coverage (16 tests)
- **Dependencies**: grammar drill audio stage (`idiomatic/grammar/audio.py` naming + reuse check), `_full_html` bolding (`idiomatic/grammar/apkg.py`), cluster strings (`idiomatic/grammar/curriculum.py`), `gemini.synthesize` provider chain, `leveled_speech_clip` + voice fingerprint (`idiomatic/grammar/explainers.py`), `EN_VOICE` (`idiomatic/pipeline/audio.py`), genanki
- **Added**: 2026-08-04

## Asset Factory QA

### Corpus-image QA loop (Q-Judger judge + classified auto-repair)
- **Status**: Active (judging); repair loop DISARMED pending user spot-review
- **Description**: Every corpus illustration (both render machines) is judged by Q-Judger on the Mac against a checklist built from its own brief — person count/genders/distinct identities (merge catcher), per-person action, absurd-element presence, anatomy, focal-point+memorability floor. Failures classified into reroll_full / reroll_inserts / targeted_edit; max 2 repairs then escalation to a human-review folder with daily contact sheets. Human overrides always beat judge verdicts; only pass-verdict images may ship to cards.
- **Entry Points**:
  - `tools/qa_rubric.py:1` - brief→checklist prompt builder, verdict classification, repair mapping, partition helpers
  - `tools/qa_judge.py:1` - batch judge runner (transformers+MPS, content-hash ledger, memory guard)
  - `tools/qa_report.py:1` - DAILY.md summaries, failure contact sheets, spot-review package (`--spot N`)
  - `idiomatic/grammar/data/illustration_prompts/PARTITION.json` - chunk→machine ownership (miners skip foreign chunks; keep in step with the Mac's run_queue.sh)
  - `docs/IMAGE_QA.md` - operations doc (topology, arming procedure, machine-local script inventory)
- **Dependencies**: illustration-prompt briefs (input+output chunks), Q-Judger weights on the Mac (`~/llms/models/qwen-image-bench/`), machine-local runners (`~/llms/factory-node/qa/` on the Mac; `~/llms/qwen-image/factory/qa_{sync.sh,repair_night.py,arm.sh}` + `qa-sync.timer` on Fedora)
- **Added**: 2026-08-07

## Rescue Lab

### Rescue Lab (struggle-idiom experiment tracker + asset generation)
- **Status**: Active
- **Description**: Operating surface for the rescue initiative (docs/research/RESCUE_PILOT.md): struggle snapshots (from the AnkiWeb revlog pull, uploaded off-server) become `rescue_items`; per-item image assets (comic, contrast, polysemy map, morphology anatomy, poster, glyph — NO video, user verdict) are generated through switchable providers with full cost accounting in `gen_ledger`. Hard rules enforced in code: polysemy_map unapprovable without ≥2 fully-taught senses (gloss + micro-example each), anatomy templates demand strict left-to-right letter order, one permanent glyph per idiom (approval pins `glyph_asset_id`; a second approved glyph is refused).
- **Entry Points**:
  - `idiomatic/genmedia.py` - provider registry (`nano-banana`/`nano-banana-lite`, prices verified against official docs 2026-08-05) + `generate_image()` → (bytes, cost)
  - `idiomatic/rescue.py` - format taxonomy + prompt templates (seeded from the pilot's approved prompts), template fill, polysemy guard, snapshot/senses validation
  - `idiomatic/api.py:1212-1520` - `/admin/rescue/struggles|generate|asset/{id}/verdict|item/{id}|export/{item_id}`
  - `idiomatic/ui_api.py:605-795` - `/ui/api/rescue/items|item/{id}|costs|formats|asset-file/{id}`
  - `frontend/src/pages/RescueLab.tsx` - overview (cost tiles, spend by provider/format, struggle table)
  - `frontend/src/pages/RescueItem.tsx` - item page (senses editor, asset gallery with verdicts, Generate panel with pre-call cost estimate)
  - `frontend/src/pages/RescueFormats.tsx` - format taxonomy page
  - `tools/seed_rescue_pilot.py` - idempotent pilot-cohort seeder (9 items from docs/research/rescue_pilot1/)
  - `db/schema.sql` - `rescue_items`, `rescue_assets`, `rescue_senses`, `gen_ledger`
  - `tests/test_rescue.py` - registry/templates/guards + schema round-trip on ephemeral Postgres
- **Dependencies**: `GEMINI_API_KEY` (image models), Admin API + dashboard; asset files under `/data/rescue_assets/`
- **Added**: 2026-08-05

### Tenses Rescue decks (per-person conjugation drills from the 2015-2022 corpus)
- **Status**: Active (batch 1: top-3 verb×tense per language; pilot format user-approved 2026-08-05)
- **Description**: The old account's `_tenses_old` struggle data (docs/research/tenses-profiles/) turned into two rolling apkgs per language (`<ROOT>::3 Tenses::1 Production::{verb}` / `::2 Exercises::{verb}` since the 2026-08-07 estate cutover): `kind='tenses'` (EN→form production: EN sentence front; form + marked TL sentence + full paradigm with drilled row highlighted + fork note + personal lapse history on the back) and `kind='tenses_ex'` (fill-the-blank recycling the same sentences and audio). One card per PERSON (the old cards drilled whole paradigms — per-person failure was unmeasurable); archaic vós displayed dimmed, never drilled. Forms verified at build time (morphology truth tables where covered, corpus-attested otherwise). Spanish audio uses its own ElevenLabs voice (`tenses_es_voice_id`, George vetoed) with a listen-and-pick audition endpoint.
- **Entry Points**:
  - `idiomatic/grammar/tenses.py` - batch parser + verification, frozen models (1_820_170_001/2), audio cache, `build_language()`, `voice_audition()`
  - `idiomatic/grammar/data/tenses/batch1.json` - 15 offenders / 85 drilled forms (17 authored + 68 codex-gated sentences)
  - `idiomatic/api.py` - `POST /admin/tenses-build?lang`, `GET /admin/tenses-list`, `POST /admin/tenses-voice-audition`
  - `idiomatic/gemini.py` - `synthesize(eleven_voice_id=…)` voice override
  - `tests/test_tenses.py` - 14 deterministic tests
- **Dependencies**: tenses profiles (docs/research/tenses-profiles/), morphology truth tables, ElevenLabs TTS, genanki
- **Added**: 2026-08-05

### LingQ vocabulary mirror
- **Status**: Active
- **Description**: The user's saved LingQ vocabulary (10 languages incl. not-yet-active sv/da/nl/no/zh) mirrored into `lingq_terms`; grammar generation weaves a per-topic sample of still-learning terms into drill sentences (optional material, never the blank); daily cron auto-sync; `/admin/lingq-sample` feeds local agents (codex).
- **Entry Points**:
  - `idiomatic/lingq.py` - API v2 client + paginated sync
  - `idiomatic/api.py` - `/admin/lingq-token|sync|status|sample`
  - `idiomatic/cron.py` - staleness-triggered auto-sync
  - `db/schema.sql` - `lingq_terms`, `kv_store`
- **Dependencies**: LingQ API v2 (token in kv_store)
- **Added**: 2026-07-31
