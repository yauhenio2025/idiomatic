# F2 interpretation cards

## Decision

F2 is a referential, think-then-reveal format. The learner reads a complete
target-language sentence, answers a target-language meaning question by
mentally choosing one labeled option, and then reveals the correct option and
a short English explanation. The visible inflection is the only cue that may
decide the answer. F2 complements F1 production; it does not replace it and
does not live in a separate deck.

The existing Anki model remains frozen: model ID, one card template, field
count, field names, field order, and GUID formula do not change. `fmt='f2'` is
an ordinary `grammar_items` presentation mode compiled into those fields.

## Authored-bank contract

Each bank is one UTF-8 JSON array. Element zero is a non-item metadata object,
following the repository's existing bank convention:

```json
[
  {"_meta": {
    "bank": "f2_es_pret_impf",
    "language": "es",
    "format": "F2 interpretation; two-option minimal pairs",
    "built": "2026-08-01",
    "item_count": 50,
    "feeds_units": ["es_preterito", "es_imperfecto"],
    "source_evidence": "...",
    "coverage": {"content_items": 50},
    "validation_notes": "..."
  }},
  {
    "sentence": "El comité evaluó la propuesta.",
    "question": "¿Cómo presenta la forma la evaluación?",
    "options": [
      "A. Como un hecho delimitado, visto como un todo.",
      "B. Como una situación habitual o en curso, sin enfocar su límite."
    ],
    "answer": "A. Como un hecho delimitado, visto como un todo.",
    "why": "Evaluó is preterite: the perfective form presents the event as a bounded whole.",
    "contrast_form": "El comité evaluaba la propuesta."
  }
]
```

Every content row has exactly the six keys shown above.

The canonical required metadata keys are `bank`, `language`, `format`,
`built`, `item_count`, `feeds_units`, `source_evidence`, `coverage`, and
`validation_notes`; provenance, variety/register, and language-policy details
may be added. `bank + ".json"` must equal the filename. A loader accepts only
`language` and `format`, not aliases such as `lang` or `fmt`, and rejects any
conflicting duplicate. The filename remains authoritative for `source_bank`.

- `sentence` and `contrast_form` are complete, grammatical sentences with no
  cloze marker or raw HTML. The latter is a true minimal pair: only the
  morphology carrying the tested contrast changes (or, in German, the
  reciprocal case markers needed to exchange roles).
- `question` and `options` are in the target language. `why` is concise English
  metalinguistic feedback, as elsewhere in the grammar system.
- `options` contains two or three distinct strings, each beginning with a
  stable `A.`, `B.`, or `C.` label. `answer` is byte-for-byte one member of
  `options`. The seed banks deliberately use two options so each card tests one
  binary meaning contrast without adding a second distractor dimension.
- Option order is authored and stable, not shuffled at review time. Correct
  positions are balanced 25/25 between A and B across each bank and
  cross-balanced within each source-tense, person-decision, or case-routing
  stratum; odd strata may differ by one. German positions are additionally
  cross-balanced within route × construction. A deterministic constraint
  solver with hash-based choice order assigns labels independently of row
  parity and source form, then freezes them.
- Content rows are stored in a frozen, deterministic constrained permutation,
  not in tense, case, construction, or A/B blocks. Every applicable stream
  rejects three serial cues: a run longer than three identical symbols, any
  six-position period-2 window such as `ABABAB`, and any nine-position
  period-3 window such as `ABAABAABA`. “Applicable” means a stream with at
  least two possible symbols, not a category filtered to itself.
- The checked answer-label streams are the full bank and each Romance
  source-form category. Portuguese additionally checks labels within the
  person/aspect decisions and the two receiving-unit routes. German
  additionally checks labels within each case route, construction, route ×
  construction cell, and first-tested-participant role.
- The checked category streams are each bank's full source category.
  Portuguese also checks the top-level person/aspect decision sequence and the
  semantic categories (`1sg`, `3sg`, perfect, imperfect) within each decision
  and receiving route. German also checks its full case-route and construction
  sequences and the construction sequence within each route. Balance without
  these local-window checks is insufficient: `ABAB...` is itself a non-form
  cue.
- All text is NFC-normalized. Sentences are unique within a language after
  Unicode normalization and whitespace folding.

The minimal pair is an interpretation oracle, not a second automatically
emitted card. It appears on the back, proves that the same lexical frame can
support both readings, and supplies the expected opposite answer for
verification. The seed banks contain 50 distinct frames rather than repeating
25 pairs in both directions.

## Meaning, not a claim about the outside world

The Romance aspect options describe **grammatical viewpoint**. A perfective
form presents an event as a bounded whole; it does not by itself prove that
every real-world goal was achieved. An imperfect form presents a situation as
ongoing, habitual, descriptive, or backgrounded without focusing its boundary;
it does not assert that the situation never ended. Explanations must use those
claims rather than the unsafe shortcuts “the task definitely succeeded” or
“the event was never completed.” The Spanish bank's learner-facing
“¿Terminada o habitual?” genre is therefore resolved by options that spell out
the bounded-versus-unbounded distinction.

The form-only rule is literal:

- Romance aspect rows contain no dates, bounded durations, iteration phrases,
  frequency adverbs, `mientras`/`pendant que`/`mentre` clauses, sequencers, or
  lexical result clauses that independently reveal the answer.
- Portuguese person rows omit subject pronouns, names, titles, vocatives, and
  agreeing predicates. The bank prioritizes `fiz`/`fez` and adds the attested,
  non-syncretic pairs `tive`/`teve`, `escrevi`/`escreveu`, `criei`/`criou`,
  `comecei`/`começou`, `entendi`/`entendeu`, and `estive`/`esteve`. A 3sg form
  is compatible in Brazilian Portuguese with `ele`, `ela`, `você`, `a gente`,
  or a singular noun phrase. The option wording tests grammatical person and
  never pretends that a 3sg form uniquely identifies one discourse referent;
  syncretic pairs such as `disse`/`disse` are ineligible.
- Italian `passato remoto` rows test recognition of a bounded narrative form,
  not the folk rule that it must denote a more chronologically remote event.
  Regional and register preferences do not change the form's perfective
  viewpoint.
- German rows use overt, non-syncretic case morphology and role-reversible
  human or institutional participants. Animacy, plausibility, finite-verb
  number, canonical word order, and punctuation must not decide
  the roles. Nominative marks the finite verb's subject, accusative its direct
  object, and dative the recipient or governed participant where tested.

Masking the focal morphology in `sentence` and `contrast_form` must leave the
same lexical and syntactic frame. Showing the contrast must flip exactly one
answer dimension.

## Frozen 14-field mapping

The source row remains structured in `grammar_items.meta`; it is not flattened
irreversibly into prompt prose. A converter stores the raw source sentence in
`grammar_items.sentence`, the exact labeled option in `answer`, the English
explanation in `why_en`, and at least `schema_version`, `source_bank`,
`source_index`, `source_unit`, `question`, `options`, and `contrast_form` in
`meta`.

At APKG build time, an F2-specific presenter maps that row as follows. It may
special-case field contents, but it must not alter the model or add a template.

| Frozen field | F2 value |
|---|---|
| `ItemId` | Stable integer `grammar_items.id` |
| `Lang` | `es`, `pt`, `fr`, `it`, or `de` |
| `Topic` | Existing receiving unit selected below |
| `TenseLabel` | Neutral localized instruction: `Interpreta la forma`, `Interprete a forma`, `Interprète la forme`, `Interpreta la forma`, or `Kasusformen lesen` |
| `Symbol` | `?`; never the source unit's tense/case symbol |
| `Sentence` | Escaped `sentence`, then escaped `question`, then the labeled options on separate lines |
| `Answer` | Exact `answer`, including its label |
| `SentenceFull` | Escaped source sentence followed by `contrast_form`, clearly introduced as the meaning-flipping contrast |
| `GlossEn` | Empty in v1; the task is target-language to target-language |
| `Why` | Escaped `why` |
| `Extra1` | Empty in text-only v1; remains the existing back-audio slot if F2 audio is later approved |
| `Extra2`–`Extra4` | Empty |

The presenter escapes every bank string first and adds only fixed application
markup (`div` and line breaks). It must not trust bank text as HTML. This
produces a front of the following shape inside the current `{{Sentence}}`
container:

```text
El comité evaluó la propuesta.

¿Cómo presenta la forma la evaluación?
A. Como un hecho delimitado, visto como un todo.
B. Como una situación habitual o en curso, sin enfocar su límite.
```

On reveal, the existing back first shows the correct labeled option, then the
source/contrast pair, then `Why`. The normal topic label and symbol must not be
used for F2: “Imperfecto” or `←≈` on the front would leak the answer even though
the note remains assigned to that topic for scheduling and telemetry.

## Self-grading

There are no clickable choices, stored JavaScript state, or typed answers. The
learner commits mentally to A or B before revealing, then uses the ordinary
Anki rating buttons:

- **Again** — chose the other option, guessed, or interpreted the sentence
  from a non-form cue.
- **Hard** — chose correctly but hesitated or could not identify the decisive
  morphology before reading `Why`.
- **Good** — chose correctly and can name the decisive form.
- **Easy** — immediate, confident, form-based interpretation; use sparingly.

The Anki revlog records only the rating, not the option mentally selected.
`Again` is therefore a generic F2 interpretation failure: it can feed accuracy
and direction-specific error rates for the gold form, but it is not a literal
record of the distractor chosen because a correctly guessed answer is also
graded `Again`. Neither binary nor future three-option cards may claim an
option-level confusion matrix without an explicit response-capture feature.
`Hard` remains correct-but-not-automatic rather than a recorded wrong choice.

## Unit and interleaving map

F2 notes use the existing receiving topics and therefore the existing cluster
subdecks. The source form determines the topic; the contrast form does not
create another note.

The converter derives `source_unit` with a deterministic sentence/contrast
diff plus the vendored Romance morphology tables or German case engine. It
stores that result in `grammar_items.meta`, requires it to occur in the bank's
`_meta.feeds_units`, and uses it as `Topic`. It must never infer routing from
`why`, option prose, or answer position.

| Bank | Existing receiving units | Existing cluster | Assignment rule |
|---|---|---|---|
| `f2_es_pret_impf.json` | `es_preterito`, `es_imperfecto` | `1 Tiempos` | Source preterite → first unit; source imperfect → second |
| `f2_pt_person_aspect.json` | `pt_preterito_perfeito`, `pt_preterito_imperfeito` | `1 Tempos` | All person-reading rows and source perfect forms → perfeito; source imperfect forms → imperfeito |
| `f2_fr_pc_imparfait.json` | `fr_passe_compose`, `fr_imparfait` | `1 Temps` | Source passé composé → first unit; source imparfait → second |
| `f2_it_pp_imperfetto.json` | `it_passato_prossimo`, `it_imperfetto`, `it_passato_remoto` | `1 Tempi` | Assign by the displayed source form; the bank contains 10 recognition rows for passato remoto |
| `f2_de_case_roles.json` | `de_adj_endings`, `de_dativ_verben` | `3 Adjektive`, `5 Kasus` | All 32 nominative–accusative rows, including accusative-relative rows → adjective/case morphology unit; all 18 nominative–dative rows, including dative-relative and seven fixed-theme ditransitive rows → dative-verbs unit |

The Portuguese future-subjunctive selection signal in the learner profile is
a strong candidate for a later F2 bank feeding `pt_futuro_subjuntivo`, but it
is outside this commissioned bank's explicit person/perfect-versus-imperfect
scope.

No `F2` subdeck or blocked F2-only unit is created. The authored permutation
removes serial cues inside F2, but it does not itself interleave exercise
genres. New-card selection must spread these rows among F1/F3 rows from the
same cluster rather than append all F2 rows as a contiguous insertion block.
Same-cluster placement alone does not guarantee that result: wiring must either
round-robin the already de-patterned F2 sequence among production rows or
configure and test a random new-card gather order. Review scheduling then mixes
interpretation with production in the confusable cluster, following the
interleaving rationale in the grammar strategy and Pan et al. (2019).

## Verification and variant generation

The five seed banks are authored, reviewed evidence. Their rows may be inserted
directly with `fmt='f2'`, `status='verified'`, and an authored batch identifier;
they need no LLM solver vote. “No verification” does not mean “no validation”:
the loader still enforces JSON shape, exact keys, option membership, normalized
uniqueness, balanced labels, item count, and a non-identical contrast.

Generated variants do **not** inherit the bank's attestation. A future variant
pipeline should keep them out of delivery until all of these gates pass:

1. **Frame-preserving generation.** Start from one reviewed row and preserve
   its question, semantic option pair, valency, participant animacy, and
   contrast dimension. Vary only reviewed lexical slots; generate both the
   displayed sentence and its opposite contrast together.
2. **Deterministic morphology.** Verify both focal forms against the vendored
   conjugation tables or German NP-inflection engine. German relative clauses
   additionally require a relative-pronoun check: `der`/`den`/`dem` must agree
   with the antecedent's gender and number while encoding the intended clause
   role and case. Confirm the intended tense/person/case, and map the displayed
   form to the receiving topic without parsing the prose explanation.
3. **Minimal-pair diff.** After tokenization and NFC normalization, permit
   differences only in the focal verb phrase or reciprocal German case spans.
   Mask those spans and require the remaining sentence skeletons, questions,
   and option semantics to be identical. Static checks reject the lexical cue
   classes listed above.
4. **Two-sided blind judging.** At least three independent solver votes,
   including one from a different model family/provider, must unanimously pick
   the expected option for the displayed form and the opposite option for the
   contrast form, naming the same morphology. Given the form-masked frame, all
   three must instead return `underdetermined`; any keyed option selected from
   lexical context rejects the variant.
5. **Failure policy.** Any disagreement, morphology miss, cue leak, or
   non-minimal diff rejects the variant; it is never silently repaired and
   published. Human review is required before resubmitting a rejected frame.

This paired test is stricter than ordinary blind fill: it checks the mapping in
both directions and tests whether removing the form removes the answer.

## Acceptance checks for a seed bank

- The file parses as JSON and has 51 array elements: one `_meta` object plus
  exactly 50 content rows.
- Every row has exactly the six commissioned keys; every seed row has exactly
  two unique labeled string options and an answer identical to one option.
- Correct labels are balanced 25 A / 25 B and cross-balanced within every
  source-tense, person-decision, or case-routing stratum (difference at most one
  for an odd stratum); German labels are also cross-balanced within every
  route × construction cell. The frozen row order is not blocked by source
  form, case, construction, or answer label. Apply the three serial-cue checks
  (run, period 2, and period 3) to every nonconstant answer-label and category
  stream enumerated in the authored-bank contract above.
- No duplicate sentence, contrast, or unordered sentence/contrast pair exists
  after normalization.
- The source and contrast are grammatical, differ only in licensed focal
  morphology, and imply opposite answers to the same question.
- No lexical, temporal, overt-subject, word-order, non-target agreement, or
  world-knowledge cue independently settles the answer.
- Every `why` names the visible form and states the interpretation it encodes;
  it does not overclaim real-world completion or non-completion.
- Register and variety match the bank metadata, with Brazilian Portuguese and
  standard contemporary usage in the other languages.
