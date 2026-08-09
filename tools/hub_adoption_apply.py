#!/usr/bin/env python3
"""F4 adoption applier — idempotent, batched, journaled, INSERT-ONLY.

Writes the adoption plan's proposed source-occurrence + example rows.
No UPDATE beyond nothing, no DELETE ever. Refuses to run unless ALL of:
  (a) the plan's content checksum verifies AND matches the committed
      .sha256 sidecar;
  (b) the target database carries the F1 staging (probes
      expression_examples.stable_key and the partial unique indexes);
  (c) --apply is passed AND the coordinator go-token file exists
      (default docs/research/hub_manifest/ADOPTION_GO_TOKEN — created
      by the coordinator, never by this tool).

Post-apply: --export-results writes adoption_results.json (stable_key ->
real example_id) for the phase-5 recompile.

Rehearsed against ephemeral Postgres by tools/hub_adoption_rehearse.py;
production --apply is coordinator-gated.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from idiomatic.hub import adoption, phase5  # noqa: E402

HUB_DIR = REPO / "docs" / "research" / "hub_manifest"
DEFAULT_GO_TOKEN = HUB_DIR / "ADOPTION_GO_TOKEN"

STAGING_PROBES = (
    ("column", "expression_examples", "stable_key"),
    ("column", "expression_examples", "source_kind"),
    ("column", "expression_idioms", "source_key"),
    ("index", "expression_examples_stable_key", None),
    ("index", "expression_idioms_expr_source_key", None),
)


async def probe_staging(conn) -> list[str]:
    problems = []
    for kind, name_a, name_b in STAGING_PROBES:
        if kind == "column":
            ok = await conn.fetchval(
                """SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_name = $1 AND column_name = $2""",
                name_a, name_b)
        else:
            ok = await conn.fetchval(
                "SELECT COUNT(*) FROM pg_indexes WHERE indexname = $1",
                name_a)
        if not ok:
            problems.append(f"missing {kind}: {name_a}"
                            + (f".{name_b}" if name_b else ""))
    return problems


async def run(args) -> None:
    import asyncpg

    plan = adoption.load_plan(args.plan)
    sidecar = args.plan.with_name(args.plan.name + ".sha256")
    if not sidecar.exists():
        raise SystemExit(f"missing plan sidecar {sidecar}")
    if sidecar.read_text().strip() != plan["content_sha256"]:
        raise SystemExit("plan sidecar checksum mismatch — the plan file "
                         "is not the reviewed one")

    counts = plan["counts"]
    print(f"plan {plan['content_sha256'][:16]}…: "
          f"{counts['adoptions']:,} adoptions "
          f"({counts['adoption_reps']:,} reps), profile "
          f"{plan['profile_key']!r}")

    dsn = args.dsn or os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("no --dsn and no DATABASE_URL")
    conn = await asyncpg.connect(dsn)
    try:
        staging_problems = await probe_staging(conn)
        if staging_problems:
            raise SystemExit("F1 staging not live on target DB: "
                             + "; ".join(staging_problems))
        print("staging probes OK")

        if args.export_results:
            rows = await adoption.export_results(conn, plan["profile_key"])
            out = args.export_results
            payload = {"profile_key": plan["profile_key"],
                       "plan_content_sha256": plan["content_sha256"],
                       "exported_at": dt.datetime.now(dt.UTC).isoformat(),
                       "rows": rows}
            out.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print(f"results exported: {out} ({len(rows):,} rows)")
            if not args.apply:
                return

        if not args.apply:
            print("DRY RUN: no rows written. --apply requires the "
                  f"coordinator go-token at {args.go_token}")
            return
        if not args.go_token.exists() or \
                not args.go_token.read_text().strip():
            raise SystemExit(f"go-token missing/empty: {args.go_token} — "
                             "production apply is coordinator-gated")

        result = await adoption.apply_plan(conn, plan,
                                           batch_size=args.batch_size)
        journal = {
            "applied_at": dt.datetime.now(dt.UTC).isoformat(),
            "plan_content_sha256": plan["content_sha256"],
            "go_token": args.go_token.read_text().strip(),
            "dsn_host": dsn.split("@")[-1].split("/")[0],
            **result,
        }
        args.journal_out.parent.mkdir(parents=True, exist_ok=True)
        args.journal_out.write_text(
            json.dumps(journal, indent=2) + "\n", encoding="utf-8")
        print(f"applied: {result['inserted_sources']:,} source rows, "
              f"{result['inserted_examples']:,} example rows "
              f"(planned {result['planned']:,}); journal: "
              f"{args.journal_out}")
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path,
                        default=HUB_DIR / "adoption_plan.json")
    parser.add_argument("--dsn", default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--go-token", type=Path, default=DEFAULT_GO_TOKEN)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--journal-out", type=Path,
                        default=HUB_DIR / "adoption_apply_journal.json")
    parser.add_argument("--export-results", type=Path, default=None,
                        help="write adoption_results.json from the target "
                             "DB (read-only unless --apply also given)")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
