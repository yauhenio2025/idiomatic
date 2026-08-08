# Addendum: Wave 3 TENSES batches

This extends `EXERCISES2_BATCH_COMMISSION.md`. Wave 3 has already received
its owner verdict: keep the raw legacy exercise order, including literary
tenses. It is approved for all five languages without another format pilot.

## What Wave 3 is (and is not)

The source is the **300 legacy TENSES sentence prompts**, in their committed
order, from `it_rebuild/input/tenses_01..03.json`. They teach tense
sequencing in context: past anteriority, ongoing action up to the present,
modal constructions, counterfactual sequences, and future-perfect
sequences. The repaired Italian output and the four `refs` values are
references; English and the canonical `it_tenses_NNN` ID remain authoritative.

This is **not an expansion of Tenses Rescue**. Tenses Rescue is the separate
per-person conjugation lane under `::3 Tenses`, built from selected
verb×tense lapse cells. Wave 3 stays under `::4 Exercises`, uses the frozen
Exercises v1 fields/templates, keeps the 300 sentence-sequencing prompts,
and does not add Rescue cards, paradigms, or IDs.

The staged inputs and their source hashes are recorded in
`batches/manifests/wave3.json`. Do not reorder, renumber, deduplicate, or
replace those source rows during authoring.

## Note contract

The base schema applies with these TENSES-specific rules:

1. `category` is one of `past-anteriority`, `ongoing-to-present`,
   `modal-construction`, `counterfactual-sequence`, `future-perfect`, or
   `literary-sequence`.
2. `tl` is the full, idiomatic translation of the legacy English sentence.
   Preserve its temporal relationship; do not flatten a pluperfect, perfect
   progressive, future perfect, counterfactual, or marked literary form.
3. `example_tl` is a **new sentence**, not a paraphrase or topical reskin of
   `tl`. It practices the same sequencing architecture in the learner's
   professional register and is 18--30 words.
4. `cloze` wraps every governed verb group needed to reconstruct that
   architecture, each in its own `{{c1::...}}`. Include auxiliaries, attached
   clitics, separable material, and participles that belong to the answer.
5. `trap` names a real cross-language sequencing hazard. It must not become a
   generic tense definition.

## How `_tenses_old` priors are used

Read the target language profile and `tenses_priors.json` before authoring.
The priors **order and adapt the new examples only**:

- among verbs compatible with the source architecture, prefer higher-lapse
  verb×tense cells first, then rotate through persons because the old cards
  cannot identify which person failed;
- use the profile's fork notes (for example *liegen/legen*) to create a
  meaningful new example where compatible;
- reverify every inflected form independently. Attested old paradigm strings
  are evidence, not copy-ready answers;
- do not use practical-frequency filtering to erase literary forms. The
  owner explicitly chose the raw order, including French literary sequences
  and Italian passato remoto. Mark the register accurately.

The priors never replace an English prompt, change canonical order, or turn
this wave into additional whole-paradigm Rescue material.

## Triage and gates

Keep the corpus unless an item is genuinely broken or an exact duplicate.
Do not drop an item merely because its tense is literary or marked. Before a
topic merge, run the batch gate, the merge-vs-triage verifier, and the
cross-topic exact-duplicate check from `tools/x2_wave_pipeline.py`.

There is no remaining owner format gate for Wave 3. Linguistic audit and the
normal server build/release steps still remain; this commission does not run
them.
