# LingQ vocabulary technical inventory

Analysis timestamp: `2026-08-09T21:21:33.543331+00:00` (SRS due-date cutoff). This report contains aggregate statistics only. Row-level terms, hints, fragments, IDs, and dates remain in the gitignored JSON outputs.

## Executive result

The estate contains 51,826 unique LingQ rows across 10 languages. Only 1,593 rows (3.07%) are at nominal status 3, the account's broad learned tier. Of those, 912 (57.25%) also have `extended_status=3`, the empirically stronger durable-known marker.

For the five product languages (`de`, `es`, `fr`, `it`, `pt`), there are 34,065 LingQ terms and 1,248 learned terms. Exact normalized matching finds only 11 learned terms in either the exercises2 headwords or the expression index. The remaining 1,237 learned terms are dormant: 1,231 single-word terms and 6 multi-word terms. That is 99.12% of the learned tier, but its product value is overwhelmingly vocabulary rather than idioms.

| Language | Rows | Status 0 | Status 1 | Status 2 | Status 3 learned | Durable-known | Fragment coverage | Hint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| de | 16,302 | 15,255 | 53 | 287 | 707 | 457 | 99.29% | 98.09% |
| sv | 6,381 | 6,118 | 24 | 104 | 135 | 20 | 88.86% | 99.66% |
| fr | 6,203 | 5,870 | 6 | 83 | 244 | 165 | 99.53% | 97.78% |
| nl | 5,514 | 5,251 | 0 | 156 | 107 | 27 | 97.48% | 99.51% |
| pt | 4,329 | 4,128 | 6 | 51 | 144 | 100 | 99.10% | 98.38% |
| es | 4,199 | 4,061 | 0 | 30 | 108 | 73 | 99.86% | 96.69% |
| zh | 3,168 | 2,955 | 28 | 91 | 94 | 34 | 93.18% | 99.34% |
| it | 3,032 | 2,942 | 16 | 29 | 45 | 31 | 99.74% | 99.70% |
| da | 1,597 | 1,585 | 5 | 6 | 1 | 1 | 99.87% | 99.75% |
| no | 1,101 | 1,091 | 0 | 2 | 8 | 4 | 99.91% | 99.73% |
| **Total** | **51,826** | **49,256** | **138** | **839** | **1,593** | **912** | **97.56%** | **98.56%** |

## Status semantics in this account

The nominal levels behave as `0=new/unprogressed`, `1=recognized`, `2=familiar`, and `3=learned`, but the SRS schedule shows that status 3 contains two materially different states.

| Status | `extended_status=null` | `extended_status=0` | `extended_status=3` | Total | Share of estate |
|---:|---:|---:|---:|---:|---:|
| 0 | 46,949 | 2,306 | 1 | 49,256 | 95.04% |
| 1 | 2 | 136 | 0 | 138 | 0.27% |
| 2 | 5 | 834 | 0 | 839 | 1.62% |
| 3 | 8 | 673 | 912 | 1,593 | 3.07% |

Every one of the 912 consistent `(status=3, extended_status=3)` rows is future-due. Every one of the other 681 status-3 rows—673 with extended status 0 and 8 with null—is overdue. Across the full estate, 50,914 dates are overdue (98.24%), 912 are future (1.76%), and none are null. This makes `extended_status=3` a reliable durable-known marker in this account, while `extended_status=0` means ordinary/reviewable rather than known.

There is one contradictory `(status=0, extended_status=3)` row, and it is overdue. It is treated as a data-quality anomaly, not as learned vocabulary. The generated known lexicons use `status=3` as the broad learned/known tier and identify the `status=3 AND extended_status=3` subset in each header. A stricter generation mode can use that subset when false-known terms are more costly than omissions.

The due dates are stale as a mastery signal outside the durable-known subset: every status 0, 1, and 2 row is overdue. Also, all 51,826 `updated_at` values fall within approximately 10 minutes on 2026-08-09 (`00:01:06` through `00:11:20` UTC), so they look like synchronization timestamps rather than a learning-history timeline.

## Corpus overlap and dormant value

Matching is deliberately conservative. The left side is the set of lowercased, whitespace-collapsed LingQ terms. The exercises2 side merges every string-valued `tl` field found recursively in the six `<lang>_*.json` files. The expression side uses `expressions.json.normalized`.

| Language | LingQ terms | Exercise headwords | Expression keys | LingQ in exercises | LingQ in expressions | LingQ in either |
|---|---:|---:|---:|---:|---:|---:|
| de | 16,302 | 961 | 708 | 23 | 38 | 61 |
| es | 4,199 | 945 | 505 | 9 | 15 | 22 |
| fr | 6,203 | 973 | 502 | 14 | 27 | 40 |
| it | 3,032 | 989 | 837 | 12 | 10 | 22 |
| pt | 4,329 | 958 | 587 | 15 | 16 | 27 |
| **Total** | **34,065** | **4,826** | **3,139** | **73** | **106** | **172** |

Only 172 of 34,065 target-language LingQ entries (0.50%) appear in either product corpus. The learned-tier view is the actionable dormant inventory:

| Language | Learned | Durable-known | In exercises | In expressions | In either | Dormant | Dormant single | Dormant multi |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| de | 707 | 457 | 6 | 3 | 9 | 698 (98.73%) | 694 | 4 |
| es | 108 | 73 | 0 | 0 | 0 | 108 (100.00%) | 107 | 1 |
| fr | 244 | 165 | 1 | 0 | 1 | 243 (99.59%) | 242 | 1 |
| it | 45 | 31 | 0 | 0 | 0 | 45 (100.00%) | 45 | 0 |
| pt | 144 | 100 | 1 | 1 | 1 | 143 (99.31%) | 143 | 0 |
| **Total** | **1,248** | **826** | **8** | **4** | **11** | **1,237 (99.12%)** | **1,231** | **6** |

The exercise and expression columns overlap for one learned Portuguese term, so `in either` is not their arithmetic sum. The six row-level dormant multi-word records are in the gitignored `dormant_expressions/` files: 4 German, 1 Spanish, 1 French, and 0 Italian or Portuguese.

### Exact normalization

Normalization performs these operations in order:

1. Unicode NFC normalization.
2. Trim outer whitespace and collapse every internal whitespace run to one ASCII space.
3. Lowercase with Python `str.lower()`; preserve accents and diacritics.
4. Strip at most one language-specific leading article. Standalone articles require a following space; apostrophized articles do not.
5. Compare by exact equality. There is no stemming, lemmatization, punctuation removal, accent folding, hyphen folding, or fuzzy matching.

Articles stripped are:

- German: `der`, `die`, `das`, `den`, `dem`, `des`, `ein`, `eine`, `einen`, `einem`, `einer`, `eines`.
- Spanish: `el`, `la`, `los`, `las`, `un`, `una`, `unos`, `unas`.
- French: `le`, `la`, `les`, `un`, `une`, `des`, `l'`, `l’`.
- Italian: `il`, `lo`, `la`, `i`, `gli`, `le`, `un`, `uno`, `una`, `l'`, `l’`, `un'`, `un’`.
- Portuguese: `o`, `a`, `os`, `as`, `um`, `uma`, `uns`, `umas`.

Article stripping creates 65 left-side match-key collisions: 1 German, 4 Spanish, 45 French, 15 Italian, and 0 Portuguese. Counts therefore remain based on deduplicated LingQ term strings, not deduplicated match keys. This exact-match overlap is a lower bound: inflected forms, punctuation variants, separable verbs, and paraphrases are not credited.

## Fragment and hint quality

Fragments are abundant: 50,560 of 51,826 rows are non-empty (97.56%), representing 49,079 distinct strings. A sentence-terminal heuristic finds punctuation at the end of 43,072 non-empty fragments (85.19%). This is a useful completeness proxy, not a parser: headlines and clauses may be valid without final punctuation, and a punctuated fragment can still lack its beginning.

| Language | Non-empty | Avg chars | Median | Distinct | Terminal | Probable 250-char truncation | Cloze markup |
|---|---:|---:|---:|---:|---:|---:|---:|
| de | 16,187 (99.29%) | 120.14 | 99 | 16,098 | 83.16% | 1,107 | 9,796 |
| sv | 5,670 (88.86%) | 56.88 | 54 | 5,077 | 98.15% | 16 | 167 |
| fr | 6,174 (99.53%) | 114.11 | 75 | 6,009 | 77.11% | 714 | 2,596 |
| nl | 5,375 (97.48%) | 65.52 | 59 | 5,255 | 98.23% | 27 | 571 |
| pt | 4,290 (99.10%) | 90.79 | 83.5 | 4,197 | 68.93% | 2 | 2,243 |
| es | 4,193 (99.86%) | 139.07 | 128 | 4,154 | 76.53% | 687 | 2,522 |
| zh | 2,952 (93.18%) | 24.99 | 25.5 | 2,680 | 86.65% | 0 | 0 |
| it | 3,024 (99.74%) | 70.48 | 63 | 2,964 | 86.90% | 100 | 146 |
| da | 1,595 (99.87%) | 52.70 | 53 | 1,573 | 98.12% | 0 | 0 |
| no | 1,100 (99.91%) | 49.08 | 50 | 1,078 | 98.91% | 0 | 0 |

There are 2,690 fragments exactly 250 characters long; 2,653 of them lack terminal sentence punctuation and are classified as probable API truncation (5.25% of all non-empty fragments). Another 18,041 fragments (35.68%) contain LingQ-style triple-bracket cloze markup, and 11 contain HTML-like markup. All JSON decodes as UTF-8, with 0 Unicode replacement characters and 0 control-character hits. Encoding is therefore sound; truncation and embedded markup are the material cleanup issues.

Hints are present on 51,082 rows (98.56%), comprising 51,286 hint records. All 51,286 declare locale `en`. For the five product languages specifically, 1,222 of 1,248 learned rows have hints (97.92%) and 1,243 have fragments (99.60%), so contextualized reactivation content is feasible with little fallback generation.

## Dormant-language picture

The five languages without an exercises2/expression comparison in this inventory—Swedish, Dutch, Danish, Norwegian, and Chinese—hold 17,761 rows and 345 learned terms. They should not be called “absent from both corpora,” because no corresponding corpora were supplied. They are nevertheless quantified candidates for future language coverage.

| Language | Rows | Learned | Durable-known | Learned single | Learned multi | Learned with fragment | Learned with hints |
|---|---:|---:|---:|---:|---:|---:|---:|
| sv | 6,381 | 135 | 20 | 120 | 15 | 111 (82.22%) | 130 (96.30%) |
| nl | 5,514 | 107 | 27 | 105 | 2 | 105 (98.13%) | 105 (98.13%) |
| da | 1,597 | 1 | 1 | 1 | 0 | 1 (100.00%) | 1 (100.00%) |
| no | 1,101 | 8 | 4 | 8 | 0 | 8 (100.00%) | 7 (87.50%) |
| zh | 3,168 | 94 | 34 | 91 | 3 | 91 (96.81%) | 90 (95.74%) |
| **Total** | **17,761** | **345** | **86** | **325** | **20** | **316 (91.59%)** | **333 (96.52%)** |

Swedish is the only material multi-word opportunity in this group (15 learned space-containing terms), but it also has the weakest learned-fragment coverage at 82.22%. The space-based word-count rule is especially weak for Chinese; the three Chinese “multi-word” entries merely contain spaces and should not be interpreted as linguistic expressions without language-specific segmentation.

## Tags and data quality

The estate has 42,399 tag assignments on 25,213 terms (48.65% of rows), but 24,055 distinct tag strings. Of those distinct tags, 23,615 (98.17%) occur once. The operational taxonomy in `inventory.json` classifies assignments as 7,681 part-of-speech, 2,028 grammatical-person, 2,745 inflection/grammar, 27,137 source/import-looking, and 2,808 lexical/other. These categories are deterministic string rules, not authoritative LingQ types; raw tags have no type field.

Other quality findings:

- The 51,826 LingQ IDs are unique, all terms are non-empty, and there are 0 exact `(lang, term)` duplicates.
- All 3,140 expression IDs are unique and all `normalized` values are non-empty. Article normalization leaves 3,139 distinct expression keys because Italian has one normalized collision.
- Spanish has 1,007 top-level exercise note records but only 965 string-valued `tl` fields; the requested matching correctly excludes the 42 records without `tl`. Every other target language has one string `tl` per top-level item.
- Fragment reuse is limited: 50,560 non-empty fragments reduce to 49,079 distinct strings, a difference of 1,481.
- Every SRS row has a due date, but 98.24% are overdue; this is not a current readiness score.

## What is feasible with this data

1. **Known-vocabulary constraints are immediately feasible.** The five target lexicons contain 1,248 learned terms, with an 826-term durable-known subset. Sentence generation can use the broad tier for coverage or the durable subset for conservative difficulty control.
2. **Dormant vocabulary reactivation is the largest quantified opportunity.** There are 1,237 learned target-language terms absent from both product corpora, and 1,231 are single-word. German alone contributes 698 dormant learned terms.
3. **Personalized context is feasible after lightweight cleaning.** Learned target terms have 99.60% fragment coverage and 97.92% hint coverage, but generators should remove triple-bracket/HTML markup and reject probable 250-character truncations before presenting source context.
4. **A large owner-known idiom program is not supported by the learned tier.** Only 8 learned target-language terms contain spaces, and only 6 are dormant. The separate 3,140-row expression index is useful as a product corpus, but it does not establish that the owner knows those expressions.
5. **Coverage analysis can be improved, but exact results should remain the baseline.** Language-aware lemmatization and punctuation handling would recover morphological matches; a second, explicitly labeled fuzzy/lemma overlap should be added rather than replacing the auditable exact normalization.
6. **Current mastery cannot be inferred reliably.** The stable signals are nominal status 3 and, more conservatively, the status-3/extended-3 combination. Overdue dates and clustered sync timestamps should not drive spaced-repetition or proficiency decisions without fresher event data.

The detailed, private results are in `inventory.json`, `overlap.json`, `known_lexicons/<lang>.json`, and `dormant_expressions/<lang>.json`. They are intentionally gitignored; this report is the aggregate-only artifact suitable for version control.
