# F4 — server-side example adoption: analyzer, applier, rehearsal record

> Built 2026-08-09 on branch `hub-adoption`. Analyzer ran READ-ONLY
> against production (`/admin/corpus-export`) and the guarded collection
> copy; the applier has NOT touched production — its `--apply` requires
> the coordinator go-token (`ADOPTION_GO_TOKEN`, not created by any tool
> here) and was exercised on ephemeral Postgres only.

## Toolchain

| piece | path |
|---|---|
| adoption library (plan build, INSERT-only SQL, results export, extract merge) | `idiomatic/hub/adoption.py` |
| analyzer (read-only; plan + fresh extract + MD) | `docs/research/anki_reorg_scripts/hub_adoption_analyze.py` |
| applier (gated: plan sha + sidecar, F1-staging probes, --apply + go-token) | `tools/hub_adoption_apply.py` |
| full-loop rehearsal (ephemeral Postgres) | `tools/hub_adoption_rehearse.py` |
| compiler flags | `hub_phase5_compile.py --adoption-results / --asset-coverage / --expect-deferred-max` |
| plan of record | `adoption_plan.json` (gitignored; sha in `adoption_plan.json.sha256`) + `ADOPTION_PLAN.md` (committed, every deferred case listed) |

## Analyzer result (3,215 deferred cards in)

| bucket | count |
|---|---:|
| resolved against fresh server examples (rows minted since the campaign export; no insert needed) | **48** |
| proposed adoptions — new NULL-video source occurrence + example row under an EXISTING expression | **120** (539 reps; de 18 / es 12 / fr 24 / it 46 / pt 20) |
| still deferred — `no-expression-match` | **3,047** (3,041 adoptable, **12,367 reps**; it 798 / fr 722 / pt 594 / de 506 / es 421 + 6 fresh-trivial) |

Reconciliation is exact: 48 + 120 + 3,047 = 3,215.

**The coordinator's "~54 remainder" expectation does not hold — and the
reason matters.** The 3,047 remainder is not ambiguity: every one of
those cards names an idiom SURFACE that does not exist among current
server expressions at all (samples: it `tanto vale che`, `girarci
intorno`; de `aus etwas hervorgehen`; pt `mal sabia`). This is the
legacy/orphan EXPRESSION-level backlog: resolving it means creating new
`expressions` rows — which the design explicitly gates ("adoption
candidates, not automatic empty hubs": reviewed expression creation,
then the normal six examples). That is an owner-scoped commission, not
an analyzer liberty. Note: surface matching sees expressions present in
the corpus export (those with ≥1 example); bare expression rows without
examples, if any exist, were not visible to it.

## Join-parity defect found and fixed

First analyzer draft normalized the note fields with our own
`normalize_join` on BOTH sides. But the compiler joins **C2's own
normalized card surfaces** against our normalization of server text —
and on old orphan notes the two normalizations disagree. Consequences
before the fix: step-1 missed resolvable cards, and an adopted row could
never rejoin its own card after apply. Fix (regression-tested,
`normalization-mismatch` defer reason): the analyzer looks up with the
C2 pair and only proposes an adoption when
`normalize_join(note field) == C2 normalized field` — proving the
round-trip closes. The apparent "126-card corpus drift" in the first
rehearsal was entirely this asymmetry; with parity, drift is **0** and
every count reconciles exactly.

## Full-loop rehearsal (ephemeral Postgres) — PASS

1. seeded parent expressions; applier run #1: **120/120 source +
   example rows inserted**; run #2: **0/0** (idempotency; deterministic
   `anki:v1:syllabus:<note_id>` / `anki-adopt:v1:syllabus:<note_id>`
   keys + `ON CONFLICT DO NOTHING`);
2. boot-migration re-run backfilled `position` on adopted rows
   (appended after existing examples), zero unpositioned rows;
3. results exported; recompile with fresh extract + results:
   conversions 17,578 → **17,698**, adoptable 927 (2,166 reps), hub
   notes 2,934, deferred **3,047 = exactly the plan's remainder**;
   assertion holds: baseline − 120.
   (One rehearsal-only artifact fixed en route: ephemeral BIGSERIAL ids
   1..120 collided with real corpus example ids and tripped the
   one-binding-per-example rule; sequences now seeded past 10M.)

## C3 files

- `C3_server_examples_extract.json` (landed first): **all 18,258
  example_ids are NULL** — unusable as a durable-ID join source;
  flagged, not wired. The analyzer's `fresh_server_extract.json`
  (from `/admin/corpus-export`, real ids) serves that role instead.
- `C3_asset_coverage.json` (landed mid-build): wired via
  `--asset-coverage` — the manifest of record now annotates every hub
  example with its asset status (**222 qa-passed**, all ES; 0 missing
  coverage rows) and re-seals its checksum; expectations re-recorded
  with the coverage file pinned. Assets stay an enrichment layer: the
  executor leaves `Image` blank, bytes ship at release build against
  the recorded SHA1s.

## Production apply runbook (coordinator-gated; NOT run)

```
source ~/.config/idiomatic-admin.env   # or however DATABASE_URL arrives
# coordinator creates docs/research/hub_manifest/ADOPTION_GO_TOKEN
.venv/bin/python tools/hub_adoption_apply.py --dsn "$DATABASE_URL" --apply
.venv/bin/python tools/hub_adoption_apply.py --dsn "$DATABASE_URL" \
    --export-results docs/research/hub_manifest/adoption_results.json
# fresh analyzer pass first if the corpus moved (it moves daily);
# then recompile the phase-5 manifest:
.venv/bin/python docs/research/anki_reorg_scripts/hub_phase5_compile.py \
    --server-extract docs/research/hub_manifest/fresh_server_extract.json \
    --adoption-results docs/research/hub_manifest/adoption_results.json \
    --asset-coverage docs/research/hub_manifest/C3_asset_coverage.json \
    --record-expectations   # reviewed act: commit the new pins
```

Caveat for the live run: the corpus moved twice during this session
(+36 rows in ~30 min — the pipeline mints daily); the analyzer, plan,
and recompile must come from ONE corpus snapshot in the same sitting,
which the plan's per-language corpus checksums enforce.

## Pool-rebuild interaction (coordinator pre-gate question) — verdict (b), guard shipped anyway

Question: after `--apply`, what does the next `pool_expr` rebuild emit
for the 120 adopted sentences?

**Verdict: (b), proven empirically — 120/120 exact GUID matches, 0
new.** The pool GUID recipe (`_guid("yt-pool", _norm(idiom_text),
_norm(target_text))`) closes over exactly the texts the adoption
preserves verbatim from the orphan notes' own fields, so the rebuild
re-emits precisely the orphan notes' existing GUIDs (compared against
every C2 `note_guid`): an in-place update, zero duplicates.

**But (b) was still harmful**: adopted rows carry NULL audio and no
video, so the in-place update would have BLANKED the studied orphans'
working `[sound:]` fields and degraded their source line. Shipped
guards:

1. **Pool guard** — `db.fetch_pool_idioms` (the single chokepoint
   feeding pool_expr, the retired didactic/audio builders, AND the
   local-TTS fluency overlay seeder) now excludes NULL-video
   occurrences, non-active sources, `legacy_adopted` examples, and
   non-published examples. SQL extracted to constants
   (`POOL_IDIOMS_SQL` / `POOL_EXAMPLES_SQL`); regression test executes
   them verbatim on ephemeral Postgres. Zero behavior change for
   current prod data (0 NULL-video rows in the live snapshot).
2. **Purge orphan-check fix** — `/admin/purge-video`'s
   `ei.video_id <> $2` was NULL-false for adopted occurrences, so a
   purge touching an expression with adopted rows would have wrongly
   classified it orphaned and then failed on the examples' FK.
   `IS DISTINCT FROM` now counts a NULL-video occurrence as the
   keep-alive it is (regression-tested).

Other consumers audited: **retts** enqueues only non-NULL audio paths —
adopted rows invisible; **audio-audit** walks staged files only;
**corpus-export** WILL include adopted examples (intended — they enter
the illustration/enrichment lane); the admin citation backfill's
backlog count will include adopted rows (operator-gated run, eventually
wanted). Grammar/translation/exercises2 never touch these tables.
