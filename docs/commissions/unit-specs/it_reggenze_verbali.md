# `it_reggenze_verbali`

- Cluster: `6 Reggenze`
- Bank: `it_reggenze_verbali.json` — 70 entries
- Format: F1 primary; F3 for the five attested 2019 regime errors
- Verification: Tier A curated regime lookup plus Tier B blind-fill
- Recommended live size: 30 cards, with `cercare di`, `permettere a qualcuno di`, `partecipare a`, and `guadagnare come` forced into the first batch

## Generator guidance draft

Use standard Italian and one exact sense from `pattern`. Blank only `prep`; preserve any other argument marker already shown in the sentence (`permettere a qualcuno ___`, `chiedere a qualcuno ___`). Contrast high-interference pairs deliberately: Italian `cercare di` versus French `chercher à`; `riuscire a` versus Portuguese `conseguir Ø`; `dipendere da`; `consistere in`; `basarsi/contare/concentrarsi su`; `fidarsi di` versus `affidarsi a`. If a verb has multiple regimes, add lexical cues that force the banked sense, such as intention for `pensare di` and faith/confidence for `credere in`.

## Self-check

- JSON parsed; 70 entries, above the 60 minimum, with the legacy regime schema.
- `example_es` contains Italian by deliberate compatibility convention.
- A placeholder/incorrect draft for `evitare` was caught; the final row is correctly `evitare di`.
- Ambiguous strict-cloze candidates `servire a/per`, `interessarsi a/di`, and the two-slot `congratularsi con…per` were removed.
- Open question: `pensare di` versus `pensare a` remains sense-dependent. The generator must make intended action, not mere contemplation, explicit and the Tier B pass must reject ambiguous sentences.
- `consistere in` is restricted to an activity/infinitive frame (`consiste nel verificare`). Italian also documents `consistere di` with constituent noun lists, so `di` must not be used as a universally wrong distractor.
