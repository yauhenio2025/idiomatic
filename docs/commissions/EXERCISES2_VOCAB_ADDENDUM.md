# Addendum: Waves 4--5 vocabulary batches

This extends `EXERCISES2_BATCH_COMMISSION.md` for `FANCY_VOCAB`,
`BIG_TECH_VOCAB`, `COLD_WAR_VOCAB`, and `GEOPOLITICS`. The committed
Italian-rebuild inputs own prompt order and IDs; reference translations are
fallible old backs, not authoring answers.

## Two formats, two owner gates

No full vocabulary batch may be authored yet.

1. **Vocab gate V1:** author and audit only
   `es_fancy_vocab_pilot_b01.json` (30 source-ordered, stratified verbs,
   nouns, adjectives, and academic lexemes). Present its note/card rendering
   to the owner. Approval unlocks full `FANCY_VOCAB`, `BIG_TECH_VOCAB`, and
   `COLD_WAR_VOCAB` staging/authoring in all five languages.
2. **Definition gate V2:** separately author and audit only
   `es_geopolitics_pilot_b01.json` (30 term--definition prompts). Present its
   term/definition treatment to the owner. Approval unlocks full
   `GEOPOLITICS` staging/authoring in all five languages.

One verdict does not imply the other. A linguistic pass by Codex is not the
owner verdict. Pilot inputs and source hashes live in the corresponding
`batches/manifests/*-pilot.json`; there are deliberately no new-format bulk
outputs in this commission.

## Generic vocabulary notes (V1)

Use the frozen Exercises v1 schema and templates. `category` is one of
`lexical-verb`, `lexical-noun`, `lexical-adjective`, `lexical-adverb`, or
`lexical-expression`.

- `tl` is a production-ready headword: infinitive for a verb, article plus
  noun when gender/article is pedagogically useful, and the governed
  preposition or reflexive marker when it belongs to the lexeme.
- `alts` contains true alternatives for the source sense, not a thesaurus
  list. Put regional or register differences in `register`.
- `example_tl` is a new 18--30 word professional sentence that fixes the
  intended sense and supplies the morphology absent from the headword.
- `cloze` wraps the inflected occurrence in that example. It need not be
  character-identical to an infinitive headword, but must test the same
  lexeme and reduce exactly to `example_tl`.
- `trap` records a genuine five-language interference risk, government, false
  cognate, gender, or register restriction. Empty is better than invented.

## GEOPOLITICS term--definition notes (V2)

Use `category: "term-definition"`. Preserve the source's term--definition
distinction: `tl` is the target-language term, while `register` gives a terse
usage/domain label. The new contextual example demonstrates the term; do not
paste the source definition into `example_tl`. Record a corrected, concise
target-language definition in `note` during the pilot so the owner can decide
whether it belongs in one of the frozen spare fields before any bulk run.
Do **not** repurpose or rename a frozen field without that verdict.

## Cross-topic duplicates

Consult `docs/research/legacy_estate/exercises2_cross_topic_exact_duplicates.json`
during triage. Its deterministic default is to keep a domain term in the
specialist topic and drop the exact `FANCY_VOCAB` copy; the already-landed
CONNECTING note owns `To clarify`. A different choice requires an explicit
linguistic-audit reason showing a distinct sense. Before merge, run both the
source report check and the retained-notes duplicate check.
