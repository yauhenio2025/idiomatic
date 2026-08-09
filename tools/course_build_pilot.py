#!/usr/bin/env python3
"""Build the disposable Grammar Course pilot APKG for one unit.

Usage:
    .venv/bin/python tools/course_build_pilot.py de kasus [--audio]
        [--api-base https://idiomatic-app.onrender.com] [--production]

``--production`` routes the decks into the estate tree —
``anki_root(lang)::2 Grammar::<unit_label>::{1 Lesson,2 Exercises}`` via
course.course_deck_names (unit_label authority: course.DE_UNITS; a
mismatch with the lesson frontmatter aborts) and writes
``course_<lang>_<unit>.apkg``. Default (no flag) stays the disposable
ZZ pilot root, unchanged.

Reads the committed lesson script (idiomatic/grammar/data/course/lessons/)
and the machine-local, gitignored exercise file (…/course/book_local/),
then writes ``…/course/book_local/ZZ_pilot_<lang>_<unit>.apkg`` — also
gitignored (*.apkg) — under the disposable review root
``ZZ Grammar Course Pilot (disposable)``.

If ``…/course/book_local/<lang>_<unit>.enrichment.json`` exists (the
codex-authored sidecar, contract 1), it is parsed and cross-validated —
an invalid sidecar ABORTS the build — and the cards get the redesigned
layout: short task line in Instruction, worked example / English gloss /
grammar-why in the spare fields.  Absent sidecar → legacy build.

With ``--audio`` the tool resolves the unit's narration through the
local-TTS lane (docs/GRAMMAR_COURSE_DESIGN.md §6): it fetches the
completed-clip manifest from `/admin/local-tts/v1/course/status`,
downloads exactly the clips that match the current script/solution text
(sha256-verified, cached under book_local/clips/), stitches complete
lesson sides with the house conventions, and builds the APKG. STRICT for
completed clips (checksum/hash mismatch aborts), GRACEFUL for missing
ones: unvoiced cards ship audio-pending, so partial voicing still builds,
and the ``idiomatic-course-audio-pending`` tag drops per note as its
clips resolve (GUIDs are stable — reimporting updates cards in place).

Admin credentials: ``ADMIN_TOKEN`` env var, else the ``ADMIN_TOKEN=…``
line in ``~/.config/idiomatic-admin.env``. Never prints the token.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import structlog  # noqa: E402

from idiomatic import local_tts  # noqa: E402
from idiomatic.grammar import course  # noqa: E402

log = structlog.get_logger()

PILOT_ROOT = "ZZ Grammar Course Pilot (disposable)"
DEFAULT_API_BASE = "https://idiomatic-app.onrender.com"
STITCH_REVISION = "stitch-v1"


def resolve_deck_root(lang: str, unit: str, lesson_unit_label: str,
                      production: bool) -> str | None:
    """The build's root_override: ZZ pilot root by default, None under
    --production (deck names then compose from anki_tree.anki_root via
    course.course_deck_names — never a baked root string).  For DE
    production the unit must exist in course.DE_UNITS and the lesson's
    unit_label must match the registry (DE_UNITS is the authority for
    deck naming)."""
    if not production:
        return PILOT_ROOT
    if lang == "de":
        try:
            _chapter, label = course.de_unit(unit)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        if lesson_unit_label != label:
            raise SystemExit(
                f"lesson unit_label {lesson_unit_label!r} does not match "
                f"DE_UNITS {label!r} — fix the lesson frontmatter"
            )
    return None


def admin_token() -> str:
    token = os.environ.get("ADMIN_TOKEN", "").strip()
    if token:
        return token
    env_file = Path.home() / ".config" / "idiomatic-admin.env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("ADMIN_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(
        "no admin token: set ADMIN_TOKEN or ~/.config/idiomatic-admin.env"
    )


def fetch_status(api_base: str, lang: str, unit: str) -> dict:
    import httpx

    response = httpx.get(
        f"{api_base}/admin/local-tts/v1/course/status",
        params={"lang": lang, "unit": unit},
        headers={"X-Admin-Token": admin_token()},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def download_clip(api_base: str, row: dict, cache_root: Path) -> Path:
    """Fetch one completed clip into the cache, verifying its checksum."""
    import httpx

    destination = cache_root / row["staged_path"]
    if destination.is_file():
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        if digest == row["audio_sha256"]:
            return destination
        destination.unlink()
    response = httpx.get(
        f"{api_base}/admin/local-tts/v1/clip",
        params={"path": row["staged_path"]},
        headers={"X-Admin-Token": admin_token()},
        timeout=120,
    )
    response.raise_for_status()
    data = response.content
    digest = hashlib.sha256(data).hexdigest()
    if digest != row["audio_sha256"] or len(data) != row["audio_size_bytes"]:
        raise SystemExit(
            f"clip checksum mismatch for {row['source_key']} — refusing "
            "(strict completed-clip policy)"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return destination


def resolve_audio(
    api_base: str,
    lesson: course.CourseLesson,
    exercises: list[course.CourseExercise],
    enrichment: course.CourseEnrichment | None = None,
) -> tuple[dict[tuple[int, str], course.SideAudio], dict[str, Path], dict]:
    # The clip plan follows the EFFECTIVE solutions (contract-2 full
    # sentences), so voicing tracks the display via content-hash change.
    expected = local_tts.course_expected_job_rows(
        lesson, course.apply_effective_solutions(exercises, enrichment)
    )
    status = fetch_status(api_base, lesson.lang, lesson.unit)
    match = local_tts.match_course_completions(expected, status["completed"])
    matched = match["matched"]

    cache_root = course.BOOK_LOCAL_DIR / "clips"
    work_dir = cache_root / "_work"
    stitched_dir = cache_root / "stitched"

    expected_by_key = {row["source_key"]: row for row in expected}
    clip_paths = {
        source_key: download_clip(api_base, row, cache_root)
        for source_key, row in matched.items()
    }

    # Lesson sides: stitch only when every segment clip of a side matched.
    lesson_audio: dict[tuple[int, str], course.SideAudio] = {}
    sides_pending: list[str] = []
    for card in lesson.cards:
        for side in (card.front, card.back):
            speech = course.speech_segments(side)
            clips: dict[int, Path] = {}
            hashes: list[str] = []
            for index in range(len(speech)):
                marker = "front" if side.side == "front" else "back"
                source_key = (
                    f"course:v{local_tts.CONTRACT_VERSION}:{lesson.lang}:"
                    f"{lesson.unit}:{card.seq}:{marker}:seg{index:03d}"
                )
                if source_key not in clip_paths:
                    break
                clips[index] = clip_paths[source_key]
                hashes.append(expected_by_key[source_key]["content_hash"])
            if len(clips) != len(speech):
                sides_pending.append(f"c{card.seq:02d}{side.side[0]}")
                continue
            identity = hashlib.sha256(json.dumps(
                [STITCH_REVISION, *hashes]
            ).encode()).hexdigest()[:12]
            out = stitched_dir / (
                f"idcrsl_{lesson.lang}_{lesson.unit}_c{card.seq:02d}"
                f"{side.side[0]}_{identity}.mp3"
            )
            if not (out.exists() and out.stat().st_size > 0):
                course.stitch_side_narration(
                    side, clips, out_path=out, work_dir=work_dir,
                )
            lesson_audio[(card.seq, side.side)] = course.SideAudio(path=out)

    exercise_audio: dict[str, Path] = {}
    for exercise in exercises:
        source_key = (
            f"course:v{local_tts.CONTRACT_VERSION}:{exercise.lang}:"
            f"{exercise.unit}:{exercise.item_id}:solution"
        )
        if source_key in clip_paths:
            exercise_audio[exercise.item_id] = clip_paths[source_key]

    report = {
        "clips_expected": len(expected),
        "clips_matched": len(matched),
        "clips_stale": len(match["stale"]),
        "clips_missing": len(match["missing"]),
        "sides_voiced": len(lesson_audio),
        "sides_pending": sides_pending,
        "exercises_voiced": len(exercise_audio),
        "exercises_pending": len(exercises) - len(exercise_audio),
        "queue_counts": status.get("counts", {}),
        "failed_jobs": status.get("failed", []),
    }
    return lesson_audio, exercise_audio, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lang")
    parser.add_argument("unit")
    parser.add_argument("--audio", action="store_true",
                        help="resolve narration clips via the admin API")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument(
        "--production", action="store_true",
        help="build for the estate tree (anki_root::2 Grammar::<unit_label>)"
             " instead of the disposable ZZ pilot root",
    )
    args = parser.parse_args()

    lesson = course.parse_course_lesson(
        course.LESSON_DIR / f"{args.lang}_{args.unit}.md"
    )
    exercises = course.parse_exercises_file(
        course.BOOK_LOCAL_DIR / f"{args.lang}_{args.unit}.exercises.json"
    )

    # Optional enrichment sidecar: present+valid → short task line + spare
    # fields; invalid → HARD abort (a bad sidecar must never half-ship);
    # absent → legacy build exactly as before.
    enrichment: course.CourseEnrichment | None = None
    enrichment_path = (
        course.BOOK_LOCAL_DIR / f"{args.lang}_{args.unit}.enrichment.json"
    )
    if enrichment_path.is_file():
        try:
            enrichment = course.parse_enrichment_file(enrichment_path)
            course.validate_enrichment(exercises, enrichment)
        except course.CourseSourceError as exc:
            raise SystemExit(
                f"enrichment sidecar invalid — aborting build: {exc}"
            ) from exc
        log.info(
            "course.pilot.enrichment", mode="enriched",
            path=str(enrichment_path),
            blocks=len(enrichment.block_tasks),
            exercises=len(enrichment.exercises),
        )
    else:
        log.info(
            "course.pilot.enrichment", mode="legacy",
            reason="sidecar absent", path=str(enrichment_path),
        )

    lesson_audio: dict[tuple[int, str], course.SideAudio] = {}
    exercise_audio: dict[str, Path] = {}
    if args.audio:
        lesson_audio, exercise_audio, report = resolve_audio(
            args.api_base.rstrip("/"), lesson, exercises, enrichment
        )
        print(json.dumps(report, indent=1, ensure_ascii=False))

    root_override = resolve_deck_root(
        args.lang, args.unit, lesson.unit_label, args.production
    )
    stem = ("course" if args.production else "ZZ_pilot")
    out = course.BOOK_LOCAL_DIR / f"{stem}_{args.lang}_{args.unit}.apkg"
    result = course.build_course_apkg(
        out_path=out,
        lesson=lesson,
        exercises=exercises,
        root_override=root_override,
        lesson_audio=lesson_audio,
        exercise_audio=exercise_audio,
        enrichment=enrichment,
    )
    print(json.dumps(result, indent=1, ensure_ascii=False))
    print(f"apkg: {out}")

    plan = course.interleave_plan(lesson, exercises)
    print("\nfirst-exposure order (due positions):")
    print(" ".join(
        f"L{key}" if kind == "lesson" else "x" for kind, key, _due in plan
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
