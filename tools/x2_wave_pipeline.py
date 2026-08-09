#!/usr/bin/env python3
"""Deterministic staging and merge checks for Exercises 2.0 waves 3--6.

The committed Italian-rebuild corpus is the aligned, read-only source of
truth: its input files own English prompts and durable IDs, while its output
files provide the repaired Italian reference.  This tool never calls a model,
TTS, a server endpoint, or Anki.  It only stages JSON, reports source-level
duplicates, and verifies/merges reviewed batch artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from idiomatic.grammar import exercises2 as x2  # noqa: E402

X2_DIR = REPO / "idiomatic" / "grammar" / "data" / "exercises2"
SOURCE_DIR = X2_DIR / "it_rebuild"
BATCH_DIR = X2_DIR / "batches"
NOTES_DIR = X2_DIR / "notes"
MANIFEST_DIR = BATCH_DIR / "manifests"
DUPLICATE_REPORT = (
    REPO
    / "docs"
    / "research"
    / "legacy_estate"
    / "exercises2_cross_topic_exact_duplicates.json"
)

LANGS = ("de", "es", "fr", "it", "pt")
WAVE_TOPICS = (
    "tenses",
    "fancy_vocab",
    "big_tech_vocab",
    "cold_war_vocab",
    "geopolitics",
    "big_tech_phrases",
)
ALL_SOURCE_TOPICS = (
    "big_tech_phrases",
    "big_tech_vocab",
    "cold_war_vocab",
    "commands",
    "conditionals",
    "connecting",
    "fancy_vocab",
    "geopolitics",
    "pronouns",
    "relfexive",
    "tenses",
)
CHUNK_SIZE = 100
# Waves 4--6 are commissioned at ~40-row chunks: vocabulary and shadowing
# notes are denser per item than the grammar waves, so 40 rows keeps one codex
# authoring invocation (and its hostile review) inside a single sitting.
# Wave 3 and the pilots keep CHUNK_SIZE so their committed manifests and
# staged inputs re-render byte-identically.
BULK_CHUNK_SIZE = 40
BULK_WAVE_PLANS = frozenset({"wave4", "wave5", "wave6"})
PLAN_CHUNK_SIZE: dict[str, int] = {plan: BULK_CHUNK_SIZE for plan in BULK_WAVE_PLANS}
# Owner verdict, 2026-08-09, ratifying pilots V1 + V2 + P1 verbatim:
# "this looks good to me too - all three formats".  This is the gate record
# that unlocks the bulk plans below (docs/research/legacy_estate/
# EXERCISES2_NEW_FORMAT_PILOTS.md carries the dated OWNER VERDICT section).
FORMAT_VERDICT_DATE = "2026-08-09"
FORMAT_VERDICT_QUOTE = "this looks good to me too - all three formats"

# These absences are settled audit facts, not optional tolerance.  Requiring
# exact equality catches a newly missing ref as well as accidental reinsertion
# of one of the quarantined 2023 PT phrase translations.
KNOWN_MISSING_REFS = frozenset(
    {
        ("tenses", "es", "it_tenses_001"),
        ("big_tech_vocab", "pt", "it_big_tech_vocab_052"),
        ("fancy_vocab", "pt", "it_fancy_vocab_312"),
        ("fancy_vocab", "pt", "it_fancy_vocab_484"),
        *{
            ("big_tech_phrases", "pt", f"it_big_tech_phrases_{number:03d}")
            for number in range(1, 31)
        },
    }
)


class PipelineError(ValueError):
    """A staged or reviewed artifact violates the wave contract."""


@dataclass(frozen=True)
class StageSpec:
    topic: str
    langs: tuple[str, ...]
    pilot: bool = False
    indices: tuple[int, ...] | None = None


# wave3 and the three pilots are the historical record and must keep
# re-rendering byte-identically.  wave4/wave5/wave6 are the bulk staging plans
# unlocked by the 2026-08-09 owner verdicts on V1/V2/P1 (FORMAT_VERDICT_DATE):
# wave4 = FANCY_VOCAB, wave5 = the specialist vocab trio, wave6 =
# BIG_TECH_PHRASES shadowing frames (separate draft model; not Exercises v1
# translation cards).  Staging never authors content; the codex lane does.
STAGE_PLANS: dict[str, tuple[StageSpec, ...]] = {
    "wave3": (StageSpec("tenses", LANGS),),
    "wave4": (StageSpec("fancy_vocab", LANGS),),
    "wave5": (
        StageSpec("big_tech_vocab", LANGS),
        StageSpec("cold_war_vocab", LANGS),
        StageSpec("geopolitics", LANGS),
    ),
    "wave6": (StageSpec("big_tech_phrases", LANGS),),
    "vocab-pilot": (
        StageSpec(
            "fancy_vocab",
            ("es",),
            pilot=True,
            # Ten verbs, ten nouns, five adjectives, five later academic
            # lexemes.  Selection stays in canonical source order.
            indices=tuple(
                list(range(0, 10))
                + list(range(93, 103))
                + list(range(339, 344))
                + list(range(488, 493))
            ),
        ),
    ),
    "geopolitics-pilot": (
        StageSpec("geopolitics", ("es",), pilot=True, indices=tuple(range(30))),
    ),
    "phrases-pilot": (
        # These are precisely the quarantined Spanish-as-PT legacy refs.  An
        # empty old_back makes the absence explicit without dropping prompts.
        StageSpec(
            "big_tech_phrases", ("pt",), pilot=True, indices=tuple(range(30))
        ),
    ),
}


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _numbered_paths(root: Path, topic: str) -> list[Path]:
    paths = list(root.glob(f"{topic}_[0-9][0-9].json"))
    return sorted(paths, key=lambda path: int(path.stem.rsplit("_", 1)[1]))


def _load_json_array(path: Path) -> list[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"{path}: cannot read JSON array: {exc}") from exc
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise PipelineError(f"{path}: expected an array of objects")
    return value


def load_topic(topic: str) -> tuple[list[dict], dict[str, dict], list[Path]]:
    """Load and validate one canonical topic in exact committed order."""
    if topic not in ALL_SOURCE_TOPICS:
        raise PipelineError(f"unsupported source topic {topic!r}")
    input_paths = _numbered_paths(SOURCE_DIR / "input", topic)
    output_paths = _numbered_paths(SOURCE_DIR / "output", topic)
    if not input_paths or [path.name for path in input_paths] != [
        path.name for path in output_paths
    ]:
        raise PipelineError(f"{topic}: input/output source chunk names do not match")

    inputs: list[dict] = []
    italian: dict[str, dict] = {}
    expected_number = 1
    for input_path, output_path in zip(input_paths, output_paths, strict=True):
        source_rows = _load_json_array(input_path)
        output_rows = _load_json_array(output_path)
        source_ids = [str(row.get("id", "")) for row in source_rows]
        output_ids = [str(row.get("id", "")) for row in output_rows]
        if source_ids != output_ids:
            raise PipelineError(f"{topic}: {output_path.name} does not preserve source IDs")
        for source_row, output_row in zip(source_rows, output_rows, strict=True):
            item_id = str(source_row.get("id", ""))
            expected_id = f"it_{topic}_{expected_number:03d}"
            if item_id != expected_id:
                raise PipelineError(
                    f"{topic}: expected canonical ID {expected_id!r}, got {item_id!r}"
                )
            en = source_row.get("en")
            refs = source_row.get("refs")
            if not isinstance(en, str) or not en.strip() or not isinstance(refs, dict):
                raise PipelineError(f"{topic}: {item_id}: malformed en/refs source row")
            if output_row.get("en") != en:
                raise PipelineError(f"{topic}: {item_id}: Italian output changed English")
            it = output_row.get("it")
            if not isinstance(it, str) or not it.strip():
                raise PipelineError(f"{topic}: {item_id}: missing Italian output")
            if item_id in italian:
                raise PipelineError(f"{topic}: duplicate canonical ID {item_id!r}")
            inputs.append(source_row)
            italian[item_id] = output_row
            expected_number += 1

    validate_missing_refs(topic, inputs)
    return inputs, italian, [*input_paths, *output_paths]


def validate_missing_refs(topic: str, rows: Sequence[dict]) -> None:
    actual: set[tuple[str, str, str]] = set()
    for row in rows:
        refs = row["refs"]
        for lang in ("de", "es", "fr", "pt"):
            if not isinstance(refs.get(lang), str) or not refs.get(lang, "").strip():
                actual.add((topic, lang, row["id"]))
    expected = {entry for entry in KNOWN_MISSING_REFS if entry[0] == topic}
    if actual != expected:
        missing = sorted(actual - expected)
        unexpectedly_present = sorted(expected - actual)
        raise PipelineError(
            f"{topic}: missing-ref allowlist drift; unexpected={missing}, "
            f"no-longer-missing={unexpectedly_present}"
        )


def _source_record(path: Path) -> dict[str, str]:
    data = path.read_bytes()
    return {"path": path.relative_to(REPO).as_posix(), "sha256": _sha256(data)}


def _selected_rows(rows: Sequence[dict], spec: StageSpec) -> list[dict]:
    if spec.indices is None:
        return list(rows)
    if tuple(sorted(set(spec.indices))) != spec.indices:
        raise PipelineError(f"{spec.topic}: pilot indices must be unique and ordered")
    if not spec.indices or spec.indices[-1] >= len(rows):
        raise PipelineError(f"{spec.topic}: pilot index outside source corpus")
    return [rows[index] for index in spec.indices]


def _expected_duplicate_drops() -> frozenset[tuple[str, str]]:
    """(topic, id) pairs the committed duplicate doctrine expects triage to drop.

    These are the non-preferred exact-English copies from the cross-topic
    report.  They stay staged — the authoring triage drops them (or keeps them
    with a documented distinct sense) per the report's triage_rule; the merged
    corpus is then enforced by check_merged_duplicates.
    """
    report = render_duplicate_report()
    return frozenset(
        (occurrence["topic"], occurrence["id"])
        for group in report["groups"]
        for occurrence in group["occurrences"]
        if occurrence["topic"] != group["preferred_topic"]
    )


def render_plan(plan: str) -> tuple[dict, dict[Path, bytes]]:
    """Return a deterministic manifest and staged-file byte map."""
    try:
        specs = STAGE_PLANS[plan]
    except KeyError as exc:
        raise PipelineError(f"unknown staging plan {plan!r}") from exc
    chunk_size = PLAN_CHUNK_SIZE.get(plan, CHUNK_SIZE)
    bulk = plan in BULK_WAVE_PLANS
    duplicate_drops = _expected_duplicate_drops() if bulk else frozenset()

    files: dict[Path, bytes] = {}
    source_records: dict[str, dict[str, str]] = {}
    chunks: list[dict] = []
    plan_topics: list[dict] = []
    for spec in specs:
        source_rows, italian, source_paths = load_topic(spec.topic)
        chosen = _selected_rows(source_rows, spec)
        for path in source_paths:
            record = _source_record(path)
            source_records[record["path"]] = record
        topic_record = {
            "topic": spec.topic,
            "mode": "pilot" if spec.pilot else "approved-full-wave",
            "languages": list(spec.langs),
            "source_rows": len(source_rows),
            "selected_rows": len(chosen),
            "selected_ids_sha256": _sha256(
                ("\n".join(row["id"] for row in chosen) + "\n").encode("utf-8")
            ),
            "owner_gate": (
                f"{spec.topic}-format-pilot-verdict" if spec.pilot else None
            ),
        }
        if bulk:
            topic_record["format_verdict"] = f"owner-approved {FORMAT_VERDICT_DATE}"
            topic_record["expected_duplicate_drops"] = sum(
                1 for row in chosen if (spec.topic, row["id"]) in duplicate_drops
            )
        plan_topics.append(topic_record)
        for lang in spec.langs:
            if lang not in LANGS:
                raise PipelineError(f"unsupported language {lang!r}")
            staged: list[dict] = []
            for row in chosen:
                item_id = row["id"]
                old_back = (
                    italian[item_id]["it"]
                    if lang == "it"
                    else row["refs"].get(lang, "")
                )
                staged.append({"id": item_id, "en": row["en"], "old_back": old_back})

            for offset in range(0, len(staged), chunk_size):
                batch_number = offset // chunk_size + 1
                suffix = f"pilot_b{batch_number:02d}" if spec.pilot else f"b{batch_number:02d}"
                name = f"{lang}_{spec.topic}_{suffix}.json"
                path = BATCH_DIR / "input" / name
                chunk_rows = staged[offset : offset + chunk_size]
                data = _json_bytes(chunk_rows)
                files[path] = data
                chunk_record = {
                    "path": path.relative_to(REPO).as_posix(),
                    "lang": lang,
                    "topic": spec.topic,
                    "mode": "pilot" if spec.pilot else "approved-full-wave",
                    "rows": len(chunk_rows),
                    "first_id": chunk_rows[0]["id"],
                    "last_id": chunk_rows[-1]["id"],
                    "missing_ref_ids": [
                        row["id"] for row in chunk_rows if not row["old_back"].strip()
                    ],
                    "sha256": _sha256(data),
                }
                if bulk:
                    chunk_record["expected_duplicate_drop_ids"] = [
                        row["id"]
                        for row in chunk_rows
                        if (spec.topic, row["id"]) in duplicate_drops
                    ]
                chunks.append(chunk_record)

    manifest = {
        "schema_version": 2 if bulk else 1,
        "generated_by": "tools/x2_wave_pipeline.py",
        "plan": plan,
        "chunk_size": chunk_size,
        "id_policy": "preserve canonical it_rebuild source IDs exactly",
        "order_policy": "preserve canonical source order; pilots preserve relative order",
    }
    if bulk:
        manifest["format_verdict"] = (
            f"V1/V2/P1 owner-approved {FORMAT_VERDICT_DATE}: "
            f"{FORMAT_VERDICT_QUOTE!r}"
        )
        manifest["duplicate_policy"] = (
            "expected_duplicate_drop_ids lists staged non-preferred exact-EN "
            "copies from the committed cross-topic report; staging never drops "
            "them — authoring triage does, unless the linguistic audit "
            "documents a distinct sense"
        )
    manifest.update(
        {
            "topics": plan_topics,
            "source_files": [source_records[key] for key in sorted(source_records)],
            "chunks": chunks,
        }
    )
    manifest_path = MANIFEST_DIR / f"{plan}.json"
    files[manifest_path] = _json_bytes(manifest)
    return manifest, files


def stage_plan(plan: str, *, check: bool = False) -> dict:
    manifest, files = render_plan(plan)
    mismatches: list[str] = []
    for path, expected in files.items():
        if check:
            if not path.exists() or path.read_bytes() != expected:
                mismatches.append(path.relative_to(REPO).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_bytes() != expected:
                path.write_bytes(expected)
    if mismatches:
        raise PipelineError(f"{plan}: staged files differ: {mismatches}")
    return manifest


def _preferred_topic(topics: Iterable[str]) -> str:
    priority = {
        "connecting": 0,
        "big_tech_vocab": 1,
        "cold_war_vocab": 1,
        "geopolitics": 1,
        "fancy_vocab": 2,
    }
    return min(topics, key=lambda topic: (priority.get(topic, 10), topic))


def render_duplicate_report() -> dict:
    occurrences: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    source_files: dict[str, dict[str, str]] = {}
    for topic in ALL_SOURCE_TOPICS:
        rows, _italian, paths = load_topic(topic)
        for path in paths:
            record = _source_record(path)
            source_files[record["path"]] = record
        for row in rows:
            exact = unicodedata.normalize("NFC", row["en"]).strip()
            occurrences[exact].append({"topic": topic, "id": row["id"]})

    groups: list[dict] = []
    for en, rows in occurrences.items():
        topics = {row["topic"] for row in rows}
        if len(topics) < 2:
            continue
        preferred = _preferred_topic(topics)
        groups.append(
            {
                "en": en,
                "preferred_topic": preferred,
                "triage_rule": (
                    f"keep in {preferred}; drop exact copies in other topics unless "
                    "a later linguistic audit documents a distinct sense"
                ),
                "occurrences": rows,
            }
        )
    groups.sort(key=lambda group: (group["en"].casefold(), group["en"]))
    return {
        "schema_version": 1,
        "generated_by": "tools/x2_wave_pipeline.py",
        "comparison": "NFC-normalized, outer-whitespace-trimmed, case-sensitive EN",
        "group_count": len(groups),
        "groups": groups,
        "source_files": [source_files[key] for key in sorted(source_files)],
    }


def duplicate_report(*, check: bool = False) -> dict:
    report = render_duplicate_report()
    expected = _json_bytes(report)
    if check:
        if not DUPLICATE_REPORT.exists() or DUPLICATE_REPORT.read_bytes() != expected:
            raise PipelineError("cross-topic duplicate report is stale")
    else:
        DUPLICATE_REPORT.parent.mkdir(parents=True, exist_ok=True)
        DUPLICATE_REPORT.write_bytes(expected)
    return report


_CHUNK_RE = re.compile(
    r"^(?P<lang>de|es|fr|it|pt)_(?P<topic>[a-z0-9]+(?:_[a-z0-9]+)*?)"
    r"(?:_(?P<pilot>pilot))?_b(?P<number>[0-9]{2})$"
)


def parse_chunk_name(chunk: str) -> tuple[str, str, bool, int]:
    match = _CHUNK_RE.fullmatch(chunk)
    if match is None:
        raise PipelineError(f"invalid batch chunk name {chunk!r}")
    return (
        match.group("lang"),
        match.group("topic"),
        match.group("pilot") is not None,
        int(match.group("number")),
    )


def _verified_chunk_notes(chunk: str) -> list[dict]:
    lang, topic, _pilot, _number = parse_chunk_name(chunk)
    input_path = BATCH_DIR / "input" / f"{chunk}.json"
    notes_path = BATCH_DIR / "output" / f"{chunk}_notes.json"
    triage_path = BATCH_DIR / "output" / f"{chunk}_triage.json"
    inputs = _load_json_array(input_path)
    notes = _load_json_array(notes_path)
    triage = _load_json_array(triage_path)
    input_ids = [row.get("id") for row in inputs]
    if [row.get("id") for row in triage] != input_ids:
        raise PipelineError(f"{chunk}: triage does not preserve input coverage/order")
    verdicts = [row.get("verdict") for row in triage]
    if any(verdict not in {"keep", "drop"} for verdict in verdicts):
        raise PipelineError(f"{chunk}: triage has invalid verdict")
    keep_ids = [
        row["id"] for row in triage if row.get("verdict") == "keep"
    ]
    if [row.get("id") for row in notes] != keep_ids:
        raise PipelineError(f"{chunk}: notes do not match keep verdicts in source order")
    input_en = {row["id"]: row["en"] for row in inputs}
    for row in notes:
        if row.get("en") != input_en[row["id"]]:
            raise PipelineError(f"{chunk}: {row['id']}: authored EN changed")
        x2._parse_note(Path(f"{lang}_{topic}.json"), lang, topic, row)
    return notes


def _target_chunks(lang: str, topic: str) -> list[str]:
    found: list[tuple[int, str]] = []
    for path in (BATCH_DIR / "input").glob(f"{lang}_{topic}_b[0-9][0-9].json"):
        parsed_lang, parsed_topic, pilot, number = parse_chunk_name(path.stem)
        if (parsed_lang, parsed_topic) == (lang, topic) and not pilot:
            found.append((number, path.stem))
    found.sort()
    if [number for number, _chunk in found] != list(range(1, len(found) + 1)):
        raise PipelineError(f"{lang}_{topic}: non-contiguous batch numbering")
    return [chunk for _number, chunk in found]


def _target(value: str) -> tuple[str, str]:
    match = re.fullmatch(r"(de|es|fr|it|pt)_(.+)", value)
    if match is None:
        raise PipelineError(f"invalid target {value!r}; use <lang>_<topic>")
    return match.group(1), match.group(2)


def expected_merged_notes(lang: str, topic: str) -> list[dict]:
    chunks = _target_chunks(lang, topic)
    if not chunks:
        raise PipelineError(f"{lang}_{topic}: no non-pilot batch inputs")
    result: list[dict] = []
    for chunk in chunks:
        result.extend(_verified_chunk_notes(chunk))
    return result


def verify_merge(lang: str, topic: str) -> int:
    expected = expected_merged_notes(lang, topic)
    path = NOTES_DIR / f"{lang}_{topic}.json"
    actual = _load_json_array(path)
    if (lang, topic) == ("es", "connecting"):
        pilot_input = _load_json_array(X2_DIR / "es_connecting_pilot_input.json")
        pilot_ids = [row["id"] for row in pilot_input]
        prefix = actual[: len(pilot_ids)]
        if [row.get("id") for row in prefix] != pilot_ids:
            raise PipelineError("es_connecting: legacy pilot prefix changed")
        actual = actual[len(pilot_ids) :]
    expected_ids = [row["id"] for row in expected]
    if [row.get("id") for row in actual] != expected_ids:
        raise PipelineError(
            f"{lang}_{topic}: merged IDs/order differ from reviewed keep verdicts"
        )
    expected_en = {row["id"]: row["en"] for row in expected}
    for row in actual:
        if row.get("en") != expected_en[row["id"]]:
            raise PipelineError(f"{lang}_{topic}: {row['id']}: merged EN changed")
        # A linguistic audit may improve authored fields after the batch gate;
        # validate that final note rather than requiring byte identity with the
        # pre-audit batch artifact.
        x2._parse_note(Path(f"{lang}_{topic}.json"), lang, topic, row)
    return len(expected)


def merge(lang: str, topic: str) -> int:
    if (lang, topic) == ("es", "connecting"):
        raise PipelineError("es_connecting has a legacy pilot prefix; verify only")
    expected = expected_merged_notes(lang, topic)
    path = NOTES_DIR / f"{lang}_{topic}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(expected))
    return len(expected)


def verify_all_merges() -> dict[str, int]:
    results: dict[str, int] = {}
    for path in sorted(NOTES_DIR.glob("*.json")):
        try:
            lang, topic = _target(path.stem)
        except PipelineError:
            continue
        if _target_chunks(lang, topic):
            results[path.stem] = verify_merge(lang, topic)
    return results


def check_merged_duplicates() -> int:
    """Reject exact EN copies retained in two topic decks for one language."""
    seen: defaultdict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for path in sorted(NOTES_DIR.glob("*.json")):
        try:
            lang, topic = _target(path.stem)
        except PipelineError:
            continue
        for row in _load_json_array(path):
            en = unicodedata.normalize("NFC", str(row.get("en", ""))).strip()
            seen[(lang, en)].append((topic, str(row.get("id", ""))))
    conflicts = {
        key: rows
        for key, rows in seen.items()
        if len({topic for topic, _item_id in rows}) > 1
    }
    if conflicts:
        sample = sorted(conflicts.items())[:5]
        raise PipelineError(f"cross-topic exact duplicates retained: {sample}")
    return len(seen)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser("stage", help="write/check one commissioned staging plan")
    stage.add_argument("plan", choices=sorted(STAGE_PLANS))
    stage.add_argument("--check", action="store_true")
    dupes = sub.add_parser("duplicate-report", help="write/check source duplicate report")
    dupes.add_argument("--check", action="store_true")
    sub.add_parser("check-merged-duplicates", help="reject retained cross-topic copies")
    verify = sub.add_parser("verify-merge", help="verify reviewed outputs against notes/")
    verify.add_argument("targets", nargs="*", help="<lang>_<topic>; default all landed")
    merge_parser = sub.add_parser("merge", help="merge one fully reviewed non-pilot target")
    merge_parser.add_argument("target", help="<lang>_<topic>")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "stage":
            manifest = stage_plan(args.plan, check=args.check)
            action = "verified" if args.check else "staged"
            print(f"{action} {args.plan}: {len(manifest['chunks'])} chunks")
        elif args.command == "duplicate-report":
            report = duplicate_report(check=args.check)
            action = "verified" if args.check else "wrote"
            print(f"{action} duplicate report: {report['group_count']} groups")
        elif args.command == "check-merged-duplicates":
            count = check_merged_duplicates()
            print(f"PASS merged cross-topic exact-duplicate check ({count} EN keys)")
        elif args.command == "verify-merge":
            if args.targets:
                results = {}
                for target in args.targets:
                    lang, topic = _target(target)
                    results[target] = verify_merge(lang, topic)
            else:
                results = verify_all_merges()
            for target, count in results.items():
                print(f"PASS {target}: {count} reviewed batch notes")
        elif args.command == "merge":
            lang, topic = _target(args.target)
            count = merge(lang, topic)
            print(f"merged {args.target}: {count} notes")
    except (PipelineError, x2.Ex2SourceError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
