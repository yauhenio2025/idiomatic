#!/usr/bin/env python3
"""Phase 5 draft: rename Mandarin/Pimsleur in place and collapse z-archive."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
from typing import Any

from _common import (
    add_copy_path_argument,
    card_state_rows,
    collection_invariants,
    display_deck_name,
    ensure_deck_journaled,
    journal_directory,
    read_only_connection,
    require_apply_flag,
    require_completed_phase,
    require_no_filtered_deck_cards,
    validated_copy_path,
    write_json,
)
from _mapping import (
    archive_card_destination,
    placement_rename_destination,
    placement_root_renames,
)
from _phase_runner import planned_moves, print_move_summary


def blob_hex(value: Any) -> str:
    return bytes(value or b"").hex()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    if args.apply:
        require_no_filtered_deck_cards(copy_path, "05_place_mandarin_pimsleur_archive")
        require_completed_phase(copy_path, args.journal_dir, "04_move_learning_families")

    archive_moves = planned_moves(copy_path, lambda deck, model: archive_card_destination(deck))
    connection = read_only_connection(copy_path)
    try:
        deck_rows = {
            display_deck_name(str(row["name"])): row
            for row in connection.execute("SELECT id,name,common,kind FROM decks")
        }
        renames = placement_root_renames(set(deck_rows))
        conflicts = {
            source: destination
            for source, destination in renames.items()
            if destination in deck_rows
        }
        if conflicts:
            raise RuntimeError(f"phase-5 rename destinations already exist: {conflicts}")

        deck_metadata: list[dict[str, Any]] = []
        expected_card_destinations: list[dict[str, Any]] = []
        cards_per_root: collections.Counter[str] = collections.Counter()
        for source, destination in sorted(renames.items()):
            for name, row in deck_rows.items():
                if name != source and not name.startswith(source + "::"):
                    continue
                suffix = name[len(source) :].lstrip(":")
                expected_name = destination + (f"::{suffix}" if suffix else "")
                deck_metadata.append(
                    {
                        "id": int(row["id"]),
                        "old_name": name,
                        "expected_name": expected_name,
                        "common_hex": blob_hex(row["common"]),
                        "kind_hex": blob_hex(row["kind"]),
                    }
                )
                for card in connection.execute(
                    "SELECT id FROM cards WHERE did=? ORDER BY id", (int(row["id"]),)
                ):
                    card_id = int(card["id"])
                    expected_card_destinations.append(
                        {"card_id": card_id, "destination": expected_name}
                    )
                    cards_per_root[source] += 1
        before = collection_invariants(connection)
        states = card_state_rows(
            connection, (int(move["card_id"]) for move in archive_moves)
        )
    finally:
        connection.close()

    print(f"metadata-preserving subtree renames: {len(renames):,}")
    for source, destination in sorted(renames.items()):
        print(f"  {cards_per_root[source]:>7,}  {source} -> {destination}")
    print("archive collapse:")
    print_move_summary(archive_moves)
    if not args.apply:
        print("DRY RUN: no decks or cards changed.")
        return

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    journal_path = (
        journal_directory(copy_path, args.journal_dir)
        / f"{stamp}_05_place_mandarin_pimsleur_archive.json"
    )
    journal = {
        "phase": "05_place_mandarin_pimsleur_archive",
        "created_at": stamp,
        "copy_path": str(copy_path),
        "status": "prepared",
        "before_invariants": before,
        "suspend_after_move": False,
        "suspended_card_ids": [],
        "card_states": states,
        "moves": archive_moves,
        "deck_renames": [
            {
                "source_id": int(deck_rows[source]["id"]),
                "old_name": source,
                "destination": destination,
            }
            for source, destination in sorted(renames.items())
        ],
        "deck_metadata": deck_metadata,
        "expected_card_destinations": expected_card_destinations,
        "created_decks": [],
    }
    write_json(journal_path, journal)

    from anki.collection import Collection

    collection = Collection(str(copy_path))
    try:
        for rename in journal["deck_renames"]:
            source_id = collection.decks.id_for_name(str(rename["old_name"]))
            if source_id is None:
                raise RuntimeError(f"source deck disappeared: {rename['old_name']}")
            if collection.decks.id_for_name(str(rename["destination"])) is not None:
                raise RuntimeError(f"rename destination appeared: {rename['destination']}")
            collection.decks.rename(int(source_id), str(rename["destination"]))

        destination_ids: dict[str, int] = {}
        for destination in sorted({str(move["destination"]) for move in archive_moves}):
            did, _ = ensure_deck_journaled(
                collection, destination, journal, journal_path
            )
            destination_ids[destination] = did
        grouped: dict[str, list[int]] = collections.defaultdict(list)
        for move in archive_moves:
            grouped[str(move["destination"])].append(int(move["card_id"]))
        for destination, card_ids in grouped.items():
            collection.set_deck(card_ids, destination_ids[destination])
    finally:
        collection.close(downgrade=False)

    after_connection = read_only_connection(copy_path)
    try:
        after = collection_invariants(after_connection)
        actual_metadata = {
            int(row["id"]): row
            for row in after_connection.execute("SELECT id,name,common,kind FROM decks")
        }
    finally:
        after_connection.close()
    if any(
        before[key] != after[key]
        for key in before
        if key != "deck_catalog_sha256"
    ):
        raise RuntimeError("phase 5 changed notes, scheduling, queues, or revlog")
    for expected in deck_metadata:
        actual = actual_metadata.get(int(expected["id"]))
        if actual is None:
            raise RuntimeError(f"renamed deck row disappeared: {expected['id']}")
        if (
            display_deck_name(str(actual["name"])) != expected["expected_name"]
            or blob_hex(actual["common"]) != expected["common_hex"]
            or blob_hex(actual["kind"]) != expected["kind_hex"]
        ):
            raise RuntimeError(f"renamed deck metadata changed: {expected['old_name']}")
    journal["after_invariants"] = after
    journal["status"] = "complete"
    write_json(journal_path, journal)
    print(
        f"Applied {len(expected_card_destinations):,} metadata-preserving placements and "
        f"{len(archive_moves):,} archive moves; journal: {journal_path}"
    )


if __name__ == "__main__":
    main()
