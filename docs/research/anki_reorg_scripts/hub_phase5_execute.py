#!/usr/bin/env python3
"""Hub phase-5 executor (REHEARSAL): apply a compiled hub manifest to a
validated collection COPY — never a live profile.

Steps (one journal, estate-style prepared -> complete):
  1. pristine + drift gates (copy sha == manifest source sha; every
     conversion card's live schedule row == its C2 evidence);
  2. install frozen models 1820180001/1820180002 through Anki's own apkg
     importer (seed package, seed notes/decks removed afterwards);
  3. archive + suspend the join-key quarantine cards;
  4. supported in-place conversion of every manifest winner to
     `Idiomatic Expression Example v1` (GUID/card/schedule/revlog
     preserved byte-for-byte), then ID field fill + tags;
  5. fresh hub notes (model 1820180001, deterministic GUIDs) under
     `<ROOT>::1 Expressions::2 Expression Focus`;
  6. bindings export for the server's anki_note_bindings staging;
  7. full gate suite; journal completes only if every gate passes.

Rollback: hub_phase5_rollback.py restores the journaled state.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from _common import (  # noqa: E402
    add_copy_path_argument,
    card_state_rows,
    collection_invariants,
    ensure_deck_journaled,
    journal_directory,
    read_only_connection,
    require_apply_flag,
    require_no_filtered_deck_cards,
    sha256_file,
    validated_copy_path,
    validated_work_artifact,
    write_json,
)

from idiomatic.hub import apkg as hub_apkg  # noqa: E402
from idiomatic.hub import identity as hub_identity  # noqa: E402
from idiomatic.hub import phase5  # noqa: E402

ARCHIVE_DECK = "zz Dormant::z-archive::Hub quarantine (join-key)"
SCHEDULE_EVIDENCE_KEYS = ("type", "queue", "due", "ivl", "factor", "reps",
                          "lapses", "left", "odue", "odid")


def capture_note_rows(connection, note_ids: list[int]) -> list[dict]:
    rows = []
    for chunk_start in range(0, len(note_ids), 5000):
        chunk = note_ids[chunk_start:chunk_start + 5000]
        marks = ",".join("?" for _ in chunk)
        rows.extend(dict(r) for r in connection.execute(
            f"""SELECT id, guid, mid, mod, usn, tags, flds, sfld, csum,
                       flags, data
                  FROM notes WHERE id IN ({marks}) ORDER BY id""", chunk))
    return rows


def capture_card_rows_full(connection, card_ids: list[int]) -> list[dict]:
    rows = []
    for chunk_start in range(0, len(card_ids), 5000):
        chunk = card_ids[chunk_start:chunk_start + 5000]
        marks = ",".join("?" for _ in chunk)
        rows.extend(dict(r) for r in connection.execute(
            f"""SELECT id, nid, did, ord, mod, usn, type, queue, due, ivl,
                       factor, reps, lapses, left, odue, odid, flags, data
                  FROM cards WHERE id IN ({marks}) ORDER BY id""", chunk))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    require_apply_flag(parser)
    parser.add_argument("--manifest", required=True, type=Path,
                        help="phase-5 manifest COPIED under the copy tree")
    parser.add_argument("--profile-key", default="syllabus")
    args = parser.parse_args()

    copy_path = validated_copy_path(args.copy_path)
    manifest_path = validated_work_artifact(
        args.manifest, copy_path, "phase-5 manifest")
    manifest = phase5.load_manifest(manifest_path)

    copy_sha = sha256_file(copy_path)
    if copy_sha != manifest["collection_source_sha256"]:
        raise SystemExit(
            f"copy is not pristine: sha {copy_sha[:16]}… != manifest source "
            f"{manifest['collection_source_sha256'][:16]}… — clone a fresh copy")

    conversions = manifest["conversions"]
    hubs = manifest["hubs"]
    joinkey = manifest["quarantine"]["join_key_cards"]
    deferred_ids = [int(g["card_id"])
                    for g in manifest["gaps"]["deferred_cards"]]
    print(f"manifest: {len(conversions):,} conversions "
          f"({manifest['counts']['conversions_adoptable']:,} adoptable, "
          f"{manifest['counts']['adopted_reps']:,} reps), "
          f"{len(hubs):,} hub notes, {len(joinkey)} join-key quarantine, "
          f"{len(deferred_ids):,} deferred")

    if not args.apply:
        print("DRY RUN: add --apply to mutate the validated copy.")
        return

    require_no_filtered_deck_cards(copy_path, "hub_phase5_execute")

    # ---- before-state capture + drift gates (read-only) --------------------
    connection = read_only_connection(copy_path)
    try:
        for target_mid in (hub_apkg.HUB_MODEL_ID, hub_apkg.EXAMPLE_MODEL_ID):
            row = connection.execute(
                "SELECT 1 FROM notetypes WHERE id=?", (target_mid,)).fetchone()
            if row:
                raise SystemExit(f"target model {target_mid} already present")
        before_invariants = collection_invariants(connection)

        conv_card_rows: dict[int, tuple] = {}
        for conv in conversions:
            row = phase5.card_schedule_row(connection, int(conv["card_id"]))
            if row is None:
                raise SystemExit(f"conversion card missing: {conv['card_id']}")
            conv_card_rows[int(conv["card_id"])] = tuple(row)
            for key_index, key in enumerate(SCHEDULE_EVIDENCE_KEYS):
                evidence = conv["schedule_evidence"].get(key)
                actual = dict(zip(
                    ("id", "nid", "ord", "type", "queue", "due", "ivl",
                     "factor", "reps", "lapses", "left", "odue", "odid",
                     "flags", "data"), tuple(row)))[key]
                if evidence is not None and int(evidence) != int(actual):
                    raise SystemExit(
                        f"card {conv['card_id']} drifted from C2 evidence: "
                        f"{key} {actual} != {evidence}")
        deferred_rows = {
            cid: tuple(phase5.card_schedule_row(connection, cid) or ())
            for cid in deferred_ids}
        conv_note_ids = [int(c["note_id"]) for c in conversions]
        conv_notes_before = capture_note_rows(connection, conv_note_ids)
        joinkey_cards_before = capture_card_rows_full(
            connection, [int(c["card_id"]) for c in joinkey])
        c1_notes_before = {
            int(r["id"]): (r["guid"], int(r["mid"]), int(r["mod"]))
            for r in capture_note_rows(
                connection, [int(n) for n in manifest["c1_archive_note_ids"]])}
        graves_before = [tuple(r) for r in connection.execute(
            "SELECT usn, oid, type FROM graves ORDER BY oid, type")]
        tags_before = [tuple(r) for r in connection.execute(
            "SELECT tag, usn, collapsed, hex(config) FROM tags ORDER BY tag")]
    finally:
        connection.close()

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    journal_dir = journal_directory(copy_path, args.journal_dir)
    journal_path = journal_dir / f"{stamp}_hub_phase5.json"
    journal: dict = {
        "phase": "hub_phase5",
        "copy_path": str(copy_path),
        "created_at": stamp,
        "status": "prepared",
        "manifest_content_sha256": manifest["content_sha256"],
        "manifest_file_sha256": sha256_file(manifest_path),
        "source_copy_sha256": copy_sha,
        "profile_key": args.profile_key,
        "before_invariants": before_invariants,
        "conversion_note_rows": conv_notes_before,
        "conversion_card_rows": {str(k): list(v)
                                 for k, v in conv_card_rows.items()},
        "joinkey_card_rows": joinkey_cards_before,
        "graves_before": graves_before,
        "tags_catalog_before": tags_before,
        "created_decks": [],
        "created_hub_notes": [],
        "seed_note_ids": [],
        "installed_models": [],
    }
    write_json(journal_path, journal)

    from anki.collection import (  # noqa: E402
        Collection,
        ImportAnkiPackageOptions,
        ImportAnkiPackageRequest,
    )

    col = Collection(str(copy_path))
    try:
        # ---- 1. frozen-model install via Anki's own importer --------------
        seed_path = copy_path.parent / "hub_seed_models.apkg"
        hub_apkg.build_hub_apkg(
            out_path=seed_path,
            hub_notes=[{"expression_id": 1, "lang": "es",
                        "expression": "seed", "gloss_en": "seed",
                        "usage_line_en": "", "key_synonym": None,
                        "false_friend": None, "examples": [], "sources": [],
                        "context_audio_media": None,
                        "expression_audio_media": None}],
            example_notes=[{"expression_id": 1, "example_id": 1,
                            "lang": "es", "en_text": "seed",
                            "target_text": "seed", "en_audio_media": None,
                            "tl_audio_media": None, "image_media": None,
                            "expression": "seed", "gloss_en": "seed",
                            "source": None, "origin": "initial"}],
            media_files=[], pilot=True)
        col.import_anki_package(ImportAnkiPackageRequest(
            package_path=str(seed_path),
            options=ImportAnkiPackageOptions(
                merge_notetypes=False,
                update_notes=2,       # NEVER
                update_notetypes=2,   # NEVER
                with_scheduling=False,
                with_deck_configs=False)))
        for target_mid, fields, n_templates in (
                (hub_apkg.HUB_MODEL_ID, hub_apkg.HUB_FIELDS, 2),
                (hub_apkg.EXAMPLE_MODEL_ID, hub_apkg.EXAMPLE_FIELDS, 1)):
            model = col.models.get(target_mid)
            if model is None:
                raise RuntimeError(f"model {target_mid} was not installed")
            names = [f["name"] for f in model["flds"]]
            if names != fields or len(model["tmpls"]) != n_templates:
                raise RuntimeError(f"installed model {target_mid} schema "
                                   f"mismatch: {names}")
            journal["installed_models"].append(target_mid)
        seed_nids = [int(r[0]) for r in col.db.all(
            "SELECT id FROM notes WHERE guid IN (?, ?)",
            hub_identity.pilot_hub_guid("es", 1),
            hub_identity.pilot_example_guid(1))]
        journal["seed_note_ids"] = seed_nids
        write_json(journal_path, journal)
        col.remove_notes(seed_nids)
        for deck in col.decks.all_names_and_ids():
            if deck.name.startswith(hub_apkg.PILOT_DECK_ROOT):
                remaining = col.db.scalar(
                    "SELECT COUNT(*) FROM cards WHERE did=?", deck.id)
                if remaining:
                    raise RuntimeError(
                        f"seed deck {deck.name} still has {remaining} cards")
                col.decks.remove([deck.id])

        # ---- 2. archive + suspend join-key quarantine ---------------------
        if joinkey:
            archive_did, _ = ensure_deck_journaled(
                col, ARCHIVE_DECK, journal, journal_path)
            quarantine_ids = [int(c["card_id"]) for c in joinkey]
            col.set_deck(quarantine_ids, archive_did)
            active = [int(r["id"]) for r in joinkey_cards_before
                      if int(r["queue"]) != -1]
            if active:
                col.sched.suspend_cards(active)

        # ---- 3. supported in-place conversion -----------------------------
        pool_model = col.models.get(phase5.POOL_MODEL_ID)
        example_model = col.models.get(hub_apkg.EXAMPLE_MODEL_ID)
        fmap = phase5.pool_to_example_fmap()
        conv_nids = [int(c["note_id"]) for c in conversions]
        for start in range(0, len(conv_nids), 2000):
            col.models.change(pool_model, conv_nids[start:start + 2000],
                              example_model, fmap, {0: 0})

        # ---- 4. ID field fill + tags; harvest gloss/sources ---------------
        gloss_by_expr: dict[int, collections.Counter] = \
            collections.defaultdict(collections.Counter)
        sources_by_expr: dict[int, list[str]] = collections.defaultdict(list)
        expression_index = hub_apkg.EXAMPLE_FIELDS.index("Expression")
        gloss_index = hub_apkg.EXAMPLE_FIELDS.index("GlossEN")
        source_index = hub_apkg.EXAMPLE_FIELDS.index("SourceHTML")
        for start in range(0, len(conversions), 500):
            chunk = conversions[start:start + 500]
            notes = []
            for conv in chunk:
                note = col.get_note(int(conv["note_id"]))
                for name, value in phase5.example_field_fill(conv).items():
                    note.fields[hub_apkg.EXAMPLE_FIELDS.index(name)] = value
                note.tags = sorted(set(note.tags)
                                   | set(phase5.example_tags(conv)))
                expr_id = int(conv["expression_id"])
                if note.fields[gloss_index]:
                    gloss_by_expr[expr_id][note.fields[gloss_index]] += 1
                raw_source = note.fields[source_index]
                if raw_source and raw_source not in sources_by_expr[expr_id]:
                    sources_by_expr[expr_id].append(raw_source)
                notes.append(note)
            col.update_notes(notes)

        # ---- 5. fresh hub notes -------------------------------------------
        hub_model = col.models.get(hub_apkg.HUB_MODEL_ID)
        focus_dids: dict[str, int] = {}
        for hub in hubs:
            lang = hub["lang"]
            if lang not in focus_dids:
                focus_dids[lang], _ = ensure_deck_journaled(
                    col, hub_apkg.hub_deck_name(lang), journal, journal_path)
            expr_id = int(hub["expression_id"])
            gloss_counter = gloss_by_expr.get(expr_id)
            gloss = gloss_counter.most_common(1)[0][0] if gloss_counter else ""
            sources_html = "\n".join(
                f'<div class="src">{s}</div>'
                for s in sources_by_expr.get(expr_id, [])[:3])
            note = col.new_note(hub_model)
            note.guid = hub["target_guid"]
            note.fields = phase5.hub_fields(hub, gloss_en=gloss,
                                            sources_html=sources_html)
            note.tags = phase5.hub_tags(hub)
            col.add_note(note, focus_dids[lang])
            journal["created_hub_notes"].append({
                "note_id": int(note.id), "guid": hub["target_guid"],
                "expression_id": expr_id, "lang": lang,
                "card_ids": [int(c.id) for c in note.cards()],
            })
        write_json(journal_path, journal)

    finally:
        col.close(downgrade=False)

    # ---- 6. bindings export + 7. gates (read-only re-open) -----------------
    connection = read_only_connection(copy_path)
    try:
        binding_rows = phase5.bindings_rows(connection, manifest,
                                            args.profile_key)
        bindings_path = journal_dir / f"{stamp}_hub_phase5_bindings.json"
        write_json(bindings_path, {
            "profile_key": args.profile_key,
            "manifest_content_sha256": manifest["content_sha256"],
            "rows": binding_rows,
        })
        journal["bindings_export"] = str(bindings_path)
        after_invariants = collection_invariants(connection)
        problems: list[str] = []
        expected_notes = before_invariants["notes"] + len(hubs)
        expected_cards = before_invariants["cards"] + 2 * len(hubs)
        if after_invariants["notes"] != expected_notes:
            problems.append(f"note count {after_invariants['notes']} != "
                            f"{expected_notes}")
        if after_invariants["cards"] != expected_cards:
            problems.append(f"card count {after_invariants['cards']} != "
                            f"{expected_cards}")
        for key in ("revlog", "revlog_sha256", "mature_cards", "card_reps"):
            if after_invariants[key] != before_invariants[key]:
                problems.append(f"invariant changed: {key}")
        problems += phase5.verify_conversions(connection, manifest,
                                              conv_card_rows)
        for cid, before_row in deferred_rows.items():
            after_row = phase5.card_schedule_row(connection, cid)
            if tuple(after_row or ()) != before_row:
                problems.append(f"deferred card {cid} changed")
        problems += phase5.verify_expression_focus_purity(connection)
        problems += phase5.verify_fluency_lane_models(connection, manifest)
        problems += phase5.verify_no_quarantine_conversion(connection,
                                                           manifest)
        problems += phase5.verify_hub_guid_uniqueness(connection, manifest)
        for nid, (guid, mid, mod) in c1_notes_before.items():
            row = connection.execute(
                "SELECT guid, mid, mod FROM notes WHERE id=?",
                (nid,)).fetchone()
            if row is None or (row[0], int(row[1]), int(row[2])) != \
                    (guid, mid, mod):
                problems.append(f"C1 archive note {nid} was touched")
        for row in joinkey_cards_before:
            after_row = connection.execute(
                "SELECT queue, did FROM cards WHERE id=?",
                (int(row["id"]),)).fetchone()
            if after_row is None or int(after_row[0]) != -1:
                problems.append(f"join-key card {row['id']} not suspended")
    finally:
        connection.close()

    if problems:
        journal["status"] = "failed_gates"
        journal["gate_problems"] = problems
        write_json(journal_path, journal)
        raise SystemExit("GATES FAILED:\n  " + "\n  ".join(problems[:40]))

    journal["after_invariants"] = after_invariants
    journal["status"] = "complete"
    write_json(journal_path, journal)
    print(f"phase 5 applied: {len(conversions):,} conversions "
          f"({manifest['counts']['conversions_adoptable']:,} adopted "
          f"schedules, {manifest['counts']['adopted_reps']:,} reps), "
          f"{len(hubs):,} hub notes / {2 * len(hubs):,} hub cards, "
          f"{len(joinkey)} join-key cards archived, "
          f"{len(deferred_ids):,} deferred untouched")
    print(f"journal: {journal_path}")


if __name__ == "__main__":
    main()
