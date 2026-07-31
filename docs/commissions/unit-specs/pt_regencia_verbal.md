# `pt_regencia_verbal`

- Cluster: `6 Regência`
- Bank: `pt_regencia_verbal.json` — 73 entries
- Format: F1 primary; F3 for `tentar de`, `conseguir a`, `decidir de`, `vou a`, missing `que`, and country-article anchors
- Verification: Tier A curated regime lookup plus Tier B blind-fill for sentence uniqueness
- Recommended live size: 30 cards, with the first four attested bare-infinitive regimes represented in every initial generation batch

## Generator guidance draft

Use Brazilian Portuguese in neutral professional/news register. Pick exactly one bank entry and blank only the target `prep`; `Ø` means the sentence must show a visible blank whose answer is “no preposition” in the item model, or the implementation should map it to a dedicated zero marker. Preserve the exact sense in `pattern`: `trabalhar em` is a field/location but `trabalhar para` is an employer; `pensar em` is consideration; `tratar de` is topic; `lutar por` is a cause. Keep article contractions (`no`, `na`, `ao`, `às`) as full answers. Country and time expressions are intentionally included because they are attested in the same regime/preposition cluster.

## Self-check

- JSON parsed; 73 entries and an exact legacy regime schema.
- `example_es` deliberately contains Portuguese to preserve compatibility with `es_verb_prep.json`; a future generalized schema should rename it to `example_target`.
- Every example was reread for Brazilian usage.
- Review/implementation questions: decide how F1 represents `Ø`; and decide whether the deck should teach careful-standard `assistir a` and `chegar a` categorically or mention the widespread colloquial BR transitive/`em` variants on the back. The bank targets careful professional prose.

