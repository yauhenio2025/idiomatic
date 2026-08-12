#!/usr/bin/env python3
"""Pull the owner's collection headlessly and extract flagged cards.

The recurring flagged-review lane (docs/commissions/
FLAGGED_REVIEWS_REMEDIATION.md): each coordinator session runs this,
diffs against the committed manifest, and feeds NEW European items
through phase 1-2.

Usage (needs ANKIWEB_HKEY in the environment — prod env file):
    .venv/bin/python tools/pull_flagged_cards.py \
        [--out docs/research/flagged_reviews/flagged_cards.json] \
        [--baseline docs/research/flagged_reviews/flagged_cards.json]

Downloads to a scratch dir (download-only sync; the helper refuses
uploads), extracts every card with a flag, prints a diff against the
baseline manifest, and (with --out) rewrites the manifest.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from idiomatic.rescue_autopilot import _pull_collection_blocking  # noqa: E402

_PREVIEW_LEN = 120


def _preview(flds: str) -> list[str]:
    parts = flds.split("\x1f")
    out = []
    for p in parts[:2]:
        p = re.sub(r"<[^>]+>|\[sound:[^\]]+\]", "", p).strip()
        out.append(p[:_PREVIEW_LEN])
    return out


def extract_flagged(colpath: str) -> list[dict]:
    con = sqlite3.connect(f"file:{colpath}?mode=ro", uri=True)
    rows = con.execute(
        """SELECT c.id, n.id, n.guid, c.flags & 7, d.name, nt.name,
                  n.tags, n.flds
           FROM cards c
           JOIN notes n ON n.id = c.nid
           JOIN decks d ON d.id = c.did
           JOIN notetypes nt ON nt.id = n.mid
           WHERE c.flags & 7 != 0
           ORDER BY c.id""").fetchall()
    con.close()
    return [
        {"card_id": cid, "note_id": nid, "guid": guid, "flag": flag,
         "deck": deck, "model": model, "tags": tags.split(),
         "preview": _preview(flds)}
        for cid, nid, guid, flag, deck, model, tags, flds in rows
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None,
                    help="rewrite this manifest with the fresh pull")
    ap.add_argument(
        "--baseline",
        default="docs/research/flagged_reviews/flagged_cards.json")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="flagpull_") as workdir:
        colpath = _pull_collection_blocking(workdir)
        flagged = extract_flagged(colpath)

    print(f"flagged cards now: {len(flagged)}")

    baseline_path = REPO_ROOT / args.baseline
    if baseline_path.is_file():
        base = json.loads(baseline_path.read_text())
        base_rows = base if isinstance(base, list) else base.get("cards", [])
        base_ids = {r["card_id"] for r in base_rows}
        cur_ids = {r["card_id"] for r in flagged}
        new = [r for r in flagged if r["card_id"] not in base_ids]
        cleared = sorted(base_ids - cur_ids)
        print(f"baseline: {len(base_ids)} | NEW: {len(new)} | "
              f"cleared since baseline: {len(cleared)}")
        for r in new:
            print(f"  NEW flag{r['flag']} {r['card_id']} [{r['model']}] "
                  f"{r['deck']} :: {r['preview'][0][:80]}")
        if cleared:
            print(f"  cleared card_ids: {cleared}")
    else:
        print(f"no baseline at {baseline_path} — skipping diff")

    if args.out:
        out_path = REPO_ROOT / args.out
        out_path.write_text(json.dumps(flagged, ensure_ascii=False, indent=1))
        print(f"wrote {out_path} ({len(flagged)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
