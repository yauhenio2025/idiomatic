"""Audio rendering for an enriched idiom.

Builds two stitched mp3s per card (front + back) by alternating:
  - the original-video clip (sliced from the source mp3 by ffmpeg)
  - English connective tissue (cached Sarah-equivalent voice, Kore)
  - target-language content (Gemini Flash TTS in the per-language voice)
  - silences (cached short/mid/long ffmpeg-generated silence mp3s)

Caches everything aggressively. A second video that mentions the same
expression skips most TTS calls.
"""

from __future__ import annotations

import asyncio
import hashlib
import subprocess
import tempfile
from pathlib import Path

import structlog

from .. import gemini
from . import connectives
from .explain import Enriched

log = structlog.get_logger()

# Per-language target voice for Gemini Flash TTS. English narration uses Kore.
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

def slice_clip(src_mp3: Path, start: float, end: float, out: Path) -> Path:
    """ffmpeg-slice the source mp3. Idempotent."""
    if out.exists() and out.stat().st_size > 0:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.3, end - start)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-ss", f"{start:.3f}", "-t", f"{duration:.3f}",
         "-i", str(src_mp3),
         "-c:a", "libmp3lame", "-q:a", "4", str(out)],
        check=True,
    )
    return out


# ---- concat ----------------------------------------------------------------

def concat_mp3s(pieces: list[Path], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False,
                                      dir=out.parent) as f:
        listfile = Path(f.name)
        for p in pieces:
            f.write(f"file '{Path(p).resolve()}'\n")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(listfile),
             "-c", "copy", str(out)],
            check=True,
        )
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
    seed = f"{source_mp3.stem}::{idx:03d}"
    pid = f"{idx:03d}"

    sh = silence_mp3(narration_root, 300)
    md = silence_mp3(narration_root, 700)
    lg = silence_mp3(narration_root, 1200)
    think = silence_mp3(narration_root, 1500)

    # --- snippet from the source video --------------------------------------
    snippet = slice_clip(source_mp3,
                          audio_start, audio_end,
                          video_audio_dir / f"snippet_{pid}.mp3")

    # ---------------------------------------------------------------------
    # PLANNING pass: every TTS coroutine we need, all paths predetermined.
    # We then asyncio.gather them — bound by the module-level TTS semaphore
    # in gemini.py — and only after they all settle do we stitch with ffmpeg
    # (which is sequential per-file anyway).
    # ---------------------------------------------------------------------
    tts_tasks: list = []

    idiom_tgt = video_audio_dir / f"idiom_tgt_{pid}.mp3"
    tts_tasks.append(gemini.synthesize(enriched.phrase, voice=voice_tgt, out=idiom_tgt))

    idiom_en = video_audio_dir / f"idiom_en_{pid}.mp3"
    tts_tasks.append(gemini.synthesize(enriched.english, voice=EN_VOICE, out=idiom_en))

    # Plan structured-explanation segments.
    expl_plan: list[tuple[Path, Path]] = []   # (conn_path, seg_path)
    for key, target_text in enriched.structured.items():
        conn_text, conn_path = connectives.pick_connective(narration_root, key, seed)
        if not conn_text:
            continue
        # Connectives are pre-cached by ensure_cached() at process start,
        # but if a code update added a new variant we missed, fall back here.
        if not conn_path.exists():
            tts_tasks.append(gemini.synthesize(conn_text, voice=EN_VOICE,
                                                 out=conn_path))
        h = hashlib.sha1(target_text.encode()).hexdigest()[:10]
        seg_path = video_audio_dir / f"expl_{pid}_{key}_{h}.mp3"
        tts_tasks.append(gemini.synthesize(target_text, voice=voice_tgt,
                                             out=seg_path))
        expl_plan.append((conn_path, seg_path))

    # Plan example sentences.
    teach_plan: list[tuple[Path, Path]] = []
    drill_plan: list[tuple[Path, Path]] = []
    for i, ex in enumerate(enriched.examples):
        en_path = video_audio_dir / f"ex_{pid}_{i+1}_en.mp3"
        tgt_path = video_audio_dir / f"ex_{pid}_{i+1}_tgt.mp3"
        tts_tasks.append(gemini.synthesize(ex["en"], voice=EN_VOICE, out=en_path))
        tts_tasks.append(gemini.synthesize(ex["target"], voice=voice_tgt, out=tgt_path))
        (teach_plan if i < 3 else drill_plan).append((en_path, tgt_path))

    # Fire them all. synthesize() never raises (it silence-falls-back on
    # any error), so a plain gather is safe.
    await asyncio.gather(*tts_tasks)

    # Now flatten the explanation plan into the canonical alternation:
    #   [conn] [silence] [target] [silence]
    expl_segments: list[Path] = []
    for conn_path, seg_path in expl_plan:
        expl_segments += [conn_path, sh, seg_path, md]
    teach_pairs = teach_plan
    drill_pairs = drill_plan

    # --- stitch FRONT: snippet → idiom_tgt → idiom_en → explanation → 3 teach
    front_pieces: list[Path] = [snippet, md, idiom_tgt, sh, idiom_en, md]
    front_pieces += expl_segments
    if teach_pairs:
        front_pieces.append(md)
        for en_p, tgt_p in teach_pairs:
            front_pieces += [en_p, sh, tgt_p, md]
    front = video_audio_dir / f"front_{pid}.mp3"
    concat_mp3s(front_pieces, front)

    # --- stitch BACK: 3 drill (EN → think pause → target) ------------------
    back_pieces: list[Path] = []
    for en_p, tgt_p in drill_pairs:
        back_pieces += [en_p, think, tgt_p, md]
    back = video_audio_dir / f"back_{pid}.mp3"
    if back_pieces:
        concat_mp3s(back_pieces, back)
    else:
        # No drill examples? Make a one-frame placeholder so the apkg builder
        # has something to attach.
        concat_mp3s([sh], back)

    return front, back
