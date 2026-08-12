# Exercises2 `fancy_vocab` hostile audit

Date: 2026-08-12

Auditor: Codex, independent post-authoring review

Scope: all 76 `{de,es,fr,it,pt}_fancy_vocab_b*` notes/triage pairs, including `es_fancy_vocab_pilot_b01`

## Outcome

All 76 chunks pass after audit. Thirty-six chunks required edits, forty passed without edits, and none failed. The review covered every one of the 2,940 source/triage rows, every field of all 1,449 retained V1 cards, and all 1,491 drop rationales. The legacy `it_` item-ID prefix was treated as the expected seed artifact because language routing comes from the chunk filename.

No triage verdict changed: every edited keep remains pedagogically defensible after repair. The final corpus has no exact target-language production-headword collision between different retained source IDs, no unexplained cross-topic exact duplicate, and no mechanical-gate failure.

## Verdict table

| Chunk | Inputs | Keep | Drop | Verdict | Edited rows | Edited fields | Final gate |
|---|---:|---:|---:|---|---:|---:|---|
| `de_fancy_vocab_b01` | 40 | 18 | 22 | PASS | 0 | 0 | PASS |
| `de_fancy_vocab_b02` | 40 | 23 | 17 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `de_fancy_vocab_b03` | 40 | 21 | 19 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `de_fancy_vocab_b04` | 40 | 20 | 20 | PASS | 0 | 0 | PASS |
| `de_fancy_vocab_b05` | 40 | 18 | 22 | PASS-WITH-EDITS | 2 | 10 | PASS |
| `de_fancy_vocab_b06` | 40 | 23 | 17 | PASS | 0 | 0 | PASS |
| `de_fancy_vocab_b07` | 40 | 21 | 19 | PASS-WITH-EDITS | 5 | 7 | PASS |
| `de_fancy_vocab_b08` | 40 | 27 | 13 | PASS | 0 | 0 | PASS |
| `de_fancy_vocab_b09` | 40 | 26 | 14 | PASS-WITH-EDITS | 2 | 4 | PASS |
| `de_fancy_vocab_b10` | 40 | 25 | 15 | PASS-WITH-EDITS | 3 | 7 | PASS |
| `de_fancy_vocab_b11` | 40 | 23 | 17 | PASS | 0 | 0 | PASS |
| `de_fancy_vocab_b12` | 40 | 40 | 0 | PASS-WITH-EDITS | 10 | 34 | PASS |
| `de_fancy_vocab_b13` | 40 | 40 | 0 | PASS-WITH-EDITS | 4 | 13 | PASS |
| `de_fancy_vocab_b14` | 40 | 40 | 0 | PASS-WITH-EDITS | 7 | 32 | PASS |
| `de_fancy_vocab_b15` | 22 | 22 | 0 | PASS-WITH-EDITS | 2 | 6 | PASS |
| `es_fancy_vocab_b01` | 40 | 20 | 20 | PASS | 0 | 0 | PASS |
| `es_fancy_vocab_b02` | 40 | 25 | 15 | PASS-WITH-EDITS | 2 | 2 | PASS |
| `es_fancy_vocab_b03` | 40 | 21 | 19 | PASS-WITH-EDITS | 4 | 6 | PASS |
| `es_fancy_vocab_b04` | 40 | 20 | 20 | PASS | 0 | 0 | PASS |
| `es_fancy_vocab_b05` | 40 | 18 | 22 | PASS | 0 | 0 | PASS |
| `es_fancy_vocab_b06` | 40 | 20 | 20 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `es_fancy_vocab_b07` | 40 | 18 | 22 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `es_fancy_vocab_b08` | 40 | 23 | 17 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `es_fancy_vocab_b09` | 40 | 16 | 24 | PASS-WITH-EDITS | 2 | 2 | PASS |
| `es_fancy_vocab_b10` | 40 | 14 | 26 | PASS | 0 | 0 | PASS |
| `es_fancy_vocab_b11` | 40 | 19 | 21 | PASS | 0 | 0 | PASS |
| `es_fancy_vocab_b12` | 40 | 24 | 16 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `es_fancy_vocab_b13` | 40 | 10 | 30 | PASS-WITH-EDITS | 2 | 2 | PASS |
| `es_fancy_vocab_b14` | 40 | 4 | 36 | PASS | 0 | 0 | PASS |
| `es_fancy_vocab_b15` | 22 | 5 | 17 | PASS | 0 | 0 | PASS |
| `es_fancy_vocab_pilot_b01` | 30 | 14 | 16 | PASS | 0 | 0 | PASS |
| `fr_fancy_vocab_b01` | 40 | 18 | 22 | PASS | 0 | 0 | PASS |
| `fr_fancy_vocab_b02` | 40 | 24 | 16 | PASS | 0 | 0 | PASS |
| `fr_fancy_vocab_b03` | 40 | 20 | 20 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `fr_fancy_vocab_b04` | 40 | 22 | 18 | PASS | 0 | 0 | PASS |
| `fr_fancy_vocab_b05` | 40 | 17 | 23 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `fr_fancy_vocab_b06` | 40 | 16 | 24 | PASS | 0 | 0 | PASS |
| `fr_fancy_vocab_b07` | 40 | 21 | 19 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `fr_fancy_vocab_b08` | 40 | 25 | 15 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `fr_fancy_vocab_b09` | 40 | 15 | 25 | PASS | 0 | 0 | PASS |
| `fr_fancy_vocab_b10` | 40 | 19 | 21 | PASS-WITH-EDITS | 1 | 6 | PASS |
| `fr_fancy_vocab_b11` | 40 | 22 | 18 | PASS | 0 | 0 | PASS |
| `fr_fancy_vocab_b12` | 40 | 26 | 14 | PASS-WITH-EDITS | 3 | 12 | PASS |
| `fr_fancy_vocab_b13` | 40 | 20 | 20 | PASS | 0 | 0 | PASS |
| `fr_fancy_vocab_b14` | 40 | 7 | 33 | PASS | 0 | 0 | PASS |
| `fr_fancy_vocab_b15` | 22 | 4 | 18 | PASS | 0 | 0 | PASS |
| `it_fancy_vocab_b01` | 40 | 17 | 23 | PASS | 0 | 0 | PASS |
| `it_fancy_vocab_b02` | 40 | 22 | 18 | PASS-WITH-EDITS | 2 | 2 | PASS |
| `it_fancy_vocab_b03` | 40 | 19 | 21 | PASS | 0 | 0 | PASS |
| `it_fancy_vocab_b04` | 40 | 20 | 20 | PASS | 0 | 0 | PASS |
| `it_fancy_vocab_b05` | 40 | 16 | 24 | PASS | 0 | 0 | PASS |
| `it_fancy_vocab_b06` | 40 | 19 | 21 | PASS | 0 | 0 | PASS |
| `it_fancy_vocab_b07` | 40 | 20 | 20 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `it_fancy_vocab_b08` | 40 | 24 | 16 | PASS | 0 | 0 | PASS |
| `it_fancy_vocab_b09` | 40 | 14 | 26 | PASS | 0 | 0 | PASS |
| `it_fancy_vocab_b10` | 40 | 15 | 25 | PASS | 0 | 0 | PASS |
| `it_fancy_vocab_b11` | 40 | 20 | 20 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `it_fancy_vocab_b12` | 40 | 27 | 13 | PASS-WITH-EDITS | 2 | 8 | PASS |
| `it_fancy_vocab_b13` | 40 | 11 | 29 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `it_fancy_vocab_b14` | 40 | 6 | 34 | PASS | 0 | 0 | PASS |
| `it_fancy_vocab_b15` | 22 | 5 | 17 | PASS | 0 | 0 | PASS |
| `pt_fancy_vocab_b01` | 40 | 22 | 18 | PASS | 0 | 0 | PASS |
| `pt_fancy_vocab_b02` | 40 | 22 | 18 | PASS-WITH-EDITS | 1 | 5 | PASS |
| `pt_fancy_vocab_b03` | 40 | 21 | 19 | PASS-WITH-EDITS | 3 | 8 | PASS |
| `pt_fancy_vocab_b04` | 40 | 20 | 20 | PASS | 0 | 0 | PASS |
| `pt_fancy_vocab_b05` | 40 | 14 | 26 | PASS | 0 | 0 | PASS |
| `pt_fancy_vocab_b06` | 40 | 22 | 18 | PASS-WITH-EDITS | 2 | 6 | PASS |
| `pt_fancy_vocab_b07` | 40 | 19 | 21 | PASS | 0 | 0 | PASS |
| `pt_fancy_vocab_b08` | 40 | 24 | 16 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `pt_fancy_vocab_b09` | 40 | 17 | 23 | PASS | 0 | 0 | PASS |
| `pt_fancy_vocab_b10` | 40 | 14 | 26 | PASS | 0 | 0 | PASS |
| `pt_fancy_vocab_b11` | 40 | 19 | 21 | PASS-WITH-EDITS | 2 | 2 | PASS |
| `pt_fancy_vocab_b12` | 40 | 28 | 12 | PASS | 0 | 0 | PASS |
| `pt_fancy_vocab_b13` | 40 | 10 | 30 | PASS-WITH-EDITS | 1 | 1 | PASS |
| `pt_fancy_vocab_b14` | 40 | 4 | 36 | PASS | 0 | 0 | PASS |
| `pt_fancy_vocab_b15` | 22 | 4 | 18 | PASS-WITH-EDITS | 1 | 7 | PASS |
| **Total** | **2,940** | **1,449** | **1,491** | **76 pass** | **77** | **196** | **76/76** |

“Edited fields” counts changed JSON fields. No triage file changed. When the ledger below says `example_tl + cloze`, both fields changed from the displayed old target sentence to the displayed new target sentence; the cloze masks were regenerated over the corresponding drilled material. Cloze-only entries print the exact masked strings.

## Audit method and evidence

- Applied all six defect classes in `CODEX_X2_WAVE_AUDIT.md`. Repetition review was item by item across all 1,449 retained cards, not sampled.
- Checked all 2,940 source rows against triage, then checked every retained object against the exact V1 vocabulary schema in `EXERCISES2_VOCAB_ADDENDUM.md`: production headword, substitutable alternatives, register, interference trap, 18–30-word professional example, faithful translation, exact cloze reduction, and provenance note.
- Read all 1,491 drop reasons. The 20 Fancy Vocabulary members in `exercises2_cross_topic_exact_duplicates.json` are dropped in every full language estate; Spanish pilot rows 098 and 099 are also dropped. `To clarify` remains owned by Connecting Ideas. No duplicate-policy exception or triage change was needed.
- The Spanish pilot overlaps the full Spanish batch on five retained source IDs (002, 005, 006, 007, 010). Those are the same source records in two commission artifacts, not different-item repetition; all other exact example-duplicate checks were clean.
- Compared retained production headwords vertically within every language. Fifteen exact answer collisions between different source IDs were repaired; the final collision count is zero.
- Reviewed all 1,449 traps. Four intentionally empty traps—Spanish 031, Spanish pilot 489, French 088, and Portuguese 031—were retained because no genuine five-language interference risk remains; inventing one would violate the addendum.
- Verified every cloze reduces exactly to `example_tl`. Seventeen clozes exposed fixed government or another indispensable part of the authored production frame and were repaired; all clozes affected by sentence/headword edits were regenerated in sync.
- Re-scanned all target and English examples for duplicate sentences, repeated multiword starters, boilerplate propositions, exact content-word repetition, and same-stem repetition. Remaining hits are deliberate constructions or contrasts such as “end to end,” “sector by sector,” `tantôt … tantôt`, and “long-term/short term.”
- Ran `.venv/bin/python tools/x2_batch_gate.py <chunk>` for every edited chunk until green, then across all 76 chunks. Final result: `76/76 chunks pass the mechanical gate`.

## Complete edit ledger

The ledger is field-exact. Unlisted fields on each item were unchanged.

### German

- `de_fancy_vocab_b02` 052, `example_en`: `Advertising networks profile users from seemingly insignificant location signals even though those users neither consented to the analysis nor can understand its logic.` → `Advertising networks profile users from seemingly insignificant location signals even though they neither consented to the analysis nor can understand its logic.`
- `de_fancy_vocab_b03` 089, `example_en`: `The platform deviated from its own moderation standard without public justification as soon as government agencies demanded the removal of content critical of the government.` → `The platform deviated from its own moderation standard without public justification as soon as state agencies demanded the removal of content critical of the government.`
- `de_fancy_vocab_b05` 161:
  - `example_tl + cloze`: `Die Geschäftemacherei mit dringend benötigten Schutzgütern zeigte, wie schnell unregulierte Plattformen gesellschaftliche Krisen in lukrative private Renditechancen verwandeln.` → `Die Geschäftemacherei mit dringend benötigten Schutzgütern zeigte, wie schnell unregulierte Plattformen gesellschaftliche Krisen zur privaten Bereicherung auf Kosten der Allgemeinheit nutzen.`
  - `example_en`: `The profiteering from urgently needed protective goods showed how quickly unregulated platforms turn social crises into lucrative private opportunities for profit.` → `Profiteering from urgently needed protective goods showed how quickly unregulated platforms exploit social crises for private enrichment at the public’s expense.`
- `de_fancy_vocab_b05` 197:
  - `tl`: `ausbeuterisch` → `räuberisch`; `alts`: `["räuberisch"]` → `["ausbeuterisch"]`.
  - `register`: `Ausbeuterisch is strongly critical but idiomatic for contracts and business models; räuberisch is more rhetorical and occurs in selected economic collocations.` → `Strongly rhetorical and condemnatory for unscrupulous business practices; ausbeuterisch is less metaphorical and foregrounds exploitation directly.`
  - `example_tl + cloze`: `Ausbeuterische Vertragsbedingungen zwingen kleine Anbieter, wachsende Datenbestände abzutreten, während die Plattform sämtliche Haftungsrisiken bei ihren formal unabhängigen Partnern belässt.` → `Räuberische Geschäftspraktiken zwingen kleine Anbieter, wachsende Datenbestände abzutreten, während die Plattform sämtliche Haftungsrisiken bei ihren formal unabhängigen Partnern belässt.`
  - `example_en`: `Predatory contract terms force small providers to surrender growing data holdings while the platform leaves all liability risks with its formally independent partners.` → `Predatory business practices force small providers to surrender growing data holdings while the platform leaves all liability risks with its formally independent partners.`
  - `note`: `Materially improves old_back for the selected business-conduct sense; the literal metaphor is retained only as a more rhetorical alternative. Self-review: replaced an over-specific pricing compound with the established plural Verdrängungspreise.` → `Materially improves old_back for the selected business-conduct sense. Self-review keeps the rhetorical metaphor as the main answer and records the less metaphorical ausbeuterisch as an alternative.`
- `de_fancy_vocab_b07` 250, `example_en`: `Advanced semiconductors have become a strategic bottleneck because their development requires global knowledge networks while the most advanced manufacturing remains highly concentrated geographically.` → `Leading-edge semiconductors have become a strategic bottleneck because their development requires global knowledge networks while the most advanced manufacturing remains highly concentrated geographically.`
- `de_fancy_vocab_b07` 259, `example_en`: `Quantum computing promises advantages for selected optimization problems, but many policy strategies confuse long-term research potential with computing power available in the short term.` → `Quantum computing promises advantages for selected optimization problems, but many policy strategies confuse long-term research potential with processing power available in the short term.`
- `de_fancy_vocab_b07` 262:
  - `example_tl + cloze`: `Öffentliche Ausgaben für Forschung und Entwicklung fördern Innovation nur dann nachhaltig, wenn Universitäten Ergebnisse teilen und kleine Unternehmen Zugang zu Forschungsinfrastrukturen erhalten.` → `Öffentliche Ausgaben für Forschung und Entwicklung fördern Innovation nur dann nachhaltig, wenn Universitäten Ergebnisse teilen und kleine Unternehmen Zugang zu gemeinsamen Infrastrukturen erhalten.`
  - `example_en`: `Public spending on research and development promotes innovation sustainably only when universities share results and small companies gain access to research infrastructure.` → `Public spending on research and development promotes innovation sustainably only when universities share results and small companies gain access to shared infrastructure.`
- `de_fancy_vocab_b07` 266, `example_en`: `Effective data privacy requires more than consent banners: users must be able to see what data is collected, combined, and used for automated decisions.` → `Effective data privacy requires more than consent banners: users must be able to see what information is collected, combined, and used for automated decisions.`
- `de_fancy_vocab_b07` 270, `example_en`: `Cloud computing can shift computing power and data storage to external providers, allowing public administrations to gain economies of scale while creating new dependencies and oversight problems.` → `Cloud computing can shift processing capacity and data storage to external providers, allowing public administrations to gain economies of scale while creating new dependencies and oversight problems.`
- `de_fancy_vocab_b09` 357:
  - `example_tl + cloze`: `Offene Standards machen Systeme interoperabel, können sie aber angreifbar machen, wenn Sicherheitsupdates nicht rechtzeitig bereitgestellt und geprüft werden.` → `Offene Standards fördern die Interoperabilität, können Systeme aber angreifbar machen, wenn Sicherheitsupdates nicht rechtzeitig bereitgestellt und geprüft werden.`
  - `example_en`: `Open standards make systems interoperable but can make them vulnerable when security updates are not provided and tested promptly.` → `Open standards promote interoperability but can leave systems vulnerable when security updates are not provided and tested promptly.`
- `de_fancy_vocab_b09` 360, `example_en`: `The interconnected supply chains rapidly transmit political conflicts to prices, jobs, and security of supply in distant regions.` → `The interconnected supply chains rapidly transmit political conflicts to prices, jobs, and access to essential goods in distant regions.`
- `de_fancy_vocab_b10` 371, `example_en`: `Collaborative development models distribute responsibility among teams without automatically making strategic decision-making more democratic or transparent to users and the public.` → `Collaborative development models distribute responsibility among teams without automatically making strategic decisions more democratic or transparent to users and the public.`
- `de_fancy_vocab_b10` 373:
  - `example_tl + cloze`: `Konsumtive Staatsausgaben finanzieren laufenden Konsum statt produktiver Investitionen und können dadurch langfristiges Wachstum und öffentliche Resilienz dauerhaft schwächen.` → `Konsumtive Staatsausgaben decken laufenden Bedarf, statt produktive Investitionen zu finanzieren, und können dadurch langfristiges Wachstum sowie institutionelle Resilienz schwächen.`
  - `example_en`: `Consumption-oriented public spending finances current consumption instead of productive investment and can thereby weaken long-term growth and public resilience.` → `Consumption-oriented public spending covers current needs rather than financing productive investment and can thereby weaken long-term growth and institutional resilience.`
- `de_fancy_vocab_b10` 385:
  - `example_tl + cloze`: `Nach der Datenschutzverletzung musste der Konzern offenlegen, welche Kundendaten betroffen waren und warum die Warnsysteme zuvor versagt hatten.` → `Nach der Datenschutzverletzung musste der Konzern offenlegen, welche Kundeninformationen betroffen waren und warum die Warnsysteme zuvor versagt hatten.`
  - `example_en`: `After the data breach, the corporation had to disclose which customer data were affected and why the warning systems had previously failed.` → `After the data breach, the corporation had to disclose which customer records were affected and why the warning systems had previously failed.`
- `de_fancy_vocab_b12` 446:
  - `example_tl + cloze`: `Mehrere unabhängige Zeugen behaupten, dass der Sicherheitsdienst oppositionelle Gruppen vor der umkämpften Wahl offenbar systematisch und gezielt eingeschüchtert habe.` → `Mehrere unabhängige Zeugen behaupten, dass der Sicherheitsdienst oppositionelle Gruppen vor der umkämpften Wahl systematisch und gezielt eingeschüchtert habe.`
  - `example_en`: `Several independent witnesses allege that the security service apparently systematically and deliberately intimidated opposition groups before the contested election.` → `Several independent witnesses allege that the security service systematically and deliberately intimidated opposition groups before the contested election.`
- `de_fancy_vocab_b12` 449:
  - `tl`: `etwas umgehen` → `etwas unterlaufen`; `alts`: `["etwas umschiffen", "etwas aushebeln"]` → `["etwas umgehen", "etwas aushebeln"]`.
  - `register`: `Formal policy, legal and technical usage for avoiding a rule, obstacle or restriction without confronting it directly.` → `Formal policy and legal usage for frustrating or evading a rule, safeguard or restriction without confronting it directly.`
  - `trap`: `Umgehen is separable when it means circumvent: Die Firma umgeht die Vorschrift; the non-separable pronunciation means handle or deal with.` → `Unterlaufen is inseparable in this sense, with unterläuft, unterlief and hat unterlaufen; the separable literal verb unter etwas durchlaufen follows a different pattern.`
  - `example_tl + cloze`: `Die Plattform umging die Exportkontrollen, indem sie die betroffenen Komponenten heimlich und wiederholt über mehrere ausländische Tochtergesellschaften weiterverkaufte.` → `Die Plattform unterlief die Exportkontrollen, indem sie die betroffenen Komponenten heimlich und wiederholt über mehrere ausländische Tochtergesellschaften weiterverkaufte.`
  - `note`: `The old gloss Umschiffen is possible but marked and often figurative; the note selects the standard policy verb umgehen and its past-tense form.` → `The old gloss Umschiffen is possible but marked and often figurative; self-review selects unterlaufen to teach a distinct formal policy verb and its strong past-tense form.`
- `de_fancy_vocab_b12` 451:
  - `example_tl + cloze`: `Neue Satellitenbilder erhärten den Verdacht, dass die Miliz ihre Stellungen nahe der Grenze offenbar seit Monaten weiter ausbaut.` → `Neue hochauflösende Satellitenbilder erhärten den Verdacht, dass die Miliz ihre Stellungen nahe der Grenze seit Monaten weiter ausbaut.`
  - `example_en`: `New satellite images corroborate the suspicion that the militia has apparently continued expanding its positions near the border for months.` → `New high-resolution satellite images corroborate the suspicion that the militia has continued expanding its positions near the border for months.`
- `de_fancy_vocab_b12` 453, `cloze`: `Aus den Haushaltsdaten {{c1::leitet die Studie ab}}, dass die Reform vor allem bereits privilegierte Regionen überproportional weiter begünstigt.` → `{{c1::Aus}} den Haushaltsdaten {{c1::leitet die Studie ab}}, dass die Reform vor allem bereits privilegierte Regionen überproportional weiter begünstigt.`
- `de_fancy_vocab_b12` 454:
  - `example_tl + cloze`: `Die Abgeordnete meldete Bedenken gegen den Gesetzentwurf an, weil seine Kontrollbefugnisse dadurch demokratische Schutzmechanismen unnötig weit aushöhlen könnten.` → `Die Abgeordnete meldete Bedenken gegen den Gesetzentwurf an, weil seine Kontrollbefugnisse grundlegende demokratische Schutzmechanismen unnötig weit aushöhlen könnten.`
  - `example_en`: `The MP voiced objections to the bill because its oversight powers could thereby erode democratic safeguards unnecessarily far.` → `The MP voiced objections to the bill because its oversight powers could erode fundamental democratic safeguards unnecessarily far.`
- `de_fancy_vocab_b12` 458:
  - `example_tl + cloze`: `Die Redaktion verbreitete die Recherche über mehrere regionale Partner, nachdem sie die wichtigsten Quellen sorgfältig rechtlich abgesichert hatte.` → `Die Redaktion verbreitete die Recherche über mehrere regionale Partner, nachdem sie die Veröffentlichung sorgfältig rechtlich geprüft und ihre wichtigsten Quellen geschützt hatte.`
  - `example_en`: `The editorial team disseminated the investigation through several regional partners after carefully securing its key sources legally.` → `The editorial team disseminated the investigation through several regional partners after carefully reviewing the publication for legal risk and protecting its key sources.`
- `de_fancy_vocab_b12` 464, `cloze`: `Aus den geleakten Protokollen ließ sich {{c1::herauslesen}}, dass die Verhandlungen längst vor der offiziellen Ankündigung intern gescheitert waren.` → `{{c1::Aus}} den geleakten Protokollen ließ sich {{c1::herauslesen}}, dass die Verhandlungen längst vor der offiziellen Ankündigung intern gescheitert waren.`
- `de_fancy_vocab_b12` 467:
  - `example_tl + cloze`: `Die Propaganda prägte einer ganzen Generation ein, dass staatliche Loyalität wichtiger als unabhängiges Denken und private Zweifel sei.` → `Die Propaganda prägte einer ganzen Generation die Überzeugung ein, dass staatliche Loyalität wichtiger als unabhängiges Denken und private Zweifel sei.`
  - `example_en`: `The propaganda inculcated in an entire generation that loyalty to the state mattered more than independent thought and private doubts.` → `The propaganda inculcated in an entire generation the belief that loyalty to the state mattered more than independent thought and private doubts.`
  - Exact `cloze`: `Die Propaganda {{c1::prägte einer ganzen Generation ein}}, dass staatliche Loyalität wichtiger als unabhängiges Denken und private Zweifel sei.` → `Die Propaganda {{c1::prägte}} einer ganzen Generation die Überzeugung {{c1::ein}}, dass staatliche Loyalität wichtiger als unabhängiges Denken und private Zweifel sei.`
- `de_fancy_vocab_b12` 473:
  - `tl`: `etwas postulieren` → `davon ausgehen, dass`; `alts`: `["etwas als gegeben annehmen", "etwas voraussetzen"]` → `["etwas postulieren", "etwas als gegeben annehmen"]`.
  - `register`: `Formal academic and theoretical usage for proposing a premise or explanatory claim as a basis for reasoning.` → `Neutral-formal analytical construction for treating a proposition as a premise; postulieren is the more technical academic alternative.`
  - `trap`: `Postulieren is a legitimate German academic loanword, but it does not mean prove; the proposition remains a premise or hypothesis.` → `Davon ausgehen is separable in the clause frame geht davon aus, dass; it presents an assumption and does not mean that the proposition has been proved.`
  - `example_tl + cloze`: `Die Studie postuliert, dass automatisierte Rankings bestehende soziale Vorurteile verstärken, selbst wenn ihre Entwickler keine politische Absicht verfolgen.` → `Die Studie geht davon aus, dass automatisierte Rankings bestehende soziale Vorurteile verstärken, selbst wenn ihre Entwickler keine politische Absicht verfolgen.`
  - `note`: `The old gloss Postulieren is usable but leaves the register implicit; self-review confirms the academic premise-setting sense and adds the dass-clause pattern.` → `The old gloss Postulieren is usable but leaves the register implicit; self-review supplies the productive davon ausgehen, dass frame as a distinct, natural premise-setting construction.`
- `de_fancy_vocab_b12` 478:
  - `example_tl + cloze`: `Der Sprecher wiederholte seine Forderung nach unabhängigen Kontrollen, nachdem die erste Untersuchung zentrale Interessenkonflikte offenbar bewusst übergangen hatte.` → `Der Sprecher wiederholte seine Forderung nach unabhängigen Kontrollen, nachdem die erste Untersuchung mehrere zentrale Interessenkonflikte nachweislich übergangen hatte.`
  - `example_en`: `The spokesperson reiterated the demand for independent oversight after the first investigation had apparently deliberately overlooked key conflicts of interest.` → `The spokesperson reiterated the demand for independent oversight after the first investigation had demonstrably ignored several key conflicts of interest.`
- `de_fancy_vocab_b13` 483:
  - `example_tl + cloze`: `Aus den widersprüchlichen Aussagen vermutete die Analystin, dass der Rücktritt auf internen Druck und nicht auf gesundheitliche Gründe zurückzuführen war.` → `Angesichts der widersprüchlichen Aussagen vermutete die Analystin, dass der Rücktritt auf internen Druck und nicht auf gesundheitliche Gründe zurückzuführen war.`
  - `example_en`: `From the contradictory statements, the analyst surmised that the resignation was due to internal pressure rather than health reasons.` → `Given the contradictory statements, the analyst surmised that the resignation was due to internal pressure rather than health reasons.`
- `de_fancy_vocab_b13` 492:
  - `tl`: `die These` → `die strittige Behauptung`; `alts`: `["die Behauptung"]` → `["die These"]`.
  - `register`: `Formal argumentative usage for a claim or position advanced in a dispute, paper or public controversy.` → `Formal argumentative usage for a claim or position advanced in a dispute, paper or public controversy; strittig makes its contested status explicit.`
  - `trap`: `Contention foregrounds a claim that is open to dispute; These is more structured than Behauptung, while Streit is the conflict itself.` → `Contention foregrounds a claim that is open to dispute; These can be more structured, while Streit names the conflict rather than the proposition.`
  - `example_tl + cloze`: `Die strittige These der Studie, Sanktionen würden die Regierung rasch zum Einlenken bewegen, unterschätzt deren Fähigkeit zur wirtschaftlichen Anpassung.` → `Die strittige Behauptung der Studie, Sanktionen würden die Regierung rasch zum Einlenken bewegen, unterschätzt deren Fähigkeit zur wirtschaftlichen Anpassung.`
  - `example_en`: `The study's contentious thesis that sanctions would quickly bring the government to the negotiating table underestimates its capacity for economic adaptation.` → `The study’s contention that sanctions would quickly bring the government to the negotiating table underestimates its capacity for economic adaptation.`
  - `note`: `The old gloss Die Behauptung is usable but misses the organized argumentative position; self-review retained this card as distinct from assertion.` → `The old gloss Die Behauptung is usable but underspecified; self-review adds strittig to preserve the contested force and keep this production answer distinct from thesis.`
- `de_fancy_vocab_b13` 494, `example_en`: `From the contradictory figures, the commission drew the deduction that the reported savings were largely only accounting shifts.` → `From the contradictory figures, the commission drew the conclusion that the reported savings were largely only accounting shifts.`
- `de_fancy_vocab_b13` 517, `example_en`: `The theory of the digital public sphere systematically loses explanatory power when it ignores economic concentration of power and state regulation alike.` → `The theory of the digital public sphere systematically loses explanatory force when it ignores economic concentration of power and state regulation alike.`
- `de_fancy_vocab_b14` 525:
  - `tl`: `die Erläuterung` → `die eingehende Interpretation`; `alts`: `["die Erklärung", "die Auslegung"]` → `["die detaillierte Textdeutung"]`.
  - `register`: `Formal academic and literary usage for a detailed explanation or interpretation of a difficult text, idea or passage.` → `Formal academic and literary usage for a close, detailed interpretation of a difficult text, idea or passage.`
  - `trap`: `Explication is a close explanation, not simply a translation; Erläuterung is more precise here than the broad, everyday Erklärung.` → `An explication develops a close interpretation rather than merely translating or briefly paraphrasing a text; Erläuterung instead foregrounds a clarifying explanation.`
  - `example_tl + cloze`: `Die Erläuterung des Leitartikels für ein breiteres Publikum zeigt, wie seine scheinbar neutrale Sprache stillschweigend eine bestimmte geopolitische Ordnung voraussetzt.` → `Die eingehende Interpretation des Leitartikels zeigt einem breiteren Publikum, wie seine scheinbar neutrale Sprache stillschweigend eine bestimmte geopolitische Ordnung voraussetzt.`
  - `example_en`: `The explication of the editorial for a broader audience shows how its seemingly neutral language tacitly presupposes a particular geopolitical order.` → `The explication of the editorial shows a broader audience how its seemingly neutral language tacitly presupposes a particular geopolitical order.`
  - `note`: `The old gloss is correct; self-review fixed the academic-literary sense and avoided treating explication as a simple synonym for translation.` → `The old gloss captures the explanatory sense; self-review selects an explicit close-reading construction to provide a distinct, production-worthy answer.`
- `de_fancy_vocab_b14` 534:
  - `example_tl + cloze`: `Die Validierung des Prognosemodells unter realen Bedingungen scheiterte, weil es bei veränderten Marktbedingungen systematisch falsche Risiken als vernachlässigbar einstufte.` → `Die Validierung des Prognosemodells im Praxiseinsatz scheiterte, weil es unter veränderten Marktbedingungen tatsächliche Risiken systematisch fälschlich als vernachlässigbar einstufte.`
  - `example_en`: `The validation of the forecasting model under real conditions failed because it systematically classified false risks as negligible under changed market conditions.` → `Validation of the forecasting model in operational use failed because, under changed market conditions, it systematically misclassified real risks as negligible.`
- `de_fancy_vocab_b14` 535:
  - `tl`: `das Urteil` → `der Richterspruch`; `alts`: `["der Richterspruch", "die Entscheidung"]` → `["das Urteil", "die Entscheidung"]`.
  - `register`: `Legal usage for the formal decision delivered by a court or jury; figurative media use is also possible.` → `Formal legal and journalistic usage for a judge’s pronounced decision; Urteil is the more neutral general legal term.`
  - `trap`: `Urteil is the standard legal verdict; Entscheidung is broader, and Richterspruch emphasizes the judge's pronouncement rather than the legal decision itself.` → `Richterspruch specifically foregrounds the judge’s pronouncement and is unsuitable for a jury verdict; Entscheidung is broader than either legal noun.`
  - `example_tl + cloze`: `Das Urteil gegen den Whistleblower löste internationale Kritik aus, weil das Gericht zentrale Beweise unter Ausschluss der Öffentlichkeit bewertete.` → `Der Richterspruch gegen den Whistleblower löste internationale Kritik aus, weil das Gericht zentrale Beweise unter Ausschluss der Öffentlichkeit bewertete.`
  - `note`: `The old gloss is exact; the source's final period is preserved in en, while the target headword gives the standard legal noun.` → `The old gloss is exact; self-review selects the more marked judicial-pronouncement sense to provide a distinct production answer from judgment.`
- `de_fancy_vocab_b14` 537:
  - `example_tl + cloze`: `Eine analytische Betrachtung der Plattformökonomie muss Geschäftsmodelle, Machtverhältnisse und regulatorische Anreize im jeweiligen politischen Kontext gemeinsam systematisch untersuchen.` → `Eine analytische Betrachtung der Plattformökonomie muss Geschäftsmodelle, Machtverhältnisse und regulatorische Anreize systematisch in ihrem Zusammenspiel und jeweiligen politischen Kontext untersuchen.`
  - `example_en`: `An analytical examination of the platform economy must systematically examine business models, power relations and regulatory incentives together within their respective political context.` → `An analytical study of the platform economy must systematically consider business models, power relations, and regulatory incentives in their interaction and specific political context.`
- `de_fancy_vocab_b14` 541:
  - `tl`: `überzeugend` → `einleuchtend`; `alts`: `[]` → `["überzeugend"]`.
  - `register`: `Neutral-formal argumentative and public-facing usage for something that persuades through its reasoning, evidence or presentation.` → `Neutral-formal argumentative usage for reasoning or an explanation that is readily understandable and convincing.`
  - `trap`: `Überzeugend means persuasive, not necessarily proven; glaubwürdig describes credibility, while plausibel may only mean compatible with the facts.` → `Einleuchtend describes reasoning that makes sense, not necessarily a claim that has been proved; glaubwürdig instead concerns credibility.`
  - `example_tl + cloze`: `Die überzeugende Gegenanalyse zeigt im Detail, dass die behaupteten Effizienzgewinne vor allem aus einer selektiven Auswahl der Vergleichsdaten stammen.` → `Die einleuchtende Gegenanalyse zeigt im Detail, dass die behaupteten Effizienzgewinne vor allem aus einer selektiven Auswahl der Vergleichsdaten stammen.`
  - `note`: `The old gloss is exact; self-review kept the ordinary adjective and clarified that persuasion does not equal proof.` → `The old gloss is exact; self-review selects the closely related but distinct einleuchtend and clarifies that intelligible persuasion does not equal proof.`
- `de_fancy_vocab_b14` 542, `example_en`: `The counterintuitive result is explained by stricter moderation removing the most visible posts, but not the underlying networks.` → `The counterintuitive result arises because stricter moderation removes the most visible posts but not the underlying networks.`
- `de_fancy_vocab_b14` 548:
  - `example_tl + cloze`: `Die empirische Studie widerlegt die Annahme, dass automatisierte Empfehlungen politisch neutrale Informationen unabhängig von bestehenden Vorurteilen in der Praxis verbreiten.` → `Die empirische Studie widerlegt die Annahme, dass automatisierte Empfehlungen in der Praxis politisch neutrale Informationen verbreiten, ohne bestehende Vorurteile zu reproduzieren.`
  - `example_en`: `The empirical study refutes the assumption that automated recommendations distribute politically neutral information independently of existing biases in practice.` → `The empirical study refutes the assumption that automated recommendations distribute politically neutral information in practice without reproducing existing biases.`
- `de_fancy_vocab_b15` 561:
  - `example_tl + cloze`: `Die scharfsinnige Analyse der Plattformökonomie zeigt, dass scheinbar kostenlose Dienste ihre Nutzer nicht als Kunden, sondern als verwertbare Verhaltensdaten behandeln.` → `Die scharfsinnige Analyse der Plattformökonomie zeigt, dass scheinbar kostenlose Dienste ihre Nutzer nicht als Kunden, sondern als Quellen verwertbarer Verhaltensdaten behandeln.`
  - `example_en`: `The incisive analysis of the platform economy shows that seemingly free services treat their users not as customers but as exploitable behavioral data.` → `The incisive analysis of the platform economy shows that seemingly free services treat their users not as customers but as sources of exploitable behavioral data.`
- `de_fancy_vocab_b15` 581:
  - `example_tl + cloze`: `Eine unvoreingenommene Untersuchung muss auch jene Zeugenaussagen berücksichtigen, die der eigenen politischen Vorannahme widersprechen und den Bericht erschweren.` → `Eine unvoreingenommene Untersuchung muss auch jene Zeugenaussagen berücksichtigen, die den eigenen politischen Vorannahmen widersprechen und eine eindeutige Schlussfolgerung erschweren.`
  - `example_en`: `An unbiased investigation must also consider those witness statements that contradict its own political presumption and make the report more difficult.` → `An unbiased investigation must also consider witness statements that contradict its own political assumptions and complicate a clear-cut conclusion.`

### Spanish

- `es_fancy_vocab_b02` 051, `example_en`: `The new framework restricts platforms' access to certain public data, but it maintains exceptions for research in the public interest.` → `The new framework restricts platforms’ access to certain government data, but it maintains exceptions for research in the public interest.`
- `es_fancy_vocab_b02` 062, `cloze`: `La auditoría {{c1::compara}} las prácticas de moderación de la plataforma con un referente europeo que publica criterios y resultados verificables.` → `La auditoría {{c1::compara}} las prácticas de moderación de la plataforma {{c1::con un referente}} europeo que publica criterios y resultados verificables.`
- `es_fancy_vocab_b03` 084, `cloze`: `El documental {{c1::yuxtapone}} las promesas públicas del grupo a sus auditorías internas para revelar la distancia entre discurso corporativo y práctica regulatoria.` → `El documental {{c1::yuxtapone}} las promesas públicas del grupo {{c1::a}} sus auditorías internas para revelar la distancia entre discurso corporativo y práctica regulatoria.`
- `es_fancy_vocab_b03` 087, `cloze`: `La nueva norma obliga a {{c1::interconectar}} los registros públicos con sistemas de verificación, ampliando la trazabilidad sin resolver quién controla esos cruces.` → `La nueva norma obliga a {{c1::interconectar}} los registros públicos {{c1::con}} sistemas de verificación, ampliando la trazabilidad sin resolver quién controla esos cruces.`
- `es_fancy_vocab_b03` 091:
  - `tl`: `tener eco en algo o alguien` → `tener eco entre un público`; `alts`: `["encontrar eco en algo o alguien"]` → `["encontrar eco entre un público"]`.
  - `cloze`: `La denuncia {{c1::tuvo eco}} entre los trabajadores porque vinculaba la precariedad cotidiana con decisiones financieras tomadas lejos de la redacción.` → `La denuncia {{c1::tuvo eco entre}} los trabajadores porque vinculaba la precariedad cotidiana con decisiones financieras tomadas lejos de la redacción.`
- `es_fancy_vocab_b03` 118, `example_en`: `Interoperability between messaging services would allow users to change providers without losing contacts, histories or the ability to communicate with other users.` → `Interoperability between messaging services would allow users to change providers without losing contacts, histories or the ability to communicate with others.`
- `es_fancy_vocab_b06` 211, `example_en`: `Market access was made contingent on compliance with independent audits, not on the voluntary promises the company made every quarter.` → `Market access became contingent on compliance with independent audits, not on the voluntary promises the company made every quarter.`
- `es_fancy_vocab_b07` 266, `example_en`: `Data privacy requires limiting information collection, even when each user has formally accepted an extensive privacy policy.` → `Data privacy requires limiting information collection, even when each user has formally accepted an extensive policy governing personal information.`
- `es_fancy_vocab_b08` 307, `example_en`: `Third-party logistics (3PL) made it possible to enter new markets without building warehouses, although it made delays harder to monitor and returns harder to manage.` → `Third-party logistics (3PL) enabled entry into new markets without building warehouses, although it complicated monitoring delays and managing returns.`
- `es_fancy_vocab_b09` 327, `cloze`: `El sistema {{c1::discriminaba}} a solicitantes por su código postal, pues la variable territorial reproducía desigualdades que el proveedor nunca había evaluado.` → `El sistema {{c1::discriminaba}} {{c1::a}} solicitantes {{c1::por}} su código postal, pues la variable territorial reproducía desigualdades que el proveedor nunca había evaluado.`
- `es_fancy_vocab_b09` 329, `cloze`: `Las empresas europeas {{c1::compiten}} con conglomerados asiáticos por contratos públicos, pero carecen del capital paciente necesario para sostener proyectos estratégicos.` → `Las empresas europeas {{c1::compiten}} {{c1::con}} conglomerados asiáticos {{c1::por}} contratos públicos, pero carecen del capital paciente necesario para sostener proyectos estratégicos.`
- `es_fancy_vocab_b12` 468, `cloze`: `Un gran jurado {{c1::acusó formalmente}} al exdirectivo de fraude electrónico y conspiración por ocultar pagos destinados a funcionarios extranjeros.` → `Un gran jurado {{c1::acusó formalmente}} {{c1::al}} exdirectivo {{c1::de}} fraude electrónico y conspiración por ocultar pagos destinados a funcionarios extranjeros.`
- `es_fancy_vocab_b13` 482, `cloze`: `La empresa no pudo {{c1::fundamentar}} su acusación con pruebas verificables, pese a que había repetido la misma versión ante tres comisiones parlamentarias.` → `La empresa no pudo {{c1::fundamentar}} su acusación {{c1::con pruebas}} verificables, pese a que había repetido la misma versión ante tres comisiones parlamentarias.`
- `es_fancy_vocab_b13` 487, `cloze`: `La campaña {{c1::demonizó}} a las organizaciones humanitarias, presentándolas como cómplices de las redes criminales sin aportar pruebas de esa colaboración.` → `La campaña {{c1::demonizó}} {{c1::a}} las organizaciones humanitarias, presentándolas como cómplices de las redes criminales sin aportar pruebas de esa colaboración.`

### French

- `fr_fancy_vocab_b03` 118, `example_en`: `The regulation requires interoperability among dominant messaging services so users can communicate across services without abandoning their contacts or histories.` → `The regulation requires interoperability among dominant messaging platforms so users can communicate across services without abandoning their contacts or histories.`
- `fr_fancy_vocab_b05` 178, `example_en`: `Open-source software allows researchers to audit the model, but this transparency guarantees neither its security nor open governance.` → `Open-source software allows researchers to audit the model, but this transparency guarantees neither its security nor participatory governance.`
- `fr_fancy_vocab_b07` 266, `example_en`: `Data privacy requires limiting collection even when the user has accepted a privacy policy written in obscure language.` → `Data privacy requires limiting collection even when the user has accepted a policy governing personal information written in obscure language.`
- `fr_fancy_vocab_b08` 305, `example_en`: `Just-in-time production reduces intermediate inventories but turns every port delay into an immediate threat to the continuity of industrial production.` → `Just-in-time methods reduce intermediate inventories but turn every port delay into an immediate threat to the continuity of industrial production.`
- `fr_fancy_vocab_b10` 377:
  - `tl`: `la réglementation` → `la régulation`.
  - `register`: `Neutral-formal policy noun for a body or framework of binding rules; common in legal and regulatory analysis.` → `Neutral-formal policy noun for the process and institutional mechanisms used to steer a sector or market.`
  - `trap`: `Un règlement is a particular rule or legal instrument, while régulation often foregrounds the process of steering a sector rather than the rules themselves.` → `La réglementation names the body of binding rules, while un règlement is a particular legal instrument; régulation foregrounds the governing process rather than the rules themselves.`
  - `example_tl + cloze`: `La réglementation sur les services numériques impose des obligations particulières aux grandes plateformes, sans interdire pour autant tous les modèles publicitaires ciblés.` → `La régulation des services numériques impose un contrôle continu aux grandes plateformes, sans interdire pour autant tous les modèles publicitaires ciblés.`
  - `note`: `Materially replaces old_back le règlement, which selects an individual instrument rather than the regulatory framework demonstrated here.` → `Materially replaces old_back le règlement, which selects an individual instrument; self-review fixes the sector-steering sense to keep the item distinct from réglementation.`
- `fr_fancy_vocab_b12` 446, `example_en`: `The company alleges that biometric data collection improves security, but it has published no data that would allow the claim to be verified.` → `The company alleges that biometric-data collection improves security, but it has published no evidence allowing the claim to be verified.`
- `fr_fancy_vocab_b12` 447:
  - `tl`: `étayer` → `renforcer`; `alts`: `["renforcer"]` → `["étayer"]`.
  - `example_tl + cloze`: `De nouvelles données indépendantes étayent l’argument selon lequel la transparence publicitaire réduit les abus sans compromettre le financement des médias.` → `De nouvelles données indépendantes renforcent l’argument selon lequel la transparence publicitaire réduit les abus sans compromettre le financement des médias.`
- `fr_fancy_vocab_b12` 449:
  - `tl`: `contourner` → `éluder`; `alts`: `[]` → `["contourner"]`.
  - `register`: `Neutral-formal verb for deliberately finding a way around a rule, safeguard, restriction or obstacle.` → `Formal verb for deliberately evading a rule, obligation or difficulty; contourner is the broader and more neutral alternative.`
  - `trap`: `Circonvenir normally means to manipulate or win over a person; it is not a formal synonym for contourner a rule.` → `Éluder foregrounds deliberate evasion and normally takes a difficulty, obligation or safeguard as its object; élucider instead means clarify or solve.`
  - `example_tl + cloze`: `Certaines applications contournent les garde-fous européens en transférant les profils sensibles vers des filiales établies dans des juridictions moins exigeantes.` → `Certaines applications éludent les garde-fous européens en transférant les profils sensibles vers des filiales établies dans des juridictions moins exigeantes.`
  - `note`: `Old_back is accurate; the example fixes the intentional regulatory-evasion sense.` → `Old_back is accurate; self-review selects éluder to fix the intentional regulatory-evasion sense and provide a production answer distinct from bypass.`

### Italian

- `it_fancy_vocab_b02` 041, `example_en`: `The editorial team curated a dossier based on open sources, selecting verifiable documents and contextualizing them so that quantity would not replace editorial judgment.` → `The newsroom curated a dossier based on open sources, selecting verifiable documents and contextualizing them so that quantity would not replace editorial judgment.`
- `it_fancy_vocab_b02` 063, `example_en`: `Some platforms bypass restrictions on political advertising by classifying messages commissioned by groups formally independent of political parties as organic content.` → `Some platforms bypass restrictions on political advertising by classifying messages commissioned by groups formally independent of parties as organic content.`
- `it_fancy_vocab_b07` 260, `example_en`: `Common technical standards promote network interoperability, but they can entrench the advantage of companies that participate regularly in standards bodies.` → `Common technical standards promote network interoperability, but they can entrench the advantage of companies that participate regularly in standardization bodies.`
- `it_fancy_vocab_b11` 403, `tl`: `sostenere` → `sostenere una proposta`.
- `it_fancy_vocab_b12` 446:
  - `tl`: `sostenere` → `sostenere che`.
  - `cloze`: `La società {{c1::sostiene}} che la fuga di dati sia opera di un fornitore esterno, ma non presenta alcuna prova verificabile.` → `La società {{c1::sostiene che}} la fuga di dati sia opera di un fornitore esterno, ma non presenta alcuna prova verificabile.`
- `it_fancy_vocab_b12` 449:
  - `tl`: `aggirare` → `eludere`; `alts`: `["eludere"]` → `["aggirare"]`.
  - `register`: `Aggirare è neutro-formale con norme, vincoli e ostacoli; eludere è più formale e sottolinea l'intenzione di sottrarsi a un obbligo.` → `Eludere è formale con norme, vincoli e obblighi e sottolinea l'intenzione di sottrarvisi; aggirare è più neutro e più ampio.`
  - `example_tl + cloze`: `Alcune piattaforme aggirano i vincoli sulla pubblicità politica classificando gli annunci come contenuti informativi e affidandone la distribuzione a intermediari opachi.` → `Alcune piattaforme eludono i vincoli sulla pubblicità politica classificando gli annunci come contenuti informativi e affidandone la distribuzione a intermediari opachi.`
  - `note`: `The legacy rendering is accurate. Self-review retained eludere because the regulatory constraints in this example license its more intentional nuance.` → `The legacy rendering is accurate. Self-review makes eludere primary because the regulatory constraints license its intentional nuance and keep the production answer distinct from bypass.`
- `it_fancy_vocab_b13` 482, `cloze`: `L'azienda non ha {{c1::suffragato}} le accuse con documenti verificabili, benché le avesse ripetute davanti a tre diverse commissioni parlamentari.` → `L'azienda non ha {{c1::suffragato}} le accuse {{c1::con}} documenti verificabili, benché le avesse ripetute davanti a tre diverse commissioni parlamentari.`

### Portuguese

- `pt_fancy_vocab_b02` 068:
  - `tl`: `minar` → `corroer`; `alts`: `["corroer"]` → `["minar"]`.
  - `example_tl + cloze`: `A divulgação seletiva de pesquisas minou a confiança pública nas eleições, embora nenhuma evidência sustentasse as acusações repetidas pelos candidatos derrotados.` → `A divulgação seletiva de pesquisas corroeu a confiança pública nas eleições, embora nenhuma evidência sustentasse as acusações repetidas pelos candidatos derrotados.`
  - `note`: `Old_back oferece corroer, alternativa válida no mesmo exemplo. Minar foi escolhido como forma principal por sua colocação frequente com confiança e legitimidade.` → `Old_back oferece corroer, forma idiomática no mesmo exemplo. A autorrevisão a torna principal para diferenciar este item de undermine, mantendo minar como alternativa contextual.`
- `pt_fancy_vocab_b03` 084, `cloze`: `O documentário {{c1::justapõe}} anúncios otimistas da empresa a depoimentos de trabalhadores que descrevem jornadas imprevisíveis, vigilância constante e remuneração cada vez menor.` → `O documentário {{c1::justapõe}} anúncios otimistas da empresa {{c1::a}} depoimentos de trabalhadores que descrevem jornadas imprevisíveis, vigilância constante e remuneração cada vez menor.`
- `pt_fancy_vocab_b03` 085:
  - `tl`: `ofuscar` → `eclipsar`; `alts`: `["eclipsar"]` → `["ofuscar"]`.
  - `example_tl + cloze`: `A controvérsia sobre o vazamento ofuscou as conclusões centrais da auditoria, que apontavam falhas sistêmicas na proteção de dados de milhões de usuários.` → `A controvérsia sobre o vazamento eclipsou as conclusões centrais da auditoria, que apontavam falhas sistêmicas na proteção de dados de milhões de usuários.`
  - `note`: `Old_back oferece um equivalente adequado. O contexto fixa o sentido informacional de retirar destaque, não os sentidos físicos de bloquear a visão ou emitir brilho. Autorrevisão: substituí um verbo-decoy pouco natural por sombrear.` → `Old_back oferece um equivalente adequado. A autorrevisão torna eclipsar principal para fixar o sentido de retirar destaque e diferenciar este item do uso técnico de ofuscar em obfuscate.`
- `pt_fancy_vocab_b03` 091, `tl`: `encontrar eco em` → `encontrar eco entre um público`; `alts`: `["ter ressonância em"]` → `["ter ressonância entre um público"]`.
- `pt_fancy_vocab_b06` 213:
  - `example_tl + cloze`: `A interface manipuladora destaca a opção mais invasiva em cores vivas e esconde a opção de recusa em menus deliberadamente confusos.` → `A interface manipuladora destaca a opção mais invasiva em cores vivas e esconde a possibilidade de recusa em menus deliberadamente confusos.`
  - `example_en`: `The manipulative interface highlights the most invasive option in bright colors and hides the refusal option in deliberately confusing menus.` → `The manipulative interface highlights the most invasive option in bright colors and hides the possibility of refusal in deliberately confusing menus.`
- `pt_fancy_vocab_b06` 217:
  - `example_tl + cloze`: `Uma empresa nativa digital pode dispensar agências físicas, mas continua sujeita às mesmas obrigações trabalhistas, tributárias e concorrenciais que qualquer empresa tradicional.` → `Uma empresa nativa digital pode dispensar agências físicas, mas continua sujeita às mesmas obrigações trabalhistas, tributárias e concorrenciais que qualquer negócio tradicional.`
  - `example_en`: `A digital-native company may do without physical branches but remains subject to the same labor, tax, and competition obligations as any traditional company.` → `A digital-native company may do without physical branches but remains subject to the same labor, tax, and competition obligations as any traditional business.`
- `pt_fancy_vocab_b08` 304, `example_en`: `Procurement management set social and environmental criteria for suppliers, but management removed requirements whenever they threatened to reduce the quarterly margin.` → `Procurement set social and environmental criteria for suppliers, but the executive board removed requirements whenever they threatened to reduce the quarterly margin.`
- `pt_fancy_vocab_b11` 404, `cloze`: `Auditores independentes {{c1::estimaram o valor}} dos ativos digitais da empresa antes de o fundo apresentar uma oferta vinculante de aquisição.` → `Auditores independentes {{c1::estimaram o valor dos}} ativos digitais da empresa antes de o fundo apresentar uma oferta vinculante de aquisição.`
- `pt_fancy_vocab_b11` 405, `cloze`: `A ministra {{c1::articulou}} suas ressalvas com clareza, sem transformar uma divergência técnica sobre o pacto em ruptura política irreversível.` → `A ministra {{c1::articulou}} suas ressalvas {{c1::com clareza}}, sem transformar uma divergência técnica sobre o pacto em ruptura política irreversível.`
- `pt_fancy_vocab_b13` 482, `cloze`: `A empresa não conseguiu {{c1::fundamentar}} a acusação com provas verificáveis, embora tivesse repetido a mesma versão perante três comissões parlamentares.` → `A empresa não conseguiu {{c1::fundamentar}} a acusação {{c1::com provas}} verificáveis, embora tivesse repetido a mesma versão perante três comissões parlamentares.`
- `pt_fancy_vocab_b15` 577:
  - `tl`: `reducionista` → `redutivo`; `alts`: `["simplista"]` → `["reducionista", "simplista"]`.
  - `register`: `Neutro-formal e crítico em análise política ou acadêmica para uma explicação que elimina fatores ou distinções necessários; simplista é mais abertamente depreciativo.` → `Neutro-formal e crítico em análise política ou acadêmica para uma explicação que reduz indevidamente uma questão complexa; reducionista é uma alternativa mais marcada.`
  - `trap`: `Redutor descreve muitas vezes aquilo que reduz uma quantidade, um risco ou um custo; reducionista marca com mais clareza a simplificação indevida de uma questão complexa.` → `Redutivo, neste contexto, critica uma simplificação indevida; redutor descreve com mais frequência aquilo que reduz uma quantidade, um risco ou um custo.`
  - `example_tl + cloze`: `A leitura reducionista da crise atribui toda a polarização às redes sociais e apaga desigualdades econômicas, conflitos regionais e decisões institucionais.` → `A leitura redutiva da crise atribui toda a polarização às redes sociais e apaga desigualdades econômicas, conflitos regionais e decisões institucionais.`
  - `note`: `Diverge de old_back: redutora é uma forma portuguesa válida, mas não fixa com igual clareza a acepção crítica de simplificação excessiva. Autorrevisão: mantive simplista como alternativa contextual, registrando sua censura mais forte.` → `Old_back fornece uma base portuguesa válida. A autorrevisão seleciona redutivo para diferenciar este item de reductionist e mantém reducionista e simplista como alternativas contextuais.`

## Defect taxonomy summary

Counts are findings by class and can overlap on the same row.

| Class | Result | Findings and disposition |
|---|---|---|
| 1. Language quality / naturalness | EDITED | Fourteen German rows had awkward, redundant, contradictory, or semantically malformed prose: 446, 451, 454, 458, 467, 478, 483, 494, 534, 537, 542, 548, 561, and 581. All examples and translations now read naturally and preserve the intended sense. |
| 2. Schema and field semantics | EDITED | Eighteen rows had an under-specified or duplicate production headword. Sixteen rows resolved 15 exact same-language answer collisions; Spanish 091 and Portuguese 091 aligned their production frame with the actual `entre` example. All retained objects still have the exact 11-key V1 schema and allowed category values. |
| 3. Triage judgment / duplicate policy | PASS | All 2,940 keep/drop decisions and 1,491 reasons are defensible; no verdict changed. Fancy Vocabulary correctly drops all 20 routed duplicate IDs: 098, 099, 104, 108, 145, 146, 147, 149, 163, 165, 169, 173, 176, 185, 220, 240, 248, 249, 271, and 407. |
| 4. Interference traps | EDITED | Nine trap fields were regenerated when their main headword/sense changed. All other traps remain specific and real; the four empty traps were consciously retained rather than filled with invented risks. |
| 5. Cloze integrity | EDITED | Seventeen clozes leaked fixed government or indispensable material from the authored frame. Thirty-three additional clozes were regenerated because their example or headword changed. All 1,449 final clozes reduce exactly to `example_tl`, hide the drilled form, and contain no empty group. |
| 6a. Circular definitions | PASS | None. V1 has no definition field, and no register/trap/note prose circularly defines a term with itself. |
| 6b. Cross-item boilerplate / repetition | EDITED | Fifteen exact production-answer collisions between different IDs were repaired across German, French, Italian, and Portuguese. No duplicate sentence, repeated multi-card proposition, or systemic sentence-template boilerplate remains. |
| 6c. English/target term-definition redundancy | N/A / PASS | V1 has no definition pair. Required English examples are translations, not duplicate definitions, and production headwords are not padded with English restatements. |
| 6d. Within-sentence repetition | EDITED | Thirty-two rows had accidental exact or same-stem repetition in a target example or its English translation. Each was recast without weakening the contrast or technical content. Deliberate parallel and fixed expressions remain. |

No uncorrected blocker remains. No triage decision was silently reinterpreted, no retained card leaks a fixed governed element, and no chunk requires rejection or rewrite.

**Final counts — chunks passed / edited / failed: 76 / 36 / 0.**
