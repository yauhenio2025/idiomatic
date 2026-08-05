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

from typing import Any, Awaitable, Callable

from . import gemini

PROVIDERS: dict[str, dict[str, Any]] = {
    "nano-banana": {
        "api": "gemini",
        "model": "gemini-3.1-flash-image",
        "usd_per_image": 0.067,
        "label": "Nano Banana (Gemini 3.1 Flash Image)",
    },
    "nano-banana-lite": {
        "api": "gemini",
        "model": "gemini-3.1-flash-lite-image",
        "usd_per_image": 0.0336,
        "label": "Nano Banana Lite (Gemini 3.1 Flash Lite Image)",
    },
}


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


# api name → adapter(model, prompt, params) -> image bytes. Retry and
# safety handling live inside each adapter's client module (tenacity in
# gemini._image_post for the Gemini family).
_ADAPTERS: dict[str, Callable[[str, str, dict[str, Any]], Awaitable[bytes]]] = {
    "gemini": _gemini_image,
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
    image = await adapter(info["model"], prompt, params or {})
    return image, float(info["usd_per_image"])
