#!/usr/bin/env python3
"""Shared safety and read-only helpers for the draft estate scripts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import datetime as dt
import tempfile
from pathlib import Path
from typing import Any, Iterable


LIVE_PROFILE_NAME = "evgeny@the-syllabus.com"
WORK_DIR_COMPONENT = "anki_reorg_work"
SQLITE_HEADER = b"SQLite format 3\x00"
DECK_SEPARATOR = "\x1f"
RESEARCH_DIRECTORY = Path(__file__).resolve().parent.parent
WORK_DIRECTORY = (RESEARCH_DIRECTORY / WORK_DIR_COMPONENT).resolve()
REQUIRED_OWNER_DECISIONS = {
    "deck_label_language": "code-plus-english",
    "native_branch_labels": "numbered-english",
    "personal_errors_branch": "6 My Errors",
    "dormant_root": "zz Dormant",
}


class SafetyError(RuntimeError):
    """Raised when a path could be a live Anki collection."""


def add_copy_path_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--copy-path",
        required=True,
        type=Path,
        help="Path to an extracted/decompressed collection COPY under anki_reorg_work.",
    )


def validated_copy_path(raw_path: Path) -> Path:
    """Return a resolved SQLite copy path, or refuse anything remotely live-like."""

    expanded = raw_path.expanduser()
    if LIVE_PROFILE_NAME.casefold() in str(expanded.absolute()).casefold():
        raise SafetyError("refusing a path containing the live syllabus profile")
    if expanded.is_symlink():
        raise SafetyError(f"copy path must not be a symlink: {expanded}")
    path = expanded.resolve(strict=True)
    if not path.is_file():
        raise SafetyError(f"copy path is not a regular file: {path}")

    if LIVE_PROFILE_NAME.casefold() in str(path).casefold():
        raise SafetyError("refusing a path containing the live syllabus profile")
    try:
        path.relative_to(WORK_DIRECTORY)
    except ValueError as error:
        raise SafetyError(f"refusing a path outside {WORK_DIRECTORY}") from error

    # Reject any conventional live Anki profile collection, not only the named one.
    folded_parts = [part.casefold() for part in path.parts]
    if "anki2" in folded_parts[:-2] and path.name.casefold().startswith("collection.anki"):
        raise SafetyError("refusing a collection path beneath an Anki2 profile")

    # A hard link inside the work directory would pass all path-string checks but
    # still write the live inode. Compare identities without opening the live DB.
    live_candidates = (
        Path.home()
        / ".var/app/net.ankiweb.Anki/data/Anki2"
        / LIVE_PROFILE_NAME
        / "collection.anki2",
        Path.home() / ".local/share/Anki2" / LIVE_PROFILE_NAME / "collection.anki2",
    )
    for live_path in live_candidates:
        try:
            if live_path.exists() and os.path.samefile(path, live_path):
                raise SafetyError("refusing a hard link to the live collection")
        except OSError as error:
            raise SafetyError(f"could not prove copy is distinct from {live_path}: {error}") from error

    with path.open("rb") as handle:
        if handle.read(len(SQLITE_HEADER)) != SQLITE_HEADER:
            raise SafetyError(f"copy is not an uncompressed SQLite collection: {path}")
    # immutable=1 deliberately ignores WAL/journal state. Refuse a copy whose
    # transaction state is not wholly contained in the main SQLite file.
    for suffix in ("-wal", "-journal"):
        sidecar = Path(f"{path}{suffix}")
        if sidecar.is_symlink() or (sidecar.exists() and sidecar.stat().st_size):
            raise SafetyError(f"refusing collection copy with active SQLite sidecar: {sidecar}")
    return path


def read_only_connection(copy_path: Path) -> sqlite3.Connection:
    """Open the copied collection with SQLite's immutable read-only URI."""

    path = validated_copy_path(copy_path)
    connection = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.create_collation(
        "unicase",
        lambda left, right: (left.casefold() > right.casefold())
        - (left.casefold() < right.casefold()),
    )
    return connection


def validated_output_path(raw_path: Path, copy_path: Path | None = None) -> Path:
    """Keep generated evidence under ``docs/research`` and away from the DB copy."""

    expanded = raw_path.expanduser()
    if expanded.is_symlink():
        raise SafetyError(f"output path must not be a symlink: {expanded}")
    path = expanded.resolve(strict=False)
    try:
        path.relative_to(RESEARCH_DIRECTORY)
    except ValueError as error:
        raise SafetyError(f"output path must remain under {RESEARCH_DIRECTORY}") from error
    if copy_path is not None and path == validated_copy_path(copy_path):
        raise SafetyError("output path must not overwrite the collection copy")
    if path.exists() and not path.is_file():
        raise SafetyError(f"output path is not a regular file: {path}")
    if not path.parent.exists() or not path.parent.is_dir():
        raise SafetyError(f"output parent directory does not exist: {path.parent}")
    return path


def display_deck_name(stored_name: str) -> str:
    """Convert Anki's database separator to the user-facing `::` separator."""

    return stored_name.replace(DECK_SEPARATOR, "::")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def query_fingerprint(connection: sqlite3.Connection, query: str) -> str:
    """Hash ordered query rows without loading the full result into memory."""

    digest = hashlib.sha256()
    for row in connection.execute(query):
        digest.update(json.dumps(tuple(row), ensure_ascii=False, separators=(",", ":")).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def queue_state_fingerprint(
    connection: sqlite3.Connection, overrides: dict[int, int] | None = None
) -> str:
    """Hash card queues, optionally substituting recorded pre-phase values."""

    overrides = overrides or {}
    digest = hashlib.sha256()
    for row in connection.execute("SELECT id,queue FROM cards ORDER BY id"):
        values = (int(row["id"]), overrides.get(int(row["id"]), int(row["queue"])))
        digest.update(json.dumps(values, separators=(",", ":")).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def collection_invariants(connection: sqlite3.Connection) -> dict[str, Any]:
    """Return identity/history fingerprints that deck moves must not alter."""

    scalar_queries = {
        "notes": "SELECT COUNT(*) FROM notes",
        "cards": "SELECT COUNT(*) FROM cards",
        "revlog": "SELECT COUNT(*) FROM revlog",
        "mature_cards": "SELECT COUNT(*) FROM cards WHERE ivl > 21",
        "card_reps": "SELECT COALESCE(SUM(reps), 0) FROM cards",
    }
    values = {
        key: connection.execute(query).fetchone()[0]
        for key, query in scalar_queries.items()
    }
    values.update(
        {
            # did and queue are omitted: moves change did; suspension intentionally changes queue.
            "schedule_core_sha256": query_fingerprint(
                connection,
                """SELECT id,nid,ord,type,due,ivl,factor,reps,lapses,left,
                                  odue,odid,flags,data
                             FROM cards ORDER BY id""",
            ),
            "queue_state_sha256": query_fingerprint(
                connection, "SELECT id,queue FROM cards ORDER BY id"
            ),
            "suspended_card_ids_sha256": query_fingerprint(
                connection,
                "SELECT id FROM cards WHERE queue=-1 ORDER BY id",
            ),
            "revlog_sha256": query_fingerprint(
                connection,
                """SELECT id,cid,usn,ease,ivl,lastIvl,factor,time,type
                             FROM revlog ORDER BY id""",
            ),
            "note_identity_sha256": query_fingerprint(
                connection,
                "SELECT id,guid,mid FROM notes ORDER BY id",
            ),
            # Tags change intentionally, while actual field content must never do so.
            "note_content_sha256": query_fingerprint(
                connection,
                "SELECT id,guid,mid,flds,sfld,csum,flags,data FROM notes ORDER BY id",
            ),
            "note_tags_sha256": query_fingerprint(
                connection,
                "SELECT id,tags FROM notes ORDER BY id",
            ),
            "lex_card_deck_sha256": query_fingerprint(
                connection,
                """SELECT c.id,n.id,n.guid,n.mid,c.did,d.name
                       FROM cards c JOIN notes n ON n.id=c.nid JOIN decks d ON d.id=c.did
                      WHERE d.name='Lex-Stage · German vocab/idiom mnemonics (prototype)'
                      ORDER BY c.id""",
            ),
            "deck_catalog_sha256": query_fingerprint(
                connection,
                "SELECT id,name FROM decks ORDER BY id",
            ),
            "tag_catalog_sha256": query_fingerprint(
                connection,
                "SELECT tag,usn,collapsed,hex(config) FROM tags ORDER BY tag",
            ),
        }
    )
    return values


def chunks(values: Iterable[int], size: int = 5_000) -> Iterable[list[int]]:
    chunk: list[int] = []
    for value in values:
        chunk.append(value)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def journal_directory(copy_path: Path, requested: Path | None) -> Path:
    """Resolve a journal directory and keep it inside the working-copy tree."""

    copy_path = validated_copy_path(copy_path)
    if requested and requested.expanduser().is_symlink():
        raise SafetyError("journal directory must not be a symlink")
    directory = requested.expanduser().resolve() if requested else copy_path.parent / "anki_reorg_journals"
    try:
        directory.relative_to(copy_path.parent)
    except ValueError as error:
        raise SafetyError(
            f"journal directory must remain under this copy tree: {copy_path.parent}"
        ) from error
    directory.mkdir(parents=True, exist_ok=True)
    if not directory.is_dir():
        raise SafetyError(f"journal path is not a directory: {directory}")
    return directory


def write_json(path: Path, payload: Any) -> None:
    """Atomically write deterministic JSON and durably replace the old journal."""

    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise SafetyError(f"JSON target must be a regular, non-symlink file: {path}")
    if not path.parent.is_dir():
        raise SafetyError(f"JSON target parent does not exist: {path.parent}")
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def validated_work_artifact(
    raw_path: Path,
    copy_path: Path,
    label: str,
    *,
    directory: bool = False,
) -> Path:
    """Resolve an input artifact beneath the selected collection-copy tree."""

    copy_path = validated_copy_path(copy_path)
    expanded = raw_path.expanduser()
    if expanded.is_symlink():
        raise SafetyError(f"{label} must not be a symlink")
    path = expanded.resolve(strict=True)
    try:
        path.relative_to(copy_path.parent)
    except ValueError as error:
        raise SafetyError(f"{label} must remain under {copy_path.parent}") from error
    if directory and not path.is_dir():
        raise SafetyError(f"{label} is not a directory: {path}")
    if not directory and not path.is_file():
        raise SafetyError(f"{label} is not a regular file: {path}")
    return path


def load_owner_decisions(raw_path: Path, copy_path: Path) -> tuple[Path, dict[str, Any]]:
    """Load a copy-local decision record and refuse unsupported structural choices."""

    path = validated_work_artifact(raw_path, copy_path, "owner decisions")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SafetyError(f"owner decisions are not valid JSON: {path}") from error
    if not isinstance(payload, dict):
        raise SafetyError("owner decisions must be a JSON object")
    for key, required in REQUIRED_OWNER_DECISIONS.items():
        if payload.get(key) != required:
            raise SafetyError(
                f"draft scripts implement {key}={required!r}; got {payload.get(key)!r}"
            )
    if payload.get("EXPERIMENTS-YT") not in {
        "merge_pt_fluency",
        "suspend_and_demote",
        "keep",
    }:
        raise SafetyError("invalid or missing EXPERIMENTS-YT owner decision")
    if payload.get("dedupe_policy") not in {
        "schedule-first",
        "canonical-model-first",
        "keep-all",
    }:
        raise SafetyError("invalid or missing dedupe_policy owner decision")
    return path, payload


def require_completed_phase(
    copy_path: Path, requested_journal_dir: Path | None, phase: str
) -> tuple[Path, dict[str, Any]]:
    """Refuse an apply run when its immediately preceding phase is incomplete."""

    copy_path = validated_copy_path(copy_path)
    directory = journal_directory(copy_path, requested_journal_dir)
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            payload.get("phase") == phase
            and payload.get("status") == "complete"
            and Path(str(payload.get("copy_path", ""))).resolve() == copy_path
        ):
            matches.append((path, payload))
    if not matches:
        raise SafetyError(f"apply requires a completed {phase} journal for this copy")
    return matches[-1]


def write_noop_phase_journal(
    *,
    copy_path: Path,
    requested_journal_dir: Path | None,
    phase: str,
    invariants: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Record an approved no-op so phase order remains reproducible."""

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    path = journal_directory(copy_path, requested_journal_dir) / f"{stamp}_{phase}.json"
    payload = {
        "phase": phase,
        "created_at": stamp,
        "copy_path": str(validated_copy_path(copy_path)),
        "status": "complete",
        "before_invariants": invariants,
        "after_invariants": invariants,
        "card_states": [],
        "suspended_card_ids": [],
        "created_decks": [],
        "moves": [],
        "tags_added": {},
    }
    payload.update(metadata or {})
    write_json(path, payload)
    return path


def card_state_rows(connection: sqlite3.Connection, card_ids: Iterable[int]) -> list[dict[str, int]]:
    """Capture scheduling-sensitive card state for a rollback journal."""

    rows: list[dict[str, int]] = []
    for card_chunk in chunks(card_ids):
        marks = ",".join("?" for _ in card_chunk)
        query = f"""
            SELECT id, nid, did, ord, type, queue, due, ivl, factor, reps,
                   lapses, left, odue, odid, flags
              FROM cards
             WHERE id IN ({marks})
             ORDER BY id
        """
        rows.extend(dict(row) for row in connection.execute(query, card_chunk))
    return rows


def require_apply_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually mutate the validated copy. Without this flag, print a dry-run.",
    )
    parser.add_argument(
        "--journal-dir",
        type=Path,
        help="Rollback-journal directory (must be under anki_reorg_work).",
    )


def ensure_deck(collection: Any, name: str) -> tuple[int, bool]:
    """Get or create a normal deck through Anki's public deck APIs."""

    existing = collection.decks.id_for_name(name)
    if existing is not None:
        return int(existing), False
    deck = collection.decks.new_deck()
    deck.name = name
    result = collection.decks.add_deck(deck)
    return int(result.id), True
