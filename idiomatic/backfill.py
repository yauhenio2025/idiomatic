"""One-shot backfill of the pool source tables from existing per-video apkgs.

The early per-video runs of process_video built their apkgs but never
wrote the expression_idioms / expression_examples tables (the tables
didn't exist yet). This module rehydrates those tables AND re-generates
the per-card audio (idiom_tgt/idiom_en/ex_*_en/ex_*_tgt) needed by the
pool builder.

Strategy:
  - Walk /data/apkgs/<lang>/<slug>-<youtube_id>.apkg, skipping _pool*.
  - For each, unzip + read SQLite to extract per-note Phrase, English,
    and the 6 example pairs from ExamplesHTML.
  - For each idiom, re-call gemini.synthesize for the four kinds of
    per-card audio, writing into /data/staged_audio/<youtube_id>/.
  - Insert expression_idioms + expression_examples rows (idempotent on
    (expression_id, video_id)).
  - When all apkgs are done, call pool.rebuild_pools(lang) per language.

Idempotency: re-running is safe. expression_idioms.expression_id+video_id
duplicates are skipped at the DB layer below. Existing audio files are
not re-TTS'd thanks to gemini.synthesize's exists-and-non-empty guard.
"""

from __future__ import annotations

import asyncio
import html as html_mod
import re
import shutil
import sqlite3
import tempfile
import time
import zipfile
from pathlib import Path

import structlog

from . import db, gemini
from .pipeline import pool as pool_mod
from .pipeline.audio import LANG_VOICE, EN_VOICE
from .pipeline.dedup import normalize
from .settings import get_settings

log = structlog.get_logger()


# Order of fields in build_apkg's make_model():
#   PhraseId, Phrase, English, StructuredHTML, ExamplesHTML,
#   FrontAudio, BackAudio, Source
_PHRASE_IDX = 1
_ENGLISH_IDX = 2
_EXAMPLES_HTML_IDX = 4

# Compiled here to parse the example blocks the apkg builder produced.
_EXAMPLE_RE = re.compile(
    r'<div class="example-block">\s*'
    r'<div class="ex-tgt">(.*?)</div>\s*'
    r'<div class="ex-en">(.*?)</div>\s*'
    r'</div>',
    re.DOTALL,
)


def _extract_youtube_id(apkg_name: str) -> str | None:
    """The build_apkg filename pattern ends with -<youtube_id>.apkg."""
    m = re.search(r"-([A-Za-z0-9_-]{11})\.apkg$", apkg_name)
    return m.group(1) if m else None


def _read_notes(apkg_path: Path) -> list[dict]:
    """Returns [{phrase, english, examples=[{target, en}, ...]}]."""
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(apkg_path) as zf:
            # Different anki versions use either name; tolerate both.
            for candidate in ("collection.anki2", "collection.anki21"):
                if candidate in zf.namelist():
                    zf.extract(candidate, td)
                    coll = Path(td) / candidate
                    break
            else:
                raise RuntimeError(f"no collection.anki2* in {apkg_path}")
        conn = sqlite3.connect(str(coll))
        try:
            rows = conn.execute("SELECT flds FROM notes").fetchall()
        finally:
            conn.close()

    out: list[dict] = []
    for (flds_str,) in rows:
        fields = flds_str.split("\x1f")
        if len(fields) <= _EXAMPLES_HTML_IDX:
            continue
        phrase = (fields[_PHRASE_IDX] or "").strip()
        english = (fields[_ENGLISH_IDX] or "").strip()
        examples_html = fields[_EXAMPLES_HTML_IDX] or ""
        examples = []
        for tgt, en in _EXAMPLE_RE.findall(examples_html):
            examples.append({
                "target": html_mod.unescape(tgt).strip(),
                "en": html_mod.unescape(en).strip(),
            })
        if phrase and english:
            out.append({
                "phrase": phrase,
                "english": english,
                "examples": examples,
            })
    return out


async def _tts_one_idiom(
    *, idx: int, phrase: str, english: str,
    examples: list[dict], voice_tgt: str, stage_dir: Path,
) -> dict[str, str]:
    """Generate (or reuse) the per-card audio for a single idiom.
    Returns a dict mapping audio kind → relative path under staged_audio."""
    pid = f"{idx:03d}"
    youtube_id = stage_dir.name
    settings = get_settings()
    # All four kinds + per-example pairs. gemini.synthesize is idempotent
    # (skips if file exists with size > 0).
    paths: dict[str, str] = {}

    async def _do(text: str, voice: str, fname: str) -> str:
        dst = stage_dir / fname
        await gemini.synthesize(text, voice=voice, out=dst)
        return f"{youtube_id}/{fname}"

    # The four per-idiom files
    tasks: list = []
    if phrase:
        tasks.append(("idiom_tgt", _do(phrase, voice_tgt, f"idiom_tgt_{pid}.mp3")))
    if english:
        tasks.append(("idiom_en", _do(english, EN_VOICE, f"idiom_en_{pid}.mp3")))

    # The 6 example pairs
    for j, ex in enumerate(examples, 1):
        if ex.get("en"):
            tasks.append((f"ex_{j}_en",
                          _do(ex["en"], EN_VOICE, f"ex_{pid}_{j}_en.mp3")))
        if ex.get("target"):
            tasks.append((f"ex_{j}_tgt",
                          _do(ex["target"], voice_tgt, f"ex_{pid}_{j}_tgt.mp3")))

    results = await asyncio.gather(*[t[1] for t in tasks])
    for (key, _), rel in zip(tasks, results):
        paths[key] = rel
    return paths


async def backfill_one_video(*, apkg_path: Path, lang: str) -> dict:
    """Backfill one video. Idempotent: if expression_idioms already has
    rows for (expression_id, video_id), the idiom is skipped."""
    youtube_id = _extract_youtube_id(apkg_path.name)
    if not youtube_id:
        return {"skipped": "no youtube_id"}
    pool_conn = await db.get_pool()
    video_id = await pool_conn.fetchval(
        "SELECT id FROM videos WHERE youtube_id = $1", youtube_id,
    )
    if not video_id:
        return {"skipped": "no video row", "youtube_id": youtube_id}

    notes = _read_notes(apkg_path)
    if not notes:
        return {"skipped": "no notes parsed", "youtube_id": youtube_id}

    settings = get_settings()
    stage_dir = Path(settings.data_dir) / "staged_audio" / youtube_id
    stage_dir.mkdir(parents=True, exist_ok=True)
    voice_tgt = LANG_VOICE.get(lang, "Charon")

    n_idioms_new = n_idioms_skip = n_examples = 0
    t0 = time.monotonic()
    for idx, note in enumerate(notes, 1):
        phrase = note["phrase"]
        english = note["english"]
        examples = note["examples"]
        norm = normalize(phrase)
        expression_id = await pool_conn.fetchval(
            "SELECT id FROM expressions WHERE lang = $1 AND normalized = $2",
            lang, norm,
        )
        if not expression_id:
            # Should never happen for an already-built apkg, but guard.
            expression_id = await pool_conn.fetchval(
                """INSERT INTO expressions (lang, text, normalized, english,
                                             first_video_id)
                   VALUES ($1, $2, $3, $4, $5) RETURNING id""",
                lang, phrase, norm, english, video_id,
            )
        # Idempotency: skip if we've already backfilled this one
        existing = await pool_conn.fetchval(
            """SELECT id FROM expression_idioms
               WHERE expression_id = $1 AND video_id = $2""",
            expression_id, video_id,
        )
        if existing:
            n_idioms_skip += 1
            continue

        paths = await _tts_one_idiom(
            idx=idx, phrase=phrase, english=english, examples=examples,
            voice_tgt=voice_tgt, stage_dir=stage_dir,
        )

        idiom_id = await db.insert_idiom_record(
            expression_id=expression_id, video_id=video_id, lang=lang,
            idiom_text=phrase, english_gloss=english,
            audio_idiom_tgt=paths.get("idiom_tgt"),
            audio_idiom_en=paths.get("idiom_en"),
        )
        example_rows = []
        for j, ex in enumerate(examples, 1):
            example_rows.append({
                "ord": j,
                "en_text": ex.get("en", ""),
                "target_text": ex.get("target", ""),
                "audio_en": paths.get(f"ex_{j}_en"),
                "audio_target": paths.get(f"ex_{j}_tgt"),
            })
        await db.insert_examples(idiom_id, example_rows)
        n_idioms_new += 1
        n_examples += len(example_rows)
        log.info("backfill.idiom_done",
                 youtube_id=youtube_id, idx=idx, of=len(notes),
                 dt=round(time.monotonic() - t0, 1))

    return {
        "youtube_id": youtube_id, "lang": lang,
        "n_notes": len(notes),
        "n_idioms_new": n_idioms_new,
        "n_idioms_skipped": n_idioms_skip,
        "n_examples": n_examples,
        "elapsed_s": round(time.monotonic() - t0, 1),
    }


# ---- Top-level orchestration ----------------------------------------------

_BACKFILL_STATE: dict = {"running": False, "stats": [], "started_at": None,
                          "finished_at": None, "error": None}


async def run_backfill() -> dict:
    """Walks /data/apkgs/<lang>/*.apkg and backfills every video deck found.
    Triggers pool rebuild per language at the end."""
    if _BACKFILL_STATE["running"]:
        return {"error": "already running"}
    _BACKFILL_STATE["running"] = True
    _BACKFILL_STATE["started_at"] = time.time()
    _BACKFILL_STATE["finished_at"] = None
    _BACKFILL_STATE["error"] = None
    _BACKFILL_STATE["stats"] = []
    try:
        settings = get_settings()
        apkgs_root = Path(settings.data_dir) / "apkgs"
        langs_touched: set[str] = set()
        for lang_dir in sorted(apkgs_root.iterdir()):
            if not lang_dir.is_dir():
                continue
            lang = lang_dir.name
            for apkg_path in sorted(lang_dir.glob("*.apkg")):
                if apkg_path.name.startswith("_pool"):
                    continue
                log.info("backfill.start_apkg", apkg=apkg_path.name)
                stats = await backfill_one_video(
                    apkg_path=apkg_path, lang=lang,
                )
                _BACKFILL_STATE["stats"].append(stats)
                log.info("backfill.apkg_done", **stats)
                langs_touched.add(lang)
        for lang in sorted(langs_touched):
            log.info("backfill.rebuild_pool_start", lang=lang)
            res = await pool_mod.rebuild_pools(lang)
            _BACKFILL_STATE["stats"].append({"pool_rebuild": res})
            log.info("backfill.rebuild_pool_done", **res)
    except Exception as e:
        _BACKFILL_STATE["error"] = repr(e)[:300]
        log.exception("backfill.crashed")
    finally:
        _BACKFILL_STATE["running"] = False
        _BACKFILL_STATE["finished_at"] = time.time()
    return _BACKFILL_STATE


def get_state() -> dict:
    s = dict(_BACKFILL_STATE)
    s["n_completed"] = len([x for x in s["stats"] if "youtube_id" in x])
    return s
