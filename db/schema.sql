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
  -- kind: 'video' (per-video idiom deck) | 'pool_expr' | 'pool_idiom_t2e' | 'pool_idiom_e2t' | 'podcast_lesson' | 'exercises2' | 'translation' | 'tenses' | 'tenses_ex'
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
-- Sentence-level slice of the original video audio ("hear it in context").
-- NULL for idioms harvested before 2026-07-20 — their source audio was
-- already deleted, so no backfill is possible.
ALTER TABLE expression_idioms ADD COLUMN IF NOT EXISTS audio_context TEXT;
-- Citation/dictionary form of the expression (verbs in infinitive, nouns
-- in singular): 'das Sagen haben' for as-spoken 'hat das Sagen'. Shown on
-- the card back next to the as-spoken form. NULL = not yet generated.
ALTER TABLE expression_idioms ADD COLUMN IF NOT EXISTS citation_form TEXT;
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

-- ============================================================================
-- Grammar drill items (docs/GRAMMAR_STRATEGY.md). LLM-generated, every row
-- carries its verification verdict — rejected rows are kept on purpose so
-- the per-topic LLM error rate is measurable. Verified rows are compiled
-- into one rolling apkg per lang (apkgs.kind='grammar').
-- ============================================================================

CREATE TABLE IF NOT EXISTS grammar_items (
  id            BIGSERIAL PRIMARY KEY,
  lang          TEXT NOT NULL,
  topic         TEXT NOT NULL,                  -- curriculum or authored unit key
  fmt           TEXT NOT NULL DEFAULT 'cloze',  -- cloze (F1) | f3 | f4 | explainer
  infinitive    TEXT,
  mood          TEXT,
  tense         TEXT,
  person        TEXT,                           -- 1s..3p
  sentence      TEXT NOT NULL,                  -- cloze/F4 frame, F3 wrong phrase, or explainer title
  answer        TEXT NOT NULL,
  gloss_en      TEXT,
  why_en        TEXT,
  status        TEXT NOT NULL DEFAULT 'verified', -- verified|rejected|retired
  reject_reason TEXT,
  batch         TEXT,                           -- generation/authored build id
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (lang, sentence)
);
CREATE INDEX IF NOT EXISTS grammar_items_lang_topic ON grammar_items(lang, topic, status);
-- Structured facts behind non-verb items (German: noun/prep/case/definite);
-- enables re-verification after verifier fixes. Idempotent migration.
ALTER TABLE grammar_items ADD COLUMN IF NOT EXISTS meta JSONB;
-- Authored grammar-radio rows use a mutable title as ``sentence``.  Their
-- stable identity is the source slug stored in meta, so source edits update
-- one row (and preserve its scheduling identity) instead of inserting a
-- second note.  Ordinary generated/F3 uniqueness remains (lang, sentence).
CREATE UNIQUE INDEX IF NOT EXISTS grammar_items_explainer_slug_unique
  ON grammar_items (lang, (meta->>'slug'))
  WHERE fmt = 'explainer';

-- Curriculum units (Wave 6): code (grammar/curriculum.py) stays the
-- DEFINITION source — api.py re-seeds rows from it on every boot and
-- overwrites the code-owned columns (cluster, label, symbol, sort_order).
-- The DB carries only the MUTABLE state: status, target_size, notes.
-- status='planned' rows are curriculum intent with no generation yet.
CREATE TABLE IF NOT EXISTS grammar_units (
  key          TEXT PRIMARY KEY,               -- curriculum.Topic.key = card tag
  lang         TEXT NOT NULL,
  cluster      TEXT NOT NULL,                  -- Anki subdeck ("1 Tiempos")
  label        TEXT NOT NULL,
  symbol       TEXT NOT NULL DEFAULT '',
  status       TEXT NOT NULL DEFAULT 'active', -- active|maintenance|planned
  target_size  INT  NOT NULL DEFAULT 12,       -- desired verified-card count
  sort_order   INT  NOT NULL DEFAULT 0,
  notes        TEXT,
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS grammar_units_lang_idx ON grammar_units(lang, sort_order);

-- ============================================================================
-- Versioned local-only TTS queue (legacy-estate Part C).  Render only brokers
-- work and stores validated clips: synthesis happens on the operator's local
-- Qwen bridge, never through the paid provider chain.  A source edit changes
-- content_hash and the idempotent seeder resets that job to queued.
-- ============================================================================

CREATE TABLE IF NOT EXISTS local_tts_jobs (
  id                BIGSERIAL PRIMARY KEY,
  contract_version  SMALLINT NOT NULL,
  source_kind       TEXT NOT NULL,
  source_key        TEXT NOT NULL UNIQUE,
  lang              TEXT NOT NULL,
  note_key          TEXT NOT NULL,
  clip_kind         TEXT NOT NULL,
  text              TEXT NOT NULL,
  voice_version     TEXT NOT NULL,
  content_hash      TEXT NOT NULL,
  staged_path       TEXT NOT NULL UNIQUE, -- relative to DATA_DIR/staged_audio
  is_pilot          BOOLEAN NOT NULL DEFAULT FALSE,
  status            TEXT NOT NULL DEFAULT 'queued',
  attempts          INTEGER NOT NULL DEFAULT 0,
  lease_token       TEXT,
  worker_id         TEXT,
  lease_started_at  TIMESTAMPTZ,
  lease_expires_at  TIMESTAMPTZ,
  last_error        TEXT,
  last_failed_at    TIMESTAMPTZ,
  audio_size_bytes  BIGINT,
  audio_sha256      TEXT,
  completed_at      TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (contract_version > 0),
  CHECK (lang ~ '^[a-z]{2}$'),
  CHECK (clip_kind IN ('answer', 'example', 'prompt_en')),
  CHECK (length(text) > 0),
  CHECK (content_hash ~ '^[0-9a-f]{64}$'),
  CHECK (status IN ('queued', 'leased', 'completed', 'failed')),
  CHECK (attempts >= 0),
  CHECK (
    (status = 'leased' AND lease_token IS NOT NULL
                       AND lease_started_at IS NOT NULL
                       AND lease_expires_at IS NOT NULL)
    OR
    (status <> 'leased' AND lease_token IS NULL
                        AND lease_expires_at IS NULL)
  ),
  CHECK (status <> 'completed'
         OR (audio_size_bytes IS NOT NULL AND audio_size_bytes > 0
             AND audio_sha256 IS NOT NULL
             AND audio_sha256 ~ '^[0-9a-f]{64}$'
             AND completed_at IS NOT NULL))
);
-- 2026-08-08: prompt_en clip kind added (English prompt audio, Extra1).
-- Existing deployments carry the two-kind CHECK; rebuild it in place.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'local_tts_jobs_clip_kind_check'
      AND pg_get_constraintdef(oid) NOT LIKE '%prompt_en%'
  ) THEN
    ALTER TABLE local_tts_jobs DROP CONSTRAINT local_tts_jobs_clip_kind_check;
    ALTER TABLE local_tts_jobs ADD CONSTRAINT local_tts_jobs_clip_kind_check
      CHECK (clip_kind IN ('answer', 'example', 'prompt_en'));
  END IF;
END $$;
CREATE INDEX IF NOT EXISTS local_tts_jobs_claim_idx
  ON local_tts_jobs(contract_version, status, is_pilot DESC, id);
CREATE INDEX IF NOT EXISTS local_tts_jobs_lease_idx
  ON local_tts_jobs(lease_expires_at) WHERE status = 'leased';
CREATE INDEX IF NOT EXISTS local_tts_jobs_note_idx
  ON local_tts_jobs(source_kind, note_key, clip_kind);

-- ============================================================================
-- LingQ vocabulary mirror (user's saved words/phrases from lingq.com, all
-- learning languages incl. not-yet-active ones). Source for vocab-aware
-- exercise generation; synced via idiomatic/lingq.py (cron-triggered +
-- /admin/lingq-sync). The API token lives in kv_store ('token:lingq'),
-- NEVER in this public repo.
-- ============================================================================

CREATE TABLE IF NOT EXISTS lingq_terms (
  id              BIGSERIAL PRIMARY KEY,
  lingq_id        BIGINT UNIQUE NOT NULL,     -- LingQ card pk
  lang            TEXT NOT NULL,
  term            TEXT NOT NULL,
  fragment        TEXT,                       -- sentence fragment it was saved from
  hints           JSONB,                      -- [{locale, text}]
  status          SMALLINT,                   -- LingQ 0..3 (new -> known)
  extended_status SMALLINT,
  notes           TEXT,
  tags            TEXT[],
  srs_due_date    TIMESTAMPTZ,
  imported_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS lingq_terms_lang_status ON lingq_terms(lang, status);

-- ============================================================================
-- Personal error registry (Wave 7 Phase 1): 5+ years of teacher-marked
-- errors, normalized by codex commission A (docs/commissions/
-- CODEX_A_ERROR_REGISTRY.md). The raw corpus lives OUTSIDE this public
-- repo (~/projects/idiomatic-data/errmine on the operator's machine);
-- rows arrive via /admin/personal-errors-upload (stages one JSONL blob in
-- Postgres) and are ingested by the CRON container (LingQ containment
-- lesson: bulk DB imports never run in the web process). Feeds F3
-- error-correction generation + error-aware prompts + the Wave-5
-- planner prior.
-- ============================================================================

CREATE TABLE IF NOT EXISTS personal_errors (
  id                  BIGSERIAL PRIMARY KEY,
  registry_id         BIGINT,                    -- stable id from the private source registry
  lang                TEXT NOT NULL,
  kind                TEXT NOT NULL,           -- error|reteach|vocab_gap
  wrong               TEXT,                    -- attested wrong form (null for reteach/vocab_gap)
  right_form          TEXT NOT NULL,
  gloss_en            TEXT,
  category            TEXT NOT NULL,           -- controlled vocabulary (idiomatic/personal_errors.py)
  subcategory         TEXT,
  why                 TEXT,
  interference_source TEXT,                    -- es|pt|it|fr|en|ru|null
  occurrences         INT NOT NULL DEFAULT 1,
  first_seen          DATE,
  last_seen           DATE,
  sources             TEXT[],
  unit_hint           TEXT,
  confidence          TEXT,                    -- high|medium|low
  status              TEXT NOT NULL DEFAULT 'active',  -- active|retired
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Older deployments predate registry-id preservation.  Keep this as an
-- idempotent ALTER as well as in CREATE TABLE for both fresh and live DBs.
ALTER TABLE personal_errors ADD COLUMN IF NOT EXISTS registry_id BIGINT;
CREATE UNIQUE INDEX IF NOT EXISTS personal_errors_pair
  ON personal_errors (lang, COALESCE(wrong, ''), right_form);
CREATE UNIQUE INDEX IF NOT EXISTS personal_errors_registry_id
  ON personal_errors (registry_id) WHERE registry_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS personal_errors_lang_cat
  ON personal_errors (lang, category, kind);
-- Link to the ordinary verified grammar_items row produced for F3. Keeping
-- this on the source registry makes conversion resumable and idempotent.
ALTER TABLE personal_errors ADD COLUMN IF NOT EXISTS f3_item_id BIGINT;
CREATE INDEX IF NOT EXISTS personal_errors_f3_item_idx
  ON personal_errors (f3_item_id) WHERE f3_item_id IS NOT NULL;

-- Staging for the registry upload: the web process does ONE cheap blob
-- INSERT here; the cron container (which cannot see /data — that mount
-- belongs to idiomatic-app only) parses and batch-upserts on its next
-- tick, then stamps processed_at. Failed ingest leaves processed_at
-- NULL for retry; a corrupt payload gets processed_at set + note.
CREATE TABLE IF NOT EXISTS personal_errors_staging (
  id           BIGSERIAL PRIMARY KEY,
  payload      TEXT NOT NULL,                  -- raw JSONL
  n_rows       INT,
  uploaded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at TIMESTAMPTZ,
  note         TEXT
);

-- Curated cross-language interference pairs (F4).  The private JSON banks
-- never enter this public repository: the web process stages one raw JSON
-- blob in f4_pairs_staging and the cron process validates it against
-- personal_errors before upserting these rows.  pair_key is the stable
-- content identity; grammar_item_id keeps the Anki note id/GUID stable when
-- mutable evidence or presentation fields change on a later upload.
CREATE TABLE IF NOT EXISTS f4_pairs (
  id                  BIGSERIAL PRIMARY KEY,
  schema_version      INT NOT NULL,
  pair_key            TEXT NOT NULL,
  target_lang         TEXT NOT NULL,
  source_lang         TEXT NOT NULL,
  concept_en          TEXT NOT NULL,
  correct_target      TEXT NOT NULL,
  false_form          TEXT NOT NULL,
  source_form         TEXT NOT NULL,
  category            TEXT NOT NULL,
  why                 TEXT NOT NULL,
  occurrences         INT NOT NULL,
  attested            BOOLEAN NOT NULL,
  personal_error_id   BIGINT REFERENCES personal_errors(id) ON DELETE SET NULL,
  grammar_item_id     BIGINT REFERENCES grammar_items(id) ON DELETE SET NULL,
  needs_conversion    BOOLEAN NOT NULL DEFAULT TRUE,
  status              TEXT NOT NULL DEFAULT 'active', -- active|retired
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  converted_at        TIMESTAMPTZ,
  CHECK (schema_version > 0),
  CHECK (pair_key ~ '^[0-9a-f]{64}$'),
  CHECK (target_lang <> source_lang),
  CHECK (occurrences >= 0),
  CHECK ((attested AND occurrences >= 1)
         OR (NOT attested AND occurrences = 0)),
  CHECK (status IN ('active', 'retired'))
);
CREATE UNIQUE INDEX IF NOT EXISTS f4_pairs_pair_key
  ON f4_pairs(pair_key);
CREATE UNIQUE INDEX IF NOT EXISTS f4_pairs_grammar_item
  ON f4_pairs(grammar_item_id) WHERE grammar_item_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS f4_pairs_target_status
  ON f4_pairs(target_lang, status, needs_conversion);

CREATE TABLE IF NOT EXISTS f4_pairs_staging (
  id           BIGSERIAL PRIMARY KEY,
  payload      TEXT NOT NULL,                    -- raw private JSON bank
  n_rows       INT,
  uploaded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at TIMESTAMPTZ,
  note         TEXT
);

-- ============================================================================
-- Legacy +2 estate audit (docs/commissions/LEGACY_ESTATE_AUDIT_COMMISSION.md).
-- One row per source deck, including empty/container rows, from a checksummed
-- download-only AnkiWeb snapshot.  Audit-owned columns are reseeded from the
-- committed manifest on boot; owner_verdict/owner_note are deliberately not
-- overwritten by reseeding so the one-sitting owner gate remains durable.
-- This table is inventory only: no import worker consumes it.
-- ============================================================================

CREATE TABLE IF NOT EXISTS legacy_estate (
  deck_path             TEXT PRIMARY KEY,
  source_deck_id        BIGINT NOT NULL,
  parent_path           TEXT,
  depth                 SMALLINT NOT NULL CHECK (depth >= 0),
  top_level             TEXT NOT NULL,
  lang                  TEXT,
  direct_notes          INTEGER NOT NULL CHECK (direct_notes >= 0),
  direct_cards          INTEGER NOT NULL CHECK (direct_cards >= 0),
  direct_mature         INTEGER NOT NULL CHECK (direct_mature >= 0),
  direct_reps           BIGINT NOT NULL CHECK (direct_reps >= 0),
  direct_reviews        BIGINT NOT NULL CHECK (direct_reviews >= 0),
  direct_audio_notes    INTEGER NOT NULL CHECK (direct_audio_notes >= 0),
  direct_sound_tags     INTEGER NOT NULL CHECK (direct_sound_tags >= 0),
  direct_last_review    TIMESTAMPTZ,
  subtree_notes         INTEGER NOT NULL CHECK (subtree_notes >= 0),
  subtree_cards         INTEGER NOT NULL CHECK (subtree_cards >= 0),
  subtree_mature        INTEGER NOT NULL CHECK (subtree_mature >= 0),
  subtree_reps          BIGINT NOT NULL CHECK (subtree_reps >= 0),
  subtree_reviews       BIGINT NOT NULL CHECK (subtree_reviews >= 0),
  subtree_audio_notes   INTEGER NOT NULL CHECK (subtree_audio_notes >= 0),
  subtree_sound_tags    INTEGER NOT NULL CHECK (subtree_sound_tags >= 0),
  subtree_last_review   TIMESTAMPTZ,
  note_models           JSONB NOT NULL DEFAULT '[]'::jsonb,
  quality_flags         JSONB NOT NULL DEFAULT '[]'::jsonb,
  overlap               JSONB NOT NULL DEFAULT '[]'::jsonb,
  proposed_verdict      TEXT NOT NULL CHECK (
    proposed_verdict IN ('import', 'partial', 'skip', 'already-covered')
  ),
  proposal_reason       TEXT NOT NULL,
  owner_verdict         TEXT CHECK (
    owner_verdict IS NULL OR
    owner_verdict IN ('import', 'partial', 'skip', 'already-covered')
  ),
  owner_note            TEXT,
  source_sha256         TEXT NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
  audited_at            TIMESTAMPTZ NOT NULL,
  seeded_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS legacy_estate_tree_idx
  ON legacy_estate (top_level, deck_path);
CREATE INDEX IF NOT EXISTS legacy_estate_verdict_idx
  ON legacy_estate (COALESCE(owner_verdict, proposed_verdict));

-- Tiny generic KV: external service tokens + sync state stamps.
CREATE TABLE IF NOT EXISTS kv_store (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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

-- ============================================================================
-- Rescue Lab (docs/commissions/RESCUE_LAB_COMMISSION.md): struggle idioms
-- from the AnkiWeb revlog pull get rescue assets (comics, word-centered
-- images, glyphs) generated through switchable image providers, with full
-- cost accounting. rescue_items.status: candidate (uploaded, not yet
-- worked) | active (being rescued) | retired (released). strike = the
-- escalation-ladder rung (docs/research/RESCUE_PILOT.md).
-- ============================================================================

CREATE TABLE IF NOT EXISTS rescue_items (
  id                 BIGSERIAL PRIMARY KEY,
  lang               TEXT NOT NULL,
  idiom              TEXT NOT NULL,
  gloss              TEXT,
  anchor             TEXT,
  status             TEXT NOT NULL DEFAULT 'candidate',
  strike             SMALLINT NOT NULL DEFAULT 1,
  -- The one permanent glyph for this idiom (FK added below — the column
  -- references rescue_assets, which is created after this table).
  struggle_snapshot  JSONB,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (lang, idiom),
  CHECK (status IN ('candidate', 'active', 'retired')),
  CHECK (strike BETWEEN 1 AND 3)
);
CREATE INDEX IF NOT EXISTS rescue_items_lang_status ON rescue_items(lang, status);

-- Every generated/authored asset of an item. file_path is relative to
-- DATA_DIR/rescue_assets/. Video is deliberately NOT a legal format
-- (round-1 verdict: dropped, never offer it).
CREATE TABLE IF NOT EXISTS rescue_assets (
  id            BIGSERIAL PRIMARY KEY,
  item_id       BIGINT NOT NULL REFERENCES rescue_items(id) ON DELETE CASCADE,
  format        TEXT NOT NULL,
  provider      TEXT,
  model         TEXT,
  prompt        TEXT,
  params        JSONB,
  file_path     TEXT,
  mime          TEXT,
  cost_usd      NUMERIC(10, 5) NOT NULL DEFAULT 0,
  status        TEXT NOT NULL DEFAULT 'draft',
  verdict_note  TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (format IN ('comic', 'contrast', 'polysemy_map', 'anatomy',
                    'poster', 'glyph', 'svg', 'sentence_audio')),
  CHECK (status IN ('draft', 'approved', 'rejected'))
);
CREATE INDEX IF NOT EXISTS rescue_assets_item_idx ON rescue_assets(item_id, format);

-- Circular FK, added after both tables exist. ADD COLUMN IF NOT EXISTS
-- keeps re-application idempotent.
ALTER TABLE rescue_items ADD COLUMN IF NOT EXISTS glyph_asset_id
  BIGINT REFERENCES rescue_assets(id) ON DELETE SET NULL;

-- The polysemy "teach every door" rule lives on this table: approving a
-- polysemy_map asset requires >= 2 rows here (enforced in the verdict
-- endpoint). Every sense carries a gloss AND a micro-example — a door
-- that is only labeled is refused at the data level (NOT NULLs below).
CREATE TABLE IF NOT EXISTS rescue_senses (
  id          BIGSERIAL PRIMARY KEY,
  item_id     BIGINT NOT NULL REFERENCES rescue_items(id) ON DELETE CASCADE,
  label       TEXT NOT NULL,
  gloss       TEXT NOT NULL,
  example_tl  TEXT NOT NULL,
  example_en  TEXT NOT NULL,
  ord         SMALLINT NOT NULL DEFAULT 1,
  UNIQUE (item_id, ord)
);

-- Cost ledger: one row per PAID generation call, written at call time
-- whether or not the produced asset survives review — deleting/rejecting
-- an asset never un-spends the money, so month totals stay honest.
CREATE TABLE IF NOT EXISTS gen_ledger (
  id          BIGSERIAL PRIMARY KEY,
  provider    TEXT NOT NULL,
  model       TEXT NOT NULL,
  kind        TEXT NOT NULL,
  units       NUMERIC NOT NULL,
  unit_kind   TEXT NOT NULL,
  cost_usd    NUMERIC(10, 5) NOT NULL,
  item_id     BIGINT REFERENCES rescue_items(id) ON DELETE SET NULL,
  asset_id    BIGINT REFERENCES rescue_assets(id) ON DELETE SET NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (kind IN ('image', 'tts')),
  CHECK (unit_kind IN ('image', 'char'))
);
CREATE INDEX IF NOT EXISTS gen_ledger_created_idx ON gen_ledger(created_at);

-- Studied orphan notes re-adopted from the user's Anki collection
-- (2026-08-05): idiomatic-generated cards whose source rows were purged
-- or regenerated server-side but which the user has review history on.
-- The remediation pipeline treats these as first-class content alongside
-- expressions. fields = the note's field list verbatim (JSON array).
CREATE TABLE IF NOT EXISTS adopted_notes (
  guid           TEXT PRIMARY KEY,               -- Anki note guid
  lang           TEXT,
  model          TEXT NOT NULL,                  -- Anki notetype name
  deck           TEXT,                           -- deck at adoption time
  fields         JSONB NOT NULL,
  tags           TEXT[] NOT NULL DEFAULT '{}',
  reps           INTEGER NOT NULL DEFAULT 0,
  lapses         INTEGER NOT NULL DEFAULT 0,
  last_review_at TIMESTAMPTZ,
  adopted_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Asset Factory cast registry (commission-B §7 subset, built 2026-08-06
-- for the Cast Review panel). One row per cast character; the sheet +
-- ref photo live under /data/factory_cast/<slug>/. A new sheet on an
-- approved actor demotes status to candidate (staleness rule, famous-cast
-- doc §2.5) — enforced app-side in the upsert endpoint.
CREATE TABLE IF NOT EXISTS factory_actors (
  id                BIGSERIAL PRIMARY KEY,
  slug              TEXT NOT NULL UNIQUE,
  real_name         TEXT,
  lang              TEXT,          -- NULL = shared wing
  role_key          TEXT,          -- 'woman_35' | 'sopranos' | 'duo' | ...
  famous_source     TEXT,
  survival_prior    TEXT,
  exclusion_checked BOOLEAN NOT NULL DEFAULT FALSE,
  exclusion_verdict TEXT,
  status            TEXT NOT NULL DEFAULT 'candidate'
                    CHECK (status IN ('candidate','approved','retired')),
  review_flag       TEXT CHECK (review_flag IN ('ok','remake')),
  review_note       TEXT,
  ref_photo_path    TEXT,
  sheet_path        TEXT,
  sheet_hash        TEXT,
  prompt_desc       TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
