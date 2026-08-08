# RESTRUCTURE STATUS — what shipped, what's parked, what's next

> Owner-facing accounting of the 2026-08 expression/estate restructure.
> Written 2026-08-08, the morning after the estate cutover. If something
> you expected is in none of these buckets, it dropped — flag it.

The 2026-08-07 architecture session split the restructure into two
sequenced commissions: the **estate reorganization** (the tree) and the
**Expression Hub** (the content model). Estate is DONE.

**PRIORITY CHANGE (owner, 2026-08-08): before the Hub comes the legacy
estate sweep** — full inventory of the old +2 account, completion of the
planned exercises imports, and cost-0 local Qwen voicing of everything
un-voiced ([LEGACY_ESTATE_AUDIT_COMMISSION](commissions/LEGACY_ESTATE_AUDIT_COMMISSION.md)).
Rationale: structure all source material BEFORE the hub's model freeze,
so nothing needs re-importing after. The Hub then holds every remaining
user-visible deliverable.

**Sweep progress (2026-08-08 11:30 +0800): Part A audit shipped.** A fresh
download-only +2 snapshot is fully inventoried in
`docs/research/legacy_estate/` (238 deck rows; 228,413 notes; 282,976 cards),
seeded into the idempotent `legacy_estate` table, and visible read-only at
`/legacy`. Codex proposals are not import authority: the one-sitting owner
verdict remains the Part-A gate. The snapshot confirms the settled targeted
cleanup (fake IT exercises, toxic ES false-friends, and 30 contaminated PT
phrase rows) is already reflected; this audit did not touch cleanup.json or
the remaining +2 purge track. Parts B/C are still ahead of the Hub and retain
their pilot/listening/GPU-window gates.

## 1. DONE — estate migration (closed 2026-08-08 morning)

- Live collection migrated to six language roots + numbered lanes +
  `zz Dormant`; scheduling/history verified intact (phases 1–10 PASS);
  full AnkiWeb upload + iPad pull verified; owner studied normally.
- All builders compose deck names from `idiomatic/anki_tree.py::
  anki_root()`; forced rebuilds of every family confirmed imports land
  inside the new tree; retired kinds (video, didactic pool, audio
  pools) blocked at `/apkgs/pending`.
- Record: ANKI_ESTATE_REORG_PLAN.md §Live copy-back cutover +
  COMPLETION NOTE. Rollback file: `collection.anki2.pre-estate-*`
  beside the live profile.

## 2. PARKED → Expression Hub commission (unblocked, not started)

User-visible gaps that are the Hub's explicit deliverables:

- **`1 Expressions::2 Expression Focus` is empty** — hub card per
  expression (model `1820180001`, vertical comic rail) needs the
  sense-resolved ID manifest first.
- **`4 Exercises::Diagnosed trouble spots` is empty** — Flag-1
  diagnosis cards (Balanced weakness policy).
- **No didactic teaching cards arrive daily** — per-video decks are
  retired (owner verdict); their replacement is Hub projections.
  Until the Hub ships, only Fluency pool updates flow.
- **6,242 archived old tasks + 2,665 surface-collision groups** wait,
  tagged and suspended, for the Hub manifest's disposition.
- **Card illustrations** — the image campaign keys on `example_id`;
  cards show them only when Hub/Fluency templates carry them.
- Hub-window plumbing: `/admin/purge-video` source-ID disposition;
  add-on release-manifest import gates.

### Owner amendments recorded 2026-08-08 (into the Hub card design)

1. **EN→TL expression-production card.** The accepted hub design has
   only the TL-front hub card (TL expression → gloss/examples) plus
   sentence-level Fluency cards. The retired `e2t` deck's task —
   English on the front, the *expression* on the back — has no
   successor in the accepted spec. The Hub note must also project an
   EN→TL expression card (second template or second card of model
   `1820180001`, decided at model-freeze time).
2. **Source-video context clip on the back.** The accepted hub back
   carries source titles/URLs as text only. Amend: embed the short
   per-occurrence context clip (`expression_idioms.audio_context` —
   the sentence as spoken in the source video) on the hub-card back
   (and the EN→TL card back). The LONG stitched listen-and-learn
   compilations stay retired; this is seconds-long occurrence audio
   that already exists server-side.

## 3. Parked elsewhere (own tracks, not lost)

| Item | State | Trigger |
|---|---|---|
| Qwen local TTS default flip | Render still pins `TTS_PROVIDER=elevenlabs`; bridge idle | Run bridge acceptance drills (advised: after the trip) |
| Pimsleur scraper + Mandarin external builders | Still bake old deck roots | Update before any re-run (flagged in plan completion note) |
| Media cleanup (~6.5 GiB orphan estimate) | Deliberately out of scope | Copied media dir + missing Mandarin `.webm` repair + owner approval |
| +2 legacy profile purge | cleanup.json single-slot pending | Factory commission-B queued-cleanup requirement |
| Exercises 2.0 remaining topic waves | Standing nag | docs/EXERCISES2_ROADMAP.md |
| Error-mine Wave 7 | Proposal pending owner decisions | docs/research (error profiles) |
| Stall-popup cap-idle false alarm | Heuristic fires on fully-capped days | Owner opts in to the fix |

## 4. What happened to the expression↔English decks (owner question, 2026-08-08)

The decks with ONLY the expression (TL front / EN back, and EN front /
TL back) were the `pool_idiom_t2e` / `pool_idiom_e2t` "Idioms Audio"
direction decks. Timeline: builders discontinued 2026-08-07 by owner
directive ("I will never have time to listen to them" — they had grown
into long listen-and-learn compilations); the estate verdicts then
moved all 12,667 existing cards intact to `zz Dormant::Retired Idioms
Audio::<LANG>::{EN to target, target to EN}` and suspended them.
Nothing is deleted; unsuspending is one click if ever wanted. The
TL→EN task returns as the hub card by design; the EN→TL task and the
context audio return via the two amendments above.
