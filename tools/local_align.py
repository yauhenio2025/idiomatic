"""Local whisper-alignment backfill for context clips.

For every idiom whose audio_context is NULL or in final_null_ids.json:
  video audio via yt-dlp (home IP — no bot wall) → whisper turbo
  word-timestamp transcript → fuzzy-locate each stored sentence →
  slice ±0.25/0.35s with accurate mp3 seeking → upload via
  /ui/api/upload-context/{id}.

Clips are correct by construction (cut at the transcript match), so no
separate verification pass is needed; a match threshold of 0.6 gates
uploads. Resumable: uploaded ids are recorded in local_align_done.json.
"""
import json
import re
import subprocess
import sys
import time
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

TOKEN = sys.argv[1]
BASE = "https://idiomatic-app.onrender.com"
SCRATCH = Path(__file__).parent
WORK = SCRATCH / "align_work"
WORK.mkdir(exist_ok=True)
DONE_F = SCRATCH / "local_align_done.json"
MATCH_AT = 0.6


def api(path, data=None, headers=None):
    h = {"X-Admin-Token": TOKEN}
    if headers:
        h.update(headers)
    req = urllib.request.Request(BASE + path, data=data, headers=h,
                                  method="POST" if data else "GET")
    # Pool rebuilds block the single-process API for 10+ minutes; wait
    # them out instead of dying (total patience ~25 min).
    for attempt in range(10):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception:
            time.sleep(min(300, 20 * (attempt + 1)))
    raise RuntimeError(f"api failed: {path}")


def norm(t):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (t or "").lower())).strip()


done = set(json.loads(DONE_F.read_text())) if DONE_F.exists() else set()
null_ids = set(json.load(open(SCRATCH / "final_null_ids.json")))

# Collect targets: paginate the library, keep NULL-context or known-bad ids.
targets = []
offset = 0
while True:
    d = api(f"/ui/api/expressions?limit=100&offset={offset}")
    for r in d["rows"]:
        if r["id"] in done:
            continue
        if r.get("audio_context") is None or r["id"] in null_ids:
            targets.append(r["id"])
    offset += 100
    if offset >= d["total"]:
        break
print(f"{len(targets)} idioms need locally-aligned clips", flush=True)

# Group by video via detail fetches.
by_video: dict[str, list[dict]] = {}
for iid in targets:
    d = api(f"/ui/api/expressions/{iid}")
    if not d.get("youtube_id") or not (d.get("source_phrase_target") or "").strip():
        continue
    by_video.setdefault(d["youtube_id"], []).append(d)
print(f"{len(by_video)} videos to align", flush=True)

from faster_whisper import WhisperModel
model = WhisperModel("turbo", device="cpu", compute_type="int8")

uploaded = located_fail = dl_fail = 0
for vi, (yt, idioms) in enumerate(sorted(by_video.items()), 1):
    audio = WORK / f"{yt}.mp3"
    if not audio.exists():
        r = subprocess.run(
            ["yt-dlp", "-q", "--no-update", "-x", "--audio-format", "mp3",
             "--audio-quality", "5", "-o", str(WORK / f"{yt}.%(ext)s"),
             f"https://www.youtube.com/watch?v={yt}"],
            capture_output=True, text=True, timeout=1800)
        if r.returncode != 0 or not audio.exists():
            print(f"DL-FAIL {yt}: {r.stderr[-120:]}", flush=True)
            dl_fail += len(idioms)
            continue
    try:
        segs, info = model.transcribe(str(audio), language=idioms[0]["lang"],
                                       word_timestamps=True, vad_filter=True,
                                       condition_on_previous_text=False)
        words = [(w.start, w.end, norm(w.word)) for s in segs
                 for w in (s.words or [])]
    except Exception as e:
        print(f"TRANSCRIBE-FAIL {yt}: {e}", flush=True)
        continue
    texts = [w[2] for w in words]

    def locate(sentence):
        target = norm(sentence).split()
        n = len(target)
        if n == 0 or len(words) < n:
            return None
        tjoin = " ".join(target)
        best = (0.0, 0)
        step = max(1, n // 4)
        for i in range(0, len(words) - n + 1, step):
            r = SequenceMatcher(None, tjoin, " ".join(texts[i:i + n])).ratio()
            if r > best[0]:
                best = (r, i)
        b = best
        for i in range(max(0, best[1] - 2 * step),
                       min(len(words) - n + 1, best[1] + 2 * step)):
            r = SequenceMatcher(None, tjoin, " ".join(texts[i:i + n])).ratio()
            if r > b[0]:
                b = (r, i)
        return (b[0], words[b[1]][0], words[min(b[1] + n, len(words)) - 1][1])

    for d in idioms:
        loc = locate(d["source_phrase_target"])
        if not loc or loc[0] < MATCH_AT:
            located_fail += 1
            continue
        score, start, end = loc
        if not (0.5 <= end - start <= 45):
            located_fail += 1
            continue
        clip = WORK / f"clip_{d['id']}.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio),
             "-ss", f"{max(0.0, start - 0.25):.3f}",
             "-t", f"{end - start + 0.6:.3f}",
             "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", "-q:a", "4",
             str(clip)], check=True, timeout=600)
        if clip.stat().st_size < 2000:
            located_fail += 1
            continue
        api(f"/ui/api/upload-context/{d['id']}", data=clip.read_bytes(),
            headers={"Content-Type": "audio/mpeg"})
        clip.unlink()
        done.add(d["id"])
        uploaded += 1
    DONE_F.write_text(json.dumps(sorted(done)))
    audio.unlink(missing_ok=True)
    print(f"video {vi}/{len(by_video)} {yt}: cumulative uploaded={uploaded} "
          f"unlocated={located_fail}", flush=True)

print("ALIGN-DONE", json.dumps({"uploaded": uploaded,
                                  "unlocated": located_fail,
                                  "download_failed": dl_fail}), flush=True)
