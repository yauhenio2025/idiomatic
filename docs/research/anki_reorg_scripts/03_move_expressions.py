#!/usr/bin/env python3
"""Phase 3 draft: merge active fluency and archive superseded expression tasks."""

from __future__ import annotations

import argparse
from pathlib import Path

from _common import (
    add_copy_path_argument,
    require_apply_flag,
    require_completed_phase,
    sha256_file,
    validated_copy_path,
    validated_work_artifact,
)
from _duplicates import validate_collision_manifest
from _provenance import assert_provenance_complete
from _mapping import RETIRED_EXPRESSION_TASK_MODELS, expression_card_destination
from _phase_runner import execute_move_phase


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    parser.add_argument("--collision-manifest", required=True, type=Path)
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    manifest_path = validated_work_artifact(
        args.collision_manifest, copy_path, "collision manifest"
    )
    manifest = validate_collision_manifest(copy_path, manifest_path)
    manifest_file_sha256 = sha256_file(manifest_path)
    if args.apply:
        _, phase_1 = require_completed_phase(
            copy_path, args.journal_dir, "01_create_targets"
        )
        if manifest.get("source_copy_sha256") != phase_1.get("source_copy_sha256"):
            raise RuntimeError(
                "collision manifest was not generated from the pristine phase-1 copy"
            )
        assert_provenance_complete(copy_path)
    execute_move_phase(
        phase="03_move_expressions",
        copy_path=copy_path,
        mapper=expression_card_destination,
        apply=args.apply,
        requested_journal_dir=args.journal_dir,
        required_phase="02_tag_provenance",
        suspend_selector=lambda _deck, model: model in RETIRED_EXPRESSION_TASK_MODELS,
        journal_metadata={
            "collision_manifest_source_copy_sha256": manifest[
                "source_copy_sha256"
            ],
            "collision_manifest_content_sha256": manifest["content_sha256"],
            "collision_manifest_file_sha256": manifest_file_sha256,
        },
    )


if __name__ == "__main__":
    main()
