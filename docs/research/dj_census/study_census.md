# DJ-C1 study telemetry census

Deterministic, read-only census of the live Anki collection. The machine-readable companion is `study_census.json`.

## Methods

- Source: `docs/research/anki_reorg_work/live_cutover_20260807T072826Z/collection.anki2`; 62,554 revlog rows, 62,407 joinable to current cards, and 147 orphaned rows excluded from card metrics.
- Local calendar/time-of-day zone: `Asia/Singapore`. The observed revlog endpoint is `2026-08-07T09:21:22.407000+08:00`; the 90-day window is `2026-05-10` through `2026-08-07`, and the 60-day mix window is `2026-06-09` through `2026-08-07`.
- Deck paths use Anki's current `\x1f` separator (the brief's `::` notation is equivalent). Numbered estate lanes map to populations; explicit podcast tags map a recognized language root to `lessons`. Unknown roots and recognized roots without an estate lane are `other`; tags are not used to infer a language.
- Revlog `time` is milliseconds. Planning stats use `min(time, 60000)`; 791 of 62,407 joinable reps (1.2675%) are at the 60-second censoring boundary, while 0 exceed it. A cell with fewer than 30 reps falls back to the global population median, then the global median.
- Sessions are clusters where the gap between consecutive revlog timestamps is at most 30.0 minutes. Active seconds are capped per rep; elapsed session seconds are first-to-last timestamp plus the final capped rep time.
- Maturity is event-based: learning/relearning/filtered from revlog type; review cards are young at `ivl <= 21` days and mature at `ivl > 21` days. Ratings are raw counts and percentages only; no weakness weighting is proposed.
- Historical `_tenses_old`/legacy material was consulted only as context and is not merged into the current-account counts.

## Source and mapping audit

| Metric | Count |
| --- | --- |
| Current cards | 83,436 |
| Current notes | 75,471 |
| Deck rows | 529 |
| All revlog rows | 62,554 |
| Joinable revlog rows used | 62,407 |
| Orphaned revlog rows excluded | 147 |

### Current-card mapping

| Reason | Cards | Revlog reps |
| --- | --- | --- |
| estate_lane | 57,274 | 29,510 |
| outside_estate_lane | 1,540 | 28,505 |
| podcast_tag | 2,611 | 275 |
| unknown_root | 22,011 | 4,117 |

### Mapped language/population cells

| Language | Population | Cards | Revlog reps |
| --- | --- | --- | --- |
| DE German | Expressions | 4,514 | 1,937 |
| DE German | Grammar | 81 | 0 |
| DE German | Tenses | 36 | 0 |
| DE German | Exercises | 684 | 0 |
| DE German | Translation | 79 | 0 |
| DE German | My Errors | 20 | 0 |
| DE German | Rescue | 2 | 5 |
| DE German | Pimsleur | 5,311 | 11 |
| DE German | lessons | 10 | 0 |
| ES Spanish | Expressions | 3,193 | 1,024 |
| ES Spanish | Grammar | 268 | 7 |
| ES Spanish | Tenses | 36 | 0 |
| ES Spanish | Exercises | 750 | 6 |
| ES Spanish | Translation | 250 | 0 |
| ES Spanish | My Errors | 20 | 0 |
| ES Spanish | Rescue | 4 | 15 |
| ES Spanish | Pimsleur | 8,429 | 1 |
| ES Spanish | lessons | 5 | 0 |
| FR French | Expressions | 3,488 | 2,329 |
| FR French | Grammar | 165 | 122 |
| FR French | Tenses | 36 | 0 |
| FR French | Exercises | 706 | 1 |
| FR French | Translation | 146 | 0 |
| FR French | My Errors | 20 | 0 |
| FR French | Pimsleur | 4,693 | 0 |
| FR French | lessons | 10 | 6 |
| IT Italian | Expressions | 5,730 | 6,262 |
| IT Italian | Grammar | 145 | 95 |
| IT Italian | Tenses | 34 | 26 |
| IT Italian | Exercises | 734 | 0 |
| IT Italian | Translation | 130 | 0 |
| IT Italian | My Errors | 11 | 18 |
| IT Italian | Rescue | 1 | 2 |
| IT Italian | Pimsleur | 5,344 | 1,892 |
| IT Italian | lessons | 10 | 0 |
| PT Portuguese | Expressions | 3,834 | 3,445 |
| PT Portuguese | Grammar | 145 | 0 |
| PT Portuguese | Tenses | 28 | 22 |
| PT Portuguese | Exercises | 670 | 0 |
| PT Portuguese | Translation | 127 | 0 |
| PT Portuguese | My Errors | 20 | 0 |
| PT Portuguese | Rescue | 3 | 9 |
| PT Portuguese | Pimsleur | 4,344 | 9 |
| PT Portuguese | lessons | 5 | 0 |
| ZH Mandarin | Pimsleur | 3,043 | 12,272 |
| ZH Mandarin | lessons | 2,571 | 269 |
| ZH Mandarin | other | 1,540 | 28,505 |
| other | other | 22,011 | 4,117 |

## Seconds per rep

| Language | Population | Cards | Reps | Capped p25 s | Capped median s | Capped p75 s | Planning constant | At 60s cap | Raw median s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DE German | Expressions | 4,514 | 1,937 | 6.384 | 7.540 | 9.368 | 7.540 (cell_median) | 17 (0.8776%) | 7.540 |
| DE German | Grammar | 81 | 0 | — | — | — | 7.783 (global_population_median) | 0 (0%) | — |
| DE German | Tenses | 36 | 0 | — | — | — | 8.012 (global_population_median) | 0 (0%) | — |
| DE German | Exercises | 684 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| DE German | Translation | 79 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| DE German | My Errors | 20 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| DE German | Rescue | 2 | 5 | 4.133 | 11.063 | 18.683 | 6.606 (global_population_median) | 0 (0.0%) | 11.063 |
| DE German | Pimsleur | 5,311 | 11 | 4.493 | 6.814 | 9.033 | 6.489 (global_population_median) | 1 (9.0909%) | 6.814 |
| DE German | lessons | 10 | 0 | — | — | — | 7.573 (global_population_median) | 0 (0%) | — |
| ES Spanish | Expressions | 3,193 | 1,024 | 7.550 | 9.448 | 12.109 | 9.448 (cell_median) | 16 (1.5625%) | 9.448 |
| ES Spanish | Grammar | 268 | 7 | 12.434 | 15.560 | 18.773 | 7.783 (global_population_median) | 0 (0.0%) | 15.560 |
| ES Spanish | Tenses | 36 | 0 | — | — | — | 8.012 (global_population_median) | 0 (0%) | — |
| ES Spanish | Exercises | 750 | 6 | 12.248 | 13.406 | 15.323 | 5.359 (global_median) | 0 (0.0%) | 13.406 |
| ES Spanish | Translation | 250 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| ES Spanish | My Errors | 20 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| ES Spanish | Rescue | 4 | 15 | 3.962 | 6.148 | 9.899 | 6.606 (global_population_median) | 1 (6.6667%) | 6.148 |
| ES Spanish | Pimsleur | 8,429 | 1 | 13.733 | 13.733 | 13.733 | 6.489 (global_population_median) | 0 (0.0%) | 13.733 |
| ES Spanish | lessons | 5 | 0 | — | — | — | 7.573 (global_population_median) | 0 (0%) | — |
| FR French | Expressions | 3,488 | 2,329 | 5.691 | 6.579 | 7.903 | 6.579 (cell_median) | 12 (0.5152%) | 6.579 |
| FR French | Grammar | 165 | 122 | 6.221 | 7.700 | 9.452 | 7.700 (cell_median) | 1 (0.8197%) | 7.700 |
| FR French | Tenses | 36 | 0 | — | — | — | 8.012 (global_population_median) | 0 (0%) | — |
| FR French | Exercises | 706 | 1 | 12.104 | 12.104 | 12.104 | 5.359 (global_median) | 0 (0.0%) | 12.104 |
| FR French | Translation | 146 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| FR French | My Errors | 20 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| FR French | Pimsleur | 4,693 | 0 | — | — | — | 6.489 (global_population_median) | 0 (0%) | — |
| FR French | lessons | 10 | 6 | 59.893 | 60.000 | 60.000 | 7.573 (global_population_median) | 4 (66.6667%) | 60.000 |
| IT Italian | Expressions | 5,730 | 6,262 | 7.173 | 9.264 | 12.710 | 9.264 (cell_median) | 46 (0.7346%) | 9.264 |
| IT Italian | Grammar | 145 | 95 | 6.213 | 7.717 | 11.877 | 7.717 (cell_median) | 1 (1.0526%) | 7.717 |
| IT Italian | Tenses | 34 | 26 | 7.277 | 8.923 | 13.031 | 8.012 (global_population_median) | 0 (0.0%) | 8.923 |
| IT Italian | Exercises | 734 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| IT Italian | Translation | 130 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| IT Italian | My Errors | 11 | 18 | 3.189 | 4.463 | 5.656 | 5.359 (global_median) | 0 (0.0%) | 4.463 |
| IT Italian | Rescue | 1 | 2 | 2.789 | 4.200 | 5.611 | 6.606 (global_population_median) | 0 (0.0%) | 4.200 |
| IT Italian | Pimsleur | 5,344 | 1,892 | 4.599 | 5.659 | 7.271 | 5.659 (cell_median) | 10 (0.5285%) | 5.659 |
| IT Italian | lessons | 10 | 0 | — | — | — | 7.573 (global_population_median) | 0 (0%) | — |
| PT Portuguese | Expressions | 3,834 | 3,445 | 6.678 | 9.256 | 12.457 | 9.256 (cell_median) | 52 (1.5094%) | 9.256 |
| PT Portuguese | Grammar | 145 | 0 | — | — | — | 7.783 (global_population_median) | 0 (0%) | — |
| PT Portuguese | Tenses | 28 | 22 | 5.761 | 7.123 | 9.962 | 8.012 (global_population_median) | 0 (0.0%) | 7.123 |
| PT Portuguese | Exercises | 670 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| PT Portuguese | Translation | 127 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| PT Portuguese | My Errors | 20 | 0 | — | — | — | 5.359 (global_median) | 0 (0%) | — |
| PT Portuguese | Rescue | 3 | 9 | 5.718 | 7.771 | 14.746 | 6.606 (global_population_median) | 0 (0.0%) | 7.771 |
| PT Portuguese | Pimsleur | 4,344 | 9 | 3.360 | 4.448 | 5.360 | 6.489 (global_population_median) | 0 (0.0%) | 4.448 |
| PT Portuguese | lessons | 5 | 0 | — | — | — | 7.573 (global_population_median) | 0 (0%) | — |
| ZH Mandarin | Pimsleur | 3,043 | 12,272 | 5.091 | 6.659 | 8.943 | 6.659 (cell_median) | 137 (1.1164%) | 6.659 |
| ZH Mandarin | lessons | 2,571 | 269 | 4.894 | 7.531 | 10.872 | 7.531 (cell_median) | 1 (0.3717%) | 7.531 |
| ZH Mandarin | other | 1,540 | 28,505 | 2.260 | 3.015 | 4.584 | 3.015 (cell_median) | 161 (0.5648%) | 3.015 |
| other | other | 22,011 | 4,117 | 3.911 | 5.594 | 9.857 | 5.594 (cell_median) | 331 (8.0398%) | 5.594 |

### Global fallback table

| Population | Reps | Capped p25 s | Capped median s | Capped p75 s | Fallback constant s |
| --- | --- | --- | --- | --- | --- |
| Expressions | 14,997 | 6.530 | 8.445 | 11.504 | 8.445 (global_population_median) |
| Grammar | 224 | 6.244 | 7.783 | 10.504 | 7.783 (global_population_median) |
| Tenses | 48 | 6.292 | 8.012 | 11.513 | 8.012 (global_population_median) |
| Exercises | 7 | 11.995 | 13.330 | 14.710 | 5.359 (global_median) |
| My Errors | 18 | 3.189 | 4.463 | 5.656 | 5.359 (global_median) |
| Rescue | 31 | 4.051 | 6.606 | 11.897 | 6.606 (global_population_median) |
| Pimsleur | 14,185 | 4.998 | 6.489 | 8.711 | 6.489 (global_population_median) |
| lessons | 275 | 5.005 | 7.573 | 11.005 | 7.573 (global_population_median) |
| other | 32,622 | 2.328 | 3.220 | 5.143 | 3.220 (global_population_median) |
| all | 62,407 | 3.077 | 5.359 | 8.303 | 5.359 (global_median) |

## Session anatomy (last 90 calendar days)

| Measure | Value |
| --- | --- |
| Calendar days | 90 |
| Study days | 66 |
| Sessions | 134 |
| Mean sessions / calendar day | 1.4889 |
| Mean sessions / study day | 2.0303 |
| Active minutes / calendar day | n=90; p25=0 min; median=56.0075 min; p75=93.6573 min; mean=59.4158 min; max=206.089 min |
| Elapsed minutes / calendar day | n=90; p25=0 min; median=65.4465 min; p75=113.4443 min; mean=74.7835 min; max=289.548 min |
| One-language sessions | 65 (48.5075%) |
| Mixed-language sessions | 69 (51.4925%) |
| Sessions with an actual language transition | 69 (51.4925%) |
| Active session length | n=134; p25=643.3985 s; median=2530.767 s; p75=3429.9052 s; mean=2394.3686 s; max=11949.1 s |
| Elapsed session length | n=134; p25=1292.7865 s; median=3263.1055 s; p75=3897.2312 s; mean=3013.6629 s; max=15170.421 s |

### Sessions by language count

| Languages in session | Sessions |
| --- | --- |
| 1 | 65 |
| 2 | 30 |
| 3 | 33 |
| 4 | 5 |
| 5 | 1 |

### Active session-length histogram

| Active length | Sessions |
| --- | --- |
| 0-15_min | 37 |
| 15-30_min | 12 |
| 30-60_min | 60 |
| 60-120_min | 22 |
| 120+_min | 3 |

### Observed language transitions

| Transition | Count |
| --- | --- |
| DE German → ES Spanish | 2 |
| DE German → FR French | 4 |
| DE German → PT Portuguese | 1 |
| DE German → ZH Mandarin | 7 |
| DE German → other | 1 |
| ES Spanish → DE German | 3 |
| ES Spanish → IT Italian | 5 |
| ES Spanish → PT Portuguese | 8 |
| ES Spanish → ZH Mandarin | 1 |
| FR French → DE German | 1 |
| FR French → PT Portuguese | 1 |
| FR French → ZH Mandarin | 4 |
| FR French → other | 2 |
| IT Italian → ES Spanish | 7 |
| IT Italian → FR French | 2 |
| IT Italian → PT Portuguese | 22 |
| IT Italian → ZH Mandarin | 11 |
| IT Italian → other | 4 |
| PT Portuguese → DE German | 5 |
| PT Portuguese → ES Spanish | 10 |
| PT Portuguese → IT Italian | 3 |
| PT Portuguese → ZH Mandarin | 4 |
| ZH Mandarin → DE German | 6 |
| ZH Mandarin → ES Spanish | 1 |
| ZH Mandarin → FR French | 1 |
| ZH Mandarin → IT Italian | 17 |
| ZH Mandarin → PT Portuguese | 4 |
| ZH Mandarin → other | 7 |
| other → DE German | 3 |
| other → FR French | 2 |
| other → IT Italian | 3 |
| other → PT Portuguese | 1 |
| other → ZH Mandarin | 3 |

### Time of day (local hour)

| Hour | Session starts | Start active min | Reps | Rep active min |
| --- | --- | --- | --- | --- |
| 00:00 | 0 | 0.0 | 0 | 0.0 |
| 01:00 | 1 | 4.634 | 26 | 4.548 |
| 02:00 | 1 | 44.561 | 376 | 44.646 |
| 03:00 | 0 | 0.0 | 0 | 0.0 |
| 04:00 | 2 | 48.482 | 130 | 48.482 |
| 05:00 | 5 | 35.903 | 134 | 34.963 |
| 06:00 | 5 | 37.715 | 182 | 18.414 |
| 07:00 | 18 | 813.713 | 2751 | 388.427 |
| 08:00 | 16 | 813.442 | 7302 | 848.86 |
| 09:00 | 8 | 421.584 | 3858 | 669.715 |
| 10:00 | 6 | 307.126 | 2340 | 278.52 |
| 11:00 | 0 | 0.0 | 1064 | 136.53 |
| 12:00 | 5 | 166.058 | 1871 | 144.928 |
| 13:00 | 5 | 134.282 | 1426 | 132.627 |
| 14:00 | 6 | 187.806 | 940 | 154.275 |
| 15:00 | 7 | 343.197 | 3162 | 291.0 |
| 16:00 | 3 | 68.184 | 1626 | 155.363 |
| 17:00 | 3 | 82.953 | 2032 | 135.252 |
| 18:00 | 2 | 200.152 | 485 | 37.682 |
| 19:00 | 7 | 315.648 | 1581 | 138.659 |
| 20:00 | 8 | 470.182 | 2884 | 306.346 |
| 21:00 | 19 | 744.164 | 10354 | 960.601 |
| 22:00 | 4 | 96.742 | 2663 | 339.687 |
| 23:00 | 3 | 10.894 | 551 | 77.9 |

### Session inventory

| # | Start | End | Reps | Active min | Elapsed min | Languages | Transitions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-05-10T10:33:26.431000+08:00 | 2026-05-10T12:28:10.599000+08:00 | 595 | 83.114 | 114.939 | ZH Mandarin | 0 |
| 2 | 2026-05-10T19:08:50.130000+08:00 | 2026-05-10T19:11:05.521000+08:00 | 19 | 2.235 | 2.38 | ZH Mandarin | 0 |
| 3 | 2026-05-10T21:37:30.746000+08:00 | 2026-05-10T22:49:06.704000+08:00 | 482 | 61.83 | 71.722 | DE German, IT Italian, other | 2 |
| 4 | 2026-05-11T10:48:40.697000+08:00 | 2026-05-11T12:30:44.202000+08:00 | 738 | 90.292 | 102.173 | DE German, IT Italian, ZH Mandarin | 3 |
| 5 | 2026-05-12T21:18:13.043000+08:00 | 2026-05-12T22:24:49.391000+08:00 | 538 | 61.718 | 66.735 | IT Italian, ZH Mandarin | 2 |
| 6 | 2026-05-12T23:11:10.444000+08:00 | 2026-05-12T23:19:34.550000+08:00 | 70 | 8.329 | 8.505 | DE German | 0 |
| 7 | 2026-05-13T13:10:13.252000+08:00 | 2026-05-13T13:10:26.293000+08:00 | 3 | 0.361 | 0.37 | DE German | 0 |
| 8 | 2026-05-14T14:06:54.677000+08:00 | 2026-05-14T14:07:15.036000+08:00 | 5 | 0.438 | 0.439 | ZH Mandarin | 0 |
| 9 | 2026-05-14T16:23:09.154000+08:00 | 2026-05-14T16:54:09.910000+08:00 | 25 | 2.837 | 31.07 | ZH Mandarin | 0 |
| 10 | 2026-05-14T20:50:47.989000+08:00 | 2026-05-14T23:05:32.916000+08:00 | 933 | 115.851 | 134.877 | IT Italian, ZH Mandarin, other | 3 |
| 11 | 2026-05-15T05:19:56.511000+08:00 | 2026-05-15T05:33:29.341000+08:00 | 29 | 3.733 | 13.63 | ZH Mandarin | 0 |
| 12 | 2026-05-15T09:51:45.632000+08:00 | 2026-05-15T09:51:45.632000+08:00 | 1 | 0.182 | 0.182 | IT Italian | 0 |
| 13 | 2026-05-15T15:07:38.410000+08:00 | 2026-05-15T15:09:42.013000+08:00 | 27 | 3.021 | 2.176 | ZH Mandarin | 0 |
| 14 | 2026-05-15T18:45:12.647000+08:00 | 2026-05-15T22:57:36.134000+08:00 | 1411 | 199.152 | 252.84 | IT Italian, ZH Mandarin | 1 |
| 15 | 2026-05-16T05:11:10.700000+08:00 | 2026-05-16T05:11:18.873000+08:00 | 3 | 0.291 | 0.197 | ZH Mandarin | 0 |
| 16 | 2026-05-16T06:31:04.077000+08:00 | 2026-05-16T07:02:38.095000+08:00 | 84 | 7.354 | 31.645 | ZH Mandarin | 0 |
| 17 | 2026-05-16T19:32:36.196000+08:00 | 2026-05-16T23:20:57.314000+08:00 | 1581 | 190.214 | 228.557 | FR French, ZH Mandarin, other | 2 |
| 18 | 2026-05-17T06:02:35.672000+08:00 | 2026-05-17T06:55:43.067000+08:00 | 66 | 5.642 | 53.164 | ZH Mandarin | 0 |
| 19 | 2026-05-17T20:12:25.624000+08:00 | 2026-05-17T22:55:30.404000+08:00 | 1072 | 129.142 | 163.202 | FR French, IT Italian, ZH Mandarin | 3 |
| 20 | 2026-05-18T22:56:32.841000+08:00 | 2026-05-18T22:59:01.172000+08:00 | 18 | 2.564 | 2.558 | ZH Mandarin | 0 |
| 21 | 2026-05-19T10:14:41.504000+08:00 | 2026-05-19T12:04:03.117000+08:00 | 630 | 69.475 | 109.441 | ZH Mandarin | 0 |
| 22 | 2026-05-19T17:15:58.581000+08:00 | 2026-05-19T17:16:10.235000+08:00 | 2 | 0.676 | 0.383 | ZH Mandarin | 0 |
| 23 | 2026-05-19T22:41:24.874000+08:00 | 2026-05-19T23:13:02.905000+08:00 | 188 | 29.238 | 31.987 | FR French | 0 |
| 24 | 2026-05-21T10:40:11.639000+08:00 | 2026-05-21T11:30:27.879000+08:00 | 224 | 31.49 | 50.367 | FR French | 0 |
| 25 | 2026-05-21T12:20:19.263000+08:00 | 2026-05-21T12:26:06.550000+08:00 | 26 | 4.022 | 5.917 | FR French | 0 |
| 26 | 2026-05-22T06:54:25.325000+08:00 | 2026-05-22T07:19:31.087000+08:00 | 189 | 22.973 | 25.184 | ZH Mandarin | 0 |
| 27 | 2026-05-23T07:20:42.389000+08:00 | 2026-05-23T07:32:48.022000+08:00 | 56 | 11.757 | 12.409 | FR French, ZH Mandarin | 1 |
| 28 | 2026-05-23T16:56:40.726000+08:00 | 2026-05-23T17:18:40.203000+08:00 | 119 | 19.909 | 22.404 | ZH Mandarin | 0 |
| 29 | 2026-05-24T08:05:09.912000+08:00 | 2026-05-24T09:34:27.016000+08:00 | 564 | 64.298 | 90.285 | ZH Mandarin | 0 |
| 30 | 2026-05-24T13:13:11.226000+08:00 | 2026-05-24T15:21:20.260000+08:00 | 544 | 75.788 | 128.453 | ZH Mandarin | 0 |
| 31 | 2026-05-25T07:21:53.635000+08:00 | 2026-05-25T07:23:24.225000+08:00 | 8 | 1.409 | 1.667 | IT Italian | 0 |
| 32 | 2026-05-25T09:06:06.578000+08:00 | 2026-05-25T11:01:43.542000+08:00 | 768 | 87.829 | 115.69 | ZH Mandarin | 0 |
| 33 | 2026-05-25T13:43:58.082000+08:00 | 2026-05-25T15:05:58.689000+08:00 | 268 | 29.778 | 82.053 | ZH Mandarin | 0 |
| 34 | 2026-05-25T16:49:25.181000+08:00 | 2026-05-25T18:19:31.370000+08:00 | 459 | 45.437 | 90.138 | ZH Mandarin | 0 |
| 35 | 2026-05-26T07:46:52.635000+08:00 | 2026-05-26T09:06:53.679000+08:00 | 483 | 59.675 | 80.654 | FR French, IT Italian, other | 3 |
| 36 | 2026-05-26T15:13:32.528000+08:00 | 2026-05-26T16:12:34.777000+08:00 | 74 | 51.925 | 60.037 | other | 0 |
| 37 | 2026-05-26T21:04:56.412000+08:00 | 2026-05-26T21:59:45.274000+08:00 | 367 | 49.716 | 55.622 | DE German, ZH Mandarin, other | 4 |
| 38 | 2026-05-27T07:16:56.558000+08:00 | 2026-05-27T08:21:31.193000+08:00 | 467 | 61.83 | 64.664 | ZH Mandarin, other | 1 |
| 39 | 2026-05-27T15:20:43.120000+08:00 | 2026-05-27T16:20:47.733000+08:00 | 756 | 57.305 | 60.151 | ZH Mandarin | 0 |
| 40 | 2026-05-27T21:00:35.262000+08:00 | 2026-05-27T22:00:41.436000+08:00 | 712 | 50.306 | 60.147 | ZH Mandarin, other | 1 |
| 41 | 2026-05-28T07:21:31.004000+08:00 | 2026-05-28T08:44:28.763000+08:00 | 590 | 57.283 | 82.985 | DE German, ZH Mandarin, other | 2 |
| 42 | 2026-05-28T13:29:09.543000+08:00 | 2026-05-28T13:29:14.415000+08:00 | 3 | 0.117 | 0.134 | ZH Mandarin | 0 |
| 43 | 2026-05-28T14:42:59.662000+08:00 | 2026-05-28T14:43:20.221000+08:00 | 5 | 0.403 | 0.444 | ZH Mandarin | 0 |
| 44 | 2026-05-28T15:16:35.976000+08:00 | 2026-05-28T17:22:06.873000+08:00 | 1614 | 114.832 | 125.559 | DE German, ZH Mandarin | 2 |
| 45 | 2026-05-29T07:35:30.721000+08:00 | 2026-05-29T08:40:21.254000+08:00 | 874 | 57.124 | 64.905 | FR French, ZH Mandarin | 1 |
| 46 | 2026-05-29T19:07:41.669000+08:00 | 2026-05-29T20:06:30.826000+08:00 | 878 | 49.023 | 58.868 | ZH Mandarin | 0 |
| 47 | 2026-05-30T21:04:53.953000+08:00 | 2026-05-30T21:56:41.412000+08:00 | 837 | 45.837 | 51.886 | IT Italian, ZH Mandarin | 2 |
| 48 | 2026-05-31T07:51:19.201000+08:00 | 2026-05-31T08:44:29.363000+08:00 | 782 | 45.317 | 53.253 | FR French, IT Italian, ZH Mandarin, other | 3 |
| 49 | 2026-05-31T17:13:02.659000+08:00 | 2026-05-31T18:07:48.816000+08:00 | 898 | 48.584 | 54.815 | IT Italian, ZH Mandarin, other | 3 |
| 50 | 2026-06-01T09:23:22.315000+08:00 | 2026-06-01T10:27:38.020000+08:00 | 631 | 60.239 | 64.339 | IT Italian, PT Portuguese, ZH Mandarin | 5 |
| 51 | 2026-06-01T15:21:19.680000+08:00 | 2026-06-01T16:25:07.343000+08:00 | 910 | 58.907 | 63.83 | PT Portuguese, ZH Mandarin, other | 2 |
| 52 | 2026-06-02T07:46:23.841000+08:00 | 2026-06-02T08:50:07.918000+08:00 | 817 | 52.863 | 63.859 | PT Portuguese, ZH Mandarin | 2 |
| 53 | 2026-06-03T08:18:53.868000+08:00 | 2026-06-03T09:20:33.066000+08:00 | 892 | 56.32 | 61.724 | IT Italian, PT Portuguese, ZH Mandarin | 4 |
| 54 | 2026-06-04T17:19:12.783000+08:00 | 2026-06-04T17:55:13.352000+08:00 | 700 | 33.694 | 36.04 | ZH Mandarin | 0 |
| 55 | 2026-06-05T19:04:42.287000+08:00 | 2026-06-05T19:16:31.644000+08:00 | 85 | 9.596 | 11.958 | ZH Mandarin | 0 |
| 56 | 2026-06-06T02:00:45.374000+08:00 | 2026-06-06T02:56:15.880000+08:00 | 374 | 44.561 | 55.576 | ZH Mandarin | 0 |
| 57 | 2026-06-06T12:10:47.240000+08:00 | 2026-06-06T13:30:55.299000+08:00 | 956 | 73.387 | 80.217 | ZH Mandarin | 0 |
| 58 | 2026-06-07T12:22:59.860000+08:00 | 2026-06-07T13:02:25.605000+08:00 | 664 | 37.957 | 39.47 | ZH Mandarin | 0 |
| 59 | 2026-06-08T12:58:01.156000+08:00 | 2026-06-08T13:48:28.302000+08:00 | 751 | 46.529 | 51.452 | ZH Mandarin | 0 |
| 60 | 2026-06-09T19:14:58.111000+08:00 | 2026-06-09T19:37:52.058000+08:00 | 273 | 21.453 | 22.953 | ZH Mandarin | 0 |
| 61 | 2026-06-09T22:21:34.337000+08:00 | 2026-06-09T23:33:47.170000+08:00 | 398 | 64.194 | 72.499 | DE German | 0 |
| 62 | 2026-06-10T20:08:43.253000+08:00 | 2026-06-10T21:06:14.988000+08:00 | 927 | 52.418 | 57.561 | PT Portuguese, ZH Mandarin | 1 |
| 63 | 2026-06-13T23:40:23.030000+08:00 | 2026-06-13T23:59:24.668000+08:00 | 32 | 1.713 | 19.066 | ZH Mandarin | 0 |
| 64 | 2026-06-14T08:46:32.562000+08:00 | 2026-06-14T09:47:34.981000+08:00 | 512 | 57.371 | 61.099 | DE German, ZH Mandarin | 1 |
| 65 | 2026-06-14T20:55:59.742000+08:00 | 2026-06-14T21:36:54.823000+08:00 | 605 | 38.577 | 41.058 | DE German, PT Portuguese, ZH Mandarin | 2 |
| 66 | 2026-06-15T20:30:39.092000+08:00 | 2026-06-15T21:28:45.396000+08:00 | 365 | 55.082 | 58.26 | IT Italian, PT Portuguese, ZH Mandarin | 2 |
| 67 | 2026-06-16T07:23:26.282000+08:00 | 2026-06-16T07:41:19.411000+08:00 | 190 | 17.206 | 17.935 | IT Italian, PT Portuguese, ZH Mandarin | 2 |
| 68 | 2026-06-16T19:58:58.990000+08:00 | 2026-06-16T20:52:51.837000+08:00 | 505 | 42.833 | 53.955 | IT Italian, ZH Mandarin | 1 |
| 69 | 2026-06-20T20:32:23.083000+08:00 | 2026-06-20T20:32:23.083000+08:00 | 1 | 0.125 | 0.125 | ZH Mandarin | 0 |
| 70 | 2026-06-20T21:04:47.886000+08:00 | 2026-06-20T21:59:40.829000+08:00 | 137 | 42.57 | 55.366 | ZH Mandarin, other | 1 |
| 71 | 2026-06-22T07:07:55.458000+08:00 | 2026-06-22T08:12:47.036000+08:00 | 319 | 62.506 | 64.952 | IT Italian | 0 |
| 72 | 2026-06-22T14:41:00.886000+08:00 | 2026-06-22T15:45:41.182000+08:00 | 652 | 57.049 | 64.954 | IT Italian, ZH Mandarin | 1 |
| 73 | 2026-06-23T07:07:27.536000+08:00 | 2026-06-23T08:09:34.044000+08:00 | 278 | 51.865 | 62.283 | IT Italian | 0 |
| 74 | 2026-06-23T14:54:09.432000+08:00 | 2026-06-23T15:51:15.684000+08:00 | 423 | 37.855 | 57.151 | FR French, IT Italian, ZH Mandarin | 3 |
| 75 | 2026-06-24T21:10:25.280000+08:00 | 2026-06-24T22:00:06.220000+08:00 | 420 | 47.456 | 49.825 | IT Italian, PT Portuguese, ZH Mandarin | 2 |
| 76 | 2026-06-25T04:12:08.867000+08:00 | 2026-06-25T04:49:37.569000+08:00 | 86 | 31.227 | 37.745 | ZH Mandarin | 0 |
| 77 | 2026-06-25T05:41:55.183000+08:00 | 2026-06-25T05:57:13.696000+08:00 | 47 | 14.918 | 15.576 | ZH Mandarin | 0 |
| 78 | 2026-06-25T08:35:08.771000+08:00 | 2026-06-25T09:38:17.515000+08:00 | 146 | 35.693 | 63.389 | IT Italian | 0 |
| 79 | 2026-06-26T05:47:37.026000+08:00 | 2026-06-26T06:20:38.991000+08:00 | 28 | 10.379 | 33.314 | ZH Mandarin | 0 |
| 80 | 2026-06-26T09:13:21.724000+08:00 | 2026-06-26T10:21:00.381000+08:00 | 177 | 48.853 | 67.75 | IT Italian, PT Portuguese | 1 |
| 81 | 2026-06-28T13:38:39.978000+08:00 | 2026-06-28T14:12:46.102000+08:00 | 148 | 28.239 | 34.161 | IT Italian, PT Portuguese, ZH Mandarin | 2 |
| 82 | 2026-06-28T21:13:24.350000+08:00 | 2026-06-28T22:00:33.466000+08:00 | 410 | 27.456 | 47.21 | ZH Mandarin | 0 |
| 83 | 2026-06-29T06:51:53.761000+08:00 | 2026-06-29T06:54:44.621000+08:00 | 29 | 1.296 | 2.888 | ZH Mandarin | 0 |
| 84 | 2026-06-29T08:12:09.058000+08:00 | 2026-06-29T08:20:28.868000+08:00 | 105 | 5.907 | 8.376 | ZH Mandarin | 0 |
| 85 | 2026-06-29T08:51:50.304000+08:00 | 2026-06-29T09:52:03.851000+08:00 | 181 | 45.299 | 60.342 | IT Italian, PT Portuguese | 1 |
| 86 | 2026-07-02T04:16:05.707000+08:00 | 2026-07-02T04:44:10.301000+08:00 | 44 | 17.255 | 28.439 | ZH Mandarin | 0 |
| 87 | 2026-07-02T05:27:26.237000+08:00 | 2026-07-02T05:34:26.525000+08:00 | 30 | 6.582 | 7.061 | ZH Mandarin | 0 |
| 88 | 2026-07-02T08:16:12.995000+08:00 | 2026-07-02T09:20:56.036000+08:00 | 257 | 54.96 | 64.801 | IT Italian, PT Portuguese | 1 |
| 89 | 2026-07-05T14:02:28.886000+08:00 | 2026-07-05T14:51:58.437000+08:00 | 173 | 34.174 | 49.752 | IT Italian | 0 |
| 90 | 2026-07-06T10:10:58.382000+08:00 | 2026-07-06T11:11:26.281000+08:00 | 586 | 30.346 | 60.532 | IT Italian, ZH Mandarin | 1 |
| 91 | 2026-07-12T06:36:23.452000+08:00 | 2026-07-12T06:36:23.452000+08:00 | 1 | 0.451 | 0.451 | other | 0 |
| 92 | 2026-07-12T08:49:37.467000+08:00 | 2026-07-12T09:51:18.997000+08:00 | 350 | 61.066 | 61.856 | IT Italian, PT Portuguese | 1 |
| 93 | 2026-07-19T07:45:37.307000+08:00 | 2026-07-19T09:02:31.844000+08:00 | 266 | 52.643 | 77.104 | IT Italian, PT Portuguese, ZH Mandarin | 2 |
| 94 | 2026-07-19T19:45:35.034000+08:00 | 2026-07-19T19:46:15.123000+08:00 | 2 | 0.294 | 0.792 | DE German, other | 1 |
| 95 | 2026-07-19T21:06:33.595000+08:00 | 2026-07-19T21:43:12.382000+08:00 | 541 | 27.445 | 36.676 | ZH Mandarin | 0 |
| 96 | 2026-07-20T09:26:16.241000+08:00 | 2026-07-20T10:30:26.795000+08:00 | 219 | 57.179 | 64.34 | IT Italian | 0 |
| 97 | 2026-07-20T21:13:41.212000+08:00 | 2026-07-20T21:34:44.264000+08:00 | 110 | 21.097 | 21.261 | PT Portuguese | 0 |
| 98 | 2026-07-21T07:09:36.226000+08:00 | 2026-07-21T08:11:08.141000+08:00 | 268 | 52.882 | 61.657 | IT Italian, PT Portuguese | 2 |
| 99 | 2026-07-23T07:27:20.112000+08:00 | 2026-07-23T08:13:07.353000+08:00 | 414 | 41.039 | 45.85 | IT Italian, ZH Mandarin | 1 |
| 100 | 2026-07-23T15:34:15.195000+08:00 | 2026-07-23T16:36:15.684000+08:00 | 492 | 57.005 | 62.104 | IT Italian, PT Portuguese, ZH Mandarin | 2 |
| 101 | 2026-07-24T07:40:15.230000+08:00 | 2026-07-24T08:47:41.601000+08:00 | 653 | 65.644 | 67.483 | IT Italian, PT Portuguese, ZH Mandarin | 3 |
| 102 | 2026-07-25T08:48:05.417000+08:00 | 2026-07-25T09:54:54.840000+08:00 | 233 | 59.86 | 67.034 | IT Italian, PT Portuguese | 1 |
| 103 | 2026-07-26T09:12:21.026000+08:00 | 2026-07-26T10:18:20.702000+08:00 | 259 | 63.04 | 66.526 | IT Italian, PT Portuguese | 1 |
| 104 | 2026-07-26T21:25:37.565000+08:00 | 2026-07-26T21:58:36.277000+08:00 | 588 | 32.889 | 33.29 | ZH Mandarin | 0 |
| 105 | 2026-07-27T10:44:24.316000+08:00 | 2026-07-27T10:47:34.960000+08:00 | 7 | 2.41 | 3.39 | other | 0 |
| 106 | 2026-07-27T14:24:49.954000+08:00 | 2026-07-27T15:35:16.576000+08:00 | 232 | 57.888 | 70.822 | IT Italian, PT Portuguese | 1 |
| 107 | 2026-07-27T20:50:35.962000+08:00 | 2026-07-27T21:48:02.432000+08:00 | 333 | 37.199 | 57.473 | ES Spanish, ZH Mandarin | 1 |
| 108 | 2026-07-28T08:11:58.526000+08:00 | 2026-07-28T09:20:11.061000+08:00 | 356 | 59.612 | 68.351 | ES Spanish, IT Italian, PT Portuguese, other | 4 |
| 109 | 2026-07-28T20:07:37.583000+08:00 | 2026-07-28T20:55:09.104000+08:00 | 198 | 41.789 | 47.891 | DE German, PT Portuguese | 1 |
| 110 | 2026-07-28T22:34:07.993000+08:00 | 2026-07-28T22:34:31.791000+08:00 | 2 | 0.746 | 0.793 | ES Spanish | 0 |
| 111 | 2026-07-28T23:55:56.717000+08:00 | 2026-07-28T23:56:36.093000+08:00 | 4 | 0.852 | 0.932 | ES Spanish | 0 |
| 112 | 2026-07-29T07:27:16.372000+08:00 | 2026-07-29T08:33:45.930000+08:00 | 307 | 61.052 | 66.611 | ES Spanish, IT Italian, PT Portuguese | 2 |
| 113 | 2026-07-29T21:46:39.197000+08:00 | 2026-07-29T22:00:04.338000+08:00 | 92 | 13.375 | 13.536 | DE German, PT Portuguese | 1 |
| 114 | 2026-07-30T08:30:04.855000+08:00 | 2026-07-30T09:32:25.062000+08:00 | 255 | 54.635 | 62.429 | ES Spanish, IT Italian, PT Portuguese | 2 |
| 115 | 2026-07-30T21:19:14.534000+08:00 | 2026-07-30T22:00:27.315000+08:00 | 665 | 38.291 | 41.252 | DE German, ZH Mandarin | 1 |
| 116 | 2026-07-31T08:15:46.131000+08:00 | 2026-07-31T09:24:16.313000+08:00 | 360 | 65.39 | 68.666 | ES Spanish, IT Italian, PT Portuguese | 2 |
| 117 | 2026-08-01T07:56:14.766000+08:00 | 2026-08-01T09:03:05.305000+08:00 | 351 | 61.156 | 66.99 | ES Spanish, IT Italian, PT Portuguese | 2 |
| 118 | 2026-08-01T21:12:13.003000+08:00 | 2026-08-01T22:00:03.014000+08:00 | 346 | 46.242 | 48.02 | DE German, FR French | 2 |
| 119 | 2026-08-02T09:01:40.235000+08:00 | 2026-08-02T10:06:12.377000+08:00 | 228 | 43.851 | 64.629 | ES Spanish, IT Italian, PT Portuguese | 3 |
| 120 | 2026-08-02T21:02:48.076000+08:00 | 2026-08-02T21:43:12.445000+08:00 | 630 | 35.214 | 40.436 | DE German, PT Portuguese, ZH Mandarin | 2 |
| 121 | 2026-08-03T08:36:19.584000+08:00 | 2026-08-03T09:42:38.093000+08:00 | 165 | 30.134 | 66.348 | IT Italian | 0 |
| 122 | 2026-08-03T12:22:48.787000+08:00 | 2026-08-03T12:27:47.588000+08:00 | 5 | 4.164 | 5.146 | FR French | 0 |
| 123 | 2026-08-03T18:47:05.720000+08:00 | 2026-08-03T18:47:05.720000+08:00 | 1 | 1.0 | 1.0 | FR French | 0 |
| 124 | 2026-08-03T21:22:44.632000+08:00 | 2026-08-03T22:00:10.592000+08:00 | 219 | 33.726 | 37.566 | ES Spanish, FR French, IT Italian, PT Portuguese | 3 |
| 125 | 2026-08-04T08:01:52.997000+08:00 | 2026-08-04T09:12:36.085000+08:00 | 289 | 56.63 | 70.854 | ES Spanish, IT Italian, PT Portuguese | 2 |
| 126 | 2026-08-04T15:56:52.335000+08:00 | 2026-08-04T15:56:52.335000+08:00 | 1 | 0.202 | 0.202 | FR French | 0 |
| 127 | 2026-08-04T21:05:24.080000+08:00 | 2026-08-04T22:00:15.876000+08:00 | 344 | 53.628 | 54.996 | DE German, FR French, PT Portuguese, other | 3 |
| 128 | 2026-08-05T09:24:38.902000+08:00 | 2026-08-05T10:27:32.707000+08:00 | 287 | 60.411 | 63.074 | ES Spanish, IT Italian, PT Portuguese | 2 |
| 129 | 2026-08-05T21:26:33.339000+08:00 | 2026-08-05T22:00:08.478000+08:00 | 129 | 20.222 | 33.814 | DE German, ES Spanish, FR French, IT Italian, ZH Mandarin | 5 |
| 130 | 2026-08-06T08:07:08.605000+08:00 | 2026-08-06T09:15:19.651000+08:00 | 243 | 52.098 | 68.317 | ES Spanish, IT Italian, PT Portuguese | 2 |
| 131 | 2026-08-06T21:12:53.751000+08:00 | 2026-08-06T22:00:18.034000+08:00 | 676 | 35.146 | 47.477 | DE German, FR French, ZH Mandarin | 4 |
| 132 | 2026-08-07T01:32:25.877000+08:00 | 2026-08-07T02:08:06.962000+08:00 | 28 | 4.634 | 35.71 | DE German, ES Spanish, IT Italian, PT Portuguese | 17 |
| 133 | 2026-08-07T07:26:10.374000+08:00 | 2026-08-07T07:26:32.483000+08:00 | 3 | 0.461 | 0.553 | DE German, ES Spanish, PT Portuguese | 2 |
| 134 | 2026-08-07T08:15:22.658000+08:00 | 2026-08-07T09:21:22.407000+08:00 | 237 | 54.17 | 66.104 | ES Spanish, IT Italian, PT Portuguese | 4 |

### Daily session totals

| Date | Sessions | Reps | Active min | Elapsed min |
| --- | --- | --- | --- | --- |
| 2026-05-10 | 3 | 1096 | 147.18 | 189.041 |
| 2026-05-11 | 1 | 738 | 90.292 | 102.173 |
| 2026-05-12 | 2 | 608 | 70.047 | 75.239 |
| 2026-05-13 | 1 | 3 | 0.361 | 0.37 |
| 2026-05-14 | 3 | 963 | 119.126 | 166.386 |
| 2026-05-15 | 4 | 1468 | 206.089 | 268.828 |
| 2026-05-16 | 3 | 1668 | 197.858 | 260.399 |
| 2026-05-17 | 2 | 1138 | 134.784 | 216.367 |
| 2026-05-18 | 1 | 18 | 2.564 | 2.558 |
| 2026-05-19 | 3 | 820 | 99.388 | 141.811 |
| 2026-05-20 | 0 | 0 | 0.0 | 0.0 |
| 2026-05-21 | 2 | 250 | 35.512 | 56.284 |
| 2026-05-22 | 1 | 189 | 22.973 | 25.184 |
| 2026-05-23 | 2 | 175 | 31.666 | 34.812 |
| 2026-05-24 | 2 | 1108 | 140.086 | 218.738 |
| 2026-05-25 | 4 | 1503 | 164.452 | 289.548 |
| 2026-05-26 | 3 | 924 | 161.316 | 196.314 |
| 2026-05-27 | 3 | 1935 | 169.44 | 184.961 |
| 2026-05-28 | 4 | 2212 | 172.634 | 209.122 |
| 2026-05-29 | 2 | 1752 | 106.146 | 123.773 |
| 2026-05-30 | 1 | 837 | 45.837 | 51.886 |
| 2026-05-31 | 2 | 1680 | 93.901 | 108.068 |
| 2026-06-01 | 2 | 1541 | 119.145 | 128.169 |
| 2026-06-02 | 1 | 817 | 52.863 | 63.859 |
| 2026-06-03 | 1 | 892 | 56.32 | 61.724 |
| 2026-06-04 | 1 | 700 | 33.694 | 36.04 |
| 2026-06-05 | 1 | 85 | 9.596 | 11.958 |
| 2026-06-06 | 2 | 1330 | 117.947 | 135.793 |
| 2026-06-07 | 1 | 664 | 37.957 | 39.47 |
| 2026-06-08 | 1 | 751 | 46.529 | 51.452 |
| 2026-06-09 | 2 | 671 | 85.647 | 95.452 |
| 2026-06-10 | 1 | 927 | 52.418 | 57.561 |
| 2026-06-11 | 0 | 0 | 0.0 | 0.0 |
| 2026-06-12 | 0 | 0 | 0.0 | 0.0 |
| 2026-06-13 | 1 | 32 | 1.713 | 19.066 |
| 2026-06-14 | 2 | 1117 | 95.948 | 102.157 |
| 2026-06-15 | 1 | 365 | 55.082 | 58.26 |
| 2026-06-16 | 2 | 695 | 60.039 | 71.89 |
| 2026-06-17 | 0 | 0 | 0.0 | 0.0 |
| 2026-06-18 | 0 | 0 | 0.0 | 0.0 |
| 2026-06-19 | 0 | 0 | 0.0 | 0.0 |
| 2026-06-20 | 2 | 138 | 42.695 | 55.491 |
| 2026-06-21 | 0 | 0 | 0.0 | 0.0 |
| 2026-06-22 | 2 | 971 | 119.555 | 129.907 |
| 2026-06-23 | 2 | 701 | 89.72 | 119.434 |
| 2026-06-24 | 1 | 420 | 47.456 | 49.825 |
| 2026-06-25 | 3 | 279 | 81.838 | 116.71 |
| 2026-06-26 | 2 | 205 | 59.232 | 101.064 |
| 2026-06-27 | 0 | 0 | 0.0 | 0.0 |
| 2026-06-28 | 2 | 558 | 55.695 | 81.37 |
| 2026-06-29 | 3 | 315 | 52.502 | 71.606 |
| 2026-06-30 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-01 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-02 | 3 | 331 | 78.796 | 100.301 |
| 2026-07-03 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-04 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-05 | 1 | 173 | 34.174 | 49.752 |
| 2026-07-06 | 1 | 586 | 30.346 | 60.532 |
| 2026-07-07 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-08 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-09 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-10 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-11 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-12 | 2 | 351 | 61.517 | 62.306 |
| 2026-07-13 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-14 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-15 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-16 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-17 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-18 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-19 | 3 | 809 | 80.382 | 114.572 |
| 2026-07-20 | 2 | 329 | 78.275 | 85.601 |
| 2026-07-21 | 1 | 268 | 52.882 | 61.657 |
| 2026-07-22 | 0 | 0 | 0.0 | 0.0 |
| 2026-07-23 | 2 | 906 | 98.044 | 107.955 |
| 2026-07-24 | 1 | 653 | 65.644 | 67.483 |
| 2026-07-25 | 1 | 233 | 59.86 | 67.034 |
| 2026-07-26 | 2 | 847 | 95.929 | 99.815 |
| 2026-07-27 | 3 | 572 | 97.496 | 131.686 |
| 2026-07-28 | 4 | 560 | 102.999 | 117.968 |
| 2026-07-29 | 2 | 399 | 74.428 | 80.147 |
| 2026-07-30 | 2 | 920 | 92.926 | 103.681 |
| 2026-07-31 | 1 | 360 | 65.39 | 68.666 |
| 2026-08-01 | 2 | 697 | 107.399 | 115.01 |
| 2026-08-02 | 2 | 858 | 79.065 | 105.065 |
| 2026-08-03 | 4 | 390 | 69.024 | 110.061 |
| 2026-08-04 | 3 | 634 | 110.46 | 126.052 |
| 2026-08-05 | 2 | 416 | 80.633 | 96.889 |
| 2026-08-06 | 2 | 919 | 87.244 | 115.794 |
| 2026-08-07 | 3 | 268 | 59.265 | 102.367 |

## Mix history (last 60 calendar days)

### Cell totals and activity coverage

| Language | Population | Cards | Reps | Active min | Active days | Share of reps | Share of active time | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DE German | Expressions | 4,514 | 1,578 | 239.764 | 11/60 | 7.9404% | 9.0079% | rarely_observed |
| DE German | Grammar | 81 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| DE German | Tenses | 36 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| DE German | Exercises | 684 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| DE German | Translation | 79 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| DE German | My Errors | 20 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| DE German | Rescue | 2 | 5 | 0.908 | 1/60 | 0.0252% | 0.0341% | rarely_observed |
| DE German | Pimsleur | 5,311 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| DE German | lessons | 10 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| ES Spanish | Expressions | 3,193 | 1,024 | 193.401 | 12/60 | 5.1527% | 7.266% | rarely_observed |
| ES Spanish | Grammar | 268 | 7 | 1.858 | 2/60 | 0.0352% | 0.0698% | rarely_observed |
| ES Spanish | Tenses | 36 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| ES Spanish | Exercises | 750 | 6 | 1.387 | 1/60 | 0.0302% | 0.0521% | rarely_observed |
| ES Spanish | Translation | 250 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| ES Spanish | My Errors | 20 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| ES Spanish | Rescue | 4 | 15 | 2.495 | 1/60 | 0.0755% | 0.0937% | rarely_observed |
| ES Spanish | Pimsleur | 8,429 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| ES Spanish | lessons | 5 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| FR French | Expressions | 3,488 | 436 | 55.38 | 5/60 | 2.1939% | 2.0806% | rarely_observed |
| FR French | Grammar | 165 | 122 | 17.799 | 1/60 | 0.6139% | 0.6687% | rarely_observed |
| FR French | Tenses | 36 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| FR French | Exercises | 706 | 1 | 0.202 | 1/60 | 0.005% | 0.0076% | rarely_observed |
| FR French | Translation | 146 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| FR French | My Errors | 20 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| FR French | Pimsleur | 4,693 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| FR French | lessons | 10 | 6 | 5.164 | 1/60 | 0.0302% | 0.194% | rarely_observed |
| IT Italian | Expressions | 5,730 | 4,223 | 890.038 | 32/60 | 21.2499% | 33.4384% | observed |
| IT Italian | Grammar | 145 | 95 | 15.591 | 2/60 | 0.478% | 0.5858% | rarely_observed |
| IT Italian | Tenses | 34 | 26 | 4.76 | 1/60 | 0.1308% | 0.1788% | rarely_observed |
| IT Italian | Exercises | 734 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| IT Italian | Translation | 130 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| IT Italian | My Errors | 11 | 18 | 1.378 | 1/60 | 0.0906% | 0.0518% | rarely_observed |
| IT Italian | Rescue | 1 | 2 | 0.14 | 1/60 | 0.0101% | 0.0053% | rarely_observed |
| IT Italian | Pimsleur | 5,344 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| IT Italian | lessons | 10 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| PT Portuguese | Expressions | 3,834 | 3,049 | 587.25 | 29/60 | 15.3424% | 22.0628% | observed |
| PT Portuguese | Grammar | 145 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| PT Portuguese | Tenses | 28 | 22 | 2.903 | 1/60 | 0.1107% | 0.1091% | rarely_observed |
| PT Portuguese | Exercises | 670 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| PT Portuguese | Translation | 127 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| PT Portuguese | My Errors | 20 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| PT Portuguese | Rescue | 3 | 9 | 1.553 | 1/60 | 0.0453% | 0.0583% | rarely_observed |
| PT Portuguese | Pimsleur | 4,344 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| PT Portuguese | lessons | 5 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| ZH Mandarin | Pimsleur | 3,043 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| ZH Mandarin | lessons | 2,571 | 0 | 0.0 | 0/60 | 0.0% | 0.0% | never_observed |
| ZH Mandarin | other | 1,540 | 9,059 | 608.912 | 25/60 | 45.5845% | 22.8766% | observed |
| other | other | 22,011 | 170 | 30.838 | 6/60 | 0.8554% | 1.1586% | rarely_observed |

### Language totals

| Language | Reps | Active min | Mean active min/day | Active-time share |
| --- | --- | --- | --- | --- |
| DE German | 1,583 | 240.672 | 4.011 | 9.042% |
| ES Spanish | 1,052 | 199.141 | 3.319 | 7.4817% |
| FR French | 565 | 78.544 | 1.309 | 2.9509% |
| IT Italian | 4,364 | 911.908 | 15.198 | 34.2601% |
| PT Portuguese | 3,080 | 591.706 | 9.862 | 22.2302% |
| ZH Mandarin | 9,059 | 608.912 | 10.149 | 22.8766% |
| other | 170 | 30.838 | 0.514 | 1.1586% |

### Systematic-starvation candidates

The label is a deterministic coverage flag, not a causal diagnosis: a populated cell with activity on at most 20% of the 60 calendar days.

| Language | Population | Cards | Reps | Active days | Status |
| --- | --- | --- | --- | --- | --- |
| DE German | Expressions | 4514 | 1578 | 11 | rarely_observed |
| DE German | Grammar | 81 | 0 | 0 | never_observed |
| DE German | Tenses | 36 | 0 | 0 | never_observed |
| DE German | Exercises | 684 | 0 | 0 | never_observed |
| DE German | Translation | 79 | 0 | 0 | never_observed |
| DE German | My Errors | 20 | 0 | 0 | never_observed |
| DE German | Rescue | 2 | 5 | 1 | rarely_observed |
| DE German | Pimsleur | 5311 | 0 | 0 | never_observed |
| DE German | lessons | 10 | 0 | 0 | never_observed |
| ES Spanish | Expressions | 3193 | 1024 | 12 | rarely_observed |
| ES Spanish | Grammar | 268 | 7 | 2 | rarely_observed |
| ES Spanish | Tenses | 36 | 0 | 0 | never_observed |
| ES Spanish | Exercises | 750 | 6 | 1 | rarely_observed |
| ES Spanish | Translation | 250 | 0 | 0 | never_observed |
| ES Spanish | My Errors | 20 | 0 | 0 | never_observed |
| ES Spanish | Rescue | 4 | 15 | 1 | rarely_observed |
| ES Spanish | Pimsleur | 8429 | 0 | 0 | never_observed |
| ES Spanish | lessons | 5 | 0 | 0 | never_observed |
| FR French | Expressions | 3488 | 436 | 5 | rarely_observed |
| FR French | Grammar | 165 | 122 | 1 | rarely_observed |
| FR French | Tenses | 36 | 0 | 0 | never_observed |
| FR French | Exercises | 706 | 1 | 1 | rarely_observed |
| FR French | Translation | 146 | 0 | 0 | never_observed |
| FR French | My Errors | 20 | 0 | 0 | never_observed |
| FR French | Pimsleur | 4693 | 0 | 0 | never_observed |
| FR French | lessons | 10 | 6 | 1 | rarely_observed |
| IT Italian | Grammar | 145 | 95 | 2 | rarely_observed |
| IT Italian | Tenses | 34 | 26 | 1 | rarely_observed |
| IT Italian | Exercises | 734 | 0 | 0 | never_observed |
| IT Italian | Translation | 130 | 0 | 0 | never_observed |
| IT Italian | My Errors | 11 | 18 | 1 | rarely_observed |
| IT Italian | Rescue | 1 | 2 | 1 | rarely_observed |
| IT Italian | Pimsleur | 5344 | 0 | 0 | never_observed |
| IT Italian | lessons | 10 | 0 | 0 | never_observed |
| PT Portuguese | Grammar | 145 | 0 | 0 | never_observed |
| PT Portuguese | Tenses | 28 | 22 | 1 | rarely_observed |
| PT Portuguese | Exercises | 670 | 0 | 0 | never_observed |
| PT Portuguese | Translation | 127 | 0 | 0 | never_observed |
| PT Portuguese | My Errors | 20 | 0 | 0 | never_observed |
| PT Portuguese | Rescue | 3 | 9 | 1 | rarely_observed |
| PT Portuguese | Pimsleur | 4344 | 0 | 0 | never_observed |
| PT Portuguese | lessons | 5 | 0 | 0 | never_observed |
| ZH Mandarin | Pimsleur | 3043 | 0 | 0 | never_observed |
| ZH Mandarin | lessons | 2571 | 0 | 0 | never_observed |
| other | other | 22011 | 170 | 6 | rarely_observed |

### Daily mix: reps and active minutes by cell

Each cell entry is `language/population: reps, active minutes`; empty means no measured reps that day.

| Date | Total reps | Total active min | Cells |
| --- | --- | --- | --- |
| 2026-06-09 | 671 | 85.647 | DE German/Expressions: 398, 64.194 min; ZH Mandarin/other: 273, 21.453 min |
| 2026-06-10 | 927 | 52.418 | PT Portuguese/Expressions: 269, 21.911 min; ZH Mandarin/other: 658, 30.507 min |
| 2026-06-11 | 0 | 0 | — |
| 2026-06-12 | 0 | 0 | — |
| 2026-06-13 | 32 | 1.713 | ZH Mandarin/other: 32, 1.713 min |
| 2026-06-14 | 1117 | 95.948 | DE German/Expressions: 478, 60.514 min; PT Portuguese/Expressions: 24, 3.568 min; ZH Mandarin/other: 615, 31.866 min |
| 2026-06-15 | 365 | 55.082 | IT Italian/Expressions: 156, 24.039 min; PT Portuguese/Expressions: 144, 22.991 min; ZH Mandarin/other: 65, 8.052 min |
| 2026-06-16 | 695 | 60.04 | IT Italian/Expressions: 115, 12.281 min; PT Portuguese/Expressions: 1, 0.285 min; ZH Mandarin/other: 579, 47.474 min |
| 2026-06-17 | 0 | 0 | — |
| 2026-06-18 | 0 | 0 | — |
| 2026-06-19 | 0 | 0 | — |
| 2026-06-20 | 138 | 42.696 | ZH Mandarin/other: 106, 30.499 min; other/other: 32, 12.197 min |
| 2026-06-21 | 0 | 0 | — |
| 2026-06-22 | 971 | 119.555 | IT Italian/Expressions: 361, 70.935 min; ZH Mandarin/other: 610, 48.62 min |
| 2026-06-23 | 701 | 89.72 | FR French/Expressions: 2, 0.427 min; IT Italian/Expressions: 375, 69.285 min; ZH Mandarin/other: 324, 20.008 min |
| 2026-06-24 | 420 | 47.457 | IT Italian/Expressions: 137, 21.717 min; PT Portuguese/Expressions: 52, 11.986 min; ZH Mandarin/other: 231, 13.754 min |
| 2026-06-25 | 279 | 81.839 | IT Italian/Expressions: 146, 35.693 min; ZH Mandarin/other: 133, 46.146 min |
| 2026-06-26 | 205 | 59.232 | IT Italian/Expressions: 64, 15.209 min; PT Portuguese/Expressions: 113, 33.644 min; ZH Mandarin/other: 28, 10.379 min |
| 2026-06-27 | 0 | 0 | — |
| 2026-06-28 | 558 | 55.695 | IT Italian/Expressions: 91, 16.988 min; PT Portuguese/Expressions: 53, 10.88 min; ZH Mandarin/other: 414, 27.827 min |
| 2026-06-29 | 315 | 52.502 | IT Italian/Expressions: 37, 8.203 min; PT Portuguese/Expressions: 144, 37.096 min; ZH Mandarin/other: 134, 7.203 min |
| 2026-06-30 | 0 | 0 | — |
| 2026-07-01 | 0 | 0 | — |
| 2026-07-02 | 331 | 78.796 | IT Italian/Expressions: 188, 42.195 min; PT Portuguese/Expressions: 69, 12.764 min; ZH Mandarin/other: 74, 23.837 min |
| 2026-07-03 | 0 | 0 | — |
| 2026-07-04 | 0 | 0 | — |
| 2026-07-05 | 173 | 34.174 | IT Italian/Expressions: 173, 34.174 min |
| 2026-07-06 | 586 | 30.346 | IT Italian/Expressions: 56, 6.784 min; ZH Mandarin/other: 530, 23.562 min |
| 2026-07-07 | 0 | 0 | — |
| 2026-07-08 | 0 | 0 | — |
| 2026-07-09 | 0 | 0 | — |
| 2026-07-10 | 0 | 0 | — |
| 2026-07-11 | 0 | 0 | — |
| 2026-07-12 | 351 | 61.517 | IT Italian/Expressions: 239, 42.658 min; PT Portuguese/Expressions: 111, 18.408 min; other/other: 1, 0.451 min |
| 2026-07-13 | 0 | 0 | — |
| 2026-07-14 | 0 | 0 | — |
| 2026-07-15 | 0 | 0 | — |
| 2026-07-16 | 0 | 0 | — |
| 2026-07-17 | 0 | 0 | — |
| 2026-07-18 | 0 | 0 | — |
| 2026-07-19 | 809 | 80.382 | DE German/Expressions: 1, 0.124 min; IT Italian/Expressions: 169, 30.66 min; PT Portuguese/Expressions: 96, 21.91 min; ZH Mandarin/other: 542, 27.518 min; other/other: 1, 0.17 min |
| 2026-07-20 | 329 | 78.276 | IT Italian/Expressions: 219, 57.179 min; PT Portuguese/Expressions: 110, 21.097 min |
| 2026-07-21 | 268 | 52.881 | IT Italian/Expressions: 134, 30.79 min; PT Portuguese/Expressions: 134, 22.091 min |
| 2026-07-22 | 0 | 0 | — |
| 2026-07-23 | 906 | 98.044 | IT Italian/Expressions: 144, 31.301 min; PT Portuguese/Expressions: 176, 31.328 min; ZH Mandarin/other: 586, 35.415 min |
| 2026-07-24 | 653 | 65.645 | IT Italian/Expressions: 115, 28.305 min; PT Portuguese/Expressions: 68, 11.192 min; ZH Mandarin/other: 470, 26.148 min |
| 2026-07-25 | 233 | 59.86 | IT Italian/Expressions: 142, 34.197 min; PT Portuguese/Expressions: 91, 25.663 min |
| 2026-07-26 | 847 | 95.929 | IT Italian/Expressions: 113, 30.589 min; PT Portuguese/Expressions: 146, 32.451 min; ZH Mandarin/other: 588, 32.889 min |
| 2026-07-27 | 572 | 97.497 | ES Spanish/Expressions: 86, 26.073 min; IT Italian/Expressions: 130, 33.808 min; PT Portuguese/Expressions: 102, 24.08 min; ZH Mandarin/other: 247, 11.126 min; other/other: 7, 2.41 min |
| 2026-07-28 | 560 | 102.999 | DE German/Expressions: 134, 23.302 min; ES Spanish/Expressions: 55, 10.366 min; ES Spanish/Grammar: 6, 1.599 min; IT Italian/Expressions: 88, 21.537 min; PT Portuguese/Expressions: 175, 37.46 min; other/other: 102, 8.735 min |
| 2026-07-29 | 399 | 74.429 | DE German/Expressions: 89, 12.845 min; ES Spanish/Expressions: 93, 19.828 min; IT Italian/Expressions: 91, 21.306 min; PT Portuguese/Expressions: 126, 20.45 min |
| 2026-07-30 | 920 | 92.927 | DE German/Expressions: 24, 6.735 min; ES Spanish/Expressions: 78, 15.45 min; IT Italian/Expressions: 106, 23.269 min; PT Portuguese/Expressions: 71, 15.917 min; ZH Mandarin/other: 641, 31.556 min |
| 2026-07-31 | 360 | 65.39 | ES Spanish/Expressions: 140, 23.2 min; IT Italian/Expressions: 100, 22.609 min; PT Portuguese/Expressions: 120, 19.581 min |
| 2026-08-01 | 697 | 107.398 | DE German/Expressions: 195, 24.47 min; ES Spanish/Expressions: 139, 21.942 min; FR French/Expressions: 151, 21.772 min; IT Italian/Expressions: 87, 18.629 min; PT Portuguese/Expressions: 125, 20.585 min |
| 2026-08-02 | 858 | 79.065 | DE German/Expressions: 42, 9.337 min; ES Spanish/Expressions: 50, 8.522 min; IT Italian/Expressions: 92, 19.305 min; PT Portuguese/Expressions: 87, 16.152 min; ZH Mandarin/other: 587, 25.749 min |
| 2026-08-03 | 390 | 69.025 | ES Spanish/Expressions: 45, 7.047 min; FR French/Grammar: 122, 17.799 min; FR French/lessons: 6, 5.164 min; IT Italian/Expressions: 62, 14.325 min; IT Italian/Grammar: 86, 14.509 min; IT Italian/My Errors: 18, 1.378 min; PT Portuguese/Expressions: 51, 8.803 min |
| 2026-08-04 | 634 | 110.461 | DE German/Expressions: 144, 24.649 min; ES Spanish/Expressions: 109, 22.993 min; FR French/Expressions: 159, 19.749 min; FR French/Exercises: 1, 0.202 min; IT Italian/Expressions: 67, 14.255 min; PT Portuguese/Expressions: 127, 21.737 min; other/other: 27, 6.876 min |
| 2026-08-05 | 416 | 80.633 | DE German/Expressions: 39, 9.165 min; ES Spanish/Expressions: 111, 16.753 min; ES Spanish/Grammar: 1, 0.259 min; ES Spanish/Exercises: 6, 1.387 min; FR French/Expressions: 73, 8.209 min; IT Italian/Expressions: 82, 21.402 min; IT Italian/Grammar: 9, 1.083 min; PT Portuguese/Expressions: 94, 22.256 min; ZH Mandarin/other: 1, 0.119 min |
| 2026-08-06 | 919 | 87.245 | DE German/Expressions: 34, 4.43 min; ES Spanish/Expressions: 57, 8.917 min; FR French/Expressions: 51, 5.223 min; IT Italian/Expressions: 86, 21.765 min; PT Portuguese/Expressions: 100, 21.416 min; ZH Mandarin/other: 591, 25.494 min |
| 2026-08-07 | 268 | 59.265 | DE German/Rescue: 5, 0.908 min; ES Spanish/Expressions: 61, 12.31 min; ES Spanish/Rescue: 15, 2.495 min; IT Italian/Expressions: 58, 14.648 min; IT Italian/Tenses: 26, 4.76 min; IT Italian/Rescue: 2, 0.14 min; PT Portuguese/Expressions: 70, 19.548 min; PT Portuguese/Tenses: 22, 2.903 min; PT Portuguese/Rescue: 9, 1.553 min |

## Rating profile

Percentages are within each displayed grouping.

### By language and population

| Language | Population | Reps | Again | Hard | Good | Easy |
| --- | --- | --- | --- | --- | --- | --- |
| DE German | Expressions | 1937 | 41.0945% (796) | 2.8394% (55) | 5.0594% (98) | 51.0067% (988) |
| DE German | Rescue | 5 | 0.0% (0) | 0.0% (0) | 100.0% (5) | 0.0% (0) |
| DE German | Pimsleur | 11 | 9.0909% (1) | 18.1818% (2) | 18.1818% (2) | 54.5455% (6) |
| ES Spanish | Expressions | 1024 | 37.3047% (382) | 1.7578% (18) | 4.2969% (44) | 56.6406% (580) |
| ES Spanish | Grammar | 7 | 14.2857% (1) | 0.0% (0) | 85.7143% (6) | 0.0% (0) |
| ES Spanish | Exercises | 6 | 100.0% (6) | 0.0% (0) | 0.0% (0) | 0.0% (0) |
| ES Spanish | Rescue | 15 | 13.3333% (2) | 13.3333% (2) | 73.3333% (11) | 0.0% (0) |
| ES Spanish | Pimsleur | 1 | 0.0% (0) | 100.0% (1) | 0.0% (0) | 0.0% (0) |
| FR French | Expressions | 2329 | 31.2581% (728) | 2.4903% (58) | 30.2276% (704) | 36.024% (839) |
| FR French | Grammar | 122 | 24.5902% (30) | 0.8197% (1) | 1.6393% (2) | 72.9508% (89) |
| FR French | Exercises | 1 | 0.0% (0) | 0.0% (0) | 100.0% (1) | 0.0% (0) |
| FR French | lessons | 6 | 0.0% (0) | 0.0% (0) | 16.6667% (1) | 83.3333% (5) |
| IT Italian | Expressions | 6262 | 29.8946% (1,872) | 2.9064% (182) | 4.0722% (255) | 63.1268% (3,953) |
| IT Italian | Grammar | 95 | 15.7895% (15) | 4.2105% (4) | 0.0% (0) | 80.0% (76) |
| IT Italian | Tenses | 26 | 30.7692% (8) | 3.8462% (1) | 0.0% (0) | 65.3846% (17) |
| IT Italian | My Errors | 18 | 33.3333% (6) | 0.0% (0) | 5.5556% (1) | 61.1111% (11) |
| IT Italian | Rescue | 2 | 0.0% (0) | 0.0% (0) | 100.0% (2) | 0.0% (0) |
| IT Italian | Pimsleur | 1892 | 8.1924% (155) | 2.167% (41) | 11.8922% (225) | 77.7484% (1,471) |
| PT Portuguese | Expressions | 3445 | 38.5776% (1,329) | 2.8447% (98) | 5.4862% (189) | 53.0914% (1,829) |
| PT Portuguese | Tenses | 22 | 27.2727% (6) | 9.0909% (2) | 0.0% (0) | 63.6364% (14) |
| PT Portuguese | Rescue | 9 | 22.2222% (2) | 11.1111% (1) | 66.6667% (6) | 0.0% (0) |
| PT Portuguese | Pimsleur | 9 | 33.3333% (3) | 0.0% (0) | 22.2222% (2) | 44.4444% (4) |
| ZH Mandarin | Pimsleur | 12272 | 28.8462% (3,540) | 3.1209% (383) | 8.3198% (1,021) | 59.7132% (7,328) |
| ZH Mandarin | lessons | 269 | 8.5502% (23) | 1.8587% (5) | 17.4721% (47) | 72.119% (194) |
| ZH Mandarin | other | 28505 | 23.7537% (6,771) | 4.1186% (1,174) | 3.2065% (914) | 68.9212% (19,646) |
| other | other | 4117 | 14.8895% (613) | 3.8377% (158) | 27.0585% (1,114) | 54.2142% (2,232) |

### By maturity band

| Maturity | Reps | Again | Hard | Good | Easy |
| --- | --- | --- | --- | --- | --- |
| learning | 20857 | 30.7571% (6,415) | 4.0802% (851) | 14.9254% (3,113) | 50.2373% (10,478) |
| relearning | 10110 | 49.3175% (4,986) | 3.4125% (345) | 3.4421% (348) | 43.8279% (4,431) |
| review_young | 8569 | 44.731% (3,833) | 5.2515% (450) | 8.1923% (702) | 41.8252% (3,584) |
| review_mature | 5056 | 0.0% (0) | 0.2967% (15) | 5.8347% (295) | 93.8687% (4,746) |
| filtered | 17815 | 5.922% (1,055) | 2.947% (525) | 1.0777% (192) | 90.0533% (16,043) |

### By language, population, and maturity

| Language | Population | Maturity | Reps | Again | Hard | Good | Easy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DE German | Expressions | learning | 1420 | 40.8451% (580) | 3.3803% (48) | 5.2113% (74) | 50.5634% (718) |
| DE German | Expressions | relearning | 211 | 47.8673% (101) | 0.4739% (1) | 3.7915% (8) | 47.8673% (101) |
| DE German | Expressions | review_young | 121 | 95.0413% (115) | 4.9587% (6) | 0.0% (0) | 0.0% (0) |
| DE German | Expressions | review_mature | 185 | 0.0% (0) | 0.0% (0) | 8.6486% (16) | 91.3514% (169) |
| DE German | Rescue | learning | 4 | 0.0% (0) | 0.0% (0) | 100.0% (4) | 0.0% (0) |
| DE German | Rescue | review_young | 1 | 0.0% (0) | 0.0% (0) | 100.0% (1) | 0.0% (0) |
| DE German | Pimsleur | learning | 11 | 9.0909% (1) | 18.1818% (2) | 18.1818% (2) | 54.5455% (6) |
| ES Spanish | Expressions | learning | 730 | 39.0411% (285) | 1.0959% (8) | 0.5479% (4) | 59.3151% (433) |
| ES Spanish | Expressions | relearning | 80 | 37.5% (30) | 3.75% (3) | 12.5% (10) | 46.25% (37) |
| ES Spanish | Expressions | review_young | 163 | 41.1043% (67) | 4.2945% (7) | 18.4049% (30) | 36.1963% (59) |
| ES Spanish | Expressions | review_mature | 51 | 0.0% (0) | 0.0% (0) | 0.0% (0) | 100.0% (51) |
| ES Spanish | Grammar | learning | 7 | 14.2857% (1) | 0.0% (0) | 85.7143% (6) | 0.0% (0) |
| ES Spanish | Exercises | learning | 6 | 100.0% (6) | 0.0% (0) | 0.0% (0) | 0.0% (0) |
| ES Spanish | Rescue | learning | 14 | 14.2857% (2) | 14.2857% (2) | 71.4286% (10) | 0.0% (0) |
| ES Spanish | Rescue | review_young | 1 | 0.0% (0) | 0.0% (0) | 100.0% (1) | 0.0% (0) |
| ES Spanish | Pimsleur | learning | 1 | 0.0% (0) | 100.0% (1) | 0.0% (0) | 0.0% (0) |
| FR French | Expressions | learning | 1679 | 26.5039% (445) | 2.978% (50) | 39.0113% (655) | 31.5068% (529) |
| FR French | Expressions | relearning | 265 | 40.7547% (108) | 0.7547% (2) | 9.434% (25) | 49.0566% (130) |
| FR French | Expressions | review_young | 256 | 68.3594% (175) | 2.3438% (6) | 8.5938% (22) | 20.7031% (53) |
| FR French | Expressions | review_mature | 129 | 0.0% (0) | 0.0% (0) | 1.5504% (2) | 98.4496% (127) |
| FR French | Grammar | learning | 122 | 24.5902% (30) | 0.8197% (1) | 1.6393% (2) | 72.9508% (89) |
| FR French | Exercises | learning | 1 | 0.0% (0) | 0.0% (0) | 100.0% (1) | 0.0% (0) |
| FR French | lessons | learning | 6 | 0.0% (0) | 0.0% (0) | 16.6667% (1) | 83.3333% (5) |
| IT Italian | Expressions | learning | 2215 | 26.5011% (587) | 1.6253% (36) | 6.0045% (133) | 65.8691% (1,459) |
| IT Italian | Expressions | relearning | 1361 | 38.6481% (526) | 5.7311% (78) | 3.086% (42) | 52.5349% (715) |
| IT Italian | Expressions | review_young | 1324 | 57.3263% (759) | 4.4562% (59) | 2.1148% (28) | 36.1027% (478) |
| IT Italian | Expressions | review_mature | 1362 | 0.0% (0) | 0.6608% (9) | 3.8179% (52) | 95.5213% (1,301) |
| IT Italian | Grammar | learning | 95 | 15.7895% (15) | 4.2105% (4) | 0.0% (0) | 80.0% (76) |
| IT Italian | Tenses | learning | 26 | 30.7692% (8) | 3.8462% (1) | 0.0% (0) | 65.3846% (17) |
| IT Italian | My Errors | learning | 18 | 33.3333% (6) | 0.0% (0) | 5.5556% (1) | 61.1111% (11) |
| IT Italian | Rescue | learning | 2 | 0.0% (0) | 0.0% (0) | 100.0% (2) | 0.0% (0) |
| IT Italian | Pimsleur | learning | 1269 | 8.1166% (103) | 2.3641% (30) | 12.6084% (160) | 76.911% (976) |
| IT Italian | Pimsleur | relearning | 48 | 14.5833% (7) | 4.1667% (2) | 12.5% (6) | 68.75% (33) |
| IT Italian | Pimsleur | review_young | 77 | 58.4416% (45) | 11.6883% (9) | 24.6753% (19) | 5.1948% (4) |
| IT Italian | Pimsleur | review_mature | 498 | 0.0% (0) | 0.0% (0) | 8.0321% (40) | 91.9679% (458) |
| PT Portuguese | Expressions | learning | 1491 | 35.4125% (528) | 3.3535% (50) | 8.1154% (121) | 53.1187% (792) |
| PT Portuguese | Expressions | relearning | 813 | 49.0775% (399) | 1.599% (13) | 1.968% (16) | 47.3555% (385) |
| PT Portuguese | Expressions | review_young | 689 | 58.3454% (402) | 5.0798% (35) | 5.225% (36) | 31.3498% (216) |
| PT Portuguese | Expressions | review_mature | 452 | 0.0% (0) | 0.0% (0) | 3.5398% (16) | 96.4602% (436) |
| PT Portuguese | Tenses | learning | 22 | 27.2727% (6) | 9.0909% (2) | 0.0% (0) | 63.6364% (14) |
| PT Portuguese | Rescue | learning | 9 | 22.2222% (2) | 11.1111% (1) | 66.6667% (6) | 0.0% (0) |
| PT Portuguese | Pimsleur | learning | 9 | 33.3333% (3) | 0.0% (0) | 22.2222% (2) | 44.4444% (4) |
| ZH Mandarin | Pimsleur | learning | 5321 | 32.0241% (1,704) | 3.4016% (181) | 8.8893% (473) | 55.685% (2,963) |
| ZH Mandarin | Pimsleur | relearning | 1872 | 39.2628% (735) | 3.312% (62) | 6.0363% (113) | 51.3889% (962) |
| ZH Mandarin | Pimsleur | review_young | 3801 | 28.9661% (1,101) | 3.6832% (140) | 8.7345% (332) | 58.6162% (2,228) |
| ZH Mandarin | Pimsleur | review_mature | 1278 | 0.0% (0) | 0.0% (0) | 8.0595% (103) | 91.9405% (1,175) |
| ZH Mandarin | lessons | learning | 224 | 8.9286% (20) | 1.3393% (3) | 17.4107% (39) | 72.3214% (162) |
| ZH Mandarin | lessons | review_young | 33 | 9.0909% (3) | 6.0606% (2) | 24.2424% (8) | 60.6061% (20) |
| ZH Mandarin | lessons | review_mature | 12 | 0.0% (0) | 0.0% (0) | 0.0% (0) | 100.0% (12) |
| ZH Mandarin | other | learning | 3447 | 51.1169% (1,762) | 8.5872% (296) | 15.9849% (551) | 24.311% (838) |
| ZH Mandarin | other | relearning | 5175 | 58.2415% (3,014) | 3.5169% (182) | 1.7778% (92) | 36.4638% (1,887) |
| ZH Mandarin | other | review_young | 1608 | 58.4577% (940) | 10.2612% (165) | 4.2289% (68) | 27.0522% (435) |
| ZH Mandarin | other | review_mature | 460 | 0.0% (0) | 1.3043% (6) | 2.3913% (11) | 96.3043% (443) |
| ZH Mandarin | other | filtered | 17815 | 5.922% (1,055) | 2.947% (525) | 1.0777% (192) | 90.0533% (16,043) |
| other | other | learning | 2708 | 11.8538% (321) | 4.9852% (135) | 31.9793% (866) | 51.1817% (1,386) |
| other | other | relearning | 285 | 23.1579% (66) | 0.7018% (2) | 12.6316% (36) | 63.5088% (181) |
| other | other | review_young | 495 | 45.6566% (226) | 4.2424% (21) | 31.7172% (157) | 18.3838% (91) |
| other | other | review_mature | 629 | 0.0% (0) | 0.0% (0) | 8.744% (55) | 91.256% (574) |

## Summary

Across the last 90 calendar days (2026-05-10–2026-08-07), the account recorded 134 gap-defined sessions on 66 study days. Capped active time averaged 59.4 minutes/day (median 56.0), with 7 days in the owner's 120–180 minute 2–3 hour band; elapsed session time and capped active time are reported separately because Anki caps each rep at 60 seconds. The 60-day mix is the measured per-day language/population baseline, including 45 populated cells flagged as rarely observed or never observed under the stated coverage rule. In that 60-day mix, mean active minutes/day were DE German 4.0 min, ES Spanish 3.3 min, FR French 1.3 min, IT Italian 15.2 min, PT Portuguese 9.9 min, ZH Mandarin 10.1 min, other 0.5 min; that is materially less than the owner's 20–30 minutes per named language and stable 2–3 hour daily gym-block model on days where the active-time distribution falls outside that band, and the session/language-interleaving tables show the actual anatomy rather than assuming one block per language.
