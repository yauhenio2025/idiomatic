#!/usr/bin/env python3
"""Reproduce the factual inventory from an extracted Anki backup copy.

This script is intentionally read-only. It uses SQLite's immutable mode and
never instantiates ``anki.collection.Collection``, because opening an older
collection through Anki can migrate it. The phase scripts use Anki's public
Collection APIs for mutations on an approved copy.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.metadata
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from _common import (
    add_copy_path_argument,
    display_deck_name,
    read_only_connection,
    sha256_file,
    validated_copy_path,
    validated_output_path,
)
from _media import media_references


FIELD_SEPARATOR = "\x1f"


@dataclass
class DeckStats:
    direct_card_ids: set[int] = field(default_factory=set)
    direct_note_ids: set[int] = field(default_factory=set)
    direct_mature: int = 0
    direct_reps: int = 0
    direct_revlog: int = 0
    direct_models: set[int] = field(default_factory=set)
    subtree_card_ids: set[int] = field(default_factory=set)
    subtree_note_ids: set[int] = field(default_factory=set)
    subtree_mature: int = 0
    subtree_reps: int = 0
    subtree_revlog: int = 0


def ancestors(name: str, available: set[str]) -> Iterable[str]:
    parts = name.split("::")
    for length in range(1, len(parts) + 1):
        candidate = "::".join(parts[:length])
        if candidate in available:
            yield candidate


def md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def tag_bucket(tag: str) -> str:
    folded = tag.casefold()
    if "::" in tag:
        return f"hierarchical::{tag.split('::', 1)[0]}"
    if folded in {"de", "es", "fr", "it", "pt", "mandarin", "zh"}:
        return "language"
    if folded in {
        "youtube",
        "pimsleur",
        "chinesepod",
        "idiomatic-cloud",
        "idiomatic-pool",
        "fluency-pool",
        "idiom-audio",
        "idiomatic-grammar",
        "idiomatic-exercises",
        "idiomatic-translation",
        "idiomatic-tenses",
    }:
        return "system/family"
    if re.fullmatch(r"level[-_]?[0-9]+", folded):
        return "level"
    if re.fullmatch(r"lesson[-_].+", folded):
        return "lesson"
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", tag):
        return "youtube-id-like"
    if "-" in tag and len(tag) >= 24:
        return "video-slug-like"
    return "other-flat"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    parser.add_argument("--json-out", type=Path, help="Optional evidence JSON path.")
    parser.add_argument(
        "--markdown-out", type=Path, help="Optional generated Markdown appendix path."
    )
    parser.add_argument("--top-tags", type=int, default=200)
    args = parser.parse_args()

    copy_path = validated_copy_path(args.copy_path)
    json_out = validated_output_path(args.json_out, copy_path) if args.json_out else None
    markdown_out = (
        validated_output_path(args.markdown_out, copy_path) if args.markdown_out else None
    )
    connection = read_only_connection(copy_path)
    try:
        deck_names = {
            row["id"]: display_deck_name(row["name"])
            for row in connection.execute("SELECT id, name FROM decks")
        }
        deck_ids = {name: did for did, name in deck_names.items()}
        available_names = set(deck_ids)
        model_names = {
            row["id"]: row["name"]
            for row in connection.execute("SELECT id, name FROM notetypes")
        }
        model_codes = {
            mid: f"M{index:02d}"
            for index, (mid, _) in enumerate(
                sorted(model_names.items(), key=lambda item: item[1].casefold()), start=1
            )
        }

        reviews_by_card = dict(
            connection.execute("SELECT cid, COUNT(*) FROM revlog GROUP BY cid")
        )
        stats = {name: DeckStats() for name in available_names}
        for row in connection.execute(
            """
            SELECT c.id, c.nid, c.did, c.ivl, c.reps, n.mid
              FROM cards c
              JOIN notes n ON n.id = c.nid
            """
        ):
            name = deck_names[row["did"]]
            review_count = reviews_by_card.get(row["id"], 0)
            direct = stats[name]
            direct.direct_card_ids.add(row["id"])
            direct.direct_note_ids.add(row["nid"])
            direct.direct_mature += row["ivl"] > 21
            direct.direct_reps += row["reps"]
            direct.direct_revlog += review_count
            direct.direct_models.add(row["mid"])
            for parent in ancestors(name, available_names):
                subtree = stats[parent]
                subtree.subtree_card_ids.add(row["id"])
                subtree.subtree_note_ids.add(row["nid"])
                subtree.subtree_mature += row["ivl"] > 21
                subtree.subtree_reps += row["reps"]
                subtree.subtree_revlog += review_count

        model_rows: list[dict[str, object]] = []
        for mid, name in sorted(model_names.items(), key=lambda item: item[1].casefold()):
            fields = [
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM fields WHERE ntid=? ORDER BY ord", (mid,)
                )
            ]
            templates = [
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM templates WHERE ntid=? ORDER BY ord", (mid,)
                )
            ]
            uses = list(
                connection.execute(
                    """
                    SELECT c.did, COUNT(DISTINCT n.id) AS notes, COUNT(c.id) AS cards,
                           SUM(c.ivl > 21) AS mature, SUM(c.reps) AS reps
                      FROM notes n
                      JOIN cards c ON c.nid=n.id
                     WHERE n.mid=?
                     GROUP BY c.did
                    """,
                    (mid,),
                )
            )
            model_rows.append(
                {
                    "code": model_codes[mid],
                    "id": mid,
                    "name": name,
                    "fields": fields,
                    "templates": templates,
                    "notes": connection.execute(
                        "SELECT COUNT(*) FROM notes WHERE mid=?", (mid,)
                    ).fetchone()[0],
                    "cards": sum(row["cards"] for row in uses),
                    "mature": sum((row["mature"] or 0) for row in uses),
                    "reps": sum((row["reps"] or 0) for row in uses),
                    "deck_uses": [
                        {
                            "deck": deck_names[row["did"]],
                            "notes": row["notes"],
                            "cards": row["cards"],
                        }
                        for row in sorted(uses, key=lambda item: deck_names[item["did"]].casefold())
                    ],
                }
            )

        tag_counts: collections.Counter[str] = collections.Counter()
        notes_without_tags = 0
        media_counts: collections.Counter[str] = collections.Counter()
        media_by_model: dict[int, set[str]] = collections.defaultdict(set)
        for row in connection.execute("SELECT mid, tags, flds FROM notes"):
            tags = row["tags"].strip().split()
            if not tags:
                notes_without_tags += 1
            tag_counts.update(tags)
            for reference in media_references(row["flds"]):
                media_counts[reference] += 1
                media_by_model[row["mid"]].add(reference)

        tag_buckets: collections.Counter[str] = collections.Counter()
        for tag, count in tag_counts.items():
            tag_buckets[tag_bucket(tag)] += count

        totals = {
            "decks": len(deck_names),
            "empty_direct_decks": sum(not item.direct_card_ids for item in stats.values()),
            "empty_subtree_decks": sum(not item.subtree_card_ids for item in stats.values()),
            "notes": connection.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
            "notes_with_cards": connection.execute(
                "SELECT COUNT(DISTINCT nid) FROM cards"
            ).fetchone()[0],
            "cards": connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0],
            "new_cards": connection.execute(
                "SELECT COUNT(*) FROM cards WHERE type=0"
            ).fetchone()[0],
            "learning_or_relearning_cards": connection.execute(
                "SELECT COUNT(*) FROM cards WHERE type IN (1,3)"
            ).fetchone()[0],
            "review_state_cards": connection.execute(
                "SELECT COUNT(*) FROM cards WHERE type=2"
            ).fetchone()[0],
            "suspended_cards": connection.execute(
                "SELECT COUNT(*) FROM cards WHERE queue=-1"
            ).fetchone()[0],
            "buried_cards": connection.execute(
                "SELECT COUNT(*) FROM cards WHERE queue IN (-2,-3)"
            ).fetchone()[0],
            "filtered_deck_cards": connection.execute(
                "SELECT COUNT(*) FROM cards WHERE odid != 0 OR odue != 0"
            ).fetchone()[0],
            "mature_cards": connection.execute(
                "SELECT COUNT(*) FROM cards WHERE ivl > 21"
            ).fetchone()[0],
            "card_reps": connection.execute("SELECT COALESCE(SUM(reps), 0) FROM cards").fetchone()[0],
            "revlog_rows": connection.execute("SELECT COUNT(*) FROM revlog").fetchone()[0],
            "revlog_rows_for_current_cards": connection.execute(
                "SELECT COUNT(*) FROM revlog WHERE cid IN (SELECT id FROM cards)"
            ).fetchone()[0],
            "orphaned_revlog_rows": connection.execute(
                """SELECT COUNT(*) FROM revlog r
                     WHERE NOT EXISTS (SELECT 1 FROM cards c WHERE c.id=r.cid)"""
            ).fetchone()[0],
            "orphan_notes": connection.execute(
                """SELECT COUNT(*) FROM notes n
                     WHERE NOT EXISTS (SELECT 1 FROM cards c WHERE c.nid=n.id)"""
            ).fetchone()[0],
            "note_models": len(model_names),
            "registered_tags": connection.execute("SELECT COUNT(*) FROM tags").fetchone()[0],
            "used_tags": len(tag_counts),
            "notes_without_tags": notes_without_tags,
            "referenced_media_files": len(media_counts),
            "media_reference_occurrences": sum(media_counts.values()),
        }

        evidence = {
            "copy": {
                "path": str(copy_path),
                "bytes": copy_path.stat().st_size,
                "sha256": sha256_file(copy_path),
                "anki_python_version": importlib.metadata.version("anki"),
                "sqlite_version": __import__("sqlite3").sqlite_version,
            },
            "totals": totals,
            "decks": [
                {
                    "id": deck_ids[name],
                    "name": name,
                    "direct_notes": len(stats[name].direct_note_ids),
                    "direct_cards": len(stats[name].direct_card_ids),
                    "direct_mature": stats[name].direct_mature,
                    "direct_reps": stats[name].direct_reps,
                    "direct_revlog": stats[name].direct_revlog,
                    "subtree_notes": len(stats[name].subtree_note_ids),
                    "subtree_cards": len(stats[name].subtree_card_ids),
                    "subtree_mature": stats[name].subtree_mature,
                    "subtree_reps": stats[name].subtree_reps,
                    "subtree_revlog": stats[name].subtree_revlog,
                    "models": sorted(model_codes[mid] for mid in stats[name].direct_models),
                }
                for name in sorted(available_names, key=lambda value: [p.casefold() for p in value.split("::")])
            ],
            "models": model_rows,
            "tags": {
                "buckets_by_note_assignments": dict(sorted(tag_buckets.items())),
                "top": tag_counts.most_common(args.top_tags),
            },
            "media": {
                "by_model": {
                    model_codes[mid]: len(files) for mid, files in media_by_model.items()
                },
                "top_duplicate_references": media_counts.most_common(100),
            },
        }

        if json_out:
            json_out.write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

        lines = [
            "## Generated collection totals",
            "",
            "| Metric | Count |",
            "|---|---:|",
        ]
        lines.extend(f"| {md_escape(key)} | {value:,} |" for key, value in totals.items())
        lines.extend(
            [
                "",
                "## Generated full deck tree",
                "",
                "Counts are attributed to each card's current deck. `Mature` means `ivl > 21`; `revlog` is joined to cards that still exist. Parent rows show subtree totals, while `direct` columns show only cards physically assigned to that deck.",
                "",
                "| Current deck | Direct notes | Direct cards | Subtree notes | Subtree cards | Mature subtree | Reps subtree | Revlog subtree | Models on direct cards |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        for row in evidence["decks"]:
            depth = str(row["name"]).count("::")
            label = f"{'↳ ' * depth}{row['name']}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_escape(label),
                        f"{row['direct_notes']:,}",
                        f"{row['direct_cards']:,}",
                        f"{row['subtree_notes']:,}",
                        f"{row['subtree_cards']:,}",
                        f"{row['subtree_mature']:,}",
                        f"{row['subtree_reps']:,}",
                        f"{row['subtree_revlog']:,}",
                        ", ".join(row["models"]) or "—",
                    ]
                )
                + " |"
            )

        lines.extend(
            [
                "",
                "## Generated note-model catalog",
                "",
                "The model code is used in the deck-tree table. Full per-deck use remains in the JSON output to keep this catalog readable.",
                "",
                "| Code | Note model (ID) | Notes | Cards | Mature | Fields in stored order | Templates |",
                "|---|---|---:|---:|---:|---|---|",
            ]
        )
        for row in model_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row["code"]),
                        md_escape(f"{row['name']} ({row['id']})"),
                        f"{row['notes']:,}",
                        f"{row['cards']:,}",
                        f"{row['mature']:,}",
                        md_escape(" · ".join(row["fields"])),
                        md_escape(" · ".join(row["templates"])),
                    ]
                )
                + " |"
            )

        lines.extend(
            [
                "",
                "## Generated tag summary",
                "",
                "| Taxonomy bucket | Note-tag assignments |",
                "|---|---:|",
            ]
        )
        for bucket, count in sorted(tag_buckets.items()):
            lines.append(f"| {md_escape(bucket)} | {count:,} |")
        lines.extend(
            [
                "",
                f"Top {args.top_tags} tags:",
                "",
                "| Tag | Notes |",
                "|---|---:|",
            ]
        )
        lines.extend(f"| {md_escape(tag)} | {count:,} |" for tag, count in tag_counts.most_common(args.top_tags))
        markdown = "\n".join(lines) + "\n"
        if markdown_out:
            markdown_out.write_text(markdown, encoding="utf-8")
        else:
            print(markdown, end="")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
