"""TTS provider-chain routing tests: qwen-local → elevenlabs → gemini.
Deterministic — no network, no DB, no GPU."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import httpx
import pytest

from idiomatic import gemini

_REAL_ASYNC_CLIENT = httpx.AsyncClient


def _settings(**over):
    base = dict(
        tts_provider="qwen-local",
        qwen_tts_token="tok",
        qwen_tts_urls="http://bridge.test",
        qwen_tts_langs="en,de,es,fr,it,pt,zh",
        qwen_tts_health_ttl_sec=60,
        qwen_tts_timeout_sec=5.0,
        elevenlabs_api_key="k",
        elevenlabs_model="eleven_turbo_v2_5",
        gemini_tts_model="gemini-tts",
        tts_concurrency=4,
    )
    base.update(over)
    return SimpleNamespace(**base)


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    gemini._QWEN.update({"url": None, "checked": 0.0, "lock": None})
    monkeypatch.setattr(gemini, "_TTS_SEM", None)
    yield
    gemini._QWEN.update({"url": None, "checked": 0.0, "lock": None})


def _mock_transport(monkeypatch, handler):
    transport = httpx.MockTransport(handler)

    def factory(**kw):
        kw.pop("transport", None)
        return _REAL_ASYNC_CLIENT(transport=transport, **kw)

    monkeypatch.setattr(gemini.httpx, "AsyncClient", factory)


# --- synthesize() routing ---------------------------------------------------

def test_qwen_primary_short_circuits(monkeypatch, tmp_path):
    calls = []

    async def fake_qwen(text, out, lang):
        out.write_bytes(b"x" * 2000)
        calls.append(lang)

    async def fake_el(*a, **k):
        raise AssertionError("ElevenLabs must not be called")

    monkeypatch.setattr(gemini, "get_settings", lambda: _settings())
    monkeypatch.setattr(gemini, "_qwen_local_tts", fake_qwen)
    monkeypatch.setattr(gemini, "_elevenlabs_tts", fake_el)
    out = tmp_path / "a.mp3"
    asyncio.run(gemini.synthesize("hola", voice="Kore", out=out, lang="es"))
    assert calls == ["es"]
    assert out.read_bytes() == b"x" * 2000


def test_qwen_down_falls_back_to_elevenlabs(monkeypatch, tmp_path):
    el_calls = []

    async def fake_qwen(text, out, lang):
        raise gemini.QwenLocalDown("no healthy bridge")

    async def fake_el(text, out, api_key, *, lang="en", voice_id=None):
        out.write_bytes(b"e" * 2000)
        el_calls.append(lang)

    monkeypatch.setattr(gemini, "get_settings", lambda: _settings())
    monkeypatch.setattr(gemini, "_qwen_local_tts", fake_qwen)
    monkeypatch.setattr(gemini, "_elevenlabs_tts", fake_el)
    out = tmp_path / "a.mp3"
    asyncio.run(gemini.synthesize("hallo", voice="Kore", out=out, lang="de"))
    assert el_calls == ["de"]
    assert out.exists()


def test_unserved_lang_skips_qwen(monkeypatch, tmp_path):
    async def fake_qwen(text, out, lang):
        raise AssertionError("bridge must not be called for unserved lang")

    async def fake_el(text, out, api_key, *, lang="en", voice_id=None):
        out.write_bytes(b"e" * 2000)

    monkeypatch.setattr(
        gemini, "get_settings", lambda: _settings(qwen_tts_langs="es,de"))
    monkeypatch.setattr(gemini, "_qwen_local_tts", fake_qwen)
    monkeypatch.setattr(gemini, "_elevenlabs_tts", fake_el)
    out = tmp_path / "a.mp3"
    asyncio.run(gemini.synthesize("ciao", voice="Kore", out=out, lang="it"))
    assert out.exists()


def test_explicit_eleven_voice_skips_qwen(monkeypatch, tmp_path):
    seen = {}

    async def fake_qwen(text, out, lang):
        raise AssertionError("explicit ElevenLabs voice must bypass bridge")

    async def fake_el(text, out, api_key, *, lang="en", voice_id=None):
        out.write_bytes(b"e" * 2000)
        seen["voice_id"] = voice_id

    monkeypatch.setattr(gemini, "get_settings", lambda: _settings())
    monkeypatch.setattr(gemini, "_qwen_local_tts", fake_qwen)
    monkeypatch.setattr(gemini, "_elevenlabs_tts", fake_el)
    out = tmp_path / "a.mp3"
    asyncio.run(gemini.synthesize("hola", voice="Kore", out=out, lang="es",
                                  eleven_voice_id="v123"))
    assert seen["voice_id"] == "v123"


def test_missing_token_skips_qwen(monkeypatch, tmp_path):
    async def fake_qwen(text, out, lang):
        raise AssertionError("bridge must not be called without a token")

    async def fake_el(text, out, api_key, *, lang="en", voice_id=None):
        out.write_bytes(b"e" * 2000)

    monkeypatch.setattr(
        gemini, "get_settings", lambda: _settings(qwen_tts_token=None))
    monkeypatch.setattr(gemini, "_qwen_local_tts", fake_qwen)
    monkeypatch.setattr(gemini, "_elevenlabs_tts", fake_el)
    out = tmp_path / "a.mp3"
    asyncio.run(gemini.synthesize("hola", voice="Kore", out=out, lang="es"))
    assert out.exists()


# --- _qwen_local_tts transport behavior -------------------------------------

def test_bridge_success_writes_bytes_and_heals_marker(monkeypatch, tmp_path):
    s = _settings()
    monkeypatch.setattr(gemini, "get_settings", lambda: s)
    ledger = []

    async def fake_ledger(chars):
        ledger.append(chars)

    monkeypatch.setattr(gemini, "_qwen_ledger", fake_ledger)
    mp3 = b"ID3" + b"\x00" * 2000

    def handler(request):
        if request.url.path == "/health":
            assert request.headers["authorization"] == "Bearer tok"
            return httpx.Response(200, json={"ok": True})
        assert request.url.path == "/synth"
        return httpx.Response(200, content=mp3)

    _mock_transport(monkeypatch, handler)
    out = tmp_path / "clip.mp3"
    out.write_bytes(b"\x00")  # stale silence placeholder
    gemini.silence_marker(out).touch()
    asyncio.run(gemini._qwen_local_tts("hola que tal", out, "es"))
    assert out.read_bytes() == mp3
    assert not gemini.silence_marker(out).exists()
    assert ledger == [len("hola que tal")]


def test_bridge_503_marks_down_for_ttl(monkeypatch, tmp_path):
    s = _settings()
    monkeypatch.setattr(gemini, "get_settings", lambda: s)
    probes = []

    def handler(request):
        if request.url.path == "/health":
            probes.append(1)
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(503, json={"error": "comfyui rendering"})

    _mock_transport(monkeypatch, handler)
    out = tmp_path / "clip.mp3"
    with pytest.raises(gemini.QwenLocalDown):
        asyncio.run(gemini._qwen_local_tts("hola", out, "es"))
    # Down-flag memoized: the next clip inside the TTL fails fast with no
    # second probe — that's the per-batch (not per-clip) failover.
    with pytest.raises(gemini.QwenLocalDown):
        asyncio.run(gemini._qwen_local_tts("hola", out, "es"))
    assert probes == [1]
    assert not out.exists()


def test_health_probe_failure_memoized(monkeypatch):
    s = _settings()
    monkeypatch.setattr(gemini, "get_settings", lambda: s)
    probes = []

    def handler(request):
        probes.append(1)
        raise httpx.ConnectError("refused", request=request)

    _mock_transport(monkeypatch, handler)
    assert asyncio.run(gemini._qwen_healthy_url(s)) is None
    assert asyncio.run(gemini._qwen_healthy_url(s)) is None
    assert probes == [1]


def test_bridge_500_is_per_clip_not_down(monkeypatch, tmp_path):
    s = _settings()
    monkeypatch.setattr(gemini, "get_settings", lambda: s)

    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(500, json={"error": "synthesis failed"})

    _mock_transport(monkeypatch, handler)
    out = tmp_path / "clip.mp3"
    with pytest.raises(RuntimeError):
        asyncio.run(gemini._qwen_local_tts("hola", out, "es"))
    # A per-clip 500 must NOT down-flag the provider.
    assert gemini._QWEN["url"] == "http://bridge.test"
