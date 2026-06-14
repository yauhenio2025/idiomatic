# idiomatic — architecture

A cloud pipeline that monitors a curated list of YouTube channels per language,
detects new short videos (5–15 min), extracts genuinely idiomatic expressions
that aren't already in the per-language expression library, generates Anki
decks teaching them, and exposes them via an HTTP API for a local agent to
pull and batch-import into Anki whenever Anki is open.

## Mental model

  - Subscribe to ~15-20 channels per language up front.
  - Cron polls every couple of hours; new videos get queued.
  - The worker only spends Gemini money on idioms NOT already in the language's
    expression library — so steady state is ~5 new decks per day total across
    languages (most days a channel publishes nothing genuinely new).
  - Apkgs live on the Render persistent disk and stay there until the local
    agent acks them as imported.
  - The local agent (a tiny systemd/cron job on the user's machine) polls the
    cloud API, downloads any unacked apkgs, and imports them into Anki via the
    existing `scraper/import_apkg.py` flatpak path. If Anki is closed it
    leaves them queued locally and tries again next tick.

No email, no AnkiWeb sync trickery — local agent + cloud API is the bridge.

## Source of truth: the existing pimsleur project

This repo grows out of `~/projects/pimsleur/scraper/*` — a local pipeline that
already does the heavy lifting:

  - `pipeline.py`           — yt-dlp + whisper + Gemini regroup + ffmpeg slice
  - `idioms.py`             — Gemini idiom extraction + structured explanations + apkg builder
  - `net.py`                — Gemini call wrapper with retries
  - `build_expression_pool.py` / `build_idiom_audio_pool.py` — language-level pools
  - `tts_provider.py`       — ElevenLabs / Gemini Flash TTS / Chatterbox / Piper / gTTS abstraction
  - The Mandarin "phrase mastery" v3.1 orchestrator (audio-first lesson scripts)

`idiomatic` ports the **idiom-deck path** to a multi-tenant cloud worker. The
local Mandarin/Pimsleur flows stay in the pimsleur repo for now.

## Topology (MVP)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Render workspace `caii`, project `idiomatic`                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   idiomatic-cron     ──┐                                                 │
│   (cron, 2h tick)      │   queues new videos found in channel RSS feeds  │
│                        ▼                                                 │
│   ┌──────────────────────────────────────┐   ┌────────────────────────┐  │
│   │ idiomatic-worker (background_worker) │◀──│ idiomatic-db (Postgres)│  │
│   │ - claims next queued video           │   │  channels              │  │
│   │ - yt-dlp audio                       │──▶│  videos                │  │
│   │ - Gemini 3.5 Flash: extract + ts     │   │  expressions           │  │
│   │ - dedup vs expression library        │   │  apkgs                 │  │
│   │ - generate structured explanations   │   │  agents                │  │
│   │ - Gemini Flash TTS audio             │   └────────────────────────┘  │
│   │ - build apkg                         │              ▲                │
│   │ - write to /data, record in db       │              │                │
│   └──────────────────────────────────────┘              │                │
│                                                         │                │
│   idiomatic-api  (FastAPI web service)                  │                │
│   - GET  /apkgs/pending?lang=…&agent=…   ──┐            │                │
│   - GET  /apkgs/<id>/download              │── exposes the queue to the  │
│   - POST /apkgs/<id>/ack                   │   local Anki-side agent     │
│   - GET  /expressions/<lang>?since=…       │                             │
│   - POST /channels                          │                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │  HTTPS  (agent_token in header)
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Local machine (user's Fedora box)                                       │
│                                                                          │
│   idiomatic-agent  (systemd timer, every 30 min)                         │
│   - polls /apkgs/pending for unacked decks                               │
│   - downloads them under ~/idiomatic-inbox/                              │
│   - if `pgrep anki` says Anki is OPEN: skip import this tick             │
│   - if CLOSED: invoke flatpak import_apkg.py for each, then POST /ack    │
│   - apkgs that fail import stay queued for next tick                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**M1 ships cron + worker + db + API.** The agent is a separate ~50-line script
that lives in the user's `pimsleur` repo (alongside `import_apkg.py`).

## Critical design choices

### 1. Transcription: Gemini 3.5 Flash (not Whisper)

In pimsleur we use `faster-whisper turbo/int8` on CPU. It works but it's slow
(minutes per video) and would require a fat Render plan or GPU. **Gemini 3.5
Flash accepts audio input directly**. For "find the idiomatic expressions in
this audio", we don't need a perfect transcript — we need timestamps for the
useful phrases. One call gets us both:

```
prompt: "You are listening to a 10-minute Italian interview. Extract 8-15
        idiomatic-but-common expressions used in the audio. For each, return:
        - the exact wording as spoken
        - start/end timestamps (seconds)
        - a rough English meaning
        Output JSON array."
audio: <base64 mp3>
```

Then we slice the original audio at those timestamps for the per-card clips.
**Net effect:** no Whisper, no separate regroup step. The worker can run on a
cheap CPU instance.

Gemini 3.5 Flash pricing (May 2026 launch): $1.50/M input tokens, $9/M output.
Audio input is ~32 tokens per second of audio, so a 10-min video ≈ 19k tokens
≈ $0.03 per video for the extraction call. Negligible.

### 2. Deduplication: per-language expression table

Every extracted expression lands in `expressions(lang, normalized_text, ...)`.
Before generating examples + explanation for a new video's candidates, we
left-join against this table. Anything matching by `normalized_text` is
filtered out — we don't waste Gemini calls on duplicates. The user's main
constraint: *new idiomatic content only*.

Normalization: lowercase, collapse whitespace, strip punctuation, optionally
lemmatize for inflected languages (de/it/fr/es) — but start with the simpler
normalization and add lemmatization only if too many near-duplicates leak
through.

### 3. TTS: Gemini Flash TTS

`gemini-3.1-flash-tts-preview` is the cheap end of TTS at $20/M audio output
tokens (~25 tok/sec audio → ~$0.50 per 10-minute video's audio). Voice quality
is good enough for the structured-explanation alternating-cadence format we
landed on in pimsleur. We can swap in ElevenLabs Flash later if voice quality
becomes a complaint — keeping the `tts_provider.py` abstraction means it's a
config flip, not a rewrite.

### 4. Channel polling: YouTube RSS feeds, no API key

`https://www.youtube.com/feeds/videos.xml?channel_id=<UC...>` returns the
channel's recent uploads as an RSS feed. No quota, no auth, no API key. Hit
every channel every 2 hours via the cron service. Filter: only videos with
duration between 5 and 15 minutes (we get that from the video metadata once
yt-dlp reads the page).

We could swap to the YouTube Data API later if we need richer filtering
(by tag, transcript availability, etc.) — but RSS gets us 80% there.

### 5. Inflow throttling: per-language daily cap

Steady state should be ~5 new decks/day total across all languages — most
videos a channel publishes won't yield any NEW idioms after the library
matures (dedup catches them). But to absorb spikes (channel uploads 8 videos
in a day during breaking news), the worker enforces a soft cap:

  - `max_new_apkgs_per_lang_per_day` (default 3): once a language has produced
    that many decks today, subsequent videos in that language stay queued
    until tomorrow. We process them eventually; we just don't blast the user
    with 15 new German decks in one day.
  - The cap counts apkgs created today, not videos processed. Videos that
    dedup down to zero new idioms get marked `skipped` and don't count.

This keeps the user's daily Anki import to a manageable handful regardless of
channel-side bursts.

### 6. Apkg storage + delivery (local-pull agent, no email)

Worker writes apkgs to the Render persistent disk (10GB at `/data`) and
records each one in the `apkgs` table. The web API exposes the queue:

  - `GET  /apkgs/pending?lang=…&agent=…` — list apkgs not yet acked by this
    agent.
  - `GET  /apkgs/<id>/download` — the raw apkg bytes.
  - `POST /apkgs/<id>/ack` — agent reports it imported successfully (or
    failed and wants the record marked).

A tiny **local agent** runs on the user's machine on a 30-min systemd
timer:

```python
# Sketch — lives in pimsleur/scraper/idiomatic_agent.py
agents = httpx.Client(base_url=settings.api_base, headers={"x-agent": TOKEN})
pending = agents.get("/apkgs/pending").json()
for apkg in pending:
    path = INBOX_DIR / apkg["filename"]
    if not path.exists():
        path.write_bytes(agents.get(f"/apkgs/{apkg['id']}/download").content)

if anki_is_running():        # pgrep -af "/app/bin/anki"
    log.info("anki open — skipping import this tick")
    sys.exit(0)

for path in INBOX_DIR.glob("*.apkg"):
    apkg_id = ...   # parse from filename
    if subprocess_import_via_flatpak(path) == 0:
        agents.post(f"/apkgs/{apkg_id}/ack", json={"status": "ok"})
        path.unlink()
    else:
        agents.post(f"/apkgs/{apkg_id}/ack", json={"status": "failed"})
```

If Anki is open, apkgs accumulate locally; the timer keeps trying. On days
the user runs Anki, the timer batches imports of everything queued since
last close. Skipped days just mean a bigger batch next time.

Agent authentication: each device gets an `agent_token` row in the db.
Tokens carry which `langs` they want and which `apkgs` they've acked — so
two machines (laptop + iPad-via-AnkiWeb) each have their own queue.

## Database schema (initial)

```sql
CREATE TABLE channels (
  id            SERIAL PRIMARY KEY,
  youtube_id    TEXT UNIQUE NOT NULL,         -- UCxxx
  lang          TEXT NOT NULL,                -- 'de', 'it', 'fr', 'es', 'pt', 'zh'
  name          TEXT,                         -- display name
  added_at      TIMESTAMPTZ DEFAULT NOW(),
  active        BOOLEAN DEFAULT TRUE
);

CREATE TABLE videos (
  id            SERIAL PRIMARY KEY,
  youtube_id    TEXT UNIQUE NOT NULL,
  channel_id    INTEGER REFERENCES channels(id),
  lang          TEXT NOT NULL,                -- copied for query speed
  title         TEXT,
  duration_sec  INTEGER,
  status        TEXT DEFAULT 'queued',        -- queued|processing|done|skipped|failed
  status_msg    TEXT,
  first_seen    TIMESTAMPTZ DEFAULT NOW(),
  finished_at   TIMESTAMPTZ,
  apkg_id       INTEGER REFERENCES apkgs(id)
);

CREATE TABLE expressions (
  id              SERIAL PRIMARY KEY,
  lang            TEXT NOT NULL,
  text            TEXT NOT NULL,              -- as it appeared
  normalized      TEXT NOT NULL,              -- for dedup
  english         TEXT,                       -- gloss
  first_video_id  INTEGER REFERENCES videos(id),
  added_at        TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(lang, normalized)
);

CREATE INDEX expressions_norm ON expressions(lang, normalized);

CREATE TABLE apkgs (
  id             SERIAL PRIMARY KEY,
  video_id       INTEGER REFERENCES videos(id),
  lang           TEXT NOT NULL,
  filename       TEXT NOT NULL,                -- relative to DATA_DIR
  size_bytes     BIGINT,
  n_idioms       INTEGER,                      -- new ones (post-dedup)
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agents (
  id             SERIAL PRIMARY KEY,
  token          TEXT UNIQUE NOT NULL,         -- bearer auth
  name           TEXT,                         -- "fedora-laptop"
  langs          TEXT[] NOT NULL,              -- which langs this device cares about
  last_seen      TIMESTAMPTZ
);

CREATE TABLE agent_acks (
  agent_id       INTEGER REFERENCES agents(id) ON DELETE CASCADE,
  apkg_id        INTEGER REFERENCES apkgs(id)  ON DELETE CASCADE,
  status         TEXT NOT NULL,                -- ok|failed
  acked_at       TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (agent_id, apkg_id)
);
```

## Worker job lifecycle

```
videos.status:  queued
                  │  (worker picks)
                  ▼
                processing
                  │
                  ├── if Gemini extract returns 0 fresh idioms after dedup:
                  │       status='skipped', finished_at=NOW()
                  │
                  ├── if any retriable error:
                  │       status='queued', leave for retry
                  │
                  ├── if non-retriable error:
                  │       status='failed', status_msg=trace
                  │
                  └── on success:
                          insert apkgs row
                          insert new expressions rows
                          status='done', finished_at=NOW()
                          (delivery is pull-based — agents fetch when they tick)
```

Before claiming a video, the worker also checks the daily cap:

```sql
-- pseudo
SELECT COUNT(*) FROM apkgs
WHERE lang = $1 AND created_at >= date_trunc('day', NOW())
```

If that's ≥ `max_new_apkgs_per_lang_per_day`, the worker skips queued videos
in that lang and looks for another. They process tomorrow.

## Repository layout

```
idiomatic/
├── ARCHITECTURE.md
├── README.md
├── pyproject.toml             # uv-managed deps
├── render.yaml                # cron + worker + postgres blueprint
├── Dockerfile                 # base image with ffmpeg + yt-dlp + python deps
├── db/
│   └── schema.sql             # tables above
├── idiomatic/
│   ├── __init__.py
│   ├── settings.py            # env-var driven config
│   ├── db.py                  # asyncpg pool + helpers
│   ├── youtube.py             # RSS poll + duration filter
│   ├── gemini.py              # 3.5 Flash text + audio + 3.1 Flash TTS wrappers
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── extract.py         # ported from pimsleur idioms.py
│   │   ├── dedup.py           # normalization + expressions table check
│   │   ├── explain.py         # structured-explanation prompt
│   │   ├── audio.py           # ffmpeg slice + Gemini TTS + concat
│   │   ├── connectives.py     # cached Sarah-equivalent connective tissue
│   │   └── apkg.py            # genanki packaging
│   ├── worker.py              # main loop: poll job table, run pipeline
│   ├── cron.py                # RSS poll → enqueue
│   └── api.py                 # FastAPI app: /apkgs/* + /channels CRUD
└── tests/
    └── ...
```

## Env vars (all secrets via Render env group `idiomatic-secrets`)

```
GEMINI_API_KEY       — text + audio + TTS, all via gemini-3.5-flash
ELEVENLABS_API_KEY   — optional, only if we swap TTS providers
DATABASE_URL         — Postgres, auto-injected by Render
DATA_DIR             — /data on the worker/api, ~/idiomatic-data locally
APP_BASE_URL         — public URL of the api service
```

The local agent (running on the user's box) needs only:
```
IDIOMATIC_API_URL    — e.g. https://idiomatic-api.onrender.com
IDIOMATIC_AGENT_TOKEN — bearer token created via `INSERT INTO agents ...`
INBOX_DIR            — ~/idiomatic-inbox (where downloaded apkgs land)
```

## Path to production

1. ✅ **M1** — scaffold, db schema, render blueprint, agent-pull design.
2. **M2** — worker processes ONE manually-enqueued video end-to-end:
   yt-dlp → Gemini 3.5 Flash audio extraction → dedup → structured-explanation
   generation → Gemini Flash TTS → genanki apkg → write to /data.
3. **M3** — cron + RSS polling. Channels seeded; pipeline runs autonomously.
4. **M4** — per-language daily cap enforced in the worker's claim loop.
5. **M5** — FastAPI service: /apkgs/pending, /apkgs/{id}/download, /ack,
   /channels CRUD. Bearer-token agent auth.
6. **M6** — local agent script lands in the pimsleur repo (alongside
   import_apkg.py) + systemd timer unit.
7. **M7** — seed 15-20 channels per language. Steady state.
8. **M8 (stretch)** — tiny web UI for browsing the expression library and
   re-queuing failed videos.
