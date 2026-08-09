#!/usr/bin/env python3
"""Build the disposable Grammar Course pilot APKG for one unit.

Usage:
    .venv/bin/python tools/course_build_pilot.py de kasus

Reads the committed lesson script (idiomatic/grammar/data/course/lessons/)
and the machine-local, gitignored exercise file (…/course/book_local/),
then writes ``…/course/book_local/ZZ_pilot_<lang>_<unit>.apkg`` — also
gitignored (*.apkg) — under the disposable review root
``ZZ Grammar Course Pilot (disposable)``.

The pilot ships audio-pending: FrontAudio/BackAudio/SolutionAudio are
empty and every note carries the ``idiomatic-course-audio-pending`` tag.
The local-TTS seeding contract is documented in
docs/GRAMMAR_COURSE_DESIGN.md §Audio.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from idiomatic.grammar import course  # noqa: E402

PILOT_ROOT = "ZZ Grammar Course Pilot (disposable)"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    lang, unit = sys.argv[1], sys.argv[2]
    lesson = course.parse_course_lesson(
        course.LESSON_DIR / f"{lang}_{unit}.md"
    )
    exercises = course.parse_exercises_file(
        course.BOOK_LOCAL_DIR / f"{lang}_{unit}.exercises.json"
    )
    out = course.BOOK_LOCAL_DIR / f"ZZ_pilot_{lang}_{unit}.apkg"
    result = course.build_course_apkg(
        out_path=out,
        lesson=lesson,
        exercises=exercises,
        root_override=PILOT_ROOT,
    )
    print(json.dumps(result, indent=1, ensure_ascii=False))
    print(f"apkg: {out}")

    plan = course.interleave_plan(lesson, exercises)
    print("\nfirst-exposure order (due positions):")
    line: list[str] = []
    for kind, key, _due in plan:
        line.append(f"L{key}" if kind == "lesson" else "x")
    print(" ".join(line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
