#!/usr/bin/env python3
"""Draft rollback for one completed phase journal; run journals newest-to-oldest."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from _common import (
    add_copy_path_argument,
    card_state_rows,
    collection_invariants,
    display_deck_name,
    ensure_deck,
    read_only_connection,
    require_no_filtered_deck_cards,
    validated_copy_path,
    validated_work_artifact,
    write_json,
)


def blob_hex(value: object) -> str:
    return bytes(value or b"").hex()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    parser.add_argument("--journal", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    journal_path = validated_work_artifact(args.journal, copy_path, "rollback journal")
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    if Path(journal["copy_path"]).resolve() != copy_path:
        raise SystemExit("journal belongs to a different collection copy")
    if journal.get("status") not in {"prepared", "complete", "rolling_back"}:
        raise SystemExit("journal status is not prepared, complete, or rolling_back")
    if journal.get("status") in {"prepared", "rolling_back"}:
        print("WARNING: resuming rollback from a potentially partial phase state.")

    active_journals: list[tuple[Path, dict]] = []
    for sibling in sorted(journal_path.parent.glob("*.json")):
        try:
            payload = json.loads(sibling.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            payload.get("status") in {"prepared", "complete", "rolling_back"}
            and Path(str(payload.get("copy_path", ""))).resolve() == copy_path
            and "phase" in payload
        ):
            active_journals.append((sibling, payload))
    if not active_journals or active_journals[-1][0] != journal_path:
        raise SystemExit("rollback must run newest active phase first")
    print(f"phase: {journal['phase']}")
    print(f"cards captured: {len(journal.get('card_states', [])):,}")
    print(f"tags captured: {len(journal.get('tags_added', {})):,}")
    print(f"subtrees captured: {len(journal.get('deck_renames', [])):,}")
    if not args.apply:
        print("DRY RUN: no rollback applied.")
        return
    require_no_filtered_deck_cards(copy_path, f"rollback of {journal['phase']}")

    # Resolve the entire rollback before making its first change. This prevents a
    # late conflict from leaving a half-rolled-back collection copy.
    planned_move_ids = {
        int(move["card_id"]) for move in journal.get("moves", [])
    }
    connection = read_only_connection(copy_path)
    try:
        if journal.get("status") == "complete":
            expected_after = journal.get("after_invariants")
            if not isinstance(expected_after, dict):
                raise RuntimeError("completed journal has no valid after-state invariants")
            if collection_invariants(connection) != expected_after:
                raise RuntimeError(
                    "collection drifted after this phase; refusing rollback before mutation"
                )
        decks_by_name = {
            display_deck_name(str(row["name"])): {
                "id": int(row["id"]),
                "common_hex": blob_hex(row["common"]),
                "kind_hex": blob_hex(row["kind"]),
            }
            for row in connection.execute("SELECT id,name,common,kind FROM decks")
        }
        decks_by_id = {row["id"]: name for name, row in decks_by_name.items()}
        cards = {
            int(row["id"]): display_deck_name(str(row["name"]))
            for row in connection.execute(
                "SELECT c.id,d.name FROM cards c JOIN decks d ON d.id=c.did"
            )
        }
        for move in journal.get("moves", []):
            card_id = int(move["card_id"])
            current = cards.get(card_id)
            allowed = {str(move["old_deck"]), str(move["destination"])}
            if current not in allowed:
                raise RuntimeError(
                    f"card {card_id} is in {current!r}, outside rollback states {sorted(allowed)!r}"
                )
        missing_state_cards = {
            int(row["id"]) for row in journal.get("card_states", [])
        } - set(cards)
        if missing_state_cards:
            raise RuntimeError(f"rollback cards disappeared: {sorted(missing_state_cards)[:10]}")

        created_decks = list(journal.get("created_decks", []))
        pending_name = journal.get("pending_deck_creation")
        if pending_name and not any(
            str(row["name"]) == str(pending_name) for row in created_decks
        ):
            pending = decks_by_name.get(str(pending_name))
            if pending is not None:
                created_decks.append(
                    {"id": int(pending["id"]), "name": str(pending_name)}
                )
        for row in created_decks:
            name = str(row["name"])
            current = decks_by_name.get(name)
            if current is None:
                continue
            if int(current["id"]) != int(row["id"]):
                raise RuntimeError(f"created deck ID changed before rollback: {name}")
            subtree_cards = {
                card_id
                for card_id, deck_name in cards.items()
                if deck_name == name or deck_name.startswith(name + "::")
            }
            unexpected = subtree_cards - planned_move_ids
            if unexpected:
                raise RuntimeError(
                    f"refusing to remove created deck with {len(unexpected)} unrelated cards: {name}"
                )

        for rename in journal.get("deck_renames", []):
            old_name = str(rename["old_name"])
            destination = str(rename["destination"])
            old = decks_by_name.get(old_name)
            new = decks_by_name.get(destination)
            if (old is None) == (new is None):
                raise RuntimeError(
                    f"rename rollback requires exactly one of {old_name!r}/{destination!r}"
                )
            current = old or new
            if int(current["id"]) != int(rename["source_id"]):
                raise RuntimeError(f"renamed deck ID changed before rollback: {old_name}")

        for row in reversed(journal.get("removed_decks", [])):
            name = str(row["name"])
            old_id = int(row["id"])
            present = decks_by_name.get(name)
            if present is not None and int(present["id"]) != old_id:
                raise RuntimeError(f"removed deck name was reused with another ID: {name}")
            occupying_name = decks_by_id.get(old_id)
            if present is None and occupying_name is not None:
                raise RuntimeError(
                    f"removed deck ID {old_id} is now occupied by {occupying_name}"
                )

        if "registered_tags_before" in journal:
            registered_now = {
                str(row[0]) for row in connection.execute("SELECT tag FROM tags")
            }
            missing_registered = set(journal["registered_tags_before"]) - registered_now
            if missing_registered:
                raise RuntimeError(
                    f"pre-phase registered tags disappeared: {sorted(missing_registered)[:10]}"
                )
    finally:
        connection.close()

    # Persist the rollback intent after the complete preflight but before the
    # first database mutation. A crash can then resume idempotently without
    # confusing its own partial rollback with unrelated post-phase drift.
    if journal.get("status") != "rolling_back":
        journal["pre_rollback_status"] = journal["status"]
        journal["status"] = "rolling_back"
        journal["rollback_started_at"] = dt.datetime.now(dt.UTC).strftime(
            "%Y%m%dT%H%M%S.%fZ"
        )
        write_json(journal_path, journal)

    from anki.collection import Collection

    collection = Collection(str(copy_path))
    try:
        if moves := journal.get("moves"):
            old_names = {int(move["card_id"]): str(move["old_deck"]) for move in moves}
            grouped: dict[str, list[int]] = {}
            for card_id, old_name in old_names.items():
                grouped.setdefault(old_name, []).append(card_id)
            for old_name, card_ids in grouped.items():
                old_did, _ = ensure_deck(collection, old_name)
                collection.set_deck(card_ids, old_did)

        newly_suspended = [int(card_id) for card_id in journal.get("suspended_card_ids", [])]
        if newly_suspended:
            collection.sched.unsuspend_cards(newly_suspended)

        for tag, note_ids in journal.get("tags_added", {}).items():
            collection.tags.bulk_remove(note_ids, tag)

        if "registered_tags_before" in journal:
            registered_before = set(journal["registered_tags_before"])
            extra_tags = set(collection.tags.all()) - registered_before
            for tag in sorted(extra_tags, key=lambda value: (value.count("::"), value), reverse=True):
                collection.tags.remove(tag)
            if set(collection.tags.all()) != registered_before:
                raise RuntimeError("registered tag catalog did not return to its pre-phase state")

        for row in reversed(journal.get("removed_decks", [])):
            if collection.decks.id_for_name(str(row["name"])) is None:
                legacy = row.get("legacy")
                if legacy is None:
                    raise RuntimeError(f"removed deck lacks exact rollback metadata: {row['name']}")
                collection.decks.update(legacy, preserve_usn=True)
        for row in journal.get("removed_decks", []):
            if collection.decks.get_legacy(int(row["id"])) != row.get("legacy"):
                raise RuntimeError(f"removed deck metadata was not exactly restored: {row['name']}")

        for rename in reversed(journal.get("deck_renames", [])):
            old_name = str(rename["old_name"])
            destination = str(rename["destination"])
            old_id = collection.decks.id_for_name(old_name)
            destination_id = collection.decks.id_for_name(destination)
            if old_id is not None and destination_id is None:
                continue
            if old_id is None and destination_id is not None:
                collection.decks.rename(int(destination_id), old_name)
                continue
            raise RuntimeError(f"rename state changed during rollback: {old_name}")

        for row in reversed(created_decks):
            did = collection.decks.id_for_name(str(row["name"]))
            if did is None:
                continue
            if collection.find_cards(f'did:{int(did)}'):
                raise RuntimeError(f"refusing to remove nonempty created deck {row['name']}")
            collection.decks.remove([int(did)])
    finally:
        collection.close(downgrade=False)

    after_connection = read_only_connection(copy_path)
    try:
        after = collection_invariants(after_connection)
        states = journal.get("card_states", [])
        restored_states = card_state_rows(
            after_connection, (int(row["id"]) for row in states)
        )
        restored_deck_metadata = {
            int(row["id"]): row
            for row in after_connection.execute("SELECT id,name,common,kind FROM decks")
        }
    finally:
        after_connection.close()
    if after != journal.get("before_invariants"):
        raise RuntimeError("rollback result does not match the phase's complete pre-state")
    if restored_states != states:
        raise RuntimeError("rollback did not exactly restore captured card states")
    for expected in journal.get("deck_metadata", []):
        actual = restored_deck_metadata.get(int(expected["id"]))
        if actual is None or (
            display_deck_name(str(actual["name"])) != str(expected["old_name"])
            or blob_hex(actual["common"]) != str(expected["common_hex"])
            or blob_hex(actual["kind"]) != str(expected["kind_hex"])
        ):
            raise RuntimeError(
                f"rollback did not restore renamed deck metadata: {expected['old_name']}"
            )
    journal["status"] = "rolled_back"
    journal["rolled_back_at"] = dt.datetime.now(dt.UTC).strftime(
        "%Y%m%dT%H%M%S.%fZ"
    )
    write_json(journal_path, journal)
    print("Rollback applied. Run 10_verify.py against the preceding baseline journal.")


if __name__ == "__main__":
    main()
