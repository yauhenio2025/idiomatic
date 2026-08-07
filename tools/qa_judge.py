#!/usr/bin/env python3
"""Q-Judger batch runner for corpus-image QA.

Loads the judge model once, sweeps image dirs for ex_<example_id>.jpg
files that lack a verdict for their current content hash, judges each
against its brief's checklist, and appends JSONL rows to the ledger.
Designed to load -> judge pending -> exit (frees ~54 GB between runs).

Typical Mac invocation (see docs/IMAGE_QA.md):
  qa_judge.py --model ~/llms/models/qwen-image-bench \\
    --prompts-dir <repo>/idiomatic/grammar/data/illustration_prompts \\
    --images mac:~/llms/factory-node/corpus_images \\
    --images fedora:~/llms/factory-node/qa/fedora_images \\
    --ledger ~/llms/factory-node/qa/verdicts.jsonl
"""
import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import qa_rubric  # noqa: E402

FIX_PROMPT = (
    "The anatomy check failed for this image. State, in ONE short "
    "imperative sentence, the single most important anatomical "
    "correction (e.g. 'Remove the extra left arm of the woman.'). "
    "Answer with the sentence only.")


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def load_ledger(path):
    rows = []
    if Path(path).exists():
        for line in open(path):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def load_overrides(path):
    """human_overrides.jsonl: {"example_id": N, "verdict": "pass"|"fail"}"""
    out = {}
    if path and Path(path).exists():
        for line in open(path):
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                    out[int(r["example_id"])] = r["verdict"]
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass
    return out


def scan_pending(image_dirs, index, ledger_rows, overrides, only=None):
    judged, errors = set(), {}
    for r in ledger_rows:
        key = (r["example_id"], r.get("sha1"))
        if r.get("verdict") == "judge_error":
            errors[key] = errors.get(key, 0) + 1
            if errors[key] >= 2:
                judged.add(key)  # two strikes: stop retrying this content
        else:
            judged.add(key)
    attempts = {}
    for r in ledger_rows:
        if r.get("verdict") == "judge_error":
            continue  # errors are not attempts — don't escalate early
        attempts[r["example_id"]] = attempts.get(r["example_id"], 0) + 1
    pending = []
    for owner, d in image_dirs:
        for p in sorted(Path(d).expanduser().glob("ex_*.jpg")):
            m = re.match(r"ex_(\d+)\.jpg$", p.name)
            if not m:
                continue
            eid = int(m.group(1))
            if only and eid not in only:
                continue
            if eid in overrides:
                continue  # human verdict recorded — never re-judge
            rec = index.get(eid)
            if rec is None:
                continue  # no brief (foreign image) — leave alone
            digest = sha1(p)
            if (eid, digest) in judged:
                continue
            pending.append({"eid": eid, "path": p, "sha1": digest,
                            "owner": owner, "rec": rec,
                            "attempt": attempts.get(eid, 0)})
    return pending


class Judge:
    def __init__(self, model_path, device="mps", max_new_tokens=3072):
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor
        self.torch = torch
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.processor = AutoProcessor.from_pretrained(model_path)
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_path, dtype=torch.bfloat16).to(device)
        self.model.eval()

    def ask(self, image, user_text, max_new_tokens=None):
        """user_text contains one '<image>' placeholder."""
        pre, _, post = user_text.partition("<image>")
        content = [{"type": "text", "text": pre},
                   {"type": "image", "image": image}]
        if post.strip():
            content.append({"type": "text", "text": post})
        messages = [
            {"role": "system",
             "content": [{"type": "text", "text": qa_rubric.SYSTEM_PROMPT}]},
            {"role": "user", "content": content},
        ]
        inputs = self.processor.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt", enable_thinking=True)
        inputs = {k: (v.to(self.device) if hasattr(v, "to") else v)
                  for k, v in inputs.items()}
        n_in = inputs["input_ids"].shape[1]
        with self.torch.no_grad():
            out = self.model.generate(
                **inputs, do_sample=False, repetition_penalty=1.05,
                max_new_tokens=max_new_tokens or self.max_new_tokens)
        return self.processor.decode(out[0][n_in:], skip_special_tokens=True)


def load_image(path):
    from PIL import Image
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    if max(img.size) > 1024:
        img = img.resize((1024, 1024), Image.LANCZOS)
    img.load()
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompts-dir", required=True)
    ap.add_argument("--images", action="append", required=True,
                    help="owner:dir, e.g. mac:~/llms/factory-node/corpus_images")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--overrides", default=None,
                    help="human_overrides.jsonl (judge never re-judges these)")
    ap.add_argument("--partition", default=None,
                    help="PARTITION.json mapping chunk -> machine")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="",
                    help="comma-separated example_ids")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--max-new-tokens", type=int, default=3072)
    ap.add_argument("--min-free-gb", type=float, default=58.0)
    ap.add_argument("--describe-fix", action="store_true",
                    help="ask for a one-line fix instruction on anatomy fails")
    ap.add_argument("--dry-run", action="store_true",
                    help="list pending + print first prompt, no model")
    args = ap.parse_args()

    index = qa_rubric.load_brief_index(args.prompts_dir)
    partition = qa_rubric.load_partition(args.partition) if args.partition else {}
    ledger_rows = load_ledger(args.ledger)
    overrides = load_overrides(args.overrides)
    only = ({int(x) for x in args.only.split(",") if x.strip()}
            if args.only else None)
    image_dirs = [tuple(s.split(":", 1)) for s in args.images]
    pending = scan_pending(image_dirs, index, ledger_rows, overrides, only)
    if args.limit:
        pending = pending[:args.limit]
    print(f"briefs: {len(index)}  ledger rows: {len(ledger_rows)}  "
          f"pending: {len(pending)}", flush=True)
    if not pending:
        return
    if args.dry_run:
        for p in pending[:20]:
            print(f"  ex_{p['eid']} ({p['owner']}, attempt {p['attempt']})")
        print("\n----- sample prompt -----")
        print(qa_rubric.build_user_prompt(pending[0]["rec"]))
        return

    try:
        import psutil
        free_gb = psutil.virtual_memory().available / 2**30
        if free_gb < args.min_free_gb:
            print(f"DEFER: only {free_gb:.0f} GB available "
                  f"(< {args.min_free_gb:.0f}); box is busy.", flush=True)
            sys.exit(3)
    except ImportError:
        pass

    t0 = time.time()
    judge = Judge(args.model, args.device, args.max_new_tokens)
    print(f"model loaded in {time.time()-t0:.0f}s", flush=True)

    ledger = open(args.ledger, "a")
    for i, p in enumerate(pending):
        rec = p["rec"]
        t1 = time.time()
        try:
            img = load_image(p["path"])
            raw = judge.ask(img, qa_rubric.build_user_prompt(rec))
            score_json = qa_rubric.extract_json(raw)
            verdict, fail_classes, repair, checks = qa_rubric.classify(
                score_json, rec)
        except Exception as e:  # noqa: BLE001
            raw, score_json = None, None
            verdict, fail_classes, repair, checks = "judge_error", [], None, {}
            print(f"ERROR ex_{p['eid']}: {repr(e)[:200]}", flush=True)
        row = {
            "example_id": p["eid"],
            "expression_id": rec["expression_id"],
            "lang": rec["lang"],
            "chunk": rec["chunk"],
            "owner_machine": qa_rubric.owner_of(rec["chunk"], partition)
                             if partition else p["owner"],
            "found_in": p["owner"],
            "image": str(p["path"]),
            "sha1": p["sha1"],
            "attempt": p["attempt"],
            "judged_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": round(time.time() - t1, 1),
            "rubric_version": qa_rubric.RUBRIC_VERSION,
            "verdict": verdict,
            "fail_classes": fail_classes,
            "repair_action": repair,
            "checks": checks,
            "scores": score_json,
        }
        if (args.describe_fix and verdict == "fail"
                and "anatomy" in fail_classes):
            try:
                fix = judge.ask(img, "# Image\n<image>\n\n" + FIX_PROMPT,
                                max_new_tokens=512)
                fix = re.sub(r"<think>.*?</think>", "", fix, flags=re.S)
                row["fix_instruction"] = fix.strip().split("\n")[-1][:300]
            except Exception:  # noqa: BLE001
                pass
        ledger.write(json.dumps(row, ensure_ascii=False) + "\n")
        ledger.flush()
        print(f"[{i+1}/{len(pending)}] ex_{p['eid']}: {verdict}"
              f"{' ' + ','.join(fail_classes) if fail_classes else ''}"
              f" ({row['elapsed_s']}s)", flush=True)
    ledger.close()


if __name__ == "__main__":
    main()
