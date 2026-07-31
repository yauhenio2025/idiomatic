# `fr_prep_lieux`

- Cluster: `5 Prépositions`
- Bank: `fr_prep_lieux.json` — 151 entries
- Format: F1 primary; F3 for the learner's attested `en Berlin`, `en Paris`, `en Rome`, `en Barcelone`, `en Chili`, and `en Brésil`
- Verification: Tier A place→preposition lookup plus Tier B blind-fill for the generated sentence
- Recommended live size: 30 cards, with at least half of each batch drawn from high-priority cities/countries and no more than 20% region/island items

## Generator guidance draft

Choose one bank row and create a timeless French news/professional sentence with a single blank immediately before `place`. The exact answer is `correct_prep`. Use `à` with ordinary cities; retain the article in `au Caire` and `au Cap`; use `en` with feminine countries and vowel-initial countries, `au` with masculine consonant-initial countries, `aux` with plural countries, and the banked lexical form for articleless countries/islands and regions. Never infer a place's preposition from spelling when a bank row exists. Keep movement versus location neutral because these geographic prepositions normally work for both.

## Self-check

- JSON parsed; 151 unique place names and consistent fields.
- The learner-attested names are all present: Berlin, Paris, Rome, Barcelone, Chili, Brésil, Asie, Turquie, Biélorussie, Italie, Zurich, and Amérique latine.
- Article-bearing cities and lexicalized region forms were reviewed separately.
- Review question: `Kyiv`, `Taïwan`, and `Crimée` use current editorial labels. The prepositions are linguistic, but the reviewing session may want a house-style decision on geopolitical naming.
- Implementation note: the loader must skip the leading `_meta` object before sampling.

