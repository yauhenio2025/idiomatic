# C2 schedule-adoption dossiers

Collection actually read (SHA-256): `485a2849bf32e349faf44a117ca27057f3516eaa3bd9f89564db9279aecedd86` (81,715,200 bytes). SQLite was opened with `mode=ro&immutable=1` and `PRAGMA query_only=ON`; `PRAGMA quick_check` returned `ok`. This is analysis only: no collection row or revlog row was changed, and no revlog edit is proposed.

## Aggregate verdicts

| Language | Cards | Adoptable | Fresh | Fresh-trivial | Mature (`ivl > 21`) | Reps at stake |
|---|---:|---:|---:|---:|---:|---:|
| DE | 4,514 | 513 | 0 | 4,001 | 158 | 1,486 |
| ES | 3,193 | 434 | 0 | 2,759 | 51 | 1,024 |
| FR | 3,488 | 746 | 0 | 2,742 | 129 | 2,329 |
| IT | 5,730 | 1,467 | 0 | 4,263 | 862 | 6,250 |
| PT | 3,834 | 809 | 0 | 3,025 | 393 | 3,445 |
| **Total** | **20,759** | **3,969** | **0** | **16,790** | **1,593** | **14,534** |

`Fresh` is the aggregate label for the machine verdict `fresh-schedule`. All reps and mature cards in this census are on adoptable rows; fresh-trivial rows have zero reps by definition.

## Methodology and compatibility boundary

- Scope is every card physically assigned to one of the five exact `*::1 Expressions::1 Fluency` lanes. The lanes contain 20,759 cards, all of model `YouTube Expression Pool v1` (`1820114700`), and every collection-wide card of that model is in scope.
- Direction compatibility comes from Pool-v1 template ordinal 0, `EN → target`, whose documented task is English front to target-language production. The scan required the exact seven-field model schema and one-card/one-note cardinality.
- A row is schedule-healthy for adoption only when it is in an active queue, has a standard queue/type pair, has no filtered-deck residue (`odid=odue=0`), uses the production template, has a collection-unique GUID, has nonempty normalized target and English surfaces, and—when studied—has revlog history.
- Healthy studied rows are `adoptable`. Healthy zero-rep new rows are `fresh-trivial`, because retaining an untouched new-card schedule carries no learning investment. Any failed health gate is `fresh-schedule`; none failed in this source.
- `Mature` follows the estate inventory convention `ivl > 21`. `Reps at stake` is the exact sum of `cards.reps`. First/last review are `MIN/MAX(revlog.id)` per card, exposed both as the raw millisecond ID and a derived UTC timestamp.
- Join surfaces use the estate normalization exactly: strip `[sound:...]` and HTML, HTML-unescape, Unicode NFKC, stabilize curly quote/dash variants, collapse whitespace, and case-fold while preserving accents and punctuation.
- Each machine row records the normalized bilingual join-key cardinality and any peer card IDs. A non-unique join key is evidence for identity review, never sufficient evidence to merge cards, choose an expression sense, or combine schedules.
- The executor must preserve adopted note/GUID/card identity, schedule fields, opaque state, and every revlog row byte-for-byte. These dossiers authorize no revlog rewrite, schedule synthesis, duplicate merge, or collection mutation.

## Anomalies and cautions

- **Source/inventory skew:** `inventory.json` declares SHA-256 `316065a3a8312a799750e7505a4d69288a6fb09f690f1c582c139aeede5f8edf` and 79,867,904 bytes, but the commissioned path currently contains `485a2849bf32e349faf44a117ca27057f3516eaa3bd9f89564db9279aecedd86` and 81,715,200 bytes. Its Pool-v1 totals still reconcile exactly with this read (20,759 cards, 1,593 mature, 14,534 reps), while its deck-use names describe the pre-estate tree. C2 is therefore evidence for the actual bytes named by `source_sha256`; phase 0 must regenerate the joint frozen manifests from one post-sync copy before any production migration.
- **Reps/revlog shape:** 270 studied cards have more revlog rows than `cards.reps` (14,997 revlog rows versus 14,534 reps across the complete scope). These rows remain `adoptable`: the migration contract preserves both values and all history verbatim and does not require them to be equal. The executor must not reconcile, delete, synthesize, or reassign those rows.

| Language | Cards with `reps != revlog_rows` | Extra retained revlog rows |
|---|---:|---:|
| DE | 262 | 451 |
| ES | 0 | 0 |
| FR | 0 | 0 |
| IT | 8 | 12 |
| PT | 0 | 0 |

- **Normalized bilingual join-key collisions:** seven exact `(language, normalized target, normalized English)` pairs cover 14 cards. Six pairs are wholly unstudied. The Italian `avere a che fare con` example has one 1-rep card and one zero-rep peer; its studied card remains the only potentially meaningful donor. These are not automatic same-sense findings: phase-5 identity resolution must determine canonical example/sense ownership before choosing a winner or leaving distinct examples active.

| Language | Normalized target / English | Card IDs (`reps`) |
|---|---|---|
| DE | `da mein chef heute gute laune hatte, nutzte ich die gunst der stunde und fragte nach einer gehaltserhöhung.` / `since my boss was in a good mood today, i seized the opportunity and asked for a raise.` | `1784687712530` (0); `1785900370175` (0) |
| DE | `er macht keinen hehl daraus, dass er sich nach einem neuen job umsieht.` / `he makes no secret of the fact that he is looking for a new job.` | `1785341785906` (0); `1785632181959` (0) |
| DE | `wer in einer grossstadt wohnt, muss oft lange staus in kauf nehmen.` / `anyone who lives in a big city often has to put up with long traffic jams.` | `1783830098493` (0); `1784512534673` (0) |
| ES | `es importante aprender idiomas de cara a tu futuro profesional.` / `it is important to learn languages with a view to your professional future.` | `1784942381609` (0); `1785896784912` (0) |
| FR | `malheureusement, la vieille grange derrière la maison est partie en fumée pendant l'orage.` / `unfortunately, the old barn behind the house went up in smoke during the storm.` | `1785721988662` (0); `1785981826441` (0) |
| IT | `ci siamo messi d'accordo per trovarci davanti al cinema alle otto.` / `we agreed to meet in front of the cinema at eight.` | `1785719145893` (0); `1785719145935` (0) |
| IT | `ieri abbiamo avuto a che fare con un cliente molto difficile.` / `yesterday we had to deal with a very difficult customer.` | `1784260377037` (1); `1784262925588` (0) |

No migration-blocking lane anomalies were found: 0 non-Pool-model, wrong-template, suspended/buried, filtered-residue, invalid queue/type, note-card-cardinality, duplicate-GUID, blank-surface, or studied-without-revlog failures in scope. The JSON retains an `anomalies` array per card: 270 rows carry the history-shape observation, 14 carry the normalized-join-key observation, and all other arrays are empty.

## Summary

C2 classifies all 20,759 active-lane Pool-v1 cards without touching the collection: DE has 513 adoptable / 0 fresh / 4,001 fresh-trivial, ES 434 / 0 / 2,759, FR 746 / 0 / 2,742, IT 1,467 / 0 / 4,263, and PT 809 / 0 / 3,025; in total, 3,969 studied schedules carrying 14,534 reps (1,593 mature cards) are adoptable, 0 require a nontrivial fresh schedule, and 16,790 untouched new cards are fresh-trivial, subject to the mandatory joint phase-0 recensus prompted by the source/inventory checksum skew.
