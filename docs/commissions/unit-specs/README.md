# Wave-7 Phase-2 unit-bank index

The separate [F4 interference specification](F4_INTERFERENCE.md) records the
private-bank ingestion/card contract and the final cluster strings for the four
receiving-language interference units; no F4 pair content is stored here.

Built 2026-07-31 for `CODEX_B_UNIT_BANKS.md`. Counts exclude each JSON file's leading `_meta` header object.

| Unit | Cluster | Entries | Primary format | Verification |
|---|---|---:|---|---|
| `fr_quantites_de` | 7 Articles & quantités | 72 | F1 + F3 | curated lookup + blind |
| `fr_prep_lieux` | 5 Prépositions | 151 | F1 + F3 | place lookup + blind |
| `fr_genre_noyau` | 6 Genre & accord | 102 | F1 + F3 | deterministic |
| `fr_an_annee` | 7 Articles & quantités | 60 | F1 + F3 | lookup + blind |
| `pt_gender_core` | 5 Gênero & Artigos | 120 | F1 + F3 | deterministic |
| `pt_regencia_verbal` | 6 Regência | 73 | F1 + F3 | regime lookup + blind |
| `it_genere_plurali` | 5 Genere e plurali | 159 | F1 + F5 | deterministic |
| `it_reggenze_verbali` | 6 Reggenze | 70 | F1 + F3 | regime lookup + blind |
| `es_muy_mucho` | 9 Grado y cantidad | 50 | F1 + F3 | closed inventory + blind |
| `de_dativ_verben` | 5 Kasus | 81 | F1 + F3 | regime + Tier B blind (v1) |
| **Total** |  | **938** |  |  |

## Loader contract

All banks are JSON arrays. Element zero is `{"_meta": {...}}`; generation code must discard that element before sampling. This preserves the existing array-bank convention while satisfying the commission's provenance requirement. The Portuguese and Italian regime banks retain the legacy `es_verb_prep.json` key `example_es`; its value is the target-language example, not Spanish.

## Open questions for review

1. The French profile names 19 top wrong-gender nouns, not the promised literal forty. The bank preserves those 19 first and expands from nouns elsewhere in the profile. Replace positions 20–40 if the raw 297-row extract yields the exact personal remainder.
2. Formal French ordinarily prefers `de` before prenominal adjective + plural noun, but `des` is not categorically ungrammatical in every register. The eight frames explicitly cue careful/formal French.
3. `pt_regencia_verbal` targets careful professional BR for `assistir a` and `chegar a`; colloquial Brazilian alternatives are widespread and should be acknowledged on the card back if retained.
4. Italian body/collective plurals have meaning-dependent masculine alternatives. The bank pins the requested body/collective forms; generated sentences must preserve those senses.
5. The recommended Italian cluster strings are `5 Genere e plurali` and `6 Reggenze`, moving reggenze one number later than the thin-profile draft so the two new clusters sort independently. Cluster strings are final once cards ship, so confirm before wiring.
6. The article-only German verifier is insufficient for adjective-ending work or
   deterministic full-NP inflection. This is resolved by the shared engine that
   ships with `de_adj_endings`; the already-shipped `de_dativ_verben` v1 is not
   automatically rewired to use it (see the decisions below).
7. Zero-preposition Portuguese regimes need an explicit item-model convention (`Ø` answer versus a different cloze representation) before generation.

## Self-check summary

- All ten files parse as JSON.
- Entry schemas are consistent within each bank, with no exact duplicate objects.
- Every required minimum is met; total bank size is 938 entries.
- Single-blank banks were checked for exactly one `___`.
- Frequency ordering, attested anchors, register, and variety were reviewed bank by bank.
- Known uncertainty and legitimate variation are recorded above and in the individual specs rather than hidden in the data.

External spot-checks used for the highest-risk rules:

- [Académie française: geographical names and articles](https://www.academie-francaise.fr/questions-de-langue)
- [Académie française: `de`/`des` before a prenominal plural adjective](https://www.academie-francaise.fr/patricia-m-paris)
- [Treccani: Italian plurals, including gender-changing and double plurals](https://www.treccani.it/enciclopedia/plurale_%28Enciclopedia-dell%27Italiano%29/)
- [Duden: the dative object](https://www.duden.de/sprachwissen/fuer-lernende/dativobjekt)
- [Ciberdúvidas: variation in Brazilian `assistir` government](https://ciberduvidas.iscte-iul.pt/consultorio/perguntas/regencia-do-verbo-assistir/19132)

## Decisions (2026-07-31, supervising session — resolves open questions 5 & 6)

1. **Italian cluster strings CONFIRMED FINAL**: `5 Genere e plurali` and
   `6 Reggenze` (as proposed above — reggenze at 6 so the two clusters
   sort independently). These strings are now frozen the moment cards
   ship, same rule as every other cluster.
2. **de_dativ_verben verification**: ship v1 with Tier B blind-fill
   (K=3) + the bank's `case` field as a static check; do NOT block on a
   full-NP inflection engine. The deterministic NP-inflection verifier
   (dative plural -n, weak nouns) is bundled into the `de_adj_endings`
   build, which needs the same declension matrix anyway — one engine,
   reusable by multiple units. Dative-verb items continue to use the
   shipped bank/static-case + blind-verification path unless a later
   commission explicitly rewires them.

## German declension and passive decision (2026-08-01)

- `de_adj_endings` now ships as an active unit in `3 Adjektive`, backed by the
  shared deterministic full-NP inflection engine. The engine covers article
  class, strong/mixed/weak adjective endings, dative plural, weak nouns, and
  genitive noun inflection. Generated plural cards are restricted to a curated
  nominative-plural bank because the vendored gender table has no plural
  paradigms.
- `de_passiv` now ships as a separate active unit in `4 Verben`, covering the
  werden-passive in the present, Präteritum, Perfekt, and modal + passive
  infinitive constructions. Deterministic form checks are used where the
  dictionaries cover an item; otherwise the item uses the established Tier B
  blind-fill fallback with `K=3`.
- `de_verb_core` is superseded and remains outside the curriculum. Its attested
  passive scope is served by `de_passiv`; Konjunktiv II remains future work.
  Boot seeding explicitly removes the obsolete planned database row on upgrade.
- This commission makes the shared NP engine available but does not change the
  verification contract of the already-shipped `de_dativ_verben` unit.

## IMPLEMENTED (2026-07-31)

All ten commissioned topics are wired into generation. Every bank loader filters
the leading `_meta` object before lookup, inventory construction, or sampling.
The shipped verification behavior is:

- `fr_quantites_de`, `fr_an_annee`, and `es_muy_mucho` use a closed blind
  inventory.
- `fr_prep_lieux`, `pt_regencia_verbal`, and `it_reggenze_verbali` use bank
  lookup plus Tier B blind-fill with `K=3`.
- `fr_genre_noyau` deterministically targets the controlled `un`/`une` choice.
- `pt_gender_core` deterministically targets controlled `o`/`a` or
  `um`/`uma` choices and checks exact bank-frame answers. Noun rows expose the
  bank noun immediately after the article blank; full-phrase rows may use a
  novel context while retaining the bank answer verbatim, then receive a
  three-vote grammatical/semantic context-fit check.
- `it_genere_plurali` deterministically targets a banked article+noun phrase
  or plural.
- `de_dativ_verben` statically checks the banked `case`, citation phrase, and
  exact banked declension, then uses Tier B blind-fill with `K=3` valid,
  unanimous votes. No general full-NP inflection engine is part of this unit.
- `Ø` is a literal answer marker, not an instruction to render an empty answer.
- Capitalization tolerance is relaxed only when the blank is sentence-initial;
  capitalization remains exact everywhere else. Accepted sentence-initial bank
  answers are capitalized before persistence and rendering.

### Deviations from the drafts

- Gender article exercises were narrowed to controlled article choices
  (`un`/`une` in French; `o`/`a` or `um`/`uma` in Portuguese). This keeps the
  deterministic target unambiguous instead of requiring a broader noun-phrase
  generator. Portuguese non-noun construction rows copy the complete bank
  answer, may place it in a new context, and use Tier B to reject a bank phrase
  that does not fit that context; Italian article/plural cards expose the
  citation noun, so bank metadata remains tied to the visible exercise.
- The three closed units verify membership in their closed inventories rather
  than requiring novel-context row identity. A blind prompt need not reproduce
  one uniquely identifiable source row, so inventory membership is the stable
  correctness criterion.
- `de_dativ_verben` does not use a full-NP inflection engine, per the supervising
<<<<<<< HEAD
  decision above. It reuses each selected row's citation phrase and exact
  declined answer, then obtains `K=3` valid blind votes; the shared declension
  engine remains deferred to the `de_adj_endings` work.
=======
   decision above. It ships with the banked-case check, `K=3` blind verification,
   and exact canonical-frame answers where applicable. The shared declension
   engine now ships with `de_adj_endings`, but this commission does not
   automatically rewire `de_dativ_verben` to use it.
>>>>>>> codex/declension
- Regime and German verb metadata cannot be morphologically matched to every
  possible conjugated surface form without another language-specific engine.
  The prompt pins one exact bank row, static verification checks that row's
  answer/case, and the blind pass checks the resulting sentence; semantic
  metadata-to-verb binding remains prompt-enforced for novel contexts.
- Required leading anchors are always included in sampled prompt rows. The
  recommended whole-batch ratios remain explicit prompt constraints rather
  than static rejection criteria, because rejecting an otherwise correct card
  cannot repair the distribution of the rest of a generated batch.

## Live reject audit and verifier tuning (2026-08-01)

Evidence came from the first live batches in
`/home/admin/projects/idiomatic-data/tuning/rejects_*.json`. Each rejected item
was classified as **(a)** genuinely bad, **(b)** good but rejected by an
over-strict verifier, or **(c)** good but serialized against an unstated prompt
rule. Counts below refer to those staged batches, not a new generation run.

### `pt_gender_core`: 14/24 rejected before, projected 2/24 after

Twelve cards used the exact banked answer in a grammatical new context. The old
verifier required normalized equality with a synthetic canonical cloze, even
though the exercise answer itself remained deterministically pinned. Two cards
really did omit the noun after an article-only blank and remain rejected.

| ID | Class | Bank target | Audit result |
|---:|:---:|---|---|
| 647 | a | `emblema` / `um` | Filling the blank yields `virou um da...`; the noun is absent. |
| 646 | b | `uns links quebrados` | Exact answer is grammatical in the novel article context. |
| 645 | b | `pelas redes` | Exact contraction and agreement in a novel campaign sentence. |
| 644 | b | `duzentas pessoas entrevistadas` | Correct feminine hundred; the old canonical substitution was impossible because the bank example splits the phrase with `foram`. |
| 643 | b | `no site` | Correct contraction in a novel availability sentence. |
| 642 | b | `duas telas adicionais` | Correct feminine numeral phrase. |
| 641 | b | `duas semanas completas` | Correct feminine numeral phrase. |
| 640 | b | `numa mensagem` | Correct contraction and following feminine agreement. |
| 639 | b | `pelos sites` | Correct masculine-plural contraction and agreement. |
| 638 | b | `na ordem judicial` | Correct feminine contraction. |
| 637 | a | `garagem` / `A` | Filling the blank yields `A do novo centro...`; the noun is absent. |
| 636 | b | `oitocentos milhões de usuários` | Correct agreement with masculine `milhões`. |
| 635 | b | `neste idioma` | Correct contraction in a novel publication sentence. |
| 634 | b | `duas leis complementares` | Correct feminine numeral phrase. |

After tuning, non-noun rows require `target="bank"` and the exact
`gender_or_correct` answer but no longer require the canonical sentence. The
answer-leak and single-blank checks remain, and each novel full-phrase context
must receive three valid affirmative context-fit votes. This catches an exact
bank phrase placed into an ungrammatical sentence without demanding canonical
wording. Noun rows still require the blank immediately before the exact visible
noun; guidance now states that rule and explicitly permits new contexts only
for complete bank phrases. Dump-derived tests pair every newly accepted sentence
with a wrong-gender answer, exercise the context validator against a malformed
placement, and retain both missing-noun rejections. Expected disposition is
therefore 22 accepted and 2 rejected, versus 10 accepted and 14 rejected before.

### `fr_quantites_de`: 9/24 rejected before, projected 6/24 after regeneration

The suspected inventory/elision mismatch was not present: the closed inventory
already contains the required `de`/`d'` variants. Seven items instead wrote a
space after the blank even though their answer ended in an apostrophe. Literal
replacement would produce invalid forms such as `d' énergie`, so that verifier
guard remains strict. The generator prompt had never stated this serialization
rule; it does now. Deeper review found only three of the seven otherwise ready
to ship.

| ID | Class | Audit result |
|---:|:---:|---|
| 822 | a | `dispose d'ingénieurs` competes with `dispose assez d'ingénieurs`; all three blind votes chose bare `d'`. |
| 821 | a | `pas de`, `plus de`, and `d'autres` remain defensible; the blind votes split. |
| 820 | c | `trop ... pour pouvoir` forces `trop d'`; only the unstated apostrophe-boundary format failed. |
| 819 | c | The sufficiency cue plus exported surplus supports `assez d'`; only boundary spacing failed. |
| 818 | a | Both `n'a pas d'autre choix` and `n'a plus d'autre choix` fit without a distinguishing cue. |
| 817 | a | The generated sentence dropped the bank's mandatory literal formal-register cue and also spaced the apostrophe. |
| 816 | c | The newer chip plus comparison cues `moins d'`; only boundary spacing failed. |
| 815 | a | `beaucoup`, `assez`, `plus`, and `trop` all produce defensible readings. |
| 814 | a | The opening modifier is ill attached, the comparison direction is not forced, and the mutable `aujourd'hui` claim is unsuitable. |

The verifier still rejects all seven unchanged spaced forms. With `___` joined
to the following vowel-initial word, IDs 820, 819, and 816 pass static checks
and proceed to Tier B; the other six rejects remain rejected on ambiguity or
quality grounds. Guidance now demands overt scalar/directional cues,
distinguishes `pas` from `plus`, preserves literal formal-register cues, and
states `___énergie` rather than `___ énergie`. Tests retain the exact boundary
rejection, accept the three corrected serializations, and prove that bare `d'`
is not treated as equivalent to `assez d'` or another longer answer.

### `de_dativ_verben`: 5/12 rejected before, projected 0/12 after

All five cards were linguistically correct and already supplied the complete
dative NP requested by the generator prompt. Across their 15 blind votes, eight
were exact full phrases, four were article-only interpretations of the visible
parenthetical hint, and three were solver errors. The generic blind prompt did
not explain that the parenthetical citation is removed on completion, and every
error was incorrectly treated as linguistic disagreement.

| ID | Class | Bank verb | Audit result |
|---:|:---:|---|---|
| 691 | b | `zustimmen` | Correct `dem Kompromiss`; two solvers returned only `dem` and one errored. |
| 692 | b | `drohen` | Correct `dem Unternehmen`; two exact votes and one article-only vote. |
| 693 | b | `widerstehen` | Correct `dem politischen Druck`; two exact votes and one error. |
| 694 | b | `gelingen` | Correct `den beiden Delegationen`; two exact votes and one error. |
| 695 | b | `fehlen` | Correct sentence-initial `dem Bericht`; capitalization tolerance worked, but one vote returned only `Dem`. |

The dedicated blind prompt now says that the parenthetical text is a nominative
citation hint removed from the completed sentence, tells the solver to infer
the case from the sentence itself, and demands the entire declined phrase,
never only its determiner. It does not reveal the banked target case. Invalid,
empty, or failed solver responses are retried once per vote slot; the verifier
still fails closed unless all three slots return valid, unanimous full answers.
The static pass requires the chosen bank row's exact citation phrase and exact
declined answer even in a novel context. The citation is stored through the
existing hint field so card backs and audio remove it after inserting the
answer, and a sentence-initial answer is capitalized before storage. Tests replay
all five sentences, reject paired wrong cases, partial answers, and a metadata-
matched dative phrase placed under an accusative verb; exercise transient and
persistent disagreement paths; assert no majority voting; and cover downstream
hint removal and capitalization.
