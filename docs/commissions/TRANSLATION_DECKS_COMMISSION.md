# Commission: Translation-exercise decks from existing grammar drills (code)

> For a codex CLI session. This is a CODE commission (like Wave-7 C-H):
> you write a new module + endpoints + tests in this repo; the reviewer
> merges and deploys. No content authoring.

## The idea (user-approved)

The `Idiomatic Grammar {LANG}` drill decks already contain thousands of
verified target-language sentences, each with (a) a natural English
translation (`grammar_items.gloss_en`) and (b) an ElevenLabs back-audio
clip (drilled form + pause + full sentence) staged under
`staged_audio/grammar/<lang>/`. Repurpose them as **translation
exercises**: FRONT = the English sentence, spoken (new, cheap EN TTS);
BACK = the target-language sentence, spoken (REUSING the existing clip),
with the drilled form bolded and the existing `why_en` explanation shown
when present. Zero new target-language synthesis.

## Deliverables

1. `idiomatic/grammar/translation.py` — the builder module.
2. Two admin endpoints in `idiomatic/api.py`:
   `POST /admin/translation-build?lang` (background task, claims the
   grammar job slot exactly like `/admin/exercises2-build`) and
   `GET /admin/translation-list` (per-lang counts: eligible items, items
   with TL audio present, EN clips already cached).
3. `'translation'` added to the `db.upsert_pool_apkg` kind whitelist and
   the `apkgs.kind` comment in `db/schema.sql`.
4. `tests/test_translation.py` — deterministic tests, no network/DB.

## Reference implementations (read these first)

- `idiomatic/grammar/exercises2.py` — the pattern to follow for: cached
  content-addressed TTS (`audio_cache_key` + `_voice_fingerprint` +
  `leveled_speech_clip`), silence-marker resilience, `build_language()`
  shape, `upsert_pool_apkg` publishing, endpoint structure.
- `idiomatic/grammar/apkg.py::build_grammar_apkg` — audio-map/media
  mechanics, `_full_html` bolding, cluster deck naming, GUID discipline.
- `idiomatic/grammar/service.py::_rebuild` (or equivalent) — where
  verified items, topic labels, clusters, and the drill audio map come
  from; mirror that data flow.

## Specification

**Model** (NEW, frozen forever once merged): `Idiomatic Translation v1`,
`MODEL_ID = 1_820_160_001`, ONE template ("Translate"), 14 fields:
`ItemId, Lang, Topic, TenseLabel, Symbol, EnText, EnAudio, TlHTML,
TlAudio, Why, Extra1, Extra2, Extra3, Extra4`.
- FRONT: meta line (symbol + tense label, like the drill card), the
  English sentence (`EnText`), `EnAudio` (autoplays).
- BACK: meta line, `TlHTML` (full TL sentence with the drilled form in
  `<b>`), `TlAudio`, the English sentence small below, `{{#Why}}`
  explanation box. CSS: adapt the grammar-drill CSS family, including
  the explicit `.night_mode` overrides (AnkiDroid inversion protection).

**Item selection** (from verified `grammar_items`, per lang):
- exclude `fmt` in (`f3`, `f4`, `explainer`) — wrong-phrase fronts,
  contrast pairs, and radio lessons are not translation material;
- require nonempty `gloss_en` and nonempty `answer`/`sentence`;
- require the TL drill clip to ALREADY EXIST on disk (reuse the same
  audio-map mechanism the grammar rebuild uses in reuse-only mode —
  never synthesize a missing TL clip; items without a clip are skipped
  and counted in the build stats);
- skip TL sentences with fewer than 4 words (too small to translate);
- dedupe on (lang, rendered full sentence), first wins.

**Audio**:
- TL: the existing staged clip, packaged exactly as the grammar apkg
  does (basename-only `[sound:]`, media list dedupe).
- EN: synthesize `gloss_en` with the English narrator voice (`EN_VOICE`
  from `idiomatic/pipeline/audio.py`) through `gemini.synthesize`,
  content-addressed cache under
  `staged_audio/grammar/translation_en/<lang>/`, leveled with
  `leveled_speech_clip`; silence-marked failures ship the card without
  EN audio (never fail the build for one clip).

**Identity & delivery**:
- GUID: `sha1("idiomatic-translation::{lang}::{item_id}")[:16]` — stable
  across rebuilds, scheduling preserved.
- Decks: `Idiomatic Translation {LANG}::{cluster}` with the SAME cluster
  strings the grammar deck uses for that item's topic (fall back to the
  root deck when clusterless). Deck ids: stable hash namespaced
  `idiomatic-translation`, in a range disjoint from grammar (1_811_…),
  exercises (1_920_…) — use `1_930_000_000 + sha1 % 60_000_000`.
- Publish: one rolling `_translation.apkg` per lang,
  `kind='translation'`, via `db.upsert_pool_apkg` — the add-on needs no
  changes.

**Tests** (mirror `tests/test_exercises2.py` style): frozen model
identity (id, field list, one template); GUID stability + namespacing;
selection filters (each exclusion rule); bold rendering of the drilled
form incl. HTML escaping; EN cache-key purity/stability; apkg packaging
with fake media (fields land in the right slots, media deduped, deck
name correct); silence-marked EN clip → card ships without EnAudio.

## Hard rules

- Do NOT touch any existing FROZEN model or change any existing module,
  except: registering the two endpoints in `api.py`, the kind whitelist
  in `db.py`, and the schema comment. Zero changes to the add-on.
- No git commands. No new dependencies.
- Run `.venv/bin/python -m pytest tests/ -q` and finish with ALL tests
  green (currently 311 + yours).
- Match house style: structlog, injectable dependencies for testability,
  async where the neighbors are async, comments only for constraints.
- If the actual data flow differs from this spec's assumption (e.g. the
  drill audio map works differently than described), follow the CODE,
  note the divergence in a top-of-module comment, and keep the
  reuse-only guarantee intact.
