#!/usr/bin/env python3
"""Reusable runner for card-move phases on a validated copy."""

from __future__ import annotations

import collections
import datetime as dt
from pathlib import Path
from typing import Any, Callable

from _common import (
    card_state_rows,
    collection_invariants,
    display_deck_name,
    ensure_deck_journaled,
    journal_directory,
    queue_state_fingerprint,
    read_only_connection,
    require_completed_phase,
    require_no_filtered_deck_cards,
    validated_copy_path,
    write_json,
)


Mapper = Callable[[str, str], str | None]
SuspendSelector = Callable[[str, str], bool]


def planned_moves(copy_path: Path, mapper: Mapper) -> list[dict[str, object]]:
    connection = read_only_connection(copy_path)
    try:
        return [
            {
                "card_id": row["card_id"],
                "note_id": row["note_id"],
                "old_deck_id": row["deck_id"],
                "old_deck": display_deck_name(row["deck_name"]),
                "model": row["model_name"],
                "queue": row["queue"],
                "destination": destination,
            }
            for row in connection.execute(
                """
                SELECT c.id AS card_id, c.nid AS note_id, c.did AS deck_id, c.queue,
                       d.name AS deck_name, nt.name AS model_name
                  FROM cards c
                  JOIN notes n ON n.id=c.nid
                  JOIN notetypes nt ON nt.id=n.mid
                  JOIN decks d ON d.id=c.did
                 ORDER BY c.id
                """
            )
            if (destination := mapper(display_deck_name(row["deck_name"]), row["model_name"]))
            and destination != display_deck_name(row["deck_name"])
        ]
    finally:
        connection.close()


def print_move_summary(moves: list[dict[str, object]]) -> None:
    by_destination = collections.Counter(str(move["destination"]) for move in moves)
    by_source = collections.Counter(str(move["old_deck"]) for move in moves)
    print(f"planned card moves: {len(moves):,}")
    print(f"source decks: {len(by_source):,}; destination decks: {len(by_destination):,}")
    for destination, count in sorted(by_destination.items()):
        print(f"  {count:>7,} -> {destination}")


def execute_move_phase(
    *,
    phase: str,
    copy_path: Path,
    mapper: Mapper,
    apply: bool,
    requested_journal_dir: Path | None,
    suspend_after_move: bool = False,
    required_phase: str | None = None,
    journal_metadata: dict[str, Any] | None = None,
    suspend_selector: SuspendSelector | None = None,
) -> None:
    copy_path = validated_copy_path(copy_path)
    if apply:
        require_no_filtered_deck_cards(copy_path, phase)
        if required_phase:
            require_completed_phase(copy_path, requested_journal_dir, required_phase)
    moves = planned_moves(copy_path, mapper)
    print_move_summary(moves)
    suspend_card_ids = {
        int(move["card_id"])
        for move in moves
        if suspend_after_move
        or (
            suspend_selector is not None
            and suspend_selector(str(move["old_deck"]), str(move["model"]))
        )
    }
    planned_new_suspensions = sum(
        int(move["card_id"]) in suspend_card_ids and int(move["queue"]) != -1
        for move in moves
    )
    if suspend_card_ids:
        print(
            f"planned task retirements: {len(suspend_card_ids):,}; "
            f"new suspensions: {planned_new_suspensions:,}"
        )
    if not apply:
        print("DRY RUN: add --apply only after owner approval and a fresh backup copy.")
        return
    before_connection = read_only_connection(copy_path)
    try:
        before = collection_invariants(before_connection)
        states = card_state_rows(before_connection, (int(move["card_id"]) for move in moves))
    finally:
        before_connection.close()

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    journal_dir = journal_directory(copy_path, requested_journal_dir)
    journal_path = journal_dir / f"{stamp}_{phase}.json"
    journal = {
        "phase": phase,
        "copy_path": str(copy_path),
        "created_at": stamp,
        "status": "prepared",
        "suspend_after_move": bool(suspend_card_ids),
        "suspension_mode": (
            "all" if suspend_after_move else "selected" if suspend_card_ids else "none"
        ),
        "before_invariants": before,
        "card_states": states,
        "suspended_card_ids": [
            int(row["id"])
            for row in states
            if int(row["id"]) in suspend_card_ids and int(row["queue"]) != -1
        ],
        "moves": moves,
        "created_decks": [],
    }
    journal.update(journal_metadata or {})
    write_json(journal_path, journal)

    from anki.collection import Collection

    if moves:
        collection = Collection(str(copy_path))
        try:
            destination_ids: dict[str, int] = {}
            for destination in sorted({str(move["destination"]) for move in moves}):
                parts = destination.split("::")
                did = 0
                for length in range(1, len(parts) + 1):
                    deck_name = "::".join(parts[:length])
                    did, _ = ensure_deck_journaled(
                        collection, deck_name, journal, journal_path
                    )
                destination_ids[destination] = did
            grouped: dict[str, list[int]] = collections.defaultdict(list)
            for move in moves:
                grouped[str(move["destination"])].append(int(move["card_id"]))
            for destination, card_ids in grouped.items():
                collection.set_deck(card_ids, destination_ids[destination])
            if suspend_card_ids:
                active_ids = [
                    row["id"]
                    for row in states
                    if int(row["id"]) in suspend_card_ids and row["queue"] != -1
                ]
                if active_ids:
                    collection.sched.suspend_cards(active_ids)
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
                if int(row["id"]) in suspend_card_ids
            },
        )
        if suspend_card_ids:
            after_states = card_state_rows(
                after_connection, sorted(suspend_card_ids)
            )
            if any(int(row["queue"]) != -1 for row in after_states):
                raise RuntimeError(f"not every intended card was suspended during {phase}")
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
            raise RuntimeError(f"invariant changed during {phase}: {key}")
    if restored_queue_hash != before["queue_state_sha256"]:
        raise RuntimeError(f"unexpected card queue change during {phase}")
    journal["after_invariants"] = after
    journal["status"] = "complete"
    write_json(journal_path, journal)
    print(
        f"Applied {len(moves):,} moves and {len(journal['suspended_card_ids']):,} "
        f"new suspensions; rollback journal: {journal_path}"
    )
