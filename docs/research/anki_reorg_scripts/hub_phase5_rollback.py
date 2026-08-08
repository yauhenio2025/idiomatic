#!/usr/bin/env python3
"""Roll back an applied hub phase-5 run from its journal (copy only).

Raw-SQLite restoration, resolved fully before the first mutation:
  - delete created hub notes/cards (guids verified first);
  - restore every converted note row verbatim (mid, flds, sfld, csum,
    tags, mod, usn) — the supported conversion left cards untouched;
  - restore join-key quarantine cards (did/queue/mod/usn);
  - remove the installed notetypes once nothing references them;
  - remove journal-created decks (must be empty);
  - restore the graves and tags catalogs to their captured snapshots.

Success = collection_invariants equality with the journal's
before-state (the estate's logical-identity standard: bookkeeping
clocks are not fingerprinted, content/schedule/history are).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
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

from idiomatic.hub import apkg as hub_apkg  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    parser.add_argument("--journal", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    copy_path = validated_copy_path(args.copy_path)
    journal_path = validated_work_artifact(args.journal, copy_path,
                                           "rollback journal")
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    if Path(journal["copy_path"]).resolve() != copy_path:
        raise SystemExit("journal belongs to a different collection copy")
    if journal.get("status") not in {"prepared", "complete", "failed_gates",
                                     "rolling_back"}:
        raise SystemExit(f"journal status {journal.get('status')!r} is not "
                         "rollback-eligible")
    if journal.get("status") in {"prepared", "rolling_back"}:
        print("WARNING: resuming rollback from a potentially partial "
              "phase state (estate parity).")

    created = journal.get("created_hub_notes", [])
    conv_rows = journal.get("conversion_note_rows", [])
    print(f"phase: {journal['phase']}; created hub notes: {len(created):,}; "
          f"converted notes captured: {len(conv_rows):,}")
    if not args.apply:
        print("DRY RUN: no rollback applied.")
        return

    # Drift refusal before mutating anything.
    connection = read_only_connection(copy_path)
    try:
        if journal.get("status") == "complete":
            if collection_invariants(connection) != journal.get(
                    "after_invariants"):
                raise SystemExit("collection drifted after this phase; "
                                 "refusing rollback")
        for row in created:
            got = connection.execute(
                "SELECT guid FROM notes WHERE id=?",
                (int(row["note_id"]),)).fetchone()
            if got is None or got[0] != row["guid"]:
                raise SystemExit(f"created hub note {row['note_id']} "
                                 "missing or guid mismatch")
    finally:
        connection.close()

    journal["status"] = "rolling_back"
    write_json(journal_path, journal)

    db = sqlite3.connect(str(copy_path))
    # Anki's schema indexes (notetypes/templates/fields names, tags) use
    # the custom `unicase` collation; register it exactly as the estate
    # read-only helper does or DML on those tables fails.
    db.create_collation(
        "unicase",
        lambda left, right: (left.casefold() > right.casefold())
        - (left.casefold() < right.casefold()),
    )
    try:
        db.execute("BEGIN")
        # 1. created hub notes + their cards
        for row in created:
            db.execute("DELETE FROM cards WHERE nid=?",
                       (int(row["note_id"]),))
            db.execute("DELETE FROM notes WHERE id=?",
                       (int(row["note_id"]),))
        # 2. converted notes verbatim
        for row in conv_rows:
            db.execute(
                """UPDATE notes SET guid=?, mid=?, mod=?, usn=?, tags=?,
                                    flds=?, sfld=?, csum=?, flags=?, data=?
                    WHERE id=?""",
                (row["guid"], row["mid"], row["mod"], row["usn"],
                 row["tags"], row["flds"], row["sfld"], row["csum"],
                 row["flags"], row["data"], row["id"]))
        # 3. join-key quarantine cards
        for row in journal.get("joinkey_card_rows", []):
            db.execute(
                """UPDATE cards SET did=?, mod=?, usn=?, queue=?
                    WHERE id=?""",
                (row["did"], row["mod"], row["usn"], row["queue"],
                 row["id"]))
        # 4. installed notetypes (nothing may reference them anymore)
        for mid in (hub_apkg.HUB_MODEL_ID, hub_apkg.EXAMPLE_MODEL_ID):
            count = db.execute("SELECT COUNT(*) FROM notes WHERE mid=?",
                               (mid,)).fetchone()[0]
            if count:
                raise RuntimeError(f"{count} notes still reference model "
                                   f"{mid}; aborting rollback")
            db.execute("DELETE FROM templates WHERE ntid=?", (mid,))
            db.execute("DELETE FROM fields WHERE ntid=?", (mid,))
            db.execute("DELETE FROM notetypes WHERE id=?", (mid,))
        # 5. journal-created decks (must be empty)
        for deck in journal.get("created_decks", []):
            remaining = db.execute("SELECT COUNT(*) FROM cards WHERE did=?",
                                   (int(deck["id"]),)).fetchone()[0]
            if remaining:
                raise RuntimeError(f"created deck {deck['name']} still has "
                                   f"{remaining} cards")
            db.execute("DELETE FROM decks WHERE id=?", (int(deck["id"]),))
        # 6. graves + tags catalogs back to their snapshots
        db.execute("DELETE FROM graves")
        db.executemany("INSERT INTO graves (usn, oid, type) VALUES (?,?,?)",
                       [tuple(r) for r in journal.get("graves_before", [])])
        db.execute("DELETE FROM tags")
        db.executemany(
            "INSERT INTO tags (tag, usn, collapsed, config) "
            "VALUES (?,?,?,?)",
            [(tag, usn, collapsed, bytes.fromhex(config_hex))
             for (tag, usn, collapsed, config_hex)
             in journal.get("tags_catalog_before", [])])
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise
    finally:
        db.close()

    connection = read_only_connection(copy_path)
    try:
        now = collection_invariants(connection)
    finally:
        connection.close()
    mismatches = [key for key, value in journal["before_invariants"].items()
                  if now.get(key) != value]
    if mismatches:
        raise SystemExit("ROLLBACK INCOMPLETE — invariants differ from "
                         f"pristine: {mismatches}")
    journal["status"] = "rolled_back"
    write_json(journal_path, journal)
    print("rollback complete: collection is logically identical to the "
          "journal's before-state (all invariant fingerprints match)")


if __name__ == "__main__":
    main()
