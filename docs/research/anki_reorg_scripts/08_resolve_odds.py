#!/usr/bin/env python3
"""Phase 8 draft: apply explicit owner decisions for EXPERIMENTS-YT only."""

from __future__ import annotations

import argparse
from pathlib import Path

from _common import (
    add_copy_path_argument,
    collection_invariants,
    load_owner_decisions,
    read_only_connection,
    require_apply_flag,
    require_completed_phase,
    require_no_filtered_deck_cards,
    validated_copy_path,
    write_noop_phase_journal,
)
from _mapping import DORMANT_ROOT
from _phase_runner import execute_move_phase


ALLOWED = {"suspend_and_demote", "keep"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    parser.add_argument("--decisions", required=True, type=Path)
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    _, payload = load_owner_decisions(args.decisions, copy_path)
    action = payload.get("EXPERIMENTS-YT")
    if action not in ALLOWED:
        raise SystemExit(f"EXPERIMENTS-YT must be one of {sorted(ALLOWED)}")
    if args.apply:
        require_no_filtered_deck_cards(copy_path, "08_resolve_odds")
        require_completed_phase(copy_path, args.journal_dir, "07_resolve_duplicates")
    if action == "keep":
        if args.apply:
            connection = read_only_connection(copy_path)
            try:
                invariants = collection_invariants(connection)
            finally:
                connection.close()
            path = write_noop_phase_journal(
                copy_path=copy_path,
                requested_journal_dir=args.journal_dir,
                phase="08_resolve_odds",
                invariants=invariants,
                metadata={"experiment_action": action},
            )
            print(f"Owner decision is keep; recorded no-op journal: {path}")
        else:
            print("Owner decision is keep; no card moves planned.")
        return

    def mapper(deck_name: str, _model_name: str) -> str | None:
        if deck_name != "EXPERIMENTS-YT" and not deck_name.startswith("EXPERIMENTS-YT::"):
            return None
        return f"{DORMANT_ROOT}::Experiments::{deck_name}"

    execute_move_phase(
        phase="08_resolve_odds",
        copy_path=copy_path,
        mapper=mapper,
        apply=args.apply,
        requested_journal_dir=args.journal_dir,
        suspend_after_move=True,
        journal_metadata={"experiment_action": action},
    )


if __name__ == "__main__":
    main()
