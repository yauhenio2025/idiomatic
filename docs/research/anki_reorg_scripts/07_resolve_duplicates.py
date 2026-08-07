#!/usr/bin/env python3
"""Phase 7 draft: suspend/link exact duplicate losers without deleting history."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
from pathlib import Path
from typing import Any

from _common import (
    add_copy_path_argument,
    card_state_rows,
    collection_invariants,
    ensure_deck,
    journal_directory,
    load_owner_decisions,
    queue_state_fingerprint,
    read_only_connection,
    require_apply_flag,
    require_completed_phase,
    validated_copy_path,
    write_json,
    write_noop_phase_journal,
)
from _duplicates import validate_collision_manifest
from _mapping import LANGUAGES


POLICIES = {"schedule-first", "canonical-model-first", "keep-all"}


def note_schedule(connection, note_id: int) -> dict[str, int]:
    row = connection.execute(
        """
        SELECT COUNT(c.id) AS cards,
               COALESCE(SUM(c.reps), 0) AS reps,
               COALESCE(SUM(rv.reviews), 0) AS reviews,
               COALESCE(SUM(c.ivl > 21), 0) AS mature,
               COALESCE(MAX(c.ivl), 0) AS max_ivl
          FROM cards c
          LEFT JOIN (SELECT cid, COUNT(*) AS reviews FROM revlog GROUP BY cid) rv
                 ON rv.cid=c.id
         WHERE c.nid=?
        """,
        (note_id,),
    ).fetchone()
    return {key: int(row[key]) for key in ("cards", "reps", "reviews", "mature", "max_ivl")}


def winner_key(note: dict[str, Any], policy: str) -> tuple[int, ...]:
    schedule = note["current_schedule"]
    history = (
        schedule["reviews"],
        schedule["reps"],
        schedule["mature"],
        schedule["max_ivl"],
    )
    lane = str(note["lane"])
    canonical = int(lane == "idiomatic_pool")
    if policy == "canonical-model-first":
        return (canonical, *history, -int(note["note_id"]))
    return (*history, canonical, -int(note["note_id"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--policy", required=True, choices=sorted(POLICIES))
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    manifest = validate_collision_manifest(copy_path, args.manifest)
    _, decisions = load_owner_decisions(args.decisions, copy_path)
    if decisions["dedupe_policy"] != args.policy:
        raise SystemExit("--policy does not match the copy-local owner decision record")
    if args.apply:
        require_completed_phase(copy_path, args.journal_dir, "06_discontinue_audio")

    connection = read_only_connection(copy_path)
    try:
        before = collection_invariants(connection)
        for key, expected in manifest["identity_invariants"].items():
            if before[key] != expected:
                raise SystemExit(f"manifest identity mismatch: {key}")
        unique_notes = {
            int(note["note_id"]): note
            for group in manifest["groups"]
            for note in group["notes"]
        }
        for note in unique_notes.values():
            note["current_schedule"] = note_schedule(connection, int(note["note_id"]))

        resolutions = []
        loser_note_ids: set[int] = set()
        winner_note_ids: set[int] = set()
        promoted_card_ids: dict[int, str] = {}
        for group in manifest["groups"]:
            notes = [unique_notes[int(note["note_id"])] for note in group["notes"]]
            winner = max(notes, key=lambda note: winner_key(note, args.policy))
            losers = [note for note in notes if note is not winner]
            winner_note_ids.add(int(winner["note_id"]))
            loser_note_ids.update(int(note["note_id"]) for note in losers)
            if str(winner["lane"]) == "idiomatic_source_archive":
                destination = f"{LANGUAGES[str(group['language'])].root}::1 Expressions::2 Expression Focus"
                for card in winner["cards"]:
                    promoted_card_ids[int(card["card_id"])] = destination
            resolutions.append(
                {
                    "group_id": group["group_id"],
                    "winner_note_id": int(winner["note_id"]),
                    "loser_note_ids": [int(note["note_id"]) for note in losers],
                    "winner_lane": winner["lane"],
                    "winner_schedule": winner["current_schedule"],
                }
            )
        loser_card_ids = [
            int(row[0])
            for note_id in sorted(loser_note_ids)
            for row in connection.execute("SELECT id FROM cards WHERE nid=? ORDER BY id", (note_id,))
        ]
        affected_card_ids = sorted(set(loser_card_ids) | set(promoted_card_ids))
        states = card_state_rows(connection, affected_card_ids)
        state_by_id = {int(row["id"]): row for row in states}
        deck_names = {
            int(row["id"]): str(row["name"]).replace("\x1f", "::")
            for row in connection.execute("SELECT id,name FROM decks")
        }
        moves = [
            {
                "card_id": card_id,
                "old_deck_id": int(state_by_id[card_id]["did"]),
                "old_deck": deck_names[int(state_by_id[card_id]["did"])],
                "destination": destination,
            }
            for card_id, destination in sorted(promoted_card_ids.items())
        ]
        registered_tags_before = [
            str(row[0]) for row in connection.execute("SELECT tag FROM tags ORDER BY tag")
        ]
        existing_tags_by_note = {
            int(row["id"]): set(str(row["tags"]).strip().split())
            for row in connection.execute(
                "SELECT id,tags FROM notes WHERE id IN (%s)"
                % ",".join("?" for _ in unique_notes),
                sorted(unique_notes),
            )
        }
    finally:
        connection.close()

    print(f"policy: {args.policy}")
    print(f"exact groups: {len(resolutions):,}")
    print(f"winner notes: {len(winner_note_ids):,}; loser notes: {len(loser_note_ids):,}")
    print(f"cards to suspend: {len(loser_card_ids):,}")
    print(f"reviewed archive cards to promote if selected: {len(promoted_card_ids):,}")
    if args.policy == "keep-all":
        if args.apply:
            path = write_noop_phase_journal(
                copy_path=copy_path,
                requested_journal_dir=args.journal_dir,
                phase="07_resolve_duplicates",
                invariants=before,
                metadata={"policy": args.policy, "manifest_content_sha256": manifest["content_sha256"]},
            )
            print(f"Owner policy is keep-all; recorded no-op journal: {path}")
        else:
            print("Owner policy is keep-all; no mutation is permitted.")
        return
    if not args.apply:
        print("DRY RUN: no cards, notes, or decks changed.")
        return

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    journal_path = journal_directory(copy_path, args.journal_dir) / f"{stamp}_07_resolve_duplicates.json"
    requested_tags: dict[str, list[int]] = {
        "estate::dedupe::winner": sorted(winner_note_ids),
        "estate::dedupe::suppressed": sorted(loser_note_ids),
    }
    for resolution in resolutions:
        group_tag = f"estate::dupe_group::{resolution['group_id']}"
        requested_tags[group_tag] = sorted(
            [resolution["winner_note_id"], *resolution["loser_note_ids"]]
        )
    tags_added = {
        tag: [
            note_id
            for note_id in note_ids
            if tag not in existing_tags_by_note.get(note_id, set())
        ]
        for tag, note_ids in requested_tags.items()
    }
    tags_added = {tag: note_ids for tag, note_ids in tags_added.items() if note_ids}
    journal = {
        "phase": "07_resolve_duplicates",
        "created_at": stamp,
        "copy_path": str(copy_path),
        "status": "prepared",
        "policy": args.policy,
        "suspend_after_move": True,
        "before_invariants": before,
        "card_states": states,
        "suspended_card_ids": sorted(
            int(row["id"])
            for row in states
            if int(row["id"]) in set(loser_card_ids) and int(row["queue"]) != -1
        ),
        "moves": moves,
        "created_decks": [],
        "tags_added": tags_added,
        "registered_tags_before": registered_tags_before,
        "resolutions": resolutions,
    }
    write_json(journal_path, journal)

    from anki.collection import Collection

    collection = Collection(str(copy_path))
    try:
        grouped_promotions: dict[str, list[int]] = collections.defaultdict(list)
        for card_id, destination in promoted_card_ids.items():
            grouped_promotions[destination].append(card_id)
        for destination, card_ids in grouped_promotions.items():
            destination_id, created = ensure_deck(collection, destination)
            if created:
                journal["created_decks"].append({"id": destination_id, "name": destination})
                write_json(journal_path, journal)
            collection.set_deck(card_ids, destination_id)
        active_losers = [
            int(row["id"])
            for row in states
            if int(row["id"]) in set(loser_card_ids) and int(row["queue"]) != -1
        ]
        if active_losers:
            collection.sched.suspend_cards(active_losers)
        for tag, note_ids in tags_added.items():
            collection.tags.bulk_add(note_ids, tag)
        write_json(journal_path, journal)
    finally:
        collection.close(downgrade=False)

    after_connection = read_only_connection(copy_path)
    try:
        after = collection_invariants(after_connection)
        restored_queue_hash = queue_state_fingerprint(
            after_connection,
            {
                int(row["id"]): int(row["queue"])
                for row in states
                if int(row["id"]) in set(loser_card_ids)
            },
        )
        after_loser_states = card_state_rows(after_connection, loser_card_ids)
        if any(int(row["queue"]) != -1 for row in after_loser_states):
            raise RuntimeError("not every duplicate loser card was suspended")
    finally:
        after_connection.close()
    for key in (
        "notes",
        "cards",
        "revlog",
        "mature_cards",
        "card_reps",
        "schedule_core_sha256",
        "revlog_sha256",
        "note_identity_sha256",
        "note_content_sha256",
    ):
        if before[key] != after[key]:
            raise RuntimeError(f"invariant changed during duplicate resolution: {key}")
    if restored_queue_hash != before["queue_state_sha256"]:
        raise RuntimeError("unexpected card queue change during duplicate resolution")
    journal["after_invariants"] = after
    journal["status"] = "complete"
    write_json(journal_path, journal)
    print(f"Duplicate resolution applied to copy; journal: {journal_path}")


if __name__ == "__main__":
    main()
