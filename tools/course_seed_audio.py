#!/usr/bin/env python3
"""Seed one Grammar Course unit's narration into the local-TTS queue.

Usage:
    .venv/bin/python tools/course_seed_audio.py de kasus
        [--api-base https://idiomatic-app.onrender.com] [--no-exercises]
        [--pilot-priority]

POSTs `/admin/local-tts/v1/course/seed`: the server parses the committed
lesson script itself; the book-derived exercises file
(idiomatic/grammar/data/course/book_local/<lang>_<unit>.exercises.json)
is sent in the request body because that content never rides the public
repo. Seeding is idempotent — completed, current clips are never
disturbed; only new/changed texts queue.

If the contract-2 enrichment sidecar (…/<lang>_<unit>.enrichment.json)
exists, each payload row's solution_html is substituted with the
effective speakable solution (the complete production sentence) before
POSTing — the server derives spoken text from the payload, so this alone
re-voices exactly the exercises that gained a full sentence.  An invalid
sidecar ABORTS the seed (same policy as the build).

``--pilot-priority`` marks the jobs is_pilot so the machine worker claims
them ahead of bulk backlog (e.g. an in-flight expression-pool render).

Admin credentials: ``ADMIN_TOKEN`` env var, else the ``ADMIN_TOKEN=…``
line in ``~/.config/idiomatic-admin.env``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from idiomatic.grammar import course  # noqa: E402
from tools.course_build_pilot import DEFAULT_API_BASE, admin_token  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lang")
    parser.add_argument("unit")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--no-exercises", action="store_true",
                        help="seed lesson narration only")
    parser.add_argument("--pilot-priority", action="store_true",
                        help="claim ahead of bulk queue backlog")
    args = parser.parse_args()

    body: dict = {"lang": args.lang, "unit": args.unit,
                  "is_pilot": args.pilot_priority}
    if not args.no_exercises:
        exercises_path = (
            course.BOOK_LOCAL_DIR / f"{args.lang}_{args.unit}.exercises.json"
        )
        body["exercises"] = json.loads(
            exercises_path.read_text(encoding="utf-8")
        )
        enrichment_path = (
            course.BOOK_LOCAL_DIR / f"{args.lang}_{args.unit}.enrichment.json"
        )
        if enrichment_path.is_file():
            exercises = course.parse_exercises_file(exercises_path)
            try:
                enrichment = course.parse_enrichment_file(enrichment_path)
                course.validate_enrichment(exercises, enrichment)
            except course.CourseSourceError as exc:
                raise SystemExit(
                    f"enrichment sidecar invalid — aborting seed: {exc}"
                ) from exc
            body["exercises"] = course.enrich_seed_payload(
                body["exercises"], enrichment
            )
            print("enrichment: effective solutions substituted into payload")

    import httpx

    response = httpx.post(
        f"{args.api_base.rstrip('/')}/admin/local-tts/v1/course/seed",
        json=body,
        headers={"X-Admin-Token": admin_token()},
        timeout=120,
    )
    print(response.status_code)
    print(json.dumps(response.json(), indent=1, ensure_ascii=False))
    return 0 if response.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
