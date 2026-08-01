# Grammar Walks podcast design

## Decision

Render the ten authored episodes with a podcast adapter over the existing
grammar-explainer audio machinery, then deliver Season 1 as numbered plain
MP3 files for manual sync to the listener's phone. This is the recommended
first release.

The renderer is already good at the difficult part: routing English and
target-language lines to different voices, caching each line by content and
voice, inserting generated silence, stitching with `ffmpeg`, normalizing
loudness, rejecting silent fallback clips, and naming the completed audio by
content hash. A long walk needs those properties, but it does not benefit from
being scheduled as a fifteen-minute Anki review. Plain MP3s also give the
listener the normal background-play, seek, and resume behavior of an audio
player without adding a feed, authentication, or another server lifecycle.

This is a delivery decision, not a second rendering path. A later card or RSS
release should package or serve the same verified audio master.

## Canonical Season 1 inventory

The source of truth is the following ten files under
`idiomatic/grammar/data/podcasts/`:

| Episode | Source | `lang` | Exact title |
|---:|---|---|---|
| 1 | `es_subjunctive-machine.md` | `es` | The subjunctive as a machine |
| 2 | `x_portuguese-speaks-spanish.md` | `x` | Why your Portuguese speaks Spanish |
| 3 | `fr_quantity-system.md` | `fr` | The French quantity system |
| 4 | `fr_gender-is-memory.md` | `fr` | Gender is memory, not logic |
| 5 | `de_case-system.md` | `de` | The case system as who-does-what-to-whom |
| 6 | `de_adjective-endings.md` | `de` | Adjective endings: one decision tree |
| 7 | `it_congiuntivo.md` | `it` | Il congiuntivo for people who avoid it |
| 8 | `it_deceptive-plurals-and-genders.md` | `it` | Plurals and genders that lie |
| 9 | `pt_future-subjunctive.md` | `pt` | Future subjunctive: the tense only Portuguese kept |
| 10 | `x_four-romance-languages.md` | `x` | Four Romance languages in one head |

Episode numbers, not filenames or alphabetical order, define playback order.
The validator must match this exact episode-to-filename-to-language-to-title
map and reject any additional Markdown source whose `series` is
`grammar-walks`. Renaming a source after release is an identity migration.

## Authored-source contract

Every file has YAML frontmatter with exactly these required fields:

```yaml
---
series: grammar-walks
episode: 1
lang: es
title: "The subjunctive as a machine"
est_minutes: 16
evidence_refs:
  - "docs/research/error-profiles/es.md §6"
---
```

The body begins at the single `## SCRIPT` heading. Its routing conventions
deliberately extend, rather than replace, the explainer conventions:

| Physical source line | Podcast rendering |
|---|---|
| Unprefixed prose | Strip Markdown emphasis and speak with the English narrator |
| `TL: ...` | Strip `TL:` and use the file's `lang` voice |
| `TL: [pt] ...` | Strip both controls and use the explicitly named voice |
| `[PAUSE]` | Insert self-check thinking silence; do not synthesize the marker |
| Blank line or Markdown heading | Structure only; do not speak it |

The inline language tag is required on every `TL:` line when `lang: x`. It is
used in Episodes 2 and 10 because a single default target voice cannot render
Spanish, Portuguese, Italian, and French accurately. Allowed tags for this
season are `[de]`, `[es]`, `[fr]`, `[it]`, and `[pt]`. In a monolingual file,
bare `TL:` is preferred; an explicit tag is valid only if it matches the file
language.

Validate each source before TTS:

1. `series` is `grammar-walks`; `episode` is unique and covers 1 through 10;
   `lang` is `de`, `es`, `fr`, `it`, `pt`, or `x`; and the source matches the
   canonical filename, language, and exact title in the inventory. Reject an
   extra `grammar-walks` source rather than silently rendering eleven files.
2. Spoken script content is 1,800–2,600 words, with an estimated duration of
   12–18 minutes. The post-render `ffprobe` duration is authoritative.
3. There are four to six `[PAUSE]` markers. Each is followed by the answer on
   the next nonblank `TL:` line. A prompt may contain a `TL:` line before the
   pause, but the answer must remain after it.
4. The ending contains an explicit sixty-second recap. The recap should be
   roughly 120–160 spoken words and introduce no new rule.
5. Every learner quotation is supported by an `evidence_refs` source. A
   teacher-supplied construction, recurrence signal, self-reported weakness,
   inferred correction, or absence from the corpus must never be relabeled as
   a recorded learner error.
6. No spoken physical line exceeds 1,200 Unicode characters. Split a longer
   paragraph at a sentence boundary so provider requests remain bounded and a
   small edit does not invalidate an enormous cache segment.
7. Unprefixed narration contains no target-language form that needs native
   pronunciation. Put that form on a `TL:` line and let the surrounding
   English refer to “the first form,” “the target,” or its translated meaning.
   This applies to learner errors as well as correct examples.

The Markdown is the reviewable source of truth. Generated clips and final MP3s
remain runtime artifacts outside the repository.

## Reusing the explainer renderer

The completed explainer implementation in
`idiomatic/grammar/explainers.py` cannot parse these files unchanged. Its
contract currently fixes a 300–450-word script, exactly three pauses, the
`fossil_evidence` mapping shape, the `fr|pt|es|de` language set, a filename
derived from `lang` plus `slug`, and one target voice per file. Italian and
cross-language routing are therefore parser gaps, not stitcher gaps.

Add a small podcast source model and parser rather than weakening the shipped
explainer contract. The adapter should produce the same ordered `Segment`
concept used by the renderer: English speech, language-coded target speech,
and pauses. Generalize the low-level routing/render function to accept a
segment's own language; keep `parse_explainer`, its expected 4/3/3/2 corpus
split, and its tests intact.

The render flow is:

1. Parse and validate one episode.
2. Convert unprefixed prose to English speech segments. Convert bare or
   tagged `TL:` lines to target speech segments, stripping all routing text.
3. Cache every speech clip from the configured provider-chain fingerprint,
   model and voice settings, language, and spoken text. Italian already has
   entries in both `LANG_VOICE` and `ELEVEN_LANG_VOICE`. The current synthesis
   API can fall back without returning provider provenance, so the key must not
   claim to identify the provider that actually answered. If a later release
   requires one provider per language route, first extend synthesis to return
   actual provider, model, and voice provenance and enforce that invariant
   before stitching.
4. Synthesize the episode's missing clips concurrently. The existing global
   TTS semaphore remains the concurrency limit.
5. Use `silence_mp3` for a six-second podcast self-check pause and the existing
   200-millisecond gap between adjacent speech clips. Six seconds is
   intentionally longer than the explainer renderer's 1.5 seconds because
   these prompts often require choosing and producing a full clause, not
   recalling one short token.
6. Refuse to stitch if any constituent is empty or has a `.silence` sidecar.
   A missing answer in a long episode is not an acceptable degraded build.
7. Call `concat_mp3s` and `ffprobe` through `asyncio.to_thread`, as the
   explainer path does. Never block the web event loop with `ffmpeg`.
8. Derive `slug` from the source filename stem after its leading `{lang}_`;
   require the ASCII pattern `[a-z0-9]+(?:-[a-z0-9]+)*`. A slug change is an
   identity migration. Name the immutable staged output from series,
   zero-padded episode number, slug, renderer revision, and ordered
   constituent hashes, for example
   `idg_podcast_grammar-walks_03_quantity-system_a1b2c3d4e5f6.mp3`.
9. For manual export, create a copied or remuxed distribution file under a
   friendly ordered name such as `03 - The French quantity system.mp3`.
   Sanitize title punctuation that is unsafe on common phone filesystems.
   Never hard-link a file that will receive tags: ID3 metadata changes bytes
   and would mutate the staged inode. Embed title, track number, album
   `Grammar Walks: Season 1`, and language metadata at export time; use `mul`
   for `lang: x` if the tagger supports ISO 639-2, otherwise omit that tag.
   Record metadata fields and the distribution-file hash in an export
   manifest. Tagging must not force a second TTS pass.

There is no practical duration ceiling in the current stitcher. It uses an
`ffmpeg` concat list rather than placing every input path on the command line,
and line-level clips keep provider calls short. A fifteen-minute final file
does make loudness normalization and probing longer than for a three-minute
explainer, so build episodes serially while retaining concurrent synthesis
inside one episode. The current concatenator uses LAME quality-mode VBR, not
a fixed bitrate, so do not enforce a speculative size range. Record actual
duration with `ffprobe` and actual bytes in the export manifest. If device
size later becomes a constraint, add an explicit-bitrate distribution encode
and listening-test it separately from the staged master.

## Cost budget

ElevenLabs is budgeted at approximately $0.05 per 1,000 synthesized
characters. The commission's representative 2,500-word script—about 15,000
spoken characters—would cost about $0.75. The completed Season 1 sources are
shorter than that ceiling: they contain 124,273 measured spoken characters,
for an estimated initial-render cost of **$6.21**.

| Episode | Spoken characters | Estimated cost |
|---:|---:|---:|
| 1 | 11,908 | $0.60 |
| 2 | 12,599 | $0.63 |
| 3 | 12,932 | $0.65 |
| 4 | 11,444 | $0.57 |
| 5 | 12,936 | $0.65 |
| 6 | 12,586 | $0.63 |
| 7 | 12,528 | $0.63 |
| 8 | 12,329 | $0.62 |
| 9 | 12,131 | $0.61 |
| 10 | 12,880 | $0.64 |
| **Season 1** | **124,273** | **$6.21** |

Keep **$7.50** as contingency headroom for pronunciation fixes, regenerated
lines after review, and provider-side character-count differences—not as the
measured initial-render estimate.

Only text actually sent to TTS counts: exclude YAML, headings, blank lines,
`TL:` and `[xx]` controls, and `[PAUSE]`. English and target-language lines
are billed alike. The content-addressed line cache makes a no-change rebuild
free and a one-paragraph correction cost only that paragraph; the completed
MP3 still receives a new hash so stale device media cannot masquerade as the
revision.

## Delivery options

| Option | Strengths | Costs and failure modes | Decision |
|---|---|---|---|
| Cards in localized `0` listening clusters | Reuses grammar APKG delivery and the familiar title/reveal/audio interaction; no manual media copy | A 12–18 minute lesson is not a spaced-repetition item; ratings and due dates add noise, resume/seek behavior is player-dependent, Italian needs a new listening unit, and `x` episodes need an arbitrary owning deck or duplication | Do not use for Season 1 |
| Numbered plain MP3s | Smallest implementation; same verified stitched asset; works in an ordinary phone audio player with background playback, seeking, and resume; cross-language episodes need no fake deck owner | One manual copy after a release or correction; no automatic discovery | **Recommended for Season 1** |
| Private RSS feed served by the app | Best eventual podcast UX: subscription, episode order, automatic downloads, cover art, and one canonical cross-language series | Requires a stable media endpoint, feed generation, absolute URLs, range requests, cache headers, per-user token/auth design, revocation, and deployment monitoring; public app hosting makes accidental exposure a real concern | Revisit when a second season makes manual sync recurrent |

The recommendation can be revisited without reauthoring or resynthesizing.
An RSS enclosure can point to the staged content-addressed MP3, and a card can
package it, after those delivery layers exist.

## Build and listening acceptance

Before an episode is exported:

1. Validate the season inventory, metadata, word range, pause count, immediate
   routed answers, recap, and maximum physical-line length.
2. Assert that every cited repository path exists and every external citation
   resolves, then manually check all numerical claims and verbatim learner
   quotations against their cited evidence.
3. Assert that `lang: x` has no bare `TL:` lines and that all other routing
   tags are supported. Synthesized text must contain neither `TL:` nor an ISO
   tag.
4. Confirm every constituent is nonempty and has no silence sidecar; stitch,
   normalize, and `ffprobe` the result.
5. Listen to the opening, every target-language voice boundary, every
   pause-to-answer transition, and the complete recap. Cross-language
   episodes require special attention to short cognates, where accent drift
   is easiest to miss.
6. Rebuild once without changes and require identical constituent and final
   hashes. Change one fixture paragraph and require reuse of every unaffected
   clip plus a new final hash.
7. Copy the ten friendly filenames to a disposable phone/player, check track
   order, seeking, screen-locked playback, pause/resume, and metadata display.

## Season 2 candidates from the error profiles

These are ranked by personal evidence and by how much coherent system-level
explanation remains after Season 1:

| Priority | Language | Working episode | Evidence spine |
|---:|---|---|---|
| 1 | pt | **Ser, estar, ficar: state versus change** | 24 selection rows across all captured years; later remediation still includes `estou contente` and `ficar pronto` |
| 2 | it | **Ci and ne: the little words inside big verbs** | A 74-row teacher remedial block on `farcela`, `cavarsela`, `sentirsela`, `prendersela`, `fregarsene`, and related procomplementari |
| 3 | fr | **Y and en: pronouns as compressed prepositions** | At least 27 direct y/en problems, including 22 `là`-for-`y` cases, plus later teaching recurrence |
| 4 | de | **The passive as a change of camera** | Roughly 35 teacher-supplied passives from 2019–2024 with no recorded spontaneous passive production; present this honestly as avoidance evidence |
| 5 | pt | **Agreement radiates from the noun** | 193 gender rows, plus adjective, possessive, and numeral agreement; the documented `-ma`, `-agem`, `dois/duas`, and `uns/umas` fossils |
| 6 | fr | **Counting time versus living through it** | About 102 `an/année`-family rows, including decade, day, morning, and evening contrasts |
| 7 | es | **Clitic choreography: why le plus lo becomes se lo** | A verbatim year-four `comprar le lo` error and a teacher-supplied mini-paradigm |
| 8 | pt | **Clitic forms without a spelling ambush** | At least 18 clitic and pronoun rows plus later notes, including `procurá-los`, `comigo`, `conosco`, and the orthographic changes before `-lo` |
| 9 | it | **Passato remoto without the wall of endings** | The learner explicitly reports avoiding it because of complexity; frame the episode as recognition plus high-value production, not corpus-proven error frequency |
| 10 | fr | **Sentence traffic: adverbs, negation, and numbered time** | Roughly 130 word-order rows, 60 negation rows, and the near-categorical numeral-before-`dernier` pattern |
| 11 | es | **The preterite forms that change identity** | Recorded `pune`, `quisemos`, `investieron`, and `me fue`, plus repeated stem-focused teaching |
| 12 | cross | **Prepositions at the Romance borders** | Attested regime transfer in every Romance profile: Portuguese zero bridges, Italian `cercare di`, French `chercher à`, and Spanish motion `a` |

Season 2 should again select ten, not automatically take the first ten. A
later deep dive on German passive modal stacks can extend Priority 4 if new
production evidence justifies it. Other alternates are French gendered
agreement and `-al` to `-aux`, or German genitive avoidance after newer error
evidence is captured.
