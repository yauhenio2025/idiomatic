# Expression Hub pilot — what you will see (owner gate 1)

> **v2 (2026-08-09, post-verdict): `hub_pilot_v2.apkg`.** The owner
> approved v1 and ratified the model freeze, with one template
> amendment: the hub back's example rail is now a responsive TILE GRID
> (~3 per row on desktop webviews, 2 on tablets/phones, 1 on narrow
> phones) — illustration on top, target sentence, muted English line
> beneath; text-only tiles share the same tile chrome. v2 differs from
> v1 ONLY in that rail layout (same selection, same GUIDs, same model
> IDs) — importing v2 updates the existing pilot deck's cards in place.
> Everything below otherwise still applies; read "rail" as "grid".

> Built 2026-08-09 on branch `hub-build` (F2 of
> HUB_BUILD_EXECUTION_COMMISSION.md). The deck is DISPOSABLE by design:
> everything lives under **"ZZ Hub Pilot (disposable)"**, uses a pilot-only
> GUID namespace (can never collide with or be updated by a production
> release), and is safe to import into the normal profile and delete
> afterwards. Nothing was generated: every sentence, clip, and image
> already existed server-side or in the QA-passed campaign store.

## Contents

- **30 expressions** — 10 ES (the ones with QA-passed illustrations),
  5 each DE / FR / IT / PT.
- **210 notes / 240 cards**, two subdecks:
  - `ZZ Hub Pilot (disposable)::Hub` — 30 hub notes, **2 cards each**
    (both directions, model `1820180001`).
  - `ZZ Hub Pilot (disposable)::Fluency` — 180 example notes, 1 card each
    (model `1820180002`).
- 461 media files: 411 staged audio clips (reused, no synthesis) and 50
  byte-verified QA-passed illustrations.

## Card 1 — Hub card (accepted design, verdict 4: vertical comic rail)

Front: the target-language expression, nothing else (e.g. **a primera
hora**).

Back, top to bottom:
1. expression + English gloss;
2. usage note (see DECISIONS-NEEDED 4 — pilot shows the full existing
   explanation, production compresses to one line);
3. "≈ synonym" block and/or "⚠ warning" block when present (blue/red
   tinted, target-language text from the structured stylebook);
4. the **vertical rail**: for each of the 6 examples — target sentence,
   muted English line, then that sentence's full-width illustration
   (ES cards; other languages show the text-only rail until their images
   are QA-judged);
5. source footer: video title(s) + full URL text, plus the **context
   clip** — the actual sentence as spoken in the source video (owner
   amendment 2). It autoplays on reveal. `es 439 a primera hora` shows
   the multi-source case (4 videos listed).

## Card 2 — EN→TL expression-production card (owner amendment 1)

Front: language badge (ES/DE/FR/IT/PT) + "SAY THE EXPRESSION" + the
English gloss only (e.g. *first thing in the morning*). No usage line on
the front — leak-conservative (DECISIONS-NEEDED 2).

Back: the expression, its atomic pronunciation clip, the gloss echo, the
same source-video context clip, and the source footer.

## Card 3 — Fluency example card (design §5.1, model `1820180002`)

Front: English sentence + English audio; deliberately NO image and no
expression hint (either would leak the answer).
Back: target sentence + target audio, the example's own illustration
(when QA-passed), a small "Expression: … (gloss)" reminder, source footer.

These 180 pilot fluency cards are NEW disposable cards. In production
this model is what the 20k existing Pool-v1 cards convert INTO (in place,
schedules retained — phase 5); the pilot does not preview schedule
adoption, only the card face.

## Coverage facts (exact, from pilot_selection.json)

| slice | value |
|---|---|
| context clips | 22/30 expressions (8 sources have no usable clip server-side: 1 null, 8 silence placeholders < 2.5 KB were refused) |
| expression pronunciation clips | 30/30 |
| example audio | 180/180 both EN and TL |
| illustrations | ES only: 6/6 on four expressions (439, 447, 870, 956), 5/6 on two (442, 874), 4/6 on four (443, 446, 872, 877) = 50 images; every image byte-verified against the QA judge's recorded SHA1 |
| synonym block | 23/30; warning block 30/30 (see DECISIONS-NEEDED 5) |

## How to inspect

1. Copy `docs/research/hub_manifest/hub_pilot.apkg` to the laptop and
   import via File → Import (do NOT route through the delivery add-on;
   it was never registered in `apkgs`).
2. Browse deck `ZZ Hub Pilot (disposable)` — suggested looks:
   - `es 439 a primera hora`: full rail (6 images), 4 sources, context clip;
   - `es 443 dar la curva`: partial rail (4/6 images — what a coverage gap
     looks like; production gates on completeness, design §10);
   - any DE/PT card: text-only rail + context clip;
   - `fr coup de cœur`: no context clip (placeholder was refused) — the
     back simply omits the player.
   - In the Fluency subdeck, filter `tag:expression::439` to see the
     example cards that belong to one hub.
3. When done: delete the deck (Anki removes its notes/cards). Nothing
   else references it.

Rebuild offline any time: `.venv/bin/python tools/build_hub_pilot.py`
(reads the committed selection + staged media; `--refresh` re-selects
from the server and refetches media, needs `IDIOMATIC_ADMIN_TOKEN`).

## DECISIONS-NEEDED (conservative choices made to keep building — all
reversible until the models freeze at pilot approval)

1. **Spare-field count.** Design doc froze Extra1/Extra2; the build
   commission requires ≥3 spares. Implemented **3 spares per model**
   (commission wins as the later, binding order). Confirm at freeze.
2. **EN→TL front shows the gloss only** (+ language badge). The usage
   line sometimes paraphrases the expression's literal wording, so it
   stays off the front. Alternative: include it for gloss disambiguation.
3. **ExpressionAudio on the EN→TL back.** Not in the amendment text;
   added as a dedicated field because every production deck in the house
   pairs an answer with its pronunciation (grammar, exercises2, pool).
   Drop the field content (not the field) if unwanted.
4. **UsageLineEN placeholder.** The reviewed one-line compression job
   (migration §6) is not built yet; the pilot shows the full existing
   `explanation_en` in that slot so the back's information design is
   judgeable. Production output will be ≤ 24 words.
5. **Synonym/warning blocks are mechanically mapped** for the pilot
   (`structured.synonyms_neutral`; `false_friend` falling back to
   `pitfall`) — hence a ⚠ block on every card. Production populates
   these only through the reviewed compression job ("only a consequential
   synonym; only a concrete false friend").
6. **Amendment fields are dedicated fields** (`ContextAudio`,
   `ExpressionAudio`), not consumed spares — the amendments bind at
   freeze, so they deserve first-class slots; spares stay free.
7. **Unjudged images were NOT used.** 891 locally-rendered but not yet
   QA-judged illustrations exist; the pilot ships only the 86 verified
   passes (50 land on the selected ES expressions). DE/FR/IT/PT hubs go
   text-only until the judge reaches their chunks.
8. **Rail order = server `ord` order** (position backfill preserves it).
9. **F1 schema stays expansion-only**: the design's `ON DELETE RESTRICT`
   ownership, `(lang, normalized)` handover, `ord ≤ 6` drop, and the
   `expression_sources` rename are contraction-phase work for the
   migration executor (F3+), not boot migration — the live purge path is
   regression-tested against the staged schema.
