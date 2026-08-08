#!/usr/bin/env python3
"""Standalone verifier for an applied hub phase-5 run (read-only).

Re-runs every gate independently of the executor, from the journal's
captured before-state + the manifest, and writes a verdict JSON next to
the journal. PASS requires zero problems.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from _common import (  # noqa: E402
    add_copy_path_argument,
    collection_invariants,
    read_only_connection,
    validated_copy_path,
    validated_work_artifact,
    write_json,
)

from idiomatic.hub import phase5  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--journal", required=True, type=Path)
    args = parser.parse_args()

    copy_path = validated_copy_path(args.copy_path)
    manifest = phase5.load_manifest(
        validated_work_artifact(args.manifest, copy_path, "manifest"))
    journal_path = validated_work_artifact(args.journal, copy_path, "journal")
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    if journal.get("manifest_content_sha256") != manifest["content_sha256"]:
        raise SystemExit("journal was not produced from this manifest")
    if journal.get("status") != "complete":
        raise SystemExit(f"journal status is {journal.get('status')!r}, "
                         "not complete")

    before = journal["before_invariants"]
    conv_before = {int(k): tuple(v) for k, v in
                   journal["conversion_card_rows"].items()}

    problems: list[str] = []
    connection = read_only_connection(copy_path)
    try:
        now = collection_invariants(connection)
        n_hubs = len(manifest["hubs"])
        if now["notes"] != before["notes"] + n_hubs:
            problems.append(f"notes {now['notes']} != "
                            f"{before['notes']} + {n_hubs}")
        if now["cards"] != before["cards"] + 2 * n_hubs:
            problems.append(f"cards {now['cards']} != "
                            f"{before['cards']} + {2 * n_hubs}")
        for key in ("revlog", "revlog_sha256", "mature_cards", "card_reps"):
            if now[key] != before[key]:
                problems.append(f"invariant changed since before-state: {key}")
        if journal.get("after_invariants") != now:
            problems.append("collection drifted since the executor's "
                            "after-state was journaled")
        problems += phase5.verify_conversions(connection, manifest,
                                              conv_before)
        problems += phase5.verify_expression_focus_purity(connection)
        problems += phase5.verify_fluency_lane_models(connection, manifest)
        problems += phase5.verify_no_quarantine_conversion(connection,
                                                           manifest)
        problems += phase5.verify_hub_guid_uniqueness(connection, manifest)

        # Every created hub note exists with both template cards.
        for created in journal["created_hub_notes"]:
            row = connection.execute(
                "SELECT COUNT(*) FROM cards WHERE nid=?",
                (int(created["note_id"]),)).fetchone()
            if int(row[0]) != 2:
                problems.append(f"hub note {created['note_id']} has "
                                f"{row[0]} cards, expected 2")

        # Adoption accounting: adopted reps present and byte-identical.
        adopted = [c for c in manifest["conversions"]
                   if c["adoption"] == "adoptable"]
        adopted_reps = 0
        for conv in adopted:
            row = phase5.card_schedule_row(connection, int(conv["card_id"]))
            adopted_reps += int(row[8]) if row else 0
        if adopted_reps != manifest["counts"]["adopted_reps"]:
            problems.append(f"adopted reps {adopted_reps} != manifest "
                            f"{manifest['counts']['adopted_reps']}")
    finally:
        connection.close()

    verdict = {
        "verdict": "PASS" if not problems else "FAIL",
        "problems": problems,
        "checked_conversions": len(manifest["conversions"]),
        "checked_hubs": len(manifest["hubs"]),
        "journal": str(journal_path),
    }
    out = journal_path.parent / (journal_path.stem + "_verify.json")
    write_json(out, verdict)
    print(f"{verdict['verdict']}: {len(problems)} problems; verdict at {out}")
    if problems:
        for problem in problems[:40]:
            print("  -", problem)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
