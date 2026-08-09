#!/usr/bin/env python3
"""Compile the phase-5 hub manifest from C1 + C2 + the server extract.

Data-only: no collection is opened. Refuses to run when any input's
checksum differs from the committed expectations file
(docs/research/hub_manifest/compiler_expectations.json) — re-recording
expectations is an explicit, reviewed act (--record-expectations).

Default server extract: the committed illustration-campaign export
(idiomatic/grammar/data/illustration_prompts/input/, produced by
/admin/corpus-export). A C3 extract file drops in via --server-extract
with the same {expressions: [...]} shape.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from idiomatic.hub import phase5  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
HUB_DIR = REPO / "docs" / "research" / "hub_manifest"
ILLU_INPUT = (REPO / "idiomatic" / "grammar" / "data"
              / "illustration_prompts" / "input")
DEFAULT_EXPECTATIONS = HUB_DIR / "compiler_expectations.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c1", type=Path,
                        default=HUB_DIR / "C1_sense_resolution.json")
    parser.add_argument("--c2", type=Path,
                        default=HUB_DIR / "C2_schedule_dossiers.json")
    parser.add_argument("--server-extract", type=Path, default=None,
                        help="C3-style extract JSON; default = committed "
                             "illustration-campaign export")
    parser.add_argument("--expectations", type=Path,
                        default=DEFAULT_EXPECTATIONS)
    parser.add_argument("--out", type=Path,
                        default=HUB_DIR / "phase5_manifest.json")
    parser.add_argument("--record-expectations", action="store_true",
                        help="write the observed input checksums as the new "
                             "expectations (reviewed act; commit the file)")
    parser.add_argument("--adoption-results", type=Path, default=None,
                        help="post-apply adoption_results.json — merges the "
                             "adopted example identities into the extract "
                             "so formerly deferred cards join")
    parser.add_argument("--asset-coverage", type=Path, default=None,
                        help="C3 asset-coverage JSON — annotates hub "
                             "examples with per-asset status (enrichment "
                             "layer, never a blocker)")
    parser.add_argument("--expect-deferred-max", type=int, default=None,
                        help="fail if the compiled manifest defers more "
                             "cards than this")
    args = parser.parse_args()

    actual = {
        "C1_sense_resolution.json": phase5.sha256_file(args.c1),
        "C2_schedule_dossiers.json": phase5.sha256_file(args.c2),
    }
    if args.server_extract is not None:
        actual["server_extract"] = phase5.sha256_file(args.server_extract)
    else:
        actual["server_extract"] = phase5.directory_extract_sha256(
            ILLU_INPUT, "*_illu_b*.json")
    if args.adoption_results is not None:
        actual["adoption_results"] = phase5.sha256_file(
            args.adoption_results)
    if args.asset_coverage is not None:
        actual["asset_coverage"] = phase5.sha256_file(args.asset_coverage)

    if args.record_expectations:
        args.expectations.write_text(
            json.dumps(actual, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        print(f"expectations recorded: {args.expectations}")
    else:
        if not args.expectations.exists():
            raise SystemExit(f"no expectations file at {args.expectations}; "
                             "run once with --record-expectations and commit")
        expected = json.loads(args.expectations.read_text(encoding="utf-8"))
        phase5.check_expectations(expected, actual)
        print("input checksums match recorded expectations")

    c1 = json.loads(args.c1.read_text(encoding="utf-8"))
    c2 = json.loads(args.c2.read_text(encoding="utf-8"))
    if args.server_extract is not None:
        extract = phase5.load_server_extract(args.server_extract)
    else:
        extract = phase5.load_server_extract_from_illustration_inputs(
            ILLU_INPUT)
    if args.adoption_results is not None:
        from idiomatic.hub import adoption  # noqa: E402
        results = json.loads(
            args.adoption_results.read_text(encoding="utf-8"))
        extract = adoption.merge_adoption_results_into_extract(
            extract, results["rows"])
        print(f"merged {len(results['rows']):,} adopted example "
              f"identities into the extract")

    manifest = phase5.compile_manifest(c1=c1, c2=c2, extract=extract,
                                       input_checksums=actual)
    if args.asset_coverage is not None:
        coverage = phase5.load_asset_coverage(args.asset_coverage)
        manifest = phase5.apply_asset_coverage(manifest, coverage)
        print(f"asset coverage applied: "
              f"{manifest['counts']['asset_qa_passed_examples']:,} "
              f"qa-passed examples, "
              f"{manifest['asset_coverage']['examples_missing_coverage']:,} "
              f"missing coverage rows")
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    (args.out.parent / (args.out.name + ".sha256")).write_text(
        manifest["content_sha256"] + "\n", encoding="utf-8")

    counts = manifest["counts"]
    print(f"manifest written: {args.out}")
    print(f"  content sha256: {manifest['content_sha256'][:16]}…")
    for key in ("c2_cards", "conversions", "conversions_adoptable",
                "conversions_fresh_trivial", "adopted_reps", "hub_notes",
                "deferred", "joinkey_quarantine_cards",
                "c1_quarantine_groups", "c1_archive_notes"):
        print(f"  {key}: {counts[key]:,}")
    reasons: dict[str, int] = {}
    for gap in manifest["gaps"]["deferred_cards"]:
        reasons[gap["reason"]] = reasons.get(gap["reason"], 0) + 1
    for reason, count in sorted(reasons.items()):
        print(f"  deferred[{reason}]: {count:,}")
    if args.expect_deferred_max is not None and \
            counts["deferred"] > args.expect_deferred_max:
        raise SystemExit(f"deferred {counts['deferred']} exceeds "
                         f"--expect-deferred-max {args.expect_deferred_max}")


if __name__ == "__main__":
    main()
