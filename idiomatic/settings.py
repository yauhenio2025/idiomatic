"""Env-driven settings. Single source of truth."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",
                                       extra="ignore")

    # --- infrastructure -----------------------------------------------------
    database_url: str
    data_dir: Path = Path("/data")
    app_base_url: str = "http://localhost:8000"
    # Bearer for /admin/* endpoints (X-Admin-Token header). Separate from
    # the per-agent tokens in the agents table, which only grant /apkgs/*.
    # Admin endpoints refuse everything while this is unset.
    admin_token: str | None = None

    # --- LLM / TTS ----------------------------------------------------------
    gemini_api_key: str
    gemini_text_model: str = "gemini-3.5-flash"          # text + audio understanding
    gemini_tts_model: str = "gemini-3.1-flash-tts-preview"

    # Primary TTS provider. "elevenlabs" (default) is ~40× cheaper per
    # character than the Gemini TTS preview (July 2026 audit: Gemini billed
    # ~€2/1k chars vs ElevenLabs turbo at $0.05/1k) and doesn't safety-block
    # target-language content. Set to "gemini" to roll back instantly.
    tts_provider: str = "elevenlabs"
    elevenlabs_api_key: str | None = None
    # Turbo v2.5: 0.5 credit/char, supports language_code enforcement.
    elevenlabs_model: str = "eleven_turbo_v2_5"

    # YouTube Data API v3 — the cron uses it to pre-filter videos by
    # duration BEFORE any Oxylabs spend (official API, no bot wall; a full
    # 24-channel walk costs ~5 quota units of the 10k/day free tier).
    # When unset or erroring, the cron enqueues blind and the worker's
    # post-download ffprobe gate catches out-of-window videos instead.
    youtube_api_key: str | None = None

    # --- Oxylabs YouTube Downloader (replaces yt-dlp) -----------------------
    oxylabs_user: str | None = None
    oxylabs_pass: str | None = None
    # Oxylabs pushes the .m4a to S3-compatible storage; we use Cloudflare R2.
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_endpoint: str | None = None
    r2_bucket: str = "idiomatic-yt-audio"
    # How long to wait for Oxylabs to finish a download (seconds).
    oxylabs_max_wait_sec: int = 900
    oxylabs_poll_interval_sec: int = 15

    # --- pipeline tunables --------------------------------------------------
    # Min bumped from 5→7 min so we skip the firehose of short news clips
    # (tagesschau alone publishes ~50/day; the longer pieces are richer in
    # idiomatic content anyway).
    min_duration_sec: int = 7 * 60
    max_duration_sec: int = 15 * 60
    target_idioms_per_video: int = 12               # rough Gemini extraction target
    worker_poll_interval_sec: int = 10
    worker_max_attempts: int = 3

    # Soft cap on inflow — keeps daily Anki import manageable.
    # Counted against apkgs created today, not videos processed.
    # (Temporarily 100 on 2026-07-29 to batch the auto-dub requeue
    # backlog; restored to 3 on 2026-07-30 after it drained cleanly.)
    max_new_apkgs_per_lang_per_day: int = 3

    # Queued videos older than this expire to 'skipped' (cron, every 2h).
    # RSS inflow (~34/day) permanently outruns build capacity (15/day), so
    # without expiry the backlog grows ~20/day forever and decks are built
    # from ever-staler news. Priority (>=10) and curated channels are
    # exempt — those are deliberately mined back-catalog. 0 disables.
    queue_expiry_days: int = 7

    # LingQ vocabulary mirror: cron re-syncs when the last pull is older
    # than this (user adds new LingQs rarely). 0 disables auto-sync.
    lingq_sync_interval_hours: int = 24
    # Emergency escape hatch only: sync in the WEB process. Twice on
    # 2026-07-31 a full sync coincided with the web app hanging (root
    # cause still unproven — batched transactions did NOT fix it), so
    # sync now runs exclusively in the cron container by default.
    lingq_web_sync_enabled: bool = False

    # Video apkg FILES older than this get deleted by the cron once every
    # agent that should receive them has acked ok (DB row stays; download
    # of a reaped file returns 410). Pool apkgs are exempt — they're
    # replaced wholesale on every rebuild.
    apkg_retention_days: int = 30

    # How many failed delivery attempts before /apkgs/pending stops
    # re-offering an apkg to an agent. A transient blip (network, locked
    # collection) used to bury the deck forever on the first failed ack.
    ack_retry_budget: int = 5

    # Skip a pool rebuild if the same language was rebuilt more recently
    # than this (worker fires one per processed video; back-to-back videos
    # in one language made that expensive). /admin/rebuild-pools bypasses.
    pool_rebuild_debounce_min: int = 30

    # --- parallelism --------------------------------------------------------
    # Concurrent Gemini TTS HTTP calls. Tier-1 paid Gemini allows ~60-300
    # RPM for the TTS preview; 8 in flight stays well clear while pushing
    # ~5× throughput vs. sequential.
    tts_concurrency: int = 8
    # Concurrent idioms processed inside a single video. Each idiom fires
    # ~15-25 TTS calls, so the global cap above is what actually bounds the
    # total. 3 idioms × 8 TTS slots saturates without bursting.
    idiom_parallelism: int = 3


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
