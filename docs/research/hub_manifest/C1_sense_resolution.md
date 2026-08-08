# C1 sense-resolution evidence pass

Collection actually read (SHA-256): `485a2849bf32e349faf44a117ca27057f3516eaa3bd9f89564db9279aecedd86`. SQLite was opened with `mode=ro&immutable=1` and `PRAGMA query_only=ON`; no proposal in this report changes or merges collection data.

The frozen collision manifest and estate inventory both declare the earlier copy SHA `316065a3a8312a799750e7505a4d69288a6fb09f690f1c582c139aeede5f8edf`, which does not match the bytes now at the commissioned collection path. Frozen group membership and origin decks were retained, while GUIDs, current decks, suspension state, card statistics, and revlog evidence were re-read from the actual immutable copy. All 411 referenced origin decks resolve in `inventory.json`.

## Disposition counts

| Disposition | Exact bilingual groups | Manual-review candidates | Total |
|---|---:|---:|---:|
| `same-sense-merge` | 2,664 | 18 | 2,682 |
| `distinct-senses` | 0 | 1 | 1 |
| `quarantine` | 1 | 6 | 7 |
| **All bundles** | **2,665** | **25** | **2,690** |

The bundles contain 5,486 member occurrences over 5,438 unique notes. Every member is currently a suspended archive task; none is an active `YouTube Expression Pool v1` fluency card.

## Full quarantine list

- `52b6d3aa46640cd6` (exact bilingual, es, `más bien`): The legacy occurrence is scalar hedging (“rather symbolic”), while the current occurrence is corrective reformulation (“rather, the Likud”), and both notes bundle the two functions.
- `df8b53300f2ff97b` (manual review, es, `al margen de`): The evidence mixes exclusion from a framework (“outside official channels”) with topic-setting or exception (“apart from the issue”), and individual notes bundle both uses.
- `e383b8e3acddf900` (manual review, es, `más bien`): The legacy occurrence is scalar hedging (“rather symbolic”), while the current occurrence is corrective reformulation (“rather, the Likud”), and both notes bundle the two functions.
- `763bc565b9c4c14f` (manual review, fr, `pour le coup`): The gloss set spans “for once/on this point,” “this time,” and resultative “as a result/indeed,” while the legacy audio-only members carry no textual context to disambiguate the use.
- `77dbf86af6dcc45a` (manual review, it, `al di là di`): The evidence combines literal spatial “beyond” with abstract topic-setting or concessive “apart from,” and the current note deliberately mixes both.
- `e170261d13bb53dc` (manual review, it, `se non fosse che`): The evidence mixes a counterfactual obstacle (“if it were not for the fact that”) with an exceptive discourse connector (“except that”), and the legacy audio-only context cannot resolve the split.
- `201ece0192435e5f` (manual review, pt, `meia dúzia`): Meia dúzia can denote literal six or a dismissively small number, and the supplied source/examples mix exact and approximate quantity without a defensible member-level split.

## Manual-review candidates

### 1. `durchgesickert` — `same-sense-merge` (medium)

Candidate `15049f5d21187202` has normalized English evidence “leaked out”; “leaked out / became known”; member note IDs: 1776907899765, 1777009537152, 1777009537161, 1785345307583, 1785349682865, 1785349689689, 1785349690028. Every textual context uses durchsickern for information becoming known unofficially; “leaked out” and “became known” are compatible glosses of that one sense. Proposed survivor: `durchgesickert` / `leaked out / became known`. Current task evidence: 7 suspended archive member(s), 0 active fluency members; aggregate card state is 8 reps and 1 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 2. `leer stehen` — `same-sense-merge` (medium)

Candidate `6573d6b4cf4f4338` has normalized English evidence “to stand empty / be vacant”; “to stand empty / to be vacant”; member note IDs: 1777795666826, 1778059190907, 1778059191889, 1785343731168, 1785345207989, 1785345214913, 1785345215276. Both generations apply leer stehen to unoccupied buildings or rooms, and “stand empty” and “be vacant” paraphrase the same state. Proposed survivor: `leer stehen` / `to stand empty / be vacant`. Current task evidence: 7 suspended archive member(s), 0 active fluency members; aggregate card state is 7 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 3. `al margen de` — `quarantine` (low)

Candidate `df8b53300f2ff97b` has normalized English evidence “apart from”; “outside of”; member note IDs: 1777193740475, 1784333005258, 1784333127078, 1784333128637, 1784333129155. The evidence mixes exclusion from a framework (“outside official channels”) with topic-setting or exception (“apart from the issue”), and individual notes bundle both uses. Current task evidence: 5 suspended archive member(s), 0 active fluency members; aggregate card state is 2 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 4. `hacer frente a` — `same-sense-merge` (medium)

Candidate `b7a343e41b7e7971` has normalized English evidence “to face / to cope with”; “to face / to tackle / to cope with”; member note IDs: 1777796469134, 1785320016212, 1785320795706, 1785320798726, 1785320798981. All contexts describe actively confronting or addressing adversity, so “face,” “tackle,” and “cope with” are compatible glosses. Proposed survivor: `hacer frente a` / `to face / tackle / cope with`. Current task evidence: 5 suspended archive member(s), 0 active fluency members; aggregate card state is 1 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 5. `más bien` — `quarantine` (low)

Candidate `e383b8e3acddf900` has normalized English evidence “rather / more like”; member note IDs: 1778057499560, 1784597530976, 1784597889057, 1784597890148, 1784597890338. The legacy occurrence is scalar hedging (“rather symbolic”), while the current occurrence is corrective reformulation (“rather, the Likud”), and both notes bundle the two functions. Current task evidence: 5 suspended archive member(s), 0 active fluency members; aggregate card state is 1 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 6. `sin duda alguna` — `same-sense-merge` (medium)

Candidate `08f683ce67f915a5` has normalized English evidence “without a doubt”; “without any doubt whatsoever”; member note IDs: 1777796469148, 1785321012301, 1785324428790, 1785324432112, 1785324432324. All examples and occurrences use sin duda alguna as an emphatic marker of certainty; the gloss difference is only degree of English emphasis. Proposed survivor: `sin duda alguna` / `without any doubt whatsoever`. Current task evidence: 5 suspended archive member(s), 0 active fluency members; aggregate card state is 2 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 7. `compte tenu du` — `same-sense-merge` (medium)

Candidate `daffb7506f920943` has normalized English evidence “given / taking into account”; “given the”; member note IDs: 1778059189260, 1778059189291, 1784938838963, 1785027682855, 1785027685792, 1785027686034. Compte tenu du introduces a factor to be considered, and the legacy “given the” gloss is a direct paraphrase of the current evidence. Proposed survivor: `compte tenu du` / `given / taking into account`. Current task evidence: 6 suspended archive member(s), 0 active fluency members; aggregate card state is 5 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 8. `ne cesse de` — `same-sense-merge` (medium)

Candidate `9cca056f8d730f1f` has normalized English evidence “continues to / keeps on”; “does not cease to / continuously”; member note IDs: 1777186141310, 1777193961217, 1777193961224, 1785337854209, 1785342871036, 1785342874728, 1785342874962. Every context expresses uninterrupted or repeated continuation, making “continues to,” “keeps on,” and “does not cease to” equivalent here. Proposed survivor: `ne cesse de` / `continue to / keep on`. Current task evidence: 7 suspended archive member(s), 0 active fluency members; aggregate card state is 7 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 9. `pour le coup` — `quarantine` (low)

Candidate `763bc565b9c4c14f` has normalized English evidence “in this case / for once / on this specific point”; “this time / as it happens”; member note IDs: 1777009537898, 1777009537902, 1784852860771, 1784938570225, 1784938572857, 1784938573132. The gloss set spans “for once/on this point,” “this time,” and resultative “as a result/indeed,” while the legacy audio-only members carry no textual context to disambiguate the use. Current task evidence: 6 suspended archive member(s), 0 active fluency members; aggregate card state is 8 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 10. `remise en cause` — `same-sense-merge` (medium)

Candidate `f5ed4fb9c24f4d3a` has normalized English evidence “calling into question / challenging”; “calling into question / questioning”; member note IDs: 1777014793533, 1777014794538, 1785721981278, 1785721986752, 1785721987120. The noun phrase consistently denotes questioning or challenging an assumption, system, or competence. Proposed survivor: `remise en cause` / `calling into question / challenging`. Current task evidence: 5 suspended archive member(s), 0 active fluency members; aggregate card state is 7 reps and 1 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 11. `à deux doigts de` — `same-sense-merge` (medium)

Candidate `cbc376430bcb28c7` has normalized English evidence “on the verge of / inches away from”; “on the verge of / this close to”; member note IDs: 1777441547837, 1777442638195, 1777442640203, 1785337854213, 1785342871040, 1785342874732, 1785342874966. All contexts express extreme proximity to an event, and “on the verge of,” “this close to,” and “inches away from” are direct paraphrases. Proposed survivor: `à deux doigts de` / `on the verge of / this close to`. Current task evidence: 7 suspended archive member(s), 0 active fluency members; aggregate card state is 9 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 12. `al di là di` — `quarantine` (low)

Candidate `77dbf86af6dcc45a` has normalized English evidence “beyond”; “beyond / apart from”; member note IDs: 1777099196771, 1777099197311, 1777099197315, 1784424360604, 1784509109609, 1784509117732, 1784509118478. The evidence combines literal spatial “beyond” with abstract topic-setting or concessive “apart from,” and the current note deliberately mixes both. Current task evidence: 7 suspended archive member(s), 0 active fluency members; aggregate card state is 6 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 13. `guarda caso` — `same-sense-merge` (medium)

Candidate `01ed10ae16e98df2` has normalized English evidence “coincidentally”; “coincidentally / as luck would have it”; “coincidentally / lo and behold”; member note IDs: 1777193931911, 1777193961445, 1777193961452, 1785716223247, 1785719128953, 1785719150995, 1785719152720. All occurrences flag an apparently coincidental event, usually with the same ironic implication that it may not be accidental. Proposed survivor: `guarda caso` / `coincidentally / lo and behold`. Current task evidence: 7 suspended archive member(s), 0 active fluency members; aggregate card state is 15 reps and 2 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 14. `in funzione di` — `distinct-senses` (high)

Candidate `f2f2fa5fbcf26063` has normalized English evidence “based on / in terms of”; “in the role of / acting as”; member note IDs: 1777099196767, 1777099197307, 1777099198310, 1785307027966, 1785309003786, 1785309013880, 1785309014657. The candidate records cleanly separate a capacity/role construction from a dependency/criterion construction. The legacy members use in funzione di to mean serving or acting in a stated role or capacity. The Idiomatic members use in funzione di to mean based on, depending on, or organized according to a criterion. Current task evidence: 7 suspended archive member(s), 0 active fluency members; aggregate card state is 7 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 15. `in parole povere` — `same-sense-merge` (medium)

Candidate `5a2b721d0d81f3f1` has normalized English evidence “in simple terms”; “simply put / in plain english”; member note IDs: 1778059189661, 1778059192680, 1784283543448, 1784338690979, 1784338697025, 1784338697343. Every member presents in parole povere as a discourse marker introducing a simplified restatement. Proposed survivor: `in parole povere` / `simply put / in simple terms`. Current task evidence: 6 suspended archive member(s), 0 active fluency members; aggregate card state is 6 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 16. `nel senso che` — `same-sense-merge` (medium)

Candidate `bd406ac57425ad81` has normalized English evidence “in the sense that”; “in the sense that / i mean...”; member note IDs: 1776916072891, 1777009537395, 1777009538404, 1784274419388, 1784338690737, 1784338696783, 1784338697101. All contexts use nel senso che to clarify, specify, or reformulate a preceding statement. Proposed survivor: `nel senso che` / `in the sense that / i mean`. Current task evidence: 7 suspended archive member(s), 0 active fluency members; aggregate card state is 5 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 17. `quando si tratta di` — `same-sense-merge` (high)

Candidate `a7ca8d4b2046ff75` has normalized English evidence “when it comes to”; member note IDs: 1776917676402, 1777009537435, 1777009538444, 1784422276640, 1784423804728, 1784423811166, 1784423811472. Both generations use the same topic-framing construction before a noun or infinitive, with exactly compatible glosses and examples. Proposed survivor: `quando si tratta di` / `when it comes to`. Current task evidence: 7 suspended archive member(s), 0 active fluency members; aggregate card state is 6 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 18. `se non fosse che` — `quarantine` (low)

Candidate `e170261d13bb53dc` has normalized English evidence “except that / if it weren't for the fact that”; “if it weren't for the fact that”; member note IDs: 1778059189681, 1778059192700, 1784339600838, 1784423804708, 1784423811146, 1784423811452. The evidence mixes a counterfactual obstacle (“if it were not for the fact that”) with an exceptive discourse connector (“except that”), and the legacy audio-only context cannot resolve the split. Current task evidence: 6 suspended archive member(s), 0 active fluency members; aggregate card state is 9 reps and 1 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 19. `afinal de contas` — `same-sense-merge` (high)

Candidate `77ea1ae2eb550eb0` has normalized English evidence “after all / at the end of the day”; member note IDs: 1777015508626, 1777015519831, 1785978724369, 1785980252401, 1785980259870, 1785980260312. Both generations use afinal de contas to introduce a decisive justification or concluding fact, with the same two English paraphrases. Proposed survivor: `afinal de contas` / `after all / at the end of the day`. Current task evidence: 6 suspended archive member(s), 0 active fluency members; aggregate card state is 2 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 20. `dar certo` — `same-sense-merge` (medium)

Candidate `2d2db3bcf78b1eb7` has normalized English evidence “to work out / succeed”; “to work out / to succeed”; member note IDs: 1777015508622, 1777015519827, 1785318661817, 1785515085011, 1785515090233, 1785515090520. Every occurrence describes a plan, process, or undertaking succeeding or working out. Proposed survivor: `dar certo` / `to work out / succeed`. Current task evidence: 6 suspended archive member(s), 0 active fluency members; aggregate card state is 2 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 21. `desde o primeiro momento` — `same-sense-merge` (medium)

Candidate `0b81a5c02eca23c2` has normalized English evidence “from the very beginning”; “from the very first moment / right from the start”; member note IDs: 1777011297721, 1777011310066, 1785345441419, 1785346567168, 1785346571770, 1785346572056. All evidence marks a state or action as holding from the beginning, and the English variants are direct paraphrases. Proposed survivor: `desde o primeiro momento` / `from the very first moment / right from the start`. Current task evidence: 6 suspended archive member(s), 0 active fluency members; aggregate card state is 2 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 22. `meia dúzia` — `quarantine` (low)

Candidate `201ece0192435e5f` has normalized English evidence “a handful / a few”; “a handful / a select few / very few”; member note IDs: 1777442604892, 1777442638721, 1786068101516. Meia dúzia can denote literal six or a dismissively small number, and the supplied source/examples mix exact and approximate quantity without a defensible member-level split. Current task evidence: 3 suspended archive member(s), 0 active fluency members; aggregate card state is 3 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 23. `recorrer a` — `same-sense-merge` (medium)

Candidate `54a3cf9d4adc7d5f` has normalized English evidence “to resort to”; “to resort to / to turn to”; member note IDs: 1777015508606, 1777015519811, 1785311237899, 1785311843223, 1785311845542, 1785311845746. All contexts use recorrer a for turning to a person, resource, or measure as a solution, with compatible “resort to/turn to” glosses. Proposed survivor: `recorrer a` / `to resort to / turn to`. Current task evidence: 6 suspended archive member(s), 0 active fluency members; aggregate card state is 4 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 24. `tanto que` — `same-sense-merge` (high)

Candidate `bd3b209b085dfe64` has normalized English evidence “so much so that”; member note IDs: 1777442604906, 1777442638735, 1781859746448, 1783832892658, 1783832893526, 1783832894686. Every source and example uses tanto que to introduce a factual consequence that demonstrates the preceding degree or claim. Proposed survivor: `tanto que` / `so much so that`. Current task evidence: 6 suspended archive member(s), 0 active fluency members; aggregate card state is 3 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

### 25. `a che punto siamo` — `same-sense-merge` (medium)

Candidate `d761643e8e6943dd` has normalized English evidence “where do we stand? / what's the status?”; “where we stand”; member note IDs: 1777020028251, 1777020029229, 1784424360600, 1784509109605, 1784509117728, 1784509118474. The question and embedded-clause forms both ask or state the stage of progress; the terminal question mark changes occurrence form, not sense. Proposed survivor: `a che punto siamo` / `where do we stand / where things stand`. Current task evidence: 6 suspended archive member(s), 0 active fluency members; aggregate card state is 5 reps and 0 lapses, with exact per-note/card revlog detail in the JSON manifest.

## Interpretation boundary

`same-sense-merge` identifies a proposed canonical expression-sense only; it does not merge notes, GUIDs, schedules, or revlog. `distinct-senses` preserves separate sense identities. `quarantine` blocks automatic identity resolution until the owner’s Monday skim and a reviewed stable `sense_key` decision.
