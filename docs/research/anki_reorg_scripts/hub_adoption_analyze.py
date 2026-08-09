#!/usr/bin/env python3
"""F4 adoption analyzer — READ-ONLY everywhere.

Joins three read-only sources:
  - the F3 phase-5 manifest's deferral list (self-checksummed);
  - the deferred notes' Pool-v1 fields from the collection COPY
    (validated work-area path, immutable read-only connection);
  - the FRESH server corpus with real durable ids
    (GET /admin/corpus-export?lang=… ; needs IDIOMATIC_ADMIN_TOKEN).

Emits to docs/research/hub_manifest/:
  fresh_server_extract.json  (+.sha256)  — compiler-shaped extract with
                                            real example ids
  adoption_plan.json         (+.sha256)  — checksummed INSERT plan
  ADOPTION_PLAN.md                       — counts + every deferred case

Never writes to the server, the collection, or the live DB.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from _common import (  # noqa: E402
    add_copy_path_argument,
    read_only_connection,
    sha256_file,
    validated_copy_path,
)

from idiomatic.hub import adoption, phase5  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
HUB_DIR = REPO / "docs" / "research" / "hub_manifest"
BASE = "https://idiomatic-app.onrender.com"
LANGS = ("de", "es", "fr", "it", "pt")


def fetch_corpus() -> tuple[list[dict], dict[str, str]]:
    import httpx
    token = os.environ.get("IDIOMATIC_ADMIN_TOKEN")
    if not token:
        raise SystemExit("IDIOMATIC_ADMIN_TOKEN not set "
                         "(source ~/.config/idiomatic-admin.env)")
    rows: list[dict] = []
    checksums: dict[str, str] = {}
    with httpx.Client(base_url=BASE, timeout=120.0,
                      headers={"X-Admin-Token": token}) as client:
        for lang in LANGS:
            response = client.get("/admin/corpus-export",
                                  params={"lang": lang})
            response.raise_for_status()
            checksums[lang] = phase5.sha256_bytes(response.content)
            for line in response.text.splitlines():
                if line.strip():
                    rows.append(json.loads(line))
    return rows, checksums


def note_fields_from_copy(copy_path: Path,
                          note_ids: list[int]) -> dict[int, dict]:
    """Map by field NAME from the notetype's own field list (migration
    doctrine: never map by bare ordinal)."""
    connection = read_only_connection(copy_path)
    try:
        names = [str(r["name"]) for r in connection.execute(
            "SELECT name FROM fields WHERE ntid=? ORDER BY ord",
            (phase5.POOL_MODEL_ID,))]
        out: dict[int, dict] = {}
        for start in range(0, len(note_ids), 5000):
            chunk = note_ids[start:start + 5000]
            marks = ",".join("?" for _ in chunk)
            for row in connection.execute(
                    f"SELECT id, mid, flds FROM notes WHERE id IN ({marks})",
                    chunk):
                if int(row["mid"]) != phase5.POOL_MODEL_ID:
                    continue  # not a Pool-v1 note; analyzer will defer it
                values = str(row["flds"]).split("\x1f")
                out[int(row["id"])] = dict(zip(names, values))
        return out
    finally:
        connection.close()


def build_fresh_extract(corpus_rows: list[dict]) -> dict:
    by_expr: dict[int, dict] = {}
    for row in corpus_rows:
        entry = by_expr.setdefault(int(row["expression_id"]), {
            "expression_id": int(row["expression_id"]),
            "lang": row["lang"],
            "idiom": row["idiom"],
            "explanation_en": row.get("explanation_en") or "",
            "examples": [],
        })
        if not entry["explanation_en"] and row.get("explanation_en"):
            entry["explanation_en"] = row["explanation_en"]
        if all(int(e["example_id"]) != int(row["example_id"])
               for e in entry["examples"]):
            entry["examples"].append({
                "example_id": int(row["example_id"]),
                "en_text": row["en_text"],
                "target_text": row["target_text"],
                "ord": row.get("ord"),
            })
    for entry in by_expr.values():
        entry["examples"].sort(key=lambda e: (e.get("ord") or 0,
                                              e["example_id"]))
        for example in entry["examples"]:
            example.pop("ord", None)
    return {"kind": "fresh-corpus-export",
            "expressions": sorted(by_expr.values(),
                                  key=lambda e: e["expression_id"])}


def write_md(plan: dict, path: Path) -> None:
    counts = plan["counts"]
    lines = [
        "# F4 adoption plan — analyzer output",
        "",
        f"> Generated {plan['generated_at']} (read-only pass; plan sha "
        f"`{plan['content_sha256'][:16]}…`). Nothing has been applied.",
        "",
        "| bucket | count |",
        "|---|---:|",
        f"| deferred cards in (from F3 manifest) | "
        f"{counts['deferred_input']:,} |",
        f"| resolved against fresh server examples (no insert needed) | "
        f"{counts['resolved_existing']:,} |",
        f"| proposed adoptions (new source + example rows) | "
        f"{counts['adoptions']:,} (reps {counts['adoption_reps']:,}) |",
        f"| still deferred | {counts['still_deferred']:,} |",
        "",
        f"Adoptions by language: {counts['by_lang_adoptions']}",
        f"Resolved by language: {counts['by_lang_resolved']}",
        f"Deferred by language: {counts['by_lang_deferred']}",
        "",
        "## Every deferred case",
        "",
    ]
    by_reason: dict[str, list[dict]] = {}
    for row in plan["deferred"]:
        by_reason.setdefault(row["reason"], []).append(row)
    for reason in sorted(by_reason):
        rows = by_reason[reason]
        lines.append(f"### {reason} ({len(rows)})")
        lines.append("")
        for row in rows:
            detail = f" — {row['detail']}" if row.get("detail") else ""
            lines.append(f"- card `{row['card_id']}` note "
                         f"`{row['note_id']}` [{row['language']}] "
                         f"reps={row['reps']}{detail}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_copy_path_argument(parser)
    parser.add_argument("--manifest", type=Path,
                        default=HUB_DIR / "phase5_manifest.json")
    parser.add_argument("--profile-key", default="syllabus")
    args = parser.parse_args()

    copy_path = validated_copy_path(args.copy_path)
    manifest = phase5.load_manifest(args.manifest)
    deferred_cards = manifest["gaps"]["deferred_cards"]
    print(f"deferred cards in: {len(deferred_cards):,}")

    c2_path = HUB_DIR / "C2_schedule_dossiers.json"
    c2 = json.loads(c2_path.read_text(encoding="utf-8"))
    c2_cards = {int(c["card_id"]): c for c in c2["cards"]}

    note_fields = note_fields_from_copy(
        copy_path, [int(c["note_id"]) for c in deferred_cards])
    print(f"note fields read from copy: {len(note_fields):,}")

    corpus_rows, corpus_checksums = fetch_corpus()
    print(f"fresh corpus rows: {len(corpus_rows):,}")

    extract = build_fresh_extract(corpus_rows)
    extract_path = HUB_DIR / "fresh_server_extract.json"
    extract_path.write_text(json.dumps(extract, ensure_ascii=False, indent=1),
                            encoding="utf-8")
    (HUB_DIR / "fresh_server_extract.json.sha256").write_text(
        sha256_file(extract_path) + "\n", encoding="utf-8")
    print(f"fresh extract: {extract_path} "
          f"({len(extract['expressions']):,} expressions)")

    plan = adoption.build_plan(
        deferred_cards=deferred_cards, note_fields=note_fields,
        corpus_rows=corpus_rows, manifest=manifest, c2_cards=c2_cards,
        profile_key=args.profile_key,
        inputs={
            "manifest_content_sha256": manifest["content_sha256"],
            "c2_file_sha256": sha256_file(c2_path),
            "collection_copy_sha256": sha256_file(copy_path),
            **{f"corpus_{lang}": sha for lang, sha
               in corpus_checksums.items()},
        })
    plan_path = HUB_DIR / "adoption_plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    (HUB_DIR / "adoption_plan.json.sha256").write_text(
        plan["content_sha256"] + "\n", encoding="utf-8")
    write_md(plan, HUB_DIR / "ADOPTION_PLAN.md")

    counts = plan["counts"]
    print(f"plan: {counts['adoptions']:,} adoptions "
          f"({counts['adoption_reps']:,} reps), "
          f"{counts['resolved_existing']:,} resolved-existing, "
          f"{counts['still_deferred']:,} still deferred")
    print(f"written: {plan_path} (sha {plan['content_sha256'][:16]}…)")


if __name__ == "__main__":
    main()
