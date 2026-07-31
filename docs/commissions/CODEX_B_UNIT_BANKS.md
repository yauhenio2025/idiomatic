# Codex commission B: data banks for the evidence-based new grammar units

> Substantial task. Work dir: `/home/admin/projects/idiomatic/` (the repo).
> Write ONLY under `idiomatic/grammar/data/` and `docs/commissions/unit-specs/`.
> NO git commits or pushes (a push mid-generation-run kills prod runs;
> the supervising session commits after review). Read for context:
> `docs/commissions/ERROR_PROFILE_PROPOSAL.md`, the five
> `docs/research/error-profiles/*.md`, `idiomatic/grammar/curriculum.py`,
> `idiomatic/grammar/data/es_verb_prep.json` and `de_preps.json`
> (the two existing, human-validated bank formats),
> `idiomatic/grammar/generate.py` (how banks feed prompts).

## Goal

Build the vetted data banks that the Wave-7 Phase-2 units will
generate from, one JSON file per bank, mirroring the quality bar of
`es_verb_prep.json` (which was itself a codex product, review-validated).
Banks are NOT curriculum code — do not touch curriculum.py or
units_fip.json. For each bank also write a short unit spec in
`docs/commissions/unit-specs/<key>.md` (unit key, cluster, format
F1/F3/F5, verification tier, guidance draft for the generator prompt,
size recommendation).

## Banks to build (priority order)

1. `fr_quantites_de.json` — the #1 French error (161 rows; `beaucoup
   des` 138×): quantifier + de/d'/des rules. Entries: {frame, correct,
   trap, rule_en, example}. Cover beaucoup/trop/assez/peu/plus/moins de,
   pas de, d'autres, la plupart des, bien des, des→de before adj-noun.
2. `fr_prep_lieux.json` — à/en/au(x)/dans + city/country/region/island
   (`en Berlin` 36×): {place, place_type, gender, correct_prep,
   example}. ≥120 places incl. every country/city in the learner's news
   diet (politics/tech/Europe; read the error profiles for his actual
   place names).
3. `fr_genre_noyau.json` — HIS ~40 wrong-gender nouns (extract the list
   from docs/research/error-profiles/fr.md §2.2) + ~60 same-pattern
   traps (nouns in -ode/-ade/-ure, -age, -eau, Greek -ème/-ame):
   {noun, gender, trap_reason, example}.
4. `fr_an_annee.json` — an/année, jour/journée, matin/matinée,
   soir/soirée: {frame, correct, rule_en, example}. ≥60 frames.
5. `pt_gender_core.json` — from pt.md §6: -ma masculines, -agem
   feminines, his attested wrong-gender nouns, dois/duas, uns/umas,
   article+contraction agreement: {noun_or_frame, gender_or_correct,
   trap_reason, example}. ≥120 entries.
6. `pt_regencia_verbal.json` — Brazilian-PT verb regimes mirroring
   es_verb_prep.json format exactly (tentar Ø+inf, conseguir Ø,
   dedicar-se a, pertencer a, depender de, gostar de, precisar de,
   em+country w/ article…). ≥60 regimes, BR usage.
7. `it_genere_plurali.json` — USER-CONFIRMED weakness: articles
   il/lo/la/i/gli/le + plural endings -o→-i, -a→-e, -e→-i + irregulars
   (il problema/i problemi, la mano/le mani, l'uovo/le uova, il
   braccio/le braccia, la città/le città…) + gender traps: {noun,
   gender, singular, plural, article_sg, article_pl, trap_reason}.
   ≥150 nouns, frequency-ordered, news-register bias.
8. `it_reggenze_verbali.json` — Italian verb+prep regimes (cercare di,
   riuscire a, dipendere da, partecipare a, consistere in,
   contare su…), es_verb_prep.json format. ≥60 regimes.
9. `es_muy_mucho.json` — frames forcing muy vs mucho/mucha/muchos/
   muchas/mucho más/tan/tanto (his 7 attested errors as anchor traps):
   {frame, correct, rule_en}. ≥50 frames.
10. `de_dativ_verben.json` — dative-object verbs (gehören, widmen,
    entsprechen, widerstehen, vertrauen, zustimmen, gratulieren…):
    {verb, case, example_frame, example_answer}. ≥50 verbs.

## Quality bar (what made es_verb_prep.json shippable)

- Every entry independently checkable: no invented words, standard
  variety (BR Portuguese, standard Italian/French/German/European
  Spanish), one unambiguous correct answer per frame/trap.
- Frequency-first ordering; register = news/professional (the learner
  reads geopolitics/tech daily).
- JSON must parse; consistent keys within each file; include a "_meta"
  header object per file: {source_evidence: profile section, format,
  built: "2026-07-31", validation_notes}.
- Self-check pass: after building each bank, re-read it hunting for
  wrong genders/regimes/plurals — list anything you were unsure about
  in the unit spec file rather than silently including it.

## Deliverables

- 10 bank JSON files in `idiomatic/grammar/data/`.
- 10 spec files in `docs/commissions/unit-specs/`.
- `docs/commissions/unit-specs/README.md` — index + per-bank entry
  counts + open questions for the reviewing session.
