# Curriculum roadmap after the 67 live units

**Research cut:** 2026-08-01  
**Scope:** Spanish, French, Italian, Brazilian Portuguese, and German; A2-C1 grammar  
**Decision rule:** observed learner error > uncovered B2/C1 inventory requirement > frequency/prerequisite value

## Executive answer

The code has **67 live units and zero planned placeholders**. This roadmap therefore starts after, rather than restates, the current curriculum. The first additions should be the still-uncovered fossilised patterns: Spanish motion prepositions and collocations; French regimes, agreement, and word order; Italian subjunctive selection and article/agreement extensions; Portuguese `ser/estar/ficar`, past choice, and future-subjunctive selection; German genitive/n-declension, prefix verbs, and Konjunktiv II. High-confidence B2 gaps follow. C1-only work is last because the German and Italian public reference inventories stop at B2, the French open C1 inventory is explicitly low-consensus, and the Brazilian Portuguese C1 mapping is functional rather than structural.

This is a coverage roadmap, not a claim that every listed construction must become an isolated deck. A candidate should be promoted only if its examples can satisfy the verification contract below and its telemetry is distinguishable from an existing unit.

## How to read this document

- A level ending in `?` is uncertain. `Remedial` means an attested learner need for which assigning a CEFR level would be misleading.
- “Covered” means a live unit can generate or retrieve the target distinction. An F3/F4 deck existing in code is infrastructure, not evidence that every error family is mastered.
- Absence from an error log is **not** mastery evidence when the corpus supplied few opportunities to produce the form.
- Formats follow the strategy exactly: **F1** one-target cloze; **F2** contrast/interpretation; **F3** error correction; **F5** a small landmark paradigm. F4 is already live and is intentionally not proposed here because the commission requested F1/F2/F3/F5 candidates.
- Verification labels are deliberately limited to the commission's three tiers:
  - `morph`: exact answer from a conjugation/declension table such as UniMorph, Kaikki/Wiktionary, Jehle, Morph-it!, verbecc, or the existing German NP engine.
  - `bank+deterministic`: a reviewed row supplies the answer and rule metadata; generation may vary the frame but not invent the grammatical fact.
  - `blind K=3`: three independent solvers must recover the same answer; the row also names the closed answer inventory or seed bank needed.
- “New machinery: no” permits a new reviewed data bank. It means the current morph, bank, or blind route can validate it without a new verifier type.

## Source and authority ledger

The CEFR is intentionally language-neutral. The Council of Europe explains that language-specific Reference Level Descriptions (RLDs) supply the language forms and grammar that the generic framework does not, and that the RLDs are produced by national teams rather than by the Council itself ([RLD explanation](https://www.coe.int/en/web/common-european-framework-reference-languages/reference-level-descriptions); [RLD catalogue](https://www.coe.int/en/web/common-european-framework-reference-languages/reference-level-descriptions-rlds-developed-so-far)). The [CEFR Companion Volume](https://rm.coe.int/cefr-companion-volume-with-new-descriptors-2020/16809ea0d4) calibrates performance—roughly good control with occasional slips at B2 and consistently high accuracy with rare errors at C1—but is not a grammar checklist.

| Language | Primary inventory | Secondary checks | Limits used in this roadmap |
|---|---|---|---|
| Spanish | Instituto Cervantes [PCIC index](https://cvc.cervantes.es/ensenanza/biblioteca_ELE/plan_curricular/indice.htm), [A1-A2 grammar](https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/niveles/02_gramatica_inventario_a1-a2.htm), [B1-B2 grammar](https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/niveles/02_gramatica_inventario_b1-b2.htm), and [C1-C2 grammar](https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/niveles/02_gramatica_inventario_c1-c2.htm) | [Kwiziq Spanish tree](https://spanish.kwiziq.com/revision/grammar/by-cefr-level) | PCIC is the strongest open, official inventory here. Kwiziq is commercial and only helps split large PCIC nodes into drill-sized units. |
| French | Open [Eaquals/CIEP/Eurocentres A1-C1 inventory](https://www.eaquals.org/wp-content/uploads/Inventaire_ONLINE_full.pdf), derived from the French RLD tradition | [Kwiziq tree](https://french.kwiziq.com/revision/grammar/by-cefr-level), [tense matrix](https://french.kwiziq.com/french-tenses-by-cefr-level), official [DELF B2 outcome](https://www.france-education-international.fr/en/diplome/delf-tout-public/niveau-b2), and [DALF C1 morphosyntax explanation](https://www.france-education-international.fr/document/explic-grille-pe-c1) | The official detailed RLD books are not open. Eaquals is selective/non-exhaustive and says C1 consensus is thinner. Kwiziq is non-normative. |
| Italian | University for Foreigners of Perugia's official open [Profilo della lingua italiana](https://www.unistrapg.it/profilo_lingua_italiana/site/index.html), including its [method/validation account](https://www.unistrapg.it/profilo_lingua_italiana/site/origini.html) and granular A2-B2 grammar pages | Official [CILS guidelines](https://cils.unistrasi.it/public/articoli/52/Linee_guida_cils_pdf.pdf), [CELI C1 competencies](https://www.unistrapg.it/sites/default/files/docs/certificazioni/celi-4-competenze-richieste.pdf), and a [Roma Tre C1 syllabus](https://cla.uniroma3.it/wp-content/uploads/sites/29/file_locked/2022/04/sillaboC1.pdf) | Profilo ends at B2. CILS/CELI and university syllabi make C1 triangulation possible, but not authoritative at topic-boundary resolution. |
| Brazilian Portuguese | Itamaraty/FUNAG's [Brazilian curriculum for Spanish-speaking learners](https://funag.gov.br/biblioteca-nova/pdf/mostraPdf/21/1124/proposta_curricular_para_ensino_de_portugues_nas_unidades_da_rede_de_ensino_do_itamaraty_em_paises_de_lingua_oficial_espanhola) | Camões [Referencial PLE](https://www.instituto-camoes.pt/images/REFERENCIAL_ebook.pdf), the [Celpe-Bras FAQ](https://www.gov.br/inep/pt-br/acesso-a-informacao/perguntas-frequentes/celpe-bras), and [Celpe-Bras base document](https://download.inep.gov.br/publicacoes/institucionais/avaliacoes_e_exames_da_educacao_basica/documento_base_do_exame_celpe_bras.pdf) | FUNAG calls its CEFR crosswalk approximate and spiral. Camões is European Portuguese; Celpe-Bras is performance/genre based and deliberately not a grammar list. |
| German | [German Grammar Profile 2025](https://aclanthology.org/2025.konvens-2.17.pdf) and its [2026 validation](https://aclanthology.org/2026.bea-1.6.pdf), based on ÖSD/Profile Deutsch | [ÖSD Profile Deutsch](https://www.osd.at/das-oesd/profile-deutsch/ziele-komponenten/), [BAMF B2 course concept](https://www.bamf.de/SharedDocs/Anlagen/DE/Integration/Berufsbezsprachf-ESF-BAMF/BSK-Konzepte/kurskonzept-b2.pdf?__blob=publicationFile&v=15), and a [Goethe B2/C1 grammar programme](https://www.goethe.de/resources/files/pdf313/kursprogramm-grammatik-b2-c1-ht-2023.pdf) | GGP has 153 expert features through B2 but its full list is not open and it has no C1. Every concrete German C1 assignment is therefore uncertain. |

Morphology candidates assume only appropriately licensed/attributed data already contemplated by the strategy, principally [UniMorph](https://unimorph.github.io/) and [Kaikki/Wiktionary extracts](https://kaikki.org/), plus the language-specific tables already used by the application. A source's presence here is not permission to copy proprietary exercise prose.

## Conflicts with the strategy or among sources

1. **Italian open data:** `GRAMMAR_STRATEGY.md` says there is no open Italian CEFR grammar dataset and describes Profilo as effectively unavailable. That is now stale for A1-B2: Perugia publishes the complete category/level inventory as HTML. The limitation still applies at C1.
2. **French open inventory:** the detailed official French RLD volumes remain print-only, as the strategy implies, but the free Eaquals/CIEP inventory is a usable simplified A1-C1 synthesis. It is less detailed than PCIC and explicitly low-consensus at C1.
3. **French level disagreements:** Eaquals places future simple at A2 while Kwiziq concentrates it at B1; Eaquals puts plus-que-parfait and initial present subjunctive at B1 while Kwiziq starts them at B2; Eaquals places passé simple at C1 while Kwiziq begins some receptive work at B2. Those roadmap labels carry `?`.
4. **Italian level disagreements:** Profilo puts future anterior at B1, while CILS first enumerates it at B2. Profilo introduces four subjunctive tenses and the passive at B2, but treats some control as partial; CILS places productive compound-subjunctive/passive control later. The taxonomy records introduction at the earlier level and marks the mastery boundary uncertain.
5. **Portuguese variety:** the strategy's Camões source describes standard European Portuguese. The live product is explicitly Brazilian (`você/vocês`, Brazilian proclisis and progressive defaults). No variety-sensitive Camões form is imported without a BR source or an uncertainty mark.
6. **German scope:** GGP is not a public A1-C1 inventory. The papers expose selected A1-B2 features and aggregate counts; C1 items below are course-syllabus inferences, not GGP facts.

The distilled, source-linked snapshots are in [`taxonomies/`](taxonomies/); the more granular Italian tree, with two examples and prerequisites on every node, is [`it-grammar-taxonomy.yaml`](it-grammar-taxonomy.yaml).

## Audited live baseline

`topics_for()` was imported from `idiomatic/grammar/curriculum.py` on 2026-08-01. It returned exactly **67** keys; `PLANNED_UNITS` was empty. Several counts in the older error profiles are therefore stale and were not used as the baseline.

| Language | Count | Exact live keys |
|---|---:|---|
| Spanish | 22 | `es_pres_irreg`, `es_preterito`, `es_imperfecto`, `es_futuro`, `es_condicional`, `es_subj_pres`, `es_subj_imp`, `es_perfecto`, `es_cmd_tu`, `es_cmd_usted`, `es_cmd_neg`, `es_cond_perf`, `es_plusc_subj`, `es_clitics_dir`, `es_clitics_ind`, `es_clitics_selo`, `es_verb_prep`, `es_por_para`, `es_ser_estar`, `es_muy_mucho`, `es_mis_errores`, `es_interference_f4` |
| French | 14 | `fr_present_irreguliers`, `fr_passe_compose`, `fr_imparfait`, `fr_futur_simple`, `fr_conditionnel_present`, `fr_subjonctif_present`, `fr_subjonctif_conjonctions`, `fr_pronoms_y_en`, `fr_quantites_de`, `fr_prep_lieux`, `fr_genre_noyau`, `fr_an_annee`, `fr_mes_erreurs`, `fr_interference_f4` |
| Italian | 12 | `it_presente_irregolari`, `it_passato_prossimo`, `it_imperfetto`, `it_futuro_semplice`, `it_condizionale_presente`, `it_congiuntivo_presente`, `it_passato_remoto`, `it_clitici_ci_ne`, `it_genere_plurali`, `it_reggenze_verbali`, `it_miei_errori`, `it_interference_f4` |
| Brazilian Portuguese | 12 | `pt_presente_irregulares`, `pt_preterito_perfeito`, `pt_preterito_imperfeito`, `pt_futuro_simples`, `pt_condicional_presente`, `pt_subjuntivo_presente`, `pt_futuro_subjuntivo`, `pt_clitic_placement`, `pt_gender_core`, `pt_regencia_verbal`, `pt_meus_erros`, `pt_interference_f4` |
| German | 7 | `de_gender`, `de_prep_fest`, `de_prep_wechsel`, `de_adj_endings`, `de_passiv`, `de_dativ_verben`, `de_meine_fehler` |

Cluster names in the candidate tables preserve all live numbering. Clusters **9** and **10** remain reserved across languages for “my errors” and interference. New domains begin at unused numbers or extend an existing semantic cluster; no existing subdeck is renamed.

## Gap analysis

### Spanish

The [Spanish error profile](error-profiles/es.md) has only 62 verbatim pairs, so counts are strong occurrence evidence but weak prevalence estimates. Twenty-six show cross-Romance/English interference; the most repeated grammatical families are `muy/mucho` (7), motion/location prepositions (7), preterite morphology (5), light-verb collocations (3 plus reteaching), fixed prepositions (3), gender/articles (4), and a clitic case. The live curriculum now covers many of those broad domains, but not always the attested lexical rows.

| Expected control not established | Live/evidence diff | Roadmap consequence |
|---|---|---|
| Motion versus location regimes | `es_verb_prep.json` has 60 rows but none for the error-profile verbs `ir`, `viajar`, `llegar`, `regresar`, `volver`, or temporal `pasar`; seven direct errors remain operationally uncovered. | First bank extension, before new CEFR-only units. |
| Collocation, derivation, number/date and personal gender traps | Current F3/F4 cards preserve exact corrections, but there is no generative transfer unit for `tomar/cometer/dar` collocations, Romance/English derivational overreach, numerals/dates, or the personal noun set. | Error-led F1/F2 units with reviewed facts. |
| Compound indicative/subjunctive system | Conditional perfect and pluperfect subjunctive are live; pluperfect indicative, future perfect, and perfect subjunctive are not. | High-confidence B1/B2 morphology additions. |
| Mood selection across clauses | Live subjunctive units teach forms/triggers, not factual versus pending temporal clauses, specific versus unknown relatives, or concessive choice. | F2 banks, not more isolated conjugation alone. |
| Voice, `se`, relatives, periphrases, reported speech | PCIC B1/B2 expects impersonal/passive `se`, periphrastic passive, compound relatives, aspectual/modal periphrases, and sequence in reported speech. None has a live unit. | B1/B2 coverage wave. |
| C1 pragmatic tense, datives, marked order and formal compression | The error corpus offers almost no obligatory opportunities; zero observed errors cannot establish mastery. | Defer until B2 units yield telemetry; C1 boundaries come from PCIC but consolidated bundles may still be uncertain. |

### French

The [French error profile](error-profiles/fr.md) classifies 2,523 use-marked errors. Approximate mass is concentrated in prepositions (~635), gender/agreement (~396), articles/quantity (~215, including 138 `beaucoup de`), word order (~130), morphology (~132), `an/année` (~100), pronouns/relatives (~95), and negation (~60). The live additions address narrow high-value slices, but not the broader families.

| Expected control not established | Live/evidence diff | Roadmap consequence |
|---|---|---|
| General verb/adjective/infinitive government | `fr_prep_lieux` is only place selection. Roughly 475 verb-regime and 77 infinitive-regime errors remain outside it. | Highest-priority reviewed regime banks. |
| Agreement beyond noun gender | `fr_genre_noyau` tests noun facts; `fr_passe_compose` intentionally avoids preceding-object agreement. Adjective/plural and clitic-relative participle errors remain. | Extend deterministic agreement, including `-al/-aux` and preceding COD. |
| Constituent order, negation and lexicalised pronominals | Repeated English-order transfer (`les premières deux`), adverb placement, double negation, and missing/spurious `se` have no dedicated unit. | Error-led F2/F1 before low-frequency tense work. |
| Relatives and double clitics | Only `y/en` is live; `qui/que/dont/où/lequel`, governed relatives, and full clitic order are absent despite direct errors. | Pronoun-cluster expansion. |
| B1/B2 compound tenses, conditions, voice, and reporting | No plus-que-parfait, futur antérieur, conditionnel passé/unreal `si`, passive/causative, or past indirect-speech unit. | High-confidence inventory wave after errors. |
| C1 narrative/register control | Passé simple level conflicts across open sources and the Eaquals C1 list is thin. | Receptive unit only, marked `C1?`; do not infer productive mastery. |

### Italian

The [Italian error profile](error-profiles/it.md) contains exactly 11 production errors from one 2019 lesson: five verb-preposition regimes, three lexical/interference choices, and one each in past-aspect choice, a fixed expression, and agreement. A 74-item procomplementary homework set and 19 connector items are teacher-priority signals, not error counts. The learner separately reports prepositions, congiuntivo, passato-remoto avoidance, articles, gender, and plurals as weaknesses; that self-report outranks a zero in this tiny corpus.

| Expected control not established | Live/evidence diff | Roadmap consequence |
|---|---|---|
| Subjunctive choice and time system | Only present-subjunctive morphology is live. No imperfect/past/pluperfect forms, consecutio, or possible/unreal hypothetical chains are drilled. | First Italian wave; separate form truth from F2 selection. |
| Contextual articles and agreement | `it_genere_plurali` is a strong noun bank but does not test article presence/omission, adjective agreement, or participle agreement after clitics. One direct plural-agreement error and the self-report remain. | Extend `it_noun`; add clitic-participle facts. |
| Full clitic system | `it_clitici_ci_ne` answers only `ci`, `ne`, or `ce ne`. It exposes some procomplementary contexts but cannot test complete clusters, placement, or agreement. | New banked clitic targets; reuse blind route where possible. |
| Preposition semantics and relatives | Verb government is live, but abstract preposition functions/locutions and governed relatives (`cui`, `il quale`) are not; the profile also infers a `dove`→`in cui` repair. | Extend cluster 6 and add syntax/cohesion cluster 7. |
| Connectors and B2 syntax | The 19-item connector upgrade, passive/impersonal `si`, non-finite clauses, indirect speech, and official Profilo marked order are absent. | Teacher-priority connector unit, then official B2 gaps. |
| C1 production | Profilo stops at B2. CILS/CELI support compound moods, productive passive, nominalisation, reported speech, and advanced cohesion, but exact placement is not a complete official tree. | Every C1 candidate carries `?` and follows validation/telemetry. |

### Brazilian Portuguese

The [Portuguese error profile](error-profiles/pt.md) contains 1,098 error rows. It identifies Romance interference (~588 overlapping rows), gender (~193 plus agreement), preposition/regime errors (32/30), preterite person errors (29), `ser/estar/ficar` (24), morphology (19), clitics (18), numerals (16), and subjunctive errors (9). The future subjunctive also has seven recorded errors plus eight later reteaching notes, so an existing morphology unit is not selection mastery.

| Expected control not established | Live/evidence diff | Roadmap consequence |
|---|---|---|
| Copula/change-of-state selection | No `ser/estar/ficar` unit despite 24 direct errors. | First candidate. |
| Past and future-subjunctive selection | Perfect and imperfect, and future subjunctive, are separate form units; none forces aspect/trigger choice. | Error-led F2 units before more paradigms. |
| Numerals, `por/para`, and targeted Romance calques | `pt_gender_core` contains some agreement facts and generic F3/F4 exists, but repeated numeral agreement and particular cross-language regimes need transferable practice. | Focused reviewed banks; no European forms. |
| Personal infinitive/reduced clauses and governed relatives | FUNAG/Camões expect these around B1/B2; none is live. Their BR CEFR boundary is approximate. | Add subject-reference metadata and mark uncertainty. |
| Passive and compound tense systems | Neither `ser` passive nor passive/impersonal `se` is live; compound indicative/subjunctive forms are absent. | B1/B2 coverage wave with agreement/transitivity checks. |
| C1 modalisation/register | Celpe-Bras and FUNAG prioritise genre, stance and register rather than a closed form list. | One banked `C1?` discourse unit, not a pseudo-authoritative grammar checklist. |

### German

The [German error profile](error-profiles/de.md) has no populated legacy `error` field and only about 28 retained utterances; much of the remainder is teacher-priority or supplied-language evidence. The strongest repeated direct family—adjective/determiner endings, six cases across 2019-2024—is now live. Remaining signals include gender (4), object case (4), noun inflection (3), supplied/avoided passive, genitive (15 supplied examples), dative verbs, Konjunktiv II (8 supplied examples), da-compound regimes, and prefix verbs.

| Expected control not established | Live/evidence diff | Roadmap consequence |
|---|---|---|
| Genitive and n-declension | `de_dativ_verben` covers dative objects only. Genitive use/avoidance and weak-noun endings remain uncovered. | Error/avoidance-led cluster-5 extensions. |
| Prefix verbs, Konjunktiv II and da-compounds | No live unit despite direct/supplied evidence and GGP B1/B2 relevance. | Early candidates, with honest “avoidance” wording. |
| Relatives and clause architecture | No case-marked relative, connector, subordinate-order, verb-cluster, or Vorfeld unit. | A2-B2 syntax progression. |
| Voice beyond process passive | `de_passiv` covers process passive including a limited modal frame, not state passive, passive alternatives, or full perfect/modal/double-infinitive chains. | B2 state/alternative work; `C1?` full-chain work. |
| Konjunktiv I, subjective modality, and complex government | GGP/BAMF/Goethe support these by B2 or upper level; no live coverage or robust learner opportunities. | Coverage-led, lower than attested gaps. |
| C1 participial/nominal style and information structure | Only course syllabi support the concrete placement; GGP stops at B2. | All marked `C1?`, late and telemetry-gated. |

## Prioritised candidate units

Ranks restart per language. Within each table, direct error/self-report/teacher evidence comes first, then inventory coverage, then frequency and prerequisite value. `Yes — ...` in the machinery column is a design warning, not approval to implement without a separate spec.

### Spanish — 18 candidates

| Rank | Proposed key; level | Cluster | Format | Verification tier and required data | New verifier machinery? | One-line rationale |
|---:|---|---|---|---|---|---|
| 1 | `es_prep_movimiento`; A2 remedial | `6 Preposiciones` | F1/F3 | `bank+deterministic`: extend the regime bank with sense-pinned `ir/viajar/llegar/regresar/volver + a`, destination contrasts, and temporal `pasar + en` rows | No — reuse reviewed-bank answer checks | Seven direct errors, and none of their core verbs occurs in the current 60-row regime bank. |
| 2 | `es_derivacion_contrastiva`; B1? | `10 Interferencias` | F2/F3 | `bank+deterministic`: reviewed minimal-pair bank (`dictado/dictación`, `consumo/consumación`, `similitud/similaridad`, etc.) | No | Derivational overgeneration is a recurrent part of the 26/62 interference errors; B1 placement is inferred. |
| 3 | `es_colocaciones_verbo_soporte`; A2-B1? | `10 Interferencias` | F1/F3 | `bank+deterministic`: noun-to-light-verb table for `tomar/cometer/dar/hacer` with sense and accepted inflected answers | No — exact bank answers suffice | `hacer decisiones/fotos/errores` recurred across four years; the exact-error deck alone does not test transfer. |
| 4 | `es_numeros_fechas`; A2 remedial | `11 Números y fechas` | F1/F5 | `bank+deterministic`: integers/hundreds, agreeing hundreds, years, dates and ordinals checked by a Spanish number/date table | **Yes — Spanish number/date formatter** | `cinco cientos` plus later spelling/date reteaching shows a persistent, mechanically checkable gap. |
| 5 | `es_genero_articulo_nucleo`; A2 remedial | `12 Género y determinación` | F1/F3/F5 | `bank+deterministic`: personal noun-gender-number-article table, including sense-pinned homonyms | **Yes — Spanish NP/article fact checker** | Four direct errors plus systematic reteaching justify a personalised core rather than a generic gender survey. |
| 6 | `es_pluscuamperfecto_ind`; B1 | `1 Tiempos` | F1/F5 | `morph`: Jehle/UniMorph indicative pluperfect rows | No | PCIC B1 past anteriority is the most obvious missing high-frequency indicative form. |
| 7 | `es_futuro_perfecto`; B2 | `1 Tiempos` | F1/F5 | `morph`: Jehle/UniMorph future-perfect rows | No | PCIC B2 expects anterior future/probability control; no live unit supplies it. |
| 8 | `es_subj_perfecto`; B2 | `2 Subjuntivo` | F1/F5 | `morph`: Jehle/UniMorph present-perfect-subjunctive rows | No | Completes the B2 subjunctive time system between live present and pluperfect units. |
| 9 | `es_temporales_modo`; B1-B2 | `2 Subjuntivo` | F2 | `bank+deterministic`: factual/pending minimal-pair bank for `cuando`, `hasta que`, `antes de que`, `una vez que` | No | Live subjunctive cards cue a form but do not test the temporal interpretation that selects mood. |
| 10 | `es_relativas_modo`; B2 | `13 Relativos` | F2 | `bank+deterministic`: specific/known versus non-specific/negated antecedent pairs | No | Indicative-subjunctive control in relatives is an explicit PCIC B2 gap. |
| 11 | `es_relativos_compuestos_cuyo`; B2-C1? | `13 Relativos` | F1/F5 | `blind K=3`: governed-relative seed bank plus closed inventory `que/quien/el que/el cual/cuyo/donde` | No — reuse blind closed-class route | Formal prepositional relatives and `cuyo` are absent; the consolidated upper boundary is uncertain. |
| 12 | `es_pasiva_ser_se`; B1-B2 | `14 Voz y se` | F2 | `bank+deterministic`: reviewed active/periphrastic-passive/passive-`se` contrast triples | No | PCIC expects both passive strategies, while no live unit drills voice choice. |
| 13 | `es_se_impersonal_accidental`; B1-C1? | `14 Voz y se` | F2 | `bank+deterministic`: construction-labelled bank for impersonal, passive, accidental and aspectual `se` | No | A high-frequency system is absent from the clitic units; only the aspectual endpoint is C1-uncertain. |
| 14 | `es_perifrasis_aspectuales`; B1-C1? | `15 Perífrasis` | F1/F2 | `bank+deterministic`: reviewed lemma/construction/meaning rows for `volver a`, `dejar de`, `seguir/llevar/venir + gerundio`, `deber/deber de` | No | A large PCIC aspect/modality branch has no live representation; rare advanced uses remain uncertain. |
| 15 | `es_discurso_indirecto_concordancia`; B2 | `16 Discurso referido` | F2 | `bank+deterministic`: direct/indirect pairs with tense, person and deixis metadata | No | B2 sequence-of-tense control is neither drilled nor observable in the thin error sample. |
| 16 | `es_condicionales_concesivas_modo`; B2 | `3 Condicionales` | F2 | `bank+deterministic`: real/unreal/mixed `si` and factual/non-factual `aunque` contrast bank | No | Existing counterfactual units verify forms, not selection among condition/concession patterns. |
| 17 | `es_a_personal`; A2-B1? | `6 Preposiciones` | F1/F2 | `blind K=3`: `a/Ø` inventory plus animacy, specificity and affected-object frame bank | No | Frequent object marking is absent; its spiral A2/B1 teaching boundary is broad in PCIC. |
| 18 | `es_determinacion_avanzada`; B1-B2 | `12 Género y determinación` | F2 | `bank+deterministic`: article/zero/neutral-`lo` contrast bank labelled by reference type | No | Bare/generic nouns and neutral `lo` remain outside every live unit. |

### French — 18 candidates

| Rank | Proposed key; level | Cluster | Format | Verification tier and required data | New verifier machinery? | One-line rationale |
|---:|---|---|---|---|---|---|
| 1 | `fr_prep_verbes`; A2-B2 | `5 Prépositions` | F1/F3 | `bank+deterministic`: sense-pinned verb-preposition table with `à/de/avec/pour/sur/Ø` answers | No — reuse the bank route used for places/regimes | Roughly 475 verb-regime errors are the largest uncovered class. |
| 2 | `fr_accords_avances`; A2-B2 | `6 Genre & accord` | F1/F3/F5 | `bank+deterministic`: adjective gender/number, `-al→-aux`, and preceding-COD participle facts | **Yes — adjective/participle agreement verifier** | About 99 adjective/plural errors remain, and the live passé-composé unit deliberately excludes preceding CODs. |
| 3 | `fr_ordre_num_adjectif`; B1? | `8 Ordre des mots` | F2/F3 | `bank+deterministic`: reviewed transferred/idiomatic order pairs such as `les deux premières` | No | Around 90-100 near-categorical ordering errors make this more urgent than new tense paradigms; B1 is inferred. |
| 4 | `fr_prep_infinitif`; A2-B2 | `5 Prépositions` | F1/F3 | `bank+deterministic`: sense-pinned verb/adjective plus `à/de/Ø + infinitif` table | No | Seventy-seven errors include `difficile de`, `chercher à`, `commencer à`, and `décider de`. |
| 5 | `fr_negation_complete`; A2-B1 | `8 Ordre des mots` | F1/F3 | `blind K=3`: closed inventory `pas/jamais/rien/personne/aucun/ni…ni/ne…que` plus polarity frames | No | Roughly 60 errors include missing `pas` and illicit `pas` with negative pronouns. |
| 6 | `fr_adverbes_position`; A2-B1 | `8 Ordre des mots` | F1/F3 | `bank+deterministic`: finite/compound/infinitive placement frames labelled by adverb class | No | More than 60 English-like preverbal placement errors recur across the corpus. |
| 7 | `fr_relatives`; A2-B2 | `4 Pronoms` | F1/F3/F5 | `blind K=3`: function/government bank plus `qui/que/dont/où/lequel` inventory | No | At least 55 direct errors plus later `dont/lequel` teaching remain outside `y/en`. |
| 8 | `fr_calques_structuraux`; B1? | `10 Interférences` | F2/F3 | `bank+deterministic`: reviewed structural pairs for `de manière`, `c'est que`, `rendre`, `au bout de`, and possessive/article contrasts | No | Roughly 60 calques need transfer beyond fixed personal-error cards; B1 placement is inferred. |
| 9 | `fr_articles_contractions`; A2 | `7 Articles & quantités` | F1/F3 | `bank+deterministic`: `à/de + article` and country/language article table | No | Twenty-seven contraction errors plus recurrent missing country/language articles are not covered by quantity `de`. |
| 10 | `fr_verbes_pronominaux`; A2-B1 | `4 Pronoms` | F1/F3 | `bank+deterministic`: sense-pinned pronominal/non-pronominal verb rows with exact conjugated target | No | Fifteen-plus dropped or spurious `se` errors show a lexicalised system gap. |
| 11 | `fr_superlatif_adjectif_place`; A2-B1 | `8 Ordre des mots` | F2/F3 | `bank+deterministic`: adjective-position, repeated-article superlative, `mieux/meilleur/pire` pairs | No | Repeated `solution meilleure`, missing second articles, and `plus pire/mieux` deserve a single contrast unit. |
| 12 | `fr_clitiques_objets_doubles`; B1-B2 | `4 Pronoms` | F1/F5 | `blind K=3`: full clitic-order inventory across finite verbs, infinitives, imperatives and negation | No | Eaquals B1/B2 expects double pronouns; live French covers only `y/en`. |
| 13 | `fr_plus_que_parfait`; B1? | `1 Temps` | F1/F5 | `morph`: verbecc/UniMorph indicative pluperfect rows | No | A clear inventory gap, but Eaquals B1 conflicts with Kwiziq B2. |
| 14 | `fr_futur_anterieur`; B2 | `1 Temps` | F1/F5 | `morph`: verbecc/UniMorph future-anterior rows | No | Both open sources place this missing compound tense at B2. |
| 15 | `fr_conditionnel_passe_si_irreel`; B2 | `2 Conditionnel` | F2/F5 | `bank+deterministic`: regret/unreal-condition pairs with forms cross-checked against the conjugation table | No | B2 requires selection in past counterfactual chains, not only conditional-present morphology. |
| 16 | `fr_voix_passive_causative`; B1-B2 | `11 Voix` | F2 | `bank+deterministic`: fixed active/passive/`faire + infinitif` transformation triples | No | Passive is in the Eaquals B1 progression and causative work appears by B2; neither is live. |
| 17 | `fr_discours_indirect_concordance`; B2 | `12 Discours` | F2 | `bank+deterministic`: present/past reporting pairs with tense, person and deixis metadata | No | Eaquals explicitly assigns past reported-speech sequencing at B2. |
| 18 | `fr_passe_simple_reception`; C1? | `1 Temps` | F1/F2/F5 | `morph`: high-frequency literary forms from verbecc/UniMorph, used in recognition-biased frames | No | Advanced reading needs it, but Eaquals C1 conflicts with Kwiziq's earlier receptive microtopics. |

### Italian — 19 candidates

| Rank | Proposed key; level | Cluster | Format | Verification tier and required data | New verifier machinery? | One-line rationale |
|---:|---|---|---|---|---|---|
| 1 | `it_congiuntivo_selezione`; B1-B2 | `3 Congiuntivo` | F2/F3 | `bank+deterministic`: trigger, matrix-time, event-time and indicative/subjunctive contrast rows | No | The learner reports congiuntivo weakness; the sole live unit tests present forms, not choice. |
| 2 | `it_congiuntivo_imperfetto`; B2 | `3 Congiuntivo` | F1/F5 | `morph`: Morph-it!/verbecc/UniMorph imperfect-subjunctive rows | No | Central B2 form and prerequisite to reported past and possible conditions. |
| 3 | `it_congiuntivo_tempi_composti`; B2-C1? | `3 Congiuntivo` | F1/F5 | `morph`: past/pluperfect-subjunctive auxiliary and participle rows | No | Profilo introduces them at B2, but CILS places productive compound control at C1. |
| 4 | `it_periodo_ipotetico`; B2 | `2 Condizionale` | F2/F3/F5 | `bank+deterministic`: one-target protasis/apodosis pairs labelled real, possible, present-unreal, and past-unreal | No — one blank keeps existing checks sufficient | This combines two known weak systems and tests selection rather than recitation. |
| 5 | `it_articoli_uso_omissione`; A2-B1 remedial | `5 Genere e plurali` | F1/F3 | `bank+deterministic`: contextual article/zero rows keyed by geography, kinship, possessive, genericity and specification | No | The self-reported article weakness is not tested by the live noun-form bank. |
| 6 | `it_accordo_aggettivale`; A2-B2 remedial | `5 Genere e plurali` | F1/F3/F5 | `bank+deterministic`: extend noun rows with adjective lemma, gender, number and ending class | **Yes — extend `it_noun` to adjective agreement** | One direct plural-agreement error plus self-report makes contextual agreement an evidence-led gap. |
| 7 | `it_accordo_participio_clitici`; B1-B2 | `4 Clitici` | F1/F2/F3 | `bank+deterministic`: clitic antecedent gender/number, auxiliary, participle and agreement-rule metadata | **Yes — Italian clitic/participle checker** | The 74-item remedial block repeatedly combines clitics and participles, which live passato prossimo avoids. |
| 8 | `it_preposizioni_semantiche`; A2-B2 remedial | `6 Reggenze` | F1/F3 | `bank+deterministic`: sense-labelled abstract prepositions and locutions, excluding rows already in verb government | No | Five of 11 direct errors concern regimes; this extends that signal to official non-lexical preposition functions. |
| 9 | `it_clitici_combinati_posizione`; B1-B2 | `4 Clitici` | F1/F2/F5 | `blind K=3`: complete-cluster frame bank and closed inventory across finite verbs, infinitive, imperative, gerund and modals | No | The live `ci/ne/ce ne` inventory cannot test `glielo`, `me la`, placement, or whole procomplementary clusters. |
| 10 | `it_connettivi_coesione`; B1-C1? | `7 Sintassi e coesione` | F1/F2/F3 | `bank+deterministic`: 19 teacher-priority items plus relation-labelled connector inventory and scope metadata | No | A direct teacher-priority set exists, and cohesion is an explicit upper-level assessment concern; C1 extent is uncertain. |
| 11 | `it_pronomi_relativi_avanzati`; B1-B2 | `7 Sintassi e coesione` | F1/F2/F3 | `blind K=3`: antecedent/function/government bank plus `che/cui/il quale/chi/quanto` inventory | No | Covers the inferred `dove`→`in cui` repair and an official B1/B2 gap. |
| 12 | `it_imperativo_registro_clitici`; A2-B2? | `4 Clitici` | F1/F2/F5 | `bank+deterministic`: person/register/polarity/clitic frames whose exact form is cross-checked against the conjugation table | No | Common commands are a prerequisite missing from live Italian; the upper register/placement boundary is uncertain. |
| 13 | `it_tempi_composti_indicativo`; B1-B2? | `1 Tempi` | F1/F2/F5 | `morph`: trapassato prossimo and futuro anteriore tables | No | Both are absent; future anterior is Profilo B1 versus CILS B2, hence the uncertainty mark. |
| 14 | `it_condizionale_passato`; B2 | `2 Condizionale` | F1/F2/F5 | `morph`: conditional-past auxiliary/participle forms, with banked function contrasts for F2 | No | Required for past counterfactuals and future-in-the-past, neither of which the present-conditional unit can express. |
| 15 | `it_diatesi_impersonale_passiva`; B2-C1? | `8 Diatesi e forme non finite` | F1/F2/F5 | `bank+deterministic`: transitivity, subject number, auxiliary, participle and `si`-type metadata | **Yes — `it_passive_si` agreement/transitivity verifier** | Profilo introduces `essere/venire/si` at B1-B2, while CILS productive mastery extends into C1. |
| 16 | `it_modi_indefiniti`; B2 | `8 Diatesi e forme non finite` | F1/F2 | `bank+deterministic`: gerund/infinitive/participle clause rows with time/relation and controlled-subject metadata | **Yes — subject-control consistency check** | Present/past non-finite clauses form a large official B2 family with no live unit. |
| 17 | `it_discorso_indiretto`; C1? | `7 Sintassi e coesione` | F2/F3 | `bank+deterministic`: reviewed direct/indirect pairs with tense, person, time and place deixis metadata | No | CILS/CELI support the upper-level target, but no official C1 RLD tree fixes its exact boundary. |
| 18 | `it_ordine_marcato`; B2 | `7 Sintassi e coesione` | F2/F3 | `bank+deterministic`: neutral/marked pairs labelled topic, focus, resumption, cleft and postverbal subject | No | Dislocation, clefts and postverbal subjects are explicit Profilo B2 gaps. |
| 19 | `it_nominalizzazione_derivazione`; C1? | `7 Sintassi e coesione` | F1/F2/F5 | `bank+deterministic`: reviewed word families and clause↔nominal transformation pairs | No | CILS/CELI and university syllabi support formal nominal style, but exact C1 decomposition is inferred. |

### Brazilian Portuguese — 18 candidates

All Portuguese CEFR labels below are approximate because FUNAG says its crosswalk is approximate and the corroborating Camões inventory is European Portuguese. A trailing `?` adds a further topic-boundary or variety uncertainty.

| Rank | Proposed key; level | Cluster | Format | Verification tier and required data | New verifier machinery? | One-line rationale |
|---:|---|---|---|---|---|---|
| 1 | `pt_ser_estar_ficar`; ≈A2-B1 | `7 Ser/Estar` | F1/F2/F3 | `blind K=3`: state, identity, location and change-result frame bank plus closed conjugated answer inventory | No | Twenty-four direct errors make this the clearest uncovered Portuguese selection unit. |
| 2 | `pt_preteritos_contraste`; ≈A2-B1 | `1 Tempos` | F2/F3 | `bank+deterministic`: aspect-labelled perfect/imperfect minimal pairs, forms checked against the conjugation table | No | Separate live paradigms do not address the observed person/aspect pressure. |
| 3 | `pt_futuro_subjuntivo_selecao`; ≈B1 | `3 Subjuntivo` | F1/F2/F3 | `bank+deterministic`: `quando/se/logo que/assim que` future-reference contrasts with exact table-backed answers | No | Seven errors plus eight later reteaching notes show that the live morphology unit has not solved selection. |
| 4 | `pt_condicionais_cadeias`; ≈B1-B2 | `2 Condicional` | F2/F3/F5 | `bank+deterministic`: one-target protasis/apodosis rows labelled real, possible and unreal | No | Extends isolated conditional/subjunctive forms to clause-level choice. |
| 5 | `pt_numerais_concordancia`; ≈A2 remedial | `5 Gênero & Artigos` | F1/F3/F5 | `bank+deterministic`: number/gender table for `dois/duas`, hundreds, ordinals and dates; reuse `pt_gender` facts | No | Sixteen explicit numeral errors, especially `dois/duas`, justify a focused extension. |
| 6 | `pt_por_para`; ≈A2-B1 | `6 Regência` | F1/F2/F3 | `blind K=3`: sense-labelled `por/para` bank and two-item answer inventory | No | The profile calls this a fossilised contrast; verb government does not exhaust it. |
| 7 | `pt_es_it_regimes_f3`; Remedial | `10 Interferência` | F2/F3 | `bank+deterministic`: attested Spanish/Italian→BR Portuguese calque/regime correction bank | No | Romance transfer dominates the 1,098-row profile; targeted transfer is more useful than an undifferentiated new F4 topic. |
| 8 | `pt_infinitivo_pessoal`; ≈B1-B2? | `8 Sintaxe e discurso` | F1/F2/F5 | `bank+deterministic`: infinitive person/number plus overt-subject/coreference metadata | **Yes — infinitive-subject validator** | Camões starts it around B1 while FUNAG foregrounds it at B2; no live unit covers it. |
| 9 | `pt_infinitivo_pessoal_composto`; ≈B2 | `8 Sintaxe e discurso` | F1/F2/F5 | `bank+deterministic`: auxiliary/participle/person rows with subject metadata | **Yes — structured compound-infinitive check** | Explicit FUNAG B2-equivalent content and a prerequisite for advanced clause compression. |
| 10 | `pt_oracoes_reduzidas`; ≈B2 | `8 Sintaxe e discurso` | F2/F3 | `bank+deterministic`: finite↔infinitive/gerund/participle pairs with subject and relation labels | **Yes — paired-transform/subject consistency check** | FUNAG explicitly lists reduced clauses; none is live. |
| 11 | `pt_relativos_regidos`; ≈B1-B2 | `8 Sintaxe e discurso` | F1/F2/F3 | `blind K=3`: antecedent/function/government bank plus `que/quem/o qual/cujo/onde` inventory | **Yes — antecedent/government metadata validator** | Governed relatives occur in Camões/FUNAG progression and are wholly uncovered. |
| 12 | `pt_passiva_ser`; ≈B1 | `8 Sintaxe e discurso` | F1/F2/F3 | `bank+deterministic`: auxiliary tense, passive subject gender/number, participle and agent metadata | **Yes — passive agreement checker** | The analytic passive is expected before advanced levels and absent live. |
| 13 | `pt_passiva_se`; ≈B2 | `8 Sintaxe e discurso` | F1/F2/F3 | `bank+deterministic`: transitivity, passive/impersonal classification and verb-number metadata | **Yes — `se` type/agreement verifier** | FUNAG explicitly includes synthetic passive; BR usage requires distinguishing passive from impersonal `se`. |
| 14 | `pt_regencia_nominal`; ≈B2 | `6 Regência` | F1/F3 | `bank+deterministic`: noun/adjective-preposition-sense triples with exact contractions | No | FUNAG names nominal as well as verbal government; the live unit covers only verbs. |
| 15 | `pt_tempos_compostos_indicativo`; ≈B2 | `1 Tempos` | F1/F2/F5 | `morph`: future-perfect and conditional-perfect forms from BR-compatible tables | No | Explicit FUNAG intermediate-II coverage is absent live. |
| 16 | `pt_tempos_compostos_subjuntivo`; ≈B2 | `3 Subjuntivo` | F1/F2/F5 | `morph`: perfect, pluperfect and future-perfect subjunctive forms from BR-compatible tables | No | Completes the compound mood system that current present/future units omit. |
| 17 | `pt_discurso_indireto`; ≈B1-B2 | `8 Sintaxe e discurso` | F2/F3 | `bank+deterministic`: direct/indirect pairs with tense, person and deixis metadata | No | Reported discourse is in the Camões/FUNAG progression and currently absent. |
| 18 | `pt_modalizacao_registro_br`; C1? | `8 Sintaxe e discurso` | F2/F3 | `bank+deterministic`: reviewed Brazilian hedge, stance, address and formality bank tied to genre | No | FUNAG/Celpe-Bras make modalisation and register the clearest advanced target, but not a fixed CEFR grammar item. |

### German — 18 candidates

| Rank | Proposed key; level | Cluster | Format | Verification tier and required data | New verifier machinery? | One-line rationale |
|---:|---|---|---|---|---|---|
| 1 | `de_genitiv`; B1-B2 | `5 Kasus` | F1/F3/F5 | `morph`: existing `de_np` declension matrices plus genitive noun-class and preposition rows | No — extend data used by `de_np` | Fifteen supplied/avoided genitives plus GGP's B1/B2 progression make this the strongest remaining case gap. |
| 2 | `de_n_deklination`; B1-B2? | `5 Kasus` | F1/F3/F5 | `bank+deterministic`: noun-class table with case/number and expected weak-noun ending | No — deterministic noun table is sufficient | Three direct missing/spurious `-n` errors recur; exact onset is not exposed in the public GGP list. |
| 3 | `de_praefixverben_kontrast`; A2-B1? | `4 Verben` | F2/F3 | `bank+deterministic`: separable/inseparable prefix and meaning-pair bank with finite/non-finite placement | No | Prefix confusion/avoidance appears in learner material; the exact public GGP level is unavailable. |
| 4 | `de_konjunktiv2_irreal`; B2 | `4 Verben` | F1/F2/F5 | `morph`: KII table plus banked wish/condition/politeness cues | No — extend morphology aliases/data | Eight supplied KII examples suggest avoidance, and GGP explicitly samples unreal wishes at B2. |
| 5 | `de_dapronomen_regime`; B1-C1? | `2 Präpositionen` | F1/F2/F3 | `bank+deterministic`: governed preposition/case plus `da(r)-/wo(r)-` form table | No | Seven supplied da-compound/regime examples expose an uncovered system; the upper progression is course-inferred. |
| 6 | `de_relativpronomen_kasus`; B1 | `6 Pronomen` | F1/F2/F3 | `blind K=3`: antecedent role/case/preposition bank and closed relative-pronoun paradigm | **Yes — antecedent-role/case validator** | GGP samples relative `was/wo` at B1, while no live relative unit exists. |
| 7 | `de_nebensatz_wortstellung`; A2-B1 | `7 Satzbau` | F1/F3/F5 | `bank+deterministic`: connector, clause type, finite head and expected bracket/order metadata | No | V2 versus verb-final order is foundational and absent from the current curriculum. |
| 8 | `de_konjunktiv1_indirekte_rede`; B2 | `4 Verben` | F1/F2/F5 | `morph`: KI paradigm plus source/reporting cue bank | No — extend morphology aliases/data | GGP explicitly places Konjunktiv I at B2; little spontaneous evidence likely reflects opportunity/avoidance. |
| 9 | `de_zustandspassiv`; B2? | `4 Verben` | F1/F2/F3 | `bank+deterministic`: event/state pairs for `werden` versus `sein + Partizip II` | No | Complements live process passive; exact B2 onset comes from mixed B2/C1 teaching sources. |
| 10 | `de_passiv_modal_perfekt`; C1? | `4 Verben` | F1/F3/F5 | `bank+deterministic`: structured auxiliary/participle/modal/infinitive chain table | **Yes — multi-verb-chain/order verifier** | Live passive covers limited frames, not full perfect/modal/double-infinitive order supported by C1 courses. |
| 11 | `de_passiversatzformen`; B2 | `4 Verben` | F2/F3 | `bank+deterministic`: paraphrase triples for `lassen`, `sein + zu`, and `-bar` | No | Explicit BAMF/Goethe B2 content and a major missing voice branch. |
| 12 | `de_modalverben_subjektiv`; B2-C1? | `4 Verben` | F1/F2 | `bank+deterministic`: evidential-strength and tense-labelled modal-meaning frames | No | Upper courses distinguish objective from subjective modal use; exact mastery boundary is uncertain. |
| 13 | `de_konnektoren_logik`; B1-B2 | `7 Satzbau` | F1/F2/F3 | `blind K=3`: relation-labelled connector bank and closed answer subsets per relation | No | BAMF expects temporal, causal, conditional, concessive and modal relations; none is live. |
| 14 | `de_nomen_adjektiv_praep_regime`; B2-C1? | `2 Präpositionen` | F1/F3 | `bank+deterministic`: noun/adjective-preposition-case-sense triples | No | Extends live verb/dative work to noun and adjective government; Goethe C1 teaches all three classes. |
| 15 | `de_nominalisierung_verbalstil`; C1? | `8 Wortbildung & Register` | F2/F3 | `bank+deterministic`: paired nominal/verbal transformations with preserved roles and tense | **Yes — paired-transform constraint checker** | Goethe C1 and BAMF support formal nominal style, but GGP supplies no C1 assignment. |
| 16 | `de_partizipialattribute`; C1? | `3 Adjektive` | F1/F2/F5 | `morph`: participle formation plus `de_np` agreement, with expanded-NP head/case metadata | **Yes — expanded-NP metadata/check** | Goethe C1 explicitly covers expanded Partizip I/II attributes; live adjective cards test simpler NPs. |
| 17 | `de_informationsstruktur_vorfeld`; B2-C1? | `7 Satzbau` | F2/F3 | `bank+deterministic`: neutral/marked movement pairs labelled topic, focus, inversion and register | No | BAMF includes inversion/field control; discourse appropriateness at C1 is inferred. |
| 18 | `de_ru_interferenz_kasus`; Remedial | `10 Interferenz` | F2/F3 | `bank+deterministic`: reviewed Russian→German gender/case/geographic-article contrasts and attested corrections | No | Directly targets the documented L1 transfer without pretending it has a CEFR level. |

## Sequencing and promotion gates

### Recommended waves

1. **Evidence repair:** build ranks 1-5 for Spanish, French, Italian, Portuguese, and German. These are not necessarily the largest units; they are the best-supported omissions. Start by extending existing banks where the verifier already works.
2. **B1/B2 structural completion:** add pronoun/relative, mood-selection, voice, compound-tense, condition and clause-order units whose levels are supported by a language-specific inventory. Within this wave, prerequisites in the taxonomy snapshots determine order.
3. **Upper-B2 integration:** promote reported speech, non-finite clauses, marked information structure, and discourse connectors only after their component morphology/selection units produce stable retrieval data.
4. **C1 validation:** do not promote a `C1?` unit solely because it appears in a course syllabus. Require either a second independent Italian/German/BR source, a teacher-attested need, or telemetry showing the prerequisite distinction is active and weak. French passé simple should remain reception-biased unless production need appears.

### Gate for every candidate

1. **No overlap:** re-import `topics_for()` and confirm the key and tested decision do not already exist. An extension may share a cluster but must have distinct telemetry.
2. **Source/data record:** record the inventory source, target variety, bank provenance/licence, level confidence, and any regional/register restriction. European Portuguese rows fail this gate unless adapted and independently checked for Brazilian usage.
3. **Uniqueness:** an F1/F2 item must have one recoverable answer or interpretation. Closed-class generation uses `blind K=3`; a fixed reviewed pair uses `bank+deterministic`; form-only targets use `morph`.
4. **Deterministic assertions:** morphology/table candidates must test every person, number, gender, case or agreement cell that can be emitted. Bank candidates must reject unknown answers and orphaned metadata. New machinery named in the tables needs its own adversarial tests before content generation.
5. **Format discipline:** keep F5 rare and orienting; it cannot substitute for retrieval. F3 must preserve the learner's actual error or be clearly labelled a documented typical error, never fabricate personal history.
6. **Telemetry gate:** ship a small batch, review ambiguity/rejection and confusion data, then expand. “No recorded errors” is meaningful only after the learner had repeated obligatory opportunities.

## Uncertainty register

- **Spanish:** PCIC directly supports most levels; only consolidated cross-level bundles and pedagogical placement of remedial derivation/collocation work carry `?`.
- **French:** future simple, plus-que-parfait, initial subjunctive, and passé simple disagree across the open inventories; C1 coverage is low-consensus.
- **Italian:** the detailed YAML marks each disputed Profilo/CILS boundary and every C1 node individually. Profilo is authoritative only through B2.
- **Brazilian Portuguese:** every CEFR label is approximate; personal infinitive timing and all concrete C1 structures have additional uncertainty. BR usage, not Camões's European norm, is controlling.
- **German:** sampled A1-B2 GGP features are usable, but unavailable feature-level details make some boundaries uncertain; every C1 assignment is explicitly provisional.

## Deliverable index

- [Detailed Italian A2-C1 tree](it-grammar-taxonomy.yaml)
- [Spanish snapshot](taxonomies/es.yaml)
- [French snapshot](taxonomies/fr.yaml)
- [Italian snapshot](taxonomies/it.yaml)
- [Brazilian Portuguese snapshot](taxonomies/pt.yaml)
- [German snapshot](taxonomies/de.yaml)
