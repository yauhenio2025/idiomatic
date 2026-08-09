# DJ-C2 study-worthiness triage evidence

Deterministic, read-only evidence for a per-subtree disposition console. No disposition was applied; nothing was deleted or suspended by this run.

## Scope and interpretation

- Source: `docs/research/anki_reorg_work/live_cutover_20260807T072826Z/collection.anki2` opened with `mode=ro&immutable=1`; as-of due date `2026-08-09T23:59:59+08:00`.
- Due now uses the 2026-08-09 local date; study recency uses the DJ-C1-compatible 60-day source window `2026-06-09`–`2026-08-07`.
- Lane rows include descendants and immediate-subdeck rows are nested evidence views. The language projection uses the most-specific row for each card, so nested rows are not added together.
- `easy-rate` and `again-rate` are raw revlog rating percentages. Mature-card interval is the current-card median for cards with `ivl > 21` days; `—` means no evidence.
- Proposed suspension is always reversible. `owner-review` is projected unchanged because it is not an applied disposition.

## Projected due backlog by language

The projection uses DJ-C1's per-language/population seconds-per-rep constants. It is a current due-load estimate, not a forecast of future cards entering the queue.

| Language | Due cards before | Due cards after | Minutes before → after | Reduction |
| --- | ---: | ---: | ---: | ---: |
| DE German | 370 | 360 | 46.3 → 45.2 | 2.3% |
| ES Spanish | 287 | 275 | 44.5 → 43.2 | 2.9% |
| FR French | 758 | 751 | 84.9 → 84.0 | 1.0% |
| IT Italian | 1,608 | 649 | 185.0 → 94.6 | 48.9% |
| PT Portuguese | 161 | 152 | 24.3 → 23.3 | 4.0% |
| ZH Mandarin | 3,381 | 447 | 364.8 → 41.3 | 88.7% |

## Proposed disposition key

- `keep-active`: recent study with a useful difficulty mix or a targeted rescue/error path.
- `suspend-reference`: never opted in, clearly stale/easy-heavy, or batch reservoir without a current study path.
- `sample-hardest`: suspend the bulk and keep N=50 studied cards with the strongest lapse/again evidence active.
- `owner-review`: evidence is genuinely mixed or too thin for an automatic choice.

## DE German

Projected due backlog if the proposals are accepted: **46.3 → 45.2 minutes** (370 → 360 due cards).

| Subtree | Cards | Due | New | Provenance | Study depth | Difficulty | Proposed | Due load min before → after |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| DE German::1 Expressions | 4,514 | 359 | 4,001 | pipeline-minted 4,514 (100.0%) | 1,937 reps / 513 cards; 2026-08-06 | A 41.1% / E 51.0% / mature ivl 166d | keep-active | 45.1 → 45.1 |
| Rationale |  |  |  |  |  |  | Recent study (1,578 reps in 60d) has a mixed signal (41.1% again, 51.0% easy); keep active. |  |
| DE German::1 Expressions::1 Fluency | 4,514 | 359 | 4,001 | pipeline-minted 4,514 (100.0%) | 1,937 reps / 513 cards; 2026-08-06 | A 41.1% / E 51.0% / mature ivl 166d | keep-active | 45.1 → 45.1 |
| Rationale |  |  |  |  |  |  | Recent study (1,578 reps in 60d) has a mixed signal (41.1% again, 51.0% easy); keep active. |  |
| DE German::8 Pimsleur | 5,311 | 10 | 5,301 | batch-imported 5,311 (100.0%) | 11 reps / 10 cards; 2026-05-11 | A 9.1% / E 54.5% / mature ivl — | suspend-reference | 1.1 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 11 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| DE German::8 Pimsleur::Level 5 | 1,258 | 6 | 1,252 | batch-imported 1,258 (100.0%) | 7 reps / 6 cards; 2026-04-21 | A 0.0% / E 42.9% / mature ivl — | suspend-reference | 0.6 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 7 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| DE German::8 Pimsleur::Level 1 | 755 | 2 | 753 | batch-imported 755 (100.0%) | 2 reps / 2 cards; 2026-04-20 | A 0.0% / E 100.0% / mature ivl — | suspend-reference | 0.2 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 2 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| DE German::8 Pimsleur::Level 3 | 1,143 | 2 | 1,141 | batch-imported 1,143 (100.0%) | 2 reps / 2 cards; 2026-05-11 | A 50.0% / E 50.0% / mature ivl — | suspend-reference | 0.2 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 2 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| DE German::7 Rescue | 2 | 1 | 0 | pipeline-minted 2 (100.0%) | 5 reps / 2 cards; 2026-08-07 | A 0.0% / E 0.0% / mature ivl — | keep-active | 0.1 → 0.1 |
| Rationale |  |  |  |  |  |  | Recent targeted study (5 reps in 60d) is an explicit rescue/error path; keep it active. |  |
| DE German::2 Grammar | 91 | 0 | 91 | pipeline-minted 91 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 91 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::2 Grammar::0 Hören | 12 | 0 | 12 | pipeline-minted 12 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 12 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::2 Grammar::1 Genus | 18 | 0 | 18 | pipeline-minted 18 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 18 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::2 Grammar::2 Präpositionen | 34 | 0 | 34 | pipeline-minted 34 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 34 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::2 Grammar::3 Adjektive | 11 | 0 | 11 | pipeline-minted 11 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 11 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::2 Grammar::4 Verben | 9 | 0 | 9 | pipeline-minted 9 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 9 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::2 Grammar::5 Kasus | 7 | 0 | 7 | pipeline-minted 7 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 7 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::3 Tenses | 36 | 0 | 36 | pipeline-minted 36 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 36 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::3 Tenses::1 Production | 18 | 0 | 18 | pipeline-minted 18 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 18 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::3 Tenses::2 Exercises | 18 | 0 | 18 | pipeline-minted 18 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 18 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::4 Exercises | 684 | 0 | 684 | pipeline-minted 684 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 684 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::4 Exercises::Konditionalsätze | 326 | 0 | 326 | pipeline-minted 326 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 326 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::4 Exercises::Konnektoren | 358 | 0 | 358 | pipeline-minted 358 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 358 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::5 Translation | 79 | 0 | 79 | pipeline-minted 79 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 79 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::5 Translation::1 Genus | 18 | 0 | 18 | pipeline-minted 18 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 18 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::5 Translation::2 Präpositionen | 34 | 0 | 34 | pipeline-minted 34 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 34 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::5 Translation::3 Adjektive | 11 | 0 | 11 | pipeline-minted 11 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 11 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::5 Translation::4 Verben | 9 | 0 | 9 | pipeline-minted 9 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 9 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::5 Translation::5 Kasus | 7 | 0 | 7 | pipeline-minted 7 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 7 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::6 My Errors | 20 | 0 | 20 | pipeline-minted 20 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 20 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::8 Pimsleur::Level 2 | 899 | 0 | 899 | batch-imported 899 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 899 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| DE German::8 Pimsleur::Level 4 | 1,256 | 0 | 1,256 | batch-imported 1,256 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 1,256 cards and 0 reps; never opted in, so suspend as reversible reference. |  |

## ES Spanish

Projected due backlog if the proposals are accepted: **44.5 → 43.2 minutes** (287 → 275 due cards).

| Subtree | Cards | Due | New | Provenance | Study depth | Difficulty | Proposed | Due load min before → after |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| ES Spanish::1 Expressions | 3,193 | 272 | 2,759 | pipeline-minted 3,193 (100.0%) | 1,024 reps / 434 cards; 2026-08-07 | A 37.3% / E 56.6% / mature ivl 25d | keep-active | 42.8 → 42.8 |
| Rationale |  |  |  |  |  |  | Recent study (1,024 reps in 60d) has a mixed signal (37.3% again, 56.6% easy); keep active. |  |
| ES Spanish::1 Expressions::1 Fluency | 3,193 | 272 | 2,759 | pipeline-minted 3,193 (100.0%) | 1,024 reps / 434 cards; 2026-08-07 | A 37.3% / E 56.6% / mature ivl 25d | keep-active | 42.8 → 42.8 |
| Rationale |  |  |  |  |  |  | Recent study (1,024 reps in 60d) has a mixed signal (37.3% again, 56.6% easy); keep active. |  |
| ES Spanish::2 Grammar | 273 | 5 | 268 | pipeline-minted 273 (100.0%) | 7 reps / 5 cards; 2026-08-05 | A 14.3% / E 0.0% / mature ivl — | suspend-reference | 0.6 → 0.0 |
| Rationale |  |  |  |  |  |  | Only 5 of 273 cards have been studied (1.8%); suspend the bulk as reversible reference. |  |
| ES Spanish::4 Exercises | 750 | 6 | 744 | pipeline-minted 750 (100.0%) | 6 reps / 6 cards; 2026-08-05 | A 100.0% / E 0.0% / mature ivl — | suspend-reference | 0.5 → 0.0 |
| Rationale |  |  |  |  |  |  | Only 6 of 750 cards have been studied (0.8%); suspend the bulk as reversible reference. |  |
| ES Spanish::4 Exercises::Conectores | 414 | 6 | 408 | pipeline-minted 414 (100.0%) | 6 reps / 6 cards; 2026-08-05 | A 100.0% / E 0.0% / mature ivl — | suspend-reference | 0.5 → 0.0 |
| Rationale |  |  |  |  |  |  | Only 6 of 414 cards have been studied (1.4%); suspend the bulk as reversible reference. |  |
| ES Spanish::2 Grammar::1 Tiempos | 71 | 4 | 67 | pipeline-minted 71 (100.0%) | 6 reps / 4 cards; 2026-07-28 | A 0.0% / E 0.0% / mature ivl — | suspend-reference | 0.5 → 0.0 |
| Rationale |  |  |  |  |  |  | Only 6 reps across 4 cards in 60d; the bulk is not yet opted in, so suspend as reversible reference. |  |
| ES Spanish::7 Rescue | 4 | 3 | 0 | pipeline-minted 4 (100.0%) | 15 reps / 4 cards; 2026-08-07 | A 13.3% / E 0.0% / mature ivl — | keep-active | 0.3 → 0.3 |
| Rationale |  |  |  |  |  |  | Recent targeted study (15 reps in 60d) is an explicit rescue/error path; keep it active. |  |
| ES Spanish::2 Grammar::3 Condicionales | 24 | 1 | 23 | pipeline-minted 24 (100.0%) | 1 reps / 1 cards; 2026-08-05 | A 100.0% / E 0.0% / mature ivl — | suspend-reference | 0.1 → 0.0 |
| Rationale |  |  |  |  |  |  | Only 1 reps across 1 cards in 60d; the bulk is not yet opted in, so suspend as reversible reference. |  |
| ES Spanish::8 Pimsleur | 8,429 | 1 | 8,428 | batch-imported 8,429 (100.0%) | 1 reps / 1 cards; 2026-04-20 | A 0.0% / E 0.0% / mature ivl — | suspend-reference | 0.1 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 1 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| ES Spanish::8 Pimsleur::Spain | 4,378 | 1 | 4,377 | batch-imported 4,378 (100.0%) | 1 reps / 1 cards; 2026-04-20 | A 0.0% / E 0.0% / mature ivl — | suspend-reference | 0.1 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 1 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| ES Spanish::2 Grammar::0 Escucha | 8 | 0 | 8 | pipeline-minted 8 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 8 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::2 Grammar::10 Interferencias | 15 | 0 | 15 | pipeline-minted 15 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 15 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::2 Grammar::2 Subjuntivo | 23 | 0 | 23 | pipeline-minted 23 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 23 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::2 Grammar::4 Imperativo | 45 | 0 | 45 | pipeline-minted 45 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 45 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::2 Grammar::5 Pronombres | 40 | 0 | 40 | pipeline-minted 40 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 40 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::2 Grammar::6 Preposiciones | 24 | 0 | 24 | pipeline-minted 24 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 24 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::2 Grammar::7 Ser/Estar | 12 | 0 | 12 | pipeline-minted 12 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 12 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::2 Grammar::8 Grado y cantidad | 11 | 0 | 11 | pipeline-minted 11 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 11 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::3 Tenses | 36 | 0 | 36 | pipeline-minted 36 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 36 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::3 Tenses::1 Production | 18 | 0 | 18 | pipeline-minted 18 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 18 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::3 Tenses::2 Exercises | 18 | 0 | 18 | pipeline-minted 18 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 18 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::4 Exercises::Condicionales | 336 | 0 | 336 | pipeline-minted 336 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 336 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::5 Translation | 250 | 0 | 250 | pipeline-minted 250 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 250 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::5 Translation::1 Tiempos | 71 | 0 | 71 | pipeline-minted 71 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 71 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::5 Translation::2 Subjuntivo | 23 | 0 | 23 | pipeline-minted 23 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 23 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::5 Translation::3 Condicionales | 24 | 0 | 24 | pipeline-minted 24 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 24 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::5 Translation::4 Imperativo | 45 | 0 | 45 | pipeline-minted 45 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 45 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::5 Translation::5 Pronombres | 40 | 0 | 40 | pipeline-minted 40 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 40 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::5 Translation::6 Preposiciones | 24 | 0 | 24 | pipeline-minted 24 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 24 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::5 Translation::7 Ser/Estar | 12 | 0 | 12 | pipeline-minted 12 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 12 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::5 Translation::8 Grado y cantidad | 11 | 0 | 11 | pipeline-minted 11 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 11 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::6 My Errors | 20 | 0 | 20 | pipeline-minted 20 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 20 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ES Spanish::8 Pimsleur::Latin America | 4,051 | 0 | 4,051 | batch-imported 4,051 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 4,051 cards and 0 reps; never opted in, so suspend as reversible reference. |  |

## FR French

Projected due backlog if the proposals are accepted: **84.9 → 84.0 minutes** (758 → 751 due cards).

| Subtree | Cards | Due | New | Provenance | Study depth | Difficulty | Proposed | Due load min before → after |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| FR French::1 Expressions | 3,488 | 662 | 2,742 | pipeline-minted 3,488 (100.0%) | 2,329 reps / 746 cards; 2026-08-06 | A 31.3% / E 36.0% / mature ivl 243d | keep-active | 72.6 → 72.6 |
| Rationale |  |  |  |  |  |  | Recent study (436 reps in 60d) has a mixed signal (31.3% again, 36.0% easy); keep active. |  |
| FR French::1 Expressions::1 Fluency | 3,488 | 662 | 2,742 | pipeline-minted 3,488 (100.0%) | 2,329 reps / 746 cards; 2026-08-06 | A 31.3% / E 36.0% / mature ivl 243d | keep-active | 72.6 → 72.6 |
| Rationale |  |  |  |  |  |  | Recent study (436 reps in 60d) has a mixed signal (31.3% again, 36.0% easy); keep active. |  |
| FR French::2 Grammar | 175 | 95 | 80 | pipeline-minted 175 (100.0%) | 128 reps / 95 cards; 2026-08-03 | A 23.4% / E 73.4% / mature ivl — | keep-active | 12.2 → 12.2 |
| Rationale |  |  |  |  |  |  | Recent study (128 reps in 60d) has a mixed signal (23.4% again, 73.4% easy); keep active. |  |
| FR French::2 Grammar::1 Temps | 58 | 58 | 0 | pipeline-minted 58 (100.0%) | 81 reps / 58 cards; 2026-08-03 | A 25.9% / E 71.6% / mature ivl — | keep-active | 7.4 → 7.4 |
| Rationale |  |  |  |  |  |  | Recent study (81 reps in 60d) has a mixed signal (25.9% again, 71.6% easy); keep active. |  |
| FR French::2 Grammar::3 Subjonctif | 20 | 20 | 0 | pipeline-minted 20 (100.0%) | 24 reps / 20 cards; 2026-08-03 | A 16.7% / E 83.3% / mature ivl — | owner-review | 2.6 → 2.6 |
| Rationale |  |  |  |  |  |  | Recently studied, but easy-rate is 83.3% with a — mature median; level signal is mixed. |  |
| FR French::2 Grammar::2 Conditionnel | 11 | 11 | 0 | pipeline-minted 11 (100.0%) | 17 reps / 11 cards; 2026-08-03 | A 29.4% / E 64.7% / mature ivl — | keep-active | 1.4 → 1.4 |
| Rationale |  |  |  |  |  |  | Recent study (17 reps in 60d) has a mixed signal (29.4% again, 64.7% easy); keep active. |  |
| FR French::2 Grammar::0 Écoute | 14 | 6 | 8 | pipeline-minted 14 (100.0%) | 6 reps / 6 cards; 2026-08-03 | A 0.0% / E 83.3% / mature ivl — | suspend-reference | 0.8 → 0.0 |
| Rationale |  |  |  |  |  |  | Only 6 reps across 6 cards in 60d; the bulk is not yet opted in, so suspend as reversible reference. |  |
| FR French::4 Exercises | 706 | 1 | 705 | pipeline-minted 706 (100.0%) | 1 reps / 1 cards; 2026-08-04 | A 0.0% / E 0.0% / mature ivl — | suspend-reference | 0.1 → 0.0 |
| Rationale |  |  |  |  |  |  | Only 1 of 706 cards have been studied (0.1%); suspend the bulk as reversible reference. |  |
| FR French::4 Exercises::Connecteurs | 382 | 1 | 381 | pipeline-minted 382 (100.0%) | 1 reps / 1 cards; 2026-08-04 | A 0.0% / E 0.0% / mature ivl — | suspend-reference | 0.1 → 0.0 |
| Rationale |  |  |  |  |  |  | Only 1 of 382 cards have been studied (0.3%); suspend the bulk as reversible reference. |  |
| FR French::2 Grammar::10 Interférences | 15 | 0 | 15 | pipeline-minted 15 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 15 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::2 Grammar::4 Pronoms | 12 | 0 | 12 | pipeline-minted 12 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 12 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::2 Grammar::5 Prépositions | 7 | 0 | 7 | pipeline-minted 7 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 7 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::2 Grammar::6 Genre & accord | 12 | 0 | 12 | pipeline-minted 12 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 12 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::2 Grammar::7 Articles & quantités | 26 | 0 | 26 | pipeline-minted 26 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 26 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::3 Tenses | 36 | 0 | 36 | pipeline-minted 36 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 36 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::3 Tenses::1 Production | 18 | 0 | 18 | pipeline-minted 18 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 18 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::3 Tenses::2 Exercises | 18 | 0 | 18 | pipeline-minted 18 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 18 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::4 Exercises::Conditionnels | 324 | 0 | 324 | pipeline-minted 324 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 324 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::5 Translation | 146 | 0 | 146 | pipeline-minted 146 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 146 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::5 Translation::1 Temps | 58 | 0 | 58 | pipeline-minted 58 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 58 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::5 Translation::2 Conditionnel | 11 | 0 | 11 | pipeline-minted 11 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 11 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::5 Translation::3 Subjonctif | 20 | 0 | 20 | pipeline-minted 20 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 20 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::5 Translation::4 Pronoms | 12 | 0 | 12 | pipeline-minted 12 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 12 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::5 Translation::5 Prépositions | 7 | 0 | 7 | pipeline-minted 7 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 7 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::5 Translation::6 Genre & accord | 12 | 0 | 12 | pipeline-minted 12 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 12 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::5 Translation::7 Articles & quantités | 26 | 0 | 26 | pipeline-minted 26 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 26 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::6 My Errors | 20 | 0 | 20 | pipeline-minted 20 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 20 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::8 Pimsleur | 4,693 | 0 | 4,693 | batch-imported 4,693 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 4,693 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::8 Pimsleur::Level 1 | 727 | 0 | 727 | batch-imported 727 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 727 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::8 Pimsleur::Level 2 | 720 | 0 | 720 | batch-imported 720 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 720 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::8 Pimsleur::Level 3 | 730 | 0 | 730 | batch-imported 730 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 730 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::8 Pimsleur::Level 4 | 1,256 | 0 | 1,256 | batch-imported 1,256 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 1,256 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| FR French::8 Pimsleur::Level 5 | 1,260 | 0 | 1,260 | batch-imported 1,260 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 1,260 cards and 0 reps; never opted in, so suspend as reversible reference. |  |

## IT Italian

Projected due backlog if the proposals are accepted: **185.0 → 94.6 minutes** (1,608 → 649 due cards).

| Subtree | Cards | Due | New | Provenance | Study depth | Difficulty | Proposed | Due load min before → after |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| IT Italian::8 Pimsleur | 5,344 | 1,009 | 4,335 | batch-imported 5,344 (100.0%) | 1,892 reps / 1,009 cards; 2026-05-17 | A 8.2% / E 77.7% / mature ivl 48d | sample-hardest (N=50) | 95.2 → 4.7 |
| Rationale |  |  |  |  |  |  | Batch-imported bulk has 1,892 reps and 1,009 due; keep 50 highest-lapse/again cards active and suspend the rest. |  |
| IT Italian::8 Pimsleur::Level 3 | 1,145 | 985 | 160 | batch-imported 1,145 (100.0%) | 1,864 reps / 985 cards; 2026-05-17 | A 8.1% / E 78.2% / mature ivl 48d | sample-hardest (N=50) | 92.9 → 4.7 |
| Rationale |  |  |  |  |  |  | Batch-imported bulk has 1,864 reps and 985 due; keep 50 highest-lapse/again cards active and suspend the rest. |  |
| IT Italian::1 Expressions | 5,730 | 515 | 4,263 | pipeline-minted 5,730 (100.0%) | 6,262 reps / 1,467 cards; 2026-08-07 | A 29.9% / E 63.1% / mature ivl 99d | keep-active | 79.5 → 79.5 |
| Rationale |  |  |  |  |  |  | Recent study (4,223 reps in 60d) has a mixed signal (29.9% again, 63.1% easy); keep active. |  |
| IT Italian::1 Expressions::1 Fluency | 5,730 | 515 | 4,263 | pipeline-minted 5,730 (100.0%) | 6,262 reps / 1,467 cards; 2026-08-07 | A 29.9% / E 63.1% / mature ivl 99d | keep-active | 79.5 → 79.5 |
| Rationale |  |  |  |  |  |  | Recent study (4,223 reps in 60d) has a mixed signal (29.9% again, 63.1% easy); keep active. |  |
| IT Italian::2 Grammar | 155 | 72 | 77 | pipeline-minted 155 (100.0%) | 95 reps / 78 cards; 2026-08-05 | A 15.8% / E 80.0% / mature ivl — | owner-review | 9.3 → 9.3 |
| Rationale |  |  |  |  |  |  | Recently studied, but easy-rate is 80.0% with a — mature median; level signal is mixed. |  |
| IT Italian::2 Grammar::1 Tempi | 68 | 20 | 42 | pipeline-minted 68 (100.0%) | 27 reps / 26 cards; 2026-08-05 | A 11.1% / E 88.9% / mature ivl — | owner-review | 2.6 → 2.6 |
| Rationale |  |  |  |  |  |  | Recently studied, but easy-rate is 88.9% with a — mature median; level signal is mixed. |  |
| IT Italian::2 Grammar::3 Congiuntivo | 18 | 18 | 0 | pipeline-minted 18 (100.0%) | 22 reps / 18 cards; 2026-08-03 | A 13.6% / E 81.8% / mature ivl — | owner-review | 2.3 → 2.3 |
| Rationale |  |  |  |  |  |  | Recently studied, but easy-rate is 81.8% with a — mature median; level signal is mixed. |  |
| IT Italian::8 Pimsleur::Level 4 | 1,269 | 23 | 1,246 | batch-imported 1,269 (100.0%) | 27 reps / 23 cards; 2026-05-09 | A 14.8% / E 48.1% / mature ivl — | suspend-reference | 2.2 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 27 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| IT Italian::2 Grammar::5 Genere e plurali | 12 | 12 | 0 | pipeline-minted 12 (100.0%) | 15 reps / 12 cards; 2026-08-03 | A 13.3% / E 80.0% / mature ivl — | owner-review | 1.5 → 1.5 |
| Rationale |  |  |  |  |  |  | Recently studied, but easy-rate is 80.0% with a — mature median; level signal is mixed. |  |
| IT Italian::2 Grammar::2 Condizionale | 11 | 11 | 0 | pipeline-minted 11 (100.0%) | 17 reps / 11 cards; 2026-08-03 | A 23.5% / E 64.7% / mature ivl — | keep-active | 1.4 → 1.4 |
| Rationale |  |  |  |  |  |  | Recent study (17 reps in 60d) has a mixed signal (23.5% again, 64.7% easy); keep active. |  |
| IT Italian::2 Grammar::4 Clitici | 11 | 11 | 0 | pipeline-minted 11 (100.0%) | 14 reps / 11 cards; 2026-08-03 | A 21.4% / E 78.6% / mature ivl — | owner-review | 1.4 → 1.4 |
| Rationale |  |  |  |  |  |  | Recently studied, but easy-rate is 78.6% with a — mature median; level signal is mixed. |  |
| IT Italian::6 My Errors | 11 | 11 | 0 | pipeline-minted 11 (100.0%) | 18 reps / 11 cards; 2026-08-03 | A 33.3% / E 61.1% / mature ivl — | keep-active | 1.0 → 1.0 |
| Rationale |  |  |  |  |  |  | Recent targeted study (18 reps in 60d) is an explicit rescue/error path; keep it active. |  |
| IT Italian::7 Rescue | 1 | 1 | 0 | pipeline-minted 1 (100.0%) | 2 reps / 1 cards; 2026-08-07 | A 0.0% / E 0.0% / mature ivl — | keep-active | 0.1 → 0.1 |
| Rationale |  |  |  |  |  |  | Recent targeted study (2 reps in 60d) is an explicit rescue/error path; keep it active. |  |
| IT Italian::8 Pimsleur::Level 1 | 788 | 1 | 787 | batch-imported 788 (100.0%) | 1 reps / 1 cards; 2026-05-12 | A 0.0% / E 100.0% / mature ivl — | suspend-reference | 0.1 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 1 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| IT Italian::2 Grammar::0 Ascolto | 10 | 0 | 10 | pipeline-minted 10 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 10 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::2 Grammar::10 Interferenze | 15 | 0 | 15 | pipeline-minted 15 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 15 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::2 Grammar::6 Reggenze | 10 | 0 | 10 | pipeline-minted 10 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 10 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::3 Tenses | 34 | 0 | 17 | pipeline-minted 34 (100.0%) | 26 reps / 17 cards; 2026-08-07 | A 30.8% / E 65.4% / mature ivl — | keep-active | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Recent study (26 reps in 60d) has a mixed signal (30.8% again, 65.4% easy); keep active. |  |
| IT Italian::3 Tenses::1 Production | 17 | 0 | 17 | pipeline-minted 17 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 17 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::3 Tenses::2 Exercises | 17 | 0 | 0 | pipeline-minted 17 (100.0%) | 26 reps / 17 cards; 2026-08-07 | A 30.8% / E 65.4% / mature ivl — | keep-active | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Recent study (26 reps in 60d) has a mixed signal (30.8% again, 65.4% easy); keep active. |  |
| IT Italian::4 Exercises | 734 | 0 | 734 | pipeline-minted 734 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 734 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::4 Exercises::Connettivi | 402 | 0 | 402 | pipeline-minted 402 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 402 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::4 Exercises::Periodo ipotetico | 332 | 0 | 332 | pipeline-minted 332 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 332 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::5 Translation | 130 | 0 | 130 | pipeline-minted 130 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 130 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::5 Translation::1 Tempi | 68 | 0 | 68 | pipeline-minted 68 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 68 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::5 Translation::2 Condizionale | 11 | 0 | 11 | pipeline-minted 11 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 11 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::5 Translation::3 Congiuntivo | 18 | 0 | 18 | pipeline-minted 18 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 18 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::5 Translation::4 Clitici | 11 | 0 | 11 | pipeline-minted 11 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 11 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::5 Translation::5 Genere e plurali | 12 | 0 | 12 | pipeline-minted 12 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 12 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::5 Translation::6 Reggenze | 10 | 0 | 10 | pipeline-minted 10 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 10 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::8 Pimsleur::Level 2 | 882 | 0 | 882 | batch-imported 882 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 882 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| IT Italian::8 Pimsleur::Level 5 | 1,260 | 0 | 1,260 | batch-imported 1,260 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 1,260 cards and 0 reps; never opted in, so suspend as reversible reference. |  |

## PT Portuguese

Projected due backlog if the proposals are accepted: **24.3 → 23.3 minutes** (161 → 152 due cards).

| Subtree | Cards | Due | New | Provenance | Study depth | Difficulty | Proposed | Due load min before → after |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| PT Portuguese::1 Expressions | 3,834 | 149 | 3,025 | pipeline-minted 3,834 (100.0%) | 3,445 reps / 809 cards; 2026-08-07 | A 38.6% / E 53.1% / mature ivl 92d | keep-active | 23.0 → 23.0 |
| Rationale |  |  |  |  |  |  | Recent study (3,049 reps in 60d) has a mixed signal (38.6% again, 53.1% easy); keep active. |  |
| PT Portuguese::1 Expressions::1 Fluency | 3,834 | 149 | 3,025 | pipeline-minted 3,834 (100.0%) | 3,445 reps / 809 cards; 2026-08-07 | A 38.6% / E 53.1% / mature ivl 92d | keep-active | 23.0 → 23.0 |
| Rationale |  |  |  |  |  |  | Recent study (3,049 reps in 60d) has a mixed signal (38.6% again, 53.1% easy); keep active. |  |
| PT Portuguese::8 Pimsleur | 4,344 | 9 | 4,335 | batch-imported 4,344 (100.0%) | 9 reps / 9 cards; 2026-04-20 | A 33.3% / E 44.4% / mature ivl — | suspend-reference | 1.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 9 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| PT Portuguese::8 Pimsleur::Level 4 | 1,254 | 6 | 1,248 | batch-imported 1,254 (100.0%) | 6 reps / 6 cards; 2026-04-20 | A 16.7% / E 66.7% / mature ivl — | suspend-reference | 0.6 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 6 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| PT Portuguese::7 Rescue | 3 | 3 | 0 | pipeline-minted 3 (100.0%) | 9 reps / 3 cards; 2026-08-07 | A 22.2% / E 0.0% / mature ivl — | keep-active | 0.3 → 0.3 |
| Rationale |  |  |  |  |  |  | Recent targeted study (9 reps in 60d) is an explicit rescue/error path; keep it active. |  |
| PT Portuguese::8 Pimsleur::Level 5 | 1,256 | 3 | 1,253 | batch-imported 1,256 (100.0%) | 3 reps / 3 cards; 2026-04-20 | A 66.7% / E 0.0% / mature ivl — | suspend-reference | 0.3 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 3 reps but no recent opt-in in the 60-day window; suspend as reversible reference. |  |
| PT Portuguese::2 Grammar | 150 | 0 | 150 | pipeline-minted 150 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 150 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::2 Grammar::0 Escuta | 8 | 0 | 8 | pipeline-minted 8 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 8 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::2 Grammar::1 Tempos | 52 | 0 | 52 | pipeline-minted 52 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 52 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::2 Grammar::10 Interferência | 15 | 0 | 15 | pipeline-minted 15 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 15 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::2 Grammar::2 Condicional | 12 | 0 | 12 | pipeline-minted 12 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 12 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::2 Grammar::3 Subjuntivo | 30 | 0 | 30 | pipeline-minted 30 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 30 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::2 Grammar::4 Clíticos | 11 | 0 | 11 | pipeline-minted 11 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 11 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::2 Grammar::5 Gênero & Artigos | 22 | 0 | 22 | pipeline-minted 22 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 22 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::3 Tenses | 28 | 0 | 14 | pipeline-minted 28 (100.0%) | 22 reps / 14 cards; 2026-08-07 | A 27.3% / E 63.6% / mature ivl — | keep-active | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Recent study (22 reps in 60d) has a mixed signal (27.3% again, 63.6% easy); keep active. |  |
| PT Portuguese::3 Tenses::1 Production | 14 | 0 | 14 | pipeline-minted 14 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 14 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::3 Tenses::2 Exercises | 14 | 0 | 0 | pipeline-minted 14 (100.0%) | 22 reps / 14 cards; 2026-08-07 | A 27.3% / E 63.6% / mature ivl — | keep-active | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Recent study (22 reps in 60d) has a mixed signal (27.3% again, 63.6% easy); keep active. |  |
| PT Portuguese::4 Exercises | 670 | 0 | 670 | pipeline-minted 670 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 670 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::4 Exercises::Condicionais | 320 | 0 | 320 | pipeline-minted 320 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 320 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::4 Exercises::Conectores | 350 | 0 | 350 | pipeline-minted 350 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 350 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::5 Translation | 127 | 0 | 127 | pipeline-minted 127 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 127 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::5 Translation::1 Tempos | 52 | 0 | 52 | pipeline-minted 52 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 52 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::5 Translation::2 Condicional | 12 | 0 | 12 | pipeline-minted 12 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 12 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::5 Translation::3 Subjuntivo | 30 | 0 | 30 | pipeline-minted 30 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 30 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::5 Translation::4 Clíticos | 11 | 0 | 11 | pipeline-minted 11 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 11 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::5 Translation::5 Gênero & Artigos | 22 | 0 | 22 | pipeline-minted 22 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 22 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::6 My Errors | 20 | 0 | 20 | pipeline-minted 20 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Pipeline reservoir has 20 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::8 Pimsleur::Level 1 | 627 | 0 | 627 | batch-imported 627 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 627 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::8 Pimsleur::Level 2 | 601 | 0 | 601 | batch-imported 601 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 601 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| PT Portuguese::8 Pimsleur::Level 3 | 606 | 0 | 606 | batch-imported 606 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Batch-imported reservoir has 606 cards and 0 reps; never opted in, so suspend as reversible reference. |  |

## ZH Mandarin

Projected due backlog if the proposals are accepted: **364.8 → 41.3 minutes** (3,381 → 447 due cards).

| Subtree | Cards | Due | New | Provenance | Study depth | Difficulty | Proposed | Due load min before → after |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| ZH Mandarin::8 Pimsleur | 3,043 | 2,989 | 8 | batch-imported 3,043 (100.0%) | 12,272 reps / 3,035 cards; 2026-06-08 | A 28.8% / E 59.7% / mature ivl 38d | sample-hardest (N=50) | 331.7 → 5.5 |
| Rationale |  |  |  |  |  |  | Batch-imported bulk has 12,272 reps and 2,989 due; keep 50 highest-lapse/again cards active and suspend the rest. |  |
| ZH Mandarin::8 Pimsleur::Level 5 | 621 | 613 | 8 | batch-imported 621 (100.0%) | 1,946 reps / 613 cards; 2026-05-25 | A 43.2% / E 49.3% / mature ivl 28d | sample-hardest (N=50) | 68.0 → 5.5 |
| Rationale |  |  |  |  |  |  | Batch-imported bulk has 1,946 reps and 613 due; keep 50 highest-lapse/again cards active and suspend the rest. |  |
| ZH Mandarin::8 Pimsleur::Level 4 | 610 | 610 | 0 | batch-imported 610 (100.0%) | 3,382 reps / 610 cards; 2026-06-03 | A 42.5% / E 50.3% / mature ivl 36d | sample-hardest (N=50) | 67.7 → 5.5 |
| Rationale |  |  |  |  |  |  | Batch-imported bulk has 3,382 reps and 610 due; keep 50 highest-lapse/again cards active and suspend the rest. |  |
| ZH Mandarin::8 Pimsleur::Level 2 | 608 | 608 | 0 | batch-imported 608 (100.0%) | 2,114 reps / 608 cards; 2026-05-12 | A 16.8% / E 65.6% / mature ivl 30d | sample-hardest (N=50) | 67.5 → 5.5 |
| Rationale |  |  |  |  |  |  | Batch-imported bulk has 2,114 reps and 608 due; keep 50 highest-lapse/again cards active and suspend the rest. |  |
| ZH Mandarin::8 Pimsleur::Level 1 | 600 | 600 | 0 | batch-imported 600 (100.0%) | 2,198 reps / 600 cards; 2026-05-11 | A 12.3% / E 69.7% / mature ivl 40d | sample-hardest (N=50) | 66.6 → 5.5 |
| Rationale |  |  |  |  |  |  | Batch-imported bulk has 2,198 reps and 600 due; keep 50 highest-lapse/again cards active and suspend the rest. |  |
| ZH Mandarin::8 Pimsleur::Level 3 | 604 | 558 | 0 | batch-imported 604 (100.0%) | 2,632 reps / 604 cards; 2026-06-08 | A 24.2% / E 66.4% / mature ivl 49d | sample-hardest (N=50) | 61.9 → 5.5 |
| Rationale |  |  |  |  |  |  | Batch-imported bulk has 2,632 reps and 558 due; keep 50 highest-lapse/again cards active and suspend the rest. |  |
| ZH Mandarin::Languages | 2,614 | 179 | 2,435 | pipeline-minted 43 (1.6%); batch-imported 2,571 (98.4%) | 270 reps / 179 cards; 2026-06-08 | A 8.5% / E 71.9% / mature ivl 23d | sample-hardest (N=50) | 22.4 → 6.2 |
| Rationale |  |  |  |  |  |  | Batch-imported bulk has 270 reps and 179 due; keep 50 highest-lapse/again cards active and suspend the rest. |  |
| ZH Mandarin::Languages::Mandarin | 2,614 | 179 | 2,435 | pipeline-minted 43 (1.6%); batch-imported 2,571 (98.4%) | 270 reps / 179 cards; 2026-06-08 | A 8.5% / E 71.9% / mature ivl 23d | sample-hardest (N=50) | 22.4 → 6.2 |
| Rationale |  |  |  |  |  |  | Batch-imported bulk has 270 reps and 179 due; keep 50 highest-lapse/again cards active and suspend the rest. |  |
| ZH Mandarin::Mandarin Characters 2026-06-20 | 222 | 122 | 100 | hand-made 222 (100.0%) | 366 reps / 122 cards; 2026-07-26 | A 46.7% / E 35.5% / mature ivl 38d | keep-active | 6.1 → 6.1 |
| Rationale |  |  |  |  |  |  | Recent study (366 reps in 60d) has a mixed signal (46.7% again, 35.5% easy); keep active. |  |
| ZH Mandarin::Mandarin Zones | 65 | 65 | 0 | hand-made 65 (100.0%) | 73 reps / 65 cards; 2026-06-01 | A 9.6% / E 83.6% / mature ivl — | suspend-reference | 3.3 → 0.0 |
| Rationale |  |  |  |  |  |  | Stale hand-made study is easy-heavy (83.6% easy) with no recent opt-in; suspend as reversible reference. |  |
| ZH Mandarin::Mandarin Locations | 13 | 13 | 0 | hand-made 13 (100.0%) | 68 reps / 13 cards; 2026-06-06 | A 16.2% / E 73.5% / mature ivl — | owner-review | 0.7 → 0.7 |
| Rationale |  |  |  |  |  |  | Study exists (68 reps) but is outside the recent window; owner review is safer than inferring the current level. |  |
| ZH Mandarin::Mandarin China Provinces | 204 | 8 | 196 | hand-made 204 (100.0%) | 15 reps / 8 cards; 2026-04-20 | A 73.3% / E 6.7% / mature ivl — | owner-review | 0.4 → 0.4 |
| Rationale |  |  |  |  |  |  | Study exists (15 reps) but is outside the recent window; owner review is safer than inferring the current level. |  |
| ZH Mandarin::Mandarin Actors | 55 | 4 | 0 | hand-made 55 (100.0%) | 1,091 reps / 55 cards; 2026-07-30 | A 31.5% / E 64.0% / mature ivl 185d | owner-review | 0.2 → 0.2 |
| Rationale |  |  |  |  |  |  | Recently active, but 64.0% easy with a 185d mature median suggests beneath-level material; owner review. |  |
| ZH Mandarin::Mandarin Palace | 339 | 1 | 338 | hand-made 339 (100.0%) | 1 reps / 1 cards; 2026-08-05 | A 0.0% / E 100.0% / mature ivl — | suspend-reference | 0.1 → 0.0 |
| Rationale |  |  |  |  |  |  | Only 1 of 339 cards have been studied (0.3%); suspend the bulk as reversible reference. |  |
| ZH Mandarin::Mandarin Palace::Characters | 100 | 1 | 99 | hand-made 100 (100.0%) | 1 reps / 1 cards; 2026-08-05 | A 0.0% / E 100.0% / mature ivl — | suspend-reference | 0.1 → 0.0 |
| Rationale |  |  |  |  |  |  | Only 1 of 100 cards have been studied (1.0%); suspend the bulk as reversible reference. |  |
| ZH Mandarin::Mandarin Palace::Words | 239 | 0 | 239 | hand-made 239 (100.0%) | 0 reps / 0 cards; never | — | suspend-reference | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Hand-made reservoir has 239 cards and 0 reps; never opted in, so suspend as reversible reference. |  |
| ZH Mandarin::Mandarin Props | 599 | 0 | 0 | hand-made 599 (100.0%) | 26,890 reps / 599 cards; 2026-08-06 | A 23.2% / E 69.6% / mature ivl 186d | owner-review | 0.0 → 0.0 |
| Rationale |  |  |  |  |  |  | Recently active, but 69.6% easy with a 186d mature median suggests beneath-level material; owner review. |  |

## zz Dormant — completeness only

These subtrees are already retired. They remain in the evidence so the console can display them, but they are not part of the active language backlog.

| Subtree | Cards | Suspended | Reps | Last touch | Proposed | Rationale |
| --- | ---: | ---: | ---: | --- | --- | --- |
| zz Dormant::Experiments | 27 | 27 | 43 | 2026-04-22 | suspend-reference | Already retired and currently suspended; keep the material only as reversible reference. |
| zz Dormant::Pimsleur | 3,047 | 0 | 0 | never | suspend-reference | Already retired in zz Dormant but 3,047 cards remain unsuspended; suspend only as reversible reference. |
| zz Dormant::Retired Idioms Audio | 12,667 | 12,667 | 3,103 | 2026-07-28 | suspend-reference | Already retired and currently suspended; keep the material only as reversible reference. |
| zz Dormant::z-archive | 6,242 | 6,242 | 937 | 2026-07-19 | suspend-reference | Already retired and currently suspended; keep the material only as reversible reference. |

## Provenance and constants

The JSON contains per-model counts, origin-tag counts, raw rating counts, and hardest-sample card-level lapse/again evidence. The cross-check below records whether DJ-C1's constants matched the local recomputation.

- DJ-C1 constants present: `True`; matched local recomputation: `True`; compared cells: `48`.
- Source totals: `83,436` current cards, `75,471` notes, `529` decks, `62,554` revlog rows; `62,407` revlogs joined to current cards.
