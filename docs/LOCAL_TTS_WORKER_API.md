# Local Qwen worker API v1

This is the versioned handoff contract for legacy-estate commission Part C.
The cloud service is a queue and validated clip store only. Synthesis runs on
the Fedora machine against its loopback Qwen3-TTS bridge. This lane never calls
`gemini.synthesize`, ElevenLabs, or Gemini TTS, and it does not depend on (or
change) Render's `TTS_PROVIDER` setting.

The machine-local worker now lives beside `~/llms/qwen3-tts/server/`, outside
this repo. Its one-owner window wrapper cooperatively drains the image lane,
stops only the exact idle ComfyUI unit, runs the queue, unloads Qwen, and then
releases images. No daily service or timer is installed or enabled.

## Authentication and version

All routes are under `/admin/local-tts/v1/` and require:

```text
X-Admin-Token: <ADMIN_TOKEN>
```

Claim responses carry an opaque batch lease. Upload and failure requests also
require:

```text
X-Local-TTS-Lease: <lease_token from claim>
```

The worker must treat contract versions it does not understand as fatal. It
must never turn a local bridge error into a request to any paid provider.

## Pilot workflow

1. Seed the frozen pilot. This is safe to repeat:

   ```bash
   curl -fsS -X POST \
     -H "X-Admin-Token: ${IDIOMATIC_ADMIN_TOKEN:?}" \
     "${IDIOMATIC_BASE_URL:?}/admin/local-tts/v1/exercises2/seed-pilot"
   ```

   The seed is exactly 30 existing Exercises2 notes: three `connecting` and
   three `conditionals` notes in each of `de`, `es`, `fr`, `it`, and `pt`.
   Each note creates an `answer` and an `example` job, for 60 clips total.
   Stable note ids are frozen in `idiomatic/local_tts.py::PILOT_NOTE_IDS`.

2. Claim a small batch:

   ```http
   POST /admin/local-tts/v1/jobs/claim
   Content-Type: application/json

   {"worker_id":"fedora-qwen","limit":4,"lease_seconds":900}
   ```

   `limit` is 1–16. `lease_seconds` is 60–3600. A response has this shape:

   ```json
   {
     "contract_version": 1,
     "lease_token": "opaque-batch-token",
     "jobs": [
       {
         "id": 123,
         "contract_version": 1,
         "source_kind": "exercises2",
         "source_key": "exercises2:v1:es:connecting:esc01:answer",
         "note_key": "es:connecting:esc01",
         "clip_kind": "answer",
         "lang": "es",
         "text": "Sea como fuere",
         "voice_version": "qwen3-tts-clone-v1",
         "content_hash": "<64 lowercase hex>",
         "staged_path": "grammar/exercises2/local_qwen/v1/es/<server name>.mp3",
         "is_pilot": true,
         "attempts": 1,
         "lease_expires_at": "<timestamp>",
         "upload_path": "/admin/local-tts/v1/jobs/123/upload",
         "failure_path": "/admin/local-tts/v1/jobs/123/fail"
       }
     ]
   }
   ```

   `staged_path` is informational. The worker must not create or choose a
   server path; the upload endpoint resolves it from the leased DB row.

3. For each job, call the bridge locally. The bridge request is:

   ```http
   POST http://127.0.0.1:8355/synth
   Authorization: Bearer <box-side QWEN_TTS_TOKEN>
   Content-Type: application/json

   {"text":"<job.text>","lang":"<job.lang>"}
   ```

   Keep generation serial unless the bridge contract later says otherwise.
   The bridge's etiquette `503` means defer, not fail over.

4. Upload the returned MP3 before the lease expires:

   ```bash
   curl -fsS -X POST \
     -H "X-Admin-Token: ${IDIOMATIC_ADMIN_TOKEN:?}" \
     -H "X-Local-TTS-Lease: ${LEASE_TOKEN:?}" \
     -H "Content-Type: audio/mpeg" \
     --data-binary "@${CLIP_PATH:?}" \
     "${IDIOMATIC_BASE_URL:?}/admin/local-tts/v1/jobs/${JOB_ID:?}/upload"
   ```

   The server accepts 1,000–8,000,000 bytes, validates ID3/MPEG structure,
   checks content/path hashes, writes a same-directory temporary file, fsyncs,
   and atomically replaces the canonical destination. It then completes the
   job only if the lease is still current. A stale lease returns `409`.

5. On local failure or bridge contention, release the lease back to the queue:

   ```http
   POST /admin/local-tts/v1/jobs/123/fail
   X-Local-TTS-Lease: <lease_token>
   Content-Type: application/json

   {"error":"bridge busy (503)","requeue":true}
   ```

   `requeue` defaults to `true`. `false` is an explicit operator quarantine;
   ordinary generation failures must remain queued for the next local window.
   If a worker disappears, a later claim automatically reclaims its expired
   lease with `FOR UPDATE SKIP LOCKED`.

6. Inspect progress:

   ```http
   GET /admin/local-tts/v1/status
   ```

   The response reports total and pilot counts by `queued|leased|completed|
   failed`, expired leases, and whether the full-corpus owner gate is open.

7. When all 60 clips are complete, build the listening artifact:

   ```http
   POST /admin/local-tts/v1/exercises2/build-pilot
   ```

   The build refuses a single missing, stale, noncanonical, invalid, or
   checksum-mismatched clip. It produces one mixed-language 30-note / 60-card
   APKG using the existing Exercises2 model id, note GUID formula, deck names,
   and deck ids. It is published as rolling kind `exercises2_pilot`; because
   `apkgs.lang` is one delivery-routing value, the mixed artifact rides the
   normal Spanish agent lane (`lang=es`). Its decks themselves retain their
   correct five language roots.

The owner listens to this APKG before any full seed or rebuild.

## Full corpus gate

Bulk routes are closed by default. Only after the owner approves the pilot,
set this separate config flag:

```text
LOCAL_TTS_EXERCISES2_PILOT_APPROVED=true
```

Then these explicit admin calls become available:

```http
POST /admin/local-tts/v1/exercises2/seed-full
POST /admin/local-tts/v1/exercises2/rebuild?lang=de
```

The first seeds all current Exercises2 source files idempotently. The second
replaces that language's ordinary `kind=exercises2` rolling APKG, but only
after every expected current-content clip has been completed locally. Neither
route synthesizes on the server. Leave the approval flag false until the
listening verdict.

## Idempotence and edits

`source_key` is durable clip identity. `content_hash` covers contract version,
language, frozen voice version, and exact text. Re-seeding unchanged content
preserves completed state and leases. An authored text/voice/contract change
keeps the source identity but generates a new canonical path and resets the job
to `queued`, clearing its old completion metadata. Old clip files become inert:
strict rebuilds only accept the current row/hash/path.

## Benchmark result

The first unscheduled pilot completed 60/60 clips and shipped APKG 1615. Its
stable segment measured 542 end-to-end clips/hour; use 1,000 clips (500
two-clip notes) as the conservative two-hour capacity. The complete metrics,
safety deferrals, media validation, and still-closed owner gates are recorded
in
[`research/legacy_estate/LOCAL_QWEN_PILOT_BENCHMARK.md`](research/legacy_estate/LOCAL_QWEN_PILOT_BENCHMARK.md).
Do not install or enable a timer until the owner approves the listening pilot
and final GPU split.
