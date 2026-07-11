"""Worker loop. Drains the videos queue and produces apkgs.

Runs as an asyncio task inside the same process as the FastAPI app (see
api.py:lifespan). Single producer, single consumer — Postgres SKIP LOCKED
gives us correct claim semantics if we ever scale to multiple instances.
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import structlog
from slugify import slugify  # python-slugify pkg, slugify module

from . import db
from . import oxylabs_client
from .pipeline import audio as audio_mod
from .pipeline import connectives
from .pipeline.apkg import build_apkg
from .pipeline.dedup import normalize
from .pipeline.explain import enrich_one
from .pipeline.extract import extract_from_audio
from .settings import get_settings

log = structlog.get_logger()


# ---- one-video helpers ----------------------------------------------------

async def _download_audio(youtube_id: str,
                           dst_dir: Path) -> tuple[Path, int | None]:
    """Fetch the audio track via Oxylabs YouTube Downloader → Cloudflare R2.

    Idempotent. Returns (audio path, duration_sec | None). The extension
    depends on what Oxylabs returns — typically .aac or .m4a; Gemini and
    ffmpeg accept both. Duration comes from the Oxylabs job status when we
    actually ran a job; on the local-reuse fast path it's None and the
    caller falls back to ffprobe. Oxylabs eats the bot-wall fight on their
    side.
    """
    # Fast path: if we already pulled it locally, reuse it (worker may retry
    # this video).
    for existing in dst_dir.glob("source.*"):
        if existing.is_file() and existing.stat().st_size > 0:
            return existing, None
    dst_dir.mkdir(parents=True, exist_ok=True)
    job_id = await oxylabs_client.submit_audio_job(youtube_id)
    status_body = await oxylabs_client.wait_for_done(job_id)
    out = await oxylabs_client.download_audio(youtube_id, job_id, dst_dir)
    # Best-effort R2 cleanup so the bucket doesn't grow forever.
    await oxylabs_client.cleanup_r2(youtube_id)
    return out, oxylabs_client.duration_from_status(status_body)


def _ffprobe_duration(path: Path) -> int | None:
    """Container duration in whole seconds, or None if ffprobe can't tell."""
    import subprocess
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=60,
        )
        return int(float(r.stdout.strip()))
    except (subprocess.SubprocessError, ValueError, OSError):
        return None


async def _filter_fresh(extracted: list, lang: str) -> list:
    """Drop phrases already in the expression library."""
    existing = await db.existing_normalized_for_lang(lang)
    fresh = [p for p in extracted if p.normalized not in existing]
    log.info("worker.dedup", n_extracted=len(extracted), n_fresh=len(fresh))
    return fresh


# ---- daily cap check ------------------------------------------------------

async def _under_daily_cap(lang: str) -> bool:
    settings = get_settings()
    pool = await db.get_pool()
    n_today = await pool.fetchval(
        """
        SELECT COUNT(*) FROM apkgs
        WHERE lang = $1 AND created_at >= date_trunc('day', NOW())
        """,
        lang,
    )
    return n_today < settings.max_new_apkgs_per_lang_per_day


# ---- pool-source persistence ----------------------------------------------

async def _persist_pool_source(*, survivors: list, lang: str, video_id: int,
                                video_audio_dir: Path) -> None:
    """Copy per-card audio (idiom_tgt/en, ex_*_en/tgt) from the ephemeral
    work_root into /data/staged_audio/<youtube_id>/, and write the
    corresponding expression_idioms + expression_examples rows.

    The per-video work_root is wiped at the end of process_video, so this
    must run BEFORE the finally-block cleanup. Idempotent: copying an
    existing file is a no-op via shutil.copy2 + path exists guard.
    """
    settings = get_settings()
    youtube_id = video_audio_dir.parent.name
    stage_dir = Path(settings.data_dir) / "staged_audio" / youtube_id
    stage_dir.mkdir(parents=True, exist_ok=True)

    def _persist(src: Path) -> str | None:
        """Copy src into stage_dir; return path RELATIVE to staged_audio root.
        Returns None if src doesn't exist."""
        if not src.exists():
            return None
        dst = stage_dir / src.name
        if not dst.exists() or dst.stat().st_size == 0:
            shutil.copy2(src, dst)
        return f"{youtube_id}/{src.name}"

    from .pipeline.dedup import normalize as _normalize

    for pid_int, en, _front, _back in survivors:
        pid = f"{pid_int:03d}"
        idiom_tgt_rel = _persist(video_audio_dir / f"idiom_tgt_{pid}.mp3")
        idiom_en_rel = _persist(video_audio_dir / f"idiom_en_{pid}.mp3")

        # Find the expression_id we just inserted for this phrase
        expression_id = await db.get_expression_id(lang, _normalize(en.phrase))
        if expression_id is None:
            log.warning("worker.pool_no_expression",
                         phrase=en.phrase[:40])
            continue

        idiom_id = await db.insert_idiom_record(
            expression_id=expression_id, video_id=video_id, lang=lang,
            idiom_text=en.phrase, english_gloss=en.english,
            audio_idiom_tgt=idiom_tgt_rel, audio_idiom_en=idiom_en_rel,
            source_phrase_target=getattr(en, "source_phrase_target", "") or None,
            source_phrase_en=getattr(en, "source_phrase_en", "") or None,
            explanation_en=getattr(en, "explanation_en", "") or None,
        )

        example_rows = []
        for j, ex in enumerate(en.examples, 1):
            ex_en_rel = _persist(video_audio_dir / f"ex_{pid}_{j}_en.mp3")
            ex_tgt_rel = _persist(video_audio_dir / f"ex_{pid}_{j}_tgt.mp3")
            example_rows.append({
                "ord": j,
                "en_text": ex.get("en", ""),
                "target_text": ex.get("target", ""),
                "audio_en": ex_en_rel,
                "audio_target": ex_tgt_rel,
            })
        await db.insert_examples(idiom_id, example_rows)

    log.info("worker.pool_source_persisted",
             youtube_id=youtube_id, n=len(survivors))


# ---- main per-video pipeline ----------------------------------------------

async def process_video(video: dict) -> None:
    settings = get_settings()
    youtube_id = video["youtube_id"]
    lang = video["lang"]
    title = video["title"] or youtube_id

    log.info("worker.processing", id=video["id"], yt=youtube_id, lang=lang,
             title=title[:60])

    work_root = Path(tempfile.gettempdir()) / "idiomatic" / youtube_id
    work_root.mkdir(parents=True, exist_ok=True)
    try:
        # 1. Download audio via Oxylabs → R2 (returns .m4a; Gemini + ffmpeg
        # both accept it directly, no re-encode needed).
        source_audio, duration_sec = await _download_audio(youtube_id, work_root)

        # 1b. Duration window check. The cron enqueues every RSS entry blind
        # (RSS has no duration; scraping the watch page for it hit the bot
        # wall), so the gate lives here where the length is known for free.
        if duration_sec is None:
            duration_sec = await asyncio.to_thread(_ffprobe_duration, source_audio)
        if duration_sec is not None:
            await db.set_video_duration(video["id"], duration_sec)
            if not (settings.min_duration_sec <= duration_sec
                    <= settings.max_duration_sec):
                await db.mark_video_status(
                    video["id"], "skipped",
                    f"duration {duration_sec}s outside "
                    f"[{settings.min_duration_sec}, {settings.max_duration_sec}]",
                )
                return
        else:
            log.warning("worker.duration_unknown", yt=youtube_id)

        # 2. Extract idiomatic phrases via Gemini 3.5 Flash audio understanding
        extracted = await extract_from_audio(
            source_audio, lang, n_target=settings.target_idioms_per_video,
        )
        if not extracted:
            await db.mark_video_status(video["id"], "skipped", "no idioms extracted")
            return

        # 3. Dedup vs existing expression library
        fresh = await _filter_fresh(extracted, lang)
        if not fresh:
            await db.mark_video_status(video["id"], "skipped", "all dedupes")
            return

        # 4. Enrich each fresh phrase (examples + structured explanation)
        narration_root = Path(settings.data_dir) / "narration"
        await connectives.ensure_cached(narration_root, voice_en="Kore")
        # Per-language practice_intro narration (one-shot per language)
        _LANG_NAMES = {"de": "German", "fr": "French", "it": "Italian",
                       "pt": "Portuguese", "es": "Spanish", "zh": "Mandarin"}
        await connectives.ensure_lang_cached(
            narration_root, _LANG_NAMES.get(lang, lang.upper()), voice_en="Kore",
        )

        # Pre-create the silence cache files. silence_mp3() checks `exists()`
        # then ffmpegs to the path — racy under parallel idioms (two writers
        # produce a corrupt file, breaking the later -c copy concat with
        # ffmpeg exit code 183). Do them serially up front.
        for ms in (300, 700, 1200, 1500):
            audio_mod.silence_mp3(narration_root, ms)

        video_audio_dir = work_root / "audio"
        video_audio_dir.mkdir(parents=True, exist_ok=True)

        import time as _time
        sem = asyncio.Semaphore(settings.idiom_parallelism)

        async def _one(i: int, phrase) -> tuple | None:
            async with sem:
                t0 = _time.monotonic()
                log.info("worker.idiom.start", i=i, of=len(fresh),
                         phrase=phrase.text[:50])
                try:
                    en = await enrich_one(
                        phrase.text, phrase.english, lang,
                        source_phrase_target=getattr(phrase,
                                                      "source_phrase_target", ""),
                        source_phrase_en=getattr(phrase,
                                                  "source_phrase_en", ""),
                        explanation_en=getattr(phrase, "explanation_en", ""),
                    )
                    log.info("worker.idiom.enriched", i=i,
                             dt=round(_time.monotonic() - t0, 1))
                    front, back = await audio_mod.render_card_audio(
                        idx=i, enriched=en, lang=lang,
                        source_mp3=source_audio,
                        audio_start=phrase.audio_start, audio_end=phrase.audio_end,
                        video_audio_dir=video_audio_dir,
                        narration_root=narration_root,
                    )
                    log.info("worker.idiom.done", i=i,
                             dt=round(_time.monotonic() - t0, 1))
                    return (i, en, front, back)
                except Exception as e:
                    import traceback
                    log.warning("worker.idiom.failed",
                                 i=i, phrase=phrase.text[:40], err=repr(e),
                                 dt=round(_time.monotonic() - t0, 1),
                                 tb=traceback.format_exc()[-400:])
                    return None

        results = await asyncio.gather(
            *[_one(i, p) for i, p in enumerate(fresh, 1)]
        )
        # survivors: list of (pid, Enriched, front_mp3, back_mp3) tuples
        survivors = [r for r in results if r is not None]

        if not survivors:
            await db.mark_video_status(video["id"], "failed",
                                        "all enrichments failed")
            return

        # 5. Build apkg — feed it just (en, front, back) to keep the signature
        enriched_tuples = [(en, f, b) for _i, en, f, b in survivors]
        slug = slugify(title)[:60] or youtube_id
        apkg_dir = Path(settings.data_dir) / "apkgs" / lang
        apkg_dir.mkdir(parents=True, exist_ok=True)
        apkg_filename = f"{lang}/{slug}-{youtube_id}.apkg"
        apkg_path = Path(settings.data_dir) / "apkgs" / apkg_filename

        # Date prefix so decks sort chronologically inside Anki. Use the
        # video's first_seen timestamp (when the cron first enqueued it).
        _LANG_NAMES_FOR_DECK = {
            "de": "German", "fr": "French", "it": "Italian",
            "pt": "Portuguese", "es": "Spanish", "zh": "Mandarin",
            "nl": "Dutch", "sv": "Swedish", "no": "Norwegian", "da": "Danish",
        }
        lang_name_deck = _LANG_NAMES_FOR_DECK.get(lang, lang.upper())
        date_prefix = "0000-00-00"
        try:
            _pool = await db.get_pool()
            row = await _pool.fetchrow(
                "SELECT first_seen::date AS d FROM videos WHERE id = $1",
                video["id"],
            )
            if row and row["d"]:
                date_prefix = row["d"].isoformat()
        except Exception:
            pass
        deck_name = f"Idiomatic::{lang_name_deck}::{date_prefix} · {title}"

        build_apkg(
            out_path=apkg_path,
            deck_name=deck_name,
            youtube_id=youtube_id,
            video_title=title,
            video_url=f"https://www.youtube.com/watch?v={youtube_id}",
            idioms=enriched_tuples,
            stage_dir=Path(settings.data_dir) / "media_stage",
        )

        # 6. Record video apkg + insert expressions
        apkg_id = await db.insert_video_apkg(
            video_id=video["id"], lang=lang,
            filename="apkgs/" + apkg_filename,
            size_bytes=apkg_path.stat().st_size,
            n_idioms=len(enriched_tuples),
        )
        log.info("worker.apkg_inserted", id=apkg_id, n=len(enriched_tuples))

        kept_phrases = [p for p, _, _ in enriched_tuples]
        ext_for_db = [
            {"text": e.phrase, "normalized": normalize(e.phrase),
             "english": e.english}
            for e in kept_phrases
        ]
        await db.insert_expressions(lang, video["id"], ext_for_db)

        # 7. Persist per-card audio + idiom/example records for the pool
        #    builder. Failures here log but don't fail the video — the
        #    per-video apkg is already shipped.
        try:
            await _persist_pool_source(
                survivors=survivors, lang=lang, video_id=video["id"],
                video_audio_dir=video_audio_dir,
            )
        except Exception as e:
            log.warning("worker.pool_persist_failed", err=repr(e)[:200])

        # 8. Rebuild the language's pool apkgs so this video's idioms show
        #    up in cross-video drilling decks.
        try:
            from .pipeline import pool as pool_mod
            await pool_mod.rebuild_pools(lang)
        except Exception as e:
            log.warning("worker.pool_rebuild_failed",
                         lang=lang, err=repr(e)[:200])

        await db.mark_video_status(video["id"], "done")
        log.info("worker.done", id=video["id"], n_idioms=len(enriched_tuples))

    finally:
        # Tidy local workdir; /data/apkgs stays.
        shutil.rmtree(work_root, ignore_errors=True)


# ---- the loop -------------------------------------------------------------

async def loop(once: bool = False) -> None:
    settings = get_settings()
    log.info("worker.start", once=once, poll=settings.worker_poll_interval_sec)
    try:
        while True:
            try:
                video = await db.claim_next_video()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Transient DB issue (schema not yet applied, connection
                # reset, etc.). Don't let it kill the unobserved task —
                # just log + back off and try again.
                log.warning("worker.claim_failed", err=str(e)[:200])
                await asyncio.sleep(settings.worker_poll_interval_sec)
                if once:
                    return
                continue
            if video is None:
                if once:
                    return
                await asyncio.sleep(settings.worker_poll_interval_sec)
                continue

            # Soft daily cap. If we're at the cap for this video's language,
            # release it back to queued WITHOUT counting this as an attempt
            # (otherwise three cap-hits permanently wedge the row).
            if not await _under_daily_cap(video["lang"]):
                log.info("worker.daily_cap_hit", lang=video["lang"])
                await db.requeue_no_attempt(video["id"], "cap hit; retry tomorrow")
                if once:
                    return
                # Avoid hot-spinning if every language is capped
                await asyncio.sleep(60)
                continue

            try:
                await process_video(video)
            except asyncio.CancelledError:
                # Lifespan shutdown — release the claim so another instance
                # can pick it up. This isn't the video's fault either.
                await db.requeue_no_attempt(video["id"], "shutdown")
                raise
            except Exception as e:
                log.exception("worker.failed", id=video["id"], err=str(e))
                await db.mark_video_status(video["id"], "failed", str(e)[:500])

            if once:
                return
    finally:
        if once:
            await db.close_pool()


# ---- standalone CLI for local testing -------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true",
                    help="Process one job and stop (or exit if queue empty)")
    args = ap.parse_args()

    structlog.configure(processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ])

    try:
        asyncio.run(loop(once=args.once))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
