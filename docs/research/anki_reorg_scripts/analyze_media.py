#!/usr/bin/env python3
"""Read-only media presence/orphan estimate against references in the copied DB.

This script has no deletion capability. It reads note fields from an immutable
collection copy and reads only names/stat metadata from ``--media-dir``.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from _common import (
    add_copy_path_argument,
    display_deck_name,
    read_only_connection,
    validated_copy_path,
    validated_output_path,
)
from _media import media_references


FIELD_SEPARATOR = "\x1f"
HASH_SUFFIX = re.compile(r"-[0-9a-fA-F]{40}(?=\.[^.]+$)")


def gibibytes(value: int) -> float:
    return value / (1024**3)


def extension(name: str) -> str:
    suffix = Path(name).suffix.casefold().lstrip(".")
    return suffix or "(none)"


def names_fingerprint(names: set[str]) -> str:
    digest = hashlib.sha256()
    for name in sorted(names):
        digest.update(name.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\n")
    return digest.hexdigest()


def validate_media_dir(raw: Path) -> Path:
    expanded = raw.expanduser()
    if expanded.is_symlink():
        raise SystemExit("media directory must not be a symlink")
    path = expanded.resolve(strict=True)
    if not path.is_dir() or path.name != "collection.media":
        raise SystemExit("--media-dir must name an actual collection.media directory")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    parser.add_argument("--media-dir", required=True, type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    media_dir = validate_media_dir(args.media_dir)
    json_out = validated_output_path(args.json_out, copy_path)
    markdown_out = (
        validated_output_path(args.markdown_out, copy_path) if args.markdown_out else None
    )

    connection = read_only_connection(copy_path)
    try:
        snapshot_ms = int(connection.execute("SELECT mod FROM col").fetchone()[0])
        references: collections.Counter[str] = collections.Counter()
        occurrences_by_note: dict[int, list[str]] = {}
        for row in connection.execute("SELECT id,flds FROM notes"):
            found = media_references(str(row["flds"]))
            if found:
                occurrences_by_note[int(row["id"])] = found
                references.update(found)
        unique_references = set(references)
    finally:
        connection.close()

    files: dict[str, dict[str, int]] = {}
    nonfiles = collections.Counter()
    with os.scandir(media_dir) as entries:
        for entry in entries:
            metadata = entry.stat(follow_symlinks=False)
            if stat.S_ISREG(metadata.st_mode):
                files[entry.name] = {
                    "bytes": int(metadata.st_size),
                    "mtime_ns": int(metadata.st_mtime_ns),
                }
            elif stat.S_ISDIR(metadata.st_mode):
                nonfiles["directories"] += 1
            elif stat.S_ISLNK(metadata.st_mode):
                nonfiles["symlinks"] += 1
            else:
                nonfiles["other"] += 1

    file_names = set(files)
    missing = unique_references - file_names
    raw_unreferenced = file_names - unique_references
    reserved = {name for name in raw_unreferenced if name.startswith("_")}
    snapshot_ns = snapshot_ms * 1_000_000
    post_snapshot = {
        name
        for name in raw_unreferenced - reserved
        if files[name]["mtime_ns"] > snapshot_ns
    }
    candidates = raw_unreferenced - reserved - post_snapshot
    referenced_families = {HASH_SUFFIX.sub("", name) for name in unique_references}
    collision_family = {
        name for name in candidates if HASH_SUFFIX.sub("", name) in referenced_families
    }

    def byte_sum(names: set[str]) -> int:
        return sum(files[name]["bytes"] for name in names)

    missing_details: list[dict[str, Any]] = []
    if missing:
        connection = read_only_connection(copy_path)
        try:
            fields_by_model: dict[int, list[str]] = collections.defaultdict(list)
            for row in connection.execute(
                "SELECT ntid,ord,name FROM fields ORDER BY ntid,ord"
            ):
                fields_by_model[int(row["ntid"])].append(str(row["name"]))
            for row in connection.execute(
                """
                SELECT n.id,n.mid,n.flds,nt.name AS model,
                       c.id AS card_id,c.ivl,c.reps,d.name AS deck,
                       COALESCE(rv.reviews,0) AS reviews
                  FROM notes n
                  JOIN notetypes nt ON nt.id=n.mid
                  LEFT JOIN cards c ON c.nid=n.id
                  LEFT JOIN decks d ON d.id=c.did
                  LEFT JOIN (SELECT cid,COUNT(*) AS reviews FROM revlog GROUP BY cid) rv
                         ON rv.cid=c.id
                 ORDER BY n.id,c.id
                """
            ):
                note_id = int(row["id"])
                if not set(occurrences_by_note.get(note_id, ())) & missing:
                    continue
                values = str(row["flds"]).split(FIELD_SEPARATOR)
                field_names = fields_by_model[int(row["mid"])]
                for index, value in enumerate(values):
                    for reference in set(media_references(value)) & missing:
                        missing_details.append(
                            {
                                "filename": reference,
                                "note_id": note_id,
                                "field": field_names[index] if index < len(field_names) else index,
                                "model": str(row["model"]),
                                "card_id": int(row["card_id"]) if row["card_id"] is not None else None,
                                "deck": display_deck_name(str(row["deck"])) if row["deck"] else None,
                                "interval": int(row["ivl"]) if row["ivl"] is not None else None,
                                "reps": int(row["reps"]) if row["reps"] is not None else None,
                                "reviews": int(row["reviews"]),
                            }
                        )
        finally:
            connection.close()

    scanned_at = dt.datetime.now(dt.UTC).isoformat()
    result = {
        "scanned_at_utc": scanned_at,
        "copy_path": str(copy_path),
        "collection_snapshot_ms": snapshot_ms,
        "media_dir": str(media_dir),
        "copy_references": {
            "occurrences": sum(references.values()),
            "unique": len(unique_references),
            "notes": len(occurrences_by_note),
        },
        "media_directory": {
            "regular_files": len(files),
            "bytes": byte_sum(file_names),
            **nonfiles,
        },
        "exact_present": len(unique_references & file_names),
        "missing": len(missing),
        "missing_details": missing_details,
        "raw_unreferenced": {
            "files": len(raw_unreferenced),
            "bytes": byte_sum(raw_unreferenced),
        },
        "excluded_reserved": {"files": len(reserved), "bytes": byte_sum(reserved)},
        "excluded_post_snapshot": {
            "files": len(post_snapshot),
            "bytes": byte_sum(post_snapshot),
        },
        "orphanable_upper_bound": {
            "files": len(candidates),
            "bytes": byte_sum(candidates),
            "names_sha256": names_fingerprint(candidates),
            "extensions": dict(
                sorted(collections.Counter(extension(name) for name in candidates).items())
            ),
        },
        "referenced_basename_family": {
            "files": len(collision_family),
            "bytes": byte_sum(collision_family),
        },
    }
    json_out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "## Generated read-only media estimate",
        "",
        f"Scanned at `{scanned_at}`. The copied collection snapshot is `{snapshot_ms}` ms since epoch.",
        "",
        "| Metric | Files | GiB |",
        "|---|---:|---:|",
        f"| Media directory | {len(files):,} | {gibibytes(byte_sum(file_names)):.3f} |",
        f"| Exact copied-DB references present | {len(unique_references & file_names):,} | — |",
        f"| Missing copied-DB references | {len(missing):,} | — |",
        f"| Raw unreferenced | {len(raw_unreferenced):,} | {gibibytes(byte_sum(raw_unreferenced)):.3f} |",
        f"| Excluded `_` static | {len(reserved):,} | {gibibytes(byte_sum(reserved)):.3f} |",
        f"| Excluded post-snapshot | {len(post_snapshot):,} | {gibibytes(byte_sum(post_snapshot)):.3f} |",
        f"| **Orphanable upper bound** | **{len(candidates):,}** | **{gibibytes(byte_sum(candidates)):.3f}** |",
        f"| Referenced basename family | {len(collision_family):,} | {gibibytes(byte_sum(collision_family)):.3f} |",
        "",
        "This is an upper bound, not permission to delete. The script reads no media content and has no deletion mode.",
    ]
    if missing_details:
        lines.extend(["", "Missing-reference details:", ""])
        for item in missing_details:
            lines.append(
                f"- `{item['filename']}` — note `{item['note_id']}`, field `{item['field']}`, "
                f"deck `{item['deck']}`, interval {item['interval']}, reps {item['reps']}, reviews {item['reviews']}."
            )
    markdown = "\n".join(lines) + "\n"
    if markdown_out:
        markdown_out.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")


if __name__ == "__main__":
    main()
