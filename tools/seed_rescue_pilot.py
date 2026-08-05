#!/usr/bin/env python3
"""Seed the Rescue Lab from docs/research/rescue_pilot1/.

Creates the 9 pilot struggle items (glosses + anchors + failed sentences
from content.json) and the polysemy senses for «está tirado» (from
round2.json), then marks the cohort active at strike 1. Idempotent: the
struggles endpoint upserts on (lang, idiom) and the senses patch
replaces the whole list.

The pilot's generated binaries live in a session scratchpad, NOT the
repo — they are deliberately not imported; fresh assets are generated
through the dashboard (cheap: $0.03-0.07/image).

Usage:
    python tools/seed_rescue_pilot.py --base https://idiomatic-app.onrender.com \
        --token "$ADMIN_TOKEN"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PILOT = ROOT / "docs" / "research" / "rescue_pilot1"

_FAILS_RE = re.compile(r"(\d+)\s+Agains?\s+today,\s+(\d+)\s+in\s+14\s+days")


def call(base: str, token: str, method: str, path: str, body=None) -> dict:
    req = urllib.request.Request(
        base.rstrip("/") + path,
        method=method,
        data=json.dumps(body, ensure_ascii=False).encode() if body is not None else None,
        headers={"X-Admin-Token": token, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--token", required=True)
    args = ap.parse_args()

    content = json.loads((PILOT / "content.json").read_text(encoding="utf-8"))
    round2 = json.loads((PILOT / "round2.json").read_text(encoding="utf-8"))

    struggles = []
    for e in content["expressions"]:
        m = _FAILS_RE.search(e["fails"])
        if not m:
            print(f"!! can't parse fails for {e['id']}: {e['fails']!r}")
            return 1
        struggles.append({
            "lang": e["lang"],
            "idiom": e["idiom"],
            "gloss": e["gloss"],
            "fails_today": int(m.group(1)),
            "fails_14d": int(m.group(2)),
            "failed_sentences": [e["failed_sentence"]],
        })
    result = call(args.base, args.token, "POST", "/admin/rescue/struggles",
                  struggles)
    print(f"struggles: {result}")

    items = call(args.base, args.token, "GET", "/ui/api/rescue/items")["rows"]
    by_key = {(r["lang"], r["idiom"]): r for r in items}

    # Anchors + activate the pilot cohort (approved for rescue 2026-08-05).
    for e in content["expressions"]:
        row = by_key.get((e["lang"], e["idiom"]))
        if not row:
            print(f"!! item missing after upsert: {e['lang']}/{e['idiom']}")
            return 1
        call(args.base, args.token, "POST", f"/admin/rescue/item/{row['id']}",
             {"anchor": e["anchor"], "status": "active", "strike": 1})
        print(f"item {row['id']}: {e['lang']} {e['idiom']} — anchored, active")

    # Senses for está tirado, from the round-2 polysemy exemplar. Every
    # door taught: gloss + micro-example split on the em-dash.
    exemplar = next(x for x in round2["exemplars"] if x["key"] == "polysemy_es2")
    senses = []
    for s in exemplar["senses"]:
        tl, _, en = s["example"].partition(" — ")
        senses.append({"label": s["label"], "gloss": s["gloss"],
                       "example_tl": tl.strip(), "example_en": en.strip()})
    tirado = by_key[("es", "está tirado")]
    call(args.base, args.token, "POST", f"/admin/rescue/item/{tirado['id']}",
         {"senses": senses})
    print(f"senses: {len(senses)} doors on item {tirado['id']} (está tirado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
