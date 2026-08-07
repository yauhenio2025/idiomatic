#!/usr/bin/env python3
"""Phase 4 draft: move grammar, tenses, exercises, translation, errors, and rescue."""

from __future__ import annotations

import argparse

from _common import add_copy_path_argument, require_apply_flag
from _mapping import learning_card_destination
from _phase_runner import execute_move_phase


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    args = parser.parse_args()
    execute_move_phase(
        phase="04_move_learning_families",
        copy_path=args.copy_path,
        mapper=learning_card_destination,
        apply=args.apply,
        requested_journal_dir=args.journal_dir,
        required_phase="03_move_expressions",
    )


if __name__ == "__main__":
    main()
