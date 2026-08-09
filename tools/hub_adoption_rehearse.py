#!/usr/bin/env python3
"""F4 full-loop rehearsal on EPHEMERAL Postgres (never production).

Boots a throwaway Postgres, applies db/schema.sql, seeds the parent
expressions the adoption plan references, then:
  1. runs the applier TWICE (second run must insert zero rows —
     idempotency proof);
  2. exports adoption results (synthetic serial ids, real shape);
  3. re-runs the phase-5 compiler with the fresh server extract merged
     with those results;
  4. asserts the deferred population collapses to exactly the plan's
     still-deferred remainder.

Prints the numbers the coordinator's report needs.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from idiomatic.hub import adoption, phase5  # noqa: E402

HUB_DIR = REPO / "docs" / "research" / "hub_manifest"
SCHEMA = REPO / "db" / "schema.sql"


def boot_pg(root: Path) -> tuple[dict, Path]:
    if not (shutil.which("initdb") and shutil.which("pg_ctl")):
        raise SystemExit("postgres binaries not installed")
    data = root / "data"
    sock = Path(tempfile.mkdtemp(prefix="idiomatic_adoptpg_"))
    subprocess.run(["initdb", "-D", str(data), "-U", "postgres",
                    "-A", "trust", "--no-sync"],
                   check=True, capture_output=True)
    subprocess.run(
        ["pg_ctl", "start", "-D", str(data), "-w",
         "-l", str(root / "pg.log"),
         "-o", f"-k {sock} -p 54333 -c listen_addresses='' -F"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return ({"host": str(sock), "port": 54333, "user": "postgres",
             "database": "postgres"}, data)


async def rehearse() -> None:
    import asyncpg

    plan = adoption.load_plan(HUB_DIR / "adoption_plan.json")
    extract = phase5.load_server_extract(HUB_DIR
                                         / "fresh_server_extract.json")
    manifest_inputs = json.loads(
        (HUB_DIR / "compiler_expectations.json").read_text())
    c1 = json.loads((HUB_DIR / "C1_sense_resolution.json").read_text())
    c2 = json.loads((HUB_DIR / "C2_schedule_dossiers.json").read_text())

    root = Path(tempfile.mkdtemp(prefix="adopt_rehearsal_"))
    dsn, data_dir = boot_pg(root)
    try:
        conn = await asyncpg.connect(**dsn)
        try:
            await conn.execute(SCHEMA.read_text(encoding="utf-8"))
            # Production sequences are far beyond the real corpus ids; an
            # ephemeral DB would otherwise mint example ids 1..N that
            # collide with genuine extract ids and trip the compiler's
            # one-binding-per-example rule (rehearsal artifact only).
            await conn.execute(
                "SELECT setval('expression_examples_id_seq', 10000000)")
            await conn.execute(
                "SELECT setval('expression_idioms_id_seq', 10000000)")
            # Seed the parent expressions the plan references.
            expr_langs = {}
            for entry in extract["expressions"]:
                expr_langs[int(entry["expression_id"])] = \
                    (entry["lang"], entry["idiom"])
            seeded = 0
            for row in plan["adoptions"]:
                expression_id = int(row["expression_id"])
                lang, idiom = expr_langs.get(
                    expression_id, (row["language"], row["idiom_text"]))
                await conn.execute(
                    """INSERT INTO expressions (id, lang, text, normalized)
                       VALUES ($1, $2, $3, $4)
                       ON CONFLICT (id) DO NOTHING""",
                    expression_id, lang, idiom,
                    phase5.normalize_join(idiom))
                seeded += 1
            print(f"seeded parent expressions for {seeded:,} adoptions")

            first = await adoption.apply_plan(conn, plan)
            print(f"apply #1: {first}")
            second = await adoption.apply_plan(conn, plan)
            print(f"apply #2 (idempotency): {second}")
            assert second["inserted_sources"] == 0, second
            assert second["inserted_examples"] == 0, second
            assert first["inserted_examples"] == first["planned"], first

            # Boot-migration re-run must backfill the staged columns on
            # the adopted rows without disturbing them.
            await conn.execute(SCHEMA.read_text(encoding="utf-8"))
            null_positions = await conn.fetchval(
                "SELECT COUNT(*) FROM expression_examples "
                "WHERE position IS NULL")
            assert null_positions == 0, f"{null_positions} unpositioned"

            results = await adoption.export_results(conn,
                                                    plan["profile_key"])
            print(f"results exported: {len(results):,} adopted examples")
            assert len(results) == first["planned"]
        finally:
            await conn.close()
    finally:
        subprocess.run(["pg_ctl", "stop", "-D", str(data_dir),
                        "-m", "immediate"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ---- recompile: fresh-extract baseline, then + adoption results --------
    # The fresh corpus is newer than the campaign export the F3 manifest
    # used, so some formerly-joined cards may UNJOIN (server rows purged/
    # changed since). That drift is a phase-0-recensus fact, not an
    # adoption failure — quantify it instead of hiding it.
    baseline = phase5.compile_manifest(
        c1=c1, c2=c2, extract=json.loads(json.dumps(extract)),
        input_checksums={"note": "ephemeral-baseline", **manifest_inputs})
    merged = adoption.merge_adoption_results_into_extract(extract, results)
    manifest = phase5.compile_manifest(
        c1=c1, c2=c2, extract=merged,
        input_checksums={"note": "ephemeral-rehearsal", **manifest_inputs})
    counts = manifest["counts"]
    print("recompiled manifest (fresh extract + adoption results):")
    for key in ("conversions", "conversions_adoptable", "adopted_reps",
                "hub_notes", "deferred", "deferred_adoptable",
                "deferred_reps"):
        print(f"  {key}: {counts[key]:,}")

    planned = plan["counts"]["adoptions"]
    base_deferred = baseline["counts"]["deferred"]
    assert counts["deferred"] == base_deferred - planned, (
        f"adoption did not convert exactly its {planned} planned cards: "
        f"baseline deferred {base_deferred} -> {counts['deferred']}")

    original_ids = {int(c["card_id"]) for c in plan["resolved_existing"]} \
        | {int(a["card_id"]) for a in plan["adoptions"]} \
        | {int(d["card_id"]) for d in plan["deferred"]}
    drift = [g for g in manifest["gaps"]["deferred_cards"]
             if int(g["card_id"]) not in original_ids]
    drift_reps = sum(int(g.get("reps") or 0) for g in drift)
    print(f"ASSERT OK: adoption converted exactly its {planned} planned "
          f"cards (baseline deferred {base_deferred:,} -> "
          f"{counts['deferred']:,})")
    print(f"fresh-corpus drift: {len(drift):,} formerly-joined cards "
          f"unjoined ({drift_reps:,} reps) — phase-0 recensus material")
    for g in drift[:10]:
        print(f"  drift sample: card {g['card_id']} [{g['language']}] "
              f"verdict={g.get('verdict')} reps={g.get('reps')}")


if __name__ == "__main__":
    asyncio.run(rehearse())
