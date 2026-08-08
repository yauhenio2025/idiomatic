"""Versioned Part-C queue, upload and strict local rebuild tests."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sqlite3
import uuid
import zipfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import asyncpg

from idiomatic import api, db, gemini, local_tts
from idiomatic.grammar import exercises2 as x2
from idiomatic.pipeline import pool as pool_mod


def _mp3(payload: bytes = b"qwen") -> bytes:
    # Empty ID3v2.4 tag followed by a valid MPEG-1 Layer III frame header.
    head = b"ID3\x04\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x64"
    return head + payload + b"\x00" * (local_tts.MIN_MP3_BYTES + 100)


def test_pilot_selection_is_frozen_30_notes_and_60_jobs():
    notes = local_tts.pilot_notes()
    assert len(notes) == 30
    for lang, topics in local_tts.PILOT_NOTE_IDS.items():
        chosen = [note for note in notes if note.lang == lang]
        assert len(chosen) == 6
        for topic, expected_ids in topics.items():
            assert tuple(
                note.item_id for note in chosen if note.topic == topic
            ) == expected_ids

    rows = local_tts.exercises2_job_rows(
        notes, is_pilot=True, include_en_prompt=False)
    assert len(rows) == 60
    assert len({row["source_key"] for row in rows}) == 60
    assert {row["clip_kind"] for row in rows} == {"answer", "example"}
    assert all(row["is_pilot"] and row["contract_version"] == 1 for row in rows)
    with_en = local_tts.exercises2_job_rows(notes, is_pilot=True)
    assert len(with_en) == 90
    assert {r["lang"] for r in with_en if r["clip_kind"] == "prompt_en"} == {"en"}


def test_source_edit_keeps_job_identity_but_changes_hash_and_canonical_path():
    note = local_tts.pilot_notes()[0]
    original = local_tts.exercises2_job_rows([note], is_pilot=True)
    edited = replace(note, tl=note.tl + " (edited)")
    changed = local_tts.exercises2_job_rows([edited], is_pilot=True)

    assert original[0]["source_key"] == changed[0]["source_key"]
    assert original[0]["content_hash"] != changed[0]["content_hash"]
    assert original[0]["staged_path"] != changed[0]["staged_path"]
    # The example text did not change, so that sibling clip stays cached.
    assert original[1]["content_hash"] == changed[1]["content_hash"]


def test_db_seed_is_idempotent_and_sql_resets_completed_job_on_edit(monkeypatch):
    class FakeSeedPool:
        def __init__(self):
            self.state: dict[str, dict] = {}
            self.sql = ""

        async def fetchrow(self, sql, payload):
            self.sql = sql
            counts = {"inserted": 0, "reset": 0, "unchanged": 0}
            for incoming in json.loads(payload):
                old = self.state.get(incoming["source_key"])
                if old is None:
                    action = "inserted"
                    self.state[incoming["source_key"]] = {
                        **incoming, "status": "queued", "audio_sha256": None,
                    }
                elif (
                    old["content_hash"] != incoming["content_hash"]
                    or old["staged_path"] != incoming["staged_path"]
                ):
                    action = "reset"
                    self.state[incoming["source_key"]] = {
                        **incoming, "status": "queued", "audio_sha256": None,
                    }
                else:
                    action = "unchanged"
                    old["is_pilot"] = old["is_pilot"] or incoming["is_pilot"]
                counts[action] += 1
            return {"total": len(json.loads(payload)), **counts, "written": 1}

    pool = FakeSeedPool()

    async def fake_pool():
        return pool

    monkeypatch.setattr(db, "get_pool", fake_pool)
    row = local_tts.exercises2_job_rows(
        [local_tts.pilot_notes()[0]], is_pilot=True,
    )[0]
    first = asyncio.run(db.seed_local_tts_jobs([row]))
    pool.state[row["source_key"]]["status"] = "completed"
    pool.state[row["source_key"]]["audio_sha256"] = "a" * 64
    second = asyncio.run(db.seed_local_tts_jobs([row]))
    after_second_status = pool.state[row["source_key"]]["status"]
    after_second_sha = pool.state[row["source_key"]]["audio_sha256"]
    edited = dict(row)
    edited["text"] += " revised"
    edited["content_hash"] = local_tts.content_hash(edited["text"], edited["lang"])
    edited["staged_path"] = local_tts.canonical_staged_path(
        edited["source_key"], edited["lang"], edited["content_hash"],
    )
    third = asyncio.run(db.seed_local_tts_jobs([edited]))

    assert first == {"total": 1, "inserted": 1, "reset": 0, "unchanged": 0}
    assert second["unchanged"] == 1
    assert after_second_status == "completed"
    assert after_second_sha == "a" * 64
    assert pool.state[row["source_key"]]["status"] == "queued"
    assert pool.state[row["source_key"]]["audio_sha256"] is None
    assert third["reset"] == 1
    assert "ON CONFLICT (source_key) DO UPDATE" in pool.sql
    assert "content_hash IS DISTINCT FROM EXCLUDED.content_hash" in pool.sql
    assert "THEN 'queued' ELSE local_tts_jobs.status" in pool.sql
    assert "audio_sha256 = CASE WHEN" in pool.sql


def test_claim_contract_reclaims_expired_leases_with_skip_locked(monkeypatch):
    class FakeClaimPool:
        sql = ""
        args = ()

        async def fetch(self, sql, *args):
            self.sql, self.args = sql, args
            return []

    pool = FakeClaimPool()

    async def fake_pool():
        return pool

    monkeypatch.setattr(db, "get_pool", fake_pool)
    monkeypatch.setattr(db.secrets, "token_urlsafe", lambda _: "lease-token")
    result = asyncio.run(db.claim_local_tts_jobs(
        worker_id="fedora-qwen", limit=4, lease_seconds=600,
    ))
    assert result == {"lease_token": "lease-token", "jobs": []}
    assert "status = 'leased' AND lease_expires_at <= NOW()" in pool.sql
    assert "FOR UPDATE SKIP LOCKED" in pool.sql
    assert "make_interval(secs => $5)" in pool.sql
    assert pool.args == (1, 4, "lease-token", "fedora-qwen", 600)

    with pytest.raises(ValueError, match="1..16"):
        asyncio.run(db.claim_local_tts_jobs(worker_id="x", limit=17))


def test_mp3_upload_is_atomic_canonical_and_confined(tmp_path: Path):
    row = local_tts.exercises2_job_rows(
        [local_tts.pilot_notes()[0]], is_pilot=True,
    )[0]
    data = _mp3()
    path, digest = local_tts.atomic_stage_mp3(data, job=row, data_dir=tmp_path)
    assert path.read_bytes() == data
    assert digest == hashlib.sha256(data).hexdigest()
    assert path.relative_to(tmp_path / "staged_audio").as_posix() == row["staged_path"]
    assert not list(path.parent.glob(f".{path.name}.*.tmp"))

    with pytest.raises(local_tts.LocalTTSUploadError, match="valid MP3"):
        local_tts.validate_mp3(b"ID3" + b"x" * 2000)

    noncanonical = {**row, "staged_path": "../../outside.mp3"}
    with pytest.raises(local_tts.LocalTTSUploadError, match="not canonical"):
        local_tts.atomic_stage_mp3(data, job=noncanonical, data_dir=tmp_path)

    escape_data = tmp_path / "escape"
    stage_root = escape_data / "staged_audio"
    outside = tmp_path / "outside"
    stage_root.mkdir(parents=True)
    outside.mkdir()
    os.symlink(outside, stage_root / "grammar", target_is_directory=True)
    with pytest.raises(local_tts.LocalTTSUploadError, match="escapes"):
        local_tts.atomic_stage_mp3(data, job=row, data_dir=escape_data)

    root_link_data = tmp_path / "root-link"
    root_link_data.mkdir()
    os.symlink(outside, root_link_data / "staged_audio", target_is_directory=True)
    with pytest.raises(local_tts.LocalTTSUploadError, match="must not be a symlink"):
        local_tts.atomic_stage_mp3(data, job=row, data_dir=root_link_data)


def _completed_rows(tmp_path: Path, note: x2.Ex2Note) -> list[dict]:
    rows = local_tts.exercises2_job_rows([note], is_pilot=False)
    completed = []
    for index, row in enumerate(rows):
        data = _mp3(str(index).encode())
        clip = tmp_path / "staged_audio" / row["staged_path"]
        clip.parent.mkdir(parents=True, exist_ok=True)
        clip.write_bytes(data)
        completed.append({
            "id": index + 1,
            "source_key": row["source_key"],
            "content_hash": row["content_hash"],
            "staged_path": row["staged_path"],
            "audio_size_bytes": len(data),
            "audio_sha256": hashlib.sha256(data).hexdigest(),
            "completed_at": "now",
        })
    return completed


def _conventional_clip(
    tmp_path: Path, note: x2.Ex2Note, text: str, settings,
) -> Path:
    digest = x2.audio_cache_key(text, note.lang, settings)
    clip = (
        tmp_path / "staged_audio" / "grammar" / "exercises2" / note.lang
        / x2.audio_filename(note.lang, digest)
    )
    clip.parent.mkdir(parents=True, exist_ok=True)
    clip.write_bytes(_mp3(text.encode("utf-8")[:20]))
    return clip


def test_full_seed_queues_only_clips_missing_from_both_local_sources(
    tmp_path: Path, monkeypatch,
):
    note = local_tts.pilot_notes()[0]
    settings = SimpleNamespace(
        data_dir=tmp_path, local_tts_exercises2_pilot_approved=True,
    )
    answer = _conventional_clip(tmp_path, note, note.tl, settings)
    seeded = []

    async def no_completed(_keys):
        return []

    async def fake_seed(rows):
        seeded.extend(rows)
        return {
            "total": len(rows), "inserted": len(rows),
            "reset": 0, "unchanged": 0,
        }

    monkeypatch.setattr(local_tts, "get_settings", lambda: settings)
    monkeypatch.setattr(local_tts, "all_exercises2_notes", lambda: [note])
    monkeypatch.setattr(db, "completed_local_tts_jobs", no_completed)
    monkeypatch.setattr(db, "seed_local_tts_jobs", fake_seed)

    result = asyncio.run(local_tts.seed_exercises2_full())

    assert answer.is_file()
    assert [(row["clip_kind"], row["text"]) for row in seeded] == [
        ("example", note.example_tl),
        ("prompt_en", note.en),
    ]
    assert result["jobs"] == result["clips_missing"] == 2
    assert result["clips_expected"] == 3
    assert result["clips_existing_conventional"] == 1
    assert result["clips_completed_local"] == 0
    assert result["missing_only"] is True


def test_current_local_completion_wins_when_conventional_cache_also_exists(
    tmp_path: Path, monkeypatch,
):
    note = local_tts.pilot_notes()[0]
    settings = SimpleNamespace(
        data_dir=tmp_path, local_tts_exercises2_pilot_approved=True,
    )
    conventional = _conventional_clip(tmp_path, note, note.tl, settings)
    completed = _completed_rows(tmp_path, note)
    local_answer = tmp_path / "staged_audio" / completed[0]["staged_path"]

    async def fake_completed(_keys):
        return completed

    monkeypatch.setattr(local_tts, "get_settings", lambda: settings)
    monkeypatch.setattr(db, "completed_local_tts_jobs", fake_completed)

    resolution = asyncio.run(local_tts.resolve_exercises2_audio([note]))

    audio = resolution.audio_by_note_key[x2.exercises_note_key(note)]
    assert conventional.is_file()
    assert audio.answer == local_answer
    assert audio.prompt_en is not None
    assert resolution.stats["clips_completed_local"] == 3
    assert resolution.stats["clips_existing_conventional"] == 0
    assert resolution.missing_rows == []


def test_corrupt_conventional_clip_is_missing_and_not_silently_reused(
    tmp_path: Path, monkeypatch,
):
    note = local_tts.pilot_notes()[0]
    settings = SimpleNamespace(
        data_dir=tmp_path, local_tts_exercises2_pilot_approved=True,
    )
    corrupt = _conventional_clip(tmp_path, note, note.tl, settings)
    _conventional_clip(tmp_path, note, note.example_tl, settings)
    corrupt.write_bytes(b"not-an-mp3")
    seeded = []

    async def no_completed(_keys):
        return []

    async def fake_seed(rows):
        seeded.extend(rows)
        return {
            "total": len(rows), "inserted": len(rows),
            "reset": 0, "unchanged": 0,
        }

    monkeypatch.setattr(local_tts, "get_settings", lambda: settings)
    monkeypatch.setattr(local_tts, "all_exercises2_notes", lambda: [note])
    monkeypatch.setattr(db, "completed_local_tts_jobs", no_completed)
    monkeypatch.setattr(db, "seed_local_tts_jobs", fake_seed)

    result = asyncio.run(local_tts.seed_exercises2_full())

    assert [row["clip_kind"] for row in seeded] == ["answer", "prompt_en"]
    assert result["clips_invalid_conventional"] == 1
    assert result["clips_existing_conventional"] == 1
    assert result["clips_missing"] == 2


def test_invalid_current_completion_is_guarded_requeued_then_seeded(
    tmp_path: Path, monkeypatch,
):
    note = local_tts.pilot_notes()[0]
    settings = SimpleNamespace(
        data_dir=tmp_path, local_tts_exercises2_pilot_approved=True,
    )
    expected = local_tts.exercises2_job_rows([note], is_pilot=False)
    completed = _completed_rows(tmp_path, note)
    invalid = completed[0]
    (tmp_path / "staged_audio" / invalid["staged_path"]).unlink()
    requeued = []
    seeded = []

    async def fake_completed(_keys):
        return completed

    async def fake_requeue(source_key, *, content_hash, staged_path, error):
        requeued.append((source_key, content_hash, staged_path, error))
        return True

    async def fake_seed(rows):
        seeded.extend(rows)
        return {
            "total": len(rows), "inserted": 0,
            "reset": 0, "unchanged": len(rows),
        }

    monkeypatch.setattr(local_tts, "get_settings", lambda: settings)
    monkeypatch.setattr(local_tts, "all_exercises2_notes", lambda: [note])
    monkeypatch.setattr(db, "completed_local_tts_jobs", fake_completed)
    monkeypatch.setattr(db, "requeue_completed_local_tts_job", fake_requeue)
    monkeypatch.setattr(db, "seed_local_tts_jobs", fake_seed)

    result = asyncio.run(local_tts.seed_exercises2_full())

    assert seeded == [expected[0]]
    assert requeued[0][:3] == (
        expected[0]["source_key"], expected[0]["content_hash"],
        expected[0]["staged_path"],
    )
    assert "missing staged file" in requeued[0][3]
    assert result["clips_completed_local"] == 2
    assert result["clips_invalid_completed_requeued"] == 1
    assert result["clips_missing"] == 1


def test_requeue_completed_job_sql_is_exact_revision_guarded(monkeypatch):
    class FakePool:
        sql = ""
        args = ()

        async def fetchrow(self, sql, *args):
            self.sql, self.args = sql, args
            return {"id": 9}

    pool = FakePool()

    async def fake_pool():
        return pool

    monkeypatch.setattr(db, "get_pool", fake_pool)
    result = asyncio.run(db.requeue_completed_local_tts_job(
        "source", content_hash="a" * 64, staged_path="clip.mp3", error="bad",
    ))

    assert result is True
    assert "source_key = $1" in pool.sql
    assert "content_hash = $2" in pool.sql
    assert "staged_path = $3" in pool.sql
    assert "status = 'completed'" in pool.sql
    assert "audio_sha256 = NULL" in pool.sql
    assert pool.args == ("source", "a" * 64, "clip.mp3", "bad")


def test_strict_full_rebuild_uses_completed_clips_and_never_paid_tts(
    tmp_path: Path, monkeypatch,
):
    note = local_tts.pilot_notes()[0]
    completed = _completed_rows(tmp_path, note)
    settings = SimpleNamespace(
        data_dir=tmp_path, local_tts_exercises2_pilot_approved=True,
    )
    monkeypatch.setattr(local_tts, "get_settings", lambda: settings)
    monkeypatch.setattr(x2, "load_notes", lambda lang: [note])

    async def fake_completed(_keys):
        return completed

    async def forbidden_synthesize(*_args, **_kwargs):
        raise AssertionError("paid/provider-chain synthesis was called")

    def fake_build(*, out_path, lang, notes, audio):
        assert lang == note.lang and notes == [note]
        assert audio[note.item_id].answer.is_file()
        assert audio[note.item_id].example.is_file()
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(b"apkg")
        return 1

    async def fake_upsert(**_kwargs):
        return 321

    monkeypatch.setattr(db, "completed_local_tts_jobs", fake_completed)
    monkeypatch.setattr(gemini, "synthesize", forbidden_synthesize)
    monkeypatch.setattr(x2, "build_exercises2_apkg", fake_build)
    monkeypatch.setattr(db, "upsert_pool_apkg", fake_upsert)

    result = asyncio.run(local_tts.rebuild_exercises2_language(note.lang))
    assert result["local_only"] is True
    assert result["apkg_id"] == 321


def test_hybrid_rebuild_uses_conventional_then_local_without_provider(
    tmp_path: Path, monkeypatch,
):
    note = local_tts.pilot_notes()[0]
    settings = SimpleNamespace(
        data_dir=tmp_path, local_tts_exercises2_pilot_approved=True,
    )
    conventional_answer = _conventional_clip(tmp_path, note, note.tl, settings)
    completed = _completed_rows(tmp_path, note)
    local_example = tmp_path / "staged_audio" / completed[1]["staged_path"]
    local_prompt = tmp_path / "staged_audio" / completed[2]["staged_path"]

    async def fake_completed(_keys):
        return [completed[1], completed[2]]

    async def forbidden_synthesize(*_args, **_kwargs):
        raise AssertionError("paid/provider-chain synthesis was called")

    def fake_build(*, out_path, lang, notes, audio):
        assert lang == note.lang and notes == [note]
        assert audio[note.item_id].answer == conventional_answer
        assert audio[note.item_id].example == local_example
        assert audio[note.item_id].prompt_en == local_prompt
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(b"apkg")
        return 1

    async def fake_upsert(**_kwargs):
        return 654

    monkeypatch.setattr(local_tts, "get_settings", lambda: settings)
    monkeypatch.setattr(x2, "load_notes", lambda lang: [note])
    monkeypatch.setattr(x2, "leveled_speech_clip", lambda path: path)
    monkeypatch.setattr(db, "completed_local_tts_jobs", fake_completed)
    monkeypatch.setattr(gemini, "synthesize", forbidden_synthesize)
    monkeypatch.setattr(x2, "build_exercises2_apkg", fake_build)
    monkeypatch.setattr(db, "upsert_pool_apkg", fake_upsert)

    result = asyncio.run(local_tts.rebuild_exercises2_language(note.lang))

    assert result["apkg_id"] == 654
    assert result["clips_existing_conventional"] == 1
    assert result["clips_completed_local"] == 2
    assert result["clips_missing"] == 0


def test_strict_rebuild_refuses_missing_clip_before_builder_or_provider(
    tmp_path: Path, monkeypatch,
):
    note = local_tts.pilot_notes()[0]
    settings = SimpleNamespace(
        data_dir=tmp_path, local_tts_exercises2_pilot_approved=True,
    )
    monkeypatch.setattr(local_tts, "get_settings", lambda: settings)
    monkeypatch.setattr(x2, "load_notes", lambda lang: [note])

    async def no_completed(_keys):
        return []

    def forbidden_builder(**_kwargs):
        raise AssertionError("builder must not run with missing clips")

    async def forbidden_synthesize(*_args, **_kwargs):
        raise AssertionError("provider-chain synthesis was called")

    monkeypatch.setattr(db, "completed_local_tts_jobs", no_completed)
    monkeypatch.setattr(x2, "build_exercises2_apkg", forbidden_builder)
    monkeypatch.setattr(gemini, "synthesize", forbidden_synthesize)
    with pytest.raises(local_tts.LocalTTSBuildError, match="refused 3 clip"):
        asyncio.run(local_tts.rebuild_exercises2_language(note.lang))


def test_mixed_pilot_apkg_preserves_frozen_guids_model_and_deck_ids(tmp_path: Path):
    notes = local_tts.pilot_notes()
    clip = tmp_path / "pilot.mp3"
    clip.write_bytes(_mp3())
    audio = {
        x2.exercises_note_key(note): x2.NoteAudio(answer=clip, example=clip)
        for note in notes
    }
    out = tmp_path / "pilot.apkg"
    assert x2.build_exercises2_mixed_apkg(
        out_path=out, notes=notes, audio=audio,
    ) == 30

    with zipfile.ZipFile(out) as archive:
        db_path = tmp_path / "collection.anki2"
        db_path.write_bytes(archive.read("collection.anki2"))
        media = json.loads(archive.read("media"))
    assert list(media.values()) == [clip.name]
    connection = sqlite3.connect(db_path)
    try:
        note_rows = connection.execute("SELECT guid, mid FROM notes").fetchall()
        assert len(note_rows) == 30
        assert {mid for _, mid in note_rows} == {x2.MODEL_ID}
        assert {guid for guid, _ in note_rows} == {
            x2.exercises_guid(note.lang, note.topic, note.item_id)
            for note in notes
        }
        (deck_json,) = connection.execute("SELECT decks FROM col").fetchone()
        actual_decks = {
            int(deck_id): deck["name"]
            for deck_id, deck in json.loads(deck_json).items()
            if deck["name"] != "Default"
        }
        expected_decks = {
            x2._deck_id(x2.deck_name_for(note.lang, note.topic)):
            x2.deck_name_for(note.lang, note.topic)
            for note in notes
        }
        assert actual_decks == expected_decks
        assert {row[0] for row in connection.execute("SELECT did FROM cards")} == set(
            expected_decks
        )
        assert connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0] == 60
    finally:
        connection.close()


def test_bulk_gate_defaults_closed(monkeypatch):
    monkeypatch.setattr(
        local_tts, "get_settings",
        lambda: SimpleNamespace(local_tts_exercises2_pilot_approved=False),
    )
    with pytest.raises(local_tts.PilotApprovalRequired, match="not approved"):
        asyncio.run(local_tts.seed_exercises2_full())


def test_normal_exercises2_local_only_route_is_closed_before_job_claim(
    monkeypatch,
):
    from idiomatic.grammar import service as grammar_service

    monkeypatch.setattr(
        local_tts, "get_settings",
        lambda: SimpleNamespace(local_tts_exercises2_pilot_approved=False),
    )
    claimed = False

    def forbidden_claim(*_args):
        nonlocal claimed
        claimed = True
        return True

    monkeypatch.setattr(grammar_service, "claim_grammar_job", forbidden_claim)
    api.app.dependency_overrides[api.authed_admin] = lambda: None

    async def request():
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test",
        ) as client:
            return await client.post(
                "/admin/exercises2-build",
                params={"lang": "es", "local_only": "true"},
            )

    try:
        response = asyncio.run(request())
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)

    assert response.status_code == 409
    assert "pilot is not approved" in response.text
    assert claimed is False


def test_normal_exercises2_local_only_route_uses_hybrid_builder(monkeypatch):
    from idiomatic.grammar import service as grammar_service

    calls = []

    async def fake_local_build(lang):
        calls.append(("local", lang))
        return {"lang": lang, "local_only": True}

    async def forbidden_provider_build(_lang):
        raise AssertionError("provider Exercises2 builder was called")

    monkeypatch.setattr(local_tts, "require_bulk_approval", lambda: None)
    monkeypatch.setattr(local_tts, "rebuild_exercises2_language", fake_local_build)
    monkeypatch.setattr(x2, "build_language", forbidden_provider_build)
    monkeypatch.setattr(grammar_service, "claim_grammar_job", lambda *_args: True)
    monkeypatch.setattr(grammar_service, "_state", {})
    spawned = []
    monkeypatch.setattr(api, "_spawn_bg", spawned.append)
    api.app.dependency_overrides[api.authed_admin] = lambda: None

    async def request_and_finish():
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test",
        ) as client:
            response = await client.post(
                "/admin/exercises2-build",
                params={"lang": "es", "local_only": "true"},
            )
        assert len(spawned) == 1
        await spawned[0]
        return response

    try:
        response = asyncio.run(request_and_finish())
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)

    assert response.status_code == 200
    assert response.json() == {"started": True, "lang": "es", "local_only": True}
    assert calls == [("local", "es")]
    assert grammar_service._state["exercises2"]["local_only"] is True


def _expression_pool_idiom() -> dict:
    return {
        "id": 77,
        "idiom_text": "dar en el clavo",
        "english_gloss": "to hit the nail on the head",
        "explanation_en": "Used when someone identifies the exact issue.",
        "audio_idiom_tgt": None,
        "audio_idiom_en": None,
        "audio_explanation": None,
        "audio_context": "source-video/context_077.mp3",
        "examples": [{
            "idiom_id": 77,
            "ord": 1,
            "en_text": "You hit the nail on the head.",
            "target_text": "Diste en el clavo.",
            "audio_en": None,
            "audio_target": None,
        }],
        "youtube_id": "video77",
        "video_title": "Example",
    }


def _completed_expression_pool_rows(
    tmp_path: Path, rows: list[dict],
) -> list[dict]:
    completed = []
    for index, row in enumerate(rows):
        data = _mp3(str(index).encode())
        clip = tmp_path / "staged_audio" / row["staged_path"]
        clip.parent.mkdir(parents=True, exist_ok=True)
        clip.write_bytes(data)
        completed.append({
            "id": index + 100,
            "source_key": row["source_key"],
            "content_hash": row["content_hash"],
            "staged_path": row["staged_path"],
            "audio_size_bytes": len(data),
            "audio_sha256": hashlib.sha256(data).hexdigest(),
            "completed_at": "now",
        })
    return completed


def test_expression_pool_adapter_is_deterministic_supports_en_and_skips_context():
    idiom = _expression_pool_idiom()
    rows = local_tts.expression_pool_job_rows("es", [idiom])

    assert len(rows) == 5
    assert [row["lang"] for row in rows] == ["es", "en", "en", "es", "en"]
    assert {row["source_kind"] for row in rows} == {"expression_pool"}
    assert len({row["source_key"] for row in rows}) == 5
    assert all("audio_context" not in row["source_key"] for row in rows)
    assert all(
        row["staged_path"].startswith("expressions/pool/local_qwen/v1/")
        for row in rows
    )
    assert local_tts._expected_path_for_job(rows[1]) == rows[1]["staged_path"]
    with pytest.raises(ValueError, match="pool lang"):
        local_tts.expression_pool_job_rows("en", [idiom])


def test_expression_pool_seed_is_gated_and_missing_only(
    tmp_path: Path, monkeypatch,
):
    idiom = _expression_pool_idiom()
    existing_rel = "video77/idiom_tgt_077.mp3"
    existing = tmp_path / "staged_audio" / existing_rel
    existing.parent.mkdir(parents=True)
    existing.write_bytes(_mp3())
    idiom["audio_idiom_tgt"] = existing_rel
    settings = SimpleNamespace(
        data_dir=tmp_path, local_tts_exercises2_pilot_approved=True,
    )
    seeded = []

    async def fake_fetch(lang):
        assert lang == "es"
        return [idiom]

    async def no_completed(_keys):
        return []

    async def fake_seed(rows):
        seeded.extend(rows)
        return {
            "total": len(rows), "inserted": len(rows),
            "reset": 0, "unchanged": 0,
        }

    monkeypatch.setattr(local_tts, "get_settings", lambda: settings)
    monkeypatch.setattr(db, "fetch_pool_idioms", fake_fetch)
    monkeypatch.setattr(db, "completed_local_tts_jobs", no_completed)
    monkeypatch.setattr(db, "seed_local_tts_jobs", fake_seed)

    result = asyncio.run(local_tts.seed_expression_pool("es"))

    assert len(seeded) == 4
    assert not any(row["text"] == idiom["idiom_text"] for row in seeded)
    assert result["clips_expected"] == 5
    assert result["clips_existing_conventional"] == 1
    assert result["clips_missing"] == result["jobs"] == 4
    assert result["audio_context_excluded"] is True


def test_expression_pool_local_only_rebuild_overlays_without_provider_calls(
    tmp_path: Path, monkeypatch,
):
    idiom = _expression_pool_idiom()
    rows = local_tts.expression_pool_job_rows("es", [idiom])
    completed = _completed_expression_pool_rows(tmp_path, rows)
    expected_paths = {row["text"]: row["staged_path"] for row in rows}
    settings = SimpleNamespace(
        data_dir=tmp_path,
        local_tts_exercises2_pilot_approved=True,
        pool_rebuild_debounce_min=30,
        build_didactic_pool=False,
        build_audio_pools=False,
    )
    ensured = False

    async def fake_fetch(lang):
        assert lang == "es"
        return [idiom]

    async def fake_completed(_keys):
        return completed

    async def forbidden_ensure(*_args, **_kwargs):
        nonlocal ensured
        ensured = True
        raise AssertionError("paid explanation TTS path was called")

    async def forbidden_synthesize(*_args, **_kwargs):
        raise AssertionError("provider synthesis was called")

    def fake_expression_builder(lang, idioms, _stage_dir, out):
        assert lang == "es"
        overlaid = idioms[0]
        assert overlaid["audio_idiom_tgt"] == expected_paths[idiom["idiom_text"]]
        assert overlaid["audio_idiom_en"] == expected_paths[idiom["english_gloss"]]
        assert overlaid["audio_explanation"] == expected_paths[idiom["explanation_en"]]
        assert overlaid["audio_context"] == idiom["audio_context"]
        example = overlaid["examples"][0]
        assert example["audio_target"] == expected_paths[example["target_text"]]
        assert example["audio_en"] == expected_paths[example["en_text"]]
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(b"apkg")
        return 1

    async def fake_upsert(**_kwargs):
        return 701

    async def fake_mark(_lang):
        return None

    monkeypatch.setattr(local_tts, "get_settings", lambda: settings)
    monkeypatch.setattr(pool_mod, "get_settings", lambda: settings)
    monkeypatch.setattr(db, "fetch_pool_idioms", fake_fetch)
    monkeypatch.setattr(db, "completed_local_tts_jobs", fake_completed)
    monkeypatch.setattr(db, "upsert_pool_apkg", fake_upsert)
    monkeypatch.setattr(db, "mark_pool_rebuilt", fake_mark)
    monkeypatch.setattr(pool_mod, "_ensure_explanation_audio", forbidden_ensure)
    monkeypatch.setattr(pool_mod, "_build_expression_pool", fake_expression_builder)
    monkeypatch.setattr(pool_mod, "_REBUILD_LOCKS", {})
    monkeypatch.setattr(gemini, "synthesize", forbidden_synthesize)

    result = asyncio.run(pool_mod.rebuild_pools(
        "es", force=True, local_only=True,
    ))

    assert ensured is False
    assert result["local_only"] is True
    assert result["expr_cards"] == 1
    assert result["clips_completed_local"] == 5
    assert result["clips_missing"] == 0


def test_expression_pool_local_only_rebuild_refuses_missing_before_build(
    tmp_path: Path, monkeypatch,
):
    idiom = _expression_pool_idiom()
    settings = SimpleNamespace(
        data_dir=tmp_path,
        local_tts_exercises2_pilot_approved=True,
        pool_rebuild_debounce_min=30,
        build_didactic_pool=False,
        build_audio_pools=False,
    )

    async def fake_fetch(_lang):
        return [idiom]

    async def no_completed(_keys):
        return []

    def forbidden_builder(*_args, **_kwargs):
        raise AssertionError("pool builder ran with missing audio")

    monkeypatch.setattr(local_tts, "get_settings", lambda: settings)
    monkeypatch.setattr(pool_mod, "get_settings", lambda: settings)
    monkeypatch.setattr(db, "fetch_pool_idioms", fake_fetch)
    monkeypatch.setattr(db, "completed_local_tts_jobs", no_completed)
    monkeypatch.setattr(pool_mod, "_build_expression_pool", forbidden_builder)
    monkeypatch.setattr(pool_mod, "_REBUILD_LOCKS", {})

    with pytest.raises(local_tts.LocalTTSBuildError, match="refused 5 clip"):
        asyncio.run(pool_mod.rebuild_pools("es", force=True, local_only=True))


def test_local_tts_api_is_admin_authenticated(monkeypatch):
    monkeypatch.setattr(
        api, "get_settings",
        lambda: SimpleNamespace(
            admin_token="secret", local_tts_exercises2_pilot_approved=False,
        ),
    )

    async def fake_seed():
        return {"pilot": True, "notes": 30, "jobs": 60}

    monkeypatch.setattr(local_tts, "seed_exercises2_pilot", fake_seed)

    async def run_requests():
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            unauth = await client.post("/admin/local-tts/v1/exercises2/seed-pilot")
            auth = await client.post(
                "/admin/local-tts/v1/exercises2/seed-pilot",
                headers={"X-Admin-Token": "secret"},
            )
        return unauth, auth

    unauth, auth = asyncio.run(run_requests())
    assert unauth.status_code == 401
    assert auth.status_code == 200
    assert auth.json()["jobs"] == 60


def test_claim_api_decorates_v1_paths(monkeypatch):
    captured = {}

    async def fake_claim(**kwargs):
        captured.update(kwargs)
        return {
            "lease_token": "batch-lease",
            "jobs": [{
                "id": 44,
                "contract_version": 1,
                "source_key": "exercises2:v1:es:connecting:esc01:answer",
                "lang": "es",
                "text": "Sea como fuere",
            }],
        }

    monkeypatch.setattr(db, "claim_local_tts_jobs", fake_claim)
    api.app.dependency_overrides[api.authed_admin] = lambda: None

    async def request():
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/admin/local-tts/v1/jobs/claim",
                json={"worker_id": "fedora", "limit": 3, "lease_seconds": 600},
            )

    try:
        response = asyncio.run(request())
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)
    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == 1
    assert body["lease_token"] == "batch-lease"
    assert body["jobs"][0]["upload_path"] == "/admin/local-tts/v1/jobs/44/upload"
    assert body["jobs"][0]["failure_path"] == "/admin/local-tts/v1/jobs/44/fail"
    assert captured == {
        "worker_id": "fedora", "limit": 3, "lease_seconds": 600,
        "contract_version": 1,
    }


def test_upload_api_success_and_stale_lease(monkeypatch):
    seen = {}

    async def successful(job_id, *, lease_token, data):
        seen.update(job_id=job_id, lease_token=lease_token, data=data)
        return {
            "ok": True, "job_id": job_id, "staged_path": "canonical.mp3",
            "size_bytes": len(data), "sha256": "a" * 64,
            "file": "/data/must-not-leak.mp3",
        }

    monkeypatch.setattr(local_tts, "accept_upload", successful)
    api.app.dependency_overrides[api.authed_admin] = lambda: None

    async def request_once():
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/admin/local-tts/v1/jobs/9/upload",
                headers={
                    "X-Local-TTS-Lease": "live-lease",
                    "Content-Type": "audio/mpeg",
                },
                content=_mp3(),
            )

    try:
        success = asyncio.run(request_once())
        assert success.status_code == 200
        assert success.json()["job_id"] == 9
        assert "file" not in success.json()
        assert seen == {"job_id": 9, "lease_token": "live-lease", "data": _mp3()}

        async def stale(*_args, **_kwargs):
            raise local_tts.LocalTTSLeaseError("expired")

        monkeypatch.setattr(local_tts, "accept_upload", stale)
        stale_response = asyncio.run(request_once())
        assert stale_response.status_code == 409
        assert "expired" in stale_response.text
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)


def test_upload_api_rejects_content_type_and_oversize_before_handler(monkeypatch):
    called = False

    async def forbidden(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("upload handler should not run")

    monkeypatch.setattr(local_tts, "accept_upload", forbidden)
    api.app.dependency_overrides[api.authed_admin] = lambda: None

    async def requests():
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            bad_type = await client.post(
                "/admin/local-tts/v1/jobs/1/upload",
                headers={"X-Local-TTS-Lease": "x", "Content-Type": "text/plain"},
                content=b"nope",
            )
            oversize = await client.post(
                "/admin/local-tts/v1/jobs/1/upload",
                headers={
                    "X-Local-TTS-Lease": "x", "Content-Type": "audio/mpeg",
                    "Content-Length": str(local_tts.MAX_MP3_BYTES + 1),
                },
                content=b"short",
            )
        return bad_type, oversize

    try:
        bad_type, oversize = asyncio.run(requests())
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)
    assert bad_type.status_code == 415
    assert oversize.status_code == 413
    assert called is False


def test_failure_api_requeues_by_default(monkeypatch):
    seen = {}

    async def fake_fail(job_id, *, lease_token, error, requeue):
        seen.update(
            job_id=job_id, lease_token=lease_token, error=error, requeue=requeue,
        )
        return {"id": job_id, "status": "queued", "attempts": 2}

    monkeypatch.setattr(db, "fail_local_tts_job", fake_fail)
    api.app.dependency_overrides[api.authed_admin] = lambda: None

    async def request():
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/admin/local-tts/v1/jobs/7/fail",
                headers={"X-Local-TTS-Lease": "batch"},
                json={"error": "bridge busy"},
            )

    try:
        response = asyncio.run(request())
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert seen == {
        "job_id": 7, "lease_token": "batch", "error": "bridge busy",
        "requeue": True,
    }


def test_real_postgres_seed_edit_reset_lease_reclaim_and_constraints(monkeypatch):
    """Optional real-SQL contract test against an isolated temporary schema.

    Set ``IDIOMATIC_TEST_POSTGRES_DSN`` to a disposable/test Postgres database.
    The test creates and drops one UUID-named schema and never touches public.
    """
    dsn = os.environ.get("IDIOMATIC_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("set IDIOMATIC_TEST_POSTGRES_DSN for real Postgres contract test")

    async def exercise():
        connection = await asyncpg.connect(dsn)
        schema_name = f"local_tts_test_{uuid.uuid4().hex}"
        assert schema_name.replace("local_tts_test_", "").isalnum()
        await connection.execute(f'CREATE SCHEMA "{schema_name}"')
        try:
            await connection.execute(f'SET search_path TO "{schema_name}"')
            schema_sql = (Path(__file__).parent.parent / "db" / "schema.sql").read_text()
            start = schema_sql.index("CREATE TABLE IF NOT EXISTS local_tts_jobs")
            end = schema_sql.index(
                "-- LingQ vocabulary mirror", start,
            )
            await connection.execute(schema_sql[start:end])
            await connection.execute(schema_sql[start:end])  # schema is re-applicable

            async def fake_pool():
                return connection

            monkeypatch.setattr(db, "get_pool", fake_pool)
            seed = local_tts.exercises2_job_rows(
                [local_tts.pilot_notes()[0]], is_pilot=True,
            )[0]
            first = await db.seed_local_tts_jobs([seed])
            assert first["inserted"] == 1
            await connection.execute(
                """
                UPDATE local_tts_jobs
                SET status='completed', audio_size_bytes=1000,
                    audio_sha256=$2, completed_at=NOW()
                WHERE source_key=$1
                """,
                seed["source_key"], "a" * 64,
            )
            same = await db.seed_local_tts_jobs([seed])
            assert same["unchanged"] == 1
            assert await connection.fetchval(
                "SELECT status FROM local_tts_jobs WHERE source_key=$1",
                seed["source_key"],
            ) == "completed"

            edited = dict(seed)
            edited["text"] += " edited"
            edited["content_hash"] = local_tts.content_hash(
                edited["text"], edited["lang"],
            )
            edited["staged_path"] = local_tts.canonical_staged_path(
                edited["source_key"], edited["lang"], edited["content_hash"],
            )
            changed = await db.seed_local_tts_jobs([edited])
            assert changed["reset"] == 1
            reset = await connection.fetchrow(
                """SELECT status, attempts, audio_sha256
                   FROM local_tts_jobs WHERE source_key=$1""",
                seed["source_key"],
            )
            assert dict(reset) == {"status": "queued", "attempts": 0,
                                   "audio_sha256": None}

            first_claim = await db.claim_local_tts_jobs(
                worker_id="postgres-test", limit=1, lease_seconds=60,
            )
            assert len(first_claim["jobs"]) == 1
            await connection.execute(
                """UPDATE local_tts_jobs
                   SET lease_expires_at=NOW() - INTERVAL '1 second'
                   WHERE id=$1""",
                first_claim["jobs"][0]["id"],
            )
            second_claim = await db.claim_local_tts_jobs(
                worker_id="postgres-test-2", limit=1, lease_seconds=60,
            )
            assert second_claim["jobs"][0]["attempts"] == 2
            assert second_claim["lease_token"] != first_claim["lease_token"]
            assert await db.fail_local_tts_job(
                second_claim["jobs"][0]["id"],
                lease_token=first_claim["lease_token"], error="stale",
            ) is None
            failed = await db.fail_local_tts_job(
                second_claim["jobs"][0]["id"],
                lease_token=second_claim["lease_token"], error="bridge busy",
            )
            assert failed is not None and failed["status"] == "queued"
            third_claim = await db.claim_local_tts_jobs(
                worker_id="postgres-test-3", limit=1, lease_seconds=60,
            )
            job_id = third_claim["jobs"][0]["id"]
            leased = await db.leased_local_tts_job(
                job_id, lease_token=third_claim["lease_token"],
            )
            assert leased is not None and leased["source_key"] == edited["source_key"]
            completed = await db.complete_local_tts_job(
                job_id, lease_token=third_claim["lease_token"],
                audio_size_bytes=1234, audio_sha256="c" * 64,
            )
            assert completed is not None and completed["status"] == "completed"
            status = await db.local_tts_status()
            assert status["counts"] == {"completed": 1}
            assert status["pilot_counts"] == {"completed": 1}

            with pytest.raises(asyncpg.CheckViolationError):
                await connection.execute(
                    """
                    INSERT INTO local_tts_jobs
                      (contract_version, source_kind, source_key, lang, note_key,
                       clip_kind, text, voice_version, content_hash, staged_path,
                       status)
                    VALUES (1,'exercises2','bad','es','bad','answer','x','v1',
                            $1,'bad.mp3','completed')
                    """,
                    "b" * 64,
                )
        finally:
            await connection.execute("RESET search_path")
            await connection.execute(f'DROP SCHEMA "{schema_name}" CASCADE')
            await connection.close()

    asyncio.run(exercise())


def test_conventional_lookup_finds_legacy_elevenlabs_fingerprint(
    tmp_path: Path, monkeypatch,
):
    """Clips cached while ElevenLabs was primary must stay visible after
    the qwen-local promotion (2026-08-09 regression: five strict rebuilds
    refused ~700 clips each because the live fingerprint changed)."""
    note = local_tts.pilot_notes()[0]
    live = SimpleNamespace(
        data_dir=tmp_path, local_tts_exercises2_pilot_approved=True,
        tts_provider="qwen-local", elevenlabs_api_key="k",
        elevenlabs_model="eleven_turbo_v2_5", gemini_tts_model="g-tts",
    )
    legacy_view = local_tts._LegacyElevenSettingsView(live)
    assert legacy_view.tts_provider == "elevenlabs"
    # Cache the answer clip under the LEGACY (elevenlabs) fingerprint only.
    legacy_clip = _conventional_clip(tmp_path, note, note.tl, legacy_view)
    live_digest = x2.audio_cache_key(note.tl, note.lang, live)
    legacy_digest = x2.audio_cache_key(note.tl, note.lang, legacy_view)
    assert live_digest != legacy_digest

    async def no_completed(_keys):
        return []

    monkeypatch.setattr(local_tts, "get_settings", lambda: live)
    monkeypatch.setattr(db, "completed_local_tts_jobs", no_completed)

    resolution = asyncio.run(local_tts.resolve_exercises2_audio([note]))
    audio = resolution.audio_by_note_key[x2.exercises_note_key(note)]
    assert audio.answer == legacy_clip
    assert resolution.stats["clips_existing_conventional"] == 1
