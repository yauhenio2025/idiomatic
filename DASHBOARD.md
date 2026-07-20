# The idiomatic dashboard

https://idiomatic-app.onrender.com/ — served by the same FastAPI app that
runs the pipeline; log in with the admin token (local copy:
`~/.config/idiomatic-admin.env`). Read-only: nothing on the dashboard can
mutate pipeline state.

## What each page answers

**Overview** — "is the machine alive, and what has it been producing?"
Health strip: worker state (idle/processing/stalled — stalled means work
is queued but nothing built for 6+ hours), queue depth, library size,
and a per-language meter of today's builds against the 3/day cap.
Below: 30-day deck throughput (stacked bars by language), cumulative
expression-library growth (lines), the last-7-days funnel from RSS
discovery through pre-filtering/enqueueing to done/skipped/failed with
skip reasons broken out, and the fresh-vs-already-known dedup split.
Auto-refreshes every 30 s.

**Videos** — "what happened to each video?" Filterable by language,
status, curated-vs-RSS, channel, and title search. Each row: channel,
duration, status with reason class, idioms fresh/duplicate (from the
extraction log; older videos show the deck's idiom count marked
pre-log), deck-built and delivered-to-Anki dates. The detail view shows
everything the video contributed (full idiom cards with trigger
sentence, stylebook fields, 6 example pairs, audio playback) and
everything rejected as already known, each reject linking to the video
that first contributed the expression.

**Expressions** — the library browser. Search-as-you-type across idiom
text, gloss, and explanation; filter by language and by channel/person
(curated buckets — Galli, Ginzburg, Caracciolo… — sort to the top with
a ★). Cards play the idiom and English audio straight from the server.
The detail view is the full card: big idiom, gloss, usage explanation,
where-it-was-said quote (with YouTube link), stylebook sections,
example pairs 1–3 (teach) and 4–6 (drill) with per-sentence audio, and
the re-encounter map — which later videos hit the same expression and
were deduped (↻ badge on the card).

**Channels** — "which subscriptions earn their keep?" Per channel:
rules (title filter, duration window), videos seen/done/skipped/queued,
idioms yielded, yield per processed video, last-video date. Priority
channels wear 🔥 (they bypass the daily cap); active channels with
plenty of traffic and zero yield are flagged as dead weight.

**Delivery** — "did it reach Anki?" Agent liveness (the add-on's
last_seen), then every apkg with kind, size, built time, and ack state:
imported ✓ / awaiting pickup / failed-but-retrying (with attempt count
vs the 5-attempt budget) / given up.

## Data honesty

The extraction log (dedup verdicts, re-encounters) exists from
2026-07-20 onward — duplicates were discarded in memory before that, so
the history is unrecoverable, not zero. The UI labels pre-log videos
accordingly. `videos.processing_seconds` was backfilled for older done
videos from picked_at→finished_at.

## Plumbing

- API: `idiomatic/ui_api.py`, all endpoints under `/ui/api/*`,
  X-Admin-Token auth (constant-time), parametrized read-only SQL.
  Audio: `/ui/api/audio/{youtube_id}/{file}.mp3` streams from
  `/data/staged_audio/` (same strict path validation as
  /admin/audio-sample; also accepts ?token= for direct links).
- Frontend: `frontend/` — Vite + React + TS + Tailwind, dark theme,
  hand-rolled SVG charts (5-language categorical palette validated for
  CVD safety on the dark surface). Built in the Dockerfile's node stage;
  FastAPI serves `frontend/dist` at `/` with an SPA fallback registered
  after every API route.
- Local dev: `npm run dev` in `frontend/` proxies `/ui/api` to a local
  uvicorn on :8000.

## Context clips (added 2026-07-20/21)

Every idiom keeps a **context clip** — the full sentence from the
original video. It plays via the "in context" buttons on expression
cards, the expression detail page, and video detail, and opens the
front audio of video-deck cards and pool idiom cards (pool cards
previously carried no original-video audio at all).

Provenance (~96% of the library has a clip):
- `context_NNN.mp3` — live pipeline: Gemini sentence timestamps at
  extraction time, sanity-checked, accurate decode-seek slicing.
- `context_bf_<id>.mp3` — server backfill (Gemini relocation), kept
  only where offline whisper verification confirmed the clip.
- `context_lc_<id>.mp3` — locally aligned: Gemini timestamps proved
  too noisy for deep positions in long videos, so `tools/local_align.py`
  (run on the operator's machine) downloads the audio via yt-dlp,
  whisper-aligns each stored sentence at word level, slices, and
  uploads via `POST /ui/api/upload-context/{idiom_id}`.

The ~40 clip-less idioms are old paraphrase-era extractions whose
stored sentence never occurred verbatim in the audio (plus a couple of
deleted/geo-blocked videos); the UI labels them honestly.
