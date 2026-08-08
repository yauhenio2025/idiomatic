# Expression-hub decisions

Study only. Recommended choices are first.

## 1. How many examples?

**Recommended: keep every existing canonical example—normally six—then allow
unlimited top-ups.** A source-only legacy adoption starts with six. The hub
shows them all through one HTML rail; each sentence has its own subordinate
note/card. This preserves compatible sentence schedules and avoids rebuilding
the note model to add slots.

Alternative: freeze 12 or 24 slots inside one giant note. This caps growth and
cannot safely absorb the existing sentence-card schedules.

**Owner decision:** approve normally six initial examples with no hard cap?

## 2. When is an expression weak?

**Recommended: Balanced.** An Again counts 1 and a Hard counts 0.5. “Rate” is
that weighted score divided by eligible reviews.

| policy | opening evidence and rule | severe | delivery/recovery |
|---|---|---|---|
| **Balanced** | 14 days; 6 reviews/2 sentences; rate ≥30% and either 3 Agains or score 4 | 5 Agains in-window, after the evidence floor | +3 normally/+5 severe or persistent; wait 14 days, then 6 reviews including 4 across 2 new sentences; recover only with a 21-day 6-review/2-sentence window, no Again, and rate <15% |
| Sensitive | 7 days; 4 reviews/2 sentences; rate ≥25% and either 2 Agains or score 3 | same 5-Again override after its evidence floor | same +3/+5, delivery gate, and recovery rule |
| Conservative | 21 days; 10 reviews/3 sentences; rate ≥35% and either 4 Agains or score 5 | same 5-Again override after its evidence floor | same +3/+5, delivery gate, and recovery rule |

“Eligible” means a normal learning/review/relearning answer on a mapped
fluency card after cutover. It excludes manual/cram events and any review tied
exactly to a new Flag-1 event. The headless fallback can make that link only
when there is one candidate Again/Hard; an ambiguous flag changes nothing.

**Owner decision:** Balanced, Sensitive, or Conservative?

## 3. Where do Flag-1 drills go?

**Recommended:** `<Language>::4 Exercises::Diagnosed trouble spots`. Store the
items in a diagnosis-specific queue, then render them with the frozen one-card
Grammar Drill shape, tagged with diagnosis, source sentence, and expression.
These reviews measure the real trouble spot, not expression weakness.
An exact verified grammar card may satisfy a slot in place; it is linked, not
duplicated or moved, and produces no diagnosis-card telemetry.

Alternatives:

- route grammar diagnoses into individual Grammar units—tidier, but routing is
  more complex;
- put them beside fluency cards—not recommended, because it muddies expression
  telemetry.

**Owner decision:** approve the dedicated Exercises subdeck?

## 4. What should the hub card look like?

**Recommended: vertical comic rail.** Target sentence, muted English line,
then one full-width image; repeat for every example. This exactly matches the
brief and reads well on a tablet.

- Two-column grid: less scrolling, but smaller images and weaker comic rhythm.
- Batch chapters: initial six, then each top-up under a heading; clearest once
  hubs get long, but adds visual furniture.

**Owner decision:** vertical rail, grid, or batch chapters?

Operational rule for any choice: the preferred add-on records the exact
review/Flag-1 pair and clears Flag 1 only after the server acknowledges the
diagnosis. With headless pull only, leave Flag 1 set through the next sync/pull
and clear it after acknowledgement. Old flags are baseline-only and are never
applied retroactively or auto-cleared.

---

## VERDICTS (user, 2026-08-07)

All four recommendations ACCEPTED: (1) six initial examples, no hard cap,
subordinate example cards; (2) **Balanced** weakness policy; (3) dedicated
`<Language>::4 Exercises::Diagnosed trouble spots` subdeck for Flag-1
diagnoses; (4) **vertical comic rail** hub card. The hub design is fully
decided; build sequencing follows the estate-reorg plan's phase order.

---

## OWNER AMENDMENTS (2026-08-08, post-estate-cutover) — bind at model freeze

Two additions to the accepted hub card spec, raised by the owner after
seeing the migrated tree (record: docs/RESTRUCTURE_STATUS.md §2):

1. **EN→TL expression-production card.** The accepted design projects
   only the TL-front hub card; the retired `e2t` task (English front →
   expression back) has no successor. The hub note must also project an
   EN→TL expression card — second template/card on model `1820180001`,
   exact shape decided when the model freezes. TL→EN recognition is
   already covered by the hub card front.
2. **Source-video context clip on card backs.** The accepted hub back
   lists source titles/URLs as text only, which loses the ability to
   HEAR the expression in the video where it first appeared. Amend:
   embed the short per-occurrence context clip
   (`expression_idioms.audio_context`) on the hub-card back and the new
   EN→TL card back. The long stitched listen-and-learn compilations
   remain retired; this is seconds-long occurrence audio already
   persisted server-side.
