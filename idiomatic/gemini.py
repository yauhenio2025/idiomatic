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

_AUDIO_MIME = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".mp4": "audio/mp4",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".flac": "audio/flac",
}


async def generate_from_audio(prompt: str, audio_path: Path, *,
                               json_mode: bool = True,
                               temperature: float = 0.3,
                               timeout: float = 300.0) -> Any:
    """Send an audio file inline (base64) alongside a prompt. Returns JSON by default."""
    s = get_settings()
    audio_bytes = audio_path.read_bytes()
    mime = _AUDIO_MIME.get(audio_path.suffix.lower(), "audio/mpeg")
    parts = [
        {"text": prompt},
        {"inlineData": {"mimeType": mime,
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


_SARAH_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"
_SARAH_MODEL = "eleven_turbo_v2_5"


async def _silence_mp3(out: Path, ms: int = 300) -> None:
    """Write a tiny silent mp3 as a placeholder when TTS is unrecoverably blocked."""
    out.parent.mkdir(parents=True, exist_ok=True)
    import subprocess
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=24000",
         "-t", f"{ms/1000:.3f}",
         "-c:a", "libmp3lame", "-q:a", "9", str(out)],
        check=True,
    )


async def synthesize(text: str, *, voice: str, out: Path) -> None:
    """TTS via Gemini Flash TTS.

    On GeminiBlocked (safety filter, etc.):
      - English text (voice='Kore') → ElevenLabs Sarah (verified voice ID).
      - Anything else → write a silent placeholder so the calling concat
        doesn't crash. We lose that snippet but the rest of the deck survives.
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
        # English → Sarah; target-language → silence placeholder.
        if voice == "Kore" and s.elevenlabs_api_key:
            try:
                log.warning("gemini.tts.blocked.fallback_sarah",
                             err=str(e)[:120], text_head=text[:60])
                await _elevenlabs_sarah(text, out, s.elevenlabs_api_key)
                return
            except Exception as fb_err:
                log.warning("gemini.tts.fallback_sarah_failed",
                             err=repr(fb_err)[:200])
        log.warning("gemini.tts.blocked.using_silence",
                     voice=voice, err=str(e)[:120], text_head=text[:60])
        await _silence_mp3(out, ms=300)
        return

    audio_part = next((p for p in cand["content"]["parts"] if "inlineData" in p), None)
    if not audio_part:
        log.warning("gemini.tts.no_inline_data.using_silence", voice=voice)
        await _silence_mp3(out, ms=300)
        return
    pcm = base64.b64decode(audio_part["inlineData"]["data"])

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False,
                                      dir=out.parent) as f:
        wav_path = Path(f.name)
    try:
        wav_path.write_bytes(_pcm_to_wav(pcm))
        _wav_to_mp3(wav_path, out)
    finally:
        wav_path.unlink(missing_ok=True)


async def _elevenlabs_sarah(text: str, out: Path, api_key: str) -> None:
    """ElevenLabs Sarah — verified voice_id. English fallback only."""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{_SARAH_VOICE_ID}",
            headers={"xi-api-key": api_key,
                     "Content-Type": "application/json",
                     "Accept": "audio/mpeg"},
            json={"text": text, "model_id": _SARAH_MODEL,
                  "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
        )
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs Sarah failed: HTTP {r.status_code} {r.text[:200]}")
    out.write_bytes(r.content)
