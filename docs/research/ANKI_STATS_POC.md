# Anki study-data POC (2026-08-05) — VERIFIED WORKING

Goal: tap the user's per-card Anki review data (iPad study sessions,
synced via AnkiWeb) so idiomatic can adapt generation to what they
actually struggle with. Status: **proof of concept succeeded end to
end**; no production code yet.

## What was proven

1. **Headless AnkiWeb pull works.** The desktop collection is stale
   (autoSync fires only on profile open/close and the user leaves Anki
   open permanently for the add-on). But the sync key in
   `prefs21.db` (pickled profile dict, keys `syncKey` +
   `currentSyncUrl`) plus the official `anki` pip library (26.08)
   gives a clean download-only sync into a scratch directory —
   no GUI, no touching the live collection:

   ```python
   from anki.collection import Collection
   from anki.sync import SyncAuth
   col = Collection(scratch_path)                # fresh empty collection
   auth = SyncAuth(hkey=..., endpoint="https://sync31.ankiweb.net/")
   out = col.sync_collection(auth, sync_media=False)   # -> FULL_DOWNLOAD
   col.close_for_full_sync()
   col.full_upload_or_download(auth=auth, server_usn=out.server_media_usn,
                               upload=False)     # upload=False is load-bearing
   ```

   Result contained the iPad session from 40 minutes earlier
   (61,119 revlog rows; desktop copy was ~2,100 behind).
   Note: the library reopens the collection itself after the full
   download — don't call `col.reopen()`. Reading the result with raw
   sqlite needs a stand-in `unicase` collation registered.

2. **The grain is everything we hoped for.** `revlog` has per-review:
   timestamp (ms), button pressed (1=Again..4=Easy), time-on-card
   (ms, capped 60s), interval before/after. Joins to
   cards→notes→decks give language, deck, and full card content.
   Example day: 2026-08-05 = 287 reviews, ~60 min, es/pt/it.

3. **Struggle detection is trivial and high-signal.** "≥3 Agains in
   14 days" surfaces exactly the remediation targets the user wants
   (top offender: a German card failed 13 of 15 views).

4. **Round-trip to our DB is exact, not fuzzy.** pool.py note guids
   are deterministic — verified byte-for-byte against live notes:
   `sha1("yt-pool::" + _norm(idiom) + "::" + _norm(sentence))[:16]`
   (pool_expr; other kinds per pool.py/apkg.py `_guid`). So
   revlog → note guid → `expressions` / `expression_examples` row.
   Verified live: struggling IT card → `expressions.id=457`
   ("andare per mare"), 6 examples, source video present.

## Caveats discovered

- **Anki is a superset of the DB.** A struggling PT card ("apelou
  para", Nicolelis video) matched the guid recipe but its expression
  and video are gone server-side (purge/regeneration; imports never
  delete). The recommender must tolerate orphans — card fields carry
  enough content (idiom, gloss, 6 sentence pairs, source) to generate
  remediation without the DB row.
  **RESOLVED 2026-08-05 (user directive):** censused 33,012 YT-pipeline
  notes → 8,217 orphans; the 4,752 studied ones now live in the
  `adopted_notes` table (full fields + reps/lapses/last_review, via
  `POST /admin/adopt-orphans`); the 3,465 never-studied ones were
  deleted from the collection via cleanup.json. `GET /admin/anki-guids`
  exports the current per-kind guid catalog for future re-runs. The
  remediation pipeline should read expressions ∪ adopted_notes.
  Old-generation models (Audio Phrase v3, Idiom Card v2/v3, Cloud Card
  v1) were included; the grammar family (Drill/Exercises/Podcast/
  Translation) is curated content and stays out of orphan logic.
- **Desktop staleness SOLVED 2026-08-05:** the idiomatic_puller add-on
  now auto-syncs (after imports + every 30 min, `sync_status`-gated so
  full-sync conflicts are never auto-answered), and Anki autostarts at
  login. The AnkiWeb pull recipe above stays the right read path for
  analytics — it needs no desktop at all.
- **Deck names are not a reliable key.** The user reorganized some
  idiomatic decks into their own `Languages::<Lang>::…` hierarchy
  (de/es/pt) while it stayed under `Idiomatic::…`. Use tags
  (`youtube`, lang code, `fluency-pool`) and guid, never deck name.
- Two AnkiWeb accounts exist; the **evgeny@the-syllabus.com** profile
  is where all current study happens (grammar + these reviews). The
  gmail+2 profile's revlog is dormant (last review 2026-04-06).

## Security

The sync key (hkey) is a full-access credential to the AnkiWeb
account. It lives in the local `prefs21.db` and MUST NEVER be
committed — this repo is public. Productionizing means putting it in
the Render env (e.g. `ANKIWEB_HKEY` + `ANKIWEB_ENDPOINT`) like the
other credentials. `upload=False` always; a scratch collection must
never be pushed to AnkiWeb.

## Obvious next steps (not started)

1. Server-side puller: daily (or per-request) full download on Render
   (~80 MB, fine at this scale), diff `revlog` by max(id) watermark
   into a new `anki_reviews` table (revlog id, guid, lang, ease,
   time_ms, ivl before/after).
2. Struggle list endpoint + dashboard page.
3. Remediation generator: for persistent lapses, generate fresh
   examples/mnemonics/audio (respecting pilot-first: ONE pilot for
   user approval before batching).
