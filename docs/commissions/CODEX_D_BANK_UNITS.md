# Codex commission D: wire the 10 bank-backed grammar units (Wave 7 Phase 2)

> Work dir: /home/admin/projects/idiomatic-wt/units (isolated git
> worktree). Edit code there ONLY. No commits/pushes — supervising
> session reviews and merges. `uv run pytest tests/` must pass. Read:
> docs/commissions/unit-specs/*.md (all 10 specs + README incl. the
> DECISIONS section), idiomatic/grammar/curriculum.py, generate.py,
> morphology.py, the 10 bank JSONs in idiomatic/grammar/data/.

## Goal

Turn the 10 vetted data banks into live generation units: Topics in
the curriculum, prompt plumbing, and verification. The banks:
fr_quantites_de, fr_prep_lieux, fr_genre_noyau, fr_an_annee,
pt_gender_core, pt_regencia_verbal, it_genere_plurali,
it_reggenze_verbali, es_muy_mucho, de_dativ_verben.

## Decisions already made (implement as stated)

- Clusters: per each unit's spec file; Italian cluster strings are
  FINAL: "5 Genere e plurali", "6 Reggenze" (README DECISIONS).
- de_dativ_verben verification: Tier B blind-fill (K=3) + static case
  check from the bank — do NOT build an NP-inflection engine.
- Every bank JSON is an array whose element 0 is {"_meta": …} —
  loaders must drop it (README "Loader contract"). pt/it regime banks
  reuse the es_verb_prep key names incl. `example_es` holding
  target-language text.
- Unit keys = bank filenames minus .json. Append Topics to each
  language's list (sort_order follows list position; grammar_units
  boot seeding handles the DB).

## Implementation shape

1. curriculum.py: add the 10 Topics (label/symbol/cluster/guidance from
   each spec file; guidance drafts exist there — tighten to the house
   style of existing Topics). bank= set to the JSON filename. verify=
   per spec: deterministic bank lookups where the spec says
   "deterministic" (gender/plural/article facts), "blind" where it
   says blind. Remove nothing; touch no existing Topic.
2. generate.py: extend the bank plumbing so these banks feed prompts
   the way es_verb_prep.json does (_bank_lines currently assumes the
   verb+prep shape — generalize per bank schema; keep prompts in the
   existing style). Verification: extend verify_item for the new
   verify modes — e.g. gender banks: answer must equal the bank's
   article/gender/plural for the named noun (the generator must be
   prompted to return the noun in a `meta`-style field the same way
   de units return noun/prep/case — follow that existing pattern);
   an/année + quantites + muy_mucho: closed answer_set + blind.
   Where the spec's verification idea conflicts with what generate.py
   can actually support cleanly, prefer the existing mechanism and
   note the deviation.
3. tests: extend tests/test_grammar.py style — every new unit's bank
   loads, prompts build, verify_item accepts a hand-written correct
   item and rejects a wrong-answer item, for ALL 10 units. Cluster/
   seed-row completeness test must keep passing (PLANNED_UNITS: leave
   as-is; none of the 10 overlap with planned keys).
4. docs/commissions/unit-specs/README.md: append an IMPLEMENTED
   section listing what deviated from spec and why.

## Hard rules

- Model/templates/GUIDs FROZEN. No generation runs, no network, no git
  ops. Files you may touch: idiomatic/grammar/curriculum.py,
  idiomatic/grammar/generate.py, idiomatic/grammar/morphology.py (only
  if genuinely needed), tests/, docs/commissions/unit-specs/. Nothing
  else. `uv run pytest tests/` green at the end.
