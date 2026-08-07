#!/usr/bin/env python3
"""Build the decision manifest for exact expression/sentence collisions."""

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
from _duplicates import collect_candidate_notes, collision_content_fingerprint, collision_groups


def md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


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
        invariants = collection_invariants(connection)
    finally:
        connection.close()

    manifest = {
        "schema_version": 1,
        "source_copy_sha256": sha256_file(copy_path),
        "identity_invariants": {
            key: invariants[key]
            for key in ("notes", "cards", "revlog", "note_identity_sha256")
        },
        "normalization": (
            "visible text; HTML/sound stripped; HTML-unescaped; Unicode NFKC; "
            "curly quotes/dashes stabilized; whitespace collapsed; case-folded; "
            "accents and punctuation preserved; both target and English must match"
        ),
        "content_sha256": collision_content_fingerprint(groups),
        "groups": groups,
    }
    json_out.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    categories = collections.Counter(
        category for group in groups for category in group["categories"]
    )
    lanes = collections.Counter(
        str(note["lane"]) for group in groups for note in group["notes"]
    )
    print(f"exact collision groups: {len(groups):,}")
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count:,}")
    for lane, count in sorted(lanes.items()):
        print(f"  notes in {lane}: {count:,}")
    print(f"manifest: {json_out}")

    if markdown_out:
        cross = [group for group in groups if "legacy_vs_idiomatic" in group["categories"]]
        lines = [
            "## Generated exact-collision audit",
            "",
            f"The conservative pass found {len(groups):,} actionable exact bilingual groups. "
            f"Of these, {categories['idiomatic_source_vs_pool']:,} are Idiomatic source-vs-pool "
            f"and {categories['legacy_vs_idiomatic']:,} cross generations.",
            "",
            "Target-only or punctuation-relaxed matches are deliberately excluded from mutation.",
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
        markdown_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
