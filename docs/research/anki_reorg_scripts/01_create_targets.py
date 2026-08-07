#!/usr/bin/env python3
"""Phase 1 draft: create the proposed deck shells on a collection copy."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from _common import (
    add_copy_path_argument,
    collection_invariants,
    display_deck_name,
    ensure_deck_journaled,
    journal_directory,
    load_owner_decisions,
    read_only_connection,
    require_apply_flag,
    require_no_filtered_deck_cards,
    validated_copy_path,
    write_json,
    sha256_file,
)
from _mapping import (
    audio_card_destination,
    expression_card_destination,
    precreated_target_decks,
    learning_card_destination,
)


def with_parents(names: set[str]) -> set[str]:
    result: set[str] = set()
    for name in names:
        parts = name.split("::")
        result.update("::".join(parts[:length]) for length in range(1, len(parts) + 1))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    parser.add_argument("--decisions", required=True, type=Path)
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    decisions_path, decisions = load_owner_decisions(args.decisions, copy_path)
    if args.apply:
        require_no_filtered_deck_cards(copy_path, "01_create_targets")
    source_copy_sha256 = sha256_file(copy_path)

    connection = read_only_connection(copy_path)
    try:
        existing = {
            display_deck_name(row[0]) for row in connection.execute("SELECT name FROM decks")
        }
        destinations = set(precreated_target_decks())
        for row in connection.execute(
            """
            SELECT d.name, nt.name
              FROM cards c
              JOIN notes n ON n.id=c.nid
              JOIN decks d ON d.id=c.did
              JOIN notetypes nt ON nt.id=n.mid
            """
        ):
            source = display_deck_name(row[0])
            model = row[1]
            for mapper in (
                expression_card_destination,
                learning_card_destination,
                audio_card_destination,
            ):
                if destination := mapper(source, model):
                    destinations.add(destination)
        destinations = with_parents(destinations)
        missing = sorted(destinations - existing, key=str.casefold)
        before = collection_invariants(connection)
    finally:
        connection.close()

    print(f"target decks: {len(destinations):,}; missing shells: {len(missing):,}")
    for name in missing:
        print(f"  + {name}")
    if not args.apply:
        print("DRY RUN: no decks created.")
        return

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    journal_path = journal_directory(copy_path, args.journal_dir) / f"{stamp}_01_create_targets.json"
    journal = {
        "phase": "01_create_targets",
        "created_at": stamp,
        "copy_path": str(copy_path),
        "status": "prepared",
        "before_invariants": before,
        "created_decks": [],
        "source_copy_sha256": source_copy_sha256,
        "owner_decisions": decisions,
        "owner_decisions_sha256": sha256_file(decisions_path),
    }
    write_json(journal_path, journal)

    from anki.collection import Collection

    collection = Collection(str(copy_path))
    try:
        for name in missing:
            ensure_deck_journaled(collection, name, journal, journal_path)
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
        if key != "deck_catalog_sha256"
    ):
        raise RuntimeError("creating empty target decks changed collection scheduling invariants")
    journal["after_invariants"] = after
    journal["status"] = "complete"
    write_json(journal_path, journal)
    print(f"Created {len(journal['created_decks']):,} shells; journal: {journal_path}")


if __name__ == "__main__":
    main()
