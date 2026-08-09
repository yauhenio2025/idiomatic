# Grammar Course — design of record

> Commission: docs/commissions/GRAMMAR_COURSE_COMMISSION.md (owner vision
> 2026-08-09 + coordinator-taken decisions). Binding principle:
> PERSONAL_DJ_COMMISSION.md §Owner-ratified — exercises are ATOMIC,
> individually-graded cards, never embedded in lesson cards.
> Engine: `idiomatic/grammar/course.py`. Tests: `tests/test_course.py`.
> Pilot: DE Kasus — see GRAMMAR_COURSE_PILOT_NOTES.md.

## 1. Unit anatomy

A unit = one grammar topic taught as a sequenced pair of populations:

- **Lesson cards** — ~10 two-sided cards ("twenty slides"), the
  podcast_lesson embryo grown up: audio-first English narration with
  target-language examples, an authored SVG diagram on sides where a
  diagram genuinely teaches (visual is OPTIONAL per side — unlike the
  podcast model's mandatory visual), NO exercises on lesson cards.
- **Exercise cards** — a distinct card population: atomic, one graded
  answer per card. v1 source is BOOK-derived items from a verified
  workbook corpus; LLM-generated items are a reserved later provenance.

Lesson sources are Markdown at
`idiomatic/grammar/data/course/lessons/<lang>_<unit>.md`
(`series: grammar-course-lesson`), reusing the proven podcast-cards line
grammar (`[CARD]` × 8–12, `[SIDE]`, `TITLE:`, `SVG:` sidecar in
`lessons/svg/`, `SHOW:`/`TL:`/`TL-:` display+narration, `[PAUSE:ms]`)
plus one course-specific addition: every side MUST carry a
`REF: <§-id>[, <§-id>…]` line — the per-slide Sources footer, rendered
as `Hammer §2.2 · §6.1`. Lesson scripts are authored in OUR OWN WORDS,
grounded in the named sections; they never contradict the book.

## 2. Frozen models (range 1_820_190_0xx)

Both models are FROZEN on first ship, same doctrine as every other deck
model (docs/research/ankidroid-tech.md): never change field count, field
order, field names, or template count. Spares absorb future needs.

### Idiomatic Course Lesson v1 — `1_820_190_001`
14 fields, 1 template, mirrors the podcast lesson shape:
`LessonId, Unit, Seq, Lang, FrontHTML, BackHTML, FrontAudio, BackAudio,
FrontImage, BackImage, Extra1..Extra4`.
`FrontImage`/`BackImage` hold inline SVG markup (house palette classes,
night-mode override block in the model CSS) or an `<img>`; empty when
the side has no visual. GUID = sha1(`idiomatic-course-lesson::lang::
unit::seq`)[:16] — re-authoring a slide updates fields in place and
preserves scheduling.

### Idiomatic Book Exercise v1 — `1_820_190_002`
15 fields (3 spares), 1 template:
`ItemId, Lang, Unit, Block, Instruction, PromptHTML, SolutionHTML,
AltsHTML, SourceRef, HammerRefs, Provenance, SolutionAudio, Extra1,
Extra2, Extra3`.
This is a NEW model, not Exercises v1 (`1_820_150_001`): workbook items
are monolingual (German prompt → German full solution), where Exercises
v1 is EN→TL production. Front = compact instruction + prompt; back =
full solution with the answer in `<mark>`, alternatives as chips, then a
footer `Hammer §… · PGG Kap./Üb./Nr. · provenance`. GUID =
sha1(`idiomatic-course-exercise::lang::unit::item_id`)[:16] with
`item_id` derived from the workbook coordinates (e.g.
`pgg-c02-e04-i3`) — stable across reselection and reordering.

Deck ids: `1_930_000_000 + sha1 % 60_000_000` — disjoint from the pool
(1.82G) and grammar/exercises2 (1.92G) formulas.

## 3. Deck layout and the interleave

Per taken decision #1, each unit is two subdecks under the estate tree:

    <ROOT>::2 Grammar::<unit_label>::1 Lesson
    <ROOT>::2 Grammar::<unit_label>::2 Exercises

composed from `anki_tree.anki_root(lang)` (never bake roots). Pilots use
`root_override` (the disposable `ZZ Grammar Course Pilot (disposable)`).

**First exposure is encoded in new-card due positions** (taken decision
#2). The interleave unit is one lesson CARD = two slides (front+back):
lesson card 1, its exercise block, lesson card 2, its block, … Blocks
are keyed to lesson card seq (`Block` field = `cNN`); blocks may be
empty — cards then follow one another directly. `course.interleave_plan`
returns 1-based, contiguous, unique due positions across BOTH decks;
`build_course_apkg` writes them via genanki's per-note `due`.

Caveat (client-side): with the v3 scheduler's default "gather by deck",
studying the parent deck would exhaust `1 Lesson` before `2 Exercises`.
The interleave requires new-card gather order **Ascending position** on
the unit's deck options preset — a one-time client setting (or the DJ's
filtered decks, which order by due anyway). Flagged in the pilot notes.

## 4. Provenance & telemetry keys (tags, never flags)

Card-type/tags are the data key; flags stay a visual convenience
(commission). Tag scheme:

- both populations: `idiomatic-course`, `idiomatic-course::<lang>::<unit>`
- lessons add: `idiomatic-course-lesson`,
  `idiomatic-course-block::<lang>::<unit>::cNN` (its own card seq)
- exercises add: `idiomatic-course-exercise`, the SAME block tag (the
  lesson card they follow — the lesson-slide span key for failure
  clustering), and `idiomatic-course-src::<provenance>`
  (`book-verbatim` now; `llm-generated` reserved; book beats LLM on
  conflict per taken decision #4)
- notes shipped without audio carry `idiomatic-course-audio-pending`
  (dropped automatically on the audio rebuild — same GUIDs, fields
  update in place)

The telemetry lane (Hub Balanced thresholds per taken decision #3) joins
revlogs → cards → note tags: exercise failure clustering per block tag
selects the lesson cards to resurface (`…-block::…::cNN` names them
directly), then escalates to commissioning per the commission ladder.

## 5. Book-grounded content flow & copyright (HARD RULE)

The repo is public; transcribed book content NEVER enters git.

- Committed: engine, tests, tools, design docs, lesson scripts (our
  words + §-citations), authored SVGs.
- Gitignored (machine-local): `idiomatic/grammar/data/course/
  book_local/` — the selected exercise JSONs and any built pilot APKG.
  A test asserts the path is ignored (`tests/test_course.py::
  TestCopyrightGuard`).
- The sealed corpora (`docs/research/grammar_books/*.tar.gz`) stay
  read-only inputs, extracted to scratch, never committed extracted.

Selection pipeline (per corpus): a committed selector tool (e.g.
`tools/course_select_de_kasus.py`) reads the extracted corpus and emits
`book_local/<lang>_<unit>.exercises.json`:

- **book-verbatim only**: any Pass-2 flag (`reconstructed-by-model`,
  `judgment-call`, `answer-by-model`, `source-suspect`, …) excludes the
  item;
- **structural hygiene gate** re-checks every solution (nonempty
  `<mark>`, no leftover blanks, no markup beyond `<mark>`, no slash-list
  remnants, no mark span ≥3 words duplicating prompt text) because the
  corpus carries mangled reconstructions even on unflagged items
  (Case ex. 16);
- `mode="key"` fallback for construct-the-whole-sentence exercises whose
  reconstructed HTML is unusable: the printed answer key verbatim,
  wrapped in one whole-sentence `<mark>` — still book-verbatim;
- per-exercise Hammer §-refs are verified against the workbook's printed
  `(GGU …)` exercise headers, not inferred.

`course.parse_exercises_file` re-validates everything at load time.

Production delivery (design, not yet built): because book content cannot
ride the public repo, server-side builds will take exercise JSONs via an
admin upload endpoint (`POST /admin/course-upload-exercises`, admin
token, stored in a `course_exercises` table) — the same trust boundary
as the dashboard mutation surfaces. Until then, units build locally via
`tools/course_build_pilot.py` and can be delivered as ordinary APKGs.

## 6. Audio pipeline (local-TTS seeding contract — immediate follow-up)

The pilot ships audio-pending by design. The wiring below follows the
exercises2 seeding pattern in `idiomatic/local_tts.py` and is the
immediate follow-up after pilot approval:

- **Lesson narration** — `source_kind="course_lesson_segment"`. Lesson
  sides are multi-voice (EN narration + TL examples), which the
  one-clip-one-voice queue cannot express as a single job; so seed ONE
  JOB PER SPEECH SEGMENT, mirroring `render_explainer`'s per-segment
  clip cache: `note_key = course:<lang>:<unit>:<seq>:<side>`,
  `clip_kind = seg<NNN>` (zero-based segment index), `lang` = the
  segment's routed voice (`en` or the TL), `text` = the segment text,
  `content_hash = content_hash(text, voice_lang)`, staged path via
  `canonical_staged_path`. The builder stitches completed segment clips
  in script order with the script's `[PAUSE:ms]` gaps, levels to the
  house loudness, stages the two per-side MP3s, and rebuilds the APKG —
  same GUIDs, so scheduling survives and the audio-pending tag drops.
- **Exercise solutions** — `source_kind="course_exercise"`,
  `note_key = course:<lang>:<unit>:<item_id>`, `clip_kind="solution"`,
  `text` = the solution plain text: `<mark>` unwrapped, bracketed
  original-prompt fragments (`[der weite Weg]`) and parenthetical key
  commentary stripped, whitespace collapsed. One clip per exercise into
  `SolutionAudio`. (No prompt audio in v1: prompts contain blanks.)
- Both kinds ride the existing lease/upload/validate machinery
  (`CONTRACT_VERSION`, `VOICE_VERSION`, MP3 size gates) — the module's
  "no silent fallback" stance applies: a missing clip keeps the note
  audio-pending rather than falling through to ElevenLabs.

## 7. Relationship to existing systems

- **podcast_cards** (`1_820_140_001`) — the proven embryo; untouched.
  Existing grammar-walk episodes keep their lane (e.g. DE Ep 5 "Die
  Fälle" is an error-profile walk; the Kasus unit is the systematic
  book-grounded course — complementary, not duplicates).
- **exercises2 / grammar drills / tenses** — separate lanes and models;
  new units reference, never duplicate.
- **Personal Study DJ** — consumes the tag scheme (§4) and serves units
  through filtered decks; the due positions define first-exposure order.
- **Hub telemetry** — shared weakness machinery; Balanced thresholds are
  the starting escalation values.

## 8. Next corpora

The Hammer/PGG pattern generalizes: per language, one reference grammar
(sections with stable §-ids) + one exercise source keyed to it. The Mac
codex lane owns book structuring; this engine only ever consumes sealed,
provenance-flagged corpora in the ch/ex/item shape.
