#!/usr/bin/env python3
"""QA reporting: ledger -> DAILY.md summary, contact sheets, and the
spot-review package (stratified sample of verdicts for the human gate).

Runs wherever the ledger lives (the Mac); PIL + stdlib only.
"""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_ledger(path):
    rows = []
    if Path(path).exists():
        for line in open(path):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def latest_per_example(rows):
    latest = {}
    for r in rows:
        latest[r["example_id"]] = r  # file order == chronological
    return latest


def tile(img_path, caption, size=384, bar=46):
    cell = Image.new("RGB", (size, size + bar), "white")
    try:
        im = Image.open(img_path).convert("RGB")
        im.thumbnail((size, size), Image.LANCZOS)
        cell.paste(im, ((size - im.width) // 2, (size - im.height) // 2))
    except Exception:  # noqa: BLE001
        ImageDraw.Draw(cell).text((10, size // 2), "missing image",
                                  fill="red")
    d = ImageDraw.Draw(cell)
    try:
        font = ImageFont.load_default(size=15)
    except TypeError:
        font = ImageFont.load_default()
    d.rectangle([0, size, size, size + bar], fill="black")
    d.text((6, size + 4), caption[:2 * (size // 8)], fill="white", font=font)
    return cell


def montage(entries, out_path, cols=4, size=384, bar=46):
    """entries: [(img_path, caption)]"""
    if not entries:
        return None
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * size, rows * (size + bar)), "white")
    for i, (p, cap) in enumerate(entries):
        sheet.paste(tile(p, cap, size, bar),
                    ((i % cols) * size, (i // cols) * (size + bar)))
    sheet.save(out_path, quality=88)
    return out_path


def spot_sample(latest, n):
    """Stratified: cover every fail class, judge errors, then passes."""
    by_bucket = {}
    for r in latest.values():
        if r["verdict"] == "fail":
            key = tuple(sorted(r.get("fail_classes") or ["?"]))
        else:
            key = (r["verdict"],)  # pass / judge_error
        by_bucket.setdefault(key, []).append(r)
    for v in by_bucket.values():
        v.sort(key=lambda r: r["example_id"])
    picked, i = [], 0
    buckets = sorted(by_bucket, key=lambda k: (k == ("pass",), k))
    while len(picked) < n and any(by_bucket.values()):
        b = buckets[i % len(buckets)]
        if by_bucket[b]:
            picked.append(by_bucket[b].pop(0))
        i += 1
        if i > 10 * n:
            break
    return picked


def failed_checks(r):
    return [k for k, v in (r.get("checks") or {}).items() if v == 0]


def build_spot_review(latest, out_dir, n, index=None):
    picked = spot_sample(latest, n)
    entries, lines = [], []
    lines.append("# QA spot review — judge verdicts for your gate\n")
    lines.append("Reply per row: agree / disagree (+ note). The repair "
                 "loop stays DISARMED until you sign off.\n")
    lines.append("| # | example | verdict | fail classes | failed checks | idiom | sentence |")
    lines.append("|---|---------|---------|--------------|---------------|-------|----------|")
    for i, r in enumerate(picked, 1):
        cap = f"#{i} ex_{r['example_id']} {r['verdict'].upper()}"
        if r.get("fail_classes"):
            cap += " " + ",".join(r["fail_classes"])
        entries.append((r["image"], cap))
        rec = (index or {}).get(r["example_id"], {})
        lines.append(
            f"| {i} | ex_{r['example_id']} ({r['chunk']}) | {r['verdict']} "
            f"| {', '.join(r.get('fail_classes') or []) or '-'} "
            f"| {', '.join(failed_checks(r)) or '-'} "
            f"| {rec.get('idiom', '—')} | {rec.get('en_text', '—')} |")
    sheet = montage(entries, Path(out_dir) / "spot_review.jpg", cols=4)
    md = Path(out_dir) / "spot_review.md"
    md.write_text("\n".join(lines) + "\n")
    return sheet, md, picked


def build_daily(rows, latest, out_dir, human_review_dir):
    today = datetime.now(timezone.utc).date().isoformat()
    todays = [r for r in rows if r["judged_at"][:10] == today]
    verdicts = Counter(r["verdict"] for r in latest.values())
    classes = Counter(c for r in latest.values()
                      for c in (r.get("fail_classes") or []))
    repaired = sum(1 for r in latest.values()
                   if r["verdict"] == "pass" and r.get("attempt", 0) > 0)
    escalated = sorted(p.name for p in Path(human_review_dir).glob("ex_*.jpg")) \
        if Path(human_review_dir).exists() else []
    lines = [
        f"\n## {today}",
        f"- judged today: {len(todays)} (corpus total {len(latest)})",
        f"- current state: {verdicts.get('pass', 0)} pass / "
        f"{verdicts.get('fail', 0)} fail / "
        f"{verdicts.get('judge_error', 0)} judge_error",
        f"- repaired-to-pass so far: {repaired}",
        f"- escalated to human review: {len(escalated)}"
        + (f" ({', '.join(escalated[:12])}{'…' if len(escalated) > 12 else ''})"
           if escalated else ""),
    ]
    if classes:
        top = ", ".join(f"{c}×{n}" for c, n in classes.most_common())
        lines.append(f"- open failure modes: {top}")
    daily = Path(out_dir) / "DAILY.md"
    if not daily.exists():
        daily.write_text("# Corpus-image QA — daily summaries\n")
    with open(daily, "a") as f:
        f.write("\n".join(lines) + "\n")
    # contact sheet of current failures + escalations
    fails = [r for r in latest.values() if r["verdict"] == "fail"]
    fails.sort(key=lambda r: r["example_id"])
    entries = [(r["image"],
                f"ex_{r['example_id']} " + ",".join(r.get("fail_classes") or []))
               for r in fails]
    sheet = None
    if entries:
        sheet = montage(entries,
                        Path(out_dir) / f"contact_{today}.jpg", cols=5)
    return daily, sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--human-review-dir", default=None)
    ap.add_argument("--spot", type=int, default=0,
                    help="build spot-review package of N verdicts")
    ap.add_argument("--prompts-dir", default=None,
                    help="brief dir; fills idiom/sentence in the spot table")
    args = ap.parse_args()
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    hr = args.human_review_dir or (out_dir / "human_review")
    rows = load_ledger(args.ledger)
    latest = latest_per_example(rows)
    if not rows:
        print("empty ledger")
        return
    if args.spot:
        index = None
        if args.prompts_dir:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            import qa_rubric
            index = qa_rubric.load_brief_index(args.prompts_dir)
        sheet, md, picked = build_spot_review(latest, out_dir, args.spot,
                                              index)
        print(f"spot review: {sheet} + {md} ({len(picked)} verdicts)")
    daily, sheet = build_daily(rows, latest, out_dir, hr)
    print(f"daily: {daily}" + (f"  contact sheet: {sheet}" if sheet else ""))


if __name__ == "__main__":
    main()
