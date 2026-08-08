"""Committed, read-only legacy-estate audit manifest.

The source collection copy stays gitignored.  Only the checksummed audit
manifest is loaded into Postgres, where the dashboard can inspect it without
ever opening an Anki collection or acquiring an AnkiWeb credential.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "research"
    / "legacy_estate"
    / "manifest.json"
)
VERDICTS = frozenset({"import", "partial", "skip", "already-covered"})
_SHA256 = re.compile(r"[0-9a-f]{64}")


class LegacyEstateManifestError(ValueError):
    """The committed manifest does not satisfy the dashboard seed contract."""


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise LegacyEstateManifestError(f"snapshot.{field} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LegacyEstateManifestError(
            f"snapshot.{field} must be an ISO timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise LegacyEstateManifestError(f"snapshot.{field} must include a timezone")
    return parsed


def load_manifest(path: Path | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and minimally validate the generated audit artifact.

    The analyzer owns the detailed metric contract.  This loader checks the
    identity and fields needed to seed safely, rejecting duplicate paths or a
    malformed checksum before any database write is attempted.
    """

    source = Path(path) if path is not None else MANIFEST_PATH
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LegacyEstateManifestError(f"cannot load {source}: {exc}") from exc
    if not isinstance(payload, dict):
        raise LegacyEstateManifestError("manifest root must be an object")
    snapshot = payload.get("snapshot")
    rows = payload.get("rows")
    if not isinstance(snapshot, dict) or not isinstance(rows, list):
        raise LegacyEstateManifestError("manifest needs snapshot object and rows array")

    source_sha256 = snapshot.get("source_sha256")
    if not isinstance(source_sha256, str) or not _SHA256.fullmatch(source_sha256):
        raise LegacyEstateManifestError("snapshot.source_sha256 must be lowercase SHA-256")
    snapshot["audited_at_parsed"] = _timestamp(snapshot.get("audited_at"), "audited_at")
    totals = payload.get("totals")
    if not isinstance(totals, dict):
        raise LegacyEstateManifestError("manifest needs totals object")
    snapshot["totals"] = totals

    required = {
        "source_deck_id",
        "deck_path",
        "parent_path",
        "depth",
        "top_level",
        "lang",
        "direct_notes",
        "direct_cards",
        "direct_mature",
        "direct_reps",
        "direct_reviews",
        "direct_audio_notes",
        "direct_sound_tags",
        "direct_last_review",
        "subtree_notes",
        "subtree_cards",
        "subtree_mature",
        "subtree_reps",
        "subtree_reviews",
        "subtree_audio_notes",
        "subtree_sound_tags",
        "subtree_last_review",
        "note_models",
        "quality_flags",
        "overlap",
        "proposed_verdict",
        "proposal_reason",
    }
    paths: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise LegacyEstateManifestError(f"rows[{index}] must be an object")
        missing = required - row.keys()
        if missing:
            raise LegacyEstateManifestError(
                f"rows[{index}] missing {', '.join(sorted(missing))}"
            )
        deck_path = row["deck_path"]
        if not isinstance(deck_path, str) or not deck_path:
            raise LegacyEstateManifestError(f"rows[{index}].deck_path must be nonempty")
        if deck_path in paths:
            raise LegacyEstateManifestError(f"duplicate deck_path {deck_path!r}")
        paths.add(deck_path)
        if row["proposed_verdict"] not in VERDICTS:
            raise LegacyEstateManifestError(
                f"{deck_path}: invalid proposed_verdict {row['proposed_verdict']!r}"
            )
    return snapshot, rows
