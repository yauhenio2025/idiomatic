# Feature Inventory

> Auto-maintained by Claude Code. Last updated: 2026-07-28

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
- **Dependencies**: Gemini 3.5 Flash, ElevenLabs TTS (primary), Gemini TTS (fallback), ffmpeg

### Language pools (4 decks per language)
- **Status**: Active
- **Description**: `pool_idioms`, `pool_expr`, `pool_idiom_t2e`, `pool_idiom_e2t` rebuilt per language with 30-min debounce.
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
- **Description**: Add-on (local, not in git) polls `/apkgs/pending`, downloads, imports on Qt main thread, acks; one-shot `cleanup.json` purge mechanism.
- **Entry Points**:
  - `idiomatic/api.py:99` - `/apkgs/pending`
  - `idiomatic/api.py:125` - `/apkgs/{id}/download`
  - `idiomatic/api.py:141` - `/apkgs/{id}/ack`
- **Dependencies**: agent bearer token (DB `agents` row)

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
- **Description**: LLM-generated grammar drills (verb morphology + closed-class), deterministically or blind-fill verified, compiled into one rolling `kind='grammar'` apkg per language with **one subdeck per topic cluster** (`Idiomatic Grammar {LANG}::{cluster}`). Strategy: `docs/GRAMMAR_STRATEGY.md`.
- **Entry Points**:
  - `idiomatic/grammar/morphology.py` - conjugation truth tables + verifier (Jehle es, verbecc fr/it/pt, german-nouns de)
  - `idiomatic/grammar/curriculum.py` - 42 units across es/de/fr/it/pt; `cluster` per Topic (`CLUSTER_BY_KEY`), `PLANNED_UNITS`, `unit_seed_rows()`
  - `idiomatic/grammar/generate.py` - Gemini batch generation + item verification (Tier A morph / Tier B blind-fill)
  - `idiomatic/grammar/apkg.py` - frozen 14-field `Idiomatic Grammar Drill v1` model, GUIDs from DB ids; `deck_name_for()` + per-cluster genanki decks
  - `idiomatic/grammar/service.py` - orchestration + rolling deck rebuild
  - `idiomatic/api.py:330-518` - `/admin/grammar-generate|status|stats|rejects|rebuild`, `/admin/grammar-deckmap` (agent-authed, add-on reorganize), `/admin/grammar-unit/{key}`, `/admin/grammar-topup/{key}`, `/admin/grammar-retire-item/{id}`
  - `db/schema.sql` - `grammar_items` (verified/rejected/retired) + `grammar_units` (cluster, status, target_size — code-owned cols re-seeded on boot)
  - `tests/test_grammar.py` - morphology, verifier, apkg/GUID stability, subdeck split, seed completeness
- **Dependencies**: Gemini text model, genanki, vendored morphology DBs
- **Added**: 2026-07-28 | **Modified**: 2026-07-31

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
