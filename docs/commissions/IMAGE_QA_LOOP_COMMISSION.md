# Image QA loop — build commission (fresh Fable session)

> Goal: every corpus illustration gets machine-judged against its brief,
> and failures get automatically repaired or escalated — running in
> parallel with minting, inside the established quiet-hours etiquette.
> User-reported defect classes driving this: anatomy glitches (extra
> limbs), identity merges ("man with beard + woman" → bearded woman —
> root-caused separately as the two-insert bug, now patched, but the
> judge must still catch stragglers), and blandness.

## Ground truth to absorb first

- CLAUDE.md; docs/commissions/ILLUSTRATION_PROMPTS_COMMISSION.md (the
  briefs: anchor/setting/absurd_element/inserts — the judge's rubric
  inputs); memory of the render fleet:
  - Fedora renderer `~/llms/qwen-image/factory/render_chunk.py`, output
    `/srv/ai-models/outputs/factory/corpus_images/ex_<example_id>.jpg`,
    NIGHT WINDOW ONLY (systemd user timers qwen-miner-*: 01:30–09:00
    until 2026-08-10, 24/7 after — do not violate; fan noise).
  - Mac renderer `~/llms/factory-node/mac_render_chunk.py` (ssh
    evgeny2026@mac.lan), output `~/llms/factory-node/corpus_images/`,
    runs anytime; queue driver `run_queue.sh`.
- The judge model is ALREADY DOWNLOADED on the Mac:
  `~/llms/models/qwen-image-bench/` (Q-Judger, 27B VL on Qwen3.6, BF16
  ~51 GB, Apache-2.0). Scores 5 dimensions against structured
  checklists, JSON out, 0.92 Spearman vs experts. The Mac (96 GB
  unified) is the designated judge host. Nothing of it is set up yet.

## Build

1. **Judge runtime on the Mac.** Options in preference order:
   transformers+MPS bf16 (simplest, ~54 GB, likely 20–60 s/verdict —
   acceptable); MLX conversion if transformers-MPS proves broken.
   Wrap as a small CLI/daemon: input = image path + its brief (idiom,
   sentence, anchor, inserts) rendered into the checklist prompt;
   output = JSON verdict appended to a ledger
   (`~/llms/factory-node/qa/verdicts.jsonl`).
2. **Rubric.** Map briefs → checks: (a) required people count + genders
   present and DISTINCT (catches merges); (b) action matches the
   insert's `action`; (c) anchor's absurd element visible; (d) anatomy
   sanity (limbs/hands); (e) not bland: composition has a focal point
   and the absurd element (score, don't philosophize). Thresholds:
   fail = any hard check (a–d) fails or aesthetics floor missed.
3. **Repair loop.** Fail classification → action:
   - identity/merge/count wrong → re-run that example's inserts from
     the saved anchor setting (both renderers keep prefixes; re-render
     from chunk JSON is idempotent — delete the bad jpg and re-run its
     chunk) with a seed bump;
   - anatomy/structure → ONE targeted Edit-2511 fix ("one change, no
     keep-everything hedging" — the proven rule), then re-judge;
   - bland/absurd-element-missing → re-roll the full example (new
     seed).
   Max 2 repair attempts per image, then move to
   `qa/human_review/<example_id>.jpg` + note in the ledger. Never loop
   forever; never touch images marked human-review.
4. **Orchestration.** A Mac-side QA daemon sweeps BOTH corpora (pull
   Fedora's new images via ssh/rsync from this box — key auth exists in
   reverse? If not, run the sweep from the Fedora side pushing to the
   Mac; pick the simpler direction), judges new arrivals, executes
   repairs on the machine that owns the image, respecting Fedora's
   night window (queue Fedora repairs for the window; Mac repairs
   anytime). Etiquette: judging (GPU-light-ish) may coexist with Mac
   minting, but serialize judge batches vs render batches if MPS
   contention hurts either badly — measure first.
5. **Reporting.** Daily one-page summary (counts: judged/passed/
   repaired/escalated, top failure modes) appended to
   `~/llms/factory-node/qa/DAILY.md` + a human-review contact sheet the
   user can flip through. When the estate/hub build later ingests
   images, ONLY pass-verdict images ship to cards.
6. **Acceptance:** run the judge over the ~100 already-minted images
   from both machines; user spot-reviews the verdicts (agree/disagree
   on ~15) before the repair loop is armed; then one full night cycle
   end-to-end with the morning summary.

## Rules

- Wait-don't-kill on both boxes (never interrupt an active render);
  Fedora GPU untouched outside its window.
- The repo is the shared brain — commit the QA scripts machine-neutral
  parts + docs; verdicts/ledgers stay machine-local.
- Judge verdicts are advisory to the USER's gate, never overrule a
  human verdict recorded anywhere.
