# Exercises 2.0 Wave 3 TENSES audit

Audited and merged 2026-08-08. Wave 3 contains the 300 canonical TENSES
prompts in each of German, Spanish, French, Italian, and Portuguese: 1,500
notes and 3,000 cards under the frozen Exercises v1 model. All source rows
remain `keep`; no ID, English prompt, or canonical ordering changed.

This is a content-complete merge, not an audio build or release. The Wave 3
format already has its owner verdict. Rebuilding and delivery remain closed
only because the local-Qwen listening verdict for APKG 1615 is pending; this
audit did not call `/admin/exercises2-build`, seed bulk TTS, invoke a provider,
or publish an APKG.

## Source anchors

- Staging manifest: `idiomatic/grammar/data/exercises2/batches/manifests/wave3.json`
  (`98a7e60211412cfd978bb2d61d2681f3d6bc250527f83fae27ca16d4ac03b307`).
- Selected canonical ID sequence:
  `ab5974f38b092c8bc4379d923beedb6f5448b79c15b5f8ce950c574ff9206c43`.
- The manifest pins all six committed source files and all 15 staged inputs.
  `stage wave3 --check` reproduced those inputs without drift.
- The committed cross-topic report contains 20 exact-English duplicate groups,
  with **zero groups involving TENSES**. `duplicate-report --check` reproduced
  the report.

## Independent audit protocol

Each of the 15 chunks received a separate hostile 100-row review after its
first authoring pass. Reviewers checked source equivalence, native usage,
register, real interference traps, complete cloze groups, and whether the new
practice sentence was genuinely independent rather than a topical or semantic
reskin. They edited the landed artifacts in place and reran the exact chunk
gate. Consequently, the correction counts below are auditor attestations, not
diff-derived metrics; there is deliberately no retained lower-quality
pre-audit corpus.

| Chunk | Auditor-attested intervention | Final legacy-identical TL |
|---|---:|---:|
| `de_tenses_b01` | 74 example reskins plus translation/trap/cloze repairs | 1 |
| `de_tenses_b02` | 55 corrected note rows | 5 |
| `de_tenses_b03` | 72 example reskins plus usage repairs | 3 |
| `es_tenses_b01` | 68 example reskins plus usage repairs | 4 |
| `es_tenses_b02` | 47 example reskins plus usage repairs | 16 |
| `es_tenses_b03` | 33 corrected rows | 11 |
| `fr_tenses_b01` | 45 corrected rows | 1 |
| `fr_tenses_b02` | 30 corrected rows | 6 |
| `fr_tenses_b03` | 92 example reskins plus translation/cloze repairs | 5 |
| `it_tenses_b01` | approximately 74 corrected rows | 93 |
| `it_tenses_b02` | 48 example reskins plus usage repairs | 72 |
| `it_tenses_b03` | 62 example reskins and 11 translation repairs | 46 |
| `pt_tenses_b01` | 50 example reskins plus usage repairs | 4 |
| `pt_tenses_b02` | 62 example reskins plus usage repairs | 11 |
| `pt_tenses_b03` | 51 corrected rows | 4 |

`legacy-identical TL` is informational, not a quality failure. In particular,
the Italian `old_back` values come from the separately repaired and verified
Italian rebuild reference. Every retained identical rendering was reviewed;
new examples, clozes, traps, and metadata were still authored independently.

The final reconciliation also removed the last three high-overlap practice
pairs (German evacuation policy, Spanish emergency-disclosure deadlines, and
Italian freight booking). Each language now has 300 distinct `example_tl`
values and 300 distinct `example_en` values, and no within-language pair has
word-set Jaccard similarity of 0.42 or greater.

## Category reconciliation

Categories describe the construction actually taught in the target language,
so they are not forced to agree merely because all five notes share an English
ID. One independent cross-language adjudication produced these intentional
splits:

| Shared ID | Final classification decision |
|---|---|
| `it_tenses_253` | All five `modal-construction`: an unconditioned conditional-perfect inference. |
| `it_tenses_264` | DE/ES explicit irrealis = `counterfactual-sequence`; FR/PT temporal adjunct + conditional perfect = `modal-construction`; IT marked absolute participle = `literary-sequence`. |
| `it_tenses_265` | DE/FR/IT/PT detached formal participles = `literary-sequence`; ES expanded open condition = `modal-construction`. |
| `it_tenses_268`, `it_tenses_272` | Same three-way realized-structure split as 264. |
| `it_tenses_280` | FR/IT completed future anteriority = `future-perfect`; DE/ES/PT non-perfect prospective sequencing = `literary-sequence`. |

Aggregate merged categories are therefore:

| Language | Past anteriority | Ongoing → present | Modal | Counterfactual | Future perfect | Literary |
|---|---:|---:|---:|---:|---:|---:|
| DE | 100 | 50 | 51 | 67 | 30 | 2 |
| ES | 100 | 50 | 52 | 67 | 30 | 1 |
| FR | 100 | 50 | 54 | 64 | 31 | 1 |
| IT | 100 | 50 | 51 | 64 | 31 | 4 |
| PT | 100 | 50 | 54 | 64 | 30 | 2 |

## Final artifacts and gates

| Merged notes | Rows | SHA-256 |
|---|---:|---|
| `de_tenses.json` | 300 | `9dc081049596e13226519ae5ebd79032c290b5897ede2371ca4008c07cf337b8` |
| `es_tenses.json` | 300 | `4a5116b9c8a60368518830951fb2da7c1e94e46ebc422dd4cbe30fbb0983971b` |
| `fr_tenses.json` | 300 | `c8f26f464008dbc1437b65e2b0fcea5cfa98db40572bb6e66b7dd43063a5c386` |
| `it_tenses.json` | 300 | `4a69344cc0cb61915bdda6d9cc1ba8168bc65868018507d28789f4e3dd69d0e2` |
| `pt_tenses.json` | 300 | `102660c1afad6681fe89ee140d11b7f4108d229c3d621a7a4db494b95431c0d7` |

The hardened mechanical gate requires exact TENSES input/triage/note schemas,
approved categories, valid verdicts, meaningful one-line drop reasons, exact
source/order preservation, parser and cloze validity, 18–30-word examples,
target-language checks, and no exact example reuse against any sibling chunk
or already merged Exercises 2 topic.

Final command results:

```text
stage wave3 --check                         PASS (15 source-hashed chunks)
x2_batch_gate.py <all 15 chunks>           PASS (15/15; 1,500/1,500 keeps)
duplicate-report --check                    PASS (20 source groups; 0 TENSES)
merge {de,es,fr,it,pt}_tenses               PASS (300 notes each)
verify-merge <all five TENSES topics>       PASS (5/5)
check-merged-duplicates                     PASS (3,272 merged EN keys)
```

Wave 4 V1, Wave 5 V2, and Wave 6 P1 remain separate owner format gates. No
bulk authoring, merge, build, or voicing for those formats is authorized by
this Wave 3 result.
