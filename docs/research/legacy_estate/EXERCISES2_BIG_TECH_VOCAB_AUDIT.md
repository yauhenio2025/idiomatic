# Exercises2 `big_tech_vocab` hostile audit

Date: 2026-08-10  
Auditor: Codex, independent post-authoring review  
Scope: all 20 `{de,es,fr,it,pt}_big_tech_vocab_b01..b04` chunks

## Outcome

All 20 chunks pass after audit. Eight chunks required edits; twelve passed without edits; none failed. The review covered every one of the 725 source/triage rows and every field of all 476 retained V1 cards. The legacy `it_` prefix on item IDs was treated as the expected seed artifact because language routing comes from the chunk filename.

## Verdict table

| Chunk | Inputs | Keep | Drop | Verdict | Edited rows | Edited fields | Final gate |
|---|---:|---:|---:|---|---:|---:|---|
| `de_big_tech_vocab_b01` | 40 | 30 | 10 | PASS | 0 | 0 | PASS |
| `de_big_tech_vocab_b02` | 40 | 26 | 14 | PASS | 0 | 0 | PASS |
| `de_big_tech_vocab_b03` | 40 | 24 | 16 | PASS | 0 | 0 | PASS |
| `de_big_tech_vocab_b04` | 25 | 17 | 8 | PASS | 0 | 0 | PASS |
| `es_big_tech_vocab_b01` | 40 | 30 | 10 | PASS | 0 | 0 | PASS |
| `es_big_tech_vocab_b02` | 40 | 26 | 14 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `es_big_tech_vocab_b03` | 40 | 21 | 19 | PASS | 0 | 0 | PASS |
| `es_big_tech_vocab_b04` | 25 | 15 | 10 | PASS | 0 | 0 | PASS |
| `fr_big_tech_vocab_b01` | 40 | 30 | 10 | PASS | 0 | 0 | PASS |
| `fr_big_tech_vocab_b02` | 40 | 26 | 14 | PASS | 0 | 0 | PASS |
| `fr_big_tech_vocab_b03` | 40 | 22 | 18 | PASS-WITH-EDITS | 1 | 3 | PASS |
| `fr_big_tech_vocab_b04` | 25 | 15 | 10 | PASS | 0 | 0 | PASS |
| `it_big_tech_vocab_b01` | 40 | 30 | 10 | PASS | 0 | 0 | PASS |
| `it_big_tech_vocab_b02` | 40 | 26 | 14 | PASS-WITH-EDITS | 1 | 3 | PASS |
| `it_big_tech_vocab_b03` | 40 | 26 | 14 | PASS-WITH-EDITS | 1 | 3 | PASS |
| `it_big_tech_vocab_b04` | 25 | 15 | 10 | PASS-WITH-EDITS | 1 | 3 | PASS |
| `pt_big_tech_vocab_b01` | 40 | 30 | 10 | PASS | 0 | 0 | PASS |
| `pt_big_tech_vocab_b02` | 40 | 26 | 14 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `pt_big_tech_vocab_b03` | 40 | 25 | 15 | PASS-WITH-EDITS | 1 | 3 | PASS |
| `pt_big_tech_vocab_b04` | 25 | 16 | 9 | PASS-WITH-EDITS | 1 | 9 | PASS |
| **Total** | **725** | **476** | **249** | **20 pass** | **8** | **26** | **20/20** |

“Edited fields” counts changed JSON fields across both notes and triage artifacts. Portuguese item 126 accounts for eight note fields plus one triage-reason field.

## Audit method and evidence

- Applied all six defect classes in `CODEX_X2_WAVE_AUDIT.md`, including an item-by-item repetition review rather than sampling.
- Checked every source row against its triage decision and every retained card against the V1 vocabulary schema in `EXERCISES2_VOCAB_ADDENDUM.md`: production headword, genuine alternatives, register, interference trap, target example, English translation, exact cloze reduction, and provenance note.
- Read all 249 drop reasons. Language-dependent keep/drop differences were reviewed against the source term and target-language teaching value; they are justified. No decision changed.
- Compared the estate with `exercises2_cross_topic_exact_duplicates.json`. All seven listed Big Tech specialist rows were correctly kept here: 009 Filter bubble, 011 Disruption, 015 Datafication, 022 Digital divide, 025 Digital footprint, 049 Digital commons, and 087 Gig economy.
- Reviewed all 476 interference traps. Each names a real false friend, semantic distinction, collocational risk, preposition risk, or register risk; item 126's reversed warning was repaired.
- Verified all 476 clozes contain exactly one cloze group, blank the drilled headword exactly, preserve the example otherwise, and do not leak the answer elsewhere.
- Compared retained cards vertically across all five languages and scanned target examples for exact and repeated phrase frames. No duplicate example field and no systemic sentence boilerplate remained.
- Ran `.venv/bin/python tools/x2_batch_gate.py <chunk>` after each affected group and once more across all 20 chunks. Final result: `20/20 chunks pass the mechanical gate`.

## Complete edit ledger

### `es_big_tech_vocab_b02`, item 042

Reason: the register field referred to “the alternative,” but `alts` is empty. This was a field-semantics/schema-quality defect.

- `register`
  - Old: `Término crítico asentado en economía política y estudios de datos; la alternativa es explicativa y menos compacta.`
  - New: `Término crítico asentado en economía política y estudios de datos; describe su conversión en activos apropiables y negociables.`

### `fr_big_tech_vocab_b03`, item 095

Reason: avoid repeating `débat` in one short example while preserving the proposition.

- `example_tl`
  - Old: `La sphère publique numérique élargit l’accès au débat, mais les choix de classement des plateformes déterminent en grande partie quelles voix deviennent visibles dans le débat collectif.`
  - New: `La sphère publique numérique élargit l’accès au débat, mais les choix de classement des plateformes déterminent en grande partie quelles voix y deviennent visibles.`
- `example_en`
  - Old: `The digital public sphere broadens access to debate, but platforms’ ranking choices largely determine which voices become visible in collective debate.`
  - New: `The digital public sphere broadens access to debate, but platforms’ ranking choices largely determine which voices become visible there.`
- `cloze`
  - Old: `{{c1::La sphère publique numérique}} élargit l’accès au débat, mais les choix de classement des plateformes déterminent en grande partie quelles voix deviennent visibles dans le débat collectif.`
  - New: `{{c1::La sphère publique numérique}} élargit l’accès au débat, mais les choix de classement des plateformes déterminent en grande partie quelles voix y deviennent visibles.`

### `it_big_tech_vocab_b02`, item 051

Reason: avoid the same-stem repetition `produzione ... processi produttivi`.

- `example_tl`
  - Old: `Il modo di produzione digitale organizza proprietà, lavoro e accumulazione intorno a dati e piattaforme, trasformando al contempo processi produttivi e rapporti sociali.`
  - New: `Il modo di produzione digitale organizza proprietà, lavoro e accumulazione intorno a dati e piattaforme, trasformando al contempo attività economiche e rapporti sociali.`
- `example_en`
  - Old: `The digital mode of production organizes ownership, labor, and accumulation around data and platforms, transforming production processes and social relations at the same time.`
  - New: `The digital mode of production organizes ownership, labor, and accumulation around data and platforms while transforming economic activity and social relations.`
- `cloze`
  - Old: `Il {{c1::modo di produzione digitale}} organizza proprietà, lavoro e accumulazione intorno a dati e piattaforme, trasformando al contempo processi produttivi e rapporti sociali.`
  - New: `Il {{c1::modo di produzione digitale}} organizza proprietà, lavoro e accumulazione intorno a dati e piattaforme, trasformando al contempo attività economiche e rapporti sociali.`

### `it_big_tech_vocab_b03`, item 111

Reason: repair the compressed, unnatural collocation `ridurre la conservazione`.

- `example_tl`
  - Old: `La protezione dei dati personali impone di limitare la raccolta, specificarne le finalità e ridurre la conservazione, mentre la sicurezza informatica tutela anche informazioni non personali.`
  - New: `La protezione dei dati personali impone di limitare la raccolta, specificarne le finalità e ridurre i tempi di conservazione, mentre la sicurezza informatica tutela anche informazioni non personali.`
- `example_en`
  - Old: `Data privacy requires limiting collection, specifying its purposes, and reducing retention, whereas information security also protects non-personal information.`
  - New: `Data privacy requires limiting collection, specifying its purposes, and limiting retention periods, whereas information security also protects non-personal information.`
- `cloze`
  - Old: `La {{c1::protezione dei dati personali}} impone di limitare la raccolta, specificarne le finalità e ridurre la conservazione, mentre la sicurezza informatica tutela anche informazioni non personali.`
  - New: `La {{c1::protezione dei dati personali}} impone di limitare la raccolta, specificarne le finalità e ridurre i tempi di conservazione, mentre la sicurezza informatica tutela anche informazioni non personali.`

### `it_big_tech_vocab_b04`, item 128

Reason: replace an awkward legal construction with the idiomatic `fare capo a` collocation.

- `example_tl`
  - Old: `La proprietà dei dati resta controversa perché accesso, controllo tecnico, tutela degli interessati e diritti di sfruttamento non coincidono automaticamente in capo allo stesso soggetto.`
  - New: `La proprietà dei dati resta controversa perché accesso, controllo tecnico, tutela degli interessati e diritti di sfruttamento non fanno necessariamente capo allo stesso soggetto.`
- `example_en`
  - Old: `Data ownership remains contested because access, technical control, data-subject protections, and exploitation rights do not automatically vest in the same entity.`
  - New: `Data ownership remains contested because access, technical control, data-subject protections, and exploitation rights need not belong to the same entity.`
- `cloze`
  - Old: `La {{c1::proprietà dei dati}} resta controversa perché accesso, controllo tecnico, tutela degli interessati e diritti di sfruttamento non coincidono automaticamente in capo allo stesso soggetto.`
  - New: `La {{c1::proprietà dei dati}} resta controversa perché accesso, controllo tecnico, tutela degli interessati e diritti di sfruttamento non fanno necessariamente capo allo stesso soggetto.`

### `pt_big_tech_vocab_b02`, item 053

Reason: repair unnatural English coordination in the translation.

- `example_en`
  - Old: `Cyber-Marxism reinterpreted class struggle in light of computer networks, examining both new forms of cooperation and of capitalist exploitation.`
  - New: `Cyber-Marxism reinterpreted class struggle in light of computer networks, examining new forms of both cooperation and capitalist exploitation.`

### `pt_big_tech_vocab_b03`, item 101

Reason: avoid repeating `serviço` in one short example.

- `example_tl`
  - Old: `Os efeitos de rede fortalecem um serviço quando cada novo participante aumenta a utilidade desse serviço, criando vantagens cumulativas difíceis de contestar por rivais.`
  - New: `Os efeitos de rede fortalecem uma plataforma quando cada novo participante a torna mais útil, criando vantagens cumulativas difíceis de contestar por rivais.`
- `example_en`
  - Old: `Network effects strengthen a service when each new participant increases its usefulness, creating cumulative advantages that rivals find difficult to challenge.`
  - New: `Network effects strengthen a platform when each new participant makes it more useful, creating cumulative advantages that rivals find difficult to challenge.`
- `cloze`
  - Old: `Os {{c1::efeitos de rede}} fortalecem um serviço quando cada novo participante aumenta a utilidade desse serviço, criando vantagens cumulativas difíceis de contestar por rivais.`
  - New: `Os {{c1::efeitos de rede}} fortalecem uma plataforma quando cada novo participante a torna mais útil, criando vantagens cumulativas difíceis de contestar por rivais.`

### `pt_big_tech_vocab_b04`, item 126

Reason: the authored card had reversed the source meaning. Capitalized `Indigenous technologies` and the legacy Portuguese back `Tecnologias indígenas` refer to technologies of Indigenous peoples, not merely technologies developed domestically. The keep decision remains sound, but the card, trap, provenance note, and triage rationale had to be corrected together.

- `tl`
  - Old: `as tecnologias desenvolvidas no país`
  - New: `as tecnologias dos povos indígenas`
- `alts`
  - Old: `["as tecnologias nacionais", "as tecnologias autóctones"]`
  - New: `["as tecnologias indígenas"]`
- `register`
  - Old: `Na política industrial, a forma explicativa é clara e neutra; tecnologias autóctones é formal e rara, enquanto tecnologias nacionais pode abranger produtos apenas montados localmente.`
  - New: `Termo de estudos decoloniais e política tecnológica para tecnologias desenvolvidas, adaptadas ou governadas por povos indígenas e enraizadas em seus sistemas de conhecimento.`
- `trap`
  - Old: `Tecnologias indígenas refere-se normalmente às tecnologias de povos indígenas; no sentido geopolítico de indigenous, o inglês descreve desenvolvimento tecnológico interno.`
  - New: `Tecnologias desenvolvidas no país significa tecnologias nacionais ou locais e apaga a referência específica a povos indígenas expressa pelo inglês Indigenous com inicial maiúscula.`
- `example_tl`
  - Old: `As tecnologias desenvolvidas no país reduziram a exposição a embargos, mas continuaram dependentes de patentes, máquinas e componentes fornecidos pelo exterior.`
  - New: `As tecnologias dos povos indígenas combinam conhecimentos herdados, adaptação local e controle comunitário, sem medir a inovação apenas por patentes, escala ou inserção em mercados globais.`
- `example_en`
  - Old: `Technologies developed domestically reduced exposure to embargoes, but they remained dependent on patents, machinery, and components supplied from abroad.`
  - New: `Indigenous peoples’ technologies combine inherited knowledge, local adaptation, and community control without measuring innovation only by patents, scale, or integration into global markets.`
- `cloze`
  - Old: `As {{c1::tecnologias desenvolvidas no país}} reduziram a exposição a embargos, mas continuaram dependentes de patentes, máquinas e componentes fornecidos pelo exterior.`
  - New: `As {{c1::tecnologias dos povos indígenas}} combinam conhecimentos herdados, adaptação local e controle comunitário, sem medir a inovação apenas por patentes, escala ou inserção em mercados globais.`
- `note`
  - Old: `Diverge materialmente de old_back, que ativa a leitura referente a povos indígenas. O contexto de soberania tecnológica sustenta a leitura industrial; se a fonte pretendia saberes indígenas, esta carta precisará ser revista.`
  - New: `Auditoria: corrige a leitura industrial aplicada na autoria. O I maiúsculo de Indigenous e old_back apontam para povos indígenas, não para tecnologia desenvolvida no país.`
- Triage `reason`
  - Old: `O sentido de política industrial exige evitar o falso equivalente tecnologias indígenas e explicitar desenvolvimento tecnológico interno.`
  - New: `O I maiúsculo de Indigenous remete a povos indígenas; a carta ensina a evitar o falso equivalente tecnologias desenvolvidas no país e a preservar essa referência política e cultural.`

## Defect taxonomy summary

Counts below are findings by defect class and may overlap on the same row.

| Class | Result | Findings and disposition |
|---|---|---|
| 1. Language quality / naturalness | EDITED | Four rows: Italian 111 and 128, Portuguese 053, and the source-meaning reversal in Portuguese 126. |
| 2. Schema and field semantics | EDITED | One row: Spanish 042's `register` referred to a nonexistent alternative. All retained objects otherwise satisfy the V1 schema. |
| 3. Triage judgment / duplicate policy | EDITED | Portuguese 126's rationale was reversed, although its `keep` decision was correct. All 249 decisions and all seven cross-topic exact duplicates were otherwise correct. |
| 4. Interference traps | EDITED | Portuguese 126's trap taught the wrong contrast and was replaced. The other 475 traps are specific and pedagogically real. |
| 5. Cloze integrity | PASS | No cloze-specific defect. Six clozes were regenerated only to remain exact reductions after their examples or headwords changed. |
| 6a. Circular definitions | PASS | None. V1 has no separate definition field; register and trap prose do not define a term with itself. |
| 6b. Cross-item boilerplate | PASS | No repeated example sentence and no repeated multi-card proposition/frame requiring repair. Recurrent register openers are categorical metadata, not recycled drilled content. |
| 6c. English/target term-definition redundancy | N/A / PASS | The definition-pair test is not structurally applicable to V1. Required English examples are faithful translations, not duplicate definitions. |
| 6d. Within-sentence repetition | EDITED | Three rows: French 095, Italian 051, and Portuguese 101. |

No uncorrected blocker remains. No source item was silently reinterpreted, no retained card leaks its cloze answer, and no chunk requires rejection or rewrite.

**Final counts — chunks passed / edited / failed: 20 / 8 / 0.**
