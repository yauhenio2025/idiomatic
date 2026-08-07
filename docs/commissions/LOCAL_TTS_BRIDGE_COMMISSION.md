# Local TTS bridge — build commission (fresh Fable session)

> Goal: make locally-hosted **Qwen3-TTS the DEFAULT TTS provider** for the
> whole idiomatic pipeline, with ElevenLabs demoted to automatic fallback
> (used only when this machine is off/unreachable) and Gemini TTS as the
> last-resort fallback it already is. User verdict 2026-08-07 after A/B
> listening: "the quality is really really great… we switch to this as
> our default provider."

## What exists (verified working — do not rebuild)

- **Runtime**: `~/llms/qwen3-tts/` (venv, `qwen_tts` package). Models on
  the models partition: `Qwen/Qwen3-TTS-12Hz-1.7B-Base` (voice cloning:
  `generate_voice_clone(text, language, ref_audio, ref_text)`) and
  `…-CustomVoice` (premades via `generate_custom_voice(text, language,
  speaker)`; speakers: aiden dylan eric ono_anna ryan serena sohee
  uncle_fu vivian). Apache-2.0. All idiomatic languages + zh.
- **Measured**: 3–5 s per sentence, ~4.5 GB VRAM, bf16, cuda:0. Clone of
  a per-language ElevenLabs deck voice from ONE ~8 s card mp3 worked
  first try in all five languages.
- **Quality baselines the user approved** (keep these reproducible):
  `/srv/ai-models/outputs/tts-samples/comparison/index.html` (5 langs,
  EL original vs cloned-voice Qwen, same sentences) and `mandarin.html`
  (HSK-3, EL vs native speaker `vivian`).
- **Server-side sampler**: `POST /admin/tts-sample` (api.py) renders
  arbitrary text through the production ElevenLabs path — use it for
  future bake-offs.

## Read first

CLAUDE.md (TTS history: ElevenLabs primary since 2026-07-27, Gemini
fallback, silence-marker healing, -16 LUFS norm); idiomatic/gemini.py
(`synthesize()` = the single choke point all builders call;
`ELEVEN_LANG_VOICE`, `_ELEVEN_LANG_CODES`, silence_marker protocol);
idiomatic/pipeline/audio.py + pool.py + grammar builders (batch volumes:
hundreds of clips per rebuild); settings.py (`TTS_PROVIDER` switch).

## Architecture to build

1. **Local TTS service** on the Fedora box (`~/llms/qwen3-tts/server/`):
   FastAPI + uvicorn on a fixed port, bearer-token auth (generate a
   token; store box-side + Render env). Endpoints: `/health` (models
   NOT loaded → still healthy; reports GPU/temp/queue), `/synth`
   (text, lang, voice spec → mp3 bytes), `/synth-batch` (array in, zip
   or NDJSON out — the pool rebuilds are bursts of hundreds).
   - Lazy model load, auto-UNLOAD after N min idle (VRAM/RAM hygiene —
     this box also renders images; 16 GB VRAM total).
   - Serialize generation (one at a time); queue with backpressure.
   - **Voice continuity**: per-language voice = CLONE of the current
     ElevenLabs deck voice. Build a frozen reference kit
     (`refs/<lang>.mp3` + `refs/<lang>.txt`, one clean existing card
     clip each, committed to the box not git) so every clip matches the
     decks' established voices. zh uses native premades (user has
     heard vivian; offer dylan/serena/uncle_fu as config).
   - Output parity: mp3, loudness-normalized to −16 LUFS like the
     current path (ffmpeg post-step), same silence-marker behavior on
     failure so healing keeps working.

2. **Load/thermal etiquette** (the user's explicit constraint — this
   box runs many AI workloads: ComfyUI image renders on :8199, codex
   sessions, Ollama, other Fable sessions):
   - Before ACCEPTING a batch: check `nvidia-smi` (VRAM headroom,
     temperature), CPU load, ComfyUI `/queue` (busy = defer), `ollama
     ps`. Single sentences may run anytime (4.5 GB fits beside most
     things); BATCHES wait for job boundaries.
   - Policy on other AI processes: prefer WAITING over killing. Allowed
     interventions: `ollama stop <model>` (idle-unload) and ComfyUI
     `/free` — both non-destructive. NEVER kill an actively sampling
     render or another session's process mid-job (this session's
     history: two GPU-collision incidents taught the safe-boundary
     rule). If contention persists, return 503 + Retry-After; the
     server-side caller falls back to ElevenLabs for that batch.
   - Thermal guard: skip/pause batch work while CPU Tccd > ~85°C or GPU
     > ~83°C (`/sys/class/hwmon`, nvidia-smi); resume below.
   - systemd USER service (autostart on login, restart on crash) + a
     small journal; no sudo required for any of this.

3. **Reachability from Render** (worker + cron call TTS via
   gemini.synthesize on Render — 127.0.0.1 is unreachable):
   - Evaluate: Tailscale (userspace client inside the Render container,
     auth via TS_AUTHKEY env — known pattern) vs cloudflared tunnel.
     Pick one, justify briefly, implement. Note: installing tailscale
     on the Fedora box needs sudo — package that as ONE copy-paste
     command block for the user (they run it; you verify after).
   - Latency target: <2 s overhead per call is fine (TTS itself is
     3–5 s; batches amortize).

4. **Provider routing** in `gemini.synthesize` / settings:
   - `TTS_PROVIDER=qwen-local` becomes the default. Chain:
     qwen-local → (health fail/timeout/503) → elevenlabs → gemini.
   - Health-check memoized ~60 s so a dead box costs one probe per
     minute, not per clip. Per-batch failover (not per-clip flapping).
   - Spend ledger: log qwen-local usage at cost 0 (keeps the audit
     trail consistent); ElevenLabs fallback usage stays billed as now.
   - Rollback: `TTS_PROVIDER=elevenlabs` restores today's behavior
     exactly. Keep it documented in CLAUDE.md's credentials section.

5. **Acceptance** (all must pass before flipping the default):
   - One full language pool-audio rebuild end-to-end via qwen-local
     (hundreds of clips), diffing durations/LUFS vs an ElevenLabs
     control sample; user spot-listens a handful.
   - Failover drill: kill the local server mid-batch → the batch
     completes via ElevenLabs, silence markers heal on re-run, nothing
     wedges.
   - Etiquette drill: submit a batch while a ComfyUI render runs →
     bridge defers or 503s, never disturbs the render.
   - Voice continuity check: new clips interleaved with old ones in an
     existing deck sound like the same speaker (user's ear).

## Coordination rules (this box is shared)

- The repo is the shared brain: commit docs/CHANGELOG as you land
  things; the estate/hub codex studies and the illustration-prompt
  campaign are running in parallel — your changes must not touch their
  paths (docs/research/, idiomatic/grammar/data/illustration_prompts/).
- Deploys restart the Render app: check nothing is mid-flight through
  the server (cloud render batches, autopilot runs) before pushing.
- The Mac Studio (ssh evgeny2026@mac.lan) is a future second TTS host —
  design the health-check/fallback so adding it later is config, not
  code. Do NOT set it up now (it runs its own heavy pipelines).
