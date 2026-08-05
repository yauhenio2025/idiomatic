# Idiom Rescue Pilot №1 (2026-08-05) — round 2 under review

## ROUND-1 VERDICT (user, 2026-08-05 afternoon)

**Comics > SVG diagrams > videos (dropped — "not helpful at all").**
Sentences and cloze exercises confirmed "very good". The winning
moments made the *expression itself* visible (the cone of shadow),
not just a scene from one sentence — the user's framing: the failure
is an un-mastered expression, not a forgotten sentence. MiniMax video
is out of the pipeline.

## ROUND 2 — word-centered image formats (exemplars generated, in review)

Five formats that encode the expression rather than illustrate a
sentence (exemplars on the same artifact page, all Nano Banana except
where noted):

1. **Inside/outside contrast** — the idiom's spatial logic as one
   image, teaching the opposite for free (estar por dentro / por fora).
2. **Polysemy map** — one word, three doors (está tirado: en el suelo /
   baratísimo / facilísimo); targets door-confusion failures.
3. **Morphology anatomy** — the word as an exploded machine (se
   desbloquee: steel se·des + concrete BLOQUE cracking + golden
   pending -e over a closed gate). Needed a strict letter-order
   prompt on retry — word must read cleanly left-to-right or the
   format is void.
4. **Iconic poster** — the metaphor's source domain as one flat emblem
   (giocare in casa: house-shaped stadium). Replaces what video tried.
5. **Idiom glyphs** — a permanent minimal logo per expression, stamped
   on every future card of that idiom: the constant identity across
   changing content.

## Repeat-failure escalation ladder (proposed)

Principle: a repeat failure means the current encoding didn't bind —
switch the encoding axis, never regenerate a harder same-axis version.
The glyph stays constant. Diagnose the failure type from revlog grain
(e2t fail = production, t2e = recognition, cloze-grammar = form,
one-sense clustering = polysemy) and pick the follow-up format by
type:

- **Strike 1** (enters struggle list, ≥3 Agains/14d): comic + anchor +
  3 personalized sentences + cloze/production. Glyph minted.
- **Strike 2** (still failing 7d after v1): switch axis by diagnosis —
  production→morphology anatomy; recognition→contrast/poster;
  polysemy→polysemy map. All sentences replaced (never let the card
  be memorized instead of the idiom).
- **Strike 3** (still failing 7d after v2): keyword mnemonic on the
  user's other languages + metacognitive "here is the fork" card +
  seed the idiom into the next exercises2/grammar wave.
- **Release**: parent idiom's Again-rate below threshold 21 days →
  rescue cards auto-retire; glyph archived for relapse.


The first personalization experiment built on the Anki study-data POC
(ANKI_STATS_POC.md): take the idioms the user actually failed **this
morning** and produce a support deck ("Idiomatic Rescue::<Language>")
whose cards attack the same expressions through different memory
channels. Pilot-first: nothing ships until the user approves the
review artifact.

## Selection

Fresh AnkiWeb pull (11:24), morning session = 287 reviews. Top 3
idioms per language by (Agains today, Agains 14d), sentence-level
pool_expr cards only:

| lang | idiom | fails (today/14d) | hero format |
|------|-------|-------------------|-------------|
| es | se desbloquee | 6/6 | SVG diagram (subjunctive gate + morphology) |
| es | está tirado | 3/7 | MiniMax video (coat on the floor scene) |
| es | dar por terminada | 3/3 | comic (café breakup, bubble = the idiom) |
| pt | estava por dentro | 2/9 | MiniMax video (glass-room exclusion scene) |
| pt | não tem esse negócio de | 2/3 | comic (grandma bans phones at dinner) |
| pt | afinal de contas | 1/5 | SVG diagram (ledger tally → trump card) |
| it | coni d'ombra | 3/4 | comic (noir flashlight over LEGGE) |
| it | andare insieme | 3/3 | SVG diagram (meshed gears TEORIA/PRATICA) |
| it | giocare in casa | 3/3 | MiniMax video (home-stadium entrance) |

## Format experiment

Every expression: **anchor** line (etymology/keyword hook), 3
personalized sentences (register: the user's world — tech criticism,
media, geopolitics) with ElevenLabs audio (the SAME per-lang voices as
the main decks: George/Matilda/Antoni), 2 exercises (cloze +
EN→TL production with a trap note). Hero formats, one of each per
language, so formats can be compared within each language:

- **video**: MiniMax-H3, 6 s, 768P, text-free visual-metaphor scene
  tied to the exact failed sentence (~3 CNY each; mandarin-videos'
  spend ledger + daily cap respected via its minimax_client).
- **comic**: Nano Banana (gemini-3.1-flash-image) 3-panel strip, the
  idiom as the only speech-bubble text — all three rendered the
  es/pt/it bubble text perfectly on the first attempt.
- **SVG diagram**: hand-authored (same night-slate style as podcast
  cards) — structural/morphological encoding.

## Pedagogy notes

Dual coding (image+word), elaborative encoding (anchors), retrieval
practice with feedback (exercises), personalization effect (sentences
in the user's own intellectual register), one vivid scene per idiom
rather than many weak associations. The within-language format triad
lets the user's next review data say which channel actually reduces
Agains — the success metric for pilot №2.

## Assets & status

Working dir: session scratchpad `rescue/` (content.json = full source
of truth incl. video/comic prompts; assets/, audio/). Review page
published as a private Artifact for approval. NOT yet in the repo:
after approval the content JSON + assets move into
`idiomatic/grammar/data/rescue/` (or R2 for videos) and a build
endpoint ships the apkg as a new `apkgs.kind='rescue'` per language.

## Open decisions (user)

1. Which hero format(s) earn a place in the standing pipeline?
2. Deck cadence: rebuild weekly from fresh struggle data? Auto or
   on-demand?
3. Card layout: hero on front (recognition) vs back (feedback)?
