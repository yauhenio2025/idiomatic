"""Course-unit APKG upload → add-on delivery entry point.

Endpoint-shape tests in the house style (ASGI transport, admin-dependency
override, db helper monkeypatched — no live Postgres)."""
from __future__ import annotations

import asyncio
import zipfile
from pathlib import Path

import httpx

from idiomatic import api


def _fake_apkg_bytes() -> bytes:
    import io

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("collection.anki21", b"x" * 2048)
    return buf.getvalue()


def _post(path: str, params: dict, content: bytes) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test",
        ) as client:
            return await client.post(path, params=params, content=content)

    return asyncio.run(request())


def _override_admin_and_settings(monkeypatch, tmp_path: Path):
    from types import SimpleNamespace

    api.app.dependency_overrides[api.authed_admin] = lambda: None
    monkeypatch.setattr(
        api, "get_settings", lambda: SimpleNamespace(data_dir=tmp_path),
    )


def _cleanup_override():
    api.app.dependency_overrides.pop(api.authed_admin, None)


def test_upload_happy_path_writes_file_and_upserts(monkeypatch, tmp_path):
    calls: list[dict] = []

    async def fake_upsert(**kwargs):
        calls.append(kwargs)
        return 4242

    _override_admin_and_settings(monkeypatch, tmp_path)
    monkeypatch.setattr(api.db, "upsert_course_apkg", fake_upsert)
    body = _fake_apkg_bytes()
    try:
        resp = _post(
            "/admin/course-apkg-upload",
            {"lang": "de", "unit": "valenz", "notes": 110},
            body,
        )
    finally:
        _cleanup_override()

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["apkg_id"] == 4242
    assert data["kind"] == "course_valenz"
    stored = tmp_path / "apkgs" / "de" / "course_valenz.apkg"
    assert stored.read_bytes() == body
    assert not stored.with_name(stored.name + ".tmp").exists()
    assert calls == [{
        "lang": "de", "kind": "course_valenz",
        "filename": "apkgs/de/course_valenz.apkg",
        "size_bytes": len(body), "n_idioms": 110,
    }]


def test_upload_rejects_unknown_unit_and_lang(monkeypatch, tmp_path):
    _override_admin_and_settings(monkeypatch, tmp_path)
    body = _fake_apkg_bytes()
    try:
        bad_unit = _post(
            "/admin/course-apkg-upload",
            {"lang": "de", "unit": "nope"}, body,
        )
        bad_lang = _post(
            "/admin/course-apkg-upload",
            {"lang": "xx", "unit": "valenz"}, body,
        )
    finally:
        _cleanup_override()

    assert bad_unit.status_code == 400
    assert "unknown DE course unit" in bad_unit.text
    assert bad_lang.status_code == 400


def test_upload_rejects_non_zip_body(monkeypatch, tmp_path):
    _override_admin_and_settings(monkeypatch, tmp_path)
    try:
        resp = _post(
            "/admin/course-apkg-upload",
            {"lang": "de", "unit": "valenz"}, b"not a zip" * 200,
        )
    finally:
        _cleanup_override()

    assert resp.status_code == 400
    assert ".apkg" in resp.text


def test_upload_requires_admin_auth(monkeypatch, tmp_path):
    from types import SimpleNamespace

    monkeypatch.setattr(
        api, "get_settings",
        lambda: SimpleNamespace(data_dir=tmp_path, admin_token=None),
    )
    resp = _post(
        "/admin/course-apkg-upload",
        {"lang": "de", "unit": "valenz"}, _fake_apkg_bytes(),
    )
    assert resp.status_code in (401, 403, 503)