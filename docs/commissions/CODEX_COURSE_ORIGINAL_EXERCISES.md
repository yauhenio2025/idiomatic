# Codex: original exercises for provenance-starved course units

You are authoring ORIGINAL German exercises for a course unit whose
workbook sets are provenance-flagged (the 2026-08-12 completeness audit:
partikeln 0 kept items, wortbildung 6, rechtschreibung 3, zahlen 15).
These are NOT book selections — you compose every sentence yourself.
The unit is named when this brief is invoked.

## Hard rules

1. NEVER open `docs/research/grammar_books/de_hammer_work/` (the sealed
   workbook corpus). Your items must be original; reading the flagged
   book sets risks reproducing them.
2. You MAY read `docs/research/grammar_books/de_hammer_ref/sections/`
   for the relevant chapter — for FACTUAL grounding only (which forms,
   which contrasts, which usage conditions). Never copy or lightly
   paraphrase an example sentence from it.
3. Ground the drills in the LESSON:
   `idiomatic/grammar/data/course/lessons/de_<unit>.md`. Each exercise
   block anchors to the lesson card it follows (`blocks[].block` = the
   card's 1-based position in the lesson SCRIPT) and drills EXACTLY
   what that card taught — no forward references to untaught material.
4. Output file (machine-local, gitignored):
   `idiomatic/grammar/data/course/book_local/de_<unit>.exercises.json`
   in the EXACT schema of the existing files (see
   `de_zahlen.exercises.json` for shape; `parse_exercises_file` in
   `idiomatic/grammar/course.py` is the validator — run it):
   - `source`: `{"workbook": "none — original exercises (this unit's
     workbook sets are provenance-flagged)", "reference": "Hammer's
     German Grammar and Usage, 7th ed. (Durrell), Ch. <n>",
     "corpus": "original-llm-2026-08"}`
   - item `id`: `orig-c<chapter>-e<set>-i<item>` (e.g. `orig-c09-e01-i1`).
   - `provenance`: `"llm-generated"` on EVERY item (the card template
     displays this — it is the owner-required visible marking).
   - `source_ref`: `"Originalübung (LLM), nach Hammer §<ref>"`.
   - `hammer_refs`: real §-ids from the chapter that the item practises.
   - `solution_html`: the full solution with the exercised material in
     one or more `<mark>` spans; prompt uses `___` blanks or a
     transformation instruction, exactly like the book items do.
   - `alternatives`: list every genuinely correct alternative answer
     (particles especially: if both `doch` and `ja` fit naturally with
     different nuance, the drilled one must be forced by unambiguous
     context — rewrite the context until only one particle is natural;
     if that is impossible, list the alternative).
5. Quality bar (C1): natural, contemporary German a native editor would
   not touch. Particles/word-formation/spelling drills live in natural
   conversational or written contexts, never metalinguistic frames.
   Vary registers and situations; no boilerplate openers repeated
   across items; no translationese.
6. Instructions (`instruction` field): German task lines in the house
   style of existing units — concise, self-contained, one per exercise
   set (they render on the card front).
7. Size: 5-8 blocks, 5-8 items per block, 30-48 items total, anchored
   across the whole lesson (early cards get drills too, not just the
   finale).
8. Self-check before finishing (mandatory, in this order):
   a. `.venv/bin/python -c "from idiomatic.grammar import course;
      print(len(course.parse_exercises_file('<path>')))"` — must pass.
   b. Re-read every solution sentence aloud-in-your-head as a hostile
      native editor; fix anything stiff.
   c. Verify every `hammer_refs` id exists in the chapter's section
      inventory.
9. Write a summary of what you authored (blocks × items, particle/topic
   coverage map, alternatives policy decisions) to
   `docs/research/grammar_books/course_audit/ORIGINALS_<unit>_NOTES.md`
   and print it.
10. Do NOT commit. Do NOT touch any other unit's files. A separate
    hostile audit reviews your output before it ships.
