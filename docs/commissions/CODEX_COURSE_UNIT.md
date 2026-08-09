# Codex: Grammar Course unit authoring (one unit per invocation)

You are authoring one complete Grammar Course lesson unit for the
idiomatic repo. The owner approved the Kasus pilot (de/ch02) as the
template; the course is batch-produced from the sealed German corpora,
one unit per codex session. Your deliverables are the unit's LESSON
(script + SVGs) and its exercise BLOCK PLAN — not the exercises
themselves (a generic selector consumes your plan later).

The invocation names: UNIT key, CHAPTER number, UNIT_LABEL.

## Absorb first, in this order

1. `idiomatic/grammar/data/course/lessons/de_kasus.md` — THE format
   template: front-matter, `[CARD]`/`[SIDE]` blocks, `TITLE:`, `SVG:`,
   `REF:`, narration prose (spoken English), `TL:` lines (German
   examples — spoken AND displayed), `EN:` gloss lines (display-only
   English under each TL — REQUIRED for every TL), `[PAUSE:ms]`,
   `SHOW:` summary lines. Match its voice: direct, spoken-register
   English narration that teaches into the ear, short punchy SHOW
   lines, "Flip the card." transitions.
2. `idiomatic/grammar/course.py` — `parse_course_lesson` (the line
   grammar + validation you must satisfy), `LESSON_CSS` `s-*` SVG
   palette classes, `load_side_svg` (no event handlers, viewBox
   required).
3. `docs/GRAMMAR_COURSE_DESIGN.md` §1–4 — unit anatomy, interleave,
   REF discipline.
4. The SEALED BOOK CORPORA (gitignored, machine-local):
   - Reference prose:
     `docs/research/grammar_books/de_hammer_ref/sections/ch<NN>.json`
     (Hammer 7th ed. — your grounding; `REF:` cites these section
     numbers)
   - Workbook exercises:
     `docs/research/grammar_books/de_hammer_work/chapters/ch<NN>.json`
     (the exercise sets your plan selects from — study each set's
     instruction/content to place it in the right block)

## Deliverable 1: `idiomatic/grammar/data/course/lessons/de_<unit>.md`

8–12 lesson cards covering the chapter's pedagogical arc for a C1+
learner (the owner: advanced, reads six languages, wants the SYSTEM of
the language — teach mechanisms and contrasts, not phrase lists).
Derive the card sequence from the Hammer sections and the workbook's
actual coverage. Per-side `REF:` cites the Hammer §§ you actually drew
on.

HARD RULES:
- Never copy Hammer or workbook sentences verbatim into the lesson —
  write ORIGINAL German examples illustrating each point. You are
  writing German that will be voiced by TTS and studied daily: it must
  be flawless, natural, C1-register. Re-read every sentence as a
  hostile native editor before finishing (gender, case, word order,
  idiomaticity).
- Every `TL:` line carries an `EN:` gloss (display-only English,
  faithful, natural).
- Narration is ENGLISH prose spoken aloud — no markdown furniture,
  nothing visual-dependent; German only inside `TL:` lines.
- `SHOW:` lines are compact display summaries.

## Deliverable 2: SVG diagrams — `…/lessons/svg/de_<unit>_cNN[f|b].svg`

4–8 diagrams where a picture genuinely teaches a mechanism. House
rules: only `s-*` palette classes from LESSON_CSS (s-ink, s-muted,
s-teal, s-coral, s-sun, s-dead, s-tile, s-stroke-teal, s-stroke-coral,
s-stroke-line), no inline fills/colors, no event handlers, sane
viewBox for 640px rendering. GEOMETRY DISCIPLINE (the owner rejected a
diagram for this): arrows/lines never cross text; arrowheads stop
8–10px short of box edges, never touch or enter boxes; labels keep
clear vertical separation from lines. Measure your coordinates —
compute, don't eyeball.

## Deliverable 3: `idiomatic/grammar/data/course/plans/de_<unit>.plan.json`

```json
{"lang": "de", "unit": "<unit>", "chapter": <NN>,
 "unit_label": "<UNIT_LABEL>",
 "blocks": [
   {"block": 1, "card_seq": 2,
    "exercise_sets": ["<set id from ch<NN>.json>", "<set id>:key"],
    "hammer_refs": ["<§ from the chapter's printed (GGU …) headers>"],
    "max_items": 14, "note": "<short rationale>"}
 ]}
```

Every workbook set you judge drill-worthy lands in exactly one block,
attached to the lesson card that teaches its topic (`card_seq`);
`block` ints unique ascending (plan ordering); `card_seq` unique too —
it becomes the interleave block number; `max_items` 10–16 per block;
total unit target 60–100 atomic items where the chapter supports it
(small chapters may yield less — never pad). Use set ids EXACTLY as
they appear in the chapter file; append `:key` to a set id when the
set's drills must be read from the printed answer key
(construct-the-sentence sets whose solutions live only in the key).
`hammer_refs` is REQUIRED per block: the Hammer §§ this block drills,
and every ref MUST appear in the chapter's printed `(GGU …)` exercise
headers — `tools/course_select.py` verifies this mechanically and
fails the plan otherwise. Sets you exclude: list them with one-line
reasons in your final summary, not in the plan.

After writing the plan, RUN the selector as a self-check:
`.venv/bin/python tools/course_select.py idiomatic/grammar/data/course/plans/de_<unit>.plan.json`
— it must exit 0 and write `book_local/de_<unit>.exercises.json`. Fix
your plan until it does.

## Self-checks before finishing (all mandatory)

- `.venv/bin/python -c "from idiomatic.grammar import course; l=course.parse_course_lesson(course.LESSON_DIR / 'de_<unit>.md'); print(len(l.cards), 'cards')"`
  parses clean.
- Every SVG loads through the course SVG loader.
- Plan JSON parses; every set id exists in the chapter file; every
  `card_seq` exists in your lesson; no set appears twice.
- Full German re-read (hostile native editor) + full gloss fidelity
  re-read.

Do NOT commit — the coordinator reviews and commits. Print a summary:
card list (seq + title), SVG list with one-line descriptions, the plan
(blocks → sets → item counts), excluded sets with reasons, and EVERY
TL German sentence you authored with its gloss (the coordinator
reviews your German).
