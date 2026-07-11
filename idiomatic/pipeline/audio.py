"""Audio rendering for one enriched idiom — pimsleur didactic shape.

FRONT audio (the lesson):
  listen_context → silence → snippet (the original video clip)
  → here_it_is → idiom_tgt
  → meaning → idiom_en
  → how_to_use → explanation_en (TTS'd English paragraph)
  → examples_intro → 3 teach pairs (en → silence → target)

BACK audio (the drill, with think-pause):
  practice_intro
  → sentence_1 → drill1_en → think pause → drill1_target
  → sentence_2 → drill2_en → think pause → drill2_target
  → sentence_3 → drill3_en → think pause → drill3_target

Connective narration is pre-rendered once per language (cached on disk).
Per-card audio (idiom_*, explanation_*, ex_*) is rendered in parallel via
gemini.synthesize then concat'd by ffmpeg.
"""

from __future__ import annotations

import asyncio
import hashlib
import subprocess
import tempfile
from pathlib import Path

import structlog

from .. import gemini
from ..langs import LANG_NAMES as _LANG_NAMES
from . import connectives
from .explain import Enriched

log = structlog.get_logger()

# Per-language target voice for Gemini Flash TTS. English narration uses Kore.
#
# EMPIRICAL TASTE TABLE, not a correctness table: Google assigns prebuilt
# voices style descriptors only ("Kore — Firm") and the model auto-detects
# language from the input text — there is no official per-language roster,
# and accent/pacing drift is per-call. Only pt and de output have been
# listen-verified; treat the rest as unreviewed defaults.
LANG_VOICE = {
    "de": "Charon",
    "fr": "Aoede",
    "it": "Leda",
    "pt": "Orus",
    "es": "Fenrir",
    "zh": "Achernar",
    "nl": "Charon",
    "sv": "Charon",
    "no": "Charon",
    "da": "Charon",
}
EN_VOICE = "Kore"

# ---- silence cache --------------------------------------------------------

def silence_mp3(root: Path, ms: int) -> Path:
    out = root / f"_silence_{ms}ms.mp3"
    if out.exists():
        return out
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=24000",
         "-t", f"{ms/1000:.3f}",
         "-c:a", "libmp3lame", "-q:a", "9", str(out)],
        check=True,
    )
    return out


# ---- slicing --------------------------------------------------------------

def slice_clip(src_audio: Path, start: float, end: float, out: Path) -> Path:
    """ffmpeg-slice the source audio to mp3. Idempotent.

    Forced to 24 kHz mono: every other concat input (Gemini TTS, silence
    stubs) is 24 kHz mono, and the concat demuxer's -c copy splices raw
    mp3 frames — heterogeneous params are undefined behavior that only
    happens to survive the loudnorm re-encode today."""
    if out.exists() and out.stat().st_size > 0:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.3, end - start)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-ss", f"{start:.3f}", "-t", f"{duration:.3f}",
         "-i", str(src_audio),
         "-ar", "24000", "-ac", "1",
         "-c:a", "libmp3lame", "-q:a", "4", str(out)],
        check=True,
    )
    return out


# ---- concat (loudness-normalized) -----------------------------------------

def concat_mp3s(pieces: list[Path], out: Path,
                 normalize_loudness: bool = True) -> Path:
    """Concat with ffmpeg. -c copy is the fastest path but it only works
    if every input shares codec params; in our pipeline they should.
    When normalize_loudness=True we run a second pass with loudnorm to
    even out the volume across narration / TTS / video snippet inputs."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False,
                                      dir=out.parent) as f:
        listfile = Path(f.name)
        for p in pieces:
            f.write(f"file '{Path(p).resolve()}'\n")
    raw = out.with_suffix(".raw.mp3") if normalize_loudness else out
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(listfile),
             "-c", "copy", str(raw)],
            check=True,
        )
        if normalize_loudness:
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error",
                 "-i", str(raw),
                 "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                 "-c:a", "libmp3lame", "-q:a", "4", str(out)],
                check=True,
            )
            raw.unlink(missing_ok=True)
    finally:
        listfile.unlink(missing_ok=True)
    return out


# ---- top-level: render front + back audio for one idiom -------------------

async def render_card_audio(idx: int, enriched: Enriched, lang: str,
                              source_mp3: Path, audio_start: float, audio_end: float,
                              video_audio_dir: Path,
                              narration_root: Path) -> tuple[Path, Path]:
    """Returns (front_mp3, back_mp3) for this idiom."""
    voice_tgt = LANG_VOICE.get(lang, "Charon")
    lang_name = _LANG_NAMES.get(lang, lang.upper())
    # Seed on the video id (work_root dir name), not source_mp3.stem —
    # the stem is always "source", which collapsed narration-variant
    # choice to per-index (every video's idiom #1 sounded identical).
    seed = f"{video_audio_dir.parent.name}::{idx:03d}"
    pid = f"{idx:03d}"

    sh = silence_mp3(narration_root, 300)
    md = silence_mp3(narration_root, 700)
    lg = silence_mp3(narration_root, 1200)
    think = silence_mp3(narration_root, 1500)

    # --- snippet from the source video --------------------------------------
    snippet = slice_clip(source_mp3,
                          audio_start, audio_end,
                          video_audio_dir / f"snippet_{pid}.mp3")

    # --- planning pass ------------------------------------------------------
    tts_tasks: list = []

    # The per-card TTS files
    idiom_tgt = video_audio_dir / f"idiom_tgt_{pid}.mp3"
    tts_tasks.append(gemini.synthesize(enriched.phrase, voice=voice_tgt,
                                         out=idiom_tgt))

    idiom_en = video_audio_dir / f"idiom_en_{pid}.mp3"
    tts_tasks.append(gemini.synthesize(enriched.english, voice=EN_VOICE,
                                         out=idiom_en))

    explanation_en_audio: Path | None = None
    if (enriched.explanation_en or "").strip():
        explanation_en_audio = video_audio_dir / f"explanation_{pid}.mp3"
        tts_tasks.append(gemini.synthesize(
            enriched.explanation_en, voice=EN_VOICE,
            out=explanation_en_audio,
        ))

    # Plan example sentences (6 total: first 3 teach, last 3 drill).
    teach_plan: list[tuple[Path, Path]] = []
    drill_plan: list[tuple[Path, Path]] = []
    for i, ex in enumerate(enriched.examples):
        en_path = video_audio_dir / f"ex_{pid}_{i+1}_en.mp3"
        tgt_path = video_audio_dir / f"ex_{pid}_{i+1}_tgt.mp3"
        tts_tasks.append(gemini.synthesize(ex["en"], voice=EN_VOICE,
                                             out=en_path))
        tts_tasks.append(gemini.synthesize(ex["target"], voice=voice_tgt,
                                             out=tgt_path))
        (teach_plan if i < 3 else drill_plan).append((en_path, tgt_path))

    # Fire them all concurrently. synthesize() never raises (silence
    # fallback on any error), so a plain gather is safe.
    await asyncio.gather(*tts_tasks)

    # --- narration cues (already pre-rendered in narration_root) -----------
    def _narr(key: str, lang_filled: bool = False) -> Path:
        text, p = connectives.pick_general(
            narration_root, key, seed,
            lang_name=(lang_name if lang_filled else None),
        )
        if not p:
            return sh  # no variants → degrade to silence
        # If the file isn't there for some reason (cache miss), fall back
        # to silence rather than crashing — ensure_cached should have
        # populated it.
        return p if p.exists() else sh

    listen_context = _narr("listen_context")
    here_it_is = _narr("here_it_is")
    meaning = _narr("meaning")
    how_to_use = _narr("how_to_use")
    examples_intro = _narr("examples_intro")
    practice_intro = _narr("practice_intro", lang_filled=True)
    sentence_1 = _narr("sentence_1")
    sentence_2 = _narr("sentence_2")
    sentence_3 = _narr("sentence_3")

    # --- stitch FRONT -------------------------------------------------------
    front_pieces: list[Path] = []
    if snippet:
        front_pieces += [listen_context, sh, snippet, md]
    front_pieces += [here_it_is, sh, idiom_tgt, md]
    front_pieces += [meaning, sh, idiom_en, md]
    if explanation_en_audio:
        front_pieces += [how_to_use, sh, explanation_en_audio, md]
    if teach_plan:
        front_pieces += [examples_intro, sh]
        for i, (en_p, tgt_p) in enumerate(teach_plan):
            if i > 0:
                front_pieces.append(md)
            front_pieces += [en_p, sh, tgt_p]
    front = video_audio_dir / f"front_{pid}.mp3"
    concat_mp3s(front_pieces, front)

    # --- stitch BACK --------------------------------------------------------
    back_pieces: list[Path] = [practice_intro, md]
    sentence_leads = [sentence_1, sentence_2, sentence_3]
    for i, (en_p, tgt_p) in enumerate(drill_plan[:3]):
        if i > 0:
            back_pieces.append(lg)
        back_pieces += [sentence_leads[i], sh, en_p, think, tgt_p]
    back = video_audio_dir / f"back_{pid}.mp3"
    if len(back_pieces) > 2:
        concat_mp3s(back_pieces, back)
    else:
        concat_mp3s([sh], back, normalize_loudness=False)

    return front, back
