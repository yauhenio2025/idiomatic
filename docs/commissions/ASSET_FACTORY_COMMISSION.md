# Commission: The Asset Factory — strategy for reusable comic/video assets

> For a codex or Claude session. INVESTIGATION + STRATEGY only — no code
> in this session. The output is a plan the user approves, which then
> becomes multiple commission-sized coding sessions.

## The user's vision (2026-08-05, condensed from their words)

Asset reusability is THE key. Tonight's pipeline experiments proved the
mechanics (see §Prior-knowledge); what turns them into a system is a
persistent library: a **stable cast of characters** (male, female,
family, different ethnicities/ages) that the learner comes to *know* —
recurring people make every card encounter meaningful and memorable —
plus **reusable settings** for the social situations the corpus actually
contains. Then per-item generation collapses to "feed the right people
into the right setting saying the right thing."

The system runs in **cycles** (overnight batches; the RTX 4090 laptop
and a Mac Studio are both available): walk the already-shipped
idiomatic expressions, pre-generate comic assets for each, and
**escalate to full video** (mandarin-videos machinery) for items that
show consistent non-improvement on comics. Card design should explore a
**combined back**: comic on top, grammar-heavy SVG diagram below (the
Rescue-pilot style), and investigate whether those SVGs can be
model-generated rather than hand-authored.

## Read first (both repos + evidence)

- `~/projects/mandarin-videos` — the architectural reference: README
  (deterministic mapping: initials→actors, finals→locations,
  tones→zones, radicals→props), `data/`, `DATA_MANIFEST.md`, the
  actors/props signoff flow, script→video pipeline, caching. Extract
  the ontology PATTERN, not the phonetic specifics (idiomatic's mapping
  axis is social context, not phonology).
- `~/projects/idiomatic` — `idiomatic/rescue.py` + `rescue_autopilot.py`
  + `rescue_ops.py` (the struggle-detection + format-ladder system THE
  FACTORY MUST EXTEND, not duplicate: strikes, formats incl. comic/
  video, activation, budgets); `docs/research/RESCUE_PILOT.md`;
  DASHBOARD.md; `db/schema.sql` (expressions, expression_idioms,
  expression_examples — the corpus to mine); `docs/STATE_OF_PLAY.md`
  (Rescue's known defects: no run lease, manual APKG export).
- `~/llms/qwen-image/LOCAL_QWEN_IMAGE.md` — the local stack + the
  comic-pipeline findings appendix (2026-08-05).
- Artifacts (WebFetch): pipeline worked examples
  claude.ai/code/artifact/7e47d809-c4e0-43f7-8526-b3ce8193b8c3 and the
  engine head-to-head …f78fffec…; Idiom Rescue Pilot …4762eb1c… (the
  approved card aesthetics + the authored-SVG diagram style).

## Prior-knowledge from the orchestrating session (verify, build on)

- Validated recipe: t2i settings (no text/people) → Edit-2511 inserts
  characters from a reference sheet (image2) → bubbles/captions TYPESET
  IN CODE (never model-rendered — Lightning garbles Romance text, edit
  drops letters/leaks instruction words) → panels stitched
  programmatically. ~4.5 min/strip warm, $0; insertion 5/7 first-pass,
  7/7 after one firmer retry; busy scenes dilute character refs; firmer
  prompts can drop backgrounds.
- Ops constraints: laptop-only server (127.0.0.1:8199, NOT reachable
  from Render — an upload path to the server's staged media is required
  for anything that ships in an apkg); jobs serial ~1/min; RAM is the
  scarce resource — THREE OOM kills on 2026-08-05; a 16–32 GB swapfile
  is the known outstanding fix; batch by model (all t2i, then all
  edits); /free after batches; idempotent re-queue loops.
- SVG provenance answer (user asked): the Rescue-pilot and podcast-card
  diagrams are LLM-AUTHORED SVG CODE (sessions write the markup,
  sanitized inline, night-mode via shared `s-*`/palette classes) — no
  image model involved. "Model-generated SVG" therefore means text-model
  authoring against a template library, which is already proven cheap;
  the strategy should specify templates + verification, not diffusion.
- Rescue already has: struggle snapshots (iPad/AnkiWeb ingestion),
  per-item strikes, format registry (comic/contrast/polysemy_map/…/
  video), a $-budgeted autopilot (Qwen API), approval gates (no
  auto-approve), 7 drafts pending user review. The factory is the
  ASSET + PREGEN layer beneath this; escalation-to-video should key off
  Rescue's strike/no-improvement telemetry rather than a new metric.

## What the strategy document must decide (docs/ASSET_FACTORY_STRATEGY.md)

1. **Social-situation taxonomy — mined, not invented.** Cluster the
   actual corpus (expressions + their source sentences + the 6 examples
   each + Exercises 2.0 example sentences) into recurring contexts
   (home/family table, café, newsroom/office, press conference,
   street/protest, screen/platform world, …) with per-language counts.
   Output: the N settings worth pre-generating per language, with
   evidence.
2. **Cast design.** How many recurring actors; demographic axes (age,
   gender, ethnicity, family roles); ONE shared cast vs per-language
   casts (cultural fit: the PT grandma vs the ES couple vs the IT
   journalist — tonight's strips suggest per-language casts with a few
   cross-language recurring figures); character-sheet spec (poses,
   outfits, naming) and identity-stability protocol (sheet as image2,
   firmer-retry ladder).
3. **Asset registry schema.** Tables for actors, settings (with views),
   props, generated panels, item↔asset assignments, render jobs +
   QA state, escalation state; where it lives (extend idiomatic
   Postgres vs local SQLite + sync — recommend one, justify);
   file/naming conventions; the laptop→server upload path for
   deck-bound media.
4. **The cycle engine.** Nightly batch design: item selection order
   (Rescue strikes first, then newest expressions), scene/cast
   assignment, generation recipe, automated QA gates (what CAN be
   auto-checked: file exists/size, panel count, palette; what needs
   the user's eyeball — keep Rescue's no-auto-approve rule), retry
   policy, OOM-safe scheduling, Mac Studio's role (second render node?
   video-only? evaluate what runs on MPS).
5. **Escalation ladder.** Comics → video: the trigger (sustained
   non-improvement definition from revlog/Rescue data), what
   mandarin-videos machinery is reusable for non-Mandarin content
   (engines, script templates, the comicization trick in reverse),
   cost model per video, cap policy.
6. **Card design.** The combined back (comic top + grammar SVG bottom):
   mock it concretely for 2-3 real items; SVG template library proposal
   (which diagram archetypes recur: timeline, contrast-zones, morphology
   strip, cone/spatial metaphor); note-model implications (Rescue has NO
   apkg path yet — this strategy should fold in the pending APKG-builder
   so the factory ships to Anki, respecting frozen-model discipline).
7. **Phased execution plan.** Commission-sized chunks (one codex session
   each, ~a day max), dependency-ordered, each with acceptance criteria:
   e.g. (a) taxonomy mining, (b) schema + registry backend, (c) cast +
   settings pregen batch 1, (d) cycle daemon + QA queue, (e) dashboard
   frontend (extend /rescue), (f) apkg/card integration, (g) video
   escalation bridge. Mark which need the user vs which are autonomous.
8. **Decisions the user owes** — compact list (cast size/composition
   approval, per-language vs shared cast, disk/hardware allocation,
   swapfile go-ahead, combined-back approval, escalation budget).

## Hard rules

- No code, no schema changes, no generation runs except (optionally) up
  to 5 cheap local probe renders if a claim genuinely needs testing —
  batch-by-model, /free after, never while another session's queue is
  active.
- Read-only on both repos and live endpoints; no git writes except
  committing `docs/ASSET_FACTORY_STRATEGY.md` — actually: write the file
  and STOP; the orchestrating session reviews and commits.
- Every recommendation grounded in either corpus data, tonight's
  measured findings, or mandarin-videos' demonstrated architecture —
  flag speculation as such.
- End with the user-decisions list printed to the terminal.
