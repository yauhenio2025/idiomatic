# F2 structured-input interpretation cards

## Purpose and learning contract

F2 complements the productive F1 cloze. The learner reads an overtly inflected
form and interprets the distinction encoded by that form: viewpoint aspect,
person, or semantic roles marked by case. There is no blank and no production
prompt. Each front asks one referential question with two or, where genuinely
needed, three labeled choices.

The decisive information must be the visible form. Lexical time expressions,
world knowledge, plausibility, word order, or a unit title must not independently
settle the answer. In particular, an aspect item cannot contain cues such as
*ayer*, *tous les jours*, *mentre*, or *de repente*. A German item may use
scrambled order, but only the case morphology may determine the roles.

The authored seed banks use news, institutional, and professional contexts.
Questions and options are in the target language; `why` is concise English
feedback, matching the existing strategy for error-specific explanations.

## Canonical bank schema

Each bank is a JSON array. Element zero is a provenance object; every later
element is an item:

```json
[
  {
    "_meta": {
      "source_evidence": "...",
      "format": "F2 ...",
      "built": "2026-08-01",
      "feeds_units": ["..."],
      "routes": ["..."],
      "validation_notes": "..."
    }
  },
  {
    "sentence": "La comisión revisaba el protocolo.",
    "question": "¿La acción se presenta como cerrada o como habitual/en curso?",
    "options": [
      {"label": "A", "text": "Cerrada: se presenta como un hecho completo."},
      {"label": "B", "text": "Habitual/en curso: no se marca el límite final."}
    ],
    "answer": "B",
    "why": "'Revisaba' is imperfect: it presents the review without a completed boundary.",
    "contrast_form": "La comisión revisó el protocolo."
  }
]
```

The item key set is exact: `sentence`, `question`, `options`, `answer`, `why`,
and `contrast_form`. Options are an ordered array of objects with exactly the
keys `label` and `text`; labels are consecutive `A`, `B`, and optionally `C`.
`answer` is one label, not repeated answer prose. Strings are NFC Unicode.
There is no `___`: F2 tests interpretation of an exposed form.

The seed banks use reciprocal minimal pairs. If item X names Y as its
`contrast_form`, Y is another item whose `contrast_form` is X, whose question
and option meanings are the same, and whose answer denotes the opposite
interpretation. Option order is alternated across pairs so a learner cannot use
an A/B frequency heuristic. The `_meta.routes` entries refer to one-based item
positions after the header and are part of the reviewed bank revision.

## `fmt='f2'` in the frozen model

F2 is compiled to an ordinary verified `grammar_items` row with `fmt='f2'`.
It keeps the existing model ID, one template, GUID formula, and all 14 fields in
their frozen order. No option is a clickable control and no second card template
is introduced.

| Frozen field | F2 value |
|---|---|
| `ItemId` | Stable integer `grammar_items.id`, as for other drills. |
| `Lang` | `es`, `pt`, `fr`, `it`, or `de`. |
| `Topic` | Existing receiving unit selected by the bank route. This preserves ordinary tags, telemetry, and subdeck interleaving. |
| `TenseLabel` | A neutral localized instruction: `Interpreta la forma`, `Interprete a forma`, `Interprétez la forme`, `Interpreta la forma`, or `Kasusrollen erkennen`. Never show the receiving unit's tense name; that would reveal the answer. |
| `Symbol` | Neutral `?`, not a tense/aspect symbol. |
| `Sentence` | Escaped `sentence`, then `question`, then one line per labeled option. The compiler alone adds safe `<br>` separators; bank text is never treated as HTML. |
| `Answer` | The correct label plus its exact text, for example `B — Habitual/en curso: ...`. |
| `SentenceFull` | The original unmodified `sentence`. |
| `GlossEn` | `Minimal contrast: ` followed by the escaped `contrast_form`. Despite the legacy field name, this is back-only contrast feedback, not a front cue. |
| `Why` | Escaped `why`. It must name the decisive surface form and the feature it marks. |
| `Extra1` | Empty in the text-first seed release. Reading the sentence aloud is not a substitute for inspecting written morphology. |
| `Extra2`–`Extra4` | Empty; the reserved fields remain reserved. |

The database row stores the six source properties under `meta.f2` so the front
can be recompiled without parsing display HTML. `sentence` in the database is
the fully compiled front string, which also keeps the existing unique
`(lang, sentence)` constraint meaningful. `answer` stores the rendered labeled
answer, `gloss_en` stores the minimal-contrast line, and `why_en` stores `why`.
`infinitive`, `mood`, `tense`, and `person` remain null: those columns describe
production targets and would leak or misstate a contrastive interpretation
item. The source bank path plus one-based item position and a bank-content hash
belong in `meta.f2` for stable provenance.

## Think, reveal, and self-grade

The front presents all choices at once. The learner reads the form, commits
mentally to a label, and reveals the back. The existing Anki answer buttons are
the grading mechanism:

- **Again** if the chosen label or interpretation was wrong.
- **Hard** if the label was correct only after hesitation or if the learner
  could not identify the decisive form.
- **Good/Easy** only when both the label and form-to-meaning link were readily
  available.

This remains a one-decision, think-then-reveal card suitable for AnkiDroid on
the elliptical. JavaScript option buttons would add interaction without adding
learning evidence, would complicate AnkiDroid behavior, and would still not
replace the scheduler grade.

## Verification

The reviewed bank rows are attested authored items. They need no LLM linguistic
verification. Intake still performs cheap deterministic hygiene: parse JSON;
discard exactly one leading `_meta` object; enforce the exact schemas and NFC;
require two or three unique consecutive option labels; require `answer` to name
one option; reject blanks/HTML/control characters; reject duplicate fronts;
check reciprocal contrasts; check opposite meanings and balanced labels; and
confirm each reviewed route names an existing unit.

Generated variants are not automatically bank-attested. They require this
counterfactual verification pipeline before `status='verified'`:

1. Start from one reviewed reciprocal pair and change only the professional
   lexical frame, preserving both members' syntax, arguments, question, and
   option meanings.
2. Morphologically analyze the two decisive forms. The existing Romance
   morphology tables, or German `decline_np()` plus the reviewed case/government
   bank, must attest both surfaces and show exactly the intended feature change.
3. Run a deterministic minimality check after replacing the two target spans
   with one sentinel. The remaining pair must be byte-identical after NFC and
   whitespace normalization. Agreement changes inside the same target span are
   allowed; unrelated tense, adverb, subject, or word-order changes are not.
4. Run three independent blind interpretation votes on the full first member;
   all must select its gold meaning. Repeat on the counterfactual member; all
   must select the opposite meaning.
5. Run cue ablation: mask the decisive form while leaving the lexical frame and
   options. All valid votes must report that the choice is underdetermined. A
   solver that can recover the gold answer from an adverb or plausible event
   script exposes a non-form cue, so the variant is rejected.

Any failed stage rejects the whole pair; never publish only one member. Batch
checks also cap reused lemmas/frames and balance visible forms and answer labels.

## Unit routing and interleaving

F2 does not create a separate deck or cluster. Each item is tagged with and
placed beside the production cards for the same confusion set, so reviews mix
interpretation and production in the existing numbered subdeck. This implements
the delayed-learning advantage of interleaving reported by Pan et al. (2019)
rather than blocking all interpretation cards together.

| Bank | Existing receiving units | Reviewed route |
|---|---|---|
| `f2_es_pret_impf.json` | `es_preterito`, `es_imperfecto` (`1 Tiempos`) | In each reciprocal pair, the preterite member routes to `es_preterito` and the imperfect member to `es_imperfecto`. |
| `f2_pt_person_aspect.json` | `pt_preterito_perfeito`, `pt_preterito_imperfeito` (`1 Tempos`); `pt_futuro_subjuntivo` (`3 Subjuntivo`) | Person pairs route to perfeito; aspect members route by their visible tense; the final future-subjunctive/present counterfactual pairs both route to `pt_futuro_subjuntivo` because the decision is future-event selection. These rows directly cover the strongest selection finding in the Portuguese profile without creating a sixth bank. |
| `f2_fr_pc_imparfait.json` | `fr_passe_compose`, `fr_imparfait` (`1 Temps`) | Compound-past members route to `fr_passe_compose`; imperfect members route to `fr_imparfait`. |
| `f2_it_pp_imperfetto.json` | `it_passato_prossimo`, `it_imperfetto`, `it_passato_remoto` (`1 Tempi`) | Passato-prossimo and imperfetto members route by visible form; the five completed narrative members in the final section route to `it_passato_remoto`. |
| `f2_de_case_roles.json` | `de_adj_endings` (`3 Adjektive`), `de_dativ_verben` (`5 Kasus`) | Nominative/accusative and relative-pronoun rows route to `de_adj_endings`; dative-object and ditransitive rows route to `de_dativ_verben`. |

Routing a contrast member under one visible-form unit does not block it from its
counterpart: the existing cluster deck and ordinary Anki scheduling produce the
mix, while `meta.f2.contrast_form` preserves the explicit confusion edge for
telemetry and later F2 confusion matrices.
