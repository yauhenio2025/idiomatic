# Commission: Romance course-factory extraction (FR / ES / IT / PT)

> Drafted 2026-08-13 by the coordinating session (from the Huawei/Italy laptop,
> orchestrating ryze + the Mac over Tailscale). Extends the German course
> factory to the four Romance languages the app already declares support for
> (`SUPPORTED_LANGS = {"de","es","fr","it","pt"}` in
> `idiomatic/grammar/course.py`; only `DE_UNITS` is populated today).
>
> Execute this with **Codex sub-agents in git worktrees** (the established
> pattern — see `.claude/worktrees/agent-*`). One book = one agent. Audio that
> needs local LLMs runs on ryze; all parsing/packaging is plain codex work and
> can run anywhere.

## Mission

For each of the four languages, reproduce **exactly** the German extraction
that already lives in `docs/research/grammar_books/de_hammer_ref/` (reference
grammar) and `docs/research/grammar_books/de_hammer_work/` (workbook
exercises), so the main app can build Anki decks for the new languages the same
way it does for German. Nothing about the app's deck build changes — this
commission only produces its **inputs** in the proven shape.

## The eight source books (from `docs/research/ROMANCE_BOOK_EQUIVALENTS.md`)

Reference grammar + companion workbook per language. Editions are load-bearing
(section anchors that the extraction keys on do not survive across editions).

| Lang | Reference grammar (ISBN pbk) | Workbook (ISBN pbk) | Extraction risk |
|------|------------------------------|---------------------|-----------------|
| FR | French Grammar and Usage 5e 2025 — 9781032444635 | Practising French Grammar 5e 2025 — 9781032441405 | LOW — born-digital EPUB, 17 ch, 1:1 mirror |
| ES | A New Reference Grammar of Modern Spanish **6e** 2019 — 9781138124011 | Practising Spanish Grammar 4e 2019 — 9781138339279 | LOW — EPUB; **must be 6e** (5e renumbered) |
| IT | A Reference Grammar of Modern Italian 2e 2007 — 9780340913390 | Practising Italian Grammar 2004 — 9780340811443 | **MEDIUM** — pre-digital; expect print-replica PDF, not EPUB → pdftotext/OCR + heavier QA |
| PT | Modern Brazilian Portuguese Grammar 3e 2023 — 9781032244334 | Modern Brazilian Portuguese Grammar Workbook 3e 2023 — 9781032244426 | MEDIUM — **Brazilian** Portuguese (owner confirmed BP acceptable); no Routledge reference-grammar pair exists for PT |

**Acquisition status (READ BEFORE STARTING):** the books are being pulled from
Anna's Archive by an autonomous loop on the Mac
(`~/llms/pimsleur/bookscan/acquire_loop.sh`), which downloads the moment
Anna's search backend recovers (it was in a broad outage on 2026-08-13). Landed
files appear on the Mac at
`~/llms/pimsleur/output/grammar_books_idiomatic/<TAG>__<md5>.<ext>` with a
`manifest.json`. **Do not start a language until its two files are present**;
pull them onto ryze into `docs/research/grammar_books/` (gitignored) first. If
after ~1 day some are still missing, the fallback is the owner's Kindle copies
(text layer, no OCR needed) — flag and ask.

## Gold template — copy this shape exactly

Read these before writing anything; they are the contract:

- `docs/research/grammar_books/de_hammer_ref/REF_MANIFEST.json` +
  `de_hammer_ref/sections/chNN.json` — reference grammar.
- `docs/research/grammar_books/de_hammer_work/chapters/chNN.json` +
  `de_hammer_work/MANIFEST.json`, `hammer_toc.json` — workbook.
- `de_hammer_work/SWEEP_BRIEF.md` + `SWEEP_REPORT.md` — the QA sweep.

### Reference-grammar output (`{lang}_ref/`)
Parse the EPUB XHTML with ElementTree — **no OCR, no paraphrase** (IT PDF is the
exception: pdftotext, and OCR only where the print-replica has no text layer).
Per chapter `sections/chNN.json`; plus `REF_MANIFEST.json` recording: source
filename+sha256+format, TOC agreement (expected vs body numbered sections,
missing/extra/title-mismatch lists — must reconcile to `agreement: true`),
per-chapter section counts, and `block_type_totals`
(example/list/note/paragraph/table). The German ref parsed to 146 numbered
sections across 24 chapters with full TOC agreement — hit the same bar for each
book against its own TOC.

### Workbook output (`{lang}_work/chapters/chNN.json`)
One dict per chapter:
```json
{
  "chapter": 2,
  "title": "...",
  "hammer_sections": ["2.1","2.6", ...],   // cross-refs into {lang}_ref
  "exercises": [
    {
      "ex_no": 1,
      "instruction": "full exercise instruction incl. the worked e.g.",
      "page": 30,
      "items": [
        {
          "item_no": "1",
          "prompt": "cue as printed (keep / slot separators verbatim)",
          "answer_key_raw": "the answer key's solved string, verbatim",
          "full_solution_html": "<mark>one solved sentence with sensible mark spans</mark>",
          "alternatives": [],
          "flags": ["resolution-repaired","book-corrected", ...],
          "key_page": 204
        }
      ]
    }
  ]
}
```
`full_solution_html` must be ONE solved sentence with `<mark>` spans, never the
fragment scaffold with text jammed into slots (this was a proven German defect).

### QA sweep (mandatory, per workbook — see SWEEP_BRIEF.md)
- **A. Language contamination**: flag foreign words leaking into
  `answer_key_raw`/`full_solution_html` (beware genuine homographs). Prompt is
  ground truth on conflict; auto-repair → flag `book-corrected`, record
  original→fixed; ambiguous → flag `contamination-review`, leave unchanged.
- **B. Solution shape**: for fragment-construction items (prompts with `/`
  separators), rebuild `full_solution_html` as one solved sentence from the
  repaired key; flag `resolution-repaired`; ambiguous mark placement → mark the
  whole sentence + flag.
Re-run mark/delimiter/key-presence validation on everything touched. Emit
`{lang}_work/SWEEP_REPORT.md` listing every change + review flags + totals, then
`tar czf docs/research/grammar_books/{lang}_work_v1.tar.gz` and print its SHA-256.

## Wire into the course (`idiomatic/grammar/course.py`)
Add `FR_UNITS / ES_UNITS / IT_UNITS / PT_UNITS` mirroring `DE_UNITS`
(`dict[str, tuple[int, str]]`, unit_key → (order, label)) using the registries
sketched in `ROMANCE_BOOK_EQUIVALENTS.md` (17 FR / 24 ES / 21 IT / 24 PT). Keep
the same accessor/error pattern as DE. Add a test per language mirroring
`tests/test_course_select.py`. The `hot-topic` mappings in the report
(subjunctive, passé composé/imparfait, ser/estar, etc.) are the acceptance
checks that a unit actually lands on the right reference sections.

## Sub-agent fan-out
- One worktree-isolated Codex agent per **book** (8 total). Ref and workbook for
  a language can run in parallel; the workbook's `hammer_sections` cross-refs are
  validated against the ref after both land.
- Sequence languages by risk: FR and ES first (clean EPUBs, prove the pipeline),
  then PT, then IT (print-replica — budget extra QA).
- **Verification gate before a book is "done"**: TOC agreement true; workbook
  items parse with prompt+key present and valid mark spans; SWEEP_REPORT emitted;
  tarball SHA recorded. A book that fails any gate stays open with the reason
  logged — never silently accept a partial/wrong-edition extraction.

## Determinism ledger
- **LLM owns judgment**: what is contamination vs. a homograph; where the solved
  sentence's mark spans go; whether a found file is the right edition; how a
  book's chapters map to pedagogical units.
- **Code owns plumbing only**: XHTML/PDF → structured blocks (shape), TOC
  reconciliation arithmetic, mark/delimiter/key-presence validation (shape),
  JSON persistence, tar+SHA. No code branches on the *meaning* of an exercise.

## Guardrails
- Source books stay under `docs/research/grammar_books/` (gitignored — repo is
  public). Never commit book bytes.
- Editions are exact (FR 5e/5e, ES 6e/4e, IT 2e/2004, PT 3e/3e). A wrong-edition
  file fails the gate.
- Don't touch the video→text or minting pipelines.
- Fail closed: a book leaves "pending" only on a passing verification gate.
