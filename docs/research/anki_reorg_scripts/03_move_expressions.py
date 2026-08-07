#!/usr/bin/env python3
"""Phase 3 draft: collapse active per-video/legacy expression cards into two decks per language."""

from __future__ import annotations

import argparse
from pathlib import Path

from _common import add_copy_path_argument, require_apply_flag
from _duplicates import validate_collision_manifest
from _provenance import assert_provenance_complete
from _mapping import expression_card_destination
from _phase_runner import execute_move_phase


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    parser.add_argument("--collision-manifest", required=True, type=Path)
    args = parser.parse_args()
    validate_collision_manifest(args.copy_path, args.collision_manifest)
    if args.apply:
        assert_provenance_complete(args.copy_path)
    execute_move_phase(
        phase="03_move_expressions",
        copy_path=args.copy_path,
        mapper=expression_card_destination,
        apply=args.apply,
        requested_journal_dir=args.journal_dir,
        required_phase="02_tag_provenance",
    )


if __name__ == "__main__":
    main()
