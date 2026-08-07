#!/usr/bin/env python3
"""Build the evidence manifest for exact bilingual surface collisions."""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from _common import (
    add_copy_path_argument,
    collection_invariants,
    read_only_connection,
    sha256_file,
    validated_copy_path,
    validated_output_path,
)
from _duplicates import (
    collect_candidate_notes,
    collect_cross_generation_primary_notes,
    collision_content_fingerprint,
    collision_groups,
    target_only_review_queue,
)


def md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def candidate_values(group: dict[str, object], lane: str, field: str) -> str:
    records = group["candidate_records"]
    assert isinstance(records, list)
    values = dict.fromkeys(
        str(record[field])
        for record in records
        if isinstance(record, dict) and record.get("lane") == lane
    )
    return "<br>".join(md(value) for value in values)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    json_out = validated_output_path(args.json_out, copy_path)
    markdown_out = (
        validated_output_path(args.markdown_out, copy_path) if args.markdown_out else None
    )
    connection = read_only_connection(copy_path)
    try:
        groups = collision_groups(collect_candidate_notes(connection))
        manual_review_queue = target_only_review_queue(
            collect_cross_generation_primary_notes(connection)
        )
        invariants = collection_invariants(connection)
    finally:
        connection.close()

    manifest = {
        "schema_version": 1,
        "source_copy_sha256": sha256_file(copy_path),
        "identity_invariants": {
            key: invariants[key]
            for key in (
                "notes",
                "cards",
                "revlog",
                "note_identity_sha256",
                "model_schema_sha256",
            )
        },
        "normalization": (
            "visible text; HTML/sound stripped; HTML-unescaped; Unicode NFKC; "
            "curly quotes/dashes stabilized; whitespace collapsed; case-folded; "
            "accents and punctuation preserved; both target and English must match"
        ),
        "content_sha256": collision_content_fingerprint(groups),
        "groups": groups,
        "manual_review_queue": manual_review_queue,
    }
    json_out.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    categories = collections.Counter(
        category for group in groups for category in group["categories"]
    )
    lanes = collections.Counter(str(note["lane"]) for group in groups for note in group["notes"])
    collision_notes = {int(note["note_id"]) for group in groups for note in group["notes"]}
    manual_metrics = manual_review_queue["metrics"]
    print(f"exact surface-collision groups: {len(groups):,}")
    print(f"  distinct candidate notes: {len(collision_notes):,}")
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count:,}")
    for lane, count in sorted(lanes.items()):
        print(f"  notes in {lane}: {count:,}")
    print(
        "manual-review groups: "
        f"{manual_metrics['groups']:,} "
        f"({manual_metrics['tiers']['strict_target_only']:,} strict target-only; "
        f"{manual_metrics['tiers']['punctuation_relaxed']:,} punctuation-relaxed)"
    )
    print(
        "  candidate notes: "
        f"{manual_metrics['legacy']['notes']:,} legacy; "
        f"{manual_metrics['idiomatic']['notes']:,} Idiomatic"
    )
    print(
        "  legacy evidence: "
        f"{manual_metrics['legacy']['reviews']:,} reviews; "
        f"{manual_metrics['legacy']['mature_cards']:,} mature cards"
    )
    print(f"manifest: {json_out}")

    if markdown_out:
        cross = [group for group in groups if "legacy_vs_idiomatic" in group["categories"]]
        lines = [
            "## Generated exact-collision audit",
            "",
            f"The conservative pass found {len(groups):,} exact bilingual surface-collision groups. "
            f"Of these, {categories['idiomatic_source_vs_pool']:,} are Idiomatic source-vs-pool "
            f"and {categories['legacy_vs_idiomatic']:,} cross generations.",
            "",
            "These are evidence candidates, not canonical identities. Sense resolution is deferred "
            "to the Expression Hub manifest. Target-only or punctuation-relaxed matches are excluded "
            "from these surface-collision groups and from automatic action.",
            "",
            "| Lang | Kind | Exact target | Exact English | Legacy notes | Idiomatic notes |",
            "|---|---|---|---|---:|---:|",
        ]
        for group in cross:
            notes = group["notes"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        md(group["language"]),
                        md(group["representation"]),
                        md(notes[0]["raw_target"]),
                        md(notes[0]["raw_english"]),
                        str(sum(note["lane"] == "legacy" for note in notes)),
                        str(sum(str(note["lane"]).startswith("idiomatic_") for note in notes)),
                    ]
                )
                + " |"
            )
        lines.extend(
            [
                "",
                "## Generated target-only manual-review queue",
                "",
                f"The separate review queue contains {manual_metrics['groups']:,} groups: "
                f"{manual_metrics['tiers']['strict_target_only']:,} preserve punctuation and "
                f"{manual_metrics['tiers']['punctuation_relaxed']:,} additionally relax Unicode "
                "punctuation/symbols. It covers "
                f"{manual_metrics['legacy']['notes']:,} legacy and "
                f"{manual_metrics['idiomatic']['notes']:,} Idiomatic notes. Legacy candidates "
                f"carry {manual_metrics['legacy']['reviews']:,} reviews and "
                f"{manual_metrics['legacy']['mature_cards']:,} mature cards.",
                "",
                "Every row is non-actionable evidence (`automatic_action=false`). English glosses "
                "are displayed precisely because a shared target surface can hide polysemy, task "
                "differences, or incompatible senses.",
                "",
                "| Tier | Lang | Kind | Target key | Legacy target / English | Idiomatic target / English | Legacy notes | Idiomatic notes | Legacy reviews | Legacy mature |",
                "|---|---|---|---|---|---|---:|---:|---:|---:|",
            ]
        )
        for group in manual_review_queue["groups"]:
            metrics = group["metrics"]
            tier = str(group["tier"]).replace("_", " ")
            legacy_evidence = (
                f"{candidate_values(group, 'legacy', 'raw_target')} / "
                f"{candidate_values(group, 'legacy', 'raw_english')}"
            )
            idiomatic_evidence = (
                f"{candidate_values(group, 'idiomatic', 'raw_target')} / "
                f"{candidate_values(group, 'idiomatic', 'raw_english')}"
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        md(tier),
                        md(group["language"]),
                        md(group["representation"]),
                        md(group["target_key"]),
                        legacy_evidence,
                        idiomatic_evidence,
                        str(metrics["legacy"]["notes"]),
                        str(metrics["idiomatic"]["notes"]),
                        str(metrics["legacy"]["reviews"]),
                        str(metrics["legacy"]["mature_cards"]),
                    ]
                )
                + " |"
            )
        markdown_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
