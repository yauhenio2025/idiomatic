"""LingQ dormant-value console: seed rules, verdicts, auth, and read side."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from idiomatic import lingq_console


class _Conn:
    def __init__(self, captured: dict):
        self.captured = captured

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    def transaction(self):
        return self

    async def executemany(self, sql, values):
        self.captured["seed_sql"] = sql
        self.captured["seed_values"] = values


class _Pool:
    def __init__(
        self,
        captured: dict,
        *,
        count: int = 0,
        fetchrow_result=None,
        fetch_rows=None,
    ):
        self.captured = captured
        self.count = count
        self.fetchrow_result = fetchrow_result
        self.fetch_rows = fetch_rows or []

    def acquire(self):
        return _Conn(self.captured)

    async def fetchval(self, sql, *args):
        self.captured.setdefault("calls", []).append(("fetchval", sql, args))
        return self.count

    async def fetchrow(self, sql, *args):
        self.captured.setdefault("updates", []).append((sql, args))
        return self.fetchrow_result

    async def fetch(self, sql, *args):
        self.captured.setdefault("calls", []).append(("fetch", sql, args))
        return self.fetch_rows


def _fake_pool(
    monkeypatch,
    captured: dict,
    *,
    count: int = 0,
    fetchrow_result=None,
    fetch_rows=None,
) -> None:
    pool = _Pool(
        captured,
        count=count,
        fetchrow_result=fetchrow_result,
        fetch_rows=fetch_rows,
    )

    async def get_pool():
        return pool

    monkeypatch.setattr(lingq_console.db, "get_pool", get_pool)


def test_definitions_are_seven_ranked_aggregate_concepts():
    assert len(lingq_console.CONCEPTS) == 7
    assert lingq_console.CONCEPT_KEYS == {
        "c1_second_encounter",
        "c2_own_words_weaver",
        "c3_reading_relics",
        "c4_morph_slot",
        "c5_polyglot_mirror",
        "c6_frontier_podcast",
        "c7_picture_idiom",
    }
    assert [row["proposal_rank"] for row in lingq_console.CONCEPTS] == list(
        range(1, 8)
    )
    recommended = [row for row in lingq_console.CONCEPTS if row["recommended"]]
    assert [row["concept_key"] for row in recommended] == ["c1_second_encounter"]
    assert all(row["pitch"] and row["sizing"] for row in lingq_console.CONCEPTS)


def test_seed_reseeds_payload_without_overwriting_owner_decisions(monkeypatch):
    captured: dict = {}
    _fake_pool(monkeypatch, captured)

    asyncio.run(lingq_console.seed_lingq_verdicts())

    update_clause = captured["seed_sql"].split("DO UPDATE SET", 1)[1]
    assert "owner_verdict" not in update_clause
    assert "owner_note" not in update_clause
    assert "verdicted_at" not in update_clause
    assert len(captured["seed_values"]) == 7
    first_key, first_json = captured["seed_values"][0]
    assert first_key == "c1_second_encounter"
    assert json.loads(first_json)["recommended"] is True
    assert "concept_key" not in json.loads(first_json)


def test_boot_seed_is_empty_only_and_idempotent(monkeypatch):
    captured: dict = {}
    _fake_pool(monkeypatch, captured, count=7)
    assert asyncio.run(lingq_console.seed_lingq_verdicts_if_empty()) is False
    assert "seed_sql" not in captured

    captured = {}
    _fake_pool(monkeypatch, captured, count=0)
    assert asyncio.run(lingq_console.seed_lingq_verdicts_if_empty()) is True
    assert len(captured["seed_values"]) == 7


def test_unknown_key_and_verdict_are_rejected_before_sql(monkeypatch):
    async def forbidden_pool():
        raise AssertionError("invalid decisions must not reach the database")

    monkeypatch.setattr(lingq_console.db, "get_pool", forbidden_pool)
    with pytest.raises(ValueError, match="unknown concept_key"):
        asyncio.run(
            lingq_console.save_lingq_verdict(
                "c99_missing", verdict="greenlight-pilot"
            )
        )
    with pytest.raises(ValueError, match="verdict must be one of"):
        asyncio.run(
            lingq_console.save_lingq_verdict(
                "c1_second_encounter", verdict="build-it-now"
            )
        )


def test_note_only_save_never_touches_verdict_or_timestamp(monkeypatch):
    captured: dict = {}
    _fake_pool(
        monkeypatch,
        captured,
        fetchrow_result={"concept_key": "c1_second_encounter"},
    )

    result = asyncio.run(
        lingq_console.save_lingq_verdict(
            "c1_second_encounter", note="Start with French"
        )
    )

    assert result == {"ok": True, "concept_key": "c1_second_encounter"}
    sql, args = captured["updates"][0]
    assert "owner_note" in sql
    assert "owner_verdict" not in sql
    assert "verdicted_at" not in sql
    assert args == ("Start with French", "c1_second_encounter")


@pytest.mark.asyncio
async def test_lingq_verdict_endpoint_validates_and_updates(monkeypatch):
    from idiomatic import api

    captured: dict = {}
    _fake_pool(
        monkeypatch,
        captured,
        fetchrow_result={"concept_key": "c1_second_encounter"},
    )

    async def allow_admin():
        return None

    api.app.dependency_overrides[api.authed_admin] = allow_admin
    try:
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            ok = await client.post(
                "/admin/lingq-verdict",
                json={
                    "concept_key": "c1_second_encounter",
                    "verdict": "greenlight-pilot",
                    "note": "FR first",
                },
            )
            note_only = await client.post(
                "/admin/lingq-verdict",
                json={"concept_key": "c1_second_encounter", "note": "60 cards"},
            )
            bad_verdict = await client.post(
                "/admin/lingq-verdict",
                json={
                    "concept_key": "c1_second_encounter",
                    "verdict": "ship-everything",
                },
            )
            unknown = await client.post(
                "/admin/lingq-verdict",
                json={"concept_key": "c8_unknown", "verdict": "defer"},
            )
            no_key = await client.post(
                "/admin/lingq-verdict", json={"verdict": "defer"}
            )
            empty = await client.post(
                "/admin/lingq-verdict", json={"concept_key": "c1_second_encounter"}
            )
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)

    assert ok.status_code == 200 and ok.json()["ok"] is True
    assert note_only.status_code == 200
    assert bad_verdict.status_code == 400
    assert unknown.status_code == 400
    assert no_key.status_code == 400
    assert empty.status_code == 400
    first_sql, first_args = captured["updates"][0]
    assert "owner_verdict" in first_sql and "verdicted_at = NOW()" in first_sql
    assert first_args == ("greenlight-pilot", "FR first", "c1_second_encounter")
    second_sql, second_args = captured["updates"][1]
    assert "owner_verdict" not in second_sql and "verdicted_at" not in second_sql
    assert second_args == ("60 cards", "c1_second_encounter")


@pytest.mark.asyncio
async def test_lingq_read_endpoint_returns_rows_and_progress(monkeypatch):
    from idiomatic import api, ui_api

    rows = [
        {
            **concept,
            "owner_verdict": "greenlight-pilot" if index == 0 else None,
            "owner_note": None,
            "verdicted_at": None,
            "seeded_at": None,
        }
        for index, concept in enumerate(lingq_console.CONCEPTS)
    ]

    async def list_rows():
        return rows

    monkeypatch.setattr(lingq_console, "list_lingq_verdicts", list_rows)

    async def allow_ui():
        return None

    api.app.dependency_overrides[ui_api.authed_ui] = allow_ui
    try:
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/ui/api/lingq")
            method_not_allowed = await client.post("/ui/api/lingq")
    finally:
        api.app.dependency_overrides.pop(ui_api.authed_ui, None)

    assert response.status_code == 200
    body = response.json()
    assert len(body["rows"]) == 7
    assert body["summary"] == {
        "total": 7,
        "verdicted": 1,
        "remaining": 6,
        "verdict_counts": {"greenlight-pilot": 1, "unverdicted": 6},
    }
    assert body["meta"]["applies_changes"] is False
    assert "nothing automatically" in body["meta"]["coordinator_note"]
    assert method_not_allowed.status_code == 405


@pytest.mark.asyncio
async def test_lingq_endpoints_require_admin_auth(monkeypatch):
    from idiomatic import api, ui_api

    monkeypatch.setattr(
        api, "get_settings", lambda: SimpleNamespace(admin_token="test-secret")
    )
    monkeypatch.setattr(
        ui_api, "get_settings", lambda: SimpleNamespace(admin_token="test-secret")
    )
    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        write = await client.post(
            "/admin/lingq-verdict",
            json={"concept_key": "c1_second_encounter", "verdict": "defer"},
        )
        read = await client.get("/ui/api/lingq")

    assert write.status_code == 401
    assert read.status_code == 401


def test_schema_declares_checked_lingq_verdict_table():
    schema = (Path(__file__).parents[1] / "db" / "schema.sql").read_text(
        encoding="utf-8"
    )
    assert "CREATE TABLE IF NOT EXISTS lingq_verdicts" in schema
    assert "concept_key    TEXT PRIMARY KEY" in schema
    assert "payload        JSONB NOT NULL" in schema
    assert (
        "'greenlight-pilot', 'interested-later', 'not-for-me', 'defer'"
        in schema
    )
