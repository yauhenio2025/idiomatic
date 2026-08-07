#!/usr/bin/env python3
"""Conservative semantic-key helpers for the estate duplicate drafts."""

from __future__ import annotations

import collections
import hashlib
import html
import json
import re
import sqlite3
import unicodedata
from typing import Any, Iterable

from pathlib import Path

from _common import (
    collection_invariants,
    display_deck_name,
    read_only_connection,
    validated_copy_path,
    validated_work_artifact,
)
from _mapping import EXPRESSION_MODELS, LANGUAGES, SENTENCE_MODELS, active_language_for_deck


FIELD_SEPARATOR = "\x1f"
MEDIA = re.compile(r"\[sound:[^\]]+\]", re.IGNORECASE)
HTML_TAG = re.compile(r"<[^>]+>")
TYPOGRAPHIC_TRANSLATION = str.maketrans(
    {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"}
)
CLOUD_V1_MODEL = "Idiomatic Cloud Card v1"
CANDIDATE_MODELS = SENTENCE_MODELS | EXPRESSION_MODELS | {CLOUD_V1_MODEL}


def normalize_visible(value: str) -> str:
    """Normalize conservatively while preserving accents and punctuation."""

    value = MEDIA.sub(" ", value)
    value = HTML_TAG.sub(" ", value)
    value = html.unescape(value)
    value = unicodedata.normalize("NFKC", value).translate(TYPOGRAPHIC_TRANSLATION)
    return " ".join(value.split()).casefold()


def field_ordinals(connection: sqlite3.Connection) -> dict[int, dict[str, int]]:
    result: dict[int, dict[str, int]] = collections.defaultdict(dict)
    for row in connection.execute("SELECT ntid, ord, name FROM fields ORDER BY ntid, ord"):
        result[int(row["ntid"])][str(row["name"])] = int(row["ord"])
    return dict(result)


def semantic_fields(model: str) -> tuple[str, str, str] | None:
    if model == CLOUD_V1_MODEL:
        return "expression", "Phrase", "English"
    if model in SENTENCE_MODELS:
        return "sentence", "Target", "English"
    if model in EXPRESSION_MODELS:
        return "expression", "Idiom", "IdiomEn"
    return None


def source_lane(deck: str, model: str) -> tuple[str, str] | None:
    """Return ``(language code, lane)`` while the original deck tree exists."""

    if deck.startswith("Idiomatic::z-archive::") and model in {
        CLOUD_V1_MODEL,
        "Idiomatic Cloud Card v2",
    }:
        parts = deck.split("::")
        if len(parts) >= 3 and parts[2] in LANGUAGES:
            return parts[2], "idiomatic_source_archive"
        return None

    language = active_language_for_deck(deck)
    if language is None or model not in CANDIDATE_MODELS:
        return None
    if deck.startswith("Languages::"):
        return language.code, "legacy"
    if deck in {
        f"Idiomatic::{language.english}::Idioms",
        f"Idiomatic::{language.english}::Fluency Expressions",
    }:
        return language.code, "idiomatic_pool"
    if deck.startswith(f"Idiomatic::{language.english}::"):
        leaf = deck.rsplit("::", 1)[-1]
        if not leaf.startswith("Idioms Audio"):
            return language.code, "idiomatic_source_video"
    return None


def collect_candidate_notes(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Collect active semantic notes plus Cloud source/archive notes."""

    ordinals = field_ordinals(connection)
    records: dict[int, dict[str, Any]] = {}
    query = """
        SELECT n.id AS note_id, n.mid, n.flds, nt.name AS model,
               c.id AS card_id, c.ivl, c.reps, c.queue,
               d.name AS deck,
               COALESCE(rv.reviews, 0) AS reviews
          FROM notes n
          JOIN notetypes nt ON nt.id=n.mid
          JOIN cards c ON c.nid=n.id
          JOIN decks d ON d.id=c.did
          LEFT JOIN (SELECT cid, COUNT(*) AS reviews FROM revlog GROUP BY cid) rv
                 ON rv.cid=c.id
         ORDER BY n.id, c.id
    """
    for row in connection.execute(query):
        model = str(row["model"])
        fields = semantic_fields(model)
        deck = display_deck_name(str(row["deck"]))
        lane = source_lane(deck, model)
        if fields is None or lane is None:
            continue
        representation, target_name, english_name = fields
        field_map = ordinals[int(row["mid"])]
        if target_name not in field_map or english_name not in field_map:
            raise RuntimeError(f"missing semantic field on {model}: {target_name}/{english_name}")
        values = str(row["flds"]).split(FIELD_SEPARATOR)
        raw_target = values[field_map[target_name]]
        raw_english = values[field_map[english_name]]
        target = normalize_visible(raw_target)
        english = normalize_visible(raw_english)
        if not target or not english:
            continue
        note_id = int(row["note_id"])
        record = records.setdefault(
            note_id,
            {
                "note_id": note_id,
                "language": lane[0],
                "lane": lane[1],
                "representation": representation,
                "target": target,
                "english": english,
                "raw_target": raw_target,
                "raw_english": raw_english,
                "model": model,
                "source_decks": [],
                "cards": [],
            },
        )
        identity = (
            record["language"],
            record["lane"],
            record["representation"],
            record["target"],
            record["english"],
            record["model"],
        )
        expected = (lane[0], lane[1], representation, target, english, model)
        if identity != expected:
            raise RuntimeError(f"note {note_id} crosses semantic lanes; manual review required")
        if deck not in record["source_decks"]:
            record["source_decks"].append(deck)
        record["cards"].append(
            {
                "card_id": int(row["card_id"]),
                "ivl": int(row["ivl"]),
                "reps": int(row["reps"]),
                "reviews": int(row["reviews"]),
                "queue": int(row["queue"]),
            }
        )
    return list(records.values())


def collision_groups(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = collections.defaultdict(list)
    for record in records:
        key = (
            str(record["language"]),
            str(record["representation"]),
            str(record["target"]),
            str(record["english"]),
        )
        grouped[key].append(record)

    collisions: list[dict[str, Any]] = []
    for key, notes in grouped.items():
        lanes = {str(note["lane"]) for note in notes}
        has_legacy = "legacy" in lanes
        has_idiomatic = any(lane.startswith("idiomatic_") for lane in lanes)
        has_pool = "idiomatic_pool" in lanes
        has_source = bool(
            lanes & {"idiomatic_source_video", "idiomatic_source_archive"}
        )
        categories = []
        if has_legacy and has_idiomatic:
            categories.append("legacy_vs_idiomatic")
        if has_pool and has_source:
            categories.append("idiomatic_source_vs_pool")
        if not categories:
            continue
        language, representation, target, english = key
        group_id = hashlib.sha256(
            json.dumps(key, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:16]
        collisions.append(
            {
                "group_id": group_id,
                "language": language,
                "representation": representation,
                "target": target,
                "english": english,
                "categories": categories,
                "notes": sorted(notes, key=lambda note: int(note["note_id"])),
            }
        )
    return sorted(
        collisions,
        key=lambda group: (
            str(group["language"]),
            str(group["representation"]),
            str(group["target"]),
            str(group["english"]),
        ),
    )


def collision_content_fingerprint(groups: Iterable[dict[str, Any]]) -> str:
    rows: set[tuple[int, str, str, str]] = set()
    for group in groups:
        for note in group["notes"]:
            rows.add(
                (
                    int(note["note_id"]),
                    str(note["representation"]),
                    str(note["target"]),
                    str(note["english"]),
                )
            )
    payload = json.dumps(sorted(rows), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def current_content_fingerprint(
    connection: sqlite3.Connection, expected_notes: Iterable[dict[str, Any]]
) -> str:
    """Re-read semantic fields by note ID after deck moves and fingerprint them."""

    ordinals = field_ordinals(connection)
    rows: list[tuple[int, str, str, str]] = []
    for expected in sorted(expected_notes, key=lambda note: int(note["note_id"])):
        row = connection.execute(
            """SELECT n.id, n.mid, n.flds, nt.name AS model
                 FROM notes n JOIN notetypes nt ON nt.id=n.mid WHERE n.id=?""",
            (int(expected["note_id"]),),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"collision note disappeared: {expected['note_id']}")
        fields = semantic_fields(str(row["model"]))
        if fields is None:
            raise RuntimeError(f"collision note model changed: {expected['note_id']}")
        representation, target_name, english_name = fields
        values = str(row["flds"]).split(FIELD_SEPARATOR)
        field_map = ordinals[int(row["mid"])]
        rows.append(
            (
                int(row["id"]),
                representation,
                normalize_visible(values[field_map[target_name]]),
                normalize_visible(values[field_map[english_name]]),
            )
        )
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_collision_manifest(copy_path: Path, manifest_path: Path) -> dict[str, Any]:
    """Validate a pre-collapse collision manifest against stable copy identity/content."""

    copy_path = validated_copy_path(copy_path)
    path = validated_work_artifact(
        manifest_path, copy_path, "collision manifest"
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise RuntimeError("unsupported collision-manifest schema")
    connection = read_only_connection(copy_path)
    try:
        invariants = collection_invariants(connection)
        for key, expected in manifest["identity_invariants"].items():
            if invariants[key] != expected:
                raise RuntimeError(f"collision manifest identity mismatch: {key}")
        unique_notes = {
            int(note["note_id"]): note
            for group in manifest["groups"]
            for note in group["notes"]
        }
        if current_content_fingerprint(connection, unique_notes.values()) != manifest[
            "content_sha256"
        ]:
            raise RuntimeError("collision manifest semantic content no longer matches")
    finally:
        connection.close()
    return manifest
