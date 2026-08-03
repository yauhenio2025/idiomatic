# Commission: Batch the remaining grammar-walk episodes into podcast cards

> For a Claude session in ~/projects/idiomatic (fable to architect/review,
> codex for bulk restructuring if useful). The FORMAT IS APPROVED — episode
> 3 (fr, beaucoup de) shipped through two user review rounds and is the
> exemplar. This commission converts the other seven single-language season
> episodes to the same card format. Episodes 2 and 10 (lang: x) stay parked
> until per-line language markers exist.
>
> Read first, in this order:
> 1. this file
> 2. `idiomatic/grammar/data/podcast_cards/fr_quantity-system.md` — the
>    approved exemplar card source (markup + all format rules embodied)
> 3. `idiomatic/grammar/data/podcast_cards/svg/` — the ten approved diagrams
>    (visual system to copy)
> 4. `idiomatic/grammar/podcast_cards.py` — parser/builder (markup contract
>    is enforced here; read the validation)
> 5. `docs/commissions/PODCAST_CARDS_COMMISSION.md` — original architecture
> 6. the season sources in `idiomatic/grammar/data/podcasts/` — the approved
>    scripts you are restructuring
> 7. CLAUDE.md ops rules (push/deploy/build discipline)

## Episodes to convert (ship order)

| order | episode | source | lang | suggested short_title |
|---|---|---|---|---|
| 1 (CHECKPOINT) | 4 | fr_gender-is-memory.md | fr | Le genre |
| 2 | 1 | es_subjunctive-machine.md | es | El subjuntivo |
| 3 | 5 | de_case-system.md | de | Die Fälle |
| 4 | 6 | de_adjective-endings.md | de | Adjektivendungen |
| 5 | 7 | it_congiuntivo.md | it | Il congiuntivo |
| 6 | 8 | it_deceptive-plurals-and-genders.md | it | Plurali bugiardi |
| 7 | 9 | pt_future-subjunctive.md | pt | Futuro do subjuntivo |

**HARD CHECKPOINT: ship episode 4 (fr) alone first and STOP for user
approval** — same language as the approved pilot, so quality is directly
comparable. Then batch the rest without stopping unless the user redirects.
Deck names derive automatically (`Idiomatic Grammar {LANG}::0 <listening
cluster>::{NN} {short_title}`); clusters for all five langs already exist in
`explainers.EXPLAINER_UNITS`.

## Format rules (all learned in user review — violations WILL be bounced)

1. **~5 cards × 2 sides per episode** ([CARD]/[SIDE]), every side
   self-contained: opens with a spoken anchor restating the rule context.
2. **Fronts end with a spoken flip cue; backs end with a spoken "move on to
   the next card" cue** — except the last back, which closes the episode
   ("That was the last card of the episode." + [MUSIC:outro]). [MUSIC:intro]
   only on card 1 front.
3. **No multi-word target-language phrase may EVER sit in unprefixed (EN)
   narration** — the English voice mangles it. One–two-word citation forms
   (the particle/word being taught) are fine. Anything longer goes on
   TL:/TL-: lines. This applies to every language in the batch.
4. **Fixed practice-item pattern**: EN prompt (+ SHOW line with the numbered
   prompt) → [THINK:6000-8000] → TL-: full answer → TL-: key-chunk echo →
   optional pure-English tip → [PAUSE]. Practice answers are TL-:
   (spoken, never displayed).
5. **Keep TL lines verbatim from the season scripts wherever possible** —
   the TTS clip cache is shared with the season build (same slug + stage
   dir), so verbatim lines cost nothing. New TTS ≈ anchors/cues/echoes only.
6. **Visuals are authored SVG sidecars** (`SVG:` line per side; `IMG:`
   generation is allowed only for a rare mood/scene side, expect ~zero).
   One diagram per side, `svg/{lang}_{slug}_c{N}{f|b}.svg`.
7. Loudness is automatic (per-clip −16 LUFS leveling lives in the renderer
   since acc7832). Do not add any normalization anywhere.

## SVG system (copy it exactly)

- viewBox width 840, height to fit; class-based palette ONLY — s-ink,
  s-muted, s-teal, s-coral, s-sun, s-dead, s-tile, s-stroke-teal,
  s-stroke-coral, s-stroke-line (colors + night mode live in the model CSS,
  never in the files). Simple primitives (circles/rects/lines/text);
  `text-decoration="line-through"` for dead forms; white text only on
  filled teal/coral shapes.
- The diagram must CARRY THE LESSON (sound labels, struck-out dead forms,
  arrows that encode the rule) — not decorate it. Practice-side diagrams
  show the rule being drilled, never the answers.
- **MANDATORY before shipping: visual verification.** Build a preview page
  embedding all the episode's SVGs (include `<meta charset="utf-8">` — its
  absence produced a mojibake false alarm once), serve via
  `python3 -m http.server` on localhost, screenshot with the playwright
  browser, and LOOK at it. Fix, re-verify, then ship.

## Per-episode workflow

1. Restructure the season script into the card source (respect rules 1–5).
   Bulk restructuring MAY go to codex with this file as the spec; the
   supervising session reviews every line — pedagogy edits are not
   mechanical.
2. Author the SVGs; preview-verify (above).
3. `pytest tests/ -q` must stay green (the parser enforces most of the
   contract; add the new sources to any per-source tests only if asked).
4. Check `/admin/grammar-status` is idle (never push during a live build) →
   commit + push. Verify the deploy actually settled REV-SPECIFICALLY:
   `/admin/podcast-cards-list` shows the new episode (data files ship in
   the image) — do not trust fixed waits or generic 200s; the SPA fallback
   and the old instance both lie.
5. `POST /admin/podcast-cards-build?lang={lang}&episode={n}` (admin token in
   `~/.config/idiomatic-admin.env`, header X-Admin-Token). Poll
   `/admin/grammar-status`. The per-lang apkg repackages ALL of that lang's
   episodes — expected.
6. Verify the result stats (sides, svg_sides, durations, apkg id, deck
   name) and the apkgs row, then move to the next episode.

## Costs & cadence

Visuals $0. TTS ≈ $0.10–0.20/episode (new connective lines only; TL content
is cache-shared). Builds ~20–90 s each. The one human gate is the episode-4
checkpoint; after that, ship all six remaining in sequence.
