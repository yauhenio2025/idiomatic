"""Switchable paid-media providers for the Rescue Lab (image only).

One registry, one entry point. The cost table lives HERE and nowhere
else — the generate endpoint writes gen_ledger rows from the number the
registry returned at call time, so a later price edit never rewrites
history.

Prices verified against https://ai.google.dev/gemini-api/docs/pricing
on 2026-08-05 (standard tier, 1K output — the resolution we generate at;
2K/4K cost more and are not offered). The commission draft said
0.039/0.02; the official page says 0.067/0.0336 — official wins.

Adding a non-Gemini provider later: one PROVIDERS entry whose "api"
names a new adapter, plus that adapter in _ADAPTERS. Nothing else
changes. Video providers are banned by user verdict (round 1: "not
helpful at all") — do not add one.
"""

from __future__ import annotations

import asyncio
import base64
from typing import Any, Awaitable, Callable

import httpx

from . import gemini
from .settings import get_settings

# Chinese-model prices are MEASURED, not list guesses, from the
# mandarin-videos benches (docs/analysis/QWEN_IMAGE_BENCH.md +
# SEEDREAM_BENCH.md + the qwen3 addendum gen-log, 2026-08-03/04):
# qwen-image-3.0-pro billed ¥0.25/1K-class image (fx 6.75 → $0.037);
# Seedream 5.0 Pro booked $0.06/page at the ≤2.36MP tier; the qwen 2.0
# family carries the official band top for its tier. `autopilot: True`
# marks providers the autonomous loop may spend on — the user directive
# (2026-08-05) is to steer clear of Nano Banana (expensive) and stick
# to the Chinese models, so the Gemini family is manual-only.
PROVIDERS: dict[str, dict[str, Any]] = {
    "qwen-image-3.0-pro": {
        "api": "dashscope-mm",
        "model": "qwen-image-3.0-pro",
        "usd_per_image": 0.037,
        "rpm": 1,
        "autopilot": True,
        "label": "Qwen-Image 3.0 Pro (DashScope) — default",
    },
    "qwen-image-2.0": {
        "api": "dashscope-mm",
        "model": "qwen-image-2.0",
        "usd_per_image": 0.05,
        "rpm": 120,
        "autopilot": True,
        "label": "Qwen-Image 2.0 (DashScope) — fast fallback",
    },
    "qwen-image-2.0-pro": {
        "api": "dashscope-mm",
        "model": "qwen-image-2.0-pro",
        "usd_per_image": 0.075,
        "rpm": 2,
        "autopilot": False,
        "label": "Qwen-Image 2.0 Pro (DashScope)",
    },
    "seedream-5.0-pro": {
        "api": "ark",
        "model": "doubao-seedream-5-0-pro-260628",
        "usd_per_image": 0.06,
        "rpm": 30,
        "autopilot": True,
        "label": "Seedream 5.0 Pro (Volcengine Ark)",
    },
    "nano-banana": {
        "api": "gemini",
        "model": "gemini-3.1-flash-image",
        "usd_per_image": 0.067,
        "rpm": 60,
        "autopilot": False,
        "label": "Nano Banana (Gemini 3.1 Flash Image) — expensive, manual only",
    },
    "nano-banana-lite": {
        "api": "gemini",
        "model": "gemini-3.1-flash-lite-image",
        "usd_per_image": 0.0336,
        "rpm": 60,
        "autopilot": False,
        "label": "Nano Banana Lite (Gemini 3.1 Flash Lite Image) — manual only",
    },
}

DEFAULT_PROVIDER = "qwen-image-3.0-pro"


def autopilot_providers() -> list[str]:
    return [k for k, v in PROVIDERS.items() if v.get("autopilot")]


class UnknownProvider(ValueError):
    pass


def provider_info(provider_key: str) -> dict[str, Any]:
    try:
        return PROVIDERS[provider_key]
    except KeyError:
        raise UnknownProvider(
            f"unknown provider {provider_key!r}; "
            f"known: {sorted(PROVIDERS)}") from None


def estimate_image_cost(provider_key: str) -> float:
    """What one generate_image call will cost — shown in the dashboard
    BEFORE the call, and written to gen_ledger after it."""
    return float(provider_info(provider_key)["usd_per_image"])


def sniff_mime(image: bytes) -> str:
    if image[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image[:4] == b"RIFF" and image[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


async def _gemini_image(model: str, prompt: str,
                        params: dict[str, Any]) -> bytes:
    return await gemini.generate_image_bytes(
        prompt, model=model,
        aspect_ratio=str(params.get("aspect_ratio", "4:3")))


_DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/api/v1"
_ARK_BASE = "https://ark.cn-beijing.volces.com/api/v3"


def _is_throttle(code: str, msg: str) -> bool:
    t = f"{code} {msg}".lower()
    return "throttl" in t or "requests rate" in t or "too many" in t


async def _dashscope_mm_image(model: str, prompt: str,
                              params: dict[str, Any]) -> bytes:
    """Qwen image via the sync multimodal-generation route — the shape
    validated by the mandarin-videos bench (call_mm in generate-qwen.py).
    qwen-image-3.0-pro is rate-limited to 1 req/min on this account, so
    throttles get a 65 s backoff instead of failing the call."""
    key = get_settings().dashscope_api_key
    if not key:
        raise RuntimeError("DASHSCOPE_API_KEY not configured")
    content: list[dict[str, str]] = []
    if params.get("image_b64"):
        # Reference-image input (factory cast sheets): data-URI in the
        # same multimodal content list, before the instruction text.
        content.append(
            {"image": f"data:image/jpeg;base64,{params['image_b64']}"})
    content.append({"text": prompt})
    body = {
        "model": model,
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": {"watermark": False,
                       "size": str(params.get("size", "1140*1472")),
                       "prompt_extend": False},
    }
    async with httpx.AsyncClient(timeout=300) as client:
        for attempt in range(4):
            r = await client.post(
                f"{_DASHSCOPE_BASE}/services/aigc/multimodal-generation/generation",
                headers={"Authorization": f"Bearer {key}"}, json=body)
            j = r.json()
            if r.status_code == 200:
                try:
                    content = j["output"]["choices"][0]["message"]["content"]
                    url = next(c["image"] for c in content if "image" in c)
                except (KeyError, IndexError, StopIteration):
                    raise RuntimeError(
                        f"dashscope: 200 but no image in response: "
                        f"{str(j)[:200]}")
                img = await client.get(url)
                img.raise_for_status()
                return img.content
            code, msg = str(j.get("code", r.status_code)), str(j.get("message", ""))
            if _is_throttle(code, msg) and attempt < 3:
                await asyncio.sleep(65)
                continue
            raise RuntimeError(f"dashscope {model}: {code} {msg[:200]}")
    raise RuntimeError(f"dashscope {model}: throttled after retries")


async def _ark_image(model: str, prompt: str,
                     params: dict[str, Any]) -> bytes:
    """Seedream via Ark's OpenAI-style images/generations — the shape
    validated by the Seedream bench (generate-seedream.py). Default size
    sits in the ≤2.36MP cheap tier."""
    key = get_settings().ark_api_key
    if not key:
        raise RuntimeError("ARK_API_KEY not configured")
    body = {"model": model, "prompt": prompt,
            "size": str(params.get("size", "1328x1770")),
            "watermark": False}
    if params.get("image_b64"):
        body["image"] = f"data:image/jpeg;base64,{params['image_b64']}"
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(f"{_ARK_BASE}/images/generations",
                              headers={"Authorization": f"Bearer {key}"},
                              json=body)
        j = r.json()
        if r.status_code == 200 and j.get("data"):
            d0 = j["data"][0]
            if d0.get("b64_json"):
                return base64.b64decode(d0["b64_json"])
            if d0.get("url"):
                img = await client.get(d0["url"])
                img.raise_for_status()
                return img.content
        err = (j.get("error") or {}).get("message") or str(j)
        raise RuntimeError(f"ark {model}: {r.status_code} {str(err)[:200]}")


# api name → adapter(model, prompt, params) -> image bytes. Retry and
# safety handling live inside each adapter's client module (tenacity in
# gemini._image_post for the Gemini family; explicit throttle backoff
# in the DashScope adapter).
_ADAPTERS: dict[str, Callable[[str, str, dict[str, Any]], Awaitable[bytes]]] = {
    "gemini": _gemini_image,
    "dashscope-mm": _dashscope_mm_image,
    "ark": _ark_image,
}


async def generate_image(provider_key: str, prompt: str, *,
                         params: dict[str, Any] | None = None,
                         ) -> tuple[bytes, float]:
    """Generate one image via the named provider.

    Returns (image_bytes, cost_usd). Raises on any failure — a failed
    call produces no bytes and, per the Gemini billing model, no image
    charge, so the caller writes gen_ledger only on success.
    """
    info = provider_info(provider_key)
    adapter = _ADAPTERS[info["api"]]
    p = dict(params or {})
    # Explicit model override rides on the provider's api/pricing entry —
    # used to probe sibling model slugs (e.g. dashscope edit variants)
    # without a registry change per experiment.
    model = str(p.pop("model_override", "") or info["model"])
    image = await adapter(model, prompt, p)
    return image, float(info["usd_per_image"])
