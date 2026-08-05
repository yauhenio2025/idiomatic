# COMMISSION: Rescue Lab — experiment tracker, asset explorer & generation dashboard

**For:** a fresh Claude Code session working in this repo (idiomatic).
**Commissioned:** 2026-08-05, after the user approved the rescue-format
experiments ("your ideas are brilliant and we need to incorporate them")
and asked for "a page in idiomatic where we track this stuff and explore
assets, calculate costs, and switch across image models — basically a
dashboard/frontend for this."

## Background (read first)

- `docs/research/RESCUE_PILOT.md` — what the rescue initiative is, the
  round-1/round-2 format verdicts, and the repeat-failure escalation
  ladder. This commission builds the OPERATING SURFACE for that system.
- `docs/research/rescue_pilot1/content.json` + `round2.json` — the
  actual pilot content: 9 struggle idioms with anchors/sentences/
  exercises, and the format taxonomy WITH the exact generation prompts
  that produced user-approved images. These prompts are the seed
  templates for the dashboard's generate flow.
- `docs/research/ANKI_STATS_POC.md` — where struggle data comes from.
- `DASHBOARD.md` + `idiomatic/ui_api.py` + `frontend/` — the existing
  dashboard this must extend (same stack, same auth, same visual
  conventions).

User verdicts to honor as hard constraints:
1. Formats in: comics, word-centered images (contrast, polysemy map,
   morphology anatomy, iconic poster, glyphs), SVG diagrams, sentences,
   cloze/production exercises. **Video is OUT — never offer it.**
2. **Polysemy rule:** a polysemy-map asset is incomplete without a
   gloss + micro-example per sense ("teach every door, don't just
   label it") — enforce at the data level, not as a convention.
3. **Morphology rule:** prompts for word-as-object images must demand
   strict left-to-right letter order (first render scrambled it;
   the retry prompt in round2.json shows the wording that worked).
4. One permanent **glyph** per rescued idiom, reused on every future
   card/asset of that idiom.

## Deliverables

### 1. Schema (append to `db/schema.sql` — idempotent, applied on boot)

- `rescue_items`: id, lang, idiom, gloss, anchor, status
  (candidate|active|retired), strike (1..3), glyph_asset_id (nullable
  FK), struggle_snapshot JSONB (fails_today/fails_14d/sentences failed,
  as uploaded), created_at, updated_at.
- `rescue_assets`: id, item_id FK, format (comic|contrast|polysemy_map|
  anatomy|poster|glyph|svg|sentence_audio), provider, model, prompt
  TEXT, params JSONB, file_path (under `/data/rescue_assets/`),
  mime, cost_usd NUMERIC, status (draft|approved|rejected),
  verdict_note, created_at.
- `rescue_senses`: id, item_id FK, label, gloss, example_tl,
  example_en, ord — REQUIRED rows for any item with a polysemy asset
  (enforce in the build/approve endpoint: refuse to approve a
  polysemy_map asset for an item with <2 senses).
- `gen_ledger`: id, provider, model, kind (image|tts), units NUMERIC,
  unit_kind (image|char), cost_usd, item_id nullable, asset_id
  nullable, created_at — every paid generation call writes here even
  if the asset is discarded, so cost accounting is complete.

### 2. Provider abstraction — `idiomatic/genmedia.py`

A small registry so image models are switchable per call:

```python
PROVIDERS = {
  "nano-banana":      {"api": "gemini", "model": "gemini-3.1-flash-image",      "usd_per_image": 0.039},
  "nano-banana-lite": {"api": "gemini", "model": "gemini-3.1-flash-lite-image", "usd_per_image": 0.02},
}
def generate_image(provider_key, prompt, *, params=None) -> (bytes, cost_usd)
```

- Gemini-family goes through the existing `GEMINI_API_KEY` Render env
  (pattern in `idiomatic/gemini.py::generate_image` — reuse/extend it,
  including its retry + safety handling).
- VERIFY current per-image pricing from official docs before hardcoding
  the numbers above; keep the table in one place, cost written to
  `gen_ledger` at call time from the table.
- Design the registry so adding a non-Gemini provider later is one
  dict entry + one adapter function — but do NOT integrate other
  providers now. NO video providers, period.

### 3. Admin endpoints (`idiomatic/api.py`, `X-Admin-Token`, follow the existing style)

- `POST /admin/rescue/struggles` — upload a struggle snapshot
  (JSON list of {lang, idiom, gloss, fails_today, fails_14d,
  failed_sentences[]}); upserts `rescue_items` as candidates. (The
  snapshot is computed off-server from the AnkiWeb pull — see POC doc;
  a server-side puller is explicitly OUT of scope here.)
- `POST /admin/rescue/generate` — {item_id, format, provider, prompt}
  → calls genmedia, stages the file, inserts `rescue_assets` (draft) +
  `gen_ledger`. Prompt defaults come from format templates seeded from
  `rescue_pilot1/round2.json` (store templates in a `rescue_formats`
  table or a code constant with per-format placeholder docs — your
  call, document it).
- `POST /admin/rescue/asset/{id}/verdict` — {status: approved|rejected,
  note}. Enforce the polysemy rule here.
- `POST /admin/rescue/item/{id}` — patch status/strike/anchor/senses.
- `GET /admin/rescue/export/{item_id}` — bundle an item's approved
  assets + senses + sentences as JSON (the future deck-builder's input;
  building the apkg itself is NOT in this commission).

### 4. Read-only UI API (`idiomatic/ui_api.py`)

- `/ui/api/rescue/items` (+ filters lang/status), `/ui/api/rescue/item/{id}`
  (with assets + senses), `/ui/api/rescue/costs` (aggregates: by day,
  by provider, by format, running month total), and an asset file
  stream `/ui/api/rescue/asset-file/{id}` (same pattern as the
  staged-audio streamer).

### 5. Frontend (`frontend/`, new route `/rescue` — "Rescue Lab")

Extend the existing React SPA (built in the Dockerfile node stage);
match the current dashboard's look and conventions:

- **Overview**: struggle-item table (lang, idiom, fails, strike,
  status, #assets, spend) + cost tiles (this month total, by provider,
  by format). Cost numbers are load-bearing — the user asked for them
  explicitly.
- **Item page**: senses editor (add/edit gloss+examples — the polysemy
  rule lives here), assets gallery grouped by format with side-by-side
  compare across providers/models, per-asset approve/reject + note,
  and a Generate panel: format picker (NO video), **provider/model
  dropdown**, prompt textarea prefilled from the format template with
  the item's fields substituted, estimated cost shown BEFORE the call.
- **Formats page**: the format taxonomy rendered from the templates
  store (name, when-to-use, the design rules above, template prompt).
- Keep it read-only except through the admin endpoints; the dashboard
  mutation-surface exception pattern is established by /grammar —
  follow how `frontend/` wires admin-token calls there.

### 6. Tests + docs

- Deterministic tests (no network) for: schema round-trip of the new
  tables, provider registry cost math, the polysemy-approval guard,
  and struggle-snapshot upsert. Follow `tests/` conventions; keep the
  suite green (`.venv/bin/python -m pytest tests/ -q`).
- Update `docs/FEATURES.md`, `docs/CHANGELOG.md`, `DASHBOARD.md`
  (Rescue Lab section), per repo rules in CLAUDE.md.

## Seeding

After the endpoints exist, seed from `docs/research/rescue_pilot1/`:
create the 9 items (with senses for está tirado from round2.json) and
register the format templates. The pilot's generated binaries live in
a session scratchpad, not the repo — do NOT try to import them; fresh
assets will be generated through the dashboard (cheap), and the pilot
JSONs carry every prompt needed to reproduce them.

## Working agreement

- Commit + push frequently (Render auto-deploys `main` in ~6 min;
  the API lifespan applies schema.sql on boot — that IS the migration).
- No secrets in the repo (it is PUBLIC). Providers read keys from env.
- Verify against the live dashboard after deploy; the admin token is
  in the Render env (endpoints 503 while unset locally — use tests
  locally, live checks after deploy).
- If something here conflicts with what you find in the repo, the repo
  and CLAUDE.md win; note the deviation in your handoff.
- Write a short handoff memo at `docs/research/RESCUE_LAB_HANDOFF.md`
  when done: what shipped, URLs, deviations, open items.
