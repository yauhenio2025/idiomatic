#!/usr/bin/env python3
"""Chunk a corpus-export JSONL into illustration-prompt input chunks.
Usage: illu_chunk.py <lang>.jsonl <lang> [expressions_per_chunk=12]
Writes idiomatic/grammar/data/illustration_prompts/input/<lang>_illu_bNN.json (idempotent
overwrite; grouped one object per expression, examples in ord order)."""
import json
import sys
from collections import OrderedDict
from pathlib import Path

OUT = Path("idiomatic/grammar/data/illustration_prompts/input")


def main():
    src, lang = sys.argv[1], sys.argv[2]
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    groups = OrderedDict()
    for line in Path(src).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        g = groups.setdefault(r["expression_id"], {
            "expression_id": r["expression_id"], "lang": r["lang"],
            "idiom": r["idiom"], "explanation_en": r["explanation_en"],
            "examples": []})
        g["examples"].append({"example_id": r["example_id"],
                              "en_text": r["en_text"],
                              "target_text": r["target_text"]})
    OUT.mkdir(parents=True, exist_ok=True)
    exprs = list(groups.values())
    n = 0
    for i in range(0, len(exprs), per):
        n += 1
        p = OUT / f"{lang}_illu_b{n:02d}.json"
        p.write_text(json.dumps(exprs[i:i + per], ensure_ascii=False,
                                indent=1), encoding="utf-8")
    print(f"{lang}: {len(exprs)} expressions, "
          f"{sum(len(g['examples']) for g in exprs)} sentences, {n} chunks")


if __name__ == "__main__":
    main()
