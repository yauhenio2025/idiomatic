#!/usr/bin/env python3
"""Phase 7 draft: tag exact surface collisions for later Hub reconciliation."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from _common import (
    add_copy_path_argument,
    chunks,
    collection_invariants,
    journal_directory,
    load_owner_decisions,
    read_only_connection,
    require_apply_flag,
    require_completed_phase,
    require_no_filtered_deck_cards,
    sha256_file,
    validated_copy_path,
    validated_work_artifact,
    write_json,
    write_noop_phase_journal,
)
from _duplicates import validate_collision_manifest


POLICIES = {"defer-to-hub-manifest", "keep-all"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--policy", required=True, choices=sorted(POLICIES))
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    manifest_path = validated_work_artifact(
        args.manifest, copy_path, "collision manifest"
    )
    manifest = validate_collision_manifest(copy_path, manifest_path)
    manifest_file_sha256 = sha256_file(manifest_path)
    _, decisions = load_owner_decisions(args.decisions, copy_path)
    if decisions["dedupe_policy"] != args.policy:
        raise SystemExit("--policy does not match the copy-local owner decision record")
    if args.apply:
        require_no_filtered_deck_cards(copy_path, "07_resolve_duplicates")
        require_completed_phase(copy_path, args.journal_dir, "06_discontinue_audio")
        _, phase_3 = require_completed_phase(
            copy_path, args.journal_dir, "03_move_expressions"
        )
        expected_manifest = {
            "collision_manifest_source_copy_sha256": manifest[
                "source_copy_sha256"
            ],
            "collision_manifest_content_sha256": manifest["content_sha256"],
            "collision_manifest_file_sha256": manifest_file_sha256,
        }
        mismatches = {
            key: (phase_3.get(key), expected)
            for key, expected in expected_manifest.items()
            if phase_3.get(key) != expected
        }
        if mismatches:
            raise RuntimeError(
                "phase 7 requires the exact collision manifest consumed by phase 3: "
                f"{mismatches}"
            )

    connection = read_only_connection(copy_path)
    try:
        before = collection_invariants(connection)
        for key, expected in manifest["identity_invariants"].items():
            if before[key] != expected:
                raise SystemExit(f"manifest identity mismatch: {key}")

        groups = [
            {
                "group_id": str(group["group_id"]),
                "language": str(group["language"]),
                "representation": str(group["representation"]),
                "categories": list(group["categories"]),
                "candidate_note_ids": sorted(
                    int(note["note_id"]) for note in group["notes"]
                ),
            }
            for group in manifest["groups"]
        ]
        candidate_note_ids = sorted(
            {
                note_id
                for group in groups
                for note_id in group["candidate_note_ids"]
            }
        )
        active_evidence_card_ids: list[int] = []
        existing_tags_by_note: dict[int, set[str]] = {}
        for note_chunk in chunks(candidate_note_ids):
            marks = ",".join("?" for _ in note_chunk)
            active_evidence_card_ids.extend(
                int(row[0])
                for row in connection.execute(
                    f"SELECT id FROM cards WHERE nid IN ({marks}) AND queue!=-1 ORDER BY id",
                    note_chunk,
                )
            )
            existing_tags_by_note.update(
                {
                    int(row["id"]): set(str(row["tags"]).strip().split())
                    for row in connection.execute(
                        f"SELECT id,tags FROM notes WHERE id IN ({marks})",
                        note_chunk,
                    )
                }
            )
        if active_evidence_card_ids:
            raise RuntimeError(
                "phase 7 requires phase 3 to archive and suspend every old hub task; "
                f"{len(active_evidence_card_ids):,} remain active"
            )
        registered_tags_before = [
            str(row[0]) for row in connection.execute("SELECT tag FROM tags ORDER BY tag")
        ]
    finally:
        connection.close()

    print(f"policy: {args.policy}")
    print(f"exact surface-collision groups: {len(groups):,}")
    print(f"retired evidence notes covered: {len(candidate_note_ids):,}")
    if args.policy == "keep-all":
        if args.apply:
            path = write_noop_phase_journal(
                copy_path=copy_path,
                requested_journal_dir=args.journal_dir,
                phase="07_resolve_duplicates",
                invariants=before,
                metadata={
                    "policy": args.policy,
                    "collision_manifest_source_copy_sha256": manifest[
                        "source_copy_sha256"
                    ],
                    "collision_manifest_content_sha256": manifest[
                        "content_sha256"
                    ],
                    "collision_manifest_file_sha256": manifest_file_sha256,
                    "resolution_role": "no automatic surface-collision grouping",
                },
            )
            print(f"Owner policy is keep-all; recorded no-op journal: {path}")
        else:
            print("Owner policy is keep-all; no mutation is permitted.")
        return

    tags_added = {}
    for group in groups:
        tag = f"estate::surface_collision::{group['group_id']}"
        note_ids = [
            note_id
            for note_id in group["candidate_note_ids"]
            if tag not in existing_tags_by_note.get(note_id, set())
        ]
        if note_ids:
            tags_added[tag] = note_ids
    assignments = sum(len(note_ids) for note_ids in tags_added.values())
    print(f"surface-collision tags to add: {len(tags_added):,}; assignments: {assignments:,}")
    if not args.apply:
        print("DRY RUN: no cards, notes, or decks changed.")
        return

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    journal_path = (
        journal_directory(copy_path, args.journal_dir)
        / f"{stamp}_07_resolve_duplicates.json"
    )
    journal = {
        "phase": "07_resolve_duplicates",
        "created_at": stamp,
        "copy_path": str(copy_path),
        "status": "prepared",
        "policy": args.policy,
        "resolution_role": (
            "surface collision evidence only; canonical identity is deferred to the "
            "sense-resolved Expression Hub manifest"
        ),
        "before_invariants": before,
        "card_states": [],
        "suspend_after_move": False,
        "suspended_card_ids": [],
        "moves": [],
        "created_decks": [],
        "tags_added": tags_added,
        "registered_tags_before": registered_tags_before,
        "surface_collision_groups": groups,
        "collision_manifest_source_copy_sha256": manifest[
            "source_copy_sha256"
        ],
        "collision_manifest_content_sha256": manifest["content_sha256"],
        "collision_manifest_file_sha256": manifest_file_sha256,
    }
    write_json(journal_path, journal)

    from anki.collection import Collection

    collection = Collection(str(copy_path))
    try:
        for tag, note_ids in tags_added.items():
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
        raise RuntimeError("surface-collision tags changed scheduling, content, or history")
    journal["after_invariants"] = after
    journal["status"] = "complete"
    write_json(journal_path, journal)
    print(f"Surface-collision evidence tags applied to copy; journal: {journal_path}")


if __name__ == "__main__":
    main()
