"""Versioned local-Qwen work queue and strict Exercises2 rebuild lane.

This module deliberately has no synthesis call.  Render seeds text jobs,
leases them to a machine-local worker, validates uploaded MP3s, and packages
only completed clips.  A missing clip is a hard build error: the lane never
falls through to ElevenLabs or Gemini.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import structlog

from . import db
from .grammar import exercises2 as x2
from .settings import get_settings

log = structlog.get_logger()

CONTRACT_VERSION = 1
VOICE_VERSION = "qwen3-tts-clone-v1"
PILOT_APKG_KIND = "exercises2_pilot"
# ``apkgs.lang`` is delivery-routing metadata and accepts one language.  The
# operator's normal agent subscribes to Spanish as well as the other pilot
# languages, so one mixed artifact rides that lane instead of five APKGs.
PILOT_DELIVERY_LANG = "es"

MIN_MP3_BYTES = 1_000
MAX_MP3_BYTES = 8_000_000

# Frozen identities: changing file order or adding notes must not silently
# change the listening pilot.  Three connecting + three conditionals per lang.
PILOT_NOTE_IDS: dict[str, dict[str, tuple[str, str, str]]] = {
    "de": {
        "connecting": ("dec001", "dec002", "dec003"),
        "conditionals": ("ded001", "ded002", "ded003"),
    },
    "es": {
        "connecting": ("esc01", "esc02", "esc03"),
        "conditionals": ("esd001", "esd002", "esd003"),
    },
    "fr": {
        "connecting": ("frc002", "frc003", "frc005"),
        "conditionals": ("frd001", "frd002", "frd003"),
    },
    "it": {
        "connecting": ("itc002", "itc003", "itc005"),
        "conditionals": ("itd001", "itd002", "itd003"),
    },
    "pt": {
        "connecting": ("ptc002", "ptc004", "ptc005"),
        "conditionals": ("ptd001", "ptd002", "ptd003"),
    },
}


class LocalTTSError(RuntimeError):
    """Base error for the versioned local-only lane."""


class PilotApprovalRequired(LocalTTSError):
    """Bulk work was requested before the listening pilot was approved."""


class LocalTTSLeaseError(LocalTTSError):
    """An upload/failure report did not carry a current lease."""


class LocalTTSUploadError(LocalTTSError):
    """Uploaded bytes or their server-chosen destination are invalid."""


class LocalTTSBuildError(LocalTTSError):
    """A strict rebuild is missing or has stale/corrupt local clips."""


def pilot_notes(*, source_dir: Path | None = None) -> list[x2.Ex2Note]:
    """Load the frozen 30-note pilot in language/topic/id order."""
    root = Path(source_dir) if source_dir is not None else x2.SOURCE_DIR
    selected: list[x2.Ex2Note] = []
    for lang, topics in PILOT_NOTE_IDS.items():
        for topic, item_ids in topics.items():
            path = root / f"{lang}_{topic}.json"
            notes = {note.item_id: note for note in x2.parse_notes_file(path)}
            missing = [item_id for item_id in item_ids if item_id not in notes]
            if missing:
                raise LocalTTSBuildError(
                    f"pilot source {path.name} lost frozen ids: {', '.join(missing)}"
                )
            selected.extend(notes[item_id] for item_id in item_ids)
    if len(selected) != 30:
        raise LocalTTSBuildError(f"pilot must contain 30 notes, got {len(selected)}")
    return selected


def all_exercises2_notes() -> list[x2.Ex2Note]:
    """Every reviewed Exercises2 note, in stable language/file order."""
    return [
        note
        for lang in sorted(x2.SUPPORTED_LANGS)
        for note in x2.load_notes(lang)
    ]


def job_source_key(note: x2.Ex2Note, clip_kind: str) -> str:
    if clip_kind not in ("answer", "example"):
        raise ValueError("clip_kind must be answer|example")
    return (
        f"exercises2:v{CONTRACT_VERSION}:{note.lang}:{note.topic}:"
        f"{note.item_id}:{clip_kind}"
    )


def content_hash(
    text: str, lang: str, *, voice_version: str = VOICE_VERSION,
    contract_version: int = CONTRACT_VERSION,
) -> str:
    payload = {
        "contract_version": contract_version,
        "lang": lang,
        "text": text,
        "voice_version": voice_version,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def canonical_staged_path(source_key: str, lang: str, digest: str) -> str:
    """Server-owned path relative to ``DATA_DIR/staged_audio``."""
    if lang not in x2.SUPPORTED_LANGS:
        raise ValueError("unsupported local TTS language")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("content digest must be 64 lowercase hex characters")
    identity = hashlib.sha256(source_key.encode("utf-8")).hexdigest()[:12]
    name = f"idx2q_v{CONTRACT_VERSION}_{lang}_{identity}_{digest[:20]}.mp3"
    return f"grammar/exercises2/local_qwen/v{CONTRACT_VERSION}/{lang}/{name}"


def exercises2_job_rows(
    notes: list[x2.Ex2Note], *, is_pilot: bool,
) -> list[dict[str, Any]]:
    """Create the two clip jobs (answer + example) for each note."""
    note_keys = [x2.exercises_note_key(note) for note in notes]
    if len(note_keys) != len(set(note_keys)):
        raise ValueError("duplicate Exercises2 note identity")
    rows: list[dict[str, Any]] = []
    for note in notes:
        for clip_kind, text in (("answer", note.tl), ("example", note.example_tl)):
            source_key = job_source_key(note, clip_kind)
            digest = content_hash(text, note.lang)
            rows.append({
                "contract_version": CONTRACT_VERSION,
                "source_kind": "exercises2",
                "source_key": source_key,
                "lang": note.lang,
                "note_key": x2.exercises_note_key(note),
                "clip_kind": clip_kind,
                "text": text,
                "voice_version": VOICE_VERSION,
                "content_hash": digest,
                "staged_path": canonical_staged_path(source_key, note.lang, digest),
                "is_pilot": is_pilot,
            })
    return rows


async def seed_exercises2_pilot() -> dict[str, Any]:
    notes = pilot_notes()
    result = await db.seed_local_tts_jobs(exercises2_job_rows(notes, is_pilot=True))
    return {**result, "notes": len(notes), "jobs": len(notes) * 2,
            "contract_version": CONTRACT_VERSION, "pilot": True}


def require_bulk_approval() -> None:
    if not get_settings().local_tts_exercises2_pilot_approved:
        raise PilotApprovalRequired(
            "Exercises2 local-TTS pilot is not approved; set "
            "LOCAL_TTS_EXERCISES2_PILOT_APPROVED=true only after owner verdict"
        )


async def seed_exercises2_full() -> dict[str, Any]:
    require_bulk_approval()
    notes = all_exercises2_notes()
    result = await db.seed_local_tts_jobs(exercises2_job_rows(notes, is_pilot=False))
    return {**result, "notes": len(notes), "jobs": len(notes) * 2,
            "contract_version": CONTRACT_VERSION, "pilot": False}


def _is_mp3_frame_header(header: bytes) -> bool:
    if len(header) < 4:
        return False
    bits = int.from_bytes(header[:4], "big")
    if (bits >> 21) & 0x7FF != 0x7FF:
        return False
    version = (bits >> 19) & 0x3
    layer = (bits >> 17) & 0x3
    bitrate_index = (bits >> 12) & 0xF
    sample_rate_index = (bits >> 10) & 0x3
    return (
        version != 0x1
        and layer != 0x0
        and bitrate_index not in (0x0, 0xF)
        and sample_rate_index != 0x3
    )


def validate_mp3(data: bytes) -> None:
    """Reject empty/oversized/polyglot uploads before they reach staging."""
    if len(data) < MIN_MP3_BYTES or len(data) > MAX_MP3_BYTES:
        raise LocalTTSUploadError(
            f"clip size must be {MIN_MP3_BYTES}..{MAX_MP3_BYTES} bytes"
        )
    offset = 0
    if data.startswith(b"ID3"):
        if len(data) < 10 or any(byte & 0x80 for byte in data[6:10]):
            raise LocalTTSUploadError("invalid ID3 header")
        tag_size = (
            (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
        )
        offset = 10 + tag_size + (10 if data[5] & 0x10 else 0)
    # ffmpeg output starts at the frame (or directly after ID3 padding).
    # Search only a small prefix after the declared tag, not arbitrary bytes.
    end = min(len(data) - 3, offset + 4096)
    if offset < 0 or offset >= end or not any(
        _is_mp3_frame_header(data[pos:pos + 4]) for pos in range(offset, end)
    ):
        raise LocalTTSUploadError("body does not contain a valid MP3 frame header")


def _expected_path_for_job(job: dict[str, Any]) -> str:
    expected_hash = content_hash(
        job["text"], job["lang"], voice_version=job["voice_version"],
        contract_version=int(job["contract_version"]),
    )
    if expected_hash != job["content_hash"]:
        raise LocalTTSUploadError("job content hash is inconsistent")
    return canonical_staged_path(job["source_key"], job["lang"], expected_hash)


def _staged_audio_root(data_dir: Path, *, create: bool) -> Path:
    """Resolve the real staging root while refusing a root-level symlink."""
    data_root = Path(data_dir).resolve()
    candidate = data_root / "staged_audio"
    if candidate.is_symlink():
        raise LocalTTSUploadError("staged_audio root must not be a symlink")
    if create:
        candidate.mkdir(parents=True, exist_ok=True)
    root = candidate.resolve()
    if root != candidate or not root.is_relative_to(data_root):
        raise LocalTTSUploadError("staged_audio root escapes DATA_DIR")
    return root


def atomic_stage_mp3(
    data: bytes, *, job: dict[str, Any], data_dir: Path,
) -> tuple[Path, str]:
    """Validate and atomically replace the server-selected canonical clip."""
    validate_mp3(data)
    expected_rel = _expected_path_for_job(job)
    if job["staged_path"] != expected_rel:
        raise LocalTTSUploadError("job staged path is not canonical")

    root = _staged_audio_root(Path(data_dir), create=True)
    destination = (root / expected_rel).resolve()
    if not destination.is_relative_to(root):
        raise LocalTTSUploadError("staged path escapes staged_audio")
    destination.parent.mkdir(parents=True, exist_ok=True)

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{destination.name}.", suffix=".tmp",
            dir=destination.parent, delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, destination)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return destination, hashlib.sha256(data).hexdigest()


async def accept_upload(
    job_id: int, *, lease_token: str, data: bytes,
) -> dict[str, Any]:
    job = await db.leased_local_tts_job(job_id, lease_token=lease_token)
    if job is None:
        raise LocalTTSLeaseError("unknown, stale or expired local-TTS lease")
    destination, digest = await asyncio.to_thread(
        atomic_stage_mp3, data, job=job, data_dir=Path(get_settings().data_dir),
    )
    completed = await db.complete_local_tts_job(
        job_id, lease_token=lease_token, audio_size_bytes=len(data),
        audio_sha256=digest,
    )
    if completed is None:
        # The canonical file is harmless/orphan-healable, but never report a
        # success for a lease that expired while its body was being stored.
        raise LocalTTSLeaseError("lease expired before upload completion")
    log.info("local_tts.upload.completed", job_id=job_id,
             staged_path=job["staged_path"], size=len(data))
    return {
        "ok": True,
        "job_id": job_id,
        "staged_path": job["staged_path"],
        "size_bytes": len(data),
        "sha256": digest,
        "file": str(destination),
    }


def _verified_completed_clip(
    expected: dict[str, Any], completed: dict[str, Any] | None, *, data_dir: Path,
) -> Path:
    if completed is None:
        raise LocalTTSBuildError(f"missing completed clip: {expected['source_key']}")
    if completed["content_hash"] != expected["content_hash"]:
        raise LocalTTSBuildError(f"stale completed clip: {expected['source_key']}")
    if completed["staged_path"] != expected["staged_path"]:
        raise LocalTTSBuildError(f"noncanonical completed clip: {expected['source_key']}")
    try:
        root = _staged_audio_root(Path(data_dir), create=False)
    except LocalTTSUploadError as exc:
        raise LocalTTSBuildError(str(exc)) from exc
    clip = (root / expected["staged_path"]).resolve()
    if not clip.is_relative_to(root) or not clip.is_file():
        raise LocalTTSBuildError(f"missing staged file: {expected['source_key']}")
    data = clip.read_bytes()
    try:
        validate_mp3(data)
    except LocalTTSUploadError as exc:
        raise LocalTTSBuildError(
            f"invalid staged MP3 for {expected['source_key']}: {exc}"
        ) from exc
    digest = hashlib.sha256(data).hexdigest()
    if len(data) != completed["audio_size_bytes"] or digest != completed["audio_sha256"]:
        raise LocalTTSBuildError(f"staged clip checksum mismatch: {expected['source_key']}")
    return clip


async def completed_audio_for_notes(
    notes: list[x2.Ex2Note], *, data_dir: Path | None = None,
) -> dict[str, x2.NoteAudio]:
    """Resolve both completed, current clips for every note or refuse all."""
    expected_rows = exercises2_job_rows(notes, is_pilot=False)
    completed_rows = await db.completed_local_tts_jobs(
        [row["source_key"] for row in expected_rows]
    )
    completed = {row["source_key"]: row for row in completed_rows}
    root = Path(data_dir) if data_dir is not None else Path(get_settings().data_dir)

    clips: dict[tuple[str, str], Path] = {}
    problems: list[str] = []
    for expected in expected_rows:
        try:
            clip = _verified_completed_clip(
                expected, completed.get(expected["source_key"]), data_dir=root,
            )
        except LocalTTSBuildError as exc:
            problems.append(str(exc))
        else:
            clips[(expected["note_key"], expected["clip_kind"])] = clip
    if problems:
        preview = "; ".join(problems[:10])
        suffix = f"; plus {len(problems) - 10} more" if len(problems) > 10 else ""
        raise LocalTTSBuildError(
            f"strict local rebuild refused {len(problems)} clip(s): {preview}{suffix}"
        )
    return {
        x2.exercises_note_key(note): x2.NoteAudio(
            answer=clips[(x2.exercises_note_key(note), "answer")],
            example=clips[(x2.exercises_note_key(note), "example")],
        )
        for note in notes
    }


async def build_pilot_apkg() -> dict[str, Any]:
    """Build and publish one mixed 30-note pilot through normal APKG delivery."""
    notes = pilot_notes()
    settings = get_settings()
    audio = await completed_audio_for_notes(notes, data_dir=Path(settings.data_dir))
    out = (
        Path(settings.data_dir) / "apkgs" / PILOT_DELIVERY_LANG
        / "_exercises2_local_qwen_pilot_v1.apkg"
    )
    n = await asyncio.to_thread(
        x2.build_exercises2_mixed_apkg,
        out_path=out, notes=notes, audio=audio,
    )
    relative = out.relative_to(Path(settings.data_dir))
    apkg_id = await db.upsert_pool_apkg(
        lang=PILOT_DELIVERY_LANG, kind=PILOT_APKG_KIND,
        filename=str(relative), size_bytes=out.stat().st_size, n_idioms=n,
    )
    return {
        "pilot": True,
        "notes": n,
        "cards": n * 2,
        "languages": sorted({note.lang for note in notes}),
        "model_id": x2.MODEL_ID,
        "apkg_id": apkg_id,
        "filename": str(relative),
        "delivery_lang": PILOT_DELIVERY_LANG,
        "kind": PILOT_APKG_KIND,
    }


async def rebuild_exercises2_language(lang: str) -> dict[str, Any]:
    """Strictly rebuild one full rolling deck from completed local clips."""
    require_bulk_approval()
    if lang not in x2.SUPPORTED_LANGS:
        raise ValueError("lang must be de|es|fr|it|pt")
    notes = x2.load_notes(lang)
    if not notes:
        raise LocalTTSBuildError(f"no Exercises2 notes for {lang}")
    settings = get_settings()
    by_note_key = await completed_audio_for_notes(
        notes, data_dir=Path(settings.data_dir),
    )
    by_item_id = {
        note.item_id: by_note_key[x2.exercises_note_key(note)] for note in notes
    }
    out = Path(settings.data_dir) / "apkgs" / lang / "_exercises2.apkg"
    n = await asyncio.to_thread(
        x2.build_exercises2_apkg,
        out_path=out, lang=lang, notes=notes, audio=by_item_id,
    )
    relative = out.relative_to(Path(settings.data_dir))
    apkg_id = await db.upsert_pool_apkg(
        lang=lang, kind="exercises2", filename=str(relative),
        size_bytes=out.stat().st_size, n_idioms=n,
    )
    return {
        "pilot": False,
        "lang": lang,
        "notes": n,
        "cards": n * 2,
        "model_id": x2.MODEL_ID,
        "apkg_id": apkg_id,
        "filename": str(relative),
        "local_only": True,
    }
