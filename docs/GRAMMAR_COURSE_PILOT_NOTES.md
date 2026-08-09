# Grammar Course pilot — DE Kasus (owner review notes)

> Built 2026-08-09 (night session). Deck: **ZZ Grammar Course Pilot
> (disposable)** — import it, judge it, delete it; nothing touches the
> estate tree. APKG at `idiomatic/grammar/data/course/book_local/
> ZZ_pilot_de_kasus.apkg` (machine-local; book-derived content is never
> committed). Rebuild any time:
> `.venv/bin/python tools/course_build_pilot.py de kasus`.

## Why German cases (Kasus)

The corpus is deepest exactly here: workbook ch. 2 "Case" has 21
exercises / 177 items with the best clean-item yield of the fully
usable chapters, and Hammer ch. 2 gives 8 well-structured sections
(2.1–2.7) to ground every slide. It is also the topic where diagrams
pay most: role-mapping, the give-triangle, genitive-vs-von decision
tree, apposition case-mirror.

## What you will see

**`::1 Lesson` — 10 two-sided cards** (~20 slides), audio-first scripts
in our own words, every side citing its Hammer §§ in a Sources footer,
9 authored house-style SVG diagrams:

| # | Front | Back | Hammer |
|---|-------|------|--------|
| 1 | Four cases, one job (role-map SVG) | Order can move, roles cannot | 2, Ch. 19 |
| 2 | Nominative: the subject | sein/werden/bleiben take two nominatives (equals-sign SVG) | 2.1, 16.6 |
| 3 | Accusative: the direct object (arrow SVG) | kosten, lehren — and inner objects | 2.2.1, 16.3.3 |
| 4 | Accusative time — no preposition | Distance, measure — and Guten Morgen | 2.2.2–2.2.3 |
| 5 | Dative: the receiver (give-triangle SVG) | Verbs and adjectives that insist | 2.5.1, 2.5.4a |
| 6 | The free dative (affected-person SVG) | Dative of possession | 2.5.2, 2.5.3 |
| 7 | Genitive: linking noun phrases (chain SVG) | Where the genitive sits | 2.3 |
| 8 | Speech says von, writing says genitive | When von is required (decision-tree SVG) | 2.4 |
| 9 | Apposition copies the case (mirror SVG) | als and wie join the club | 2.6 |
| 10 | Measurement: apposition first | Vague amounts and big numbers (three-lane SVG) | 2.7 |

**`::2 Exercises` — 92 atomic cards**, all book-verbatim from
Practising German Grammar ch. 2 (fair-use scale: ~7% of the workbook's
2,802 items, machine-local only). German prompt on the front with the
exercise's own instruction; full solution on the back with the answer
`<mark>`-highlighted, plus `Hammer §… · PGG Kap./Üb./Nr. · provenance`.
Selection per block (Üb. = workbook exercise number):

- after card 2 (nominative): Üb. 1 — 10 items
- after card 3 (acc. object): Üb. 4 — 22 items
- after card 4 (acc. time/measure): Üb. 5 — 10 items
- after card 5 (dative verbs): Üb. 12 — 17 items
- after card 6 (free dative): Üb. 10 — 8 items
- after card 8 (genitive/von): Üb. 9 — 10 items
- after card 9 (apposition): Üb. 14 — 9 items
- after card 10 (measurement): Üb. 17 — 6 items

14 items were dropped by the conservative gate (any extraction flag:
judgment-call, reconstructed-by-model). Identification/project-style
exercises (Üb. 2, 13, 19–21) and the broken Üb. 16 reconstruction were
excluded; EN→DE translation exercises (Üb. 15, 18) were excluded to
keep the population monolingual. Cards 1 and 7 intentionally carry no
exercise block (card 7's genitive forms are drilled by the
genitive-vs-von block).

**Sequencing**: new-card due positions 1–102 encode lesson card → its
exercises → next card. To see this order when studying the parent deck,
set the deck preset's new-card gather order to **Ascending position**
(one-time setting; the future DJ filtered decks order by due anyway).

## Known limitations (deliberate, not oversights)

1. **Audio** (owner verdict 2026-08-09: wanted now — implemented): the
   local-TTS lane voices lesson narration per segment (EN clone for
   explanation, DE clone for examples; 121 clips for this unit) and
   every exercise's full solution sentence (92 clips) — 213 clips
   total. Flow: seed via `tools/course_seed_audio.py de kasus`
   (idempotent), voice during the night window, rebuild via
   `tools/course_build_pilot.py de kasus --audio`. Partial voicing
   builds fine; unvoiced cards keep the
   `idiomatic-course-audio-pending` tag and lose it on the next rebuild
   (stable GUIDs — reimporting updates cards in place, scheduling
   survives).
2. Üb. 1 and Üb. 10 solutions display as one whole-sentence highlight
   (the printed key verbatim) because those are
   construct-the-whole-sentence exercises — the extraction's per-word
   highlighting was unusable for Üb. 1.
3. A few solutions keep the book's own inline commentary, e.g.
   "(deutschen Weines sounds old-fashioned)" — that is the printed
   answer key speaking, kept verbatim by policy.

## Decisions needed (multiple choice; comment boxes welcome)

1. ~~**Pilot verdict**~~ — ANSWERED 2026-08-09: format approved; audio
   non-negotiable and wanted now (lesson narration + voiced exercise
   backs). Audio lane implemented the same night; see Known
   limitations #1 for the flow.
2. **Exercise volume per unit**: keep all clean items (92 here), or cap
   per block (~10) and bank the rest for the telemetry lane's
   remediation top-ups?
3. **Whole-sentence-highlight backs** (Üb. 1/10 style): fine as-is, or
   exclude construct-type exercises in favor of cloze-type only?
4. **Sequencing setting**: OK to have the add-on set the unit deck
   preset to gather-by-ascending-position automatically, or leave it
   manual until the DJ lane takes over ordering?
5. **Card 7 empty block**: acceptable pattern, or should every lesson
   card be followed by at least a few exercises (would require relaxing
   the flags-only gate for the genitive exercises)?
6. **Estate placement on approval**: `DE German::2 Grammar::Kasus
   (cases)::{1 Lesson,2 Exercises}` — confirm the unit_label wording.
