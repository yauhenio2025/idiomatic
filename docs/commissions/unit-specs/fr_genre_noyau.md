# `fr_genre_noyau`

- Cluster: `6 Genre & accord`
- Bank: `fr_genre_noyau.json` — 102 entries
- Format: F1 primary; F3 for personal wrong-gender anchors
- Verification: Tier A noun-gender bank plus deterministic article/adjective agreement
- Recommended live size: 36 cards: all 19 explicitly named personal nouns should appear before pattern expansion; thereafter sample 60% personal/profile nouns and 40% same-pattern traps

## Generator guidance draft

Choose a noun from the bank and create one short French sentence whose blank is a determiner or a visibly gendered adjective. The sentence and noun sense must force the banked gender. Favor `ce/cette`, `un/une`, possessives, and adjective agreement over bare `le/la` recognition. Keep `mode` in the “method/mode” sense, `livre` in the “book” sense, and `politique` as the feminine noun meaning policy. Include occasional contrast batches for masculine `-age` nouns versus feminine exceptions, masculine `-eau` nouns versus `eau`, and masculine Greek `problème/système/thème/programme` versus feminine `crème`.

## Self-check

- JSON parsed; 102 unique nouns and consistent fields.
- Every gender and example was reread by suffix family rather than trusting the suffix rule.
- The profile's §2.2 explicitly lists 19 top offenders, despite describing an underlying list of about forty. Those 19 are first. Positions 20–40 are other nouns attested in the same profile, not falsely labeled as direct wrong-gender counts.
- Sense-sensitive nouns are pinned by `trap_reason` and `example`.
- Open question: if the reviewing session has the raw 297 gender rows available, replace profile-derived positions 20–40 with the exact remaining personal noun list.

