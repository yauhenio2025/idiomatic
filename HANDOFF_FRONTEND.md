# HANDOFF: Build the idiomatic dashboard

You are building a comprehensive web frontend for **idiomatic** — a
pipeline that turns YouTube videos into Anki idiom decks. Read
`CLAUDE.md` first (system map, credentials, schema), and skim
`AUDIT_2026_07.md` (known history — several past bugs came from
docstrings that lied; trust code over comments).

The owner's words: *"a super comprehensive, nicely designed front end …
constantly showing us what we have harvested from which videos, in what
capacity, what expressions we already had in the database, what we have
rejected"*. They review the output in Anki daily; this dashboard is how
they SEE the machine. Polish matters. They have budget and patience —
build it properly, use subagents/workflows freely if available.

────────────────────────────────────────────────────────────
ARCHITECTURE — PRE-DECIDED, do not relitigate
────────────────────────────────────────────────────────────

- **Serve the frontend from the existing FastAPI app** (`idiomatic-app`
  on Render, service `srv-d8nbs7reo5us73epeehg`). No new Render service.
  Mount a built static SPA at `/` via StaticFiles; keep all existing
  routes working (`/apkgs/*`, `/agent/*`, `/admin/*`, `/health` — the
  Anki add-on and worker depend on them; breaking them breaks delivery).
- **Stack**: Vite + React + TypeScript + Tailwind, built in a multi-stage
  Dockerfile (node build stage → copy `dist/` into the python image).
  The repo's Dockerfile currently is python-only; extend it.
- **API**: new read-only JSON endpoints under `/ui/api/*` in a new
  `idiomatic/ui_api.py` router. asyncpg via the existing `db.get_pool()`.
  SQL read-only; parametrized only.
- **Auth**: single-user. A minimal login screen asking for the admin
  token; store in localStorage; send as `X-Admin-Token` on every
  `/ui/api/*` call; verify server-side with the existing
  `settings.admin_token` constant-time check (see how `/admin/*` does
  it). No public unauthenticated data.
- **Audio playback in the browser**: add
  `/ui/api/audio/{youtube_id}/{filename}` (same strict-regex validation
  pattern as `/admin/audio-sample`) so expression cards can play their
  per-card mp3s from `/data/staged_audio/`.
- **Deploy**: push to `main` → Render auto-deploys in ~6 min. Verify
  with curl after. Never restart the DB; never touch `agents` rows.

────────────────────────────────────────────────────────────
DATA GAPS YOU MUST FILL FIRST (the dashboard needs data that
isn't persisted yet)
────────────────────────────────────────────────────────────

1. **Extraction/dedup log.** Today the worker extracts N idioms, drops
   the ones already in `expressions` (see `worker._filter_fresh`), and
   only the survivors are recorded. The owner explicitly wants to see
   "what expressions we already had" per video. Add a table:

     extraction_log(id, video_id, lang, phrase, normalized, english,
                    verdict TEXT,  -- 'fresh' | 'duplicate'
                    duplicate_of INTEGER NULL REFERENCES expressions(id),
                    created_at)

   Populate it in `worker.process_video` right where `_filter_fresh`
   runs. Backfill is impossible (data was never kept) — the log starts
   at deploy time; the UI should say so rather than show misleading
   zeros for old videos.

2. **Per-video processing metrics.** Add `videos.processing_seconds`
   (set at mark-done) so throughput charts are real. Optional but cheap.

3. Migrations: extend `db/schema.sql` (keep everything idempotent —
   `IF NOT EXISTS` style) and apply to prod with psql using the
   credentials in CLAUDE.md. This is the ONE prod write you're allowed.

────────────────────────────────────────────────────────────
PAGES — the spec
────────────────────────────────────────────────────────────

**1. Overview (landing).**
- Health strip: worker state (reuse `/agent/digest` internals: queued,
  hours since last apkg, stalled flag), videos processing right now,
  today's builds vs daily caps per language.
- Throughput chart: decks built per day, stacked by language, last 30d.
- Library growth chart: cumulative expressions per language over time
  (derivable from `expressions.added_at`).
- Funnel for the last 7 days: RSS-seen → enqueued → skipped (by reason
  class: duration pre-filter, duration post-check, oxylabs-permanent,
  wrong-channel) → failed → done. Skip reasons live in
  `videos.status_msg` — classify by prefix matching.

**2. Videos.**
- Filterable table (lang, channel, status, date, curated-vs-RSS) of all
  `videos` rows: title (linked to YouTube), channel, duration, status
  with reason, idioms extracted/fresh (from extraction_log once live),
  deck built at, delivered at (join agent_acks).
- Video detail view: everything above plus the full idiom list from
  `expression_idioms` (with per-idiom examples from
  `expression_examples`), the duplicates that were rejected (from
  extraction_log), and the trigger sentence pairs.

**3. Expressions (the library browser — make this one shine).**
- Search-as-you-type across `expression_idioms.idiom_text`,
  `english_gloss`, `explanation_en`; filters: language, channel/person
  (join via video → channel; the curated buckets are channels named
  'Curated · Carlo Galli' etc.), date range.
- Expression card: idiom (big), gloss, explanation paragraph, structured
  fields (JSONB `structured` — labelled sections, see EXPL_LABELS in
  `pipeline/apkg.py`), 6 example pairs, trigger sentence, source video
  link, and AUDIO PLAY buttons for idiom_tgt/idiom_en/example mp3s via
  the new audio endpoint.
- A "duplicates map": for an expression, which videos re-encountered it
  later (extraction_log.duplicate_of).

**4. Channels.**
- Table: name, lang, active, priority, title_filter, duration window,
  videos seen / skipped / done, idioms yielded, last video date. Data:
  join channels ↔ videos ↔ expression_idioms.
- Highlight zero-yield channels (the owner knows some are dead weight).

**5. Delivery.**
- apkgs table with kind, lang, size, built-at, acked-at, attempts;
  pending-for-agent view; failed-ack surfacing.

Keep navigation to those five. Resist inventing more pages; depth over
breadth. Dark-mode friendly. If a `dataviz` skill is available in your
session, load it before writing any chart code.

────────────────────────────────────────────────────────────
RULES OF ENGAGEMENT
────────────────────────────────────────────────────────────

- The pipeline is LIVE and processing daily. Do not break `worker.py`,
  `cron.py`, `oxylabs_client.py`, `gemini.py`, or the existing API
  routes. Your changes are: new router, new tables, small hook in
  process_video for extraction_log, Dockerfile build stage, frontend/.
- Commit in reviewable units. Smoke-test imports after every commit:
    uv run python -c "import os; os.environ.setdefault('DATABASE_URL','postgres://x:x@localhost/x'); os.environ.setdefault('GEMINI_API_KEY','x'); from idiomatic import api, worker, cron, ui_api; print('OK')"
- Test the SQL of every endpoint against prod (read-only!) with psql
  before wiring it into the router.
- After deploy: curl every new endpoint with the admin token; open the
  dashboard URL; verify `/health` and `/apkgs/pending` still answer
  (the add-on must not notice anything happened).
- The past sessions' biggest failure mode: shipping code whose SQL/API
  calls were never executed before deploy (a broken claim query once
  silently killed the pipeline for 4 days). EXECUTE EVERYTHING ONCE
  before pushing. If you add a query, run it. If you add an endpoint,
  curl it locally (uvicorn against prod DB read-only is fine).
- Update CLAUDE.md at the end: the new router, tables, and dashboard
  URL, in the same terse style as the rest of the file.

────────────────────────────────────────────────────────────
DEFINITION OF DONE
────────────────────────────────────────────────────────────

1. https://idiomatic-app.onrender.com/ shows the login, then the
   five-page dashboard, live against prod data.
2. Existing pipeline + Anki delivery visibly unaffected (acks continue).
3. extraction_log filling up as new videos process.
4. CLAUDE.md updated; a short DASHBOARD.md with screenshots-by-words of
   what each page answers.
5. A closing summary listing anything cut, deferred, or discovered
   broken along the way.
