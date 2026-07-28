# Technical report: rich grammar-exercise cards on AnkiDroid + feedback loop

> Commissioned research, 2026-07-28. Raw findings; synthesis lives in
> ../GRAMMAR_STRATEGY.md.

## 1. Card-template capabilities on AnkiDroid

### Rendering engine parity (the single most important fact)
Since **AnkiDroid 2.17.0 (2024-02-23)**, AnkiDroid directly includes Anki Desktop code — the Rust backend (`ankitects/anki` rslib) does all template rendering, cloze processing, type-answer diffing, and scheduling (incl. FSRS). Template behavior (conditionals, `{{cloze:}}`, `{{type:}}`, special fields) is therefore **byte-identical to desktop**. Source: https://ankidroid.org/changelog.html

### JavaScript
- Cards render in an Android System WebView (Chromium): modern ES2020+, CSS grid/flex, `<audio>`, canvas all work.
- **AnkiDroid JS API — actively supported.** Current API version `0.0.3` (AnkiDroid 2.18+). Since 2.17 it is **asynchronous (breaking change)** — calls return `Promise<{success, value}>`. Mandatory init contract:
  ```js
  var jsApiContract = { version: "0.0.3", developer: "you@example.com" };
  var api = new AnkiDroidJS(jsApiContract);
  const eta = await api.ankiGetETA();
  ```
  ~46 methods: answering (`ankiAnswerEase1`–`4`), card info, deck counts/ETA, suspend/bury, mark/flag, toasts, night-mode status, TTS (`ankiTtsSpeak`), speech-to-text (2.17+). Docs: https://github.com/ankidroid/Anki-Android/wiki/AnkiDroid-Javascript-API. Another "new JavaScript API" is in the pipeline — pin against `0.0.3` and wrap defensively.
  - **This API does not exist on desktop or AnkiMobile.** Detect platform (`.android` CSS class) and degrade gracefully — "grade yourself inside the card" widgets can only auto-press ease buttons on AnkiDroid.
- JS runs on every side render; no DOM persistence between front and back. `console.log` via `chrome://inspect` USB debugging.

### HTML/CSS + night mode
- Platform classes on `.card`: `.win .mac .linux .mobile .android .iphone .ipad` (AnkiDroid gets both `.linux` and `.android`). https://docs.ankiweb.net/templates/styling.html
- **Night mode pitfall**: if the literal string `.night_mode` appears nowhere in the card CSS, AnkiDroid applies heuristic color-inversion; if it appears anywhere, your CSS is used unmodified. Style both `.card.night_mode, .card.nightMode { … }`; `prefers-color-scheme` also works.
- Conditional sections `{{#Field}}…{{/Field}}` / `{{^Field}}` identical (backend-rendered). Special fields: `{{Tags}} {{Type}} {{Deck}} {{Subdeck}} {{Card}} {{CardFlag}} {{FrontSide}}`.

### Type-in-the-answer
- `{{type:Field}}` — one per card, single-line. Diff via shared backend: classes `typeGood`, `typeBad`, `typeMissed` inside `#typeans`. **`{{type:nc:Field}}`** ignores diacritics — relevant for de/fr/it/pt/es typed drills. Cloze typing: `{{type:cloze:Text}}`; multiple elisions entered comma-separated. https://docs.ankiweb.net/templates/fields.html
- AnkiDroid: since 2.17 the input box is built into the card HTML; 2.21.0 uses Noto Sans Mono for the diff. Historical accent bugs: #4695, #18184. Android IMEs with autocorrect interfere (#4444) — use a keyboard without autocorrect, or own `<input>` + JS + anki-persistence.

### Persistence between front and back
- Canonical solution: **SimonLammer/anki-persistence** (https://github.com/SimonLammer/anki-persistence) — paste at top of both templates; `Persistence.setItem/getItem/clear`. Uses sessionStorage on AnkiDroid, windowKey on desktop. This is how to carry "user chose option B" from front to back. `localStorage` also persists on AnkiDroid but treat as cache only (doesn't sync, can be wiped).

### Audio
- `[sound:file.mp3]` tags autoplay in order of appearance when the side is shown; each renders a `.replay-button`.
- On the answer side, audio inside `{{FrontSide}}` is NOT auto-replayed; to replay front audio on the back, repeat the field explicitly. AnkiDroid "replay question audio" preference changes this.
- Deck option "Don't play audio automatically" exists per-preset. Template-controlled autoplay order (anki PR #3868) is very new — don't rely on it for AnkiDroid.

## 2. Cloze specifics

- `{{c1::answer}}`, hint: `{{c1::answer::hint}}` (renders `[hint]`). Same number in two spans → one card hiding both; distinct numbers → one card per number.
- **Nested clozes since 2.1.56** (AnkiDroid 2.17+): `{{c1::Canberra was {{c2::founded}}}} in 1913`; ~3 levels max; partial overlaps not permitted.
- `{{cloze:Text}}` only on the special Cloze note type (clone it to customize). One card per distinct cN.
- Per-cloze conditionals: `{{#c1}}{{Hint1}}{{/c1}}` — one note type can show different scaffolding per blank. https://docs.ankiweb.net/templates/generation.html
- Styling: active cloze = `<span class="cloze">`, others `.cloze-inactive`, both with `data-ordinal="N"` (2.1.56+). Hide inactive brackets: `.cloze-inactive { all: unset; }`.
- Cloze-only TTS: `{{tts en_US:cloze-only:Text}}` reads only the elided text (useful for "beep + answer" reveals).
- One cloze per note vs many: many-per-note is the intended design but siblings auto-bury (spreads c1/c2/c3 across days). **One cloze per note gives cleaner GUID-based updates and independent scheduling.** Overlapping-cloze beyond native nesting: https://github.com/krmanik/ocloze.

## 3. Review-log data and add-on access (the feedback loop)

### revlog schema (same DB on AnkiDroid)
From https://github.com/ankidroid/Anki-Android/wiki/Database-Structure:
- `id` — review timestamp epoch-ms (PK); `cid` — card id; `usn` — sync seq
- `ease` — button: review: 1=Again 2=Hard 3=Good 4=Easy; learning: 1/2/3
- `ivl` — new interval (negative = seconds, positive = days); `lastIvl`
- `factor` — ease permille; **under FSRS stores normalized difficulty (100–1100)**
- `time` — answer time ms, **capped at 60000**
- `type` — 0=learn 1=review 2=relearn 3=filtered 4=manual 5=rescheduled

### Add-on / headless Python access
- `mw.col` in add-ons; standalone: `from anki.collection import Collection` (pylib officially headless: https://addon-docs.ankiweb.net/the-anki-module.html).
- `col.find_cards("deck:… is:review")`, `col.get_card(cid)`, raw SQL reads fine: `col.db.all("SELECT id, cid, ease, ivl, lastIvl, factor, time, type FROM revlog WHERE cid = ?", cid)`.
- Card object: `ivl, factor, reps, lapses, due, memory_state, desired_retention, last_review_time`. **FSRS**: `card.memory_state` = `FsrsMemoryState{stability, difficulty}`; `None` until first review. Retrievability via `col.card_stats_data(card_id)` — but ~400ms/card, don't bulk-call; read revlog + `memory_state` directly.
- AnkiConnect alternative: `cardReviews`, `getReviewsOfCards`, `getLatestReviewID`.
- Architecture: the add-on POSTs `SELECT … FROM revlog WHERE id > :last_seen` joined to `notes.guid` (via `cards.nid`) — **note GUID is the stable join key between server-side generator and client-side review outcomes**.

## 4. Programmatic deck generation

### genanki (https://github.com/kerrickstaley/genanki)
- GUID: same GUID on import → note update (if models have same fields). **Default GUID = hash of all fields — wrong for an update pipeline**; fix:
  ```python
  class MyNote(genanki.Note):
      @property
      def guid(self):
          return genanki.guid_for(self.fields[0])  # stable key
  ```
- `model_id`/`deck_id`: generate once, **hardcode** (changing model_id on re-import = duplicate mess, issue #49).
- `CLOZE_MODEL` built-in; custom cloze models need `model_type=genanki.Model.CLOZE`.
- Media: `genanki.Package(deck, media_files=[…])`; fields reference basename only; namespace filenames (global to collection).
- Limits: cannot read/modify existing .apkg (#66); no deck presets; no scheduling state; fields are HTML (entity-encode); writes legacy schema-11 (Anki upgrades on import).

### Re-import merge behavior (Anki 23.10+ importer, same on AnkiDroid 2.17+)
https://docs.ankiweb.net/importing/packaged-decks.html:
- Notes matched **by GUID**; default update "if newer" (note `mod` comparison); options Always/If newer/Never for notes and note types.
- **Trap**: genanki sets `mod` at build time; for server-as-source-of-truth, the add-on should import with `update_notes: ALWAYS` (`ImportAnkiPackageOptions` protobuf via `col.import_anki_package`).
- Note type changed between apkg versions → updating "generally not possible"; 23.10+ "merge notetypes" makes field-union hybrids. Avoid by freezing the model. Wart: shared static media (e.g. `_shared.css`) not refreshed on update-import (anki #4491).
- Scheduling: genanki decks carry none, so re-imports never touch existing cards' scheduling — **field updates on an existing GUID preserve FSRS state and review history.**

### Alternative: official `anki` pylib headless
`Collection(path)` + `col.import_anki_package(...)` / `col.export_anki_package(...)` gives real importer/exporter semantics at the cost of the bundled Rust backend dependency.

## 5. Audio: TTS vs bundled mp3

- **Bundled mp3s are the reliable path** — identical everywhere, offline, our ElevenLabs voices.
- `{{tts}}` on AnkiDroid **since 2.17** with desktop-compatible syntax: `{{tts de_DE:Sentence}}`, `{{tts fr_FR speed=0.8:Field}}`, `[anki:tts lang=en_US]static {{Field1}}[/anki:tts]`, **`{{tts es_ES:cloze-only:Text}}`**. On Android the OS TTS engine's voice for the locale is used.
- Autoplay order = template order. "Beep + answer" without JS:
  - Front: `[sound:sentence_with_beep_gap.mp3]` (beep baked server-side with ffmpeg) + `{{cloze:Text}}`.
  - Back: full-sentence mp3 after `{{FrontSide}}` (front audio doesn't auto-replay). Or `{{tts xx:cloze-only:Text}}`.
- JS-triggered `new Audio("file.mp3")` works on AnkiDroid; desktop Qt sometimes blocks relative media paths — `[sound:]` + `.replay-button` is safest.

## 6. Prior art: adaptive/generated drills, LLM decks with feedback

- **AnkiAIUtils** (https://github.com/thiswillbeyourgithub/AnkiAIUtils) — closest to the feedback loop: cron-driven "enhance cards you struggled with yesterday" (revlog → lapsed cards → LLM regenerate → write back).
- **anki-llm** (https://github.com/raine/anki-llm) — bulk generation/regeneration with LLMs.
- **anki-grammar** (https://github.com/Mononofu/anki-grammar) — dynamic grammar-testing cards (JS randomized drill per review).
- **anki_ai** (https://github.com/gasparl/anki_ai) — generated language decks with audio, frequency buckets.
- Conjugation trainers: conjugations2csv, PT_ConjugationTrainer_Anki, Italian fill-in trainer (AnkiWeb 1906054931), https://github.com/bikenik/Anki_Templates.
- Morphman-style for grammar: nothing mature exists — server-side LLM generation + revlog-driven re-targeting of grammar points has no established tool; AnkiAIUtils' cron pattern is the precedent.

## 7. Deck flow, sync churn, full-sync avoidance

- Flow: add-on imports into desktop collection → AnkiWeb → AnkiDroid. No direct deck subscription on Android; stick with sync. Add-on can schedule a sync after import; AnkiDroid has auto-sync options.
- **Frequent .apkg imports are normal-sync safe** (note adds/updates, new cards, media are mergeable deltas). Media sync detects changes **by filename** — if regenerating an mp3, version the filename.
- **What forces a one-way (full) sync**: adding/removing/renaming/reordering **fields**, adding/removing **card templates** on an existing note type, note-type deletion, DB repairs. Template HTML/CSS edits do NOT; importing notes does not.
- Consequences:
  1. **Freeze the model**: never change field count/order/names or template count of a shipped `model_id`. Reserve `Extra1..ExtraN` spare fields up front.
  2. Schema evolution = new model_id + new GUIDs (old deck purged via cleanup.json), not mutation.
  3. Template HTML/CSS iteration is cheap via re-import with notetype update.
  4. Add-ons that dodge full sync for note-type surgery exist but are risky; don't build on them.

## Design recommendations distilled

1. Put exercise logic in shared backend features (cloze + per-cloze conditionals + `{{type:nc:}}` + bundled audio), not JS.
2. JS only progressively: anki-persistence for front→back state; AnkiDroid JS API for tablet-only extras (self-scored multiple choice pressing `ankiAnswerEase1/3`).
3. Stable GUIDs from DB primary keys, frozen `model_id`, versioned media filenames → re-imports become clean field-level updates preserving FSRS state.
4. Feedback loop via the existing add-on: incremental revlog export keyed on `notes.guid`, plus `card.memory_state.difficulty/stability`; avoid `card_stats_data` in bulk.
