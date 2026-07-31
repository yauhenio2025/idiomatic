# Grammar explainer delivery design

## Decision

Ship the explainers as a new listening cluster inside each existing
per-language grammar APKG, not as a separate deck kind. The exact subdeck
names are:

| Language | Cluster | Cards |
|---|---|---:|
| French | `0 Écoute` | 4 |
| Portuguese | `0 Escuta` | 3 |
| Spanish | `0 Escucha` | 3 |
| German | `0 Hören` | 2 |

The zero prefix keeps the listening cards together and sorts them before
the drill clusters. This route reuses the existing `apkgs.kind='grammar'`
delivery, acknowledgement, replacement, media packaging, and subdeck
machinery. A dedicated deck would need another delivery kind and lifecycle
for only two to four cards per language, while also separating each
explanation from the grammar deck whose F3 cards it supports. As with every
shipped cluster name, these four strings become stable once cards are in
learners' collections.

These are authored, static notes. They must not enter the generated
`grammar_items` target-size/top-up loop: a listener should get exactly one
card per source file, and a rebuild must never ask the LLM to manufacture
more of them.

## Source contract

The canonical sources are the twelve Markdown files in
`idiomatic/grammar/data/explainers/`. Each file has this frontmatter shape:

```yaml
---
lang: fr
slug: beaucoup-de
title: "The quantity link"
fossil_evidence:
  - ref: "docs/research/error-profiles/fr.md §3, pattern 1"
    count: 138
est_seconds: 180
---
```

The renderer starts after the single `## SCRIPT` heading and recognizes
three physical-line types:

| Source line | Rendered result |
|---|---|
| Unprefixed prose | English TTS; the Markdown line itself is spoken |
| `TL: …` | Strip `TL:` and use the file's target-language voice |
| `[PAUSE]` | No TTS; insert self-test thinking silence |

Blank lines are structural and are not spoken. No other inline routing
syntax is needed. In particular, target-language examples must not be
embedded in an English line: keeping every complete target utterance on a
`TL:` line is what prevents accent switching inside a TTS request.

Before rendering, fail validation unless all of the following hold:

1. `lang`, `slug`, `title`, `fossil_evidence`, and `est_seconds` are present;
   the filename is exactly `{lang}_{slug}.md`; and the language is one of
   `fr`, `pt`, `es`, or `de`.
2. The script contains 300–450 words after removing the routing markers,
   exactly three `[PAUSE]` lines, and exactly three answers after those
   pauses.
3. Every evidence item has a nonempty internal profile reference and a
   count or an explicitly qualified evidence quantity such as “~35
   teacher-supplied instances.” Avoidance evidence must not be relabeled as
   a learner error.
4. No unsupported control prefix appears. This catches a misspelled `TL`
   marker before an English voice reads the target language.

Counts and learner quotations still require a human source check against
the cited profile; syntax validation cannot establish provenance.

## Audio rendering with the current pipeline

Render one clip per nonblank script line, then stitch the clips in source
order. The implementation can stay on the existing boundaries in
`idiomatic.gemini` and `idiomatic.pipeline.audio`:

- English prose: call `gemini.synthesize` with `voice=EN_VOICE` (`Kore`)
  and `lang="en"`.
- A `TL:` line: call it with `voice=LANG_VOICE[lang]` and `lang=lang`.
  With today's default ElevenLabs provider, `lang` selects the voice ID in
  `ELEVEN_LANG_VOICE`; the named Gemini voice remains the provider fallback.
- `[PAUSE]`: append `silence_mp3(work_dir, 4000)`. Four seconds is long
  enough to produce a short phrase without making a three-question ending
  drag.
- Put `silence_mp3(work_dir, 200)` between adjacent spoken clips, but not on
  either side of an explicit four-second pause. This prevents clipped line
  boundaries without turning blank Markdown lines into timing instructions.
- Call `concat_mp3s(pieces, final_path)` with its default loudness
  normalization. All synthesized and silence inputs are already 24 kHz
  mono, matching the concat contract.

Line synthesis should run concurrently through `asyncio.gather`; the global
TTS semaphore already supplies the provider concurrency bound. Key each work
clip by routed voice language plus a short hash of the effective provider,
model, voice ID, and spoken text, such as `en_<hash>.mp3` or
`fr_<hash>.mp3`. The ordered piece list—not the filename—preserves source
order. This lets an unchanged line survive insertions above it while
ensuring a text or voice correction cannot pick up an old clip.

The final media name should also be content-addressed, for example:

```text
idg_explainer_fr_beaucoup-de_a1b2c3d4.mp3
```

The hash matters because the add-on detects changed media by filename. A
fixed filename could leave an older recording on a device after the script
was corrected. The final hash should cover the ordered constituent cache
keys, language routing, pause duration, and a renderer revision, but not
mutable filesystem paths.

`gemini.synthesize` turns a failed request into a short audio placeholder
and a `.silence` sidecar. For an explainer, one missing line compromises the
whole lesson: if any constituent has that sidecar, do not publish the new
MP3 or its new card. Leave an earlier complete revision in place if one
exists, report the failed slug, and retry on the next rebuild. After concat,
use `ffprobe` to confirm a nonzero MP3 duration and compare it with
`est_seconds`; a large discrepancy is a cue for a missing or accidentally
spoken control line, not a reason to stretch the audio mechanically.

Runtime audio belongs under the existing staged grammar-audio data root,
not in the repository. The Markdown remains the reviewable source of truth.
The stitched file in that staging tree is also the plain MP3 deliverable;
the APKG packages the same bytes rather than producing a second encoding.

## Frozen-model card mapping

Append the twelve static notes during the normal grammar APKG build and use
the existing `make_model()` result unchanged. Do not add a field, rename a
field, alter field order, or add a template. A separate GUID namespace keeps
these static notes stable without pretending that they are database-backed
cloze items:

```text
sha1("idiomatic-grammar-explainer::{lang}::{slug}")[:16]
```

Use the fields as follows:

| Frozen field | Explainer value |
|---|---|
| `ItemId` | `explainer:{lang}:{slug}` |
| `Lang` | frontmatter `lang` |
| `Topic` | `{lang}_explainers` |
| `TenseLabel` | `Grammar radio` |
| `Symbol` | `🎧` |
| `Sentence` | HTML-escaped frontmatter title |
| `Answer` | `Listen` |
| `SentenceFull` | HTML-escaped title again |
| `GlossEn` | empty |
| `Why` | concise evidence summary generated from frontmatter |
| `Extra1` | `[sound:<content-addressed filename>]` |
| `Extra2`–`Extra4` | empty |

Tags should include `idiomatic-grammar`, `grammar-radio`,
`{lang}_explainers`, and the hierarchical fossil tag
`idiomatic-fossil::{lang}::{slug}`. The corresponding F3 correction cards
should receive that same fossil tag. This pairs explanation and production
practice for browsing/search without moving F3 cards out of their topical
drill clusters. Add the explainer note to
`deck_name_for(lang, localized_zero_cluster)` alongside the ordinary drill
subdecks in the same package. Include these notes in the builder's returned
card count so the APKG delivery metadata matches the actual package.

The frozen template renders `Extra1` only on the back. Consequently, v1 is
a title card on the front and the explainer starts automatically when the
learner reveals the answer. That is the intended interaction: see the
topic, choose to listen, then reveal. Front-side autoplay would require
putting a sound tag in `Sentence`; it is not needed here and the model must
not be edited to move `Extra1`.

A source edit updates the note in place because the GUID depends only on
language and slug; the changed content hash gives the corrected MP3 a new
media identity. Renaming a slug is therefore a note-identity migration and
should be avoided after first shipment. Retiring or renaming a shipped
explainer needs the normal cleanup-manifest purge for the old GUID; an APKG
re-import does not delete an absent note by itself. Its content-addressed
MP3 then becomes an orphan for the normal media-cleanup path.

## Size and cost budget

The measured source totals and estimates for this commissioned set are
recorded below. “Characters” means exactly the text sent to TTS after
stripping `TL:`; YAML, `## SCRIPT`, blank lines, and `[PAUSE]` are excluded.
MP3 size assumes the current 24 kHz mono VBR output, approximately
32–48 kbit/s. The APKG/card metadata overhead is negligible beside audio.

| Language | Scripts | Spoken words | TTS characters | Est. audio | Est. MP3 | ElevenLabs at $0.05/1k chars |
|---|---:|---:|---:|---:|---:|---:|
| French | 4 | 1,448 | 8,579 | 12:05 | 2.9–4.4 MB | $0.43 |
| Portuguese | 3 | 1,100 | 6,726 | 9:10 | 2.2–3.3 MB | $0.34 |
| Spanish | 3 | 1,072 | 6,485 | 9:05 | 2.2–3.3 MB | $0.32 |
| German | 2 | 721 | 4,782 | 6:05 | 1.5–2.2 MB | $0.24 |
| **Total** | **12** | **4,341** | **26,572** | **36:25** | **8.7–13.1 MB** | **$1.33** |

Audio time is the sum of the per-source `est_seconds` values. Those use a
reproducible planning rate of 135 English words per minute and 120 target-
language words per minute, plus the specified four-second pauses and
200-millisecond clip gaps, rounded to the nearest five seconds. Actual
duration becomes authoritative after the first `ffprobe` pass.

This is a one-time synthesis cost for the initial revision. Idempotent line
caching makes an unchanged rebuild free; editing one line pays only for
that line, though the final stitched media gets a new content-addressed
name. If `tts_provider` is explicitly switched to Gemini, ElevenLabs cost
is zero except for calls that actually fall back to ElevenLabs.

## Build and review acceptance checks

1. Parse and validate all twelve sources; assert the expected 4/3/3/2
   language split and unique `(lang, slug)` pairs.
2. Render every physical line through the routing table; assert no
   `.silence` sidecars before stitching.
3. Inspect the twelve final durations with `ffprobe`, and human-listen to at
   least the opening, every voice boundary, and all three pause/answer
   transitions in every file. Per-line switching solves accent selection,
   but only listening catches odd prosody on fragments and abbreviations.
4. Build each language APKG and inspect `collection.anki2`: the model ID,
   fourteen fields, and single template remain unchanged; explainer GUIDs
   match the slug formula; each note is in its localized zero cluster; and
   `Extra1` contains exactly one packaged sound reference.
5. Inspect the APKG media map and confirm that all referenced MP3s are
   present once, no work fragments or silence sidecars are packaged, and
   ordinary grammar-drill audio still maps to its original notes.
6. Rebuild without source changes and assert identical explainer GUIDs and
   media names. Then change one fixture line and assert a stable GUID but a
   different media filename.
7. Import a disposable package in desktop Anki or AnkiDroid: the front is a
   title only, reveal starts the audio, replay works, night mode remains
   readable, and existing grammar scheduling survives an update import.
