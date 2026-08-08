# Addendum: Wave 6 BIG_TECH_PHRASES production/shadowing pilot

The 90 legacy rows are long professional sentence frames, not single-answer
translation prompts. They must not be forced into the frozen Exercises v1
production+cloze templates.

## Pilot gate P1 (blocks all Wave 6 bulk work)

Author only `pt_big_tech_phrases_pilot_b01.json`: the first 30 canonical
prompts, whose Spanish-contaminated 2023 PT backs were deliberately removed.
Empty `old_back` is therefore expected and source-hash recorded, not an error.

The owner must approve all of the following before the remaining 60 prompts
or any other language is staged/authored:

- the full-sentence PT renderings and the selected shadowing focus spans;
- the listen-and-shadow plus cue-and-produce card behavior;
- a pilot rendering in the separate model; and
- a representative listening sample made through the **local Qwen lane only**
  after its own voicing pilot is cleared.

No owner verdict is inferred from mechanical or linguistic checks. Do not
bulk-author, build, deliver, or use paid TTS while P1 is open.

## Authored pilot schema

Each kept row uses:

```json
{
  "id": "<canonical source id>",
  "en": "<source frame>",
  "category": "context-frame|concession-frame|stance-frame|transition-frame",
  "tl": "<one complete, native target-language sentence/frame>",
  "focus_tl": "<the reusable target-language discourse span inside tl>",
  "focus_en": "<short English function cue>",
  "register": "<usage/register guidance>",
  "trap": "<real interference trap or empty>",
  "note": "<audit record or empty>"
}
```

`focus_tl` must occur verbatim inside `tl`. Ellipses are allowed only when the
frame genuinely invites continuation; do not manufacture a unique "correct"
ending. Triage still covers every input row and preserves source order.

## Isolated draft model

`idiomatic/grammar/exercises2_shadowing.py` reserves a distinct draft model
ID and validates this pilot shape. It has two draft templates, `Listen &
Shadow` and `Cue & Produce`. It has **no builder, API route, delivery hook, or
TTS call**, so it cannot alter the frozen Exercises v1 fields/templates or
ship accidentally. P1 freezes or rejects this skeleton before runtime wiring.
