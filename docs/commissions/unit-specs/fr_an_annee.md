# `fr_an_annee`

- Cluster: `7 Articles & quantités`
- Bank: `fr_an_annee.json` — 60 entries
- Format: F1 primary; F3 for `cet an`, `chaque an`, and `dans les ans 90`
- Verification: Tier A exact frame-family lookup, with Tier B blind-fill on newly generated contexts
- Recommended live size: 24 cards, six from each opposition: `an/année`, `jour/journée`, `matin/matinée`, `soir/soirée`

## Generator guidance draft

Generate a single French blank targeting one banked form. Force the contrast through a fixed expression or a clearly marked construal: age and neutral numerical measurement use `an(s)`; calendar/evaluated/experienced periods use `année(s)`; counted calendar points use `jour(s)` while an event or full duration uses `journée`; time-of-day labels use `matin/soir`, while a scheduled event or elapsed block uses `matinée/soirée`. Avoid free contexts such as `deux ans/deux années` where both are grammatical with a nuance difference.

## Self-check

- JSON parsed; exactly 60 entries and one blank per frame.
- The bank has 24 `an/année` frames and 12 each for day, morning, and evening.
- Frames were restricted to fixed expressions, age/counts, named calendar cycles, greetings, or explicit whole-period/event readings.
- No unresolved lexical item remains. The only implementation caution is to keep the banked construal when paraphrasing.

