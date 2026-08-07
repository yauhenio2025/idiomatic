# Corpus-image QA loop (Q-Judger) — operations

> Every corpus illustration is machine-judged against its own brief;
> failures are auto-repaired by class or escalated to a human-review
> folder. Built per
> [IMAGE_QA_LOOP_COMMISSION](commissions/IMAGE_QA_LOOP_COMMISSION.md).
> Judge verdicts are ADVISORY to the user's gate — a human verdict
> recorded anywhere always wins.

## Topology

- **Judge host: the Mac Studio** (96 GB unified). Model:
  `~/llms/models/qwen-image-bench/` — Q-Judger, 27B VL on Qwen3.6,
  BF16 ≈ 54 GB, runs via transformers+MPS in
  `~/llms/factory-node/qa/venv` (py3.12, torch 2.13, transformers 5.8.1).
- **QA home (Mac, machine-local):** `~/llms/factory-node/qa/` —
  `verdicts.jsonl` (ledger), `fedora_repair_queue.jsonl`,
  `human_overrides.jsonl`, `human_review/`, `DAILY.md`,
  `contact_<date>.jpg`, `spot_review.{jpg,md}`, `repair_log.jsonl`,
  `judge_batch.sh`, `repair_loop.py`, `briefs/` + `repo/tools/`
  (synced copies; the repo is the source of truth).
- **Fedora mirror:** `/srv/ai-models/outputs/factory/qa_mirror/` —
  pulled copies of the ledger, queue, reports, `human_review/`, the
  Mac corpus (`mac_corpus/`), and the `ARMED` flag.

## Machine-neutral code (this repo)

- [tools/qa_rubric.py](../tools/qa_rubric.py) — brief → checklist
  prompt (official Q-Judger scaffold, custom checklist), verdict
  classification, repair-action mapping, chunk-partition helpers.
- [tools/qa_judge.py](../tools/qa_judge.py) — batch runner: sweeps
  image dirs, judges images whose content hash has no verdict yet,
  appends ledger rows. Loads → judges pending → exits (frees ~54 GB).
  Memory guard defers (rc=3) when the box is busy.
- [tools/qa_report.py](../tools/qa_report.py) — ledger → DAILY.md
  append, failure contact sheet, spot-review package (`--spot N`).
- [idiomatic/grammar/data/illustration_prompts/PARTITION.json](../idiomatic/grammar/data/illustration_prompts/PARTITION.json)
  — chunk → render machine. Unlisted chunks belong to Fedora. **When
  assigning new chunks to the Mac, update this file AND the Mac's
  `run_queue.sh` together.** The Fedora night miner skips mac-owned
  chunks (that skip is what stops the two renderers duplicating work).

## The rubric (v1)

Hard checks (any 0 ⇒ fail): person count (medallion chips excluded),
gender presence, distinct-individuals / identity-coherence (catches
merges — the bearded-woman class), per-person action match, absurd
element visible, anatomical fidelity (limb/hand/head counts). Soft
pair (both 0 ⇒ fail "bland"): focal point, memorability.

Fail class → repair (max 2 repairs, then escalate to `human_review/`):

| class | action | mechanics |
|---|---|---|
| absurd, bland | `reroll_full` | new t2i seed (+10007·n) + new edit seed |
| identity, action | `reroll_inserts` | same setting seed, new edit seed (+101·n) |
| anatomy | `targeted_edit` | ONE Edit-2511 fix (judge-authored one-line instruction, no keep-everything hedging) on the pre-medallion intermediate, else falls back to reroll_inserts |

Repairs render to a temp file and atomically replace the corpus jpg —
there is never a deleted-jpg window for the miners to race. Escalation
COPIES (never moves) the jpg to `human_review/` — a missing file would
just get re-minted. The judge re-judges any image whose content hash
changes (that is how repaired images get their re-verdict).

## Orchestration

- **Mac judging:** launchd agent `com.idiomatic.qa-judge` (every
  15 min) and `run_queue_v2.sh` (after every render chunk) →
  `qa/judge_batch.sh` (mkdir-lock, judge, report, repair loop). BF16
  judge + active minting do NOT fit in 96 GB together (ComfyUI holds
  ~50 GB of Metal buffers mid-chunk); the memory guard (default 58 GB
  available) defers judge batches to the gaps between render chunks —
  measured 2026-08-07, per the commission's serialize-if-needed clause.
- **Bookscan coordination contract (2026-08-07):** when judge_batch has
  pending work and no mint render is active, it touches
  `~/llms/factory-node/PAUSE_BOOKSCAN` — bookscan holds new book spawns
  and in-flight books drain within ~15 min, freeing the judge's memory
  — waits up to 25 min for ≥58 GB, judges, then removes the flag
  (trap-guaranteed, even on crash). NEVER SIGSTOP bookscan's driver —
  a stopped driver wedges its children (5 h lost 2026-08-07). While a
  mint render is active the pause is skipped (no window is possible);
  the chunk boundary is the deterministic window.
- **Transport (Fedora-initiated, key auth exists this direction):**
  systemd user timer `qa-sync.timer` every 30 min →
  `~/llms/qwen-image/factory/qa_sync.sh`: push Fedora corpus images +
  repo tools/briefs to the Mac; pull verdicts, repair queue, reports,
  human_review, mac corpus mirror, ARMED flag.
- **Fedora repairs run in the night window only:**
  `night_miner.sh` calls `factory/qa_repair_night.py` at the top of
  each cycle (before chunk mining), which executes the Mac-authored
  queue for fedora-owned images. Double-gated: mirrored ARMED flag +
  window check (01:30–09:00 until 2026-08-10, then anytime).
- **Mac repairs** run right after each judge batch (`repair_loop.py`),
  ComfyUI-queued so they serialize with any Mac minting job.

## Arming (the human gate)

The repair loop ships DISARMED. Flag = `qa/ARMED` on the Mac (single
source of truth; `qa_sync.sh` mirrors it to Fedora).

1. Judge the existing corpus (happens automatically once memory frees).
2. `tools/qa_report.py --spot 15` → `spot_review.jpg` + `.md` (synced
   to the Fedora mirror). User agrees/disagrees per verdict.
3. Disagreements → `qa/human_overrides.jsonl` lines
   `{"example_id": N, "verdict": "pass"|"fail"}` (never re-judged,
   never repaired).
4. User signs off → `~/llms/qwen-image/factory/qa_arm.sh on`
   (off/status also available). Then one full night cycle with the
   morning DAILY.md is the final acceptance step.

## Consumption rule

When estate/hub builds ingest corpus images, ONLY images whose latest
ledger verdict (or human override) is `pass` may ship to cards.
