# Commission: Grammar section in the dashboard + organized deck/curriculum structure

> Written 2026-07-31 for a FRESH session to execute. Read this whole file
> plus: CLAUDE.md (grammar section), docs/GRAMMAR_STRATEGY.md (§4, §8),
> DASHBOARD.md, HANDOFF_FRONTEND.md. The grammar pipeline code lives in
> `idiomatic/grammar/`; dashboard API in `idiomatic/ui_api.py`; React SPA
> in `frontend/src/`.

## Why

Five grammar decks are live (es 222 / de 50 / fr 83 / it 84 / pt 82
cards, 42 units) but (a) each deck is FLAT — units exist only as tags —
and (b) the dashboard has NO grammar surface at all; unit stats and
reject diagnostics are raw admin JSON. The user wants: subdecks per
topic cluster, a per-language curriculum view ("lessons"), per-unit
sizing that will later follow mastery, and generation controls in the UI
instead of curl.

## Non-negotiable constraints (violating these breaks user data)

1. **The note model is FROZEN** (`grammar/apkg.py` MODEL_ID
   1_820_130_001, 14 fields). Never add/remove/reorder fields or
   templates — that forces a full one-way Anki sync. Extra2..Extra4 are
   the only expansion room.
2. **GUIDs are sacred**: `sha1("idiomatic-grammar::{lang}::{item_id}")`.
   Deck reorganization must NOT touch GUIDs — scheduling history dies
   otherwise.
3. **Re-importing an apkg does NOT move existing cards** between decks.
   Subdeck migration of already-imported cards must happen client-side
   in the add-on (it already has a Reorganize step for video decks —
   extend that pattern; cards carry their unit key as a tag, which is
   the join key).
4. **Never git-push while a generation run is live** (push → Render
   redeploy → kills the in-flight run). Check `/admin/grammar-status`
   first.
5. Dashboard auth: the SPA already holds the admin token
   (X-Admin-Token) — new write endpoints can reuse `authed_admin`.
   Grammar mutations from the UI are acceptable (the "read-only
   dashboard" rule in DASHBOard.md predates this commission and is
   hereby amended for the grammar section only).

## Workstream A — deck taxonomy: subdecks per cluster

Target Anki structure (`::` nests decks; names are user-visible):

    Idiomatic Grammar ES::1 Tiempos          ← es_pres_irreg, es_preterito,
                                                es_imperfecto, es_futuro,
                                                es_condicional, es_perfecto
    Idiomatic Grammar ES::2 Subjuntivo       ← es_subj_pres, es_subj_imp
    Idiomatic Grammar ES::3 Condicionales    ← es_cond_perf, es_plusc_subj
    Idiomatic Grammar ES::4 Imperativo       ← es_cmd_tu, es_cmd_usted, es_cmd_neg
    Idiomatic Grammar ES::5 Pronombres       ← es_clitics_dir/_ind/_selo
    Idiomatic Grammar ES::6 Preposiciones    ← es_por_para, es_verb_prep
    Idiomatic Grammar DE::1 Genus            ← de_gender
    Idiomatic Grammar DE::2 Präpositionen    ← de_prep_fest, de_prep_wechsel
    Idiomatic Grammar FR::1 Temps            ← fr_present_irreguliers,
                                                fr_passe_compose, fr_imparfait,
                                                fr_futur_simple
    Idiomatic Grammar FR::2 Conditionnel     ← fr_conditionnel_present
    Idiomatic Grammar FR::3 Subjonctif       ← fr_subjonctif_present,
                                                fr_subjonctif_conjonctions
    Idiomatic Grammar IT::1 Tempi            ← it_presente_irregolari,
                                                it_passato_prossimo, it_imperfetto,
                                                it_futuro_semplice, it_passato_remoto
    Idiomatic Grammar IT::2 Condizionale     ← it_condizionale_presente
    Idiomatic Grammar IT::3 Congiuntivo      ← it_congiuntivo_presente
    Idiomatic Grammar PT::1 Tempos           ← pt_presente_irregulares,
                                                pt_preterito_perfeito,
                                                pt_preterito_imperfeito,
                                                pt_futuro_simples
    Idiomatic Grammar PT::2 Condicional      ← pt_condicional_presente
    Idiomatic Grammar PT::3 Subjuntivo       ← pt_subjuntivo_presente,
                                                pt_futuro_subjuntivo

Implementation:
- Add `cluster: str` to `curriculum.Topic` + the units_fip.json schema;
  cluster strings above are FINAL (numbered so Anki sorts them).
- `grammar/apkg.py::build_grammar_apkg`: one `genanki.Deck` per cluster
  present in the item set (`Idiomatic Grammar {LANG}::{cluster}`), stable
  deck_ids hashed from the full deck name. New/updated cards then import
  into the right subdeck.
- Add-on (`idiomatic_puller/__init__.py`, local path in CLAUDE.md): a
  one-shot "Reorganize grammar decks" step — for each card whose note
  type is `Idiomatic Grammar Drill v1`, read its unit tag, look up the
  cluster (ship the tag→deckname map to the add-on via a new
  `/admin/grammar-deckmap` endpoint or embed in cleanup.json-style
  config), `col.set_deck(card_ids, deck_id)`. Runs on profile open,
  marks itself done (same pattern as cleanup.json).
- FSRS: subdecks inherit the parent preset — remind the user once to
  keep the grammar preset on the PARENT deck only.

## Workstream B — curriculum model in the DB

New table `grammar_units` (schema.sql, idempotent):

    key TEXT PRIMARY KEY, lang TEXT, cluster TEXT, label TEXT,
    symbol TEXT, status TEXT DEFAULT 'active',   -- active|maintenance|planned
    target_size INT DEFAULT 12,                  -- desired verified-card count
    sort_order INT, notes TEXT, updated_at TIMESTAMPTZ

- Seed from `curriculum.topics_for()` on boot (INSERT … ON CONFLICT DO
  NOTHING) so code remains the definition source and the DB carries the
  MUTABLE state (status, target_size, notes).
- `target_size` is the "some subdecks longer than others" knob: a
  "Top up to target" action generates `target_size - current_verified`
  items for a unit. For now the user sets targets by hand in the UI;
  after Wave 5 (telemetry) the planner will adjust them from mastery
  data — design the column, not the automation.
- `status='planned'` units (empty, no generation yet) let the curriculum
  tree show what's NEXT per language (pull candidate planned units from
  GRAMMAR_STRATEGY.md §3 taxonomy, e.g. es ser/estar, de adjective
  endings, fr pronoms y/en, it clitics ci/ne, pt clitic placement).

## Workstream C — dashboard grammar section

New top-nav entry **Grammar** with two levels:

1. **/grammar** — per-language curriculum tree. For each language:
   cluster → unit rows showing: label+symbol, verified count vs
   target_size (progress bar), reject count + rate, last batch time,
   status chip, buttons [Top up] [Rebuild deck] (rebuild once per lang,
   in the header row). Header: deck card count, last apkg id/size/ack
   state (join `apkgs` kind='grammar' + agent_acks like Delivery page).
2. **/grammar/unit/:key** — unit detail: the generation guidance text,
   all verified items as rendered mini-cards (front sentence with blank
   highlighted, reveal shows answer/gloss/why, audio play button), and
   the REJECTS with reasons (this is the LLM-error-rate diagnostic that
   has caught every pipeline bug so far — make it first-class).

Endpoints to add (`ui_api.py` for reads, `api.py` for actions):
- GET /ui/api/grammar/overview → all langs, clusters, units w/ counts,
  targets, last batches, deck+ack info.
- GET /ui/api/grammar/units/{key} → unit meta + items (verified) +
  rejects (id, sentence, answer, reason, batch, created_at).
- GET /ui/api/grammar/audio/{lang}/{filename} → stream from
  /data/staged_audio/grammar/{lang}/ (mirror the existing audio route;
  sanitize filename).
- POST /admin/grammar-unit/{key} {target_size?, status?, notes?}.
- POST /admin/grammar-generate + /admin/grammar-rebuild + GET
  /admin/grammar-status ALREADY EXIST — the UI wraps them (poll status
  while a run is live; disable buttons when running=true).
- POST /admin/grammar-retire-item/{id} (status='retired') for killing a
  bad card from the UI; a following rebuild drops it from the deck (its
  note stays in Anki until a cleanup.json purge — acceptable v1; note it
  in the UI).

Frontend conventions: follow HANDOFF_FRONTEND.md and existing pages
(api.ts fetch wrapper, hooks.ts polling, format.ts). Reuse the audio
player component from Expressions.

## Acceptance checklist

- [ ] New cards land in correct subdecks on a fresh generation+import.
- [ ] Add-on reorganize moves ALL existing grammar cards into subdecks
      with review history intact (verify: intervals unchanged after move).
- [ ] /grammar renders 5 languages with live counts; Top up runs a
      generation and the tree refreshes when status flips to done.
- [ ] Unit detail plays audio, shows rejects with reasons.
- [ ] target_size editable; "Top up" honors it.
- [ ] `uv run pytest` green; no changes to MODEL_ID/fields/templates;
      GUIDs of existing items unchanged (test exists).
- [ ] docs: DASHBOARD.md + FEATURES.md + CHANGELOG.md updated; Wave 6
      checked off in GRAMMAR_STRATEGY.md §8.

## Explicitly OUT of scope

- Telemetry/revlog push + planner (Wave 5 — separate commission).
- German adjective endings/verb core, new languages, audio-front (beep)
  cards.
- Any note-model change. Any renaming of existing unit keys (they're
  tags on live cards).

## Cost/effort note

Pure code + one deploy; no LLM spend except Top-up runs the user
triggers. Bulk-ish subtasks suitable for codex per the delegation
directive (CLAUDE.md): the add-on reorganize function, the React table
components, endpoint boilerplate — with the executing session reviewing.
