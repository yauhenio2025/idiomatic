"""Shared Rescue Lab operations — the one code path that turns a
generation request into a staged file + rescue_assets row + gen_ledger
row. Used by the /admin/rescue/generate endpoint (synchronous, dashboard)
and by the autopilot (idiomatic/rescue_autopilot.py)."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from . import db, genmedia
from .settings import get_settings


async def generate_asset(item_id: int, fmt: str, provider: str,
                         prompt: str, params: dict[str, Any] | None = None,
                         ) -> dict:
    """Generate one image, stage it, insert draft asset + ledger row.
    The prompt must already be filled/validated by the caller. Raises on
    provider failure (no ledger row is written — Gemini/DashScope/Ark
    do not bill failed image requests)."""
    params = params or {}
    image, cost_usd = await genmedia.generate_image(
        provider, prompt, params=params)
    mime = genmedia.sniff_mime(image)
    ext = {"image/png": "png", "image/jpeg": "jpg",
           "image/webp": "webp"}.get(mime, "bin")
    rel = f"{item_id}/{fmt}_{secrets.token_hex(4)}.{ext}"
    path = Path(get_settings().data_dir) / "rescue_assets" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image)

    info = genmedia.PROVIDERS[provider]
    pool = await db.get_pool()
    asset = await pool.fetchrow(
        """
        INSERT INTO rescue_assets (item_id, format, provider, model, prompt,
                                   params, file_path, mime, cost_usd)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9)
        RETURNING *
        """,
        item_id, fmt, provider, info["model"], prompt,
        json.dumps(params, ensure_ascii=False), rel, mime, cost_usd)
    await pool.execute(
        """
        INSERT INTO gen_ledger (provider, model, kind, units, unit_kind,
                                cost_usd, item_id, asset_id)
        VALUES ($1, $2, 'image', 1, 'image', $3, $4, $5)
        """,
        provider, info["model"], cost_usd, item_id, asset["id"])
    return dict(asset)
