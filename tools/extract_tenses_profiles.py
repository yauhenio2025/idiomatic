#!/usr/bin/env python3
"""Extract per-language "worst verbs × tenses" profiles from the old
account's `_tenses_old` conjugation decks (evgeny.morozov+2@gmail.com,
14,267 cards / 176k reviews 2015-2022; see memory tenses-old-corpus).

Runs on the operator's machine against the local collection (read-only,
immutable URI — safe with Anki open). Outputs, error-mine-profile
style, into docs/research/tenses-profiles/:

  - {lang}.md            human profile: worst verb×tense + tense rollup
  - tenses_priors.json   machine-readable prior for generators
                         (verb, tense, gloss, paradigm, stats)

The paradigm strings are copied from the deck backs (attested source,
occasional typos — e.g. vir imperfect-subj "viessesele") — any future
card build MUST re-verify forms through grammar/morphology.py, never
trust these verbatim.

Usage: .venv/bin/python tools/extract_tenses_profiles.py
"""

from __future__ import annotations

import datetime
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

COLLECTION = ("/home/admin/.var/app/net.ankiweb.Anki/data/Anki2/"
              "evgeny.morozov+2@gmail.com/collection.anki2")
OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "research" / "tenses-profiles"

SUBDECK_LANG = {
    "tenses_french_kolya": "fr",
    "tenses_german_corrected": "de",
    "tenses_italian_kolya": "it",
    "tenses_portuguese_kolya": "pt",
    "tenses_spanish_kolya": "es",
}
LANG_NAMES = {"fr": "French", "de": "German", "it": "Italian",
              "pt": "Portuguese", "es": "Spanish"}

# Front format variants: "verb; _de _simple_past" / "vir;_pt_present" /
# "décrire;_fr_passé_composé" (accented tags) / "oser;_fr" (no tense tag —
# kept as "(untagged)"; still useful for verb-level difficulty).
_FRONT_RE = re.compile(
    r"^\s*(?P<verb>[^;]+?)\s*;\s*_(?P<lang>[a-z]{2})(?:\s*_?(?P<tense>[\w'’]+))?\s*$",
    re.UNICODE)

TOP_N_MD = 30
TOP_N_JSON = 60


def ts(ms: int | None) -> str:
    if not ms:
        return "?"
    return datetime.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")


def main() -> int:
    db = sqlite3.connect(f"file:{COLLECTION}?immutable=1", uri=True)
    db.create_collation(
        "unicase", lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))

    decks = {i: n.replace("\x1f", "::") for i, n in
             db.execute("SELECT id, name FROM decks")}
    did_lang = {}
    for did, name in decks.items():
        parts = name.split("::")
        if parts[0] == "_tenses_old" and len(parts) > 1:
            lang = SUBDECK_LANG.get(parts[1])
            if lang:
                did_lang[did] = lang

    rows = []
    unparsed = 0
    for did, lang in did_lang.items():
        for cid, flds, reps, lapses, factor in db.execute(
                """SELECT c.id, n.flds, c.reps, c.lapses, c.factor
                   FROM cards c JOIN notes n ON n.id = c.nid
                   WHERE c.did = ?""", (did,)):
            front, _, back = flds.partition("\x1f")
            m = _FRONT_RE.match(front)
            if not m:
                unparsed += 1
                continue
            gloss, _, paradigm = back.partition(";")
            first, last, n_rev = db.execute(
                "SELECT MIN(id), MAX(id), COUNT(*) FROM revlog WHERE cid = ?",
                (cid,)).fetchone()
            rows.append({
                "lang": lang,
                "verb": m.group("verb").strip(),
                "tense": (m.group("tense") or "(untagged)").strip("_"),
                "gloss": gloss.strip(),
                "paradigm": paradigm.strip(),
                "reps": reps, "lapses": lapses,
                "ease_pct": round(factor / 10),
                "lapse_rate": round(lapses / reps, 3) if reps else 0.0,
                "first_review": ts(first), "last_review": ts(last),
                "n_reviews": n_rev,
            })
    db.close()

    by_lang: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_lang[r["lang"]].append(r)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    priors = {
        "meta": {
            "source": "_tenses_old decks, old account (evgeny.morozov+2@gmail.com)",
            "review_span": "2015-07-26 .. 2022-08-21",
            "extracted": datetime.date.today().isoformat(),
            "grain": "one row per verb x tense CARD (whole-paradigm cards; "
                     "per-person failure is NOT distinguishable in this "
                     "corpus — new drills should split persons)",
            "warning": "paradigm strings are attested deck backs with "
                       "occasional typos; re-verify via grammar/morphology.py "
                       "before shipping any card",
        },
        "langs": {},
    }

    for lang in sorted(by_lang):
        cards = sorted(by_lang[lang], key=lambda r: (-r["lapses"], -r["reps"]))
        priors["langs"][lang] = [
            {k: r[k] for k in ("verb", "tense", "gloss", "paradigm", "reps",
                               "lapses", "ease_pct", "lapse_rate",
                               "last_review")}
            for r in cards[:TOP_N_JSON]
        ]

        # tense rollup
        tense_agg: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
        for r in cards:
            a = tense_agg[r["tense"]]
            a[0] += 1
            a[1] += r["reps"]
            a[2] += r["lapses"]

        n_cards = len(cards)
        n_studied = sum(1 for r in cards if r["reps"])
        tot_reps = sum(r["reps"] for r in cards)
        tot_lapses = sum(r["lapses"] for r in cards)

        md = [
            f"# {LANG_NAMES[lang]} — worst verbs × tenses "
            f"(_tenses_old corpus)",
            "",
            f"> Extracted {datetime.date.today().isoformat()} by "
            f"`tools/extract_tenses_profiles.py` from the old account's "
            f"conjugation decks: {n_cards} cards ({n_studied} studied), "
            f"{tot_reps} reviews, {tot_lapses} lapses, span 2015-07 .. "
            f"2022-08. Cards drilled WHOLE paradigms — per-person failure "
            f"is not recoverable; new drills split persons.",
            "",
            "## Worst cards (by lapses)",
            "",
            "| # | verb | tense | lapses | reps | lapse rate | ease | last seen |",
            "|---|------|-------|--------|------|------------|------|-----------|",
        ]
        for i, r in enumerate(cards[:TOP_N_MD], 1):
            md.append(
                f"| {i} | {r['verb']} | {r['tense']} | {r['lapses']} | "
                f"{r['reps']} | {r['lapse_rate']:.0%} | {r['ease_pct']}% | "
                f"{r['last_review']} |")
        md += [
            "",
            "## Tense rollup (all cards)",
            "",
            "| tense | cards | reps | lapses | lapses/card |",
            "|-------|-------|------|--------|-------------|",
        ]
        for tense, (n, reps, lapses) in sorted(
                tense_agg.items(), key=lambda kv: -kv[1][2]):
            md.append(f"| {tense} | {n} | {reps} | {lapses} | "
                      f"{lapses / n:.1f} |")
        md.append("")
        (OUT_DIR / f"{lang}.md").write_text("\n".join(md), encoding="utf-8")
        print(f"{lang}: {n_cards} cards, top lapser: "
              f"{cards[0]['verb']} {cards[0]['tense']} "
              f"({cards[0]['lapses']} lapses)")

    (OUT_DIR / "tenses_priors.json").write_text(
        json.dumps(priors, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"unparsed fronts: {unparsed}")
    print(f"wrote {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
