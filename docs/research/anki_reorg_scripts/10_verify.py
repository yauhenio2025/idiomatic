#!/usr/bin/env python3
"""Final read-only verification for a migrated collection copy."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from _common import (
    add_copy_path_argument,
    collection_invariants,
    display_deck_name,
    load_owner_decisions,
    read_only_connection,
    sha256_file,
    validated_copy_path,
    validated_work_artifact,
)
from _mapping import AUDIO_MODELS, fixed_target_decks


SACRED_KEYS = (
    "notes",
    "cards",
    "revlog",
    "mature_cards",
    "card_reps",
    "schedule_core_sha256",
    "revlog_sha256",
    "note_identity_sha256",
    "note_content_sha256",
    "lex_card_deck_sha256",
)
EXPECTED_PHASES = (
    "01_create_targets",
    "02_tag_provenance",
    "03_move_expressions",
    "04_move_learning_families",
    "05_place_mandarin_pimsleur_archive",
    "06_discontinue_audio",
    "07_resolve_duplicates",
    "08_resolve_odds",
    "09_cleanup_empty_decks",
)
OLD_PREFIXES = (
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
)
LEX_DECK = "Lex-Stage · German vocab/idiom mnemonics (prototype)"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def id_fingerprint(ids: set[int]) -> str:
    digest = hashlib.sha256()
    for card_id in sorted(ids):
        digest.update(json.dumps((card_id,), separators=(",", ":")).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def blob_hex(value: object) -> str:
    return bytes(value or b"").hex()


def is_old_source(name: str, keep_experiments: bool) -> bool:
    if name == "EXPERIMENTS-YT" or name.startswith("EXPERIMENTS-YT::"):
        return not keep_experiments
    return any(
        name.startswith(prefix)
        if prefix.endswith(" ")
        else name == prefix or name.startswith(prefix + "::")
        for prefix in OLD_PREFIXES
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    parser.add_argument("--baseline-journal", required=True, type=Path)
    parser.add_argument("--journal-dir", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    baseline_path = validated_work_artifact(
        args.baseline_journal, copy_path, "baseline journal"
    )
    journal_dir = validated_work_artifact(
        args.journal_dir, copy_path, "journal directory", directory=True
    )
    decisions_path, decisions = load_owner_decisions(args.decisions, copy_path)

    failures: list[str] = []
    experiment_action = decisions.get("EXPERIMENTS-YT")
    if experiment_action not in {"merge_pt_fluency", "suspend_and_demote", "keep"}:
        failures.append("invalid or missing EXPERIMENTS-YT owner decision")
    dedupe_policy = decisions.get("dedupe_policy")
    if dedupe_policy not in {"schedule-first", "canonical-model-first", "keep-all"}:
        failures.append("invalid or missing dedupe_policy owner decision")
    keep_experiments = experiment_action == "keep"

    baseline = load_json(baseline_path)
    if Path(str(baseline.get("copy_path", ""))).resolve() != copy_path:
        failures.append("baseline journal belongs to a different collection copy")
    baseline_invariants = baseline.get("before_invariants", {})
    if baseline.get("owner_decisions_sha256") != sha256_file(decisions_path):
        failures.append("owner decision record changed since phase 01")

    journals: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(journal_dir.glob("*.json")):
        payload = load_json(path)
        if "phase" not in payload or "before_invariants" not in payload:
            continue
        if Path(str(payload.get("copy_path", ""))).resolve() != copy_path:
            failures.append(f"journal belongs to another copy: {path.name}")
            continue
        if payload.get("status") == "rolled_back":
            continue
        if payload.get("status") != "complete":
            failures.append(f"phase journal is not complete: {path.name}")
            continue
        if "after_invariants" not in payload:
            failures.append(f"phase journal lacks after_invariants: {path.name}")
            continue
        journals.append((path, payload))

    if not journals:
        failures.append("no completed phase journals found")
    elif baseline_path not in {path for path, _ in journals}:
        failures.append("baseline journal is not a completed journal in --journal-dir")
    elif journals[0][0] != baseline_path:
        failures.append("baseline journal is not the first completed migration phase")
    phase_names = [str(payload.get("phase")) for _, payload in journals]
    if phase_names != list(EXPECTED_PHASES):
        failures.append(
            "completed phase order/count differs from the required once-only 01–09 sequence"
        )

    for (previous_path, previous), (current_path, current) in zip(journals, journals[1:]):
        if previous["after_invariants"] != current["before_invariants"]:
            failures.append(
                f"journal chain break between {previous_path.name} and {current_path.name}"
            )

    connection = read_only_connection(copy_path)
    try:
        invariants = collection_invariants(connection)
        deck_names = {
            display_deck_name(str(row["name"])): int(row["id"])
            for row in connection.execute("SELECT id,name FROM decks")
        }
        actual_deck_metadata = {
            int(row["id"]): {
                "name": display_deck_name(str(row["name"])),
                "common_hex": blob_hex(row["common"]),
                "kind_hex": blob_hex(row["kind"]),
            }
            for row in connection.execute("SELECT id,name,common,kind FROM decks")
        }
        missing_targets = sorted(fixed_target_decks() - set(deck_names), key=str.casefold)
        if missing_targets:
            failures.append(f"missing {len(missing_targets)} target deck shells")

        obsolete = sorted(
            (name for name in deck_names if is_old_source(name, keep_experiments)),
            key=str.casefold,
        )
        if obsolete:
            failures.append(f"{len(obsolete)} obsolete source deck rows remain")

        active_audio = connection.execute(
            """
            SELECT COUNT(*)
              FROM cards c JOIN notes n ON n.id=c.nid JOIN notetypes nt ON nt.id=n.mid
             WHERE nt.name IN (?, ?) AND c.queue != -1
            """,
            tuple(AUDIO_MODELS),
        ).fetchone()[0]
        if active_audio:
            failures.append(f"{active_audio} discontinued Idioms Audio cards remain active")

        filtered_cards = connection.execute("SELECT COUNT(*) FROM cards WHERE odid != 0").fetchone()[0]
        if filtered_cards:
            failures.append(f"{filtered_cards} cards unexpectedly occupy filtered decks")

        lex = connection.execute(
            """
            SELECT COUNT(DISTINCT n.id) AS notes, COUNT(c.id) AS cards
              FROM decks d LEFT JOIN cards c ON c.did=d.id LEFT JOIN notes n ON n.id=c.nid
             WHERE d.name=?
            """,
            (LEX_DECK,),
        ).fetchone()
        if lex is None or (int(lex["notes"]), int(lex["cards"])) != (18, 28):
            failures.append("Lex-Stage was not preserved at 18 notes / 28 cards")

        final_suspended = {
            int(row[0]) for row in connection.execute("SELECT id FROM cards WHERE queue=-1")
        }
        note_tags = {
            int(row["id"]): set(str(row["tags"]).strip().split())
            for row in connection.execute("SELECT id,tags FROM notes")
        }
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
        if quick_check != "ok":
            failures.append(f"SQLite quick_check returned {quick_check!r}")
    finally:
        connection.close()

    for key in SACRED_KEYS:
        if baseline_invariants.get(key) != invariants.get(key):
            failures.append(f"baseline sacred invariant mismatch: {key}")

    if journals and journals[-1][1]["after_invariants"] != invariants:
        failures.append("final collection does not match the last phase journal")

    authorized_new_suspensions: set[int] = set()
    expected_final_decks: dict[int, str] = {}
    expected_deck_metadata: dict[int, dict[str, Any]] = {}
    for _, journal in journals:
        authorized_new_suspensions.update(
            int(card_id) for card_id in journal.get("suspended_card_ids", [])
        )
        for assignment in journal.get("expected_card_destinations", []):
            expected_final_decks[int(assignment["card_id"])] = str(
                assignment["destination"]
            )
        for move in journal.get("moves", []):
            expected_final_decks[int(move["card_id"])] = str(move["destination"])
        for row in journal.get("deck_metadata", []):
            expected_deck_metadata[int(row["id"])] = row
        for tag, note_ids in journal.get("tags_added", {}).items():
            for note_id in note_ids:
                if tag not in note_tags.get(int(note_id), set()):
                    failures.append(f"journaled tag missing: note {note_id}, tag {tag}")
                    break
    if expected_final_decks:
        connection = read_only_connection(copy_path)
        try:
            actual_final_decks = {
                int(row["card_id"]): display_deck_name(str(row["deck_name"]))
                for row in connection.execute(
                    """
                    SELECT c.id AS card_id, d.name AS deck_name
                      FROM cards c JOIN decks d ON d.id=c.did
                    """
                )
                if int(row["card_id"]) in expected_final_decks
            }
        finally:
            connection.close()
        wrong_decks = {
            card_id: (destination, actual_final_decks.get(card_id))
            for card_id, destination in expected_final_decks.items()
            if actual_final_decks.get(card_id) != destination
        }
        if wrong_decks:
            failures.append(f"{len(wrong_decks)} moved cards are not in their final journaled decks")
    wrong_metadata = []
    for deck_id, expected in expected_deck_metadata.items():
        actual = actual_deck_metadata.get(deck_id)
        if actual is None or actual != {
            "name": str(expected["expected_name"]),
            "common_hex": str(expected["common_hex"]),
            "kind_hex": str(expected["kind_hex"]),
        }:
            wrong_metadata.append(deck_id)
    if wrong_metadata:
        failures.append(
            f"{len(wrong_metadata)} metadata-preserving deck renames no longer match"
        )
    missing_suspensions = authorized_new_suspensions - final_suspended
    if missing_suspensions:
        failures.append(f"{len(missing_suspensions)} intentionally suspended cards are active")
    preexisting_suspended = final_suspended - authorized_new_suspensions
    if id_fingerprint(preexisting_suspended) != baseline_invariants.get(
        "suspended_card_ids_sha256"
    ):
        failures.append("pre-existing suspended-card set changed")

    phase_08_count = 0
    for _, journal in journals:
        if journal.get("phase") == "07_resolve_duplicates" and journal.get("policy") != dedupe_policy:
            failures.append("completed dedupe phase does not match the owner decision")
        if journal.get("phase") == "08_resolve_odds":
            phase_08_count += 1
            if journal.get("experiment_action") != experiment_action:
                failures.append("completed phase 08 does not match the owner decision")
    if phase_08_count != 1:
        failures.append("verification requires exactly one completed phase 08")

    print(json.dumps(invariants, indent=2, sort_keys=True))
    if failures:
        print("FAILURES:")
        for failure in failures:
            print(f"  - {failure}")
        raise SystemExit(1)
    print("PASS: target structure and all scheduling/history safeguards hold.")


if __name__ == "__main__":
    main()
