# Codex commission F: grammar explainer scripts ("grammar radio")

> Work dir: /home/admin/projects/idiomatic (main repo tree). Write ONLY
> under `idiomatic/grammar/data/explainers/` and
> `docs/commissions/unit-specs/EXPLAINERS_DESIGN.md`. No git ops, no
> other files. Read: docs/research/error-profiles/*.md (the fossil
> sections), docs/commissions/ERROR_PROFILE_PROPOSAL.md (Phase 5),
> docs/GRAMMAR_STRATEGY.md §3b (metalinguistic feedback evidence),
> idiomatic/pipeline/audio.py + idiomatic/gemini.py (how TTS +
> stitching work today — design within these capabilities).

## Goal

The learner's structural errors repeat for years; the evidence (Heift;
strategy §3b) says explicit metalinguistic explanation beats bare
correction for exactly this. Write the actual scripts for short audio
explainers on his top fossil clusters — to be TTS'd by the existing
pipeline and delivered as a small per-language deck later.

## Tasks

1. **Twelve explainer scripts** in
   `idiomatic/grammar/data/explainers/{lang}_{slug}.md`, one each for:
   - fr: beaucoup-de (the 138× fossil), an-annee (102×),
     prep-lieux (en Berlin), ordre-adverbes (je déjà connais)
   - pt: genero-ma-agem (six-year fossil), regencia (tentar de...),
     futuro-subjuntivo (quando eu vou voltar)
   - es: muy-mucho, light-verbs (hacer/tomar/cometer), interferencia-pt
   - de: adjektivendungen (der härtester...), passiv
   Format per file: YAML frontmatter (lang, slug, title, fossil
   evidence refs with counts from the profiles, est_seconds), then the
   SCRIPT: 300-450 words, spoken register, English matrix language
   with target-language examples inline (the TTS pipeline can switch
   voices per language — write examples on their own lines prefixed
   `TL:` so the stitcher can route them to the target-language voice;
   English prose lines unprefixed). Each script: name the error (quote
   his actual recorded forms), give the rule memorably, walk 3-4
   contrasting examples, end with a 3-item self-test (question,
   pause marker `[PAUSE]`, answer).
2. **Delivery design** (`docs/commissions/unit-specs/EXPLAINERS_DESIGN.md`):
   how these become mp3s + cards with today's machinery: per-line TTS
   (Kore/EN voice for prose, ELEVEN_LANG_VOICE for TL: lines,
   silence_mp3 for [PAUSE]) stitched via concat_mp3s; one card per
   explainer in the FROZEN grammar model (front = title card,
   Extra1 = [sound:]); a new cluster "0 Écoute"-style per language OR
   a dedicated small deck — recommend one; size estimates and
   ElevenLabs cost at ~$0.05/1k chars.

## Quality bar

Linguistically impeccable examples (they'll be spoken aloud to an
advanced learner); every claimed count/quote traceable to the
profiles; no invented "he says X" — only attested forms from the
error-profile docs.
