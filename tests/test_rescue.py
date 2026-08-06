"""Rescue Lab tests: deterministic, no network.

The schema round-trip runs against an EPHEMERAL local Postgres (initdb
into a tmp dir, unix socket only) because schema.sql is Postgres SQL —
sqlite can't parse it. Skips cleanly where the postgres binaries are
absent; everything else runs anywhere.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

import pytest

from idiomatic import genmedia, rescue


# --- provider registry ------------------------------------------------------

def test_registry_entries_are_complete_and_image_only():
    assert set(genmedia.PROVIDERS) == {
        "qwen-image-3.0-pro", "qwen-image-2.0", "qwen-image-2.0-pro",
        "seedream-5.0-pro", "nano-banana", "nano-banana-lite"}
    for key, info in genmedia.PROVIDERS.items():
        assert info["api"] in genmedia._ADAPTERS, key
        assert isinstance(info["model"], str) and info["model"]
        assert 0 < info["usd_per_image"] < 1
        assert "video" not in info["model"], "video providers are banned"


def test_cost_estimate_comes_from_the_single_table():
    assert genmedia.estimate_image_cost("nano-banana") == pytest.approx(0.067)
    assert genmedia.estimate_image_cost("nano-banana-lite") == pytest.approx(0.0336)
    with pytest.raises(genmedia.UnknownProvider):
        genmedia.estimate_image_cost("minimax-video")


def test_generate_image_returns_table_cost(monkeypatch):
    seen = {}

    async def fake_bytes(prompt, *, model=None, aspect_ratio="4:3"):
        seen.update(prompt=prompt, model=model, aspect_ratio=aspect_ratio)
        return b"\x89PNG\r\n\x1a\n" + b"x" * 20

    monkeypatch.setattr(genmedia.gemini, "generate_image_bytes", fake_bytes)
    image, cost = asyncio.run(genmedia.generate_image(
        "nano-banana-lite", "a poster", params={"aspect_ratio": "1:1"}))
    assert image.startswith(b"\x89PNG")
    assert cost == pytest.approx(0.0336)
    assert seen["model"] == "gemini-3.1-flash-lite-image"
    assert seen["aspect_ratio"] == "1:1"


def test_generate_image_model_override_and_image_param(monkeypatch):
    """model_override reaches the adapter as the model; image_b64 rides
    through in params (the factory cloud-sheet path); pricing stays the
    registry's — overrides never invent a price."""
    seen = {}

    async def fake_adapter(model, prompt, params):
        seen.update(model=model, prompt=prompt, params=dict(params))
        return b"\x89PNGfake"

    monkeypatch.setitem(genmedia._ADAPTERS, "dashscope-mm", fake_adapter)
    image, cost = asyncio.run(genmedia.generate_image(
        "qwen-image-3.0-pro", "a sheet",
        params={"image_b64": "QUJD", "size": "1328*1328",
                "model_override": "qwen-image-edit-x"}))
    assert image == b"\x89PNGfake"
    assert cost == pytest.approx(0.037)
    assert seen["model"] == "qwen-image-edit-x"
    assert seen["params"]["image_b64"] == "QUJD"
    assert "model_override" not in seen["params"]
    # and without the override the registry model is used
    asyncio.run(genmedia.generate_image("qwen-image-3.0-pro", "p"))
    assert seen["model"] == "qwen-image-3.0-pro"


def test_sniff_mime():
    assert genmedia.sniff_mime(b"\x89PNG\r\n\x1a\n123") == "image/png"
    assert genmedia.sniff_mime(b"\xff\xd8\xff\xe0rest") == "image/jpeg"
    assert genmedia.sniff_mime(b"RIFF1234WEBPmore") == "image/webp"
    assert genmedia.sniff_mime(b"???") == "application/octet-stream"


# --- format taxonomy + templates --------------------------------------------

_ITEM = {
    "lang": "es", "idiom": "está tirado",
    "gloss": "is lying around / dirt cheap / dead easy",
    "anchor": "From tirar (to throw): thrown down and LEFT there.",
    "struggle_snapshot": {
        "fails_today": 3, "fails_14d": 7,
        "failed_sentences": ["Tu abrigo está tirado en el suelo."],
    },
}

_SENSES = [
    {"label": "en el suelo", "gloss": "lying around, abandoned",
     "example_tl": "Tu abrigo está tirado en el suelo.",
     "example_en": "Your coat is lying on the floor.", "ord": 1},
    {"label": "baratísimo", "gloss": "dirt cheap",
     "example_tl": "¿Solo un euro? ¡Está tirado!",
     "example_en": "Only one euro? That's a steal!", "ord": 2},
]


def test_taxonomy_has_the_commission_formats_and_no_video():
    assert set(rescue.ALL_FORMATS) == {
        "comic", "contrast", "polysemy_map", "anatomy", "poster", "glyph",
        "svg", "sentence_audio"}
    assert set(rescue.IMAGE_FORMATS).isdisjoint(rescue.MANUAL_FORMATS)
    # No video format, ever (round-1 verdict). The prose may MENTION the
    # verdict; no key or template may offer it.
    assert not any("video" in fmt for fmt in rescue.ALL_FORMATS)
    for spec in rescue.FORMATS.values():
        assert "video" not in (spec["template"] or "").lower()


def test_image_formats_have_templates_and_manual_ones_do_not():
    for fmt in rescue.IMAGE_FORMATS:
        assert rescue.FORMATS[fmt]["template"]
        assert rescue.format_placeholders(fmt)
    for fmt in rescue.MANUAL_FORMATS:
        assert rescue.FORMATS[fmt]["template"] is None
        with pytest.raises(ValueError, match="authored manually"):
            rescue.fill_template(fmt, _ITEM)


def test_fill_substitutes_item_fields():
    prompt = rescue.fill_template("comic", _ITEM)
    assert "está tirado" in prompt
    assert "Spanish" in prompt
    # scene_hint prefers the failed sentence over the anchor
    assert "Tu abrigo está tirado en el suelo." in prompt
    assert "{" not in prompt  # nothing left unsubstituted


def test_fill_falls_back_to_anchor_without_failed_sentences():
    item = dict(_ITEM, struggle_snapshot=None)
    prompt = rescue.fill_template("comic", item)
    assert "thrown down and LEFT there" in prompt


def test_anatomy_template_demands_strict_letter_order():
    prompt = rescue.fill_template("anatomy", _ITEM)
    assert "LEFT TO RIGHT" in prompt
    assert "strict spelling order" in prompt


def test_polysemy_fill_needs_two_senses_and_builds_the_doors():
    with pytest.raises(ValueError, match="teach every door"):
        rescue.fill_template("polysemy_map", _ITEM, [_SENSES[0]])
    prompt = rescue.fill_template("polysemy_map", _ITEM, _SENSES)
    assert "ESTÁ TIRADO" in prompt
    assert "en el suelo" in prompt and "baratísimo" in prompt
    assert "¡Está tirado!" in prompt  # micro-example, not just the label


def test_unknown_format_is_rejected():
    with pytest.raises(ValueError, match="unknown format"):
        rescue.fill_template("video", _ITEM)


# --- polysemy approval guard ------------------------------------------------

def test_polysemy_guard_blocks_underspecified_items():
    assert rescue.polysemy_approval_error("polysemy_map", 0)
    assert rescue.polysemy_approval_error("polysemy_map", 1)
    assert rescue.polysemy_approval_error("polysemy_map", 2) is None
    assert rescue.polysemy_approval_error("comic", 0) is None


# --- struggle snapshot / senses validation ----------------------------------

def _struggle_row(**overrides) -> dict:
    base = {"lang": "es", "idiom": "está tirado", "gloss": "lying around",
            "fails_today": 3, "fails_14d": 7,
            "failed_sentences": ["Tu abrigo está tirado en el suelo."]}
    base.update(overrides)
    return base


def test_struggles_accepts_bare_list_and_items_wrapper():
    for payload in ([_struggle_row()], {"items": [_struggle_row()]}):
        rows, errors = rescue.validate_struggles(payload)
        assert not errors
        assert rows[0]["lang"] == "es"
        assert rows[0]["snapshot"]["fails_14d"] == 7


@pytest.mark.parametrize("overrides", [
    {"lang": "esp"}, {"lang": ""}, {"idiom": "  "},
    {"fails_today": -1}, {"fails_14d": "7"},
    {"failed_sentences": "not a list"}, {"failed_sentences": [""]},
])
def test_struggles_rejects_bad_rows(overrides):
    rows, errors = rescue.validate_struggles([_struggle_row(**overrides)])
    assert errors and not rows


def test_struggles_rejects_empty_and_non_list():
    assert rescue.validate_struggles([])[1]
    assert rescue.validate_struggles({"nope": 1})[1]


def test_senses_validation_requires_every_door_taught():
    rows, errors = rescue.validate_senses(
        [{k: v for k, v in s.items() if k != "ord"} for s in _SENSES])
    assert not errors
    assert [r["ord"] for r in rows] == [1, 2]
    for missing in ("label", "gloss", "example_tl", "example_en"):
        bad = {k: v for k, v in _SENSES[0].items() if k != "ord"}
        bad[missing] = "  "
        rows, errors = rescue.validate_senses([bad])
        assert errors and not rows


# --- schema round-trip (ephemeral Postgres) ----------------------------------

_SCHEMA = Path(__file__).resolve().parent.parent / "db" / "schema.sql"

pg_available = shutil.which("initdb") and shutil.which("pg_ctl")


@pytest.fixture(scope="module")
def pg_dsn(tmp_path_factory):
    if not pg_available:
        pytest.skip("postgres binaries not installed")
    import tempfile

    root = tmp_path_factory.mktemp("pg")
    data = root / "data"
    # The socket dir must be SHORT (kernel caps unix socket paths at ~107
    # bytes; pytest tmp paths can blow past it), so it lives directly
    # under /tmp like postgres's own default.
    sock = Path(tempfile.mkdtemp(prefix="idiomatic_pgtest_"))
    subprocess.run(
        ["initdb", "-D", str(data), "-U", "postgres", "-A", "trust",
         "--no-sync"],
        check=True, capture_output=True)
    # NOT capture_output: the daemonized postgres inherits the pipe and
    # subprocess.run would block on EOF forever after pg_ctl exits.
    subprocess.run(
        ["pg_ctl", "start", "-D", str(data), "-w", "-l", str(root / "pg.log"),
         "-o", f"-k {sock} -p 54329 -c listen_addresses='' -F"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        yield {"host": str(sock), "port": 54329, "user": "postgres",
               "database": "postgres"}
    finally:
        subprocess.run(["pg_ctl", "stop", "-D", str(data), "-m", "immediate"],
                       check=False, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        shutil.rmtree(sock, ignore_errors=True)


def test_schema_round_trip(pg_dsn):
    import asyncpg

    async def run() -> None:
        conn = await asyncpg.connect(**pg_dsn)
        try:
            sql = _SCHEMA.read_text(encoding="utf-8")
            await conn.execute(sql)
            await conn.execute(sql)  # idempotent — the boot migration re-runs

            item_id = await conn.fetchval(
                """INSERT INTO rescue_items (lang, idiom, gloss,
                       struggle_snapshot)
                   VALUES ('es', 'está tirado', 'lying around',
                           '{"fails_today": 3}'::jsonb)
                   RETURNING id""")
            # (lang, idiom) unique → the struggles upload upserts
            with pytest.raises(asyncpg.UniqueViolationError):
                await conn.execute(
                    "INSERT INTO rescue_items (lang, idiom) "
                    "VALUES ('es', 'está tirado')")
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    "INSERT INTO rescue_items (lang, idiom, strike) "
                    "VALUES ('es', 'otra', 5)")
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    "INSERT INTO rescue_assets (item_id, format) "
                    "VALUES ($1, 'video')", item_id)

            asset_id = await conn.fetchval(
                """INSERT INTO rescue_assets (item_id, format, provider,
                       model, prompt, file_path, mime, cost_usd)
                   VALUES ($1, 'glyph', 'nano-banana',
                           'gemini-3.1-flash-image', 'p', '1/g.png',
                           'image/png', 0.067)
                   RETURNING id""", item_id)
            await conn.execute(
                "UPDATE rescue_items SET glyph_asset_id = $2 WHERE id = $1",
                item_id, asset_id)
            await conn.execute(
                """INSERT INTO rescue_senses (item_id, label, gloss,
                       example_tl, example_en, ord)
                   VALUES ($1, 'en el suelo', 'abandoned', 'tl', 'en', 1)""",
                item_id)
            ledger_id = await conn.fetchval(
                """INSERT INTO gen_ledger (provider, model, kind, units,
                       unit_kind, cost_usd, item_id, asset_id)
                   VALUES ('nano-banana', 'gemini-3.1-flash-image', 'image',
                           1, 'image', 0.067, $1, $2)
                   RETURNING id""", item_id, asset_id)

            row = await conn.fetchrow(
                "SELECT * FROM rescue_items WHERE id = $1", item_id)
            assert row["glyph_asset_id"] == asset_id
            assert row["status"] == "candidate" and row["strike"] == 1

            # Deleting the asset keeps the ledger row (SET NULL) and
            # clears the glyph pointer.
            await conn.execute(
                "DELETE FROM rescue_assets WHERE id = $1", asset_id)
            assert await conn.fetchval(
                "SELECT asset_id FROM gen_ledger WHERE id = $1",
                ledger_id) is None
            assert await conn.fetchval(
                "SELECT glyph_asset_id FROM rescue_items WHERE id = $1",
                item_id) is None
            # Deleting the item cascades senses but keeps the spend.
            await conn.execute(
                "DELETE FROM rescue_items WHERE id = $1", item_id)
            assert await conn.fetchval(
                "SELECT COUNT(*) FROM rescue_senses") == 0
            assert float(await conn.fetchval(
                "SELECT SUM(cost_usd) FROM gen_ledger")) == pytest.approx(0.067)
        finally:
            await conn.close()

    asyncio.run(run())


def test_kv_claim_interval_single_winner(pg_dsn):
    """The autopilot's concurrency guard: exactly one of N overlapping
    claimants wins the interval slot (the double-spend fix)."""
    import time

    import asyncpg

    from idiomatic import db as idb

    async def run() -> None:
        pool = await asyncpg.create_pool(**pg_dsn, min_size=2, max_size=6)
        orig_get_pool = idb.get_pool

        async def fake_get_pool():
            return pool

        idb.get_pool = fake_get_pool
        try:
            await pool.execute(_SCHEMA.read_text(encoding="utf-8"))
            # Fresh key: first claim wins, immediate second loses.
            assert await idb.kv_claim_interval("test:claim", 3600) is True
            assert await idb.kv_claim_interval("test:claim", 3600) is False
            # Stale stamp: claimable again.
            await pool.execute(
                "UPDATE kv_store SET value = $1 WHERE key = 'test:claim'",
                str(int(time.time()) - 7200))
            assert await idb.kv_claim_interval("test:claim", 3600) is True
            # Garbled legacy value never wedges the slot.
            await pool.execute(
                "UPDATE kv_store SET value = 'not-a-number' "
                "WHERE key = 'test:claim'")
            assert await idb.kv_claim_interval("test:claim", 3600) is True
            # Concurrent burst on a fresh key: exactly one winner.
            results = await asyncio.gather(
                *[idb.kv_claim_interval("test:burst", 3600)
                  for _ in range(8)])
            assert sum(results) == 1
        finally:
            idb.get_pool = orig_get_pool
            await pool.close()

    asyncio.run(run())
