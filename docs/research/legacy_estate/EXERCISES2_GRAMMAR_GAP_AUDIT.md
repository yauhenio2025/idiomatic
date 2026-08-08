# Exercises2 grammar gap audit: COMMANDS, PRONOUNS, REFLEXIVE

Audit date: 2026-08-08

Machine-readable companion: `docs/research/legacy_estate/exercises2_grammar_gap_audit.json`

## Decision

**No import.** None of the 400 canonical shared rows, the 400 repaired Italian translations, or the 1,600 matching DE/ES/FR/PT estate notes is approved for import, authoring, packaging, audio, or delivery.

The corpus is useful as a map of structural intentions, but not as production content. Current coverage is uneven rather than absent; the old English and target-language text has material quality and register problems; and 50 of the 150 source rows filed under `RELFEXIVE` are actually plural commands. Any approved follow-up should create new, independently verified curriculum items for the uncovered objectives.

This report closes only the roadmap's analytical COMMANDS / PRONOUNS / REFLEXIVE lane. It does not create cards or change a live deck.

## Executive result

Counts below are **covered / partial / gap / misfiled source-row equivalents**. Coverage is assigned at the contiguous authored-block level, not as a claim that an old translation is reusable. `Misfiled` applies only to the 50 command rows inside `RELFEXIVE` and is excluded from that topic's 100-row reflexive denominator.

| Topic | DE | ES | FR | IT | PT |
|---|---:|---:|---:|---:|---:|
| COMMANDS (100) | 0 / 50 / 50 / 0 | 50 / 50 / 0 / 0 | 0 / 0 / 100 / 0 | 0 / 100 / 0 / 0 | 0 / 100 / 0 / 0 |
| PRONOUNS (150) | 0 / 100 / 50 / 0 | 100 / 50 / 0 / 0 | 0 / 100 / 50 / 0 | 0 / 100 / 50 / 0 | 0 / 150 / 0 / 0 |
| RELFEXIVE (150) | 0 / 0 / 100 / 50 | 0 / 100 / 0 / 50 | 0 / 0 / 100 / 50 | 0 / 100 / 0 / 50 | 0 / 100 / 0 / 50 |

The actionable reading is:

- Spanish already has the broadest command and object-clitic curriculum. Its remaining gap is integration: clitics inside infinitives and affirmative/negative commands, plus a genuine pronominal-verb objective.
- German has useful dative-case coverage but no imperative, personal-object-pronoun, or reflexive-verb unit.
- French has only `y/en`; it still lacks general object clitics, imperatives, and the strongly evidenced pronominal-verb unit.
- Italian has a strong `ci/ne` and procomplementary foothold plus a five-card imperative sample, but its own taxonomy shows missing A2 basic pronouns/reflexives and B1 double-clitic placement.
- Portuguese has a useful Brazilian placement bank plus a four-card `vir` imperative sample. It needs broader recipient/pronominal coverage and a settled Brazilian command policy, not the legacy deck's mixed register.

## Audited source and hashes

The five input files contain the 400 canonical English prompts and all four old DE/ES/FR/PT references. The five output files contain the repaired Italian translations used only to identify structural intent.

| Role | Path | Rows | ID range | SHA-256 |
|---|---|---:|---|---|
| Canonical + refs | `idiomatic/grammar/data/exercises2/it_rebuild/input/commands_01.json` | 100 | `it_commands_001`–`it_commands_100` | `3b953f3fd7c601e1cb4537b61b33942d6a3b7eed5ce0904f9958e1f0b0d47cee` |
| Repaired IT | `idiomatic/grammar/data/exercises2/it_rebuild/output/commands_01.json` | 100 | `it_commands_001`–`it_commands_100` | `f1bbbdb5c11c8b494f320ff8b264cfc39c29d17cceab59042adda24c131ecd72` |
| Canonical + refs | `idiomatic/grammar/data/exercises2/it_rebuild/input/pronouns_01.json` | 130 | `it_pronouns_001`–`it_pronouns_130` | `8fa81c465f4eede82ebd6c0e2ff9ad00af6d9c8c5b077ff74c8ae0c2899115a0` |
| Canonical + refs | `idiomatic/grammar/data/exercises2/it_rebuild/input/pronouns_02.json` | 20 | `it_pronouns_131`–`it_pronouns_150` | `eedba0e9c90306d8249981c149f34b08dc52651b56c5f2ebbc36ca20a7085031` |
| Repaired IT | `idiomatic/grammar/data/exercises2/it_rebuild/output/pronouns_01.json` | 130 | `it_pronouns_001`–`it_pronouns_130` | `2333ca319f2709be71e05b8d36050242de88423025a43b34998b643732572a3a` |
| Repaired IT | `idiomatic/grammar/data/exercises2/it_rebuild/output/pronouns_02.json` | 20 | `it_pronouns_131`–`it_pronouns_150` | `20f8b299a3503061e35c2925cf6538bc1ebb0bdcf2bc7f759282b0782c5189cd` |
| Canonical + refs | `idiomatic/grammar/data/exercises2/it_rebuild/input/relfexive_01.json` | 130 | `it_relfexive_001`–`it_relfexive_130` | `e9f4d641021b5f13e34191c6822e664bbbb657fc6af5391c72f6a2ec74bbd119` |
| Canonical + refs | `idiomatic/grammar/data/exercises2/it_rebuild/input/relfexive_02.json` | 20 | `it_relfexive_131`–`it_relfexive_150` | `f1b3dabb0e1caef90ed1b6d8a13988661eae09bbf90d6063467335edd756ac1e` |
| Repaired IT | `idiomatic/grammar/data/exercises2/it_rebuild/output/relfexive_01.json` | 130 | `it_relfexive_001`–`it_relfexive_130` | `a22429852303bf6eaad67639379b1e268ef58ea9618605744a8159803c1dc489` |
| Repaired IT | `idiomatic/grammar/data/exercises2/it_rebuild/output/relfexive_02.json` | 20 | `it_relfexive_131`–`it_relfexive_150` | `4256297e47134e119c2905c4cf7cca96a83898dedf92ea375b2715d7df551dc3` |

Integrity checks found 400 unique, contiguous canonical IDs; 400 nonempty English prompts; four nonempty references on every input row; a one-to-one 400-ID repaired-Italian join; and zero exact English duplicate groups inside this 400-row scope.

The full evidence ledger, including hashes for the commission, roadmap, prior audit, estate manifest, curriculum, deterministic banks, Tenses Rescue, error profiles, and Italian taxonomy, is recorded in the companion JSON. Important code/data anchors were:

| Evidence | SHA-256 |
|---|---|
| `docs/research/legacy_estate/manifest.json` | `65aed9b0b7bb10452c74f90514010d9b07c83d165a9da87f20ae31d6b046291b` |
| `idiomatic/grammar/curriculum.py` | `9164b26f3554b22f09f58d97adb6d66649b1efb97a6adf03dee78b1689093f29` |
| `idiomatic/grammar/data/units_fip.json` | `39b94b77c7dfc91e91025a3c5bb5d97dc8bf97fa8cdadec336e8fc8dbc76196c` |
| `idiomatic/grammar/translation.py` | `ace88f89e310e0ac7152f79eaae7f5b506a89d54a03b9f17ec721d56e58f95dd` |
| `idiomatic/grammar/data/tenses/batch1.json` | `9deae900cb3a641d5da32cb01f7c98461f6003b7e0c9054f519383a06fd7d20c` |
| `docs/research/it-grammar-taxonomy.yaml` | `6bc1ebb4996fda896befe5d59e4ee3deb0794a53daca4574344bae441d0a8fc0` |

## Estate evidence

The fresh +2-account manifest contains 12 matching decks: COMMANDS, PRONOUNS, and a spelling variant of REFLEXIVE for each of DE, ES, FR, and PT. Together they contain 1,600 notes/cards: 400 per language, each a normalized-exact canonical prompt-and-pair match.

All 12 decks have zero reps, zero reviews, zero mature cards, and zero `[sound:]` tags. There is no scheduling or audio value to preserve.

There is no fresh `EXCERCISES::IT` tree. The settled audit finding remains that all 2,612 former Italian exercise backs were byte-identical French copies. The repaired Italian files therefore supply structural evidence only; they do not restore estate provenance.

## Live coverage snapshot

Production was read through the authenticated, read-only `/ui/api/grammar/overview` and `/ui/api/delivery?limit=500` endpoints at `2026-08-08T04:41:49Z`. Every deck listed below was acknowledged successfully.

| Lang | Grammar deck | Relevant verified units | Translation deck | Tenses production + exercise | Relevant Tenses slice |
|---|---:|---|---:|---:|---|
| DE | 101 | `de_dativ_verben` 7 | 79 | 18 + 18 | none |
| ES | 288 | `es_cmd_tu` 21; `es_cmd_usted` 12; `es_cmd_neg` 12; `es_clitics_dir` 11; `es_clitics_ind` 12; `es_clitics_selo` 17 | 250 | 18 + 18 | none |
| FR | 185 | `fr_pronoms_y_en` 12 | 146 | 18 + 18 | none |
| IT | 156 | `it_clitici_ci_ne` 11 | 130 | 17 + 17 | 5 `volere` imperative cells |
| PT | 165 | `pt_clitic_placement` 11 | 127 | 14 + 14 | 4 `vir` imperative cells |

Translation does not add coverage. Its selector mirrors verified grammar items, excludes F3/F4/explainers, requires usable text and target audio, rejects short/duplicate sentences, and preserves the source grammar topic. It can reinforce a mapped unit, but it cannot close a missing structural objective. The DE/FR/IT/PT translation APKGs were built on August 4, before their current August 7 grammar APKGs; only Spanish's August 7 translation build follows its current grammar build. The four older totals therefore do not prove that a newly live unit is present in translation.

Likewise, Tenses Rescue counts here only where it explicitly drills an imperative. DE, ES, and FR have no relevant tense-profile rows. IT's five `volere` cells and PT's four `vir` cells are narrow samples, not general command curricula. No Tenses Rescue item has a pronoun or reflexive objective.

## Reproducible source-row buckets

The corpus changes its template and objective in contiguous 50-row blocks. Those authored boundaries—not subjective sentence-by-sentence salvage judgments—are the audit unit.

| Key | IDs | Rows | Structural objective | Exact measured traits |
|---|---|---:|---|---|
| C1 | `it_commands_001`–`050` | 50 | Commands plus recipients/direct/indirect objects; Romance references often require clitic placement or clusters | 26 negative, 24 affirmative English commands |
| C2 | `it_commands_051`–`100` | 50 | General topical commands, including polarity and occasional hortative intent | 6 negative commands; 2 English rows contain “let's” |
| P1 | `it_pronouns_001`–`050` | 50 | Recipient, direct, indirect, and double objects across finite/modal clauses | one authored block |
| P2 | `it_pronouns_051`–`100` | 50 | Human matrix object plus embedded non-human object/control or complement syntax | all 50 contain English “it” |
| P3 | `it_pronouns_101`–`150` | 50 | Singular recipients, tonic complements, and formal-address contrasts | 11 explicitly say “(formal)” |
| R1 | `it_relfexive_001`–`050` | 50 | Finite self-directed or lexically pronominal constructions | all 50 have an explicit English reflexive pronoun |
| R2 | `it_relfexive_051`–`100` | 50 | Infinitive/lexical pronominality, often visible only in target references | only 1 explicit English reflexive pronoun (`089`) |
| R3 | `it_relfexive_101`–`150` | 50 | Vocative plural commands; wrong topic | 50 commands; only 2 explicit reflexives (`108`, `144`) |

## COMMANDS findings

### German — partial: 0 covered / 50 partial / 50 gap

`de_dativ_verben` makes C1 partial because it teaches recipient case selection, but it blanks complete noun phrases and has no imperative objective. C2 has no mapping. The uncovered system is du/ihr/Sie imperative morphology, negative commands, separable-verb behavior, and pronoun/recipient placement.

Recommendation: propose `de_imperativ`, starting with verified du, ihr, and Sie forms and negation, then add a bounded accusative/dative-recipient integration slice. Priority is medium: the curriculum gap is certain, but the learner corpus has no imperative opportunities.

### Spanish — partial: 50 covered / 50 partial / 0 gap

C2 is covered by `es_cmd_tu`, `es_cmd_usted`, and `es_cmd_neg`. C1 is only partial: the three command units and three clitic units exist, but no objective joins affirmative-command enclisis, negative-command proclisis, accent behavior, and `le + lo → se lo` in a command.

Recommendation: add a bounded `es_cmd_clitics_integration` slice to the existing units. Do not create another general-command deck. The error profile's zero command count is a genre gap, while the late `comprar le lo → comprárselo` error directly supports the integration work.

### French — gap: 0 / 0 / 100

Neither block has a live imperative mapping. `fr_pronoms_y_en` is not command coverage.

Recommendation: propose `fr_imperatif` for tu/nous/vous, polarity, high-frequency irregulars, then a separately verified clitic-order/hyphenation extension. Priority is medium because the structural gap is clear but command opportunities are not quantified in the error profile.

### Italian — partial: 0 / 100 / 0

The five `volere` imperative cells give both blocks narrow morphology coverage, but they do not teach a productive imperative across verbs. `it_clitici_ci_ne` overlaps only selected pronominal constructions, not C1's direct/indirect/double-clitic placement.

Recommendation: propose `it_imperativo`, explicitly mapped to taxonomy node `it_a2_future_imperative` (affirmative and negative tu/noi/voi), followed by the placement portion of `it_b1_double_clitics`. Priority is medium and taxonomy-driven; learner-specific Italian data is too thin to rank command errors.

### Portuguese — partial: 0 / 100 / 0

Four `vir` imperative cells plus the selected placement frames in `pt_clitic_placement` are a foothold, not a general command system. The legacy references cannot settle the scope because they mix true imperatives and bare infinitives.

Recommendation: propose `pt_imperativo_br` under the current Brazilian policy, with você/vocês/nós, affirmative/negative contrast, then integrate command-specific clitic placement. Resolve the Tenses Rescue 2s `vem` sample against that policy rather than inheriting the legacy mixture.

## PRONOUNS findings

### German — partial: 0 covered / 100 partial / 50 gap

P1 and P3 partially map to `de_dativ_verben` through dative recipient selection. That unit deliberately teaches full noun phrases, not pronoun forms. P2's layered object-control/complement architecture has no useful current mapping.

Recommendation: propose `de_objektpronomen_akk_dat`: personal accusative/dative paradigms, explicit case selection, `jemandem/jemanden`, recipient-plus-thing order, and later a bounded embedded-clause slice. Priority is high because the learner evidence includes four verbatim object-case errors and repeated dative-verb remediation.

### Spanish — partial: 100 / 50 / 0

P1 and P3 map directly to `es_clitics_dir`, `es_clitics_ind`, and `es_clitics_selo`. P2 is partial because basic clitic identity is live, but placement across infinitives/gerunds/commands and matrix-plus-embedded object combinations is not a distinct objective.

Recommendation: extend the current clitic units with deterministic `es_clitics_placement_integration` cards. Priority is high; the year-four `le lo` error is exactly the rule boundary to teach.

### French — partial: 0 / 100 / 50

P1 and P2 have limited semantic overlap with `fr_pronoms_y_en`, but the unit explicitly excludes human antecedents and does not teach `le/la/les/lui/leur`, tonic complements, or double-clitic ordering. P3 is a gap.

Recommendation: propose high-priority `fr_pronoms_objets` for direct, indirect, tonic, and ordered double-object pronouns, keeping `fr_pronoms_y_en` as a narrower sibling/prerequisite. The error profile records a missing object clitic and roughly 95 pronoun-family errors; `y/en` alone is plainly insufficient.

### Italian — partial: 0 / 100 / 50

P1 and P2 have limited `ci/ne/ce ne` overlap through `it_clitici_ci_ne`; P3's basic recipient and tonic-person system is absent. The 15 live `it_passato_prossimo` cards contain no clitic objective and therefore do not count as coverage.

Recommendation: build the taxonomy in dependency order: A2 `it_a2_pronouns_clitics` as `it_pronomi_diretti_indiretti`, then B1 `it_b1_double_clitics` as `it_doppi_clitici`; retain the current `it_b1_ci_ne` branch. Cover tonic complements, direct/indirect forms, `glielo` clusters, agreement, and placement with infinitives, modals, and imperatives. Priority is high for the curriculum dependency, while learner-specific evidence is strongest only for the already-live ci/ne/procomplementary branch.

### Portuguese — partial: 0 / 150 / 0

All three blocks overlap `pt_clitic_placement`, whose bank covers 18 infinitive-enclisis rows, six `comigo/conosco` rows, and 16 finite proclisis rows. It still does not define the complete direct/indirect recipient inventory, register-sensitive `lhe` versus `o/a`, or double objects.

Recommendation: high-priority extension of `pt_clitic_placement` with separately verified recipient and double-object frames under an explicit Brazilian register policy. The learner profile gives about 21 direct error/remediation signals for the existing placement mechanics; the broader recipient scope is curriculum-driven.

## REFLEXIVE findings

R3 is not counted as reflexive coverage for any language. Its 50 rows are routed to the COMMANDS conclusions above, where the routed status is DE gap, ES partial, FR gap, IT partial, and PT partial. The rows are still not import candidates.

### German — gap: 0 covered / 0 partial / 100 gap / 50 misfiled

No current unit teaches lexical reflexivity, accusative versus dative reflexive pronouns, or placement. A few reflexive verbs appearing incidentally in the dative bank do not make that a reflexive objective.

Recommendation: a small, low-priority `de_reflexive_verben` unit with explicit reflexive/non-reflexive contrasts and case. The only direct learner signal is the spurious `sich` in `Auswirkungen haben`, so better-evidenced case units should come first.

### Spanish — partial: 0 / 100 / 0 / 50

The current direct-clitic answer set contains overlapping surface forms (`me/te/nos/os`), but its guidance is object-clitic selection, not lexical reflexivity. The command units cover some R3 morphology but not pronominal-command placement.

Recommendation: propose `es_verbos_pronominales` for lexical `se` contrasts, person agreement, meaning changes, infinitive placement, and later command integration. Priority is medium; `me fue → me fui` and repeated `irse` remediation support the direction without proving a broad frequency ranking.

### French — gap: 0 / 0 / 100 / 50

`fr_pronoms_y_en` does not cover `se`. There is no lexical pronominal-verb, reflexive-infinitive, auxiliary/agreement, or pronominal-imperative objective.

Recommendation: high-priority `fr_verbes_pronominaux`, covering dropped versus spurious `se`, infinitive placement, and passé-composé auxiliary/agreement. The error profile identifies at least 15 direct pronominal-verb errors and already proposes this unit.

### Italian — partial: 0 / 100 / 0 / 50

`it_clitici_ci_ne` has selected reflexive procomplementary clusters, but it is not the basic A2 reflexive paradigm. The 15 live `it_passato_prossimo` cards contain no clitic objective, and the five `volere` imperative cells only partially cover routed R3 commands.

Recommendation: propose `it_verbi_riflessivi` for the basic reflexive slice of `it_a2_pronouns_clitics`, clearly separated from `it_b2_procomplementary_clitics`, and coordinate it with `it_imperativo` and `it_b1_double_clitics`. Priority is medium: the taxonomy is clear, but the learner's strong 74-row remedial signal concerns advanced procomplementaries rather than broad basic-reflexive frequency.

### Portuguese — partial: 0 / 100 / 0 / 50

`pt_clitic_placement` includes selected `se lembra`/`se chama` and related placement frames, but not a broad lexical pronominal-verb inventory or reflexive infinitive/command system. The `vir` imperative cells make routed R3 partial only.

Recommendation: first extend `pt_clitic_placement` with explicit lexical-`se` contrasts plus infinitive and command frames. Split a candidate `pt_verbos_pronominais` only if live lapse data later supports it. Priority is medium because placement has strong learner evidence while broad lexical reflexivity does not.

## Quality limits that force no import

- The prior audit estimates 5–10% old-translation defects and documents literal calques, machine-English, and register inconsistency. The exact references can identify a construction, not certify an answer.
- Spanish COMMANDS are formal `usted` while Spanish PRONOUNS use `tú`; Portuguese COMMANDS mix imperative and bare infinitive. A production unit must set register independently.
- Every P2 row repeats an embedded English “it”. P3 is a 50-row recipient template with recurring unidiomatic double-object English. These are objective sketches, not polished prompts.
- R2 has only one explicit English reflexive pronoun in 50 rows. R3 has only two in 50 and is entirely a vocative command block. A target-language pronominal form cannot repair an underspecified English cue.
- The original Italian estate has no recoverable learning value. Repaired Italian is better evidence, but it has neither estate study history nor permission to bypass normal curriculum verification.
- Zero reps, reviews, mature cards, or sound tags means the relevant estate contributes no learner-priority or audio-preservation signal.

## Methodology and validation

1. Parsed and hashed all five canonical input files and five repaired-Italian outputs. Required contiguous IDs, unique English rows, all four reference-language fields, and exact one-to-one Italian joins.
2. Inspected all 400 English prompts in ID order. Read DE/ES/FR/PT references and repaired Italian only as secondary evidence of the intended target construction.
3. Assigned the source's contiguous authored blocks to C1–C2, P1–P3, and R1–R3. Mechanically counted polarity, “let's,” explicit formal markers, explicit reflexive pronouns, and R3's command contamination.
4. Compared those objectives against the committed curriculum and banks, then against the read-only live grammar/delivery snapshot. A unit counts only when it is verified, delivered, and acknowledged.
5. Treated translation as reinforcement only and Tenses Rescue as relevant only for explicit imperative cells.
6. Applied the fixed status rules: covered means every defining axis is live; partial means at least one is live and another material axis is not; gap means no defining objective is live; misfiled means the rows belong to another topic.
7. Used learner error profiles to rank recommendations and the Italian CEFR taxonomy to order Italian dependencies. No legacy row was promoted into a content pipeline.

Re-run the principal checks with:

```bash
sha256sum \
  idiomatic/grammar/data/exercises2/it_rebuild/input/{commands_01,pronouns_01,pronouns_02,relfexive_01,relfexive_02}.json \
  idiomatic/grammar/data/exercises2/it_rebuild/output/{commands_01,pronouns_01,pronouns_02,relfexive_01,relfexive_02}.json

jq -e '.' docs/research/legacy_estate/exercises2_grammar_gap_audit.json >/dev/null

jq -e '
  (.scope.canonical_rows_total == 400) and
  (.findings | length == 15) and
  ([.findings[] |
    (.row_counts.covered + .row_counts.partial + .row_counts.gap +
     .row_counts.misfiled) == .row_counts.total] | all) and
  (.disposition.rows_selected_for_import == 0)
' docs/research/legacy_estate/exercises2_grammar_gap_audit.json >/dev/null
```

To refresh the unstable production evidence, export the admin token without printing it and query:

```bash
curl -fsS -H "X-Admin-Token: ${IDIOMATIC_ADMIN_TOKEN}" \
  https://idiomatic-app.onrender.com/ui/api/grammar/overview

curl -fsS -H "X-Admin-Token: ${IDIOMATIC_ADMIN_TOKEN}" \
  'https://idiomatic-app.onrender.com/ui/api/delivery?limit=500'
```

The final disposition remains **no-import / analysis complete**.
