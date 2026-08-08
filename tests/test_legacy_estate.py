"""Legacy-estate manifest, seed, and read-only dashboard tests."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from idiomatic import db
from idiomatic.legacy_estate import LegacyEstateManifestError, load_manifest


def _row(**overrides) -> dict:
    row = {
        "source_deck_id": 42,
        "deck_path": "EXCERCISES::ES::CONNECTING",
        "parent_path": "EXCERCISES::ES",
        "depth": 2,
        "top_level": "EXCERCISES",
        "lang": "es",
        "direct_notes": 10,
        "direct_cards": 10,
        "direct_mature": 1,
        "direct_reps": 20,
        "direct_reviews": 19,
        "direct_audio_notes": 0,
        "direct_sound_tags": 0,
        "direct_last_review": "2024-03-01T00:00:00+00:00",
        "subtree_notes": 10,
        "subtree_cards": 10,
        "subtree_mature": 1,
        "subtree_reps": 20,
        "subtree_reviews": 19,
        "subtree_audio_notes": 0,
        "subtree_sound_tags": 0,
        "subtree_last_review": "2024-03-01T00:00:00+00:00",
        "note_models": [{"id": 1, "name": "_Basic"}],
        "quality_flags": [{"code": "duplicate_front", "count": 2}],
        "overlap": [{"kind": "exercises2", "status": "shipped"}],
        "proposed_verdict": "already-covered",
        "proposal_reason": "Wave 1 shipped.",
    }
    row.update(overrides)
    return row


def _manifest(rows: list[dict]) -> dict:
    return {
        "snapshot": {
            "source_sha256": "a" * 64,
            "audited_at": "2026-08-08T03:00:00+00:00",
        },
        "totals": {"notes": 10, "cards": 10},
        "models": [],
        "rows": rows,
    }


def test_manifest_loader_validates_identity_and_rows(tmp_path: Path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_manifest([_row()])), encoding="utf-8")
    snapshot, rows = load_manifest(path)
    assert snapshot["source_sha256"] == "a" * 64
    assert snapshot["audited_at_parsed"].tzinfo is not None
    assert rows[0]["deck_path"] == "EXCERCISES::ES::CONNECTING"


@pytest.mark.parametrize(
    "payload,message",
    [
        (_manifest([_row(), _row()]), "duplicate deck_path"),
        (_manifest([_row(proposed_verdict="maybe")]), "invalid proposed_verdict"),
        (
            {**_manifest([_row()]), "snapshot": {"source_sha256": "bad", "audited_at": "x"}},
            "source_sha256",
        ),
    ],
)
def test_manifest_loader_rejects_unsafe_payloads(tmp_path: Path, payload: dict, message: str):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(LegacyEstateManifestError, match=message):
        load_manifest(path)


def test_seed_is_idempotent_and_never_overwrites_owner_columns(monkeypatch):
    captured: dict = {}

    class Context:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        def transaction(self):
            return self

        async def executemany(self, sql, values):
            captured["sql"] = sql
            captured["values"] = values

    class Pool:
        def acquire(self):
            return Context()

    async def fake_pool():
        return Pool()

    monkeypatch.setattr(db, "get_pool", fake_pool)
    asyncio.run(
        db.seed_legacy_estate(
            [_row()],
            source_sha256="a" * 64,
            audited_at=datetime(2026, 8, 8, tzinfo=UTC),
        )
    )
    update_clause = captured["sql"].split("DO UPDATE SET", 1)[1]
    assert "owner_verdict" not in update_clause
    assert "owner_note" not in update_clause
    assert captured["values"][0][0] == "EXCERCISES::ES::CONNECTING"
    assert captured["values"][0][13].tzinfo is not None


@pytest.mark.asyncio
async def test_legacy_dashboard_is_read_only_and_prefers_owner_verdict(monkeypatch):
    from idiomatic import api, ui_api

    now = datetime(2026, 8, 8, tzinfo=UTC)
    record = {
        **_row(),
        "owner_verdict": "partial",
        "owner_note": "keep only the studied slice",
        "verdict": "partial",
        "verdict_source": "owner",
        "source_sha256": "a" * 64,
        "audited_at": now,
        "direct_last_review": now,
        "subtree_last_review": now,
    }

    class Pool:
        async def fetch(self, _sql):
            return [record]

    async def fake_pool():
        return Pool()

    monkeypatch.setattr(ui_api.db, "get_pool", fake_pool)
    api.app.dependency_overrides[ui_api.authed_ui] = lambda: None
    try:
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ui/api/legacy")
            method_not_allowed = await client.post("/ui/api/legacy")
    finally:
        api.app.dependency_overrides.pop(ui_api.authed_ui, None)
    assert response.status_code == 200
    body = response.json()
    assert body["rows"][0]["verdict"] == "partial"
    assert body["rows"][0]["verdict_source"] == "owner"
    assert body["totals"]["owner_pending"] == 0
    assert method_not_allowed.status_code == 405


def test_schema_declares_checked_legacy_estate_table():
    schema = (Path(__file__).parents[1] / "db" / "schema.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS legacy_estate" in schema
    assert "owner_verdict IN ('import', 'partial', 'skip', 'already-covered')" in schema

