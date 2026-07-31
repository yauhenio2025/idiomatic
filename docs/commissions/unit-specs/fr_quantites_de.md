# `fr_quantites_de`

- Cluster: `7 Articles & quantités`
- Bank: `fr_quantites_de.json` — 72 entries
- Format: F1 primary; F3 for the attested `beaucoup des`, `beaucoup de l'`, `des autres`, and `la plupart d'eux` fossils
- Verification: Tier A curated-bank answer lookup, followed by Tier B blind-fill agreement for generated F1 sentences
- Recommended live size: 36 cards, initially weighted 40% `beaucoup`, 25% other quantity words, 15% negation/`d'autres`, 10% `la plupart`/`bien des`, 10% formal adjective+noun

## Generator guidance draft

Generate one French blank whose answer is the bank entry's exact `correct` string. Preserve the entry's semantic class: an indefinite amount after `beaucoup/trop/assez/peu/plus/moins` takes `de/d'`; negated indefinite/partitive objects take `pas de/d'`; additional indefinite items take `d'autres`; noun complements after `la plupart` take `des`, while stressed pronouns take `d'entre`; `bien des` retains `des`. Do not generate a subset reading such as `beaucoup des rapports déjà cités`, where `des` is grammatical. Use news, publishing, politics, and technology contexts. F3 fronts may use `trap`; generated F1 items must contain exactly one blank and one defensible answer.

For the last eight entries, explicitly preserve the formal/careful-written-language cue. Do not turn them into a universal claim that `des + adjective + plural noun` is always ungrammatical.

## Self-check

- JSON parsed; all 72 entries have the same five fields and one blank.
- Quantity frames were reread to exclude definite-subset readings.
- One malformed `avoir besoin` frame was caught and rewritten during the pass.
- Review question: the `des → de` items represent the careful written norm, but `des` is also attested and accepted in other registers. Keep them only if the unit is explicitly targeting formal production.

