# Local Qwen estate-voicing pilot and benchmark

Status: **pilot delivered; owner listening verdict pending; bulk gate closed**.

On 2026-08-08 the versioned local-only lane voiced the frozen 30-note
Exercises2 slice: three CONNECTING and three CONDITIONALS notes in each of DE,
ES, FR, IT, and PT. Each note has an answer clip and a full-example clip, so
the run produced 60 clips. Production reports 60 completed jobs, zero queued,
leased, failed, or expired jobs. The strict builder accepted all 60 current
hash/path/checksum records and published APKG **1615** as
`exercises2_pilot`: 30 notes, 60 cards, existing model `1820150001`, existing
GUIDs and estate deck IDs. It rides the normal ES delivery lane but contains
the correct five language-root decks. The normal `fedora-laptop` agent imported
it and acknowledged `ok` on its first attempt at 12:03:39 +08.

The owner must listen to that APKG before `LOCAL_TTS_EXERCISES2_PILOT_APPROVED`
may become true. It remains false. Render's `TTS_PROVIDER=elevenlabs` pin was
not changed; neither ElevenLabs nor Gemini is callable from this queue worker.

## Measured result

The mixed corpus contained 6,467 characters and 382.2 seconds of audio. All
60 retained artifacts probe as MP3, 24 kHz, mono. They total 3.09 MB. The
machine-local audio work area remains gitignored; its filename+content
manifest hashes to
`268d07ce5bea5160122785e1b3afb4e68f4b52380b65be8b0dd1b6645fe3021a`.

Across the complete diagnostic run, generation took 272.0 seconds and active
worker wall time was 429.883 seconds: **794 clips/hour at the model** and **502
clips/hour end to end**, including leases, per-clip Render uploads, cold loads,
and two deliberate safety deferrals. The final patched, contention-free
34-clip segment measured **925 generation clips/hour** and **542 end-to-end
clips/hour**. Warm per-language generation medians were 4.1--4.9 seconds; the
DE/ES/FR p95 values include each restarted window's cold model load.

Decoded loudness averaged -16.92 LUFS. One very short French answer
(`frc002`, job 25) measured -24.22 LUFS despite a -1.5 dB peak and only 0.23
seconds of trailing silence; it is not a silence placeholder, but the owner
should listen to that card particularly closely. Maximum decoded true peak
was -1.09 dBTP. Exact metrics are in
[`local_qwen_pilot_benchmark.json`](local_qwen_pilot_benchmark.json).

## Safety findings executed during the run

The first admission probe refused to load Qwen while idle ComfyUI still held
about 19 GiB RAM and left only 8.2 GiB available. The managed window then
waited for image runners and both Comfy queues, stopped only the exact idle
`qwen-comfy.service`, and verified at least 10 GiB available before starting.

Two later boundaries exercised durable recovery rather than hiding problems:

- A legacy guessed-VRAM heuristic mistook Qwen's own allocation for another
  workload. The untouched tail requeued, Qwen unloaded, and the heuristic was
  replaced with driver-reported per-process compute memory.
- The hottest CPU sensor reached 86 C against the 85 C gate. The untouched
  tail requeued, Qwen unloaded, and the host cooled to 75.9 C before resuming.
  The between-clip gate now waits and rechecks the full thermal state for up to
  two minutes instead of racing two separate readings.

The local bridge now rechecks contention between clips, immediately unloads on
a mid-batch deferral, keeps only one Qwen model resident, checks RAM, memory
pressure, CPU load/temperature and foreign GPU-process memory, fails closed on
missing telemetry, counts queued clips rather than batch HTTP requests, and
does not stop Ollama or another process as an admission remediation.

The image lane now pauses between expressions, variations, and QA repair
items. The old forceful `pkill`/Comfy `/interrupt` morning stop was replaced by
a cooperative marker. A singleton `flock` plus an unguessable owner token owns
the whole TTS lifecycle: drain image work, stop exact idle Comfy, run the
worker, verify bridge queue zero, authenticated Qwen unload, then release the
marker. A failed resume leaves the marker in place rather than allowing two GPU
owners. These are machine-local files beside the bridge/miner, not repository
deployment code.

## GPU-window proposal — not activated

At the stable end-to-end rate, a two-hour reservation yields about 1,084
clips, or 542 Exercises2 notes at two clips per note. Use **1,000 clips / 500
notes per window** as the conservative planning number. The recent image-miner
rate was about 43 images/hour, so a full two-hour reservation trades roughly
86 images/day. Opportunistic idle runs can reduce that cost.

The proposed 09:00--11:00 Asia/Singapore split remains technically viable,
with early release when the queue empties, but no service or timer was created
or enabled. The owner must approve both the listening pilot and the daily GPU
tradeoff before bulk seeding or scheduling.
