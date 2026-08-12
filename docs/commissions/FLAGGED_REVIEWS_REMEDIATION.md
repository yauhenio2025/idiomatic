# Flagged-review remediation (owner's in-review problem flags)

Owner flags problem cards during reviews (mostly RED flag 1; a few
2/4/6). Pulled 2026-08-12 ~05:30 via the rescue-autopilot headless
AnkiWeb sync (`_pull_collection_blocking`; ANKIWEB_HKEY in prod env).

Extracts (committed):
- `docs/research/flagged_reviews/flagged_cards.json` — all 140 flagged
  cards (card_id, note_id, guid, flag, deck, model, tags, previews).
- `docs/research/flagged_reviews/flagged_euro_full.json` — the 17
  EUROPEAN pipeline cards with FULL fields (13 `YouTube Expression
  Pool v1` + 4 `Idiomatic Grammar Drill v1`).

## Population A — 17 European cards (OUR pipeline; fix these)

Phase 1 DIAGNOSIS (codex, read-only): for each of the 17, map the note
to its DB rows — pool cards join `expression_examples` /
`expression_idioms` via the note GUID scheme in
`idiomatic/pipeline/pool.py`; grammar drills join `grammar_items` via
GUID in `idiomatic/grammar/apkg.py`. Classify the defect: (a) missing/
empty audio field, (b) audio present but wrong/truncated (can't hear —
flag for re-TTS anyway), (c) target-language error in text, (d) other.
Output `docs/research/flagged_reviews/DIAGNOSIS.md` + machine
`diagnosis.json` (note_id → {db_table, db_id, defect, proposed_fix}).

Phase 2 FIXES (coordinator-gated):
- Audio defects in pool cards: null the stale audio paths in
  `expression_examples` (or re-seed via the expression-pool local-TTS
  seed) → local-TTS voices → `/admin/rebuild-pools?lang=…` →
  add-on re-imports (GUID-stable).
- Grammar-drill text defects: fix via `/admin/retire-item` +
  regenerate, or direct `grammar_items` correction + grammar rebuild
  (deckmap rebuild endpoints in api.py).
- Text defects in pool examples: correct `expression_examples` rows,
  re-TTS the changed clips, rebuild pools.
- After fixes land in Anki, CLEAR the flags so the owner's flag lane
  stays a clean inbox: flags live client-side — clearing needs either
  an add-on step (extend cleanup.json mechanism with a
  `clear_flags: [card_ids]` key) or owner does it manually
  post-verification. Decide with the owner.

## Population B — 123 Mandarin cards (external builders; DO NOT touch
from idiomatic)

96 `Mandarin Prop` + 25 `Mandarin Character - Video` + 2 `Mandarin
Zone` — built by the external Mandarin/pimsleur repos. Park for a
dedicated post-trip session with those repos; the manifest has
everything needed.

## Recurring lane

The flag pull is one command (see the ledger). Make it a routine:
each coordinator session pulls flags, diffs against
`flagged_cards.json`, and feeds NEW European items through phase 1-2.
