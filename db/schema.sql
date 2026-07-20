-- idiomatic — initial schema (M1)
-- Run with: psql $DATABASE_URL < db/schema.sql

CREATE TABLE IF NOT EXISTS channels (
  id            SERIAL PRIMARY KEY,
  youtube_id    TEXT UNIQUE NOT NULL,
  lang          TEXT NOT NULL,
  name          TEXT,
  added_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  active        BOOLEAN NOT NULL DEFAULT TRUE,
  -- Optional per-channel controls:
  --   title_filter: case-insensitive regex; RSS entries whose title doesn't
  --     match are ignored (e.g. 'caracciolo' on a general talk-show channel).
  --   min/max_duration_sec: override the global duration window (NULL =
  --     global default). Long-form channels (Limes lectures) set max=3600.
  title_filter       TEXT,
  min_duration_sec   INT,
  max_duration_sec   INT,
  -- priority >= 10: claimed before everything else AND bypasses the
  -- daily per-language cap (used for must-have sources, e.g. Caracciolo).
  priority           INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS videos (
  id            SERIAL PRIMARY KEY,
  youtube_id    TEXT UNIQUE NOT NULL,
  channel_id    INTEGER REFERENCES channels(id) ON DELETE SET NULL,
  lang          TEXT NOT NULL,
  title         TEXT,
  duration_sec  INTEGER,
  status        TEXT NOT NULL DEFAULT 'queued',  -- queued|processing|done|skipped|failed
  status_msg    TEXT,
  attempts      INTEGER NOT NULL DEFAULT 0,
  first_seen    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  picked_at     TIMESTAMPTZ,
  finished_at   TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS videos_status_idx ON videos(status);
CREATE INDEX IF NOT EXISTS videos_lang_idx ON videos(lang);

CREATE TABLE IF NOT EXISTS expressions (
  id              SERIAL PRIMARY KEY,
  lang            TEXT NOT NULL,
  text            TEXT NOT NULL,
  normalized      TEXT NOT NULL,
  english         TEXT,
  first_video_id  INTEGER REFERENCES videos(id) ON DELETE SET NULL,
  added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(lang, normalized)
);
CREATE INDEX IF NOT EXISTS expressions_norm ON expressions(lang, normalized);

CREATE TABLE IF NOT EXISTS apkgs (
  id             SERIAL PRIMARY KEY,
  video_id       INTEGER REFERENCES videos(id) ON DELETE CASCADE,
  lang           TEXT NOT NULL,
  filename       TEXT NOT NULL,                  -- path relative to DATA_DIR
  size_bytes     BIGINT,
  n_idioms       INTEGER,                        -- new idioms (post-dedup)
  -- kind: 'video' (per-video idiom deck) | 'pool_expr' | 'pool_idiom_t2e' | 'pool_idiom_e2t'
  kind           TEXT NOT NULL DEFAULT 'video',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS apkgs_lang_created_idx ON apkgs(lang, created_at);
-- One pool apkg per (lang, kind). Video apkgs are one per video_id by ON CONFLICT.
CREATE UNIQUE INDEX IF NOT EXISTS apkgs_pool_unique ON apkgs (lang, kind) WHERE kind <> 'video';
-- One video apkg per video — a crashed-and-retried video upserts instead of
-- double-delivering.
CREATE UNIQUE INDEX IF NOT EXISTS apkgs_video_unique ON apkgs (video_id) WHERE kind = 'video';

-- ============================================================================
-- Pool-deck source data: per-idiom + per-example records, persistent across
-- per-video work_root cleanup. The pool builder re-stitches these into one
-- big apkg per language for cross-video drilling.
-- ============================================================================

CREATE TABLE IF NOT EXISTS expression_idioms (
  id             BIGSERIAL PRIMARY KEY,
  expression_id  INTEGER NOT NULL REFERENCES expressions(id) ON DELETE CASCADE,
  video_id       INTEGER REFERENCES videos(id) ON DELETE CASCADE,
  lang           TEXT NOT NULL,
  idiom_text     TEXT NOT NULL,
  english_gloss  TEXT NOT NULL,
  -- The full sentence from the video where the idiom appeared
  -- (both langs, populated by extract.py).
  source_phrase_target TEXT,
  source_phrase_en     TEXT,
  -- 2-3 sentence English explanation of usage. Drives the
  -- "how to use it" portion of the front audio.
  explanation_en TEXT,
  -- Categorical stylebook notes from explain.generate_structured_explanation
  -- ({usage, collocations, synonyms_*, antonyms, register_note, metaphor,
  --   pitfall, false_friend}). Rendered on the card back.
  structured     JSONB,
  -- All paths are relative to DATA_DIR/staged_audio
  audio_idiom_tgt TEXT,
  audio_idiom_en  TEXT,
  -- English TTS of explanation_en. Persisted by the worker per video;
  -- pool rebuilds TTS-on-miss for older rows (backfill-v2 era idioms
  -- have the text but never had the audio).
  audio_explanation TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Migration for pre-existing deployments (CREATE TABLE IF NOT EXISTS above
-- won't add the column to an already-created table). Idempotent.
ALTER TABLE expression_idioms ADD COLUMN IF NOT EXISTS structured JSONB;
ALTER TABLE expression_idioms ADD COLUMN IF NOT EXISTS audio_explanation TEXT;
CREATE INDEX IF NOT EXISTS expression_idioms_lang_idx ON expression_idioms (lang);
-- One idiom row per (expression, video) — makes _persist_pool_source
-- re-runnable after a mid-video crash (retries upsert in place).
CREATE UNIQUE INDEX IF NOT EXISTS expression_idioms_expr_video
  ON expression_idioms (expression_id, video_id);
CREATE INDEX IF NOT EXISTS expression_idioms_video_idx ON expression_idioms (video_id);

CREATE TABLE IF NOT EXISTS expression_examples (
  id             BIGSERIAL PRIMARY KEY,
  idiom_id       BIGINT NOT NULL REFERENCES expression_idioms(id) ON DELETE CASCADE,
  ord            SMALLINT NOT NULL CHECK (ord BETWEEN 1 AND 6),
  en_text        TEXT NOT NULL,
  target_text    TEXT NOT NULL,
  audio_en       TEXT,
  audio_target   TEXT,
  UNIQUE (idiom_id, ord)
);
CREATE INDEX IF NOT EXISTS expression_examples_idiom_idx ON expression_examples (idiom_id);

-- Debounce state for pool rebuilds: rebuild_pools() skips a language that
-- was already rebuilt in the last N minutes (worker triggers a rebuild
-- after every video; back-to-back videos in one language made that
-- expensive). /admin/rebuild-pools bypasses.
CREATE TABLE IF NOT EXISTS pool_rebuild_state (
  lang             TEXT PRIMARY KEY,
  last_rebuilt_at  TIMESTAMPTZ NOT NULL
);

-- ============================================================================
-- Extraction/dedup log: one row per phrase Gemini extracted from a video,
-- with the dedup verdict. Fills the "what did we reject as already-known"
-- gap — before this table only fresh survivors were recorded anywhere.
-- No backfill is possible (duplicates were dropped in memory); rows exist
-- from the table's deploy date forward. UNIQUE(video_id, normalized) makes
-- a retried video upsert its rows instead of duplicating them.
-- ============================================================================

CREATE TABLE IF NOT EXISTS extraction_log (
  id            BIGSERIAL PRIMARY KEY,
  video_id      INTEGER REFERENCES videos(id) ON DELETE CASCADE,
  lang          TEXT NOT NULL,
  phrase        TEXT NOT NULL,
  normalized    TEXT NOT NULL,
  english       TEXT,
  verdict       TEXT NOT NULL,                  -- 'fresh' | 'duplicate'
  duplicate_of  INTEGER REFERENCES expressions(id) ON DELETE SET NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (video_id, normalized)
);
CREATE INDEX IF NOT EXISTS extraction_log_video_idx ON extraction_log (video_id);
CREATE INDEX IF NOT EXISTS extraction_log_dup_idx
  ON extraction_log (duplicate_of) WHERE duplicate_of IS NOT NULL;

-- Wall-clock seconds process_video spent on the video (set at mark-done).
ALTER TABLE videos ADD COLUMN IF NOT EXISTS processing_seconds INTEGER;
-- Historical approximation for rows finished before the column existed:
-- picked_at → finished_at brackets the processing window. Idempotent.
UPDATE videos SET processing_seconds =
    GREATEST(0, EXTRACT(EPOCH FROM finished_at - picked_at)::int)
  WHERE processing_seconds IS NULL AND status = 'done'
    AND picked_at IS NOT NULL AND finished_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS agents (
  id             SERIAL PRIMARY KEY,
  token          TEXT UNIQUE NOT NULL,           -- bearer auth header
  name           TEXT,                           -- e.g. "fedora-laptop"
  langs          TEXT[] NOT NULL,                -- which langs to deliver
  last_seen      TIMESTAMPTZ,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_acks (
  agent_id       INTEGER REFERENCES agents(id) ON DELETE CASCADE,
  apkg_id        INTEGER REFERENCES apkgs(id)  ON DELETE CASCADE,
  status         TEXT NOT NULL,                  -- ok|failed
  -- Delivery attempts so far. A 'failed' ack no longer buries the apkg:
  -- /apkgs/pending re-offers it until attempts reaches the retry budget.
  attempts       INTEGER NOT NULL DEFAULT 1,
  acked_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (agent_id, apkg_id)
);
-- Migration for pre-existing deployments.
ALTER TABLE agent_acks ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 1;
