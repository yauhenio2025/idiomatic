# Codex commission M: "Grammar walks" — long-form podcast scripts

> Work dir: /home/admin/projects/idiomatic (main repo). Write ONLY under
> `idiomatic/grammar/data/podcasts/` + one design doc
> `docs/commissions/unit-specs/PODCASTS_DESIGN.md`. No git ops. Read:
> the 12 explainer scripts in grammar/data/explainers/ (format + TTS
> routing conventions: TL:-prefixed lines, [PAUSE]), the five error
> profiles in docs/research/error-profiles/, docs/GRAMMAR_STRATEGY.md
> §3b (pedagogy evidence), the interference matrix summary in
> docs/commissions/ERROR_PROFILE_PROPOSAL.md.

## Goal

The explainers are 2-4 min drills-adjacent clips. The learner also
wants THEORY he can listen to on long walks: 12-18 minute podcast-style
episodes that teach a grammar SYSTEM as a coherent story, personalized
to his documented weaknesses, TTS-able by the existing pipeline.

## Episodes (10 scripts, 1,800-2,600 words each)

1. es: "The subjunctive as a machine" (system view: triggers, not forms
   — he avoids it; build intuition).  2. es/pt: "Why your Portuguese
   speaks Spanish" (interference mechanics, his attested pairs).
3. fr: "The French quantity system" (de/des/du as ONE system — his
   #1 error).  4. fr: "Gender is memory, not logic" (his 40-noun list
   as the spine).  5. de: "The case system as who-does-what-to-whom"
   (Russian-speaker angle — he has L1 case intuitions to TRANSFER, his
   de profile shows Russian signatures).  6. de: "Adjective endings:
   one decision tree" (the engine's logic, spoken).  7. it: "Il
   congiuntivo for people who avoid it".  8. it: "Plurals and genders
   that lie" (-ma nouns, invariants, body-part plurals).  9. pt:
   "Future subjunctive: the tense only Portuguese kept".  10. cross:
   "Four Romance languages in one head" (the science: Pan 2025,
   interleaving, why mixing helps — pop-science register).

Format per file ({lang-or-x}_{slug}.md): YAML frontmatter (series:
grammar-walks, episode N, lang, title, est_minutes, evidence refs),
then the script: conversational English, TL: example lines, [PAUSE]
before answers of the 4-6 embedded self-checks, a 60-second recap at
the end. Quote his real errors verbatim where evidence supports it.

## Design doc

PODCASTS_DESIGN.md: how these ride the explainer TTS machinery
(episode length vs the stitcher, cost estimate at ~$0.05/1k chars,
~2.5k words ≈ 15k chars ≈ $0.75/episode), delivery options (cards in a
"0" cluster vs plain mp3s the user syncs manually vs an RSS feed
served by the app — recommend one), and a season-2 topic list derived
from the error profiles.
