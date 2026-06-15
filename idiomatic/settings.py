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
    sign_key: str = "dev-insecure-change-me"

    # --- LLM / TTS ----------------------------------------------------------
    gemini_api_key: str
    gemini_text_model: str = "gemini-3.5-flash"          # text + audio understanding
    gemini_tts_model: str = "gemini-3.1-flash-tts-preview"

    # Fallback TTS provider (used only if we swap voices via tts_provider)
    elevenlabs_api_key: str | None = None

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
    max_new_apkgs_per_lang_per_day: int = 3


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
