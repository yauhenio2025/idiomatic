"""Gemini 3.5 Flash wrappers — text, audio-input, and TTS in one place.

All three live in this module so the pipeline only imports one boundary.
Retries via tenacity. JSON responses use Gemini's responseMimeType so we
don't need to clean up code fences.
"""

from __future__ import annotations

import base64
import io
import json
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import httpx
import structlog
from tenacity import (
    retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter,
)

from .settings import get_settings

log = structlog.get_logger()


class GeminiBlocked(Exception):
    """Response had no candidate (safety filter, etc.). Don't retry — the
    caller's prompt or content is the problem."""


class GeminiTransient(Exception):
    """5xx / 429 / connection errors. Tenacity retries."""


_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _model_url(model: str) -> str:
    return f"{_BASE}/{model}:generateContent"


@retry(
    retry=retry_if_exception_type(GeminiTransient),
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=2, max=30),
    reraise=True,
)
async def _call(model: str, parts: list[dict], *,
                response_mime_type: str | None = None,
                response_modalities: list[str] | None = None,
                speech_voice: str | None = None,
                temperature: float = 0.3,
                timeout: float = 240.0) -> dict:
    s = get_settings()
    gen_config: dict[str, Any] = {"temperature": temperature}
    if response_mime_type:
        gen_config["responseMimeType"] = response_mime_type
    if response_modalities:
        gen_config["responseModalities"] = response_modalities
    if speech_voice:
        gen_config["speechConfig"] = {
            "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": speech_voice}},
        }

    body = {"contents": [{"parts": parts}], "generationConfig": gen_config}
    url = _model_url(model)

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, params={"key": s.gemini_api_key}, json=body)

    if r.status_code in (429, 500, 502, 503, 504):
        raise GeminiTransient(f"HTTP {r.status_code}: {r.text[:200]}")
    if r.status_code >= 400:
        raise GeminiBlocked(f"HTTP {r.status_code}: {r.text[:300]}")

    body_json = r.json()
    cands = body_json.get("candidates") or []
    if not cands:
        fb = body_json.get("promptFeedback") or {}
        raise GeminiBlocked(f"no candidates; feedback={fb}")
    return cands[0]


# ============================================================================
# 1. Text generation (with optional JSON structured output)
# ============================================================================

async def generate_text(prompt: str, *, json_mode: bool = False,
                         temperature: float = 0.3) -> str | Any:
    """Returns the text payload (or parsed JSON if json_mode)."""
    s = get_settings()
    parts = [{"text": prompt}]
    cand = await _call(
        s.gemini_text_model, parts,
        response_mime_type="application/json" if json_mode else None,
        temperature=temperature,
    )
    text = cand["content"]["parts"][0]["text"].strip()
    return json.loads(text) if json_mode else text


# ============================================================================
# 2. Audio-input extraction — the key M2 capability that lets us skip Whisper
# ============================================================================

async def generate_from_audio(prompt: str, audio_path: Path, *,
                               json_mode: bool = True,
                               temperature: float = 0.3,
                               timeout: float = 300.0) -> Any:
    """Send an mp3 inline (base64) alongside a prompt. Returns JSON by default."""
    s = get_settings()
    audio_bytes = audio_path.read_bytes()
    parts = [
        {"text": prompt},
        {"inlineData": {"mimeType": "audio/mpeg",
                         "data": base64.b64encode(audio_bytes).decode()}},
    ]
    cand = await _call(
        s.gemini_text_model, parts,
        response_mime_type="application/json" if json_mode else None,
        temperature=temperature, timeout=timeout,
    )
    text = cand["content"]["parts"][0]["text"].strip()
    return json.loads(text) if json_mode else text


# ============================================================================
# 3. TTS — Gemini 3.1 Flash TTS preview (returns raw PCM, we wrap to wav→mp3)
# ============================================================================

def _pcm_to_wav(pcm: bytes, sample_rate: int = 24000) -> bytes:
    """Wrap raw 16-bit PCM mono in a minimal RIFF/WAVE header."""
    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + len(pcm)))
    buf.write(b"WAVEfmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    buf.write(b"data"); buf.write(struct.pack("<I", len(pcm)))
    buf.write(pcm)
    return buf.getvalue()


def _wav_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-i", str(wav_path), "-c:a", "libmp3lame", "-q:a", "4", str(mp3_path)],
        check=True,
    )


async def synthesize(text: str, *, voice: str, out: Path) -> None:
    """TTS via Gemini Flash TTS. Falls back to ElevenLabs on GeminiBlocked
    if ELEVENLABS_API_KEY is set (covers the safety-filter case).
    Idempotent: skips if `out` already exists with size > 0.
    """
    if out.exists() and out.stat().st_size > 0:
        return
    out.parent.mkdir(parents=True, exist_ok=True)

    s = get_settings()
    parts = [{"text": text}]
    try:
        cand = await _call(
            s.gemini_tts_model, parts,
            response_modalities=["AUDIO"],
            speech_voice=voice,
            timeout=180,
        )
    except GeminiBlocked as e:
        if not s.elevenlabs_api_key:
            raise
        log.warning("gemini.tts.blocked.fallback_elevenlabs", err=str(e)[:120])
        await _elevenlabs_fallback(text, voice, out)
        return

    audio_part = next((p for p in cand["content"]["parts"] if "inlineData" in p), None)
    if not audio_part:
        raise GeminiBlocked("Gemini TTS returned no inlineData part")
    pcm = base64.b64decode(audio_part["inlineData"]["data"])

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False,
                                      dir=out.parent) as f:
        wav_path = Path(f.name)
    try:
        wav_path.write_bytes(_pcm_to_wav(pcm))
        _wav_to_mp3(wav_path, out)
    finally:
        wav_path.unlink(missing_ok=True)


# ---- ElevenLabs fallback (only used when Gemini TTS refuses a payload) ----

# Voice mapping mirrors the pimsleur LANG_VOICES.
_ELEVENLABS_VOICE_BY_GEMINI = {
    "Charon":  ("dlGxemPxFMTY7iXagmOj", "eleven_multilingual_v2"),  # Johannes Dokumentarfilm (DE)
    "Aoede":   ("h5HFD5gAWf8oVdGbAW1L", "eleven_multilingual_v2"),  # Claire Estelle (FR)
    "Leda":    ("uScy1bXtKz8vPzfdFsFw", "eleven_multilingual_v2"),  # Giovanni Rossi (IT)
    "Orus":    ("v7iolaAOTNCBKtFhJzZc", "eleven_multilingual_v2"),  # Marcelo Costa (PT-BR)
    "Fenrir":  ("piI8Kku0DcvcL6TTSeQI", "eleven_multilingual_v2"),  # Eleguar (ES)
    "Kore":    ("EXAVITQu4vr4xnSDxMaL", "eleven_turbo_v2_5"),         # Sarah (EN, narration)
}


async def _elevenlabs_fallback(text: str, gemini_voice: str, out: Path) -> None:
    s = get_settings()
    voice_id, model = _ELEVENLABS_VOICE_BY_GEMINI.get(
        gemini_voice, _ELEVENLABS_VOICE_BY_GEMINI["Kore"])
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": s.elevenlabs_api_key or "",
                     "Content-Type": "application/json",
                     "Accept": "audio/mpeg"},
            json={"text": text, "model_id": model,
                  "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
        )
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs fallback failed: HTTP {r.status_code}")
    out.write_bytes(r.content)
