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
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS apkgs_lang_created_idx ON apkgs(lang, created_at);

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
