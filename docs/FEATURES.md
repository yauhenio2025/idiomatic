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

### Grammar drill pipeline (Spanish pilot)
- **Status**: Active
- **Description**: LLM-generated conjugation drills, deterministically verified against the Jehle Spanish verb DB, compiled into one rolling `kind='grammar'` apkg per language (delivered via the normal add-on path). Strategy: `docs/GRAMMAR_STRATEGY.md`.
- **Entry Points**:
  - `idiomatic/grammar/morphology.py` - conjugation truth table + verifier (Jehle DB, vendored gzip)
  - `idiomatic/grammar/curriculum.py` - pilot topics (8 Spanish tense/mood topics, KOFI-style)
  - `idiomatic/grammar/generate.py` - Gemini batch generation + item verification
  - `idiomatic/grammar/apkg.py` - frozen 14-field `Idiomatic Grammar Drill v1` model, GUIDs from DB ids
  - `idiomatic/grammar/service.py` - orchestration + rolling deck rebuild
  - `idiomatic/api.py` - `/admin/grammar-generate`, `/admin/grammar-status`, `/admin/grammar-stats`, `/admin/grammar-rebuild`
  - `db/schema.sql` - `grammar_items` table (verified AND rejected rows kept)
  - `tests/test_grammar.py` - deterministic tests (morphology, verifier, apkg/GUID stability)
- **Dependencies**: Gemini text model, genanki, Jehle verb DB (vendored)
- **Added**: 2026-07-28
