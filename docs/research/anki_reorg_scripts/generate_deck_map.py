#!/usr/bin/env python3
"""Generate the exact per-current-deck migration appendix from the copy."""

from __future__ import annotations

import argparse
import collections
from pathlib import Path

from _common import (
    add_copy_path_argument,
    display_deck_name,
    read_only_connection,
    sha256_file,
    validated_copy_path,
    validated_output_path,
)
from _mapping import (
    DORMANT_ROOT,
    LANGUAGES,
    MANDARIN_ROOT,
    audio_card_destination,
    expression_card_destination,
    learning_card_destination,
    placement_card_destination,
    placement_rename_destination,
)


MAPPERS = (
    expression_card_destination,
    learning_card_destination,
    placement_card_destination,
    audio_card_destination,
)
SYSTEM_KEEP = {
    "Default",
    "Custom Study Session",
    "Lex-Stage · German vocab/idiom mnemonics (prototype)",
}
TARGET_PREFIXES = tuple(
    [DORMANT_ROOT, MANDARIN_ROOT] + [language.root for language in LANGUAGES.values()]
)


def md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def mapped_destination(deck: str, model: str) -> str | None:
    destinations = {destination for mapper in MAPPERS if (destination := mapper(deck, model))}
    if len(destinations) > 1:
        raise RuntimeError(f"conflicting mappings for {deck!r}/{model!r}: {destinations}")
    return next(iter(destinations), None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    copy_path = validated_copy_path(args.copy_path)
    output_path = validated_output_path(args.output, copy_path) if args.output else None
    connection = read_only_connection(copy_path)
    try:
        decks = {
            row["id"]: display_deck_name(row["name"])
            for row in connection.execute("SELECT id,name FROM decks")
        }
        direct: dict[int, list[dict[str, object]]] = collections.defaultdict(list)
        for row in connection.execute(
            """
            SELECT c.did, c.id, c.nid, c.ivl, c.reps, nt.name AS model
              FROM cards c JOIN notes n ON n.id=c.nid JOIN notetypes nt ON nt.id=n.mid
            """
        ):
            direct[row["did"]].append(dict(row))
        rows: list[dict[str, object]] = []
        for did, deck in sorted(decks.items(), key=lambda item: item[1].casefold()):
            cards = direct.get(did, [])
            rename_destination = placement_rename_destination(deck)
            destinations: dict[str, int] = collections.Counter()
            models = sorted({str(card["model"]) for card in cards}, key=str.casefold)
            for card in cards:
                destination = mapped_destination(deck, str(card["model"]))
                destinations[destination or "UNMAPPED"] += 1
            if rename_destination:
                action = (
                    "rename subtree in place + demote"
                    if rename_destination.startswith(f"{DORMANT_ROOT}::")
                    else "rename subtree in place"
                )
                destination_text = rename_destination
                mechanism = (
                    "Anki decks.rename runs once at the matched subtree root; "
                    "this deck row follows that rename with its deck id, config/metadata, "
                    "cards, scheduling and revlog intact."
                )
            elif not cards:
                if deck in SYSTEM_KEEP or deck.startswith(TARGET_PREFIXES):
                    action = "keep"
                    mechanism = "System/prototype/target shell; no mutation."
                elif deck.startswith("EXPERIMENTS-YT"):
                    action = "owner decision; then remove if empty"
                    mechanism = "Decision-gated; delete shell only after all descendant cards move."
                else:
                    action = "remove empty shell after descendants move"
                    mechanism = "Safe only after subtree evacuation; no notes/cards are deleted."
                destination_text = "—"
            elif deck == "Lex-Stage · German vocab/idiom mnemonics (prototype)":
                action = "keep untouched"
                destination_text = deck
                mechanism = "Hard constraint: no move and no note-model change."
            elif deck.startswith("EXPERIMENTS-YT"):
                action = "owner decision"
                destination_text = "PT Portuguese::1 Expressions::1 Fluency (recommended)"
                mechanism = "Move cards only, or suspend+demote; never delete reviewed notes."
            elif "UNMAPPED" in destinations:
                action = "manual review required"
                destination_text = "; ".join(f"{name} ({count})" for name, count in destinations.items())
                mechanism = "No draft phase will touch an unmapped card."
            else:
                destination_text = "; ".join(
                    f"{name} ({count})" for name, count in sorted(destinations.items())
                )
                if all(name.startswith(f"{DORMANT_ROOT}::Retired Idioms Audio") for name in destinations):
                    action = "move + suspend"
                    mechanism = "Anki set_deck + scheduler suspend; fields/GUID/revlog retained."
                elif any(name.startswith(f"{DORMANT_ROOT}::") for name in destinations):
                    action = "demote"
                    mechanism = "Anki set_deck; no note-model or scheduling conversion."
                elif any("::1 Expressions::" in name for name in destinations):
                    action = "merge by card move; dedupe separately"
                    mechanism = "Anki set_deck after provenance tagging; exact collisions are policy-gated."
                else:
                    action = "move"
                    mechanism = "Anki set_deck; note model, GUID, interval, due, reps and revlog unchanged."
            rows.append(
                {
                    "deck": deck,
                    "notes": len({int(card["nid"]) for card in cards}),
                    "cards": len(cards),
                    "mature": sum(int(card["ivl"]) > 21 for card in cards),
                    "reps": sum(int(card["reps"]) for card in cards),
                    "models": models,
                    "action": action,
                    "destination": destination_text,
                    "mechanism": mechanism,
                }
            )
    finally:
        connection.close()

    lines = [
        "## Exact per-current-deck migration map",
        "",
        f"Generated from copied collection SHA-256 `{sha256_file(copy_path)}`. There are {len(rows):,} current deck rows; every row appears once below. Counts are direct, not subtree counts.",
        "",
        "| Current deck | Notes | Cards | Mature | Reps | Model(s) | Action | Exact destination(s) | Mechanism / risk |",
        "|---|---:|---:|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md(row["deck"]),
                    f"{row['notes']:,}",
                    f"{row['cards']:,}",
                    f"{row['mature']:,}",
                    f"{row['reps']:,}",
                    md("; ".join(row["models"]) or "—"),
                    md(row["action"]),
                    md(row["destination"]),
                    md(row["mechanism"]),
                ]
            )
            + " |"
        )
    output = "\n".join(lines) + "\n"
    if output_path:
        output_path.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
