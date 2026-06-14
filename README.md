# idiomatic

A cloud worker that watches a curated set of YouTube channels per language,
detects new short videos (5–15 min), extracts genuinely idiomatic expressions
that aren't already in the per-language library, builds Anki decks teaching
them, and emails the download link.

**Read first:** [ARCHITECTURE.md](./ARCHITECTURE.md)

## Status

M1 — scaffold only. Worker doesn't run yet. Schema sketched in `db/schema.sql`.
Pipeline code being ported from sibling repo `pimsleur`.

## Stack

| Concern        | Choice                                   |
|----------------|------------------------------------------|
| Hosting        | Render (cron + background_worker + Postgres) |
| Lang analysis  | Gemini 3.5 Flash (text + audio in one call) |
| TTS            | Gemini 3.1 Flash TTS                     |
| Audio plumbing | ffmpeg, yt-dlp                           |
| Deck packaging | genanki                                  |
| Channel poll   | YouTube per-channel RSS feeds (no API key) |
| Email          | Resend                                   |
| Web/API        | FastAPI (optional, post-MVP)             |

## Local dev

```bash
# uv-managed (install uv if you haven't)
uv sync

# bring up a local Postgres if needed
docker run -d --name idiomatic-pg -p 5432:5432 \
  -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=idiomatic postgres:16
psql postgresql://postgres:dev@localhost/idiomatic < db/schema.sql

# run the worker pointed at it
DATABASE_URL=postgresql://postgres:dev@localhost/idiomatic \
GEMINI_API_KEY=... \
DATA_DIR=./data \
uv run python -m idiomatic.worker --once
```

## Render

`render.yaml` declares the cron, worker, and Postgres. Push to `main` and
Render picks it up. Secrets live in env group `idiomatic-secrets`.

## See also

- [ARCHITECTURE.md](./ARCHITECTURE.md) — the full design + DB schema + open
  decisions
- Sibling repo `~/projects/pimsleur` — the source pipeline this app extracts
  from
