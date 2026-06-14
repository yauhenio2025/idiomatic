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

    # Fallback / future
    elevenlabs_api_key: str | None = None

    # --- email --------------------------------------------------------------
    resend_api_key: str | None = None
    email_from: str = "idiomatic@example.com"

    # --- pipeline tunables --------------------------------------------------
    min_duration_sec: int = 5 * 60
    max_duration_sec: int = 15 * 60
    target_idioms_per_video: int = 12      # rough target before dedup
    worker_poll_interval_sec: int = 10
    worker_max_attempts: int = 3


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
