# Wave-7 Phase-2 unit-bank index

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
| `de_dativ_verben` | 5 Kasus | 81 | F1 + F3 | regime + NP inflection |
| **Total** |  | **938** |  |  |

## Loader contract

All banks are JSON arrays. Element zero is `{"_meta": {...}}`; generation code must discard that element before sampling. This preserves the existing array-bank convention while satisfying the commission's provenance requirement. The Portuguese and Italian regime banks retain the legacy `es_verb_prep.json` key `example_es`; its value is the target-language example, not Spanish.

## Open questions for review

1. The French profile names 19 top wrong-gender nouns, not the promised literal forty. The bank preserves those 19 first and expands from nouns elsewhere in the profile. Replace positions 20–40 if the raw 297-row extract yields the exact personal remainder.
2. Formal French ordinarily prefers `de` before prenominal adjective + plural noun, but `des` is not categorically ungrammatical in every register. The eight frames explicitly cue careful/formal French.
3. `pt_regencia_verbal` targets careful professional BR for `assistir a` and `chegar a`; colloquial Brazilian alternatives are widespread and should be acknowledged on the card back if retained.
4. Italian body/collective plurals have meaning-dependent masculine alternatives. The bank pins the requested body/collective forms; generated sentences must preserve those senses.
5. The recommended Italian cluster strings are `5 Genere e plurali` and `6 Reggenze`, moving reggenze one number later than the thin-profile draft so the two new clusters sort independently. Cluster strings are final once cards ship, so confirm before wiring.
6. `de_dativ_verben` needs deterministic full-NP inflection, including dative plural and weak nouns; the current article-only German verifier is insufficient.
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
   (dative plural -n, weak nouns) is bundled into the de_adj_endings
   build, which needs the same declension matrix anyway — one engine,
   two units. Until then dative-verb items use article+noun frames the
   existing de_art checker can already validate where possible.
