#!/usr/bin/env python3
"""Build the 30-expression Expression Hub PILOT apkg (disposable).

Work package F2 of docs/commissions/HUB_BUILD_EXECUTION_COMMISSION.md.
Everything in the package is REAL, already-existing data: expressions +
examples from the server DB (admin API), staged TL/EN/context clips
(downloaded, never synthesized — no TTS, no paid provider calls), and
QA-passed campaign illustrations whose bytes are verified against the
judge's recorded SHA1 before use. The deck is disposable by name
("ZZ Hub Pilot (disposable)") and uses the pilot GUID namespace, so a
lingering import can never collide with a production release.

Usage:
  # selection + media fetch (needs network + IDIOMATIC_ADMIN_TOKEN, e.g.
  # `source ~/.config/idiomatic-admin.env`), then build:
  .venv/bin/python tools/build_hub_pilot.py --refresh

  # offline, reproducible rebuild from the committed selection + staged
  # media (what the coordinator should run to verify):
  .venv/bin/python tools/build_hub_pilot.py

Outputs (docs/research/hub_manifest/):
  pilot_selection.json  committed selection + coverage manifest
  pilot_media/          staged content-addressed media (gitignored)
  hub_pilot.apkg        the deliverable (gitignored; sha256 in selection)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from idiomatic.hub import apkg as hub_apkg  # noqa: E402
from idiomatic.hub import identity  # noqa: E402

BASE = "https://idiomatic-app.onrender.com"
HUB_DIR = REPO / "docs" / "research" / "hub_manifest"
MEDIA_DIR = HUB_DIR / "pilot_media"
SELECTION = HUB_DIR / "pilot_selection.json"
OUT_APKG = HUB_DIR / "hub_pilot.apkg"
ILLU_INPUT = REPO / "idiomatic" / "grammar" / "data" / "illustration_prompts" / "input"
QA_DIR = Path(os.environ.get("HUB_QA_DIR", "/srv/ai-models/outputs/factory"))

# Anything under ~2.5 KB is the known Gemini-TTS silence placeholder
# (~600 B mp3) or a truncated fetch — treat as absent, never ship it.
MIN_AUDIO_BYTES = 2500

ES_TARGET = 10          # ES carries the QA-passed images
OTHER_TARGET = 5        # de/fr/it/pt each
OTHER_LANGS = ["de", "fr", "it", "pt"]
MAX_PER_CHANNEL = 2


def _die(msg: str) -> None:
    raise SystemExit(f"build_hub_pilot: {msg}")


# --- campaign example-id index (committed input JSONs) ----------------------

def load_example_index() -> dict[int, list[dict]]:
    """expression_id -> ordered [{example_id, en_text, target_text}]."""
    index: dict[int, list[dict]] = {}
    for path in sorted(ILLU_INPUT.glob("*_illu_b*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            index[int(row["expression_id"])] = row["examples"]
    return index


def resolve_example_ids(expression_id: int, examples: list[dict],
                        index: dict[int, list[dict]]) -> list[int] | None:
    """Map the API's ord-ordered examples to durable example ids by EXACT
    text match against the frozen campaign export. Any mismatch → None
    (the expression is dropped; identity is never guessed)."""
    campaign = index.get(expression_id)
    if not campaign:
        return None
    by_target = {c["target_text"].strip(): int(c["example_id"]) for c in campaign}
    by_en = {c["en_text"].strip(): int(c["example_id"]) for c in campaign}
    ids: list[int] = []
    for ex in examples:
        eid = by_target.get(ex["target_text"].strip())
        if eid is None:
            eid = by_en.get(ex["en_text"].strip())
        if eid is None or eid in ids:
            return None
        ids.append(eid)
    return ids


# --- QA-passed image inventory ----------------------------------------------

def load_qa_images() -> dict[int, Path]:
    """example_id -> verified local image path (verdict=pass AND the local
    bytes hash to the judge's recorded sha1)."""
    verdicts = QA_DIR / "qa_mirror" / "verdicts.jsonl"
    if not verdicts.exists():
        print(f"  ! no verdicts at {verdicts} — pilot will have no images")
        return {}
    out: dict[int, Path] = {}
    for line in verdicts.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("verdict") != "pass":
            continue
        eid = int(r["example_id"])
        for cand in (QA_DIR / "corpus_images" / f"ex_{eid}.jpg",
                     QA_DIR / "qa_mirror" / "mac_corpus" / f"ex_{eid}.jpg"):
            if cand.exists():
                if hashlib.sha1(cand.read_bytes()).hexdigest() == r["sha1"]:
                    out[eid] = cand
                break
    return out


# --- admin API --------------------------------------------------------------

def api_client():
    import httpx
    token = os.environ.get("IDIOMATIC_ADMIN_TOKEN")
    if not token:
        _die("IDIOMATIC_ADMIN_TOKEN not set "
             "(source ~/.config/idiomatic-admin.env)")
    return httpx.Client(base_url=BASE, headers={"X-Admin-Token": token},
                        timeout=60.0)


def list_idiom_rows(client, lang: str, pages: int = 12) -> list[dict]:
    rows: list[dict] = []
    for page in range(pages):
        r = client.get("/ui/api/expressions",
                       params={"lang": lang, "limit": 100,
                               "offset": page * 100})
        r.raise_for_status()
        batch = r.json()["rows"]
        rows.extend(batch)
        if len(batch) < 100:
            break
    return rows


def fetch_detail(client, idiom_row_id: int) -> dict:
    r = client.get(f"/ui/api/expressions/{idiom_row_id}")
    r.raise_for_status()
    return r.json()


# --- selection ---------------------------------------------------------------

def select_pilot(client, index, qa_images) -> list[dict]:
    """Return 30 detail dicts (with resolved example_ids attached)."""
    chosen: list[dict] = []

    # ES: expressions with verified QA-passed images, ranked by coverage.
    qa_by_expr: dict[int, set[int]] = {}
    for line in (QA_DIR / "qa_mirror" / "verdicts.jsonl").read_text(
            encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("verdict") == "pass" and int(r["example_id"]) in qa_images:
            qa_by_expr.setdefault(int(r["expression_id"]), set()).add(
                int(r["example_id"]))

    es_rows = list_idiom_rows(client, "es")
    newest_row: dict[int, dict] = {}
    for row in es_rows:  # listing is newest-first
        newest_row.setdefault(int(row["expression_id"]), row)
    ranked = sorted(
        (e for e in qa_by_expr if e in newest_row),
        key=lambda e: (-len(qa_by_expr[e]),
                       newest_row[e].get("audio_context") is None, e))
    for expr_id in ranked:
        if sum(1 for c in chosen if c["lang"] == "es") >= ES_TARGET:
            break
        d = fetch_detail(client, int(newest_row[expr_id]["id"]))
        ids = resolve_example_ids(expr_id, d["examples"], index)
        if ids is None or len(d["examples"]) < 6:
            print(f"  - es expr {expr_id}: unresolved ids/examples, skipped")
            continue
        d["example_ids"] = ids
        chosen.append(d)

    # Other languages: newest rows with context audio, resolvable ids,
    # six examples, and channel variety.
    for lang in OTHER_LANGS:
        rows = list_idiom_rows(client, lang)
        per_channel: dict[int | None, int] = {}
        picked = 0
        for prefer_ctx in (True, False):
            if picked >= OTHER_TARGET:
                break
            for row in rows:
                if picked >= OTHER_TARGET:
                    break
                if bool(row.get("audio_context")) != prefer_ctx:
                    continue
                if any(int(c["expression_id"]) == int(row["expression_id"])
                       for c in chosen):
                    continue
                ch = row.get("channel_id")
                if per_channel.get(ch, 0) >= MAX_PER_CHANNEL:
                    continue
                if int(row["expression_id"]) not in index:
                    continue
                d = fetch_detail(client, int(row["id"]))
                if len(d["examples"]) < 6:
                    continue
                ids = resolve_example_ids(int(row["expression_id"]),
                                          d["examples"], index)
                if ids is None:
                    continue
                d["example_ids"] = ids
                chosen.append(d)
                per_channel[ch] = per_channel.get(ch, 0) + 1
                picked += 1

    total = len(chosen)
    if total != ES_TARGET + OTHER_TARGET * len(OTHER_LANGS):
        _die(f"selection incomplete: {total} expressions "
             f"({[(c['lang']) for c in chosen]})")
    return chosen


# --- media staging -----------------------------------------------------------

def _stage_bytes(data: bytes, name: str) -> str:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    (MEDIA_DIR / name).write_bytes(data)
    return name


def stage_media(client, chosen, qa_images) -> tuple[dict, dict]:
    """Download staged audio + copy verified images. Returns
    (media_map, coverage): media_map[(kind, key)] = basename."""
    jobs: list[tuple[str, str, str]] = []   # (kind, key, remote rel path)

    def add(kind: str, key, rel: str | None):
        if rel:
            jobs.append((kind, key, rel))

    for d in chosen:
        rid = int(d["id"])
        add("ctx", rid, d.get("audio_context"))
        add("expr", rid, d.get("audio_idiom_tgt"))
        for ex, eid in zip(d["examples"], d["example_ids"]):
            add("ex_en", eid, ex.get("audio_en"))
            add("ex_tl", eid, ex.get("audio_target"))

    media_map: dict[tuple[str, int], str] = {}
    misses: list[str] = []

    def fetch(job):
        kind, key, rel = job
        yt, _, fname = rel.partition("/")
        r = client.get(f"/ui/api/audio/{yt}/{fname}")
        if r.status_code != 200 or len(r.content) < MIN_AUDIO_BYTES:
            return kind, key, rel, None
        return kind, key, rel, r.content

    with ThreadPoolExecutor(max_workers=4) as pool:
        for kind, key, rel, data in pool.map(fetch, jobs):
            if data is None:
                misses.append(f"{kind}:{key}:{rel}")
                continue
            h8 = identity.hash8(data)
            if kind == "ctx":
                name = identity.context_media_name(key, h8)
            elif kind == "expr":
                name = identity.expression_audio_media_name(key, h8)
            elif kind == "ex_en":
                name = identity.example_audio_media_name(key, "en", h8)
            else:
                name = identity.example_audio_media_name(key, "tl", h8)
            media_map[(kind, key)] = _stage_bytes(data, name)

    n_img = 0
    for d in chosen:
        for eid in d["example_ids"]:
            src = qa_images.get(eid)
            if not src:
                continue
            data = src.read_bytes()
            name = identity.image_media_name(eid, identity.hash8(data))
            media_map[("img", eid)] = _stage_bytes(data, name)
            n_img += 1

    coverage = {
        "audio_files_staged": sum(1 for k in media_map if k[0] != "img"),
        "audio_misses": misses,
        "images_staged": n_img,
    }
    return {f"{k}:{v}": n for (k, v), n in media_map.items()}, coverage


# --- selection JSON <-> note rows -------------------------------------------

def compose_notes(chosen, media_map) -> tuple[list[dict], list[dict]]:
    def med(kind, key):
        return media_map.get(f"{kind}:{key}")

    hub_notes, example_notes = [], []
    for d in chosen:
        rid = int(d["id"])
        expr_id = int(d["expression_id"])
        lang = d["lang"]
        structured = d.get("structured") or {}
        sources = [{"title": d.get("video_title") or "",
                    "url": f"https://www.youtube.com/watch?v={d['youtube_id']}"
                           if d.get("youtube_id") else "",
                    "youtube_id": d.get("youtube_id")}]
        seen_yt = {d.get("youtube_id")}
        for re_row in (d.get("reencounters") or [])[:3]:
            if re_row.get("youtube_id") and re_row["youtube_id"] not in seen_yt:
                seen_yt.add(re_row["youtube_id"])
                sources.append({
                    "title": re_row.get("video_title") or "",
                    "url": ("https://www.youtube.com/watch?v="
                            + re_row["youtube_id"]),
                    "youtube_id": re_row["youtube_id"]})

        rail = []
        for ex, eid in zip(d["examples"], d["example_ids"]):
            rail.append({"example_id": eid,
                         "target_text": ex["target_text"],
                         "en_text": ex["en_text"],
                         "image_media": med("img", eid)})
            example_notes.append({
                "expression_id": expr_id, "example_id": eid, "lang": lang,
                "en_text": ex["en_text"], "target_text": ex["target_text"],
                "en_audio_media": med("ex_en", eid),
                "tl_audio_media": med("ex_tl", eid),
                "image_media": med("img", eid),
                "expression": d.get("citation_form") or d["idiom_text"],
                "gloss_en": d.get("english_gloss") or "",
                "source": sources[0],
                "origin": "initial",
            })

        hub_notes.append({
            "expression_id": expr_id, "lang": lang,
            "expression": d.get("citation_form") or d["idiom_text"],
            "gloss_en": d.get("english_gloss") or "",
            # PILOT ONLY: the full explanation stands in for the future
            # reviewed one-line compression (UsageLineEN) — see PILOT_NOTES.
            "usage_line_en": d.get("explanation_en") or "",
            "key_synonym": structured.get("synonyms_neutral") or None,
            "false_friend": (structured.get("false_friend")
                             or structured.get("pitfall") or None),
            "examples": rail,
            "sources": sources,
            "context_audio_media": med("ctx", rid),
            "expression_audio_media": med("expr", rid),
        })
    return hub_notes, example_notes


# --- phases ------------------------------------------------------------------

def refresh() -> None:
    index = load_example_index()
    qa_images = load_qa_images()
    print(f"campaign index: {len(index)} expressions; "
          f"verified QA images: {len(qa_images)}")
    with api_client() as client:
        chosen = select_pilot(client, index, qa_images)
        print("selected:", [(c["lang"], int(c["expression_id"]),
                             c["idiom_text"]) for c in chosen])
        media_map, coverage = stage_media(client, chosen, qa_images)
    hub_notes, example_notes = compose_notes(chosen, media_map)
    HUB_DIR.mkdir(parents=True, exist_ok=True)
    SELECTION.write_text(json.dumps({
        "note": "Expression Hub pilot selection (disposable). "
                "Rebuild offline: tools/build_hub_pilot.py",
        "hub_notes": hub_notes,
        "example_notes": example_notes,
        "coverage": coverage,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"selection written: {SELECTION}")
    print(f"coverage: {coverage['audio_files_staged']} audio staged, "
          f"{len(coverage['audio_misses'])} misses, "
          f"{coverage['images_staged']} images")


def build(out_name: str = "hub_pilot.apkg") -> None:
    out_path = HUB_DIR / out_name
    if not SELECTION.exists():
        _die(f"{SELECTION} missing — run with --refresh first")
    sel = json.loads(SELECTION.read_text(encoding="utf-8"))
    names: set[str] = set()
    for h in sel["hub_notes"]:
        names.update(filter(None, (h.get("context_audio_media"),
                                   h.get("expression_audio_media"))))
        names.update(filter(None, (e.get("image_media")
                                   for e in h["examples"])))
    for e in sel["example_notes"]:
        names.update(filter(None, (e.get("en_audio_media"),
                                   e.get("tl_audio_media"),
                                   e.get("image_media"))))
    media_files = []
    for n in sorted(names):
        p = MEDIA_DIR / n
        if not p.exists():
            _die(f"staged media missing: {p} — rerun --refresh")
        media_files.append(p)
    n_hub, n_ex = hub_apkg.build_hub_apkg(
        out_path=out_path, hub_notes=sel["hub_notes"],
        example_notes=sel["example_notes"], media_files=media_files,
        pilot=True)
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(f"built {out_path}")
    print(f"  hub notes {n_hub} (x2 cards), example notes {n_ex}, "
          f"media {len(media_files)}, sha256 {sha[:16]}…")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true",
                    help="reselect from the server + refetch media first")
    ap.add_argument("--out", default="hub_pilot.apkg",
                    help="output apkg basename inside hub_manifest/")
    args = ap.parse_args()
    if args.refresh:
        refresh()
    build(args.out)
