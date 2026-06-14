# idiomatic — architecture

A cloud pipeline that monitors a curated list of YouTube channels per language,
detects new short videos (5–15 min), extracts genuinely idiomatic expressions
that aren't already in the per-language expression library, generates Anki
decks teaching them, and emails the user a download link.

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
│   idiomatic-cron      ──┐                                                │
│   (cron job, 2h tick)   │   queues new videos found in channel RSS feeds │
│                         ▼                                                │
│   ┌──────────────────────────────────────┐   ┌────────────────────────┐  │
│   │ idiomatic-worker (background_worker) │◀──│ idiomatic-db (Postgres)│  │
│   │ - dequeues video jobs                │   │  channels              │  │
│   │ - yt-dlp audio                       │──▶│  videos                │  │
│   │ - Gemini 3.5 Flash: extract + ts     │   │  expressions           │  │
│   │ - dedup vs expression library        │   │  jobs                  │  │
│   │ - structured-explanation generation  │   │  apkgs                 │  │
│   │ - render audio (Gemini Flash TTS)    │   │  subscribers           │  │
│   │ - build apkg                         │   └────────────────────────┘  │
│   │ - upload to /data persistent disk    │                               │
│   │ - email signed download link         │                               │
│   └──────────────────────────────────────┘                               │
│                         ▲                                                │
│                         │                                                │
│   idiomatic-api ───────┘   (FastAPI; optional for MVP)                   │
│   - /channels CRUD       — manage tracked channels                       │
│   - /videos              — pipeline status                               │
│   - /expressions/<lang>  — browse library                                │
│   - /apkg/<token>        — signed download                               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

For the MVP we ship **cron + worker + db** only. The API service can come once
the worker proves out end to end.

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

### 5. Apkg storage + delivery

Render persistent disk (10GB mounted on the worker at `/data`) holds the apkgs.
When the worker finishes a video, it inserts into `apkgs` table, generates a
signed download token, emails the user.

Email via [Resend](https://resend.com) (3000 free emails/month, simple API).

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
  id            SERIAL PRIMARY KEY,
  video_id      INTEGER REFERENCES videos(id),
  lang          TEXT NOT NULL,
  filename      TEXT NOT NULL,                -- relative to /data
  size_bytes    BIGINT,
  n_idioms      INTEGER,                      -- new ones (not deduped)
  download_token TEXT UNIQUE NOT NULL,        -- random URL slug
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  delivered_at  TIMESTAMPTZ                   -- when email was sent
);

CREATE TABLE subscribers (
  id            SERIAL PRIMARY KEY,
  email         TEXT NOT NULL,
  langs         TEXT[] NOT NULL,              -- which langs they want
  active        BOOLEAN DEFAULT TRUE
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
                          email each subscriber with download link
```

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
│   └── email.py               # Resend client
└── tests/
    └── ...
```

## Env vars (all secrets via Render env group `idiomatic-secrets`)

```
GEMINI_API_KEY       — text + audio + TTS
ELEVENLABS_API_KEY   — optional, only if we swap TTS providers
RESEND_API_KEY       — email
DATABASE_URL         — Postgres, auto-injected by Render
SIGN_KEY             — random string, for signing download tokens
APP_BASE_URL         — https://idiomatic.onrender.com (or wherever the API lives)
DATA_DIR             — /data on Render, ~/idiomatic-data locally
```

## Open decisions for the user

Before we commit to the above, three questions:

1. **TTS provider for MVP?** Defaulting to Gemini Flash TTS (cheaper, in-stack).
   ElevenLabs voices sound better but add cost + dependency. Easy to flip later
   via `tts_provider.py`.
2. **Email provider?** Resend assumed. Postmark also fine. Need an API key on
   the chosen provider.
3. **First language to target?** I'd start with one (Italian or German — best
   tested in pimsleur) to nail the loop, then turn on more channels.

## Path to production

1. **This commit** (M1): scaffold, db schema, render.yaml. No code runs yet.
2. **M2**: worker that processes ONE manually-enqueued video end-to-end and
   produces an apkg on disk. Skip email, skip cron.
3. **M3**: cron + RSS polling. Now it processes channels autonomously.
4. **M4**: dedup against expressions table. Worker filters before generating.
5. **M5**: email delivery via Resend.
6. **M6**: 15-20 channels seeded per language.
7. **M7** (stretch): minimal web UI for browsing the expression library and
   re-queuing failed videos.
