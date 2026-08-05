# Rescue Lab — handoff memo (2026-08-05)

Built per `docs/commissions/RESCUE_LAB_COMMISSION.md` by a fresh session,
end to end, in one day. Everything below is deployed and seeded.

## What shipped

- **Schema** (`db/schema.sql`, applied by the boot migration):
  `rescue_items` (unique per lang+idiom, status candidate/active/retired,
  strike 1..3, glyph pointer, snapshot JSONB), `rescue_assets` (format
  CHECK excludes video at the DB level), `rescue_senses` (all four
  teaching fields NOT NULL — a door cannot exist half-taught),
  `gen_ledger` (asset FK is SET NULL, so deleting an asset never
  un-spends the money).
- **Provider registry** `idiomatic/genmedia.py`: `nano-banana`
  (gemini-3.1-flash-image, $0.067/img) and `nano-banana-lite`
  (gemini-3.1-flash-lite-image, $0.0336/img); one
  `generate_image(provider_key, prompt, params) -> (bytes, cost_usd)`
  entry point riding gemini.py's existing retry/safety machinery
  (`generate_image_bytes` extracted with a per-call model override).
  Adding a non-Gemini provider = one dict entry + one adapter function.
  No video adapter exists and none may be added.
- **Format taxonomy + templates** `idiomatic/rescue.py`: comic,
  contrast, polysemy_map, anatomy, poster, glyph (generated) + svg,
  sentence_audio (manual). Templates are the pilot's approved prompts
  generalized with placeholders; the polysemy template refuses to fill
  without ≥2 senses; the anatomy template hard-demands strict
  left-to-right letter order.
- **Admin endpoints** (`/admin/rescue/*`, X-Admin-Token):
  `struggles` (upsert snapshot → candidates), `generate` (template
  prefill → genmedia → draft asset + ledger row, synchronous),
  `asset/{id}/verdict` (polysemy guard + glyph permanence),
  `item/{id}` (status/strike/anchor/gloss + replace-all senses),
  `export/{item_id}` (approved assets + senses + snapshot — the future
  deck-builder's input).
- **Read-only UI API** (`/ui/api/rescue/*`): items, item detail (with
  server-side canonical prompt fills for the Generate panel), costs
  (month/all-time, by day/provider/format off gen_ledger), formats
  (taxonomy + providers), asset-file streamer (header or ?token=).
- **Dashboard** — new nav section **Rescue Lab** (✚):
  - `/rescue` — cost tiles + spend by provider/format + struggle table
    (fails, strike dots, senses, approved/total assets, per-item spend).
  - `/rescue/item/:id` — item editing, senses editor, per-format asset
    galleries for side-by-side provider compare, approve/reject + note,
    Generate panel with provider dropdown and the estimated cost shown
    before the call.
  - `/rescue/formats` — taxonomy + provider prices.
- **Tests** `tests/test_rescue.py` (23): registry cost math, template
  rules (letter-order text, teach-every-door refusal), approval guard,
  snapshot/senses validation, and a real schema round-trip (idempotent
  double-apply, CHECKs, FK cascade/SET NULL behavior) against an
  ephemeral local Postgres (initdb per run; skips where absent).
  Full suite: 351 green.
- **Docs**: DASHBOARD.md (Rescue Lab section), FEATURES.md, CHANGELOG.md,
  CLAUDE.md mutation-surface note.
- **Seeder** `tools/seed_rescue_pilot.py`: idempotent; created the 9
  pilot items with glosses/anchors/failed sentences from
  `rescue_pilot1/content.json` and the 3 tirado senses from
  `round2.json`; run against prod after deploy (see below).

## URLs

- Dashboard: https://idiomatic-app.onrender.com/rescue
- Item pages: `/rescue/item/<id>` (seeded ids below)
- Formats: https://idiomatic-app.onrender.com/rescue/formats

## Seeded state (prod, 2026-08-05)

All 9 pilot idioms upserted, anchored, set active at strike 1:

| id | lang | idiom | fails (today/14d) | senses |
|----|------|-------|-------------------|--------|
| 1 | es | se desbloquee | 6/6 | 0 |
| 2 | es | está tirado | 3/7 | **3** (en el suelo / baratísimo / facilísimo) |
| 3 | es | dar por terminada | 3/3 | 0 |
| 4 | pt | estava por dentro | 2/9 | 0 |
| 5 | pt | não tem esse negócio de | 2/3 | 0 |
| 6 | pt | afinal de contas | 1/5 | 0 |
| 7 | it | coni d'ombra | 3/4 | 0 |
| 8 | it | andare insieme | 3/3 | 0 |
| 9 | it | giocare in casa | 3/3 | 0 |

One real generation was run as the paid-path smoke test: **asset 1**, a
glyph for está tirado via nano-banana-lite ($0.0336, image/jpeg,
`2/glyph_f30d53a8.jpg`) — a two-color crumpled-coat-thrown-down
pictogram, no text, on-template. It is deliberately left in **draft**
for the user's verdict (approving pins it as the idiom's permanent
glyph). gen_ledger: 1 call, $0.0336 this month; the overview tiles and
by-provider/by-format tables reflect it.

Live checks passed: `/ui/api/rescue/items|item/2|costs|formats` all
correct; item 1's polysemy prompt correctly refuses to fill (0 senses);
the SPA overview, item page (3 doors + glyph image rendered), and
formats page verified in a real browser against prod.

## Deviations from the commission (repo/facts won)

1. **Prices**: the draft's 0.039/0.02 were stale. Official docs
   (ai.google.dev/gemini-api/docs/pricing, checked 2026-08-05) say
   $0.067 (flash-image) and $0.0336 (flash-lite-image) per image at 1K
   standard tier — the registry carries those. 2K/4K cost more and are
   deliberately not offered.
2. **Morphology retry wording**: the commission says the retry prompt
   "in round2.json shows the wording that worked" — round2.json carries
   only the original anatomy prompt, no retry. The letter-order demand
   was authored into the template ("must read cleanly LEFT TO RIGHT in
   strict spelling order, every letter present exactly once…") and a
   test pins it.
3. **Templates in code, not a table**: the commission allowed either;
   they live in `rescue.FORMATS` (same pattern as grammar/curriculum.py
   — the definition versions with the logic that fills it) and reach
   the UI via `/ui/api/rescue/formats`.
4. **Item patch also accepts `gloss`** (superset of the commissioned
   status/strike/anchor/senses — glosses arrive from snapshots and
   needed an edit path).
5. **Seeding status**: the 9 pilot items were set active/strike 1 (not
   left as candidates) — they are the user-approved in-flight cohort.
6. **gen_ledger on failure**: a failed provider call writes no ledger
   row — no image is produced and Gemini does not bill failed image
   requests. The commission's "even if the asset is discarded" is
   honored the way that matters: rejecting or deleting an asset keeps
   its ledger row (SET NULL), so month totals never shrink.
7. `svg` and `sentence_audio` are legal asset formats (schema + export)
   but have no dashboard generation flow — `/admin/rescue/generate`
   refuses them with a pointer. There is currently no upload path for
   manually-authored assets (see open items).

## Open items

- **First real generations**: no images were generated in prod yet —
  every asset should be born through the Generate panel with the user's
  eye on it (pilot-first memory). Suggested first run: mint glyphs for
  the 9 items (~$0.30 with nano-banana-lite), then the strike-1 comics.
- **Manual-asset upload**: svg/sentence_audio rows can only enter via
  SQL today. A small `POST /admin/rescue/asset-upload` (multipart,
  format ∈ manual set) would complete the loop.
- **Struggle snapshot automation**: the AnkiWeb puller (ANKI_STATS_POC)
  still runs off-server by hand; wiring its output to
  `POST /admin/rescue/struggles` on a schedule is the obvious next
  step, explicitly out of scope here.
- **Deck builder**: `/admin/rescue/export/{id}` is the contract; the
  apkg builder (`apkgs.kind='rescue'`) is the next commission.
- **Escalation automation**: strike transitions are manual (the ladder
  is documented on the item page's strike selector); auto-diagnosis
  from revlog grain per RESCUE_PILOT.md is future work.

## Verification trail

- Local: full pytest suite green (351); Playwright E2E against an
  ephemeral Postgres + uvicorn — polysemy 409, glyph-permanence 409,
  video 400, authed image streaming, senses editor, prompt prefill all
  exercised through the real SPA.
- Prod: deploy dep-d9pd5mc9v7es73appfg0 (commit 33a214e) live; seeder
  run against the live API; spot-checks below in "Seeded state".
