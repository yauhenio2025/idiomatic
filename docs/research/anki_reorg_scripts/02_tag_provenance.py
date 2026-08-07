#!/usr/bin/env python3
"""Phase 2 draft: add normalized language/video/origin tags before deck collapse."""

from __future__ import annotations

import argparse
import collections
import datetime as dt

from _common import (
    add_copy_path_argument,
    collection_invariants,
    journal_directory,
    read_only_connection,
    require_apply_flag,
    require_completed_phase,
    validated_copy_path,
    write_json,
)
from _provenance import provenance_plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    if args.apply:
        require_completed_phase(copy_path, args.journal_dir, "01_create_targets")

    connection = read_only_connection(copy_path)
    try:
        note_tags, origin_map = provenance_plan(connection)
        before = collection_invariants(connection)
        registered_tags_before = [
            str(row[0]) for row in connection.execute("SELECT tag FROM tags ORDER BY tag")
        ]
    finally:
        connection.close()

    by_tag: dict[str, list[int]] = collections.defaultdict(list)
    for nid, tags in note_tags.items():
        for tag in tags:
            by_tag[tag].append(nid)
    print(f"notes gaining provenance tags: {len(note_tags):,}")
    print(f"distinct tags to add: {len(by_tag):,}; origin mappings: {len(origin_map):,}")
    if not args.apply:
        print("DRY RUN: no note tags changed.")
        return

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    journal_path = journal_directory(copy_path, args.journal_dir) / f"{stamp}_02_tag_provenance.json"
    journal = {
        "phase": "02_tag_provenance",
        "created_at": stamp,
        "copy_path": str(copy_path),
        "status": "prepared",
        "before_invariants": before,
        "tags_added": {tag: sorted(note_ids) for tag, note_ids in sorted(by_tag.items())},
        "origin_tag_to_deck": dict(sorted(origin_map.items())),
        "registered_tags_before": registered_tags_before,
    }
    write_json(journal_path, journal)

    from anki.collection import Collection

    collection = Collection(str(copy_path))
    try:
        for tag, note_ids in sorted(by_tag.items()):
            collection.tags.bulk_add(note_ids, tag)
    finally:
        collection.close(downgrade=False)

    after_connection = read_only_connection(copy_path)
    try:
        after = collection_invariants(after_connection)
    finally:
        after_connection.close()
    if any(
        before[key] != after[key]
        for key in before
        if key not in {"note_tags_sha256", "tag_catalog_sha256"}
    ):
        raise RuntimeError("provenance tags changed card identity, scheduling, or revlog")
    journal["after_invariants"] = after
    journal["status"] = "complete"
    write_json(journal_path, journal)
    print(f"Tagged {len(note_tags):,} notes; journal: {journal_path}")


if __name__ == "__main__":
    main()
