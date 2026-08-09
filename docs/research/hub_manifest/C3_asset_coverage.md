# C3 asset coverage

Deterministic local snapshot through `2026-08-09T00:06:46.948035+00:00`. The scan opened no image for decoding: it captured canonical filenames, byte sizes, and SHA-1 hashes only. The render snapshot digest is `0f77243ef277361907e13892e7726f94ee22b32661aac69a47e9e6e2b0116e39`.

## Asset coverage by language

| Language | Examples | QA-passed | Rendered-unjudged | Brief-only | No-brief | Remote-unverified | QA pass rate | QA-passed coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DE | 4,110 | 0 | 72 | 4,038 | 0 | 0 | — (0/0) | 0.00% |
| ES | 2,886 | 222 | 762 | 681 | 174 | 1,047 | 56.78% (222/391) | 7.69% |
| FR | 2,892 | 0 | 0 | 2,892 | 0 | 0 | — (0/0) | 0.00% |
| IT | 4,974 | 0 | 0 | 4,974 | 0 | 0 | — (0/0) | 0.00% |
| PT | 3,396 | 0 | 0 | 3,396 | 0 | 0 | — (0/0) | 0.00% |

The final-status total is 18,258: qa-passed 222, rendered-unjudged 834, brief-only 15,981, no-brief 174, remote-unverified 1,047. `Rendered-unjudged` is the commissioned catch-all for a local render without an effective pass; the separate QA field distinguishes current fail from pending.

## Context-audio coverage

| Language | Idioms | Has context | No context | Coverage |
|---|---:|---:|---:|---:|
| DE | 685 | 676 | 9 | 98.69% |
| ES | 481 | 460 | 21 | 95.63% |
| FR | 482 | 478 | 4 | 99.17% |
| IT | 829 | 806 | 23 | 97.23% |
| PT | 567 | 552 | 15 | 97.35% |
| **Total** | **3,044** | **2,972** | **72** | **97.63%** |

## Top 50 render priorities

This is the head of the complete numeric-ID queue stored in the JSON. A `remote-unverified` row requests Mac verification/sync, not a duplicate render; a local failed or pending row requests repair/judging before any rerender decision.

| Rank | Lang | Example | Expression | Ord | Idiom | Status | Expr reps | Ex reps | Basis | Next action |
|---:|---|---:|---:|---:|---|---|---:|---:|---|---|
| 1 | IT | 2614 | 457 | 4 | andare per mare | brief-only | 28 | 10 | expression-study-activity | render-on-owner |
| 2 | IT | 2612 | 457 | 2 | andare per mare | brief-only | 28 | 8 | expression-study-activity | render-on-owner |
| 3 | IT | 2615 | 457 | 5 | andare per mare | brief-only | 28 | 4 | expression-study-activity | render-on-owner |
| 4 | IT | 2613 | 457 | 3 | andare per mare | brief-only | 28 | 3 | expression-study-activity | render-on-owner |
| 5 | IT | 2611 | 457 | 1 | andare per mare | brief-only | 28 | 2 | expression-study-activity | render-on-owner |
| 6 | IT | 2616 | 457 | 6 | andare per mare | brief-only | 28 | 1 | expression-study-activity | render-on-owner |
| 7 | IT | 766 | 115 | 4 | visto sfilare | brief-only | 27 | 9 | expression-study-activity | render-on-owner |
| 8 | IT | 768 | 115 | 6 | visto sfilare | brief-only | 27 | 7 | expression-study-activity | render-on-owner |
| 9 | IT | 765 | 115 | 3 | visto sfilare | brief-only | 27 | 4 | expression-study-activity | render-on-owner |
| 10 | IT | 767 | 115 | 5 | visto sfilare | brief-only | 27 | 3 | expression-study-activity | render-on-owner |
| 11 | IT | 763 | 115 | 1 | visto sfilare | brief-only | 27 | 2 | expression-study-activity | render-on-owner |
| 12 | IT | 764 | 115 | 2 | visto sfilare | brief-only | 27 | 2 | expression-study-activity | render-on-owner |
| 13 | PT | 843 | 149 | 3 | acabado de sair | brief-only | 24 | 11 | expression-study-activity | render-on-owner |
| 14 | PT | 844 | 149 | 4 | acabado de sair | brief-only | 24 | 6 | expression-study-activity | render-on-owner |
| 15 | PT | 841 | 149 | 1 | acabado de sair | brief-only | 24 | 4 | expression-study-activity | render-on-owner |
| 16 | PT | 842 | 149 | 2 | acabado de sair | brief-only | 24 | 1 | expression-study-activity | render-on-owner |
| 17 | PT | 845 | 149 | 5 | acabado de sair | brief-only | 24 | 1 | expression-study-activity | render-on-owner |
| 18 | PT | 846 | 149 | 6 | acabado de sair | brief-only | 24 | 1 | expression-study-activity | render-on-owner |
| 19 | IT | 755 | 113 | 5 | quello a cui stiamo guardando | brief-only | 23 | 9 | expression-study-activity | render-on-owner |
| 20 | IT | 788 | 119 | 2 | vanno di moda | brief-only | 23 | 8 | expression-study-activity | render-on-owner |
| 21 | IT | 717 | 107 | 3 | non provò nemmeno a addolcire la notizia | brief-only | 23 | 6 | expression-study-activity | render-on-owner |
| 22 | IT | 718 | 107 | 4 | non provò nemmeno a addolcire la notizia | brief-only | 23 | 5 | expression-study-activity | render-on-owner |
| 23 | IT | 787 | 119 | 1 | vanno di moda | brief-only | 23 | 4 | expression-study-activity | render-on-owner |
| 24 | IT | 715 | 107 | 1 | non provò nemmeno a addolcire la notizia | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 25 | IT | 716 | 107 | 2 | non provò nemmeno a addolcire la notizia | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 26 | IT | 719 | 107 | 5 | non provò nemmeno a addolcire la notizia | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 27 | IT | 720 | 107 | 6 | non provò nemmeno a addolcire la notizia | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 28 | IT | 751 | 113 | 1 | quello a cui stiamo guardando | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 29 | IT | 752 | 113 | 2 | quello a cui stiamo guardando | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 30 | IT | 753 | 113 | 3 | quello a cui stiamo guardando | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 31 | IT | 754 | 113 | 4 | quello a cui stiamo guardando | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 32 | IT | 789 | 119 | 3 | vanno di moda | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 33 | IT | 790 | 119 | 4 | vanno di moda | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 34 | IT | 792 | 119 | 6 | vanno di moda | brief-only | 23 | 3 | expression-study-activity | render-on-owner |
| 35 | IT | 756 | 113 | 6 | quello a cui stiamo guardando | brief-only | 23 | 2 | expression-study-activity | render-on-owner |
| 36 | IT | 791 | 119 | 5 | vanno di moda | brief-only | 23 | 2 | expression-study-activity | render-on-owner |
| 37 | IT | 1999 | 355 | 1 | bottino di guerra | brief-only | 22 | 6 | expression-study-activity | render-on-owner |
| 38 | IT | 2001 | 355 | 3 | bottino di guerra | brief-only | 22 | 5 | expression-study-activity | render-on-owner |
| 39 | IT | 2003 | 355 | 5 | bottino di guerra | brief-only | 22 | 4 | expression-study-activity | render-on-owner |
| 40 | IT | 2000 | 355 | 2 | bottino di guerra | brief-only | 22 | 3 | expression-study-activity | render-on-owner |
| 41 | IT | 2002 | 355 | 4 | bottino di guerra | brief-only | 22 | 2 | expression-study-activity | render-on-owner |
| 42 | IT | 2004 | 355 | 6 | bottino di guerra | brief-only | 22 | 2 | expression-study-activity | render-on-owner |
| 43 | IT | 714 | 106 | 6 | non smise mai di crederci | brief-only | 20 | 5 | expression-study-activity | render-on-owner |
| 44 | IT | 2035 | 361 | 1 | calarsi dentro | brief-only | 20 | 5 | expression-study-activity | render-on-owner |
| 45 | IT | 709 | 106 | 1 | non smise mai di crederci | brief-only | 20 | 4 | expression-study-activity | render-on-owner |
| 46 | IT | 2036 | 361 | 2 | calarsi dentro | brief-only | 20 | 4 | expression-study-activity | render-on-owner |
| 47 | IT | 710 | 106 | 2 | non smise mai di crederci | brief-only | 20 | 3 | expression-study-activity | render-on-owner |
| 48 | IT | 711 | 106 | 3 | non smise mai di crederci | brief-only | 20 | 3 | expression-study-activity | render-on-owner |
| 49 | IT | 713 | 106 | 5 | non smise mai di crederci | brief-only | 20 | 3 | expression-study-activity | render-on-owner |
| 50 | IT | 2037 | 361 | 3 | calarsi dentro | brief-only | 20 | 3 | expression-study-activity | render-on-owner |

## Study-activity join

Weights use only `reps` from C2 rows whose verdict is `adoptable`. The join is exact and bilingual under the normalizer that produced C2: strip sound/HTML, HTML-unescape, NFKC, stabilize the defined quote/dash variants, collapse whitespace, and case-fold while preserving accents and punctuation. A key must be unique on both sides.

| Language | Adoptable cards / reps | Uniquely joined cards / reps | Unmatched cards / reps | Ambiguous cards / reps |
|---|---:|---:|---:|---:|
| DE | 513 / 1,486 | 1 / 1 | 512 / 1,485 | 0 / 0 |
| ES | 434 / 1,024 | 1 / 1 | 433 / 1,023 | 0 / 0 |
| FR | 746 / 2,329 | 0 / 0 | 746 / 2,329 | 0 / 0 |
| IT | 1,467 / 6,250 | 622 / 1,267 | 844 / 4,982 | 1 / 1 |
| PT | 809 / 3,445 | 179 / 350 | 630 / 3,095 | 0 / 0 |
| **Total** | **3,969 / 14,534** | **803 / 1,619** | **3,165 / 12,914** | **1 / 1** |

There are 137 expressions with positive defensible weight. Seven duplicated bilingual keys cover 14 server examples; only one adoptable card carries activity in those collisions (1 rep), and that rep is not assigned. Four further adoptable cards carrying 8 reps would match only after restoring clipped server text; those reps also remain unassigned.

## Methodology

- **ID boundary.** The extract contains 18,258 example rows and every `example_id` is null. For the 3,014 expressions already in the authored campaign, the output variation at the same unique `(lang, expression_id, ord)` supplies 18,084 numeric IDs. The sibling input records validate every position: 17,976 bilingual pairs are exact and 108 are strict prefixes where one or both server fields stop at 120 characters. The 174 examples in 29 new Spanish expressions have no brief and no recoverable numeric ID; the JSON preserves each under a unique composite locator and excludes it from the numeric priority queue.
- **Render discovery.** Canonical images are flat `ex_<example_id>.jpg` files: 519 in `/srv/ai-models/outputs/factory/corpus_images` and 537 in `/srv/ai-models/outputs/factory/qa_mirror/mac_corpus` for this snapshot. Each listed file was statted before and after hashing. Mac-owned examples without a local mirror are `remote-unverified`; `hold-es-first` is not Mac ownership, so absent held renders are `brief-only`.
- **QA authority.** The local ledger has 399 rows. Current content matches 222 pass and 169 fail rows; 8 rendered examples have only stale-hash history. A pass can ship only when its ledger SHA-1 equals current local bytes. The commissioned human-override file is absent locally; 0 overrides were applied.
- **Pass rate.** The table reports effective current-hash passes divided by current-hash pass-or-fail verdicts. Pending images, remote-unverified rows, brief-only rows, and no-brief rows are excluded from that quality denominator; QA-passed coverage is separately measured against every language example.
- **Priority.** Every resolved example lacking a current effective pass is ordered first by positive unambiguous expression-level adoptable reps, then example-level reps. Ties and every ambiguous/unmatched/zero-weight case use lower language QA-passed coverage, then larger uncovered count, followed by stable language/expression/ord/ID keys. The JSON contains the full ordered ID list and the rank/basis/action on each example ledger row.

## Anomalies

- All 18,258 server example IDs are null; 18,084 are positionally recoverable from authored output and 174 are not.
- 108 server rows have clipped bilingual text. Strict C2 joining intentionally leaves 4 otherwise diagnostic matches (8 reps) unweighted.
- `/srv/ai-models/outputs/factory/qa_mirror/human_overrides.jsonl` is absent. The Fedora sync script does not mirror that file, so this report applies zero overrides but cannot assert that the remote Mac has none.
- 8 current files have only historical verdicts for another SHA-1 and remain pending: 2509, 2510, 2511, 2512, 2513, 2514, 2517, 2518.
- 72 local renders belong to chunks now marked `hold-es-first`; they remain ordinary local rendered assets.
- The server contains 1 zero-example idiom: PT expression 2756 (prestou um depoimento).
- Canonical-pool integrity at the captured boundary: 0 IDs in both pools, 0 render IDs outside authored briefs, 0 noncanonical files ignored, and 0 malformed QA rows.

## Summary

DE has 0 qa-passed, 72 rendered-unjudged, 4,038 brief-only, 0 no-brief, 0 remote-unverified; ES has 222 qa-passed, 762 rendered-unjudged, 681 brief-only, 174 no-brief, 1,047 remote-unverified; FR has 0 qa-passed, 0 rendered-unjudged, 2,892 brief-only, 0 no-brief, 0 remote-unverified; IT has 0 qa-passed, 0 rendered-unjudged, 4,974 brief-only, 0 no-brief, 0 remote-unverified; PT has 0 qa-passed, 0 rendered-unjudged, 3,396 brief-only, 0 no-brief, 0 remote-unverified. Across all languages, the Hub has 222 current-hash QA-passed images available to ship today.
