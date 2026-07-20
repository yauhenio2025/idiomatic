# idiomatic

Cloud service that turns YouTube videos into Anki idiom decks. Runs on
Render. Delivered into the user's Anki via an add-on that auto-imports.

## The whole flow, one sentence

Cron polls YouTube channels → worker downloads audio via Oxylabs →
Gemini extracts idioms → per-video `.apkg` + per-language pool `.apkg`
land in the DB → the Anki add-on on the user's laptop pulls + imports.

## Repos & paths

- Cloud code: `/home/admin/projects/idiomatic/` (this repo).
- Anki add-on (LOCAL, not in git):
  `/home/admin/.var/app/net.ankiweb.Anki/data/Anki2/addons21/idiomatic_puller/`
  It hits `/apkgs/pending`, downloads, imports on the Qt main thread,
  acks. Also executes a one-shot `cleanup.json` (deck names + note GUIDs
  to delete) on Anki startup — the mechanism for propagating server-side
  purges into the collection, since imports never delete.
  acks. Runs on a QTimer inside Anki — the user leaves Anki open and
  never touches the terminal. Menu items under Tools → Idiomatic.
- Deprecated local agent: `~/projects/pimsleur/scraper/idiomatic_agent.py`
  + systemd user timer. Was replaced by the add-on. Stop with
  `systemctl --user stop idiomatic-agent.timer && systemctl --user disable idiomatic-agent.timer`.

## Deployed services (Render)

- `srv-d8nbs7reo5us73epeehg` — `idiomatic-app`, docker, web + worker.
- `crn-d8nbs7reo5us73epeeh0` — `idiomatic-cron`, python starter.
- `idiomatic-db` — Postgres 16, basic-256mb, Frankfurt.

## Credentials the user has given me (already in Render env)

- `GEMINI_API_KEY` — Gemini 3.5 Flash + Flash TTS preview.
- `YOUTUBE_API_KEY` — YouTube Data API v3 (GCP project `idiomatic-502204`),
  used by the cron to pre-filter video durations before Oxylabs spend.
  10k quota units/day free; a full walk costs ~5.
- `ELEVENLABS_API_KEY` — English fallback voice (Sarah) when Gemini
  blocks Kore. Non-English blocks silence-fallback.
- `OXYLABS_USER` / `OXYLABS_PASS` — YouTube Downloader source, pushes
  audio to Cloudflare R2.
- `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_ENDPOINT` /
  `R2_BUCKET=idiomatic-yt-audio`.
- Agent bearer (`X-Agent-Token`, grants /apkgs/* + /admin/video-info only;
  used by the add-on): NOT in this file — the live value exists only in
  the `agents` DB row and the add-on's local `config.json`. Rotate with
  `POST /admin/rotate-agent-token` (admin-authed, JSON
  `{"name": "...", "new_token": "..."}`), then update the add-on config.
  All tokens that ever appeared in git history are dead.
- Admin bearer (`X-Admin-Token`, required for all /admin/* and the
  dashboard /ui/api/*): NOT in this file — set as `ADMIN_TOKEN` in the
  Render env for idiomatic-app (admin endpoints return 503 while unset);
  the local copy lives in `~/.config/idiomatic-admin.env` (gitignored
  path outside the repo). Rotate by updating both places.
- SECURITY NOTE: this repo must stay PUBLIC for Render deploys to work
  (the service clones it anonymously — no GitHub App connection), so no
  live secret may ever be committed. Tokens formerly in git history were
  all rotated dead on 2026-07-20.

## Pipeline stages (`idiomatic/`)

1. `cron.py` — every 2h. Channels can carry `title_filter` (case-insens.
   regex; e.g. 'caracciolo' on La7 Attualità) and per-channel
   `min/max_duration_sec` overriding the global 7–15 min window (Limes and
   La7-Caracciolo allow up to 60 min; audio >18 MB automatically routes
   through the Gemini Files API instead of inline base64). Walks `channels` (24 subs across de/fr/it/pt/es),
   pulls each channel's RSS, enqueues every unseen entry (no watch-page
   fetches — those hit the bot wall; duration is checked by the worker).
2. `worker.py`::`process_video` — the whole per-video pipeline:
   - `oxylabs_client.py` submits audio job → downloads .aac from R2.
   - Duration window check right after download (Oxylabs job-status
     `duration_sec`, ffprobe fallback) — out-of-window → status `skipped`.
   - `pipeline/extract.py` — Gemini 3.5 Flash on the audio returns
     `{text, english, source_phrase, source_phrase_en, explanation,
      audio_start, audio_end}` per idiom.
   - `pipeline/explain.py` — parallel Gemini calls for 6 example pairs
     + structured `{usage, collocations, ...}` fields.
   - `pipeline/audio.py`::`render_card_audio` — pimsleur-shape stitching:
     FRONT: listen_context → snippet → here_it_is → idiom_tgt → meaning
            → idiom_en → how_to_use → explanation_en → examples_intro
            → 3 teach pairs
     BACK:  practice_intro → sentence_1 → drill1_en → think → drill1_tgt
            → sentence_2 → … → sentence_3 → …
     Loudness-normalized (-16 LUFS).
   - `pipeline/apkg.py` — 21-field `Idiomatic Cloud Card v2` model.
   - `_persist_pool_source` — copies per-card mp3s to
     `/data/staged_audio/<youtube_id>/`, writes `expression_idioms` +
     `expression_examples` rows.
   - `pipeline/pool.py::rebuild_pools(lang)` — builds ALL FOUR pool
     apkgs for the language: `pool_idioms` (didactic), `pool_expr`
     (fluency), `pool_idiom_t2e`, `pool_idiom_e2t`.
3. `api.py` — FastAPI. `/apkgs/pending`, `/apkgs/{id}/download`,
   `/apkgs/{id}/ack` for the add-on (agent token). `/health`. Admin
   endpoints (require `X-Admin-Token`):
   `/admin/backfill-v2`, `/admin/audio-audit`, `/admin/audio-sample`,
   `/admin/rebuild-pools?lang=…` (bypasses the 30-min pool debounce),
   `/admin/rotate-agent-token` (JSON {name, new_token}).
   Exception: `/admin/video-info` stays agent-authed — the add-on's
   Reorganize step calls it.
   The API lifespan applies `db/schema.sql` (idempotent) at every boot —
   that IS the migration mechanism; there is no manual psql step.
4. **Dashboard** — https://idiomatic-app.onrender.com/ (see DASHBOARD.md).
   `ui_api.py` = read-only JSON under `/ui/api/*` (admin token);
   `frontend/` = React SPA built in the Dockerfile's node stage, served
   at `/` by api.py behind every API route. Audio playback streams
   staged_audio via `/ui/api/audio/{yt}/{file}`.

## DB schema (`db/schema.sql`)

- `channels` — YouTube channel subscriptions.
- `videos` — enqueued videos.
- `expressions` — per-language unique idiom index.
- `expression_idioms` — one row per idiom occurrence (in a video).
  Has `source_phrase_target`, `source_phrase_en`, `explanation_en`.
- `expression_examples` — 6 rows per idiom (target sentence + english
  translation + persisted audio paths).
- `apkgs` — one row per deliverable. `kind` ∈ `{video, pool_idioms,
  pool_expr, pool_idiom_t2e, pool_idiom_e2t}`. Video apkgs are per
  (video_id); pool apkgs are per (lang, kind) via partial-unique index.
- `agents`, `agent_acks` — agent auth + delivery tracking.
- `extraction_log` — every Gemini-extracted phrase with its dedup
  verdict ('fresh' | 'duplicate' + duplicate_of → expressions.id).
  Written best-effort in worker._filter_fresh; data exists from
  2026-07-20 forward (earlier dedups were never persisted).
- `expression_idioms.audio_context` — per-idiom context clip (the full
  sentence from the source video). Live path slices from Gemini
  sentence timestamps; historical clips were whisper-aligned LOCALLY
  (`tools/local_align.py` + `POST /ui/api/upload-context/{id}`) because
  Gemini audio timestamps drift badly deep into long files. LESSON:
  never trust LLM audio timestamps beyond ~10 min without verification,
  and always decode-seek (-ss after -i) when slicing ADTS .aac.
- `videos.processing_seconds` — wall-clock per-video processing time,
  set at mark-done (older done rows backfilled from picked_at→finished_at).

## Rate limits I have to remember

- **Daily cap per language**: `settings.max_new_apkgs_per_lang_per_day = 3`.
  Only `kind='video'` apkgs count (enforced in `worker._under_daily_cap`
  AND excluded at claim time via `db.langs_at_daily_cap`, so a capped
  language can't starve the queue).
- **Retry policy**: the claim burns an attempt; any failure except
  OxylabsFatal requeues until `worker_max_attempts=3`, then `failed`.
  Rows stuck in `processing` > 2 h are reclaimed automatically (reaper
  in `claim_next_video`); exhausted stale rows are marked failed.
  Manual `UPDATE videos SET status='queued', attempts=0` is only needed
  to resurrect a `failed` row.
- **Backfills**: only `/admin/backfill-v2` exists now — v1 was deleted
  (it parsed the old 8-field model and would have inserted example-less
  rows). `/admin/retts` re-synthesizes silence placeholders;
  `/admin/rebuild-pools?lang=…` forces past the 30-min pool debounce.
- **Gemini TTS preview** blocks ~1-4% of target-language content →
  silence placeholder (~600B mp3). English via Kore is stable.
- **YouTube RSS** load-sheds. Cron paces 1.5s between channels.

## When the user says…

- "sync latest" / "pull anki updates" — nothing for me to do; the
  add-on already does it every 5 min. If they want a manual kick,
  Tools → Idiomatic → Pull now inside Anki.
- "no new decks" — check `/apkgs/pending` count and the DB
  (`SELECT * FROM apkgs WHERE created_at > NOW() - INTERVAL '2 days'`).
  If the DB has them but the add-on hasn't pulled them, Anki is
  probably closed OR the add-on crashed (check the collection console).
- "add a channel" — INSERT into `channels(youtube_id, lang, name)`.
  Resolve `@handle` → `UC…` via the watch-page HTML (`"externalId":"UC…"`).
  The cron will pick it up on the next 2h tick.
- "the pipeline redesign" — commits `b1731f8` (pimsleur-shape 4-deck
  layout) and `7687a8e` / `deead5a` (backfill of trigger sentence +
  explanation for the 162 pre-redesign idioms).

## Deploying / touching prod safely

- Push to `main`. Render auto-deploys the web service in ~6 min.
- Never restart the DB.
- Admin operations run via the API endpoints, not via SSH (SSH would
  need a public key I haven't added).
- To reset stuck videos: `UPDATE videos SET status='queued', attempts=0
  WHERE …`. `db.requeue_no_attempt` inside the worker is the
  bug-avoidance path (cap-hit doesn't burn attempts).
