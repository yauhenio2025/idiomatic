# Idiom Rescue Pilot №1 (2026-08-05) — awaiting user approval

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
