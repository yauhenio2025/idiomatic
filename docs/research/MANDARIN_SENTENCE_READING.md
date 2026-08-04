# Mandarin sentence reading — porting the idiomatic method stack to the Memory Palace

> Deliverable 1 of `docs/commissions/MANDARIN_SENTENCE_READING_COMMISSION.md`
> (2026-08-04). Phase-0 asset audit → design space → ranked proposals →
> pilot spec. **Stopped for user approval before any pilot build.**
> All audit steps were read-only; every number below was computed, not guessed.

## 0. Executive summary

The two systems fit together better than the commission dared assume:

- **99.8% of the 5,138 course sentences are fully decodable with the
  3,050 composed character films** (5,126 sentences have every hanzi
  filmed). The palace covers the sentence corpus almost perfectly,
  because both come from the same course.
- **1,882 sentences sit in the i+1 sweet spot**: every character filmed
  AND exactly one unknown word against the user's evidence-based known
  set (LingQ zh mirror + curated palace words). 885 of them are
  pilot-ready *today* (real translation + pinyin + working audio);
  the rest need repairable data cleanup.
- **Native course audio still works**: ~99% of sentences carry two
  Mandarin Blueprint MP3 URLs (male/female takes) on Google Cloud
  Storage, verified live 2026-08-04.
- **Mnemonic continuity is free**: a 480 px frame from a character's
  composed film is ~11 KB (verified with ffmpeg). A sentence card can
  visually quote the frontier word's film scenes for $0 and ~30-60 KB
  per card — no new image generation, no dependency on the parked
  word-comic scale decision.
- The idiomatic stack ports with **three small code changes** (add `zh`
  to the podcast-cards lang gate, one zh voice entry, one local-image
  attach mode); the frozen `Idiomatic Podcast Lesson v1` model is
  language-agnostic and needs no schema change.

**Top proposal (P1)**: "Sentence-Walk" podcast-card lessons — the
approved multi-side card-lesson format, where each card teaches one
sweet-spot sentence: segmentation-chunked reading front, mnemonic
film-quote + echo-practice back. Pilot = one 5-card episode covering
~10 sentences. Full spec in §6.

---

## 1. Phase-0 asset audit — Mandarin Memory Palace

Sources: local Postgres `mandarin_memory_palace` (localhost mirror),
prod API `mandarin-memory-palace.onrender.com`, the original scrape DB
`~/projects/chinese-words/mandarin_scrape.db`, `data/` JSON stores in
`~/projects/mandarin-videos`. (Note: the `mandarin_scrape.db` in the
mandarin-videos repo root is a 0-byte stub; the real one lives in
`~/projects/chinese-words/`.)

### 1.1 Sentences (the asset this commission is about)

| Metric | Value |
|---|---|
| Sentences in DB (local = prod, verified both) | **5,138** |
| Provenance | Mandarin Blueprint course, scraped via Traverse (3,264 zh + 1,937 EN-side items in the scrape DB) |
| Linked characters (`characters[]` per sentence) | **1,491 distinct** chars; median 4 sentences per char; 3,933 sentences linked to >1 char |
| Length | avg 18 hanzi; clean-set p25/p50/p75 = 12/15/18 |
| Levels | 0–88 (course level structure; bulk at L13–60) |
| With remote audio (`audioUrl1`) | **5,103 (99.3%)** — GCS-hosted MP3s, usually 2 per sentence (male + female takes, `-女` suffix); HTTP 200 verified 2026-08-04 |
| With pinyin | 3,747 (72.9%) — **1,391 missing** |
| English field | **1,301 (25.3%) are `"Level N - …"` placeholders**, not translations; ~24 more carry the word's gloss instead of a sentence translation |
| `vocabulary` field | 3,521 filled but messy (glosses interleaved with stray example sentences) — treat as unreliable |
| Dialogues (A:/B: multi-turn) | 69 |

**Data-quality verdict**: the corpus is rich but one-quarter of the
English fields need repair before those sentences can ship on cards.
Pinyin can be generated (pypinyin) and spot-checked; translations can
be LLM-generated behind the standard verification discipline. The
885-sentence clean subset needs no repair at all.

### 1.2 Characters, films, words

| Asset | Count | Notes |
|---|---|---|
| Composed character films | **3,050 / 3,050** (production DONE) | per char: intro frame + HMM video + tail frame; 1.2–2.9 MB each, 9.5 GB local in `data/composed-videos/`; also on prod's persistent disk |
| Scenes (actor/location/tone-zone/prop mappings) | 3,020 rows local; every film's scene carries actor, location ending, zone/tone, prop components | the deterministic mnemonic layer |
| Actors / locations / props | 55 / 13 (65 tone-zones) / 594 | actor portraits curated (`data/actor-portraits.json`) |
| Curated words (`words` table / `source == 'word'`) | **661** | studied word set with lesson/level/phase |
| Word bank | **19,975** attested words (`data/word-bank.json`): 8,974 HSK 3.0 core + 11,001 extended | built 2026-08-03; used here as the segmentation lexicon |
| Word films (legacy per-director system) | **dormant** — prod `has_films: false` across the board; status endpoint reads an empty local cache | do not build on it |
| Word comics (5-panel pages) | pilot-validated (r1–r3 + Seedream/Qwen benches) but **scale run PARKED** awaiting the user's engine/spend pick | sentence work must not depend on it |
| Per-char pronunciation MP3s | 3,025 local (`~/projects/chinese-words/audio/`) | usable for character-level audio |

### 1.3 What does NOT exist

- No sentence-level videos, images, or mnemonics of any kind.
- No word→sentence join table: sentences link to *characters* (the
  lesson they were scraped under), not to the words they contain.
  Word-level linkage must be computed by segmentation (done in §3).
- No local copy of prod render state beyond the composed films
  (local DB shows 7 `videoData` rows vs 3,050 films on prod — the
  local Postgres is a data mirror, not a render mirror).

---

## 2. Phase-0 asset audit — idiomatic toolkit

Full details verified in-repo 2026-08-04 (file:line cites available in
the session log; key facts only here).

### 2.1 Podcast-card machinery (the approved lesson format)

- Frozen model `Idiomatic Podcast Lesson v1` (1_820_140_001), 14 fields
  incl. 4 spares, GUID = `sha1("idiomatic-podcast-lesson::{lang}::{slug}::{seq}")[:16]`.
  The model is **language-agnostic** (Lang is data, not schema) —
  reusing it for zh is legitimate; it is the same content type.
- Markup: `[CARD]`/`[SIDE]`, mandatory `TITLE:` per side, `SVG:`/`IMG:`
  (exactly one per side), `SHOW:`, `TL:` (spoken+shown), `TL-:`
  (spoken-only), `[PAUSE:ms]`/`[THINK:ms]`/`[CHIME]`/`[MUSIC:intro|outro]`.
- Hard review rules (violations bounce): ~5 cards × 2 sides; spoken
  flip/next-card navigation cues; **no multi-word TL phrase ever in the
  EN narration voice**; fixed practice pattern EN prompt → SHOW →
  `[THINK:6000-8000]` → `TL-:` answer → `TL-:` echo → optional EN tip;
  per-clip −16 LUFS is automatic (never add normalization); mandatory
  visual verification of SVGs (build preview page, screenshot, look).
- Build: `POST /admin/podcast-cards-build?lang&episode` → one apkg per
  lang, kind `podcast_lesson`, delivered by the `idiomatic_puller`
  add-on.
- **Gates that block zh today**: `SUPPORTED_LANGS = {de,es,fr,it,pt}`
  in `podcast_cards.py:34` + the same guard in `api.py:766`.

### 2.2 zh TTS reality

- ElevenLabs (primary): `ELEVEN_LANG_VOICE` has **no zh entry** → falls
  back to Sarah (an English voice) while correctly sending
  `language_code="zh"` (zh IS in the accepted-codes set for
  turbo/flash v2.5). Adding a proper zh voice is a one-line change +
  listening check.
- Gemini TTS (fallback): **zh voice already configured** ("Achernar",
  `pipeline/audio.py:51`), unverified by ear.
- The pilot should include a 3-clip voice bake-off (ElevenLabs zh
  candidate vs Gemini Achernar vs native course MP3) before committing.

### 2.3 SVG sidecars

Authored per side (`svg/{lang}_{slug}_c{N}{f|b}.svg`), inlined into the
field; palette lives once in model CSS (`s-ink/s-muted/s-teal/s-coral/
s-sun/s-dead/s-tile` + stroke variants) with explicit
`.night_mode/.nightMode` overrides; viewBox width 840; simple
primitives; the diagram must carry the lesson. Builder rejects scripts/
event handlers and caps 200k chars. **Constraint that matters here:**
authored SVG cannot do actor likeness — the mnemonic quote must come
from film pixels, not vector art (§4.2).

### 2.4 Known-vocabulary evidence (LingQ zh mirror)

`lingq_terms` (idiomatic prod DB, cron-synced, zh included):
**3,168 zh terms**. Status distribution: 2,955 at status 0
(encountered/lookup), 119 at status 1–2 (learning), 94 at status 3
(learned/known). LingQ terms arrive pre-segmented (space-separated
tokens) → 2,977 distinct hanzi tokens after cleanup. There is **no
local zh export** — terms were pulled read-only from the DB for this
analysis. Personal term data stays out of this repo; only aggregates
appear here.

**Honest caveat**: the LingQ statuses are a weak "known" signal for
Mandarin (94 learned terms). The palace itself is the strong signal:
3,050 studied characters + 661 curated words. The i+1 computation
therefore uses layered known-set definitions (§3).

### 2.5 Renderer + delivery constraints (AnkiDroid/iPad research)

- iPad = AnkiMobile = **no AnkiDroid JS API**; interactivity must be
  pure HTML/CSS (the planned chunk-reveal is CSS-only — fine).
- `.night_mode` string must appear in card CSS or AnkiDroid inverts
  heuristically (podcast-card CSS already handles this).
- Audio: bundled `[sound:]` MP3s, content-hash filenames (media sync
  is by filename); front audio must be repeated explicitly to replay
  on the back.
- Model freeze discipline: never touch field count/order of a shipped
  model; spares exist.
- Delivery: `idiomatic_puller` imports into **whichever profile is
  open**. Mandarin palace decks live in **`evgeny@the-syllabus.com`**
  (verified read-only: `Mandarin Palace`, `Mandarin Actors`, … plus all
  Idiomatic Grammar decks). The agent row must gain `zh` in
  `agents.langs` or `/apkgs/pending` will never offer the deck.

---

## 3. The i+1 computation (the load-bearing feasibility result)

Method: extract hanzi from each sentence → greedy longest-match
segmentation against a 21,109-entry lexicon (word bank ∪ curated words
∪ LingQ tokens) → grade each sentence's segments against layered known
sets. Single-char segments count as known iff the character has a film.
Script + full row dump preserved in the session scratchpad;
reproducible from the DBs.

**Known-set definitions:**
- `K_studied` = 661 curated words + LingQ status ≥1 tokens (807 words)
- `K_enc` = K_studied + all LingQ-encountered tokens (3,383 words)
- Char level = the 3,050 filmed characters

**Results (N = 5,138):**

| Metric | Count | % |
|---|---|---|
| Every character filmed | **5,126** | 99.8% |
| Exactly one unfilmed char | 11 | 0.2% |
| i+0 vs K_enc (every word encountered) | 1,286 | 25.0% |
| **i+1 vs K_enc (exactly one unknown word)** | **1,883** | 36.6% |
| i+1 vs K_studied (strict) | 1,286 | 25.0% |
| **Sweet spot: all chars filmed AND i+1 (K_enc)** | **1,882** | 36.6% |
| … of which with working audio | 1,871 | 99.4% |
| … frontier word in HSK-3.0 core | 1,427 | 75.8% |
| … distinct frontier words | 1,249 | — |
| **Clean sweet spot (real EN + pinyin + audio, no repair needed)** | **885** | 664 distinct frontier words |

Reading of the numbers:

1. **The i+1 pipeline is real, computed, and deep.** Even the strictest
   definition yields 1,286 candidate sentences; the practical pool is
   1,882, of which 885 need zero data repair. A pilot needs ~10.
2. **Every frontier word is multi-char and (in 76% of cases) an HSK
   core word whose characters all have films** — the mnemonic-quote
   design (§4.2) applies to essentially every card.
3. **Sequencing writes itself**: one card per frontier word; 111
   frontier words have ≥3 sweet-spot sentences (primary + production
   probe + spare). After each lesson the frontier words move into the
   known set and the pool re-ranks — the same evidence-driven loop the
   grammar system uses.
4. The 1,286-sentence i+0 "free pool" is a bonus asset: pure fluency /
   speed-reading material with zero new vocabulary, usable for a
   listening-cluster variant later.

---

## 4. Design space explored

### 4.1 Comprehensibility-graded sequencing (commission direction 1)

**Verdict: adopt as the backbone of everything, not a standalone
format.** Computed above. Two honest limitations: (a) LingQ status 0
means *encountered once*, not known — "i+1" vs K_enc is really "one
never-seen word, everything else at least met"; the pilot should ask
the user whether that matches felt difficulty; (b) segmentation is
greedy longest-match, which occasionally over-merges — acceptable for
ranking, but pilot sentences get a manual segmentation check (10
sentences, minutes of work).

### 4.2 Mnemonic continuity (direction 2)

The commission imagined SVG panels echoing the word film's
iconography. The audit says: better raw material exists. **The
composed films themselves are the canonical mnemonic pixels** (the
comic-pilot r3 ruling — "settings from film pixels, never DB text" —
points the same way). A 480 px JPEG frame is ~11 KB (measured);
a frontier word = 2–3 chars = 2–3 frames side by side ≈ 30 KB.

Design: the back side of each card carries a **film-quote strip** —
one frame per character of the frontier word, captioned with the
actor/zone/prop line from the scene DB (e.g. 「取」 = actor X, zone Y,
prop Z), so word recall chains: sentence → frontier word → per-char
film scenes the user already knows. Authored SVG stays for what SVG is
good at (segmentation diagram, tone marking); raster frames carry
likeness. Cost $0, no dependency on the parked comic-scale decision,
no IP/filter surface (the frames already passed the engines' filters
when rendered).

Builder impact: podcast-cards needs a *local-file image attach* mode
(today `IMG:` means "generate"). Small, clean extension; fallback
exists (embed the strip as a data URI inside an SVG wrapper under the
200k cap) but the clean extension is preferred.

### 4.3 Comic-strip sentence lessons (direction 3)

Full 3-4 panel generated comics per sentence — evaluated and
**deferred (P3)**. Reasons: (a) the word-comic scale decision is itself
parked; sentence comics would compound an unapproved dependency;
(b) $0.06–0.24/sentence × 1,900 ≈ $115–450 + retake overhead, vs $0
for film-quote strips that serve the same mnemonic-continuity goal;
(c) sentence-level *scene* imagery adds narrative charm but the
reading skill being trained is segmentation + word recognition, which
the film-quote design serves more directly. Revisit after the comic
scale run lands and if the pilot shows the cards feel visually flat.

### 4.4 Segmentation + tone visuals (direction 4)

**Adopt — this is the heart of the front side.** Word boundaries are
THE Mandarin reading skill, and none of the palace's existing formats
train it. Design (all iPad-safe, no JS):

- Front shows the sentence **unsegmented** (real reading conditions),
  set large (clamp ~34-40 px, CJK-safe line breaking).
- The reveal moves to the back: same sentence **chunked** — word
  boundaries as subtle boxes/underlines, tone contour marked per
  syllable using the palace's tone-zone convention (tone number →
  the same 5-zone semantics the user's location zones encode; colors
  from the podcast-card palette: e.g. T1 `s-sun`, T2 `s-teal`, T3
  `s-ink`, T4 `s-coral`, T5 `s-muted` — final mapping is a user taste
  call, one of the pilot's review questions).
- Frontier word highlighted (`s-coral` fill, white text — existing
  convention for emphasis).
- Pinyin appears only on the back, as ruby over the chunked version.
- Implementation: authored SVG per side (840-wide, existing palette
  classes, night-mode already handled by the model CSS). For ~15-char
  sentences this is comfortably within the SVG conventions already
  approved for grammar cards. HTML/CSS chunking inside the field is
  the fallback if per-sentence SVGs prove tedious to author — but SVG
  keeps typography deterministic across platforms.

### 4.5 Audio echo-reading (direction 5)

**Adopt, hybrid sourcing.** The renderer already does everything
needed: `[THINK:ms]` piano gaps, per-clip −16 LUFS, content-addressed
cache. Flow per card (matches the approved fixed practice pattern):

- Front: EN anchor (spoken) → cue "read it aloud" → `[THINK:6000]` →
  zh sentence audio → flip cue. (Hear the answer only after attempting
  the read — the sentence-final recall probe the commission asked for.)
- Back: zh sentence again (slow echo), frontier word isolated
  (`TL-:` echo), EN tip, production probe: EN prompt → `[THINK:8000]`
  → `TL-:` answer → echo.
- Sourcing: TTS for everything the renderer speaks (needs the zh voice
  decision, §2.2); the **native course MP3s are a bonus asset** — two
  takes (male/female) per sentence, downloadable once and stitchable
  if the builder gains an `[AUDIO:file]` token. Not pilot-blocking:
  pilot ships on TTS, with one card A/B'd against native audio so the
  user can rule on whether the `[AUDIO:]` extension is worth it.

### 4.6 Video composition (direction 6)

**Rejected for cards; films appear as frames only.** Numbers: films
average ~2 MB per character; one 15-char sentence's films ≈ 25–30 MB;
a 10-card lesson ≈ 250 MB into a synced Anki collection — unacceptable,
and AnkiMobile offers no filesystem link-out. Sequencing films into a
per-sentence montage (ffmpeg concat, ~$0) is technically trivial but
produces a 1-2 minute video per sentence — a review-dashboard artifact,
not a card asset; it also trains character recall, not sentence
reading. Generating new sentence-level video (MiniMax et al.) costs
real money (~3¥/6s) for unproven pedagogy. If sentence-scene video is
ever wanted, it should be a handful of showcase pieces, not a format.

---

## 5. Ranked proposals

### P1 — "Sentence-Walk" podcast-card lessons ★ recommended

One episode = one lesson in the approved podcast-card format
(5 cards × 2 sides), each card teaching **one sweet-spot sentence**
whose frontier word is new, everything else known/encountered.

| Aspect | Detail |
|---|---|
| Front | TITLE + authored SVG: unsegmented sentence, large type; spoken EN anchor sets the scene (no TL through EN voice); "read aloud" cue → `[THINK:6000]` → `TL-:` sentence audio → flip cue |
| Back | TITLE + chunked/tone-marked SVG with pinyin ruby + **film-quote strip** (per-char frames of the frontier word, actor/zone/prop caption) + translation `SHOW:`; spoken: slow echo, frontier-word isolation, one EN tip, production probe (fixed pattern), next-card cue |
| Borrows | podcast-card model/markup/review rules verbatim; `[THINK]`/LUFS/clip-cache renderer; SVG palette + night mode; i+1 grading (LingQ + palace evidence); film frames as mnemonic quotes |
| Data requirements | 885-sentence clean pool (no repair); scene DB for captions; ffmpeg frame pulls; zh voice decision |
| Code changes | (1) `zh` in `SUPPORTED_LANGS` + api guard; (2) one `ELEVEN_LANG_VOICE["zh"]` entry (or route zh to Gemini); (3) local-image attach for the film strip; (4) deck-root decision (see §7) |
| Build cost | pilot ≈ authoring one episode file + ~10 SVGs + frame pulls; TTS pennies; images $0 |
| Risks | zh TTS quality unheard (bake-off in pilot); segmentation edge cases (manual check, 10 sentences); "encountered ≠ known" calibration (user verdict) |

Why first: it delivers the full idiomatic stack — approved format,
audio-first echo reading, evidence-graded sequencing, and mnemonic
continuity — at near-zero marginal cost, and it is the only proposal
that *teaches* (narrated walk) rather than just drills.

### P2 — Segmentation drill cards (the volume complement)

A new frozen model (`Mandarin Sentence Reading v1`, spare fields
reserved) for **programmatically generated** one-card-per-sentence
drills: front = bare sentence + native audio on demand; back = chunked
tone-colored rendering, pinyin, translation, frontier-word film strip.
No narration layer — so no authoring bottleneck, and the 885→1,882
pool can flow at volume (small approved batches per the volume rule,
e.g. 20/batch). Cost ≈ TTS-free (native MP3s) + $0 images. This is
the scalable engine P1's lessons sit on top of; it can also consume
the i+0 free pool as a speed-reading deck. Build after P1's format
verdicts (tone colors, chunk styling, strip layout) are locked, so
the drill cards inherit approved visual decisions.

### P3 — Sentence comics (deferred)

Generated 3-4 panel comics per sentence quoting word-comic
iconography. Deferred: depends on the parked word-comic scale pick,
costs real money per sentence, and its pedagogical delta over the
film-quote strip is unproven. Reconsider after the comic scale run
ships and P1/P2 verdicts are in.

---

## 6. Pilot spec (P1, ONE lesson — pending approval)

**Scope**: one episode, `zh_sentence-walk-01`, 5 cards × 2 sides,
**10 sentences touched** (5 primary + 5 production-probe), all drawn
from the 885-sentence clean pool, frontier words chosen from the 111
words with ≥3 sweet-spot sentences (primary + probe share the frontier
word → the probe reinforces the card's one new item, honoring
one-frontier-element-per-card).

**Selection**: level band L37–45 (the sweet-spot density peak, 150+
sentences at L37 alone), frontier words in HSK core, manual
segmentation check on all 10.

**Assets per card**: 2 authored SVGs (front unsegmented / back chunked
+ ruby); 1 film-quote strip (2-3 frames, ffmpeg, 480 px, captioned);
TTS clips via the renderer; native-audio A/B on exactly one card.

**Code, minimal**: the three changes in P1's table, done in idiomatic
with tests mirroring the existing podcast-cards tests; no model
changes; deck root decision from §7 applied.

**Verification before the user sees it**: markup validator passes;
SVG preview page screenshotted and eyeballed; full episode audio
listened to end-to-end; apkg imported into a scratch profile first;
zero unverified claims.

**Delivery**: apkg kind `podcast_lesson`, lang `zh`; requires `zh`
added to the agent's langs; import with `evgeny@the-syllabus.com` open.

**Explicit user verdict points**: zh voice pick (bake-off clips) ·
tone-color mapping · "encountered = known enough?" calibration ·
native-audio `[AUDIO:]` extension worth it? · deck root name.

## 7. Open decisions for the user (blocking the pilot)

1. **Approve P1 pilot as specced?** (Or reorder P1/P2.)
2. **Deck root**: `Idiomatic Grammar ZH::0 …` (machinery default,
   wrong branding) vs a new `Mandarin Palace::Sentences::…` root
   (needs a small deck-naming case for zh). Recommendation: the
   latter.
3. **zh TTS**: pick from bake-off clips (delivered with the pilot's
   first review round, before full episode synthesis).
4. Anything in the known-set layering that contradicts felt reality
   (e.g. should status-0 LingQ terms count as "met"?).

---

*Verification log: all counts SQL/script-computed 2026-08-04 against
local Postgres, prod API (basic-auth, read-only), idiomatic prod DB
(read-only MCP), and the file system; GCS audio HEAD-checked; frame
extraction measured. No writes to any Mandarin store. No personal
LingQ term contents appear in this document (aggregates only).*
