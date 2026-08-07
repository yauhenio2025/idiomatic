#!/usr/bin/env python3
"""Phase 6 draft: move long Idioms Audio projections to dormant decks and suspend them."""

from __future__ import annotations

import argparse

from _common import add_copy_path_argument, require_apply_flag
from _mapping import audio_card_destination
from _phase_runner import execute_move_phase


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    args = parser.parse_args()
    execute_move_phase(
        phase="06_discontinue_audio",
        copy_path=args.copy_path,
        mapper=audio_card_destination,
        apply=args.apply,
        requested_journal_dir=args.journal_dir,
        suspend_after_move=True,
        required_phase="05_place_mandarin_pimsleur_archive",
    )


if __name__ == "__main__":
    main()
