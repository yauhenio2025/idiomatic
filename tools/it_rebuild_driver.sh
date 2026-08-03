#!/usr/bin/env bash
# Drives the per-chunk codex runs for the Italian corpus rebuild.
# Resumable: chunks with a valid existing output are skipped.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
IN="$REPO/idiomatic/grammar/data/exercises2/it_rebuild/input"
OUT="$REPO/idiomatic/grammar/data/exercises2/it_rebuild/output"
LOG="$REPO/idiomatic/grammar/data/exercises2/it_rebuild/logs"
mkdir -p "$LOG"

run_chunk() {
  chunk="$1"
  name="$(basename "$chunk")"
  out="$OUT/$name"
  if [ -f "$out" ] && python3 -c "
import json,sys
i=json.load(open('$chunk')); o=json.load(open('$out'))
assert [x['id'] for x in i]==[y['id'] for y in o]
assert all(y.get('it','').strip() for y in o)" 2>/dev/null; then
    echo "[skip] $name already done"
    return 0
  fi
  echo "[run ] $name $(date +%H:%M:%S)"
  codex exec -s workspace-write --skip-git-repo-check -C "$REPO" \
    "Read docs/commissions/EXERCISES2_IT_REBUILD_COMMISSION.md and execute it for the chunk file idiomatic/grammar/data/exercises2/it_rebuild/input/$name. Follow every rule, including the mandatory verification pass and hard rules." \
    >"$LOG/${name%.json}.log" 2>&1
  if [ -f "$out" ]; then echo "[done] $name $(date +%H:%M:%S)"; else echo "[FAIL] $name"; fi
}
export -f run_chunk
export REPO IN OUT LOG

ls "$IN"/*.json | xargs -P 3 -n 1 -I{} bash -c 'run_chunk "$@"' _ {}
echo "ALL CHUNKS PROCESSED $(date)"
ls "$OUT" | wc -l
