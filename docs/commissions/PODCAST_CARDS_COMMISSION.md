# Commission: "Grammar walks" as multi-card Anki lessons (audio + visuals + HTML)

> For a FRESH session (fable for architecture/review, codex for bulk).
> Read first: this file, docs/commissions/unit-specs/PODCASTS_DESIGN.md,
> idiomatic/grammar/explainers.py + podcasts.py (segment renderer:
> TL:/[PAUSE:ms]/[THINK:ms]/[CHIME]/[MUSIC:x] all work),
> idiomatic/grammar/data/podcasts/fr_quantity-system.md (the approved-
> format v2 pilot script), CLAUDE.md, docs/GRAMMAR_STRATEGY.md §3b.
> HARD RULE inherited from the user: PILOT FIRST — build ONE episode as
> cards, get approval, only then batch.

## The user's concept (2026-08-03, gym use case)

At the gym the user has an iPad running Anki (the SYLLABUS profile,
evgeny@the-syllabus.com — where all grammar decks live). Instead of one
long MP3 per episode, decompose each podcast episode into ~10 CARDS
(~5 notes × 2 sides): the narration plays per side, and at the end of
each side the voice says "now flip the card" — flipping reveals the
next chunk with its own audio. Each side also carries TEXT (the
examples rendered as rich HTML, big fonts) and a GENERATED IMAGE
(Gemini's newest image model — "Nano Banana Pro"-class — via the
existing GEMINI_API_KEY) that visualizes the rule/scene. Dual coding:
hearing + reading + imagery. Sides must be SELF-CONTAINED (studyable
in any order despite thematic sequence).

## Architecture guidance (decided, don't relitigate)

1. **New note model, NOT the frozen grammar model.** The 14-field
   `Idiomatic Grammar Drill v1` stays untouched forever. Create
   `Idiomatic Podcast Lesson v1` with its OWN new model_id and a field
   set designed for this format (suggested: LessonId, Episode, Seq,
   Lang, FrontHTML, BackHTML, FrontAudio, BackAudio, FrontImage,
   BackImage, + 4 spares). Same rules as ever once shipped: fields
   frozen, GUIDs = pure function of DB id, spares reserved.
2. **Delivery**: new `apkgs.kind='podcast_lesson'` per lang riding the
   existing one-row-per-(lang,kind) upsert + add-on path (zero add-on
   changes). Deck name `Idiomatic Grammar {LANG}::0 Écoute::{episode}`
   or a sibling top deck — implementer proposes, user confirms in the
   pilot review.
3. **Source format**: extend the podcast script markup with card
   boundaries, e.g. `[CARD]` separators and per-side `[SIDE]` breaks +
   an `IMG: <prompt>` line per side describing the image to generate.
   The segment renderer already handles everything else. The "now flip
   the card" line is authored TEXT (English narration), not magic.
4. **Images**: Gemini image generation through the server key. Cache
   by content hash next to the audio (staged_audio/grammar/podcasts/
   images/). Style consistency: one strong style prompt prefix reused
   across a lesson (define it in the pilot; think clean, bold,
   diagram-meets-illustration, readable on an iPad at arm's length).
   Images go into the apkg media like card audio does.
5. **Self-containment**: every side opens with a 1-line spoken+written
   anchor ("Beaucoup, trop, assez, peu — plain de") so shuffled review
   still teaches. Scheduling: these are LESSON cards, not drills —
   consider suspending-by-default or a very long initial interval;
   present options at pilot review.
6. **Pilot** = episode 3 (fr quantities, the user-reviewed v2 script):
   restructure that exact script into ~5 notes × 2 sides, generate
   images, build, deliver, STOP for approval. Then the other nine.

## Costs

TTS ≈ same as v2 pilot (clips are cache-shared where text unchanged).
Images: ~10-12 per episode; check current Gemini image pricing and
report cost-per-episode at pilot review before batching.

## Ops rules that WILL bite you if ignored (from hard experience)

- Never git-push while a grammar generation/build run is live (push →
  redeploy kills it; check /admin/grammar-status).
- The web process event loop must never run ffmpeg/bulk work directly
  — asyncio.to_thread (see docs/incidents/2026-07-31-web-hangs.md).
- Bulk DB writes never run in the web process — stage via one blob
  insert, ingest cron-side (see personal_errors.py pattern).
- .gitignore has `*.mp3` — new committed audio/image assets need
  scoped negations (this silently ate the music assets once).
- Verify deploys settled before calling new endpoints (SPA fallback
  returns HTML 200 for unknown paths on the old instance).
- codex: run in isolated worktrees for code, `-c
  model_reasoning_effort="ultra"`, no git ops, supervising session
  reviews and merges.
