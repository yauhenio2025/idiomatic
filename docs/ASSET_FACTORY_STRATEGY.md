# The Asset Factory — strategy for reusable comic/video assets

> Deliverable of `docs/commissions/ASSET_FACTORY_COMMISSION.md`.
> Investigation session 2026-08-05 (evening). Status: **awaiting user review — nothing here is committed to.**
> Inputs read: both repos (`idiomatic`, `~/projects/mandarin-videos` incl. a live query
> of its Postgres), `~/llms/qwen-image/LOCAL_QWEN_IMAGE.md`, the three artifacts
> (Comic Pipeline worked examples, Nano-Banana-vs-Qwen head-to-head, Idiom Rescue
> Pilot №1 incl. Round 2), and the **live idiomatic production DB** (read-only,
> via Render MCP). Every number below is either a live query result, a repo
> file:line, or a measured figure from tonight's artifacts. Speculation is
> tagged `SPECULATION`.

## 0. Prior-knowledge verification (commission §Prior-knowledge)

| Claim | Verdict |
|---|---|
| Validated recipe (t2i settings → Edit-2511 insertion w/ sheet as image2 → typeset bubbles → code stitch) | **Confirmed.** Ledger in the worked-examples artifact: 17 jobs, ~13 min GPU for 3 strips → ~4.5 min/strip, $0; insertion 5/7 first pass, 7/7 after one firmer retry (~40 s); busy scenes dilute refs (ES beat-3 man vanished); firmer prompts drop backgrounds (PT jar panel). |
| Ops constraints (laptop-only 127.0.0.1:8199, serial ~1/min, RAM scarce, 3 OOMs, swapfile outstanding) | **Confirmed.** `LOCAL_QWEN_IMAGE.md` + artifact footer ("laptop-only pipeline — Render's autopilot can't reach it"). Third OOM happened during the 2-ref edit batch. |
| SVG diagrams are LLM-authored code, not image-model output | **Confirmed.** The pilot artifact contains the literal inline `<svg>` markup (e.g. the *se desbloquee* diagram: timeline + morphology strip + rule line, hand-tuned hex palette). Strategy below specifies templates + verification, no diffusion. |
| Rescue has snapshots, strikes, format registry, $-budgeted autopilot, approval gates, drafts pending | **Confirmed and sharpened.** Live DB right now: **266 items (27 active / 239 candidates), 23 draft assets, 0 approved, $1.2156 spent** (moved on from STATE_OF_PLAY's 21/7/$0.2556 — the autopilot ran again today). Critical additions the factory must fix: the strike ladder exists **only in docs** (no code path changes `strike` except activation); `struggle_snapshot` is **overwritten** on every ingest, so "sustained non-improvement" is *currently unmeasurable*; there is **no delivered state** for assets; `rescue_assets` **bans `video` at the DB CHECK level** (`db/schema.sql:447-448`); and rescue items have **no join to the corpus** — only 73/266 exact-match an `expressions` row by `(lang, lower(text))` (live query). |

---

## 1. Social-situation taxonomy — mined from the corpus

### 1.1 What was mined

Live production DB (read-only): `expressions` (2,764 rows: de 601, es 440,
fr 431, it 785, pt 507), `expression_idioms` (2,759 occurrences; 2,523 with
`structured` JSONB), `expression_examples` (16,548 sentences), plus
`expression_idioms.source_phrase_en` (the sentence each idiom was actually
spoken in on YouTube), the `channels` roster, and the Exercises 2.0 sentence
files (`idiomatic/grammar/data/exercises2/it_rebuild/input/*.json`, 2,589
items). Method: regex bucket classifier over English glosses run server-side
(multi-label per sentence; per-expression clustering; residual sampling to
catch missed buckets).

### 1.2 The headline finding: the corpus lives in TWO registers

**Register A — everyday life** (the 16,548 generated example sentences).
Work/office dominates every language; then commerce, home/family, travel,
school, sports, media/tech. Per-language share of sentences touching each
context (multi-label, so rows overlap):

| context | de | es | fr | it | pt |
|---|---|---|---|---|---|
| work / office / project | 16.8% | 17.0% | 16.8% | 15.2% | 18.0% |
| money / commerce | 5.8% | 6.7% | 6.4% | 6.1% | 7.8% |
| home / family | 5.2% | 6.7% | 5.4% | 5.8% | 6.8% |
| media / tech / culture | 5.0% | 4.8% | 6.4% | 6.3% | 6.2% |
| travel / transport | 5.0% | 6.7% | 4.4% | 5.1% | 5.5% |
| school / study | 4.6% | 6.3% | 4.6% | 5.5% | 4.9% |
| politics / government | 5.2% | 3.9% | 4.6% | 2.6% | 2.9% |
| sports / fitness | 4.9% | 4.9% | 4.5% | 2.6% | 3.4% |
| nature / weather | 4.2% | 6.3% | 3.2% | 3.7% | 3.3% |
| friends / social events | 4.1% | 4.6% | 3.4% | 3.9% | 6.0% |
| justice / crime | 2.1% | 1.5% | **3.7%** | 1.5% | 1.4% |
| **no located context** | 44% | 40% | 46% | 49% | 42% |

Language skews worth honoring in the settings library: **de** leans
politics+sports+workplace-formality; **fr** has a justice/courts streak (2.5×
the es rate); **pt** leans social/family/media; **it** is the most
domestic/school-flavored; **es** the most nature/travel-flavored.

**Register B — the user's world** (three independent corpora agree):
- `source_phrase_en` (where idioms were actually heard): politics/geopolitics
  is the top located context in every language — de 18.0%, fr 16.7%, it 14.8%,
  es 12.5%, pt 9.4% — with economy/business second and, for pt, a media/tech
  skew (7.2%, Meteoro Brasil / piauí effect). The channel roster is
  wall-to-wall news & geopolitics (tagesschau, Limes, Le Monde, BBC Brasil…).
- The Rescue pilot's approved personalized sentences are set in newsrooms,
  platform regulation, Silicon Valley, press embargoes.
- Exercises 2.0 sentence topics are literally `big_tech`, `cold_war_vocab`,
  `geopolitics`, plus grammar waves whose example sentences are about arms
  races, neoliberalism, journalists, and peace treaties (verified samples).

**Consequence:** the settings library needs two wings. Everyday wing for the
6-example corpus (what most pool cards drill), world wing for rescue
personalized sentences, source-context panels, and Exercises 2.0 art.

### 1.3 Fine-grain scenes (all languages pooled, sentence hits)

company/project 1,585 · classroom/exam 569 · house/moving/repair 555 ·
family/children 509 · meeting/negotiation 497 · boss/hiring/interview 488 ·
nature/outdoors 477 · match/stadium 449 · phone/screen/online 410 ·
shop/market 385 · trip/airport/hotel 345 · politics/parliament 334 ·
office/colleagues 273 · street/city 272 · dinner-table/guests 233 ·
bank/savings 228 · café/restaurant 181 · kitchen 131 · doctor 119 ·
newsroom/press 111.

### 1.4 Two structural findings that shape the design

1. **Settings are assigned per-sentence, not per-expression.** Only ~15–19%
   of expressions have even 2 of their 6 examples in the same bucket (work is
   the only strong cluster: de 114/601, es 75/440, fr 80/431, it 136/785,
   pt 96/507). The rest scatter. So the factory's unit of scene-assignment is
   the *illustrated sentence/beat*, and the same expression will legitimately
   appear in different settings across its cards.
2. **40–49% of sentences are placeless** — abstract interpersonal statements
   ("He always manages to get what he wants, one way or another"). Sampled
   residuals confirm these are two-person conversation beats with no inherent
   location. They need *generic conversation stages* (café table, kitchen
   table, office desk, street walk), which is exactly what makes a small
   reusable settings library viable at all.

### 1.5 The settings list worth pre-generating (recommendation)

14 settings, 2 camera views each (the worked-examples pattern: e.g. café
table-view + door-view), t2i, **no people, no text** (both are added later —
people by insertion, text by typesetting; this is what makes them reusable and
risk-free). Evidence column = pooled sentence hits from §1.3.

**Everyday wing (10):**
| # | setting | views | evidence |
|---|---|---|---|
| 1 | open-plan office + meeting room corner | desk view, table view | 1,585+497+273 |
| 2 | boss's office / interview room | across-desk, door | 488 |
| 3 | family kitchen + dinner table | stove view, table view | 131+233+509 |
| 4 | living room / home misc | sofa view, doorway | 555 |
| 5 | café / bar (per-lang flavor, see below) | table, counter | 181 + placeless host |
| 6 | street / city square | sidewalk, crossing | 272 |
| 7 | shop / market | aisle, counter | 385 |
| 8 | classroom / exam hall | desk rows, blackboard | 569 |
| 9 | stadium terrace + five-a-side pitch | stands, pitch | 449 |
| 10 | station/airport + trail/outdoors | platform, trailhead | 345+477 |

**World wing (4):**
| # | setting | views | evidence |
|---|---|---|---|
| 11 | newsroom (desks, monitors, pinned frontpages) | desk, editor's corner | 111 + Register B |
| 12 | TV studio / press conference | podium, panel table | source corpus politics 398 hits pooled |
| 13 | parliament corridor / ministry office | corridor, office | 334 |
| 14 | "platform world" — glowing feed wall, server room, phone-screen macro | 2 stylized views | 410 + Exercises 2.0 big_tech |

Cost to build: 14 settings × 2 views × 5 language-flavors ≈ 140 t2i renders
≈ **80 min GPU, $0** — cheap enough that the real question is curation, not
compute. Per-language flavor is carried by *architecture and props only*
(azulejos in the PT café, Altbau moldings in the DE kitchen, the IT bar
counter) since settings contain no text by construction. A shared-neutral
alternative costs 28 renders; the pilot's strips already leaned
language-flavored (PT grandma kitchen, IT newsroom) and the user's per-language
cast instinct (commission §2) pulls the same way → **recommend per-language
flavored for the 5 "conversation host" settings (café, kitchen, office,
street, newsroom) and shared-neutral for the other 9**, ≈ 70 renders total.

---

## 2. Cast design

### 2.1 Size and composition (recommendation)

Evidence for role demand: the corpus's recurring humans are colleague/boss
(work 16–18% everywhere), partner/spouse, parent+child, grandparent
(pilot-validated: PT grandma is already a proven character), teacher/student,
shopkeeper/waiter, journalist, official/politician. The pilot cast (ES couple,
PT grandma+teen, IT journalist) held identity across beats — that's the
existence proof.

**Per-language core cast of 6** (roles, not names):
1. woman ~35 (the "protagonist" — partner / colleague / customer)
2. man ~35 (her counterpart — the pilot's ES couple generalized)
3. older woman ~70 (grandmother / neighbor — PT-proven archetype)
4. young adult ~19 (teen/student — phone-world native)
5. professional woman ~50 (boss / editor / anchor)
6. professional man ~45 (official / journalist / teacher)

Plus **2 cross-language recurring figures** shared by all five casts
(SPECULATION on which: recommend a "foreign correspondent" pair who can
plausibly appear in any country's setting — they give the learner continuity
when hopping languages, which is the user's "learner comes to *know* them"
goal applied across decks). Total: 5×6 + 2 = **32 actors**.

Demographic axes to vary across the five casts so the whole roster isn't
monochrome: age (19→70 covered per cast), gender (3/3 per cast), ethnicity
varied *between* language casts to match plausible local demographics plus
deliberate diversity within each (e.g. the FR cast's young adult
Franco-Maghrebi, the PT cast Afro-Brazilian grandmother — the corpus is
Brazil-heavy: BBC Brasil, CartaCapital, piauí). These are user-taste
decisions — the strategy only fixes the axes, the user approves faces (§8).

### 2.2 Naming

Fictional names only, never real people (mandarin-videos burns real-celebrity
likenesses and needs a whole REDACT/archetype machinery to survive engine
filters — `worker/batch_first10_words.py` `ACTOR_ARCHETYPES`, `REDACT_RE`;
idiomatic should simply not import that problem). Names appear **only in
typeset captions/bubbles**, never model-rendered, so they are letter-perfect
and free. Mandarin's placard lesson still transfers in spirit: a *stable
visual identity anchor* must exist even when a face drifts — for idiomatic
that anchor is the **fixed outfit** (below) plus the typeset name label when
a strip introduces a character.

### 2.3 Character-sheet spec

One sheet per actor, generated once, versioned, then **frozen** (like the
deck models): single 1024² image containing front bust + full-body + ¾ view
on a neutral light background, **one fixed outfit** with 2–3 signature
elements (the identity anchors: grandma's cardigan + glasses chain; editor's
rolled sleeves + lanyard). Optionally a second sheet per actor for a seasonal
outfit — but not in v1; every extra reference dilutes insertions (measured
tonight: busy scenes already dilute).

Storage: `factory_actors` row (schema §3) + sheet file; the sheet is the
`image2` reference for every insertion, always.

### 2.4 Identity-stability protocol (what tonight + mandarin-videos proved)

1. Sheet as `image2` on every Edit-2511 insertion; **one character per edit
   call** where possible; work **per-panel, never per-strip** (Edit-2511
   overshoots panel targeting — head-to-head artifact).
2. **Describe wardrobe, not body.** Mandarin's single most transferable trick
   (`hh_worker.py:509` `_wardrobe_only()`): when a reference image carries the
   face, prompt text must not re-describe the face or the text wins and
   recasts it. Insertion prompts say "the WOMAN from the reference image
   (copy face, hair, build exactly) now sits…" + wardrobe/pose only.
3. **Firmer-retry ladder** (measured 7/7 after one retry): pass 1 normal
   phrasing → pass 2 imperative + article-of-existence ("a MAN MUST now be
   sitting…") → pass 3 simplify the scene (fewer background elements) →
   park for human. Retries are ~40 s and free; 2 automatic retries max, then
   the panel goes to the review queue *with its best attempt attached*.
4. Busy scenes dilute: prefer settings views with clear insertion zones;
   the planner (§4) should cap 2 cast members per panel, 3 per strip.
5. Every strip's beat text is **linted for figurative language** before
   generation (mandarin lesson: "bullseye" in a beat drew a bull's head).
   Beats describe what is *visible*, in plain literal prose.

### 2.5 Signoff flow

Adapt mandarin's actor-signoff pattern (its best-engineered surface,
`app/actors/signoff/page.tsx` + `data/actor-signoff.json`):
- Signed-off identity facts (gender, age, distinctive features bullets) live
  **separately** from the generation prompt prose, so the user can approve an
  identity without wordsmithing prompts.
- Distinctive-feature bullets are consumed verbatim at prompt-build time
  (mandarin's TELLTALES mechanism) — they double as QA checklist items.
- Autosave never approves: approval is an explicit button; status is omitted
  from autosave payloads (mandarin does exactly this, deliberately).
- States: `candidate → approved → retired`; a sheet regeneration on an
  approved actor demotes to candidate and requires re-approval (mandarin's
  `componentsAtReview` staleness idea, applied to the sheet hash).
- Surface: a **Cast page inside the existing Rescue Lab** (`/rescue` is the
  sanctioned dashboard-mutation surface — CLAUDE.md).

---

## 3. Asset registry schema

### 3.1 Where it lives: **extend idiomatic Postgres** (recommended)

Justification:
- The registry's consumers are all server-side already: the dashboard
  (admin-token JSON under `/ui/api/*`), the rescue tables it must join
  (`rescue_items`, `rescue_assets`, `gen_ledger`), and the future APKG builder
  (runs on Render where `/data` is mounted). A local SQLite would need a
  sync protocol to serve any of them — that's the deprecated local-agent
  architecture idiomatic already abandoned once (CLAUDE.md: idiomatic_agent →
  add-on).
- The laptop is not a server; it's an intermittent worker. The proven pattern
  in this exact codebase is **pull-based clients**: the Anki add-on polls
  `/apkgs/pending`, downloads, acks. The factory runner is the same shape in
  reverse: poll `/admin/factory/jobs`, render, upload, ack. No inbound
  connectivity to the laptop is ever required, which is the hard constraint
  (127.0.0.1:8199 unreachable from Render).
- Schema migration is free here: api.py applies `db/schema.sql` idempotently
  at boot — that IS the migration mechanism.
- The laptop keeps a tiny local job cache (JSON file, not SQLite) only so an
  interrupted night can resume without re-asking the server; it is never
  authoritative.

### 3.2 Tables (sketch — final DDL is commission B's job)

```
factory_actors      id, lang (NULL = shared), role_key, name, sheet_path,
                    sheet_hash, prompt_desc, features JSONB (signoff bullets),
                    status candidate|approved|retired, approved_at, updated_at
factory_settings    id, key, wing everyday|world, lang (NULL = neutral),
                    name, prompt_desc, status, updated_at
factory_setting_views id, setting_id FK, view_key, file_path, status
factory_assets      id, expression_id FK→expressions (nullable ONLY for
                    rescue items that fail adoption, see §3.3),
                    rescue_item_id FK→rescue_items NULL,
                    kind panel|strip|glyph|diagram_svg|video,
                    sentence_ref JSONB ({example_id} | {rescue_sentence} |
                    {exercises2_id}), setting_view_id FK NULL,
                    actor_ids BIGINT[], beats JSONB, file_path, mime,
                    engine, cost_usd, status draft|approved|rejected,
                    delivered_at TIMESTAMPTZ,     -- the ladder's missing clock
                    verdict_note, created_at
factory_jobs        id, kind t2i|edit|stitch|qa|svg|video, payload JSONB,
                    status queued|leased|done|failed,
                    leased_by, lease_expires_at,  -- the lease rescue lacks
                    attempts, last_error, created_at, finished_at
struggle_history    id, rescue_item_id FK, snapshot JSONB, captured_at
                    -- append-only; autopilot writes here IN ADDITION to the
                    -- existing overwrite, making non-improvement measurable
```

Design rules baked in, each fixing a verified defect:
- `factory_jobs` has a **real lease** (atomic `UPDATE … WHERE status='queued'
  … RETURNING`, expiry reaper) — rescue's read-then-write timestamp is the #1
  defect in STATE_OF_PLAY.
- `factory_assets.delivered_at` + `struggle_history` make "still failing 7+
  days after delivery" computable for the first time (§5).
- `expression_id` FK closes the rescue↔corpus gap. **Adoption backfill**: only
  73/266 rescue items exact-match `expressions.text` today; commission B
  includes a normalized/fuzzy matcher (strip articles, lowercase, unaccent,
  then trigram) with a manual-confirm queue for the tail.
- Spend rows continue to go to the existing `gen_ledger` (single money truth);
  factory adds `unit_kind` values as needed rather than a parallel ledger.

### 3.3 Files, naming, storage tiers

- **Laptop (creation tier)**: originals + intermediates stay in
  `/srv/ai-models/outputs/` under `factory/<lang>/<expression_id>/…`
  (1.33 TiB partition — the space is there). Names:
  `set_<setting>_<view>.png`, `sheet_<actor>.png`,
  `strip_<expressionid>_<sentencehash>_v<N>.jpg`.
- **Server (delivery tier)**: only *approved, deck-bound* finals are uploaded
  to `/data/factory_assets/<expression_id>/…`. Budget note: `/data` is 10 GB
  and has filled once (2026-07-27 ENOSPC incident). Final strips at ~300–500 KB
  ×2,764 expressions ≈ 1.4 GB worst case — fits, but the janitor must learn to
  reap superseded versions, and originals never ship.
- **R2 (archive tier, optional)**: the bucket already exists for audio;
  park superseded/rejected generations there if the user wants full history
  off-laptop. Not required for v1.
- **Upload path**: `POST /admin/factory/upload` (multipart: file + JSON
  metadata), admin-token auth — the exact pattern of the existing
  `/admin/personal-errors-upload` and `/admin/f4-pairs-upload`
  (`idiomatic/api.py:662,700`) and of the proposed-but-unbuilt rescue
  `asset-upload` (RESCUE_LAB_HANDOFF open item — this supersedes it and also
  finally gives `svg`/`sentence_audio` rescue formats an ingest path).

---

## 4. The cycle engine

### 4.1 A night, end to end

```
[server, dusk]   PLAN    select items (order below) → for each unillustrated
                         sentence: assign bucket→setting view + cast (mined
                         tags §1, planner heuristics §1.4) → author beats
                         (codex/local LLM, linted §2.4.5) → enqueue
                         factory_jobs, batched BY MODEL: all t2i, then all
                         edits, then stitch/QA
[laptop, night]  RENDER  runner leases jobs → t2i batch → /free → edit batch
                         (per-panel, retry ladder) → /free → typeset+stitch
                         (PIL, deterministic) → auto-QA → upload drafts →
                         ack jobs
[server, night]  QA      auto-gates on upload (below); failures re-queue or
                         park with reason
[user, morning]  REVIEW  Rescue-Lab factory queue: approve / reject-with-note
                         (existing verdict UX, no auto-approve — unchanged
                         hard rule)
```

### 4.2 Item selection order (per commission)

1. Rescue `active` items, by `fails_14d` desc (27 today).
2. Rescue `candidate` items above the strike threshold (239 today).
3. Newest shipped expressions without assets (`expressions.added_at` desc) —
   matching the pipeline's newest-first claim philosophy.
Within an item: the failed sentence first (it's the scene_hint rescue already
uses), then examples 1–3. Illustrating all 6 examples is not planned — 2–3
strips per item is the ceiling before novelty beats reuse (SPECULATION:
the right per-item depth is a review-data question; start at 1 strip + glyph
and let strikes pull more).

### 4.3 Beat authoring at scale — the actual bottleneck

Mandarin-videos' comic pilot concluded generation was never the bottleneck;
**authoring the per-item fusion beat was** (`docs/analysis/COMIC_PILOT_RESULTS.md`).
Same here: 4.5 min GPU per strip is nothing; 3 good literal beats × thousands
of items is the cost. Plan: beats are authored by **codex/local text LLM**
(standing delegation directive) from a template contract per strip archetype
(three-beat arc: setup → the idiom SAID in the bubble → consequence), with
hard lint gates borrowed from mandarin's measured failures: literal language
only, describe-what's-visible, ≤2 cast per panel, the idiom's typeset text is
NEVER in the beat prompt (nothing for the model to garble), exactly one comic
device allowed. Premium-model review only samples (tranche culture).

### 4.4 Automated QA gates (what CAN be auto-checked)

Auto (cheap, code):
- file exists, size > 50 KB, decodes, expected dimensions;
- panel count and stitch geometry correct (we stitched it — deterministic);
- bubble text == intended string (we typeset it — true by construction; the
  check is that typesetting ran and fit: no overflow, tail anchored);
- palette/brightness sanity (catches all-black VAE failures);
- perceptual-hash distance between panels (catches duplicate/unchanged panel
  after a failed edit — tonight's "man vanished" class);
- OCR sweep over the pre-typeset panel: **any detected text = fail** (model
  leaked text into the artwork; the recipe demands none).
Auto (one cheap vision call, optional per-strip):
- mandarin's `props_visible_check` pattern (`hh_worker.py:966`): Gemini
  Flash, strict JSON schema `{cast_present: int, setting_matches: bool}`,
  temperature 0.1, **checker errors count as pass** (infrastructure never
  blocks the line).
Eyeball-only (Rescue's no-auto-approve rule, unchanged):
- likeness to the cast sheet, storytelling, tone, cultural fit. Nothing
  ships unapproved.

### 4.5 Retry policy

Per panel: 2 automatic retries (firmer ladder §2.4.3), then park with best
attempt. Per strip: parked panels don't block sibling strips. Per night: a
`--limit` tranche cap (mandarin's spend-gate idiom) so a systematic failure
can't burn the whole night; failure classes logged per job (`last_error`).
Terminal conditions (OOM-killed server ×3, disk full) stop the runner cleanly;
leases expire; next night resumes idempotently (job cache + `factory_jobs`
status are both idempotent by design).

### 4.6 OOM-safe scheduling

Preconditions and rules, all from today's measured incidents:
1. **16–32 GB swapfile first** — three OOM kills on 2026-08-05; this is the
   known durable fix and blocks unattended overnight runs (user go-ahead §8).
2. Batch by model; never interleave t2i↔edit (15–20 s swap + resident-set
   growth); `POST /free` between phases (both already validated practice).
3. RAM guard: runner checks `MemAvailable` before each batch; below threshold
   → `/free`, re-check, else sleep+alert.
4. Watchdog: if 127.0.0.1:8199 stops answering, assume OOM-kill, rerun
   `start_comfy.sh`, resume queue (documented recovery in LOCAL_QWEN_IMAGE.md).
5. Serial queue only (the server is 1-job-at-a-time by design); the runner
   never submits ahead more than 1 job.

### 4.7 Throughput and cost

Measured: strip ≈ 4.5 min warm incl. retries; settings/sheets amortized.
8 h night ≈ **~100 strips**, $0 marginal. So: the whole live rescue cohort
(266 items × 1 strip) ≈ 3 nights; the full shipped corpus (2,764 expressions
× 1 strip) ≈ 26–28 nights ≈ one month of quiet overnights; glyphs for the
full corpus (1 t2i each ≈ 35 s) ≈ 4 additional nights. Cloud fallback for
daytime/urgent items stays Nano Banana at ~$0.04/strip (server-side engine of
record — it's the only one Render can reach), i.e. the whole corpus one-shot
in the cloud would be ~$110 but with the pilot's known text-garble risk —
cloud one-shots are only acceptable for panels with no target-language text,
or with the same typeset-over pipeline run server-side (viable: PIL runs
anywhere; only t2i/edit need the GPU).

### 4.8 Mac Studio role — SPECULATION (no specs on file anywhere)

No document in either repo records the Mac Studio's chip/RAM. What is safe to
say: ComfyUI runs on MPS; a Q8 20 GB GGUF fits comfortably in ≥64 GB unified
memory with *no* VRAM/RAM split (it would structurally not have the laptop's
OOM problem); MPS diffusion throughput on a Studio is typically slower per
image than a 4090 but not catastrophically (order 1.5–4× depending on chip —
unverified). Recommendation: **do not build multi-node scheduling into v1.**
Ship the single-laptop runner; once it runs, a one-evening probe on the Studio
(install ComfyUI, run the standard t2i benchmark workflow, measure s/image)
decides between: (a) second render node (runner is already pull-based, so a
second runner Just Works — that's the payoff of §3.1's job queue), (b) the
QA/typeset/stitch node (CPU-only, trivial, frees laptop GPU minutes), or
(c) nothing. Video escalation (§5) needs no local GPU at all — it's API calls.

---

## 5. Escalation ladder: comics → video

### 5.1 Reconciling the record

Round-1 verdict was "comics > diagrams > videos (**dropped**)" — as the
*default hero format*. The user's 2026-08-05 vision reinstates video strictly
as **last-resort escalation** for items that resist comics. These are
compatible: video is banned at strike 1–2 (and stays banned in
`rescue_assets` — the DB CHECK agrees), and becomes available only at
strike 3 under a hard cap. Escalation videos live in `factory_assets`
(`kind='video'`), NOT in `rescue_assets` — no schema-weakening of the
rescue ban required.

### 5.2 The trigger — and the telemetry it needs first

"Sustained non-improvement" is currently **unmeasurable** (verified §0:
snapshots overwritten, no delivery clock, ladder not implemented). Definition
once `struggle_history` + `delivered_at` exist (§3.2):

> An item escalates to video-candidate when: (1) it has an approved comic
> **delivered** ≥14 days ago, and (2) at least two autopilot snapshots taken
> ≥7 days apart since delivery each show `fails_14d ≥ 3` (same threshold as
> `rescue_struggle_min_fails_14d`), and (3) the item's glyph + one
> alternate-axis format (anatomy/polysemy/contrast per the diagnosis rules in
> RESCUE_PILOT.md:50-53) was also tried — video never skips the middle rungs.

Escalation is **proposed, never automatic**: candidates appear in a queue with
their history; the user pulls the trigger per item (consistent with
no-auto-approve and with video's per-unit cost).

### 5.3 What mandarin-videos machinery is reusable (verified inventory)

Directly liftable:
- **Engine adapters**: `worker/hh_worker.py` already speaks MiniMax v2
  (portrait+props as base64 refs, 7,000-char cap), Volcengine ARK/Seedance,
  Vertex/Veo — Python, self-contained, with poll/timeout/rate-limit handling.
- **Ladder mechanics**: fixed rung list, failure advances a rung, exhausted
  ladder = `failed` until a human re-queues; **budget/balance errors are
  TERMINAL** (no rung advance, no retry) — plus the flock-guarded spend
  ledger with a daily cap (`data/minimax-spend-ledger.json` pattern →
  a `gen_ledger` daily-cap query here).
- **Auto-QA**: `props_visible_check` (frames at 5 timestamps → Gemini vision,
  JSON schema, lenient rules, errors-pass) → becomes "cast present, setting
  matches, expression's staging visible".
- **Composition**: `scripts/compose-mnemonic-card.py` (intro card → film →
  tail card, loudnorm, tone-badge HUD) → intro = the item's glyph + idiom,
  tail = gloss; ~14 s study composite.
- **Identity**: portrait-last-in-refs, wardrobe-only text, cast-anchor
  repetition — all directly applicable with cast sheets as portraits.

**The comicization trick in reverse** (the design): mandarin derived comics
from existing videos by pulling frames as refs. Idiomatic derives *videos
from existing comics*: the approved strip's panels become the reference
images for image-to-video (MiniMax refs / Seedance first-frame), the beats
become the shot list, the ElevenLabs sentence audio becomes the track. The
video inherits an already-approved visual identity instead of gambling on a
fresh one — this addresses *why* round-1 videos lost (generic scenes,
expression not visible; Round 2's lesson was "make the expression itself
visible", which the approved comic already does).

### 5.4 Cost model per video (verified prices)

| engine | spec | cost |
|---|---|---|
| MiniMax-H3 | 6 s 768P (0.5¥/s) | 3¥ ≈ **$0.42** |
| MiniMax-H3 | 8 s 2K (0.8¥/s) | 6.4¥ ≈ **$0.90** |
| Seedance 2.0 | 8 s 1080P | **$0.30–0.50** |
| Veo 3.1 Fast | 8 s 720p + audio | **~$1.20** |

(Pilot ground truth: 3 MiniMax videos cost ≈9 CNY total.) Recommended lane:
MiniMax 768P first (cheapest, likeness-tolerant, native audio optional),
Seedance retry rung, Veo only on explicit user pick. With retry allowance,
budget **≈ $1/item escalated**.

### 5.5 Cap policy (proposal, number is the user's — §8)

Hard monthly cap enforced against `gen_ledger` (a *global* cap, not
per-invocation — fixing rescue's budget defect class): e.g. 10 videos/month
≈ $10 ceiling incl. retries. Escalation queue sorted by `fails_14d`; cap
reached → queue holds.

---

## 6. Card design: the combined back

### 6.1 The layout

Front unchanged (expression prompt per existing deck direction). Back, top to
bottom: ① comic strip (the scene encoding), ② typeset idiom + gloss line,
③ **grammar-heavy SVG diagram** (the form encoding — Rescue-pilot style),
④ sentences + audio. Glyph stamped top-right on every card (Round-2 rule:
"the constant identity across changing content"). Comic answers *when would I
say this*; diagram answers *how is it built* — the two failure axes
(recognition vs production) from the pilot's diagnosis rules, on one back.

### 6.2 Concrete mocks (three real pilot items)

**es · se desbloquee** — comic: office/meeting-room setting, boss (cast #5)
frozen mid-negotiation across the table, beat 3 handshake; bubble typeset
«Una vez que se desbloquee, firmaremos.» Below: the **morphology-anatomy SVG
that already exists in the pilot artifact** (des·BLOQUE·e exploded, golden
`-e` as the pending-subjunctive switch, timeline NEGOCIACIÓN→FIRMA) — this
item is the proof the combined back needs no new invention, only assembly.

**es · está tirado** — comic: living-room setting, the coat on the floor,
woman (cast #1) pointing; bubble «Tu abrigo está tirado en el suelo.» Below:
the **polysemy-map three-door SVG** (en el suelo / baratísimo / facilísimo),
each door with gloss + micro-example — the teach-every-door rule is already
enforced by `rescue_senses` NOT NULLs; this item has its 3 senses seeded.

**it · coni d'ombra** — comic: newsroom setting (world wing), journalist
(cast #6) with desk lamp, literal light-cone across the law pages; typeset
caption box «Restano coni d'ombra.» Below: **cone/spatial-metaphor SVG** —
flashlight cone, obstacle, shadow zone labeled; rule line "lasciare/restare +
coni d'ombra".

### 6.3 SVG template library (model-authored, template-constrained)

Confirmed: all existing diagrams are LLM-authored SVG code with shared
`s-*`/palette night-mode classes — cheap and proven. The factory formalizes
**7 archetypes**, each a skeleton SVG with named slots; a text model (codex
tier) fills slots, never freeforms. Demand evidence per archetype from the
live `structured` JSONB (2,523 idiom occurrences):

| archetype | fills from | demand |
|---|---|---|
| morphology strip (anatomy) | citation_form + pitfall | pitfall present on **98.3%** (2,480) |
| polysemy doors | rescue_senses | items with ≥2 senses (gate already enforced) |
| contrast-zones (inside/outside, false friends) | false_friend + spatial preps | false_friend on **12.1%** (305) |
| cone/spatial metaphor | metaphor field | metaphor on **70.4%** (1,776) |
| timeline / tense-gate | usage + grammar notes | subjunctive/temporal idioms (pilot-proven) |
| collocation web | collocations field | present in structured (shape varies) |
| register thermometer | register_note | register on **96.8%** (2,443) |

Verification pipeline for model-authored SVG (no eyeballing 2,000 diagrams):
XML well-formedness; whitelist of elements/attrs (no scripts, no external
refs — the add-on imports this into Anki); only palette classes (night-mode
guaranteed); text-fit check (estimated glyph width vs slot box, the #1
authoring failure); deterministic render-to-PNG smoke (resvg) with the
palette/brightness gate from §4.4; then the normal draft→approve queue.
Content correctness (is the grammar claim right?) follows the grammar
initiative's verification ethos: the slot-filling model must cite which
`structured` field each claim came from; claims with no source field are
rejected at lint time (no unverified generated form ships — the standing
rule).

### 6.4 Note model + delivery (folding in the pending APKG builder)

- **New note model `Idiomatic Rescue v1`**, frozen at ship like the others.
  Proposed 16 fields: Expression, Gloss, Anchor, GlyphImg, ComicImg,
  DiagramSVG, Sent1_TL, Sent1_EN, Sent1_Audio, Sent2_TL, Sent2_EN,
  Sent2_Audio, Exercise, ExerciseAnswer, Tags, Extra1 (spare). Existing
  frozen models (21-field cloud card, 14-field grammar) are untouched —
  frozen-model discipline is satisfied by *addition*, never mutation.
- **`apkgs.kind='rescue'`, one rolling apkg per language** — the exact
  grammar-deck pattern (rolling per-lang, subdeck `Idiomatic Rescue::<Lang>`
  as the pilot named it). Stable GUIDs per (lang, expression) so re-imports
  update cards in place instead of duplicating (both mandarin's
  `anki-guid.ts` and idiomatic's grammar decks already do this).
- The builder consumes the existing export contract
  (`GET /admin/rescue/export/{id}` — api.py:1536) extended with factory
  assets; approved assets only; writing `delivered_at` on ship is what arms
  the escalation clock (§5.2).
- Delivery caveat to design around: the add-on imports into whichever profile
  is open; idiom decks live in the +2 profile. Rescue decks should carry the
  same profile expectations as the idiom pools (and the wrong-profile
  recovery path `/admin/reset-acks` already exists).

---

## 7. Phased execution plan (commission-sized chunks)

Each ≤ a day of codex-session work; dependency-ordered. "USER" marks a gate
that needs the user; everything else is autonomous after strategy approval.

| # | commission | contents | depends | acceptance criteria |
|---|---|---|---|---|
| A | Taxonomy freeze + assignment miner | Ship the §1 classifier as `tools/factory_mine.py` writing per-sentence bucket tags to a `factory_sentence_tags` table; adoption matcher rescue_items↔expressions (§3.2) with manual-confirm list | — | tags for 100% of examples; ≥90% of rescue items adopted or queued for confirm; spot-check 50 tags ≥85% agreement |
| B | Registry backend | §3.2 DDL into schema.sql; `/admin/factory/*` job-queue endpoints (lease semantics), `/admin/factory/upload`; `struggle_history` append wired into autopilot | A | schema applies idempotently on boot; lease survives concurrent pollers (test); upload round-trips a file to /data + row |
| C | Cast + settings pregen batch 1 | Generate 32 sheet candidates + ~70 setting views locally; Cast/Settings signoff pages in Rescue Lab | B, **USER** (approves axes §8 first; approves each sheet after) | all sheets/views uploaded as candidates; signoff page mutations work; user has approved ≥1 full language cast |
| D | Cycle runner + QA | Laptop daemon (poll→render→QA→upload→ack), OOM guards §4.6, auto-QA gates §4.4, beat-author prompt contract + lints | B, C | one unattended overnight completes ≥50 strips from the rescue queue with zero manual intervention; parked-panel reasons visible in dashboard |
| E | Dashboard factory queue | Review queue (approve/reject with note), per-item asset galleries, cost tiles vs gen_ledger, escalation-candidates view | B, D | user reviews a morning batch end-to-end from the browser; no CLI needed |
| F | APKG builder (`kind='rescue'`) | Note model v1, builder, rolling per-lang apkg, GUID stability, `delivered_at` stamping; **pilot deck of ~10 approved items first** (pilot-first rule) | E, **USER** (approves combined-back mock + pilot deck) | pilot deck imports cleanly into the +2 profile; re-import updates not duplicates; delivered_at set |
| G | Escalation bridge | §5 trigger query over struggle_history; escalation queue UI; MiniMax/Seedance adapters ported from hh_worker; strip→video composer; global monthly cap | F | one user-triggered escalation produces a reviewable video composite ≤ $1; cap blocks the N+1th |
| H | Corpus walk | Extend cycle beyond rescue to newest-first expressions; glyph pregen; Exercises 2.0 art hooks | D–F stable | steady-state: nightly cycle keeps up with the 3-apkg/day/lang inflow |

Swapfile creation precedes D (one command, but it's a machine-config change —
user's call, §8).

---

## 8. Decisions the user owes

1. **Cast**: approve size/composition (6 per language + 2 shared, §2.1) and
   the demographic axes; then per-sheet approval as batch C lands. Also:
   should the 2 shared cross-language figures exist at all?
2. **Per-language casts vs one shared cast** — strategy recommends
   per-language with 2 shared figures (pilot evidence + cultural fit); veto
   here reshapes batch C.
3. **Settings flavor**: per-language flavored for the 5 conversation-host
   settings + neutral for the rest (§1.5), or all-neutral (cheaper to curate,
   blander), or all-flavored (~140 renders, most curation)?
4. **Swapfile go-ahead**: 16–32 GB on the laptop NVMe — blocks unattended
   overnights until done. (Three OOM kills today.)
5. **Disk/hardware allocation**: OK to dedicate `/srv/ai-models` space for
   factory originals (~tens of GB over time) and ~1.5 GB of `/data` for
   deck-bound finals? Provide Mac Studio specs (chip/RAM) if the second-node
   probe (§4.8) should happen.
6. **Combined-back approval**: sign off the §6.1 layout + §6.2 mocks before
   commission F builds the note model (the model is frozen once shipped).
7. **Escalation budget**: videos/month cap (proposal: 10 ≈ $10/mo) and
   whether Veo is ever in the lane or MiniMax/Seedance only.
8. **Corpus-walk scope**: pre-generate comics for ALL 2,764 shipped
   expressions (~1 month of nights, $0) or only rescue + new inflow until
   review capacity is proven? (Reviewing ~100 strips/morning is the real
   constraint, not GPU.)
9. **Rescue deck cadence + hero placement** (inherited open decisions from
   RESCUE_PILOT.md:129-133): rolling rescue apkg update frequency, and comic
   on the back (recommended §6.1) vs front.
