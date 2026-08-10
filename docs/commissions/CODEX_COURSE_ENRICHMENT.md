# Codex: Grammar Course enrichment sidecar (one unit per invocation)

You are authoring the CONTRACT-2 enrichment sidecar for one Grammar
Course unit. The invocation names UNIT (and its language, always `de`
for now). Inputs:

- `idiomatic/grammar/data/course/book_local/de_<unit>.exercises.json`
  — the unit's selected exercises (blocks[].exercises[]: id,
  instruction = the block rubric often containing a worked example,
  prompt, solution_html with `<mark>` spans, alternatives,
  hammer_refs, source_ref).
- `idiomatic/grammar/data/course/lessons/de_<unit>.md` — the unit's
  lesson (for tone and topical grounding).
- Reference grounding for why-lines:
  `docs/research/grammar_books/de_hammer_ref/sections/ch<NN>.json`.
- The shipped example of a complete sidecar:
  `idiomatic/grammar/data/course/book_local/de_kasus.enrichment.json`.

Write ONE file: `…/book_local/de_<unit>.enrichment.json`. Modify
nothing else.

## Schema (contract 2)

```json
{"lang": "de", "unit": "<unit>", "contract": 2,
 "blocks": [{"block": <int>, "task_html": "...",
             "example_html": "..." | null}],
 "exercises": [{"id": "...", "solution_en": "...", "why_en": "...",
                "solution_full_html": "..." | null}]}
```

Every block number exactly once; every exercise id exactly once
(exactly the ids present in the exercises file).

## Content rules

1. `task_html` — per block, a CONCISE rewrite of the block's rubric:
   1–2 short English imperative sentences (aim under ~180 visible
   chars) stating what the learner must produce. Drop book-artifact
   phrasing ('from the following list', 'check in a dictionary', the
   inline e.g.). Wrap EVERY German word/phrase in `<i>…</i>`. Tags
   allowed: i, b, br.
2. `example_html` — the rubric's worked example reformatted: cue, then
   →, then the sentence(s); German in `<i>`; null when the rubric has
   no example. Tags: i, br.
3. `solution_en` — natural English rendering of what the DISPLAYED
   solution means (the full sentence when solution_full_html is a
   string, else the original solution). Plain text, no HTML.
4. `why_en` — ONE short English sentence (~under 140 visible chars)
   naming the rule at work and its trigger, grounded in the exercise's
   hammer_refs sections (cite like (§19.3)); never state a rule you
   cannot ground in the reference corpus. Tags: i only.
5. `solution_full_html` — null when the original solution_html already
   IS the complete requested production; otherwise the complete
   sentence(s) the rubric actually asks for, realized exactly in the
   pattern of the rubric's worked example, with ONLY the
   inserted/converted material wrapped in `<mark>`. Tags: mark, i, br.
   Sentences end with terminal punctuation.

## HARD INVARIANTS (mechanical validators reject violations)

- No invented German: every `<i>` span in task_html/example_html/
  why_en must be a verbatim (whitespace-normalized) copy of text
  present in that block's instructions/prompts/solutions/alternatives.
- solution_full_html: every `<mark>` span must equal one of the
  original solution_html's `<mark>` spans; every original mark span
  must appear inside the full text; German outside the marks must be
  verbatim-copyable from the exercise's prompt, its block's
  instruction, or the original solution. If an exercise cannot be
  realized under this rule, set null and list it in your summary with
  one line of why.

## Mandatory self-check before finishing

```
.venv/bin/python -c "
from idiomatic.grammar import course
ex = course.parse_exercises_file(course.BOOK_LOCAL_DIR / 'de_<unit>.exercises.json')
enr = course.parse_enrichment_file(course.BOOK_LOCAL_DIR / 'de_<unit>.enrichment.json')
course.validate_enrichment(ex, enr)
print('VALID')"
```

Iterate until it prints VALID. Then self-review: every task_html
against its rubric (task preserved?), every solution_en against the
displayed solution (meaning exact?), every why_en against its cited §
(rule true? the drilled rule?), every full sentence against the rubric
pattern (word order? punctuation? agreement?).

Do NOT commit. Print: blocks count, exercises count, full-vs-null
counts, null ids with reasons, and 5 sample entries.
