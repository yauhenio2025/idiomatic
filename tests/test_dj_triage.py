"""DJ-C2 triage: evidence loader, seed-preservation, projection, endpoints."""

from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path

import httpx
import pytest

from idiomatic import db
from idiomatic.dj_triage import (
    EVIDENCE_PATH,
    TriageEvidenceError,
    load_evidence,
    project_languages,
)


# ---- synthetic evidence helpers --------------------------------------------

def _subtree(**overrides) -> dict:
    row = {
        "subtree": "IT Italian::8 Pimsleur::Level 3",
        "language": "IT Italian",
        "scope_kind": "first_level_subdeck",
        "parent_subtree": "IT Italian::8 Pimsleur",
        "overlapping_evidence_view": True,
        "card_count": 1145,
        "card_state": {
            "active_cards": 1145,
            "suspended_cards": 0,
            "due_now": 985,
            "new_reservoir": 160,
        },
        "provenance": {"dominant": "batch-imported"},
        "study_depth": {
            "reps": 1864,
            "distinct_studied_cards": 985,
            "last_touch_date": "2026-05-17",
            "recent_reps": 0,
        },
        "difficulty_signal": {
            "easy_rate_pct": 78.2,
            "again_rate_pct": 8.1,
            "median_ivl_mature_days": 48.0,
        },
        "proposal": {
            "disposition": "sample-hardest",
            "sample_n": 50,
            "rationale": "keep 50 hardest active",
        },
        "due_load_projection": {
            "due_minutes_before": 92.9,
            "due_cards_before": 985,
            "due_minutes_after_if_this_row_applied": 4.72,
            "due_cards_after_if_this_row_applied": 50,
        },
        "rationale": "keep 50 hardest active",
    }
    row.update(overrides)
    return row


def _evidence(subtrees: list[dict], applied: list[str] | None = None) -> dict:
    if applied is None:
        applied = [row["subtree"] for row in subtrees]
    return {
        "report": {"id": "DJ-C2"},
        "source": {"as_of_local": "2026-08-09T23:59:59+08:00"},
        "methods": {},
        "planning_constants": {},
        "language_projections": [
            {
                "language": "IT Italian",
                "due_cards_by_applied_scope": {s: 1 for s in applied},
            }
        ],
        "subtrees": subtrees,
    }


def _write(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "triage_evidence.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ---- loader ----------------------------------------------------------------

def test_loader_flattens_committed_census():
    meta, rows = load_evidence()
    assert len(rows) == 178
    by_subtree = {row["subtree"]: row for row in rows}
    level3 = by_subtree["IT Italian::8 Pimsleur::Level 3"]
    assert level3["proposal_disposition"] == "sample-hardest"
    assert level3["sample_n"] == 50
    assert level3["lane"] == "8 Pimsleur"
    assert level3["applied_scope"] is True
    assert level3["parent_subtree"] == "IT Italian::8 Pimsleur"
    # per-level Pimsleur rows exist (owner steer 2026-08-09)
    pimsleur_levels = [s for s in by_subtree if "8 Pimsleur::Level" in s]
    assert len(pimsleur_levels) >= 15
    # dormant summaries ride along but are never applied scopes
    dormant = [row for row in rows if row["scope_kind"] == "dormant_summary"]
    assert dormant and not any(row["applied_scope"] for row in dormant)
    assert all(row["source_as_of"] == meta["source"]["as_of_local"] for row in rows)


@pytest.mark.parametrize(
    "mutate,message",
    [
        (lambda p: p["subtrees"].append(copy.deepcopy(p["subtrees"][0])),
         "duplicate subtree"),
        (lambda p: p["subtrees"][0]["proposal"].__setitem__("disposition", "delete"),
         "invalid proposed disposition"),
        (lambda p: p["subtrees"][0].__setitem__("scope_kind", "galaxy"),
         "invalid scope_kind"),
        (lambda p: p["language_projections"][0]
         ["due_cards_by_applied_scope"].__setitem__("Ghost::Lane", 3),
         "not an emitted subtree"),
        (lambda p: p.__setitem__("subtrees", []), "nonempty subtrees"),
        (lambda p: p["source"].pop("as_of_local"), "as_of_local"),
    ],
)
def test_loader_rejects_unsafe_payloads(tmp_path: Path, mutate, message):
    payload = _evidence([_subtree()])
    mutate(payload)
    with pytest.raises(TriageEvidenceError, match=message):
        load_evidence(_write(tmp_path, payload))


# ---- seed ------------------------------------------------------------------

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
        self.captured["sql"] = sql
        self.captured["values"] = values


class _Pool:
    def __init__(self, captured: dict, count: int = 0):
        self.captured = captured
        self.count = count

    def acquire(self):
        return _Conn(self.captured)

    async def fetchval(self, _sql):
        return self.count


def _fake_pool(monkeypatch, captured: dict, count: int = 0) -> None:
    async def fake_pool():
        return _Pool(captured, count)

    monkeypatch.setattr(db, "get_pool", fake_pool)


def test_seed_upsert_never_overwrites_owner_columns(monkeypatch):
    captured: dict = {}
    _fake_pool(monkeypatch, captured)
    _meta, rows = load_evidence()  # the committed artifact
    asyncio.run(db.seed_dj_triage(rows[:3]))
    update_clause = captured["sql"].split("DO UPDATE SET", 1)[1]
    assert "owner_verdict" not in update_clause
    assert "owner_note" not in update_clause
    assert "verdicted_at" not in update_clause
    assert captured["values"][0][0] == rows[0]["subtree"]
    assert len(captured["values"]) == 3


def test_boot_seed_only_when_table_is_empty(monkeypatch):
    _meta, rows = load_evidence()
    # non-empty table: boot must not reseed
    captured: dict = {}
    _fake_pool(monkeypatch, captured, count=178)
    assert asyncio.run(db.seed_dj_triage_if_empty(rows)) is False
    assert "sql" not in captured
    # empty table: boot seeds every committed row
    captured = {}
    _fake_pool(monkeypatch, captured, count=0)
    assert asyncio.run(db.seed_dj_triage_if_empty(rows)) is True
    assert len(captured["values"]) == 178


# ---- projection ------------------------------------------------------------

def _census_projections() -> dict[str, dict]:
    raw = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    return {p["language"]: p for p in raw["language_projections"]}


def test_projection_unverdicted_equals_census_before():
    _meta, rows = load_evidence()
    expected = _census_projections()
    projections = {p["language"]: p for p in project_languages(rows)}
    assert set(projections) == set(expected)
    for language, census in expected.items():
        ours = projections[language]
        assert ours["before_minutes"] == pytest.approx(
            census["before_minutes"], abs=0.01)
        assert ours["current_minutes"] == pytest.approx(
            census["before_minutes"], abs=0.01)
        assert ours["before_due_cards"] == census["before_due_cards"]
        # the census "if all proposals accepted" numbers are reproduced
        assert ours["proposal_minutes"] == pytest.approx(
            census["after_minutes"], abs=0.01)
        assert ours["proposal_due_cards"] == census["after_due_cards"]


def test_projection_accept_all_matches_census_after():
    _meta, rows = load_evidence()
    for row in rows:
        row["owner_verdict"] = "accept-proposal"
    expected = _census_projections()
    for projection in project_languages(rows):
        census = expected[projection["language"]]
        assert projection["current_minutes"] == pytest.approx(
            census["after_minutes"], abs=0.01)
        assert projection["current_due_cards"] == census["after_due_cards"]
        assert projection["undecided_scopes"] == 0


def test_projection_verdict_semantics():
    lane = _subtree(
        subtree="IT Italian::8 Pimsleur",
        scope_kind="lane",
        parent_subtree=None,
        due_load_projection={
            "due_minutes_before": 95.17, "due_cards_before": 1009,
            "due_minutes_after_if_this_row_applied": 4.72,
            "due_cards_after_if_this_row_applied": 50,
        },
    )
    level = _subtree()
    keep = _subtree(
        subtree="IT Italian::1 Expressions",
        scope_kind="lane",
        parent_subtree=None,
        proposal={"disposition": "keep-active", "sample_n": None,
                  "rationale": "recent study"},
        due_load_projection={
            "due_minutes_before": 79.5, "due_cards_before": 515,
            "due_minutes_after_if_this_row_applied": 79.5,
            "due_cards_after_if_this_row_applied": 515,
        },
    )

    def project(verdicts: dict[str, str | None]) -> dict:
        # applied scopes = the census's most-specific decomposition: the
        # Pimsleur LEVEL (not its overlapping lane view) + the keep lane.
        _m, flat = _load_synth(
            [lane, level, keep],
            applied=[level["subtree"], keep["subtree"]],
        )
        for row in flat:
            row["owner_verdict"] = verdicts.get(row["subtree"])
        return {p["language"]: p for p in project_languages(flat)}["IT Italian"]

    # applied scopes are the level + the keep lane (most-specific rule)
    base = project({})
    assert base["current_minutes"] == pytest.approx(92.9 + 79.5, abs=0.01)

    # suspend on the level zeroes its minutes; keep lane unchanged
    suspended = project({level["subtree"]: "suspend-reference"})
    assert suspended["current_minutes"] == pytest.approx(79.5, abs=0.01)

    # defer = undecided = unchanged (both scopes: deferred level +
    # never-verdicted keep lane)
    deferred = project({level["subtree"]: "defer"})
    assert deferred["current_minutes"] == base["current_minutes"]
    assert deferred["undecided_scopes"] == 2
    assert project({level["subtree"]: "defer",
                    keep["subtree"]: "keep-active"})["undecided_scopes"] == 1

    # accept-proposal resolves to the row's own census proposal
    accepted = project({level["subtree"]: "accept-proposal"})
    assert accepted["current_minutes"] == pytest.approx(4.72 + 79.5, abs=0.01)

    # a lane verdict cascades to its unverdicted subdeck...
    cascade = project({lane["subtree"]: "suspend-reference"})
    assert cascade["current_minutes"] == pytest.approx(79.5, abs=0.01)

    # ...but the subdeck's own verdict wins over the lane's
    override = project({lane["subtree"]: "suspend-reference",
                        level["subtree"]: "keep-active"})
    assert override["current_minutes"] == pytest.approx(92.9 + 79.5, abs=0.01)

    # owner-chosen sample-hardest on a non-sample proposal row: min(N, due)
    sampled = project({keep["subtree"]: "sample-hardest"})
    assert sampled["current_minutes"] == pytest.approx(
        92.9 + 79.5 * 50 / 515, abs=0.01)


def _load_synth(subtrees: list[dict], applied: list[str]):
    """Build flat rows from synthetic census entries via the real loader."""
    import tempfile

    payload = _evidence(subtrees, applied=applied)
    with tempfile.TemporaryDirectory() as tmp:
        return load_evidence(_write(Path(tmp), payload))


# ---- endpoints -------------------------------------------------------------

class _EndpointPool:
    def __init__(self, *, fetchrow_result=None, execute_status="UPDATE 0",
                 fetch_rows=None):
        self.fetchrow_result = fetchrow_result
        self.execute_status = execute_status
        self.fetch_rows = fetch_rows or []
        self.calls: list[tuple] = []

    async def fetchrow(self, sql, *args):
        self.calls.append(("fetchrow", sql, args))
        return self.fetchrow_result

    async def execute(self, sql, *args):
        self.calls.append(("execute", sql, args))
        return self.execute_status

    async def fetch(self, sql, *args):
        self.calls.append(("fetch", sql, args))
        return self.fetch_rows


@pytest.mark.asyncio
async def test_triage_verdict_endpoint_validates_and_updates(monkeypatch):
    from idiomatic import api

    pool = _EndpointPool(fetchrow_result={"subtree": "IT Italian::8 Pimsleur"})

    async def fake_pool():
        return pool

    monkeypatch.setattr(api.db, "get_pool", fake_pool)
    api.app.dependency_overrides[api.authed_admin] = lambda: None
    try:
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport,
                                     base_url="http://test") as client:
            ok = await client.post("/admin/triage-verdict", json={
                "subtree_id": "IT Italian::8 Pimsleur",
                "verdict": "suspend-reference",
                "note": "beneath level",
            })
            note_only = await client.post("/admin/triage-verdict", json={
                "subtree_id": "IT Italian::8 Pimsleur", "note": "examine later",
            })
            bad_verdict = await client.post("/admin/triage-verdict", json={
                "subtree_id": "IT Italian::8 Pimsleur", "verdict": "delete-all",
            })
            no_subtree = await client.post("/admin/triage-verdict", json={
                "verdict": "keep-active",
            })
            empty = await client.post("/admin/triage-verdict", json={
                "subtree_id": "IT Italian::8 Pimsleur",
            })
            pool.fetchrow_result = None
            unknown = await client.post("/admin/triage-verdict", json={
                "subtree_id": "No Such::Lane", "verdict": "keep-active",
            })
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)
    assert ok.status_code == 200 and ok.json()["ok"] is True
    assert note_only.status_code == 200
    assert bad_verdict.status_code == 400
    assert no_subtree.status_code == 400
    assert empty.status_code == 400
    assert unknown.status_code == 404
    # the verdict update wrote verdict + note and targeted the subtree
    _kind, sql, args = pool.calls[0]
    assert "owner_verdict" in sql and "verdicted_at = NOW()" in sql
    assert args == ("suspend-reference", "beneath level", "IT Italian::8 Pimsleur")
    # the note-only update never touches the verdict columns
    _kind, sql, args = pool.calls[1]
    assert "owner_verdict" not in sql and "verdicted_at" not in sql
    assert args == ("examine later", "IT Italian::8 Pimsleur")


@pytest.mark.asyncio
async def test_triage_bulk_endpoint_accept_all_unverdicted(monkeypatch):
    from idiomatic import api

    pool = _EndpointPool(execute_status="UPDATE 154")

    async def fake_pool():
        return pool

    monkeypatch.setattr(api.db, "get_pool", fake_pool)
    api.app.dependency_overrides[api.authed_admin] = lambda: None
    try:
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport,
                                     base_url="http://test") as client:
            ok = await client.post("/admin/triage-verdict-bulk", json={
                "verdict": "accept-proposal", "scope": "all-unverdicted",
            })
            bad_scope = await client.post("/admin/triage-verdict-bulk", json={
                "verdict": "accept-proposal", "scope": "everything",
            })
            bad_verdict = await client.post("/admin/triage-verdict-bulk", json={
                "verdict": "purge", "scope": "all-unverdicted",
            })
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)
    assert ok.status_code == 200 and ok.json()["updated"] == 154
    assert bad_scope.status_code == 400
    assert bad_verdict.status_code == 400
    _kind, sql, args = pool.calls[0]
    assert "WHERE owner_verdict IS NULL" in sql
    assert args == ("accept-proposal",)


@pytest.mark.asyncio
async def test_triage_console_endpoint_reads_rows_and_projects(monkeypatch):
    from idiomatic import api, ui_api

    _meta, rows = load_evidence()
    for row in rows:
        row.update(owner_verdict=None, owner_note=None, verdicted_at=None,
                   seeded_at=None)
        row.pop("evidence")
    pool = _EndpointPool(fetch_rows=rows)

    async def fake_pool():
        return pool

    monkeypatch.setattr(ui_api.db, "get_pool", fake_pool)
    api.app.dependency_overrides[ui_api.authed_ui] = lambda: None
    try:
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport,
                                     base_url="http://test") as client:
            response = await client.get("/ui/api/triage")
            method_not_allowed = await client.post("/ui/api/triage")
    finally:
        api.app.dependency_overrides.pop(ui_api.authed_ui, None)
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total"] == 178
    assert body["summary"]["remaining"] == 178
    assert body["summary"]["verdicted"] == 0
    assert len(body["summary"]["languages"]) == 6
    assert body["meta"]["applies_dispositions"] is False
    assert "executor lane" in body["meta"]["executor_note"]
    # the payload never ships the full evidence blob
    assert "evidence" not in body["rows"][0]
    assert method_not_allowed.status_code == 405


# ---- schema ----------------------------------------------------------------

def test_schema_declares_checked_dj_triage_table():
    schema = (Path(__file__).parents[1] / "db" / "schema.sql").read_text(
        encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS dj_triage" in schema
    assert ("'accept-proposal', 'keep-active', 'suspend-reference', "
            "'sample-hardest', 'defer'") in schema
