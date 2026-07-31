# Codex commission I: explainer TTS delivery ("grammar radio")

> Work dir: /home/admin/projects/idiomatic-wt/explainers (isolated
> worktree). No git ops; `uv run pytest tests/` green. Read first:
> docs/commissions/unit-specs/EXPLAINERS_DESIGN.md (the design YOU
> follow), idiomatic/grammar/data/explainers/*.md (the 12 scripts),
> idiomatic/grammar/audio.py + idiomatic/pipeline/audio.py
> (concat_mp3s, silence_mp3, LANG_VOICE) + idiomatic/gemini.py
> (synthesize; EN voice is "Kore"), idiomatic/grammar/service.py.

## Goal

Turn the 12 explainer scripts into stitched mp3s + one card each,
delivered through the existing grammar decks.

## Implementation shape

- `grammar/explainers.py`: parse a script file (YAML frontmatter +
  body); split into segments: EN prose lines → Kore voice, `TL:` lines
  → the language's LANG_VOICE, `[PAUSE]` → silence_mp3(1500). TTS each
  segment idempotently (persist under
  /data/staged_audio/grammar/{lang}/explainers/, filename from
  slug+segment hash so re-runs reuse), stitch with concat_mp3s.
- Cards: one grammar_items row per explainer (fmt='explainer',
  status='verified', topic = per-lang unit like fr_ecoute; cluster
  "0 Écoute" per the design — final localized strings recorded in
  unit-specs). Sentence = title card text, Answer = the 1-line rule
  takeaway (add a `takeaway:` frontmatter field to each script — you
  may edit the 12 script files for this), Why = fossil evidence line,
  audio = the stitched mp3 via the existing Extra1 [sound:] path
  (audio map in service.rebuild_grammar_deck: extend ensure_audio or
  bypass with a pre-built map — keep it minimal and documented).
- Endpoint `/admin/explainers-build?lang=` (background task, poll
  grammar-status pattern): TTS+stitch that language's scripts, insert/
  update card rows; deck rebuild stays a separate explicit action.
- CRITICAL prod constraint: ALL ffmpeg/stitch work via
  asyncio.to_thread (see docs/incidents/2026-07-31-web-hangs.md; the
  event loop must never run subprocesses directly).
- Tests: parser (frontmatter, TL:/[PAUSE] segmentation, takeaway),
  segment→voice routing table, card field mapping — pure functions,
  no network/DB; fake TTS by injection.
