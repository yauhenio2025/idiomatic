-- idiomatic — initial schema (M1)
-- Run with: psql $DATABASE_URL < db/schema.sql

CREATE TABLE IF NOT EXISTS channels (
  id            SERIAL PRIMARY KEY,
  youtube_id    TEXT UNIQUE NOT NULL,
  lang          TEXT NOT NULL,
  name          TEXT,
  added_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  active        BOOLEAN NOT NULL DEFAULT TRUE
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
  -- Both paths are relative to DATA_DIR/staged_audio
  audio_idiom_tgt TEXT,
  audio_idiom_en  TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS expression_idioms_lang_idx ON expression_idioms (lang);
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
  acked_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (agent_id, apkg_id)
);
