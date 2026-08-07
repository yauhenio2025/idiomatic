#!/usr/bin/env python3
"""Provenance requirements that must be satisfied before deck collapse."""

from __future__ import annotations

import collections
import hashlib
import re
import sqlite3
from pathlib import Path

from _common import display_deck_name, read_only_connection, validated_copy_path
from _mapping import LANGUAGES, active_language_for_deck


FIELD_SEPARATOR = "\x1f"
YOUTUBE_URL = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})")


def is_video_source_deck(name: str) -> bool:
    if name.startswith("Idiomatic::z-archive"):
        parts = name.split("::")
        return len(parts) >= 4 and parts[2].casefold() in LANGUAGES
    language = active_language_for_deck(name)
    if language is None:
        return False
    if name.startswith(f"Idiomatic::{language.english}::"):
        leaf = name.rsplit("::", 1)[-1]
        return leaf not in {
            "Fluency Expressions",
            "Idioms",
            "Idioms Audio (EN → target)",
            "Idioms Audio (target → EN)",
        }
    return "::YouTube" in name or "::Porta dos Fundos" in name


def source_field_ord(connection: sqlite3.Connection, mid: int) -> int | None:
    row = connection.execute(
        "SELECT ord FROM fields WHERE ntid=? AND name='Source'", (mid,)
    ).fetchone()
    return int(row[0]) if row else None


def provenance_plan(
    connection: sqlite3.Connection,
) -> tuple[dict[int, set[str]], dict[str, str]]:
    """Return missing tags by note and the complete origin-tag legend."""

    source_ords = {
        int(mid): source_field_ord(connection, int(mid))
        for (mid,) in connection.execute("SELECT id FROM notetypes")
    }
    note_tags: dict[int, set[str]] = collections.defaultdict(set)
    origin_map: dict[str, str] = {}
    for row in connection.execute(
        """
        SELECT DISTINCT n.id, n.mid, n.tags, n.flds, d.name
          FROM notes n
          JOIN cards c ON c.nid=n.id
          JOIN decks d ON d.id=c.did
        """
    ):
        deck = display_deck_name(str(row["name"]))
        if not is_video_source_deck(deck):
            continue
        if deck.startswith("Idiomatic::z-archive::"):
            language = LANGUAGES.get(deck.split("::")[2].casefold())
        else:
            language = active_language_for_deck(deck)
        if language is None:
            continue
        existing = set(str(row["tags"]).strip().split())
        wanted = {"youtube", f"lang::{language.code}"}
        source_ord = source_ords.get(int(row["mid"]))
        if source_ord is not None:
            fields = str(row["flds"]).split(FIELD_SEPARATOR)
            if source_ord < len(fields) and (match := YOUTUBE_URL.search(fields[source_ord])):
                wanted.add(f"source::youtube::{match.group(1)}")
        origin_key = hashlib.sha1(deck.encode("utf-8")).hexdigest()[:12]
        origin_tag = f"estate::origin::{origin_key}"
        wanted.add(origin_tag)
        origin_map[origin_tag] = deck
        note_tags[int(row["id"])].update(wanted - existing)
    return ({nid: tags for nid, tags in note_tags.items() if tags}, origin_map)


def assert_provenance_complete(copy_path: Path) -> None:
    """Refuse per-video collapse if any source note still lacks required tags."""

    copy_path = validated_copy_path(copy_path)
    connection = read_only_connection(copy_path)
    try:
        missing, _ = provenance_plan(connection)
    finally:
        connection.close()
    if missing:
        missing_assignments = sum(len(tags) for tags in missing.values())
        raise RuntimeError(
            f"provenance precondition failed: {len(missing):,} notes lack "
            f"{missing_assignments:,} required tag assignments"
        )
