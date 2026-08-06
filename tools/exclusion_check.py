#!/usr/bin/env python3
"""Mandarin Memory Palace exclusion checker (famous-cast amendment).
No args: print roster. Args or stdin lines: check candidate names."""
import json, re, sys, unicodedata
from pathlib import Path

DATA = Path.home() / "projects/mandarin-videos/data"
WORKER = Path.home() / "projects/mandarin-videos/worker/batch_first10_words.py"

def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()

def load_roster():
    names = {}
    def add(name, src):
        name = (name or "").strip()
        if not name or name.startswith("[TBD"):
            return
        key = " ".join(norm(name)) or name.lower()
        names.setdefault(key, [name, set()])[1].add(src)
    for x in json.load(open(DATA / "actors.json")):
        add(x.get("Actor"), "actors.json")
    for x in json.load(open(DATA / "actor-signature-wardrobe-2026-06-15.json")):
        add(x.get("name"), "signoff55")
    for x in json.load(open(DATA / "actor-archetype-snapshot-2026-05-28.json")):
        add(x.get("name"), "archetype-snapshot")
    for x in json.load(open(DATA / "actor-audit-2026-07-20.json")):
        add(x.get("name"), "audit-2026-07-20")
    for r in json.load(open(DATA / "actor-backfill-snapshot-2026-04-11.json")):
        add((r.get("actor") or {}).get("name"), "backfill-snapshot")
    return names

LIKENESS_RING = {
    "Tom Hanks": "IS Forrest Gump (fu-) / Woody voice",
    "Ben Stiller": "IS Zoolander",
    "Omar Sy": "IS Lupin, Netflix (lu-)",
    "Malcolm McDowell": "IS the Droog from Clockwork Orange (ru-)",
    "Aleksandr Demyanenko": "IS Shurik (shu-)",
    "Yuri Nikulin": "Brilliantovaya Ruka lead (shu- attribution ambiguity)",
    "Boris Babochkin": "IS Chapayev (ch-)",
}

def load_redact_names():
    src = WORKER.read_text()
    alts = re.findall(r'r"\\b\((.*?)\)\\b"', src, re.S)
    toks = set()
    for a in alts:
        a = re.sub(r'"\s*\n\s*r"', "", a)
        for t in a.split("|"):
            t = t.replace("\\xe9", "é").strip()
            if re.fullmatch(r"[A-Za-zé\- ]+", t) and t[:1].isupper():
                toks.add(t)
    return toks

def check(candidate, roster, redact):
    ctoks = norm(candidate)
    ckey = " ".join(ctoks)
    csurname = ctoks[-1] if ctoks else ""
    hits = []
    for key, (display, srcs) in roster.items():
        rtoks = key.split()
        if ckey == key:
            return ("EXCLUDED", f"full-name match: {display}")
        if csurname and len(csurname) > 2 and rtoks and csurname == rtoks[-1]:
            hits.append(("EXCLUDED", f"surname match: {display}"))
        elif set(ctoks) & {t for t in rtoks if len(t) > 2}:
            hits.append(("NEAR", f"shares token with anchor: {display}"))
    for ln, why in LIKENESS_RING.items():
        if " ".join(norm(ln)) == ckey:
            hits.insert(0, ("REDACT", f"likeness ring: {why}"))
    for t in redact:
        if " ".join(norm(t)) == ckey or (len(ctoks) > 1 and set(norm(t)) >= set(ctoks)):
            hits.insert(0, ("REDACT", f"worker REDACT list: '{t}'"))
    if hits:
        hits.sort(key=lambda h: {"EXCLUDED": 0, "REDACT": 1, "NEAR": 2}[h[0]])
        return hits[0]
    return ("OK", "")

if __name__ == "__main__":
    roster, redact = load_roster(), load_redact_names()
    cands = sys.argv[1:] or [l.strip() for l in sys.stdin if l.strip()]
    if not cands:
        for key in sorted(roster):
            d, s = roster[key]
            print(f"{d:45s} [{', '.join(sorted(s))}]")
    else:
        for c in cands:
            v, why = check(c, roster, redact)
            print(f"{v:9s} {c:35s} {why}")
