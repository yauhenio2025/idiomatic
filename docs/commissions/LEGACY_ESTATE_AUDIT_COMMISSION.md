# Legacy estate audit, import completion & local voicing — commission

> Owner directive 2026-08-08: this is the PRIORITY BEFORE the Expression
> Hub build. Rationale: structure and import the legacy wealth now, so
> the hub's model freeze doesn't get followed by a painful re-import of
> poorly structured data. Owner travels from 2026-08-10; design so the
> bulk phases run unattended (codex + scheduled jobs), with owner gates
> only where verdicts are genuinely needed.

## Context (read first)

- `docs/research/legacy-excercises-audit.md` — the 2026-08-03 audit
  covered ONLY `EXCERCISES::{DE,ES,FR,IT,PT}` (13,377 notes) in the old
  `evgeny.morozov+2@gmail.com` account. Its findings (IT deck = French
  copy-paste; PT BIG_TECH_PHRASES 30/91 Spanish; ES FALSE_FRIENDS
  toxic) are settled — do not re-litigate.
- `docs/research/tenses-old-corpus` memory + docs/research/tenses-profiles/
  — the `_tenses_old` conjugation corpus (14,267 cards) was pulled
  HEADLESSLY from AnkiWeb for the +2 account: that mechanism is proven
  and is the access path for this commission. Never touch the live
  syllabus profile for this work.
- `docs/EXERCISES2_ROADMAP.md` — waves 3–7 of the exercises revival are
  already specified with a proven pipeline (codex batch commissions →
  mechanical gate → audit → merge → `/admin/exercises2-build`).
- CLAUDE.md TTS section — local Qwen3-TTS bridge on the Fedora box
  (`~/llms/qwen3-tts/server/`, `/synth` + `/synth-batch`, bearer auth,
  etiquette gate that defers under GPU contention), cost 0. Render still
  pins `TTS_PROVIDER=elevenlabs`; that pin is NOT touched by this
  commission — voicing here runs as LOCAL batch jobs against the bridge
  (or the model directly), never through the Render chain.
- Memory `content-pilot-first`: every new content format ships ONE pilot
  for owner verdict before batching. Applies to the voicing lane and to
  any newly imported deck family.

## Part A — full inventory of the +2 legacy account (codex-heavy)

1. Fresh headless AnkiWeb pull of the ENTIRE +2 collection (read-only
   copy under `docs/research/legacy_estate_work/`, gitignored;
   reuse/adapt `anki_reorg_scripts/00_inventory.py` + `generate_deck_map.py`
   — they are collection-agnostic read-only tools).
2. Codex-run breakdown, per top-level deck and language (ALL of them:
   the five actives, Mandarin, Scandinavian Pimsleur remnants, anything
   else found): note models, card counts, per-deck study history
   (reps/mature/last-review), audio presence (sound-tag scan), text
   quality flags (MT contamination heuristics from the 2023 audit),
   overlap against content already imported (exercises2 waves,
   _tenses_old profiles, grammar decks).
3. Deliverables: `legacy_estate` DB table (schema.sql, idempotent) +
   read-only dashboard page **`/legacy`** (ui_api JSON + SPA page,
   same read-only pattern as /grammar overview) showing the tree with
   per-deck verdict column: `import | partial | skip | already-covered`
   — verdicts start as codex proposals, owner flips them in ONE sitting
   (this is the only owner gate in Part A; can happen after return).

## Part B — finish the planned imports (existing pipeline, resumed)

- Execute `docs/EXERCISES2_ROADMAP.md` waves 3→6 through the proven
  batch pipeline. Wave 3 TENSES has its verdict (raw lapse order incl.
  literary tenses) and can start immediately; FANCY_VOCAB and the vocab
  trio follow. FALSE_FRIENDS stays a rebuild (F4 territory), not an
  import; COMMANDS/PRONOUNS/REFLEXIVE = gap-audit only, per roadmap.
- Anything Part A marks `import` gets its own wave-style commission
  AFTER its owner verdict — no freelance imports of unaudited decks.
- All new decks land under the estate tree via `anki_root()` lanes.

## Part C — local Qwen voicing lane (cost-0 audio for the un-voiced)

1. **Pilot first**: voice ONE representative deck slice (~30 notes,
   mixed languages) with the frozen clone voices; owner listens and
   verdicts BEFORE any batch run. Ship as a small apkg to the normal
   delivery path.
2. Batch voicing job (machine-local script beside the bridge server):
   walks a work queue of (note, lang, text) rows lacking audio —
   sources: exercises2 waves as they merge, Part-A imports once
   verdicted, any existing imported rows flagged audio-less. Writes
   clips into the server's staged-audio convention; rebuilds ride the
   existing admin endpoints.
3. **GPU scheduling**: the image miner owns the box 24/7 from 08-10.
   Voicing runs (a) opportunistically whenever the ComfyUI queue is
   idle (the bridge's etiquette gate already implements this), plus
   (b) one guaranteed daily window where the miner pauses —
   PROPOSAL: 09:00–11:00 local, right after the current night window,
   sized after a codex benchmark of clips/hour. The window trades
   against image-mining throughput → owner OKs the final split before
   departure or via remote note.
4. ElevenLabs is NOT used for this lane (owner directive: no reason to
   pay when qwen-local exists). Gemini fallback also off — a failed
   clip just stays queued for the next window.

## Sequencing & the Hub

Priority now: A (audit) + B (waves) + C (voicing) → THEN the Expression
Hub build. Hub amendments and hand-off stay recorded in
`docs/RESTRUCTURE_STATUS.md` and `EXPRESSION_HUB_DECISIONS.md`; the hub
model freeze will consume Part A's inventory so legacy content gets
durable IDs on first import, not a re-import later.

## Hard rules

- The +2 account is READ-ONLY source material; its pending purge
  (cleanup.json thread) is untouched by this commission.
- Nothing imports into Anki without going through the server pipeline
  and the estate lanes; no direct collection surgery.
- Codex does the bulk (inventory crunching, wave authoring, benchmark,
  batch scripts); premium sessions design schemas, verify, and gate.
- Every audit artifact is committed (docs/research/legacy_estate/*);
  work-area collection copies stay gitignored.
