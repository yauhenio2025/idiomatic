# Commission: Mandarin SENTENCE reading — porting the idiomatic method stack to the Memory Palace

> For a FRESH session. This is an EXPLORATION-then-pilot commission:
> the deliverable is first a well-argued design, then ONE pilot after
> user approval (pilot-first is a standing user directive — see
> memory content-pilot-first.md and docs/HANDOFF_SESSION_MEMO.md).

## Mission (user's words, 2026-08-04)

"Look into how we can apply our methods — videos, comics, images,
etc. — to study not just multi-character words but also SENTENCES
containing them, which we already have in the DB from the hanzi movie
method. Explicitly explore useful methods for improving reading of
sentences, leveraging the innovative methods we've developed here."

## The two systems you are bridging

1. **Mandarin Memory Palace** (~/projects/mandarin-videos — Next.js +
   Prisma; also mandarin_scrape.db): deterministic mnemonics — initial
   sound → actor, final → location, tone → zone within location,
   radicals → props; 8-second AI videos per character, "word films"
   composing character memories for multi-character words, and
   SENTENCE data containing those words. Phase 0 of your work: audit
   prisma/schema.prisma + the DBs and report exactly what sentence/
   word/character/video assets exist, their counts and quality, before
   designing anything.
2. **idiomatic** (~/projects/idiomatic — this repo): the European-
   language grammar system whose innovations are the toolkit to port:
   - **Podcast-card lessons** (APPROVED format 2026-08-03): multi-side
     Anki notes with per-side audio + "flip the card" narration cues,
     frozen dedicated model `Idiomatic Podcast Lesson v1`
     (1_820_140_001), [CARD]/[SIDE]/TL-:/SVG: markup, built via
     /admin/podcast-cards-build. Review lessons already encoded in
     docs/commissions/PODCAST_CARDS_BATCH_COMMISSION.md — READ THEM
     (spoken navigation cues; no target-language phrases through the
     EN voice; fixed practice pattern EN prompt → THINK music →
     TL answer → echo → tip).
   - **Authored SVG sidecars** for visuals (user: "we switch to svgs
     for sure" — generated raster images drifted semantically; SVGs
     are precise, $0, themeable via s-* palette classes with night-
     mode overrides). Generated images (gemini-3-pro-image-preview,
     ~$0.134/img) reserved for mood/scene shots only.
   - **Leveled dual-voice audio**: per-clip -16 LUFS leveling,
     [PAUSE:ms]/[THINK:ms]/[CHIME]/[MUSIC:intro|outro], content-
     addressed clip cache (explainers.py).
   - **Personalization from evidence**: the user's LingQ mirror in
     the idiomatic DB includes ~3.2k zh terms with learning status —
     a machine-readable KNOWN-VOCABULARY inventory for Mandarin.
   - **Verification discipline + volume rule**: nothing unverified
     ships; small batches; never bulk-dump a syllabus.

## Directions to explore (starting points, not limits)

1. **Comprehensibility-graded sentence cards**: rank the DB's
   sentences by coverage against the user's known set (LingQ zh
   status + characters with completed films) → i+1 sequencing; each
   card = sentence with exactly one frontier element.
2. **Mnemonic continuity**: the sentence's unknown word is the one
   whose actors/props/location the user already met in its word film
   — the sentence card VISUALLY quotes that scene (SVG panel echoing
   the film's actor/prop iconography) so word recall chains into
   sentence reading.
3. **Comic-strip lessons**: a sentence as a 3-4 panel multi-side card
   lesson (podcast-card machinery): panel 1 scene-setting, panel 2
   the sentence with word-segmentation visualization, panel 3 the
   frontier word's mnemonic quote, panel 4 production challenge.
4. **Segmentation + tone visuals**: SVG chunking of the sentence
   (word boundaries are THE Mandarin reading skill), tone coloring
   conventions, karaoke-style per-chunk reveal across sides (HTML/CSS
   only — must work on iPad Anki; see docs/research/ankidroid-tech.md
   for what the renderer supports).
5. **Audio echo-reading**: leveled zh TTS (check ELEVEN_LANG_VOICE
   zh support; else Gemini TTS) with [THINK] gaps: hear → read →
   speak → hear again; sentence-final recall probes.
6. **Video composition**: whether/how the existing 8s films can be
   sequenced or referenced (not necessarily embedded — Anki media
   size!) for sentence-level scenes; be honest about cost and size.

## Deliverables

1. `docs/research/MANDARIN_SENTENCE_READING.md` (in the idiomatic
   repo): Phase-0 asset audit; the design space explored with honest
   trade-offs; 2-3 concrete method proposals RANKED, each with data
   requirements, build cost, and what it borrows from the idiomatic
   stack; a pilot spec for the top proposal (scope: ONE lesson /
   ~10-20 sentences).
2. STOP for user approval. Then build the pilot only.

## Ops notes

- Read docs/HANDOFF_SESSION_MEMO.md for the full ops rulebook
  (push-kills-runs, deploy settling, event-loop rule, cron
  containment, gitignore traps, codex-at-ultra worktree pattern).
- The Mandarin project may have its own conventions — read its
  CLAUDE.md/DATA_MANIFEST.md before touching anything; audit
  read-only first.
- Delivery target is the user's Anki (which profile holds the
  Mandarin decks — CHECK, don't assume; the add-on delivers to
  whichever profile is open and grammar lives in SYLLABUS).
- Personal data (LingQ export contents, learning states) stays out
  of public repos.
