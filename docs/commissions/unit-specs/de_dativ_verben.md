# `de_dativ_verben`

- Cluster: `5 Kasus`
- Bank: `de_dativ_verben.json` — 81 entries
- Format: F1 primary; F3 for `jemanden einen Gefallen → jemandem` and `den Programm → dem Programm`
- Verification: Tier A verb-government lookup plus deterministic German NP inflection
- Recommended live size: 30 cards, about 70% pure dative-object verbs and 30% high-frequency ditransitives

## Generator guidance draft

Choose one verb and create a German sentence with one dative noun-phrase blank. Include the noun phrase's nominative citation form as a hint, as in the examples, but require the whole correctly inflected phrase as the answer. Vary masculine, feminine, neuter, and plural; include adjective endings, dative plural `-n`, and selected weak masculine nouns only when the verifier can inflect them. Keep the verb sense that selects a dative object. For ditransitives, make the dative recipient and accusative thing explicit. Never count a noun as a dative object merely because a preposition governs dative.

## Self-check

- JSON parsed; 81 entries, above the 50 minimum, and every frame has one blank.
- Pure dative verbs were separated conceptually from the final common ditransitives.
- Dative plural endings and weak nouns (`Zeuge`, `Asteroid`, `Journalist`) were checked in their example answers.
- A malformed `fehlen` draft was caught and corrected.
- Implementation question: the present `de_art` verifier only checks articles. This unit needs full NP inflection or tightly controlled answer templates before generation; do not downgrade it to blind-only verification.

