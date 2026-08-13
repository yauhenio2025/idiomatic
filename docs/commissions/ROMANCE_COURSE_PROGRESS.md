# Romance course-factory expansion — coordination log

> Cross-machine operation to extend the German course factory to FR/ES/IT/PT.
> Started 2026-08-13 by the coordinating session (Huawei/Italy laptop over
> Tailscale). Commission: `ROMANCE_COURSE_EXTRACTION_COMMISSION.md` (same dir).

## Machine roles
- **Mac** (`rps-002s-mac-studio`, `~/llms/pimsleur/bookscan`): owns the Anna's
  Archive keys + download machinery + quota. Acquires the 8 books.
- **ryze** (`fevm-fa65g` = admin@fedora): idiomatic repo lives here; runs the
  Codex extraction sub-agents and the local-LLM audio.
- **Coordinator** (Italy laptop): set this up; Anna's is ISP-blocked in Italy so
  all shadow-library work happens in Shanghai.

## Phase 1 — Acquire the 8 books  [IN PROGRESS — externally blocked]
- Source/editions: see commission table. Confirmed against Routledge/library
  catalogues (ES 6e e-book ISBN 9781317301028; FR born-digital 2025; etc.).
- **Blocker (2026-08-13 ~15:50 CST):** broad shadow-library search outage.
  Anna's `.gd` search = HTTP 500 (its *download API still works*); `.org`/`.se`
  = unreachable/504; `.li`/`.gs` = parked ad domains; all Libgen forks = 503/504
  or DNS-blocked from China. No md5-discovery surface reachable from anywhere
  right now (confirmed China + Italy + Exa vantage).
- **Automated recovery:** `bookscan/acquire_loop.sh` (launched, `caffeinate`d,
  pid noted in loop log) retries every 15 min for ~16 h. The moment Anna's search
  returns, it resolves all 8 md5s via the bookscan lookup machinery and downloads
  them via the working `.gd` API. Best-candidate auto-pick + `validate()`; all
  candidates recorded so editions can be re-checked.
  - **Check status:** `tail ~/llms/pimsleur/output/grammar_books_idiomatic/acquire_loop.log`
    and `manifest.json` in the same dir. Success = 8 files `<TAG>__<md5>.<ext>`.
  - **Fallback if outage persists >~1 day:** owner's Kindle copies (text layer,
    no OCR) — convert via Calibre; skips shadow libraries entirely.
- Codex account on ryze + Mac = `evgeny.morozov@gmail.com` (ChatGPT Pro),
  ~91% quota remaining (owner confirmed — no account switch).

## Phase 2 — Extract to de_hammer shape  [READY, not started]
Per commission. One worktree Codex agent per book. FR+ES first, then PT, then IT
(print-replica). Blocked on Phase 1 delivering each language's two files.

## Phase 3 — Wire into course.py + build decks  [PENDING]
Add FR/ES/IT/PT `_UNITS` to `idiomatic/grammar/course.py`; app builds decks;
audio via local LLMs on ryze.

## Next action for whoever picks this up
1. `tail` the acquire loop log on the Mac; when files land, pull them to
   `~/projects/idiomatic/docs/research/grammar_books/` on ryze.
2. Execute `ROMANCE_COURSE_EXTRACTION_COMMISSION.md` with Codex sub-agents.
