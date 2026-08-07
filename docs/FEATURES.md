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

### Admin API + dashboard
- **Status**: Active
- **Description**: Admin-token endpoints (backfills, retts, rebuild-pools, rotate-agent-token) + React SPA dashboard with read-only `/ui/api/*`.
- **Entry Points**:
  - `idiomatic/api.py:194` - admin endpoints start (`/admin/audio-audit` …)
  - `idiomatic/ui_api.py` - dashboard JSON API
  - `frontend/` - React SPA
- **Dependencies**: `ADMIN_TOKEN` env

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
  - `tests/test_grammar.py` - morphology, verifier, apkg/GUID stability, subdeck split, seed completeness
- **Dependencies**: Gemini text model, genanki, pinned `regex` grapheme segmentation, vendored morphology DBs
- **Added**: 2026-07-28 | **Modified**: 2026-08-01

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

### Exercises 2.0 (rich EN→TL usage notes; pilot: es connecting — format approved)
- **Status**: Active (ES CONNECTING pilot approved 2026-08-04; IT corpus rebuild + further batches in progress)
- **Description**: Revival of the 2023 legacy EXCERCISES corpus (see docs/research/legacy-excercises-audit.md) as rich notes: EN prompt → TL main rendering + accepted alternatives, register line, interference trap, in-register example (El País-opinion style), pre-rendered cloze. Content is codex-authored against commissions, audited, then committed as JSON under `data/exercises2/notes/<lang>_<topic>.json`; the builder synthesizes two cached leveled ElevenLabs clips per note (answer + example; silence-marked failures ship text-only), packages one frozen 17-field `Idiomatic Exercises v1` model (2 templates: Production, Cloze) into `<ROOT>::4 Exercises::{Topic}` subdecks, and publishes a rolling `apkgs.kind='exercises2'` row per language — zero add-on changes.
- **Entry Points**:
  - `idiomatic/grammar/exercises2.py` - schema validation, GUID/deck naming, cloze→mark/blank HTML, TTS cache + leveling, model + apkg build, `build_language()`
  - `idiomatic/grammar/data/exercises2/notes/es_connecting.json` - approved 42-note pilot content
  - `idiomatic/grammar/data/exercises2/it_rebuild/` - IT corpus rebuild inputs/outputs (2,589 EN prompts with es/fr/pt/de refs)
  - `idiomatic/api.py:796-830` - `POST /admin/exercises2-build?lang`, `GET /admin/exercises2-list`
  - `docs/commissions/EXERCISES2_PILOT_COMMISSION.md`, `docs/commissions/EXERCISES2_IT_REBUILD_COMMISSION.md` - codex authoring contracts
  - `tools/it_rebuild_driver.sh` - resumable parallel codex driver for the IT rebuild
  - `tests/test_exercises2.py` - schema/GUID/cloze/TTS-cache/apkg coverage
- **Dependencies**: `gemini.synthesize` provider chain (ElevenLabs primary), `leveled_speech_clip` + voice fingerprint (`idiomatic/grammar/explainers.py`), `LANG_VOICE` (`idiomatic/pipeline/audio.py`), genanki, codex CLI (authoring)
- **Added**: 2026-08-04

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
