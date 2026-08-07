#!/usr/bin/env python3
"""Phase 9 draft: remove only empty obsolete deck shells, deepest first."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from _common import (
    add_copy_path_argument,
    collection_invariants,
    display_deck_name,
    journal_directory,
    load_owner_decisions,
    read_only_connection,
    require_apply_flag,
    require_completed_phase,
    require_no_filtered_deck_cards,
    validated_copy_path,
    write_json,
)
from _mapping import DORMANT_ROOT, LANGUAGES, MANDARIN_ROOT


KEEP_EXACT = {
    "Default",
    "Custom Study Session",
    "Lex-Stage · German vocab/idiom mnemonics (prototype)",
    DORMANT_ROOT,
    MANDARIN_ROOT,
    *(language.root for language in LANGUAGES.values()),
}
OBSOLETE_PREFIXES = (
    "Idiomatic",
    "Idiomatic Exercises ",
    "Idiomatic Grammar ",
    "Idiomatic Rescue Comics",
    "Idiomatic Tenses ",
    "Idiomatic Tenses Exercises ",
    "Idiomatic Translation ",
    "Languages",
    "Mandarin Actors",
    "Mandarin Characters 2026-06-20",
    "Mandarin China Provinces",
    "Mandarin Locations",
    "Mandarin Palace",
    "Mandarin Props",
    "Mandarin Zones",
    "Pimsleur",
    "EXPERIMENTS-YT",
)


def is_obsolete(name: str, keep_experiments: bool) -> bool:
    if name in KEEP_EXACT:
        return False
    if name.startswith(tuple(f"{root}::" for root in KEEP_EXACT)):
        return False
    if keep_experiments and (
        name == "EXPERIMENTS-YT" or name.startswith("EXPERIMENTS-YT::")
    ):
        return False
    return name.startswith(OBSOLETE_PREFIXES)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    parser.add_argument("--decisions", required=True, type=Path)
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    _, decisions = load_owner_decisions(args.decisions, copy_path)
    experiment_action = decisions.get("EXPERIMENTS-YT")
    if experiment_action not in {"suspend_and_demote", "keep"}:
        raise SystemExit("invalid or missing EXPERIMENTS-YT owner decision")
    keep_experiments = experiment_action == "keep"
    if args.apply:
        require_no_filtered_deck_cards(copy_path, "09_cleanup_empty_decks")
        require_completed_phase(copy_path, args.journal_dir, "08_resolve_odds")

    connection = read_only_connection(copy_path)
    try:
        rows = [
            {
                "id": row["id"],
                "name": display_deck_name(row["name"]),
                "direct_cards": row["direct_cards"],
            }
            for row in connection.execute(
                """
                SELECT d.id, d.name, COUNT(c.id) AS direct_cards
                  FROM decks d LEFT JOIN cards c ON c.did=d.id
                 GROUP BY d.id, d.name
                """
            )
        ]
        candidates = [
            row for row in rows if is_obsolete(str(row["name"]), keep_experiments)
        ]
        nonempty = [row for row in candidates if row["direct_cards"]]
        if nonempty:
            print("Obsolete source decks still contain cards; cleanup refuses:")
            for row in sorted(nonempty, key=lambda item: str(item["name"]).casefold()):
                print(f"  {row['direct_cards']:>7,}  {row['name']}")
            raise SystemExit(2)
        removable = sorted(candidates, key=lambda item: str(item["name"]).count("::"), reverse=True)
        before = collection_invariants(connection)
    finally:
        connection.close()

    print(f"empty obsolete shells eligible for removal: {len(removable):,}")
    for row in removable:
        print(f"  - {row['name']}")
    if not args.apply:
        print("DRY RUN: no decks removed.")
        return

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    journal_path = journal_directory(copy_path, args.journal_dir) / f"{stamp}_09_cleanup_empty_decks.json"
    journal = {
        "phase": "09_cleanup_empty_decks",
        "created_at": stamp,
        "copy_path": str(copy_path),
        "status": "prepared",
        "before_invariants": before,
        "removed_decks": removable,
    }
    write_json(journal_path, journal)

    from anki.collection import Collection

    collection = Collection(str(copy_path))
    try:
        for row in removable:
            current = collection.decks.id_for_name(str(row["name"]))
            if current is None or int(current) != int(row["id"]):
                raise RuntimeError(f"empty source deck changed before removal: {row['name']}")
            legacy = collection.decks.get_legacy(int(current))
            if legacy is None:
                raise RuntimeError(f"could not capture deck metadata: {row['name']}")
            row["legacy"] = legacy
        # Persist every exact deck record before deleting the first one.
        journal["removed_decks"] = removable
        write_json(journal_path, journal)
        for row in removable:
            current = collection.decks.id_for_name(str(row["name"]))
            if current is not None:
                collection.decks.remove([int(current)])
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
        raise RuntimeError("empty-deck cleanup changed notes, cards, scheduling, or revlog")
    journal["after_invariants"] = after
    journal["status"] = "complete"
    write_json(journal_path, journal)
    print(f"Removed {len(removable):,} empty shells; journal: {journal_path}")


if __name__ == "__main__":
    main()
