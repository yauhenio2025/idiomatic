# Anki estate reorganization — study commission (codex)

> STUDY ONLY. You produce an inventory, a target structure, and a
> migration plan with draft scripts. You NEVER modify the live
> collection, the live database, or the pipeline. The user reviews the
> plan before anything executes.

## Context

One Anki profile (evgeny@the-syllabus.com) has accumulated several
years and several generations of language-learning systems. It is a
mess by the owner's own verdict. Generations present:

1. **The idiomatic pipeline** (this repo — read CLAUDE.md first):
   rolling decks auto-imported by a local add-on. Deck families:
   `Idiomatic::<Language>::…` per-video decks (hundreds, one per
   YouTube video — the owner wants these GONE as a structure),
   `…::Fluency Expressions` (one card per example sentence),
   `…::Idioms` (expression EN↔target), `…::Idioms Audio (EN → target)`
   and `(target → EN)` (long listen-and-learn cards — being
   discontinued), plus top-level `Idiomatic Exercises {DE,ES,FR,IT,PT}`,
   `Idiomatic Grammar XX`, `Idiomatic Tenses XX` (+ `Tenses Exercises`),
   `Idiomatic Translation XX`, `Idiomatic Rescue Comics`.
2. **Legacy pre-idiomatic decks** under `Languages::{French,German,
   Italian,Mandarin,Portuguese,Spanish}` — hand-era equivalents of the
   same data (fluency sentences, idioms audio, per-video YouTube
   subdecks). Similar shape, different models.
3. **Pimsleur** — one tree mixing every language incl. inactive ones
   (Danish, Dutch…).
4. **Mandarin family** — `Mandarin Palace`, `Mandarin Actors/Props/
   Zones/Locations/Characters/China Provinces` + Mandarin under
   Languages. A SEPARATE flow (mandarin-videos repo) — do NOT
   restructure its internals; only place it in the hierarchy.
5. Odds and ends: `EXPERIMENTS-YT`, `Webtest`, `z-archive`, `Lex-Stage`,
   `Custom Study Session`, empty stubs (`Idiomatic::de`, `::fr`, `::it`).

## The owner's target (verbatim intent)

- **Language-first hierarchy**: one top-level tree per actively studied
  language (German, Spanish, French, Italian, Portuguese) containing
  everything for that language — expressions/fluency, grammar, tenses,
  exercises, translation, errors, rescue — in a clean, linear, numbered
  order. Mandarin is its own top-level tree (separate flow).
- **No per-video decks.** Provenance stays as tags/fields, not decks.
- **Legacy content merged in**, not parked: same-shaped legacy cards
  join the same language trees (scheduling preserved; dedupe where the
  same sentence exists in both generations).
- **Pimsleur disaggregated by language**; its cards join each
  language's tree. Inactive languages (Danish, Dutch, …) live under a
  demoted tree (e.g. `zz Dormant::…`) so they sort last and stay out of
  the way.
- **Discontinue** the long Idioms Audio listen-and-learn decks (keep
  the notes' data accessible; the cards stop being studied/generated).
- Empty stubs and junk decks removed; `z-archive` absorbed into the
  demoted tree.

## Your inputs

- Work from a COPY of the collection. Anki may be open; copy from the
  most recent automatic backup instead of the live file:
  `~/.var/app/net.ankiweb.Anki/data/Anki2/evgeny@the-syllabus.com/backups/`
  (newest `.colpkg`) — unzip to a working dir under
  `docs/research/anki_reorg_work/` (gitignored is fine). NEVER open the
  live `collection.anki2` for writing; prefer not opening it at all.
- The repo docs: CLAUDE.md, DASHBOARD.md, docs/GRAMMAR_STRATEGY.md,
  docs/ASSET_FACTORY_STRATEGY.md (for what the pipeline will need
  next), docs/commissions/EXPRESSION_HUB_MODEL_COMMISSION.md (the
  parallel data-model study — your deck plan must leave room for its
  outcome).

## Deliverables (all under docs/research/)

1. `ANKI_ESTATE_INVENTORY.md` — the facts: full deck tree with note
   counts, note models (fields, which decks use them), scheduling mass
   per subtree (cards with intervals > 21d = mature investment that
   must not be lost), tag taxonomy, duplicates across generations
   (same sentence/expression in legacy + idiomatic), orphaned media
   estimate.
2. `ANKI_ESTATE_REORG_PLAN.md` — the proposal:
   - Target deck tree, drawn in full, with numbered ordering
     (e.g. `ES Spanish::1 Expressions`, `::2 Grammar`, …) — propose a
     concrete naming scheme; bilingual names are fine but keep sort
     order deterministic.
   - Per current deck: destination (move / merge / demote / delete),
     and the mechanism (deck move = safe; note-model change = risky —
     call out every place one is required).
   - The per-video deck elimination: how provenance is preserved
     (tags exist: `youtube`, lang tags; check what else is needed).
   - Pimsleur split by language + dormant demotion.
   - Dedup policy for legacy-vs-idiomatic collisions (suspend legacy /
     merge history — argue one).
   - **Pipeline compatibility**: the add-on imports apkgs whose deck
     names are baked at build time (grammar/exercises2/translation/
     tenses/rescue_comics builders in this repo). List every builder
     deck-name constant that must change to match the new tree, and
     the order of operations (rename in Anki first vs builder first)
     that avoids duplicate trees. Grammar reorg add-on precedent:
     the add-on once moved cards into subdecks by tag — the same
     mechanism can execute deck moves at scale.
   - Migration phases, each independently pausable, each with a
     rollback note, scheduling preserved throughout.
3. `anki_reorg_scripts/` — DRAFT Python scripts (anki library, operate
   on the working COPY only, with a --copy-path arg) for each phase.
   Scripts must refuse to run on a path containing the live profile.
4. A short list of decisions only the owner can make (kill vs keep per
   odd deck, naming language, dormant-tree name, dedupe policy).

## Hard constraints

- Scheduling/review history is sacred. Deck moves preserve it; never
  propose export/reimport that resets it.
- Mandarin internals untouched; Lex-Stage untouched (prototype).
- Study only: no writes outside docs/research/ + the working copy dir.
- Everything reproducible: scripts + queries, not hand-edits.
