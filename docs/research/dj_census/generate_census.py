#!/usr/bin/env python3
"""Generate the read-only DJ-C1 study telemetry census.

The source collection is opened with SQLite's immutable, read-only URI mode.
Only the two report files in this directory are written.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
import json
import math
from pathlib import Path
import re
import sqlite3
from statistics import mean, pstdev
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "docs/research/anki_reorg_work/live_cutover_20260807T072826Z/collection.anki2"
OUT_DIR = Path(__file__).resolve().parent
JSON_OUT = OUT_DIR / "study_census.json"
MD_OUT = OUT_DIR / "study_census.md"

TIME_CAP_MS = 60_000
SESSION_GAP_MS = 30 * 60 * 1_000
THIN_CELL_REPS = 30
MIX_DAYS = 60
SESSION_DAYS = 90
LOCAL_TZ_NAME = "Asia/Singapore"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME)
DECK_SEPARATOR = re.compile(r"::|\x1f")

LANGUAGES = {
    "DE German": "DE German",
    "ES Spanish": "ES Spanish",
    "FR French": "FR French",
    "IT Italian": "IT Italian",
    "PT Portuguese": "PT Portuguese",
    "ZH Mandarin": "ZH Mandarin",
}
LANGUAGE_ORDER = [*LANGUAGES, "other"]

LANE_TO_POPULATION = {
    "1 Expressions": "Expressions",
    "2 Grammar": "Grammar",
    "3 Tenses": "Tenses",
    "4 Exercises": "Exercises",
    "5 Translation": "Translation",
    "6 My Errors": "My Errors",
    "7 Rescue": "Rescue",
    "8 Pimsleur": "Pimsleur",
}
POPULATION_ORDER = [
    "Expressions",
    "Grammar",
    "Tenses",
    "Exercises",
    "Translation",
    "My Errors",
    "Rescue",
    "Pimsleur",
    "lessons",
    "other",
]
MATURITY_ORDER = ["learning", "relearning", "review_young", "review_mature", "filtered"]
RATING_LABELS = {1: "again", 2: "hard", 3: "good", 4: "easy"}
PODCAST_TAG_RULES = (
    "idiomatic-podcast",
    "chinesepod",
    "podcast",
)


def register_unicase(connection: sqlite3.Connection) -> None:
    """The collection's custom collation is needed even for simple selects."""

    connection.create_collation(
        "unicase",
        lambda left, right: (left.casefold() > right.casefold())
        - (left.casefold() < right.casefold()),
    )


def split_deck(name: str) -> list[str]:
    return [part for part in DECK_SEPARATOR.split(name or "") if part]


def is_podcast_tag(tag: str) -> bool:
    return any(tag == prefix or tag.startswith(prefix + "::") for prefix in PODCAST_TAG_RULES)


def classify_deck(deck_name: str | None, raw_tags: str | None) -> tuple[str, str, str]:
    """Return language, population, and an auditable mapping reason.

    A recognized language root plus an explicit podcast tag maps to lessons.
    A recognized language root plus a numbered estate lane maps to that lane.
    Everything else is deliberately `other`; no language is inferred from
    legacy archive tags or arbitrary text deeper in a deck path.
    """

    parts = split_deck(deck_name or "")
    root = parts[0] if parts else ""
    if root not in LANGUAGES:
        return "other", "other", "unknown_root"
    language = LANGUAGES[root]
    tags = (raw_tags or "").split()
    if any(is_podcast_tag(tag) for tag in tags):
        return language, "lessons", "podcast_tag"
    for part in parts[1:]:
        if part in LANE_TO_POPULATION:
            return language, LANE_TO_POPULATION[part], "estate_lane"
    return language, "other", "outside_estate_lane"


def quantile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def stats(values: list[float], *, include_sum: bool = False) -> dict[str, float | int] | None:
    if not values:
        return None
    result: dict[str, float | int] = {
        "count": len(values),
        "min": round(min(values), 4),
        "p25": round(quantile(values, 0.25) or 0, 4),
        "median": round(quantile(values, 0.50) or 0, 4),
        "p75": round(quantile(values, 0.75) or 0, 4),
        "max": round(max(values), 4),
        "mean": round(mean(values), 4),
        "pstdev": round(pstdev(values), 4) if len(values) > 1 else 0,
    }
    if include_sum:
        result["sum"] = round(sum(values), 4)
    return result


def pct(numerator: int | float, denominator: int | float) -> float:
    return round((100 * numerator / denominator) if denominator else 0, 4)


def iso_local(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=LOCAL_TZ).isoformat()


def local_date(ts_ms: int) -> date:
    return datetime.fromtimestamp(ts_ms / 1000, tz=LOCAL_TZ).date()


def round_seconds(milliseconds: int | float) -> float:
    return round(milliseconds / 1000, 3)


def ordered_cells(cells: set[tuple[str, str]] | list[tuple[str, str]]) -> list[tuple[str, str]]:
    language_rank = {value: index for index, value in enumerate(LANGUAGE_ORDER)}
    population_rank = {value: index for index, value in enumerate(POPULATION_ORDER)}
    return sorted(
        set(cells),
        key=lambda cell: (
            language_rank.get(cell[0], len(language_rank)),
            population_rank.get(cell[1], len(population_rank)),
            cell,
        ),
    )


def ratings(counter: Counter[int]) -> dict[str, object]:
    total = sum(counter.values())
    return {
        "rep_count": total,
        "counts": {label: counter.get(value, 0) for value, label in RATING_LABELS.items()},
        "percentages": {
            label: pct(counter.get(value, 0), total)
            for value, label in RATING_LABELS.items()
        },
    }


def maturity_band(revlog_type: int, interval: int) -> str:
    if revlog_type == 0:
        return "learning"
    if revlog_type == 2:
        return "relearning"
    if revlog_type == 3:
        return "filtered"
    return "review_mature" if interval > 21 else "review_young"


def session_summary(events: list[dict[str, object]]) -> dict[str, object]:
    first = events[0]
    last = events[-1]
    languages = [str(event["language"]) for event in events]
    language_counts = Counter(languages)
    transitions = sum(left != right for left, right in zip(languages, languages[1:]))
    active_ms = sum(int(event["capped_time_ms"]) for event in events)
    elapsed_ms = int(last["ts_ms"]) - int(first["ts_ms"]) + int(last["capped_time_ms"])
    return {
        "start": str(first["local_ts"]),
        "end": str(last["local_ts"]),
        "date": str(first["local_date"]),
        "reps": len(events),
        "active_seconds_capped": round_seconds(active_ms),
        "elapsed_seconds_estimate": round_seconds(elapsed_ms),
        "languages": sorted(language_counts),
        "language_count": len(language_counts),
        "language_reps": dict(sorted(language_counts.items())),
        "language_transitions": transitions,
        "interleaved": transitions > 0,
    }


def cluster_sessions(events: list[dict[str, object]]) -> list[dict[str, object]]:
    if not events:
        return []
    sessions: list[dict[str, object]] = []
    current: list[dict[str, object]] = [events[0]]
    for event in events[1:]:
        if int(event["ts_ms"]) - int(current[-1]["ts_ms"]) > SESSION_GAP_MS:
            sessions.append(session_summary(current))
            current = []
        current.append(event)
    sessions.append(session_summary(current))
    return sessions


def render_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        values = [str(value).replace("|", "\\|").replace("\n", " ") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def format_stats(stat: dict[str, object] | None, suffix: str = "") -> str:
    if not stat:
        return "—"
    return (
        f"n={stat['count']}; p25={stat['p25']}{suffix}; "
        f"median={stat['median']}{suffix}; p75={stat['p75']}{suffix}; "
        f"mean={stat['mean']}{suffix}; max={stat['max']}{suffix}"
    )


def format_ms_stat(stat: dict[str, object] | None, key: str) -> str:
    if not stat or stat.get(key) is None:
        return "—"
    return f"{round_seconds(float(stat[key])):.3f}"


def build_markdown(report: dict[str, object]) -> str:
    source = report["source"]
    methods = report["methods"]
    mapping = report["mapping_audit"]
    seconds = report["seconds_per_rep"]
    sessions = report["session_anatomy"]
    mix = report["mix_history"]
    rating = report["rating_profile"]
    lines: list[str] = []
    lines += [
        "# DJ-C1 study telemetry census",
        "",
        "Deterministic, read-only census of the live Anki collection. The machine-readable companion is `study_census.json`.",
        "",
        "## Methods",
        "",
        f"- Source: `{source['path']}`; {source['revlog_rows_total']:,} revlog rows, {source['revlog_rows_joined']:,} joinable to current cards, and {source['orphaned_revlog_rows']:,} orphaned rows excluded from card metrics.",
        f"- Local calendar/time-of-day zone: `{methods['timezone']}`. The observed revlog endpoint is `{source['max_revlog_local']}`; the 90-day window is `{sessions['window']['start']}` through `{sessions['window']['end']}`, and the 60-day mix window is `{mix['window']['start']}` through `{mix['window']['end']}`.",
        f"- Deck paths use Anki's current `\\x1f` separator (the brief's `::` notation is equivalent). Numbered estate lanes map to populations; explicit podcast tags map a recognized language root to `lessons`. Unknown roots and recognized roots without an estate lane are `other`; tags are not used to infer a language.",
        f"- Revlog `time` is milliseconds. Planning stats use `min(time, 60000)`; {seconds['cap_effect']['at_or_above_60s_count']:,} of {seconds['cap_effect']['rep_count']:,} joinable reps ({seconds['cap_effect']['at_or_above_60s_pct']}%) are at the 60-second censoring boundary, while {seconds['cap_effect']['raw_gt_60s_count']:,} exceed it. A cell with fewer than {methods['thin_cell_rep_threshold']} reps falls back to the global population median, then the global median.",
        f"- Sessions are clusters where the gap between consecutive revlog timestamps is at most {methods['session_gap_minutes']} minutes. Active seconds are capped per rep; elapsed session seconds are first-to-last timestamp plus the final capped rep time.",
        f"- Maturity is event-based: learning/relearning/filtered from revlog type; review cards are young at `ivl <= 21` days and mature at `ivl > 21` days. Ratings are raw counts and percentages only; no weakness weighting is proposed.",
        "- Historical `_tenses_old`/legacy material was consulted only as context and is not merged into the current-account counts.",
        "",
        "## Source and mapping audit",
        "",
    ]
    lines += render_table(
        ["Metric", "Count"],
        [
            ["Current cards", f"{source['current_cards']:,}"],
            ["Current notes", f"{source['current_notes']:,}"],
            ["Deck rows", f"{source['current_decks']:,}"],
            ["All revlog rows", f"{source['revlog_rows_total']:,}"],
            ["Joinable revlog rows used", f"{source['revlog_rows_joined']:,}"],
            ["Orphaned revlog rows excluded", f"{source['orphaned_revlog_rows']:,}"],
        ],
    )
    lines += ["", "### Current-card mapping", ""]
    lines += render_table(
        ["Reason", "Cards", "Revlog reps"],
        [
            [reason, f"{mapping['cards_by_reason'].get(reason, 0):,}", f"{mapping['reps_by_reason'].get(reason, 0):,}"]
            for reason in sorted(set(mapping["cards_by_reason"]) | set(mapping["reps_by_reason"]))
        ],
    )
    lines += ["", "### Mapped language/population cells", ""]
    lines += render_table(
        ["Language", "Population", "Cards", "Revlog reps"],
        [
            [row["language"], row["population"], f"{row['cards']:,}", f"{row['reps']:,}"]
            for row in mapping["mapped_cells"]
        ],
    )
    lines += ["", "## Seconds per rep", ""]
    sec_rows = []
    for cell in seconds["cells"]:
        capped = cell["capped_time_ms"]
        raw = cell["raw_time_ms"]
        sec_rows.append(
            [
                cell["language"],
                cell["population"],
                f"{cell['card_count']:,}",
                f"{cell['rep_count']:,}",
                format_ms_stat(capped, "p25"),
                format_ms_stat(capped, "median"),
                format_ms_stat(capped, "p75"),
                f"{cell['recommended_planning_seconds']:.3f} ({cell['planning_source']})",
                f"{cell['at_or_above_60s_count']:,} ({cell['at_or_above_60s_pct']}%)",
                format_ms_stat(raw, "median"),
            ]
        )
    lines += render_table(
        ["Language", "Population", "Cards", "Reps", "Capped p25 s", "Capped median s", "Capped p75 s", "Planning constant", "At 60s cap", "Raw median s"],
        sec_rows,
    )
    lines += ["", "### Global fallback table", ""]
    lines += render_table(
        ["Population", "Reps", "Capped p25 s", "Capped median s", "Capped p75 s", "Fallback constant s"],
        [
            [
                row["population"],
                f"{row['rep_count']:,}",
                f"{round_seconds(row['capped_time_ms']['p25']):.3f}",
                f"{round_seconds(row['capped_time_ms']['median']):.3f}",
                f"{round_seconds(row['capped_time_ms']['p75']):.3f}",
                f"{row['planning_constant_seconds']:.3f} ({row['planning_source']})",
            ]
            for row in seconds["global_fallbacks"]
        ],
    )
    lines += ["", "## Session anatomy (last 90 calendar days)", ""]
    daily = sessions["daily"]
    lines += render_table(
        ["Measure", "Value"],
        [
            ["Calendar days", sessions["window"]["calendar_days"]],
            ["Study days", sessions["daily_summary"]["study_days"]],
            ["Sessions", f"{sessions['session_count']:,}"],
            ["Mean sessions / calendar day", sessions["daily_summary"]["sessions_per_calendar_day"]["mean"]],
            ["Mean sessions / study day", sessions["daily_summary"]["sessions_per_study_day"]],
            ["Active minutes / calendar day", format_stats(sessions["daily_summary"]["active_minutes_per_calendar_day"], " min")],
            ["Elapsed minutes / calendar day", format_stats(sessions["daily_summary"]["elapsed_minutes_per_calendar_day"], " min")],
            ["One-language sessions", f"{sessions['language_interleaving']['single_language_sessions']:,} ({sessions['language_interleaving']['single_language_pct']}%)"],
            ["Mixed-language sessions", f"{sessions['language_interleaving']['mixed_language_sessions']:,} ({sessions['language_interleaving']['mixed_language_pct']}%)"],
            ["Sessions with an actual language transition", f"{sessions['language_interleaving']['interleaved_sessions']:,} ({sessions['language_interleaving']['interleaved_pct']}%)"],
            ["Active session length", format_stats(sessions["session_length_seconds"]["active"], " s")],
            ["Elapsed session length", format_stats(sessions["session_length_seconds"]["elapsed"], " s")],
        ],
    )
    lines += ["", "### Sessions by language count", ""]
    lines += render_table(
        ["Languages in session", "Sessions"],
        [[key, f"{value:,}"] for key, value in sessions["languages_per_session"].items()],
    )
    lines += ["", "### Active session-length histogram", ""]
    lines += render_table(
        ["Active length", "Sessions"],
        [[key, value] for key, value in sessions["session_length_histogram_active"].items()],
    )
    lines += ["", "### Observed language transitions", ""]
    lines += render_table(
        ["Transition", "Count"],
        [[key, value] for key, value in sessions["language_interleaving"]["language_transitions"].items()] or [["—", 0]],
    )
    lines += ["", "### Time of day (local hour)", ""]
    lines += render_table(
        ["Hour", "Session starts", "Start active min", "Reps", "Rep active min"],
        [
            [row["hour"], row["session_starts"], row["start_active_minutes"], row["reps"], row["rep_active_minutes"]]
            for row in sessions["time_of_day"]
        ],
    )
    lines += ["", "### Session inventory", ""]
    lines += render_table(
        ["#", "Start", "End", "Reps", "Active min", "Elapsed min", "Languages", "Transitions"],
        [
            [
                index,
                session["start"],
                session["end"],
                session["reps"],
                round(float(session["active_seconds_capped"]) / 60, 3),
                round(float(session["elapsed_seconds_estimate"]) / 60, 3),
                ", ".join(session["languages"]),
                session["language_transitions"],
            ]
            for index, session in enumerate(sessions["sessions"], start=1)
        ],
    )
    lines += ["", "### Daily session totals", ""]
    lines += render_table(
        ["Date", "Sessions", "Reps", "Active min", "Elapsed min"],
        [[row["date"], row["sessions"], row["reps"], row["active_minutes"], row["elapsed_minutes"]] for row in daily],
    )
    lines += ["", "## Mix history (last 60 calendar days)", ""]
    lines += ["### Cell totals and activity coverage", ""]
    lines += render_table(
        ["Language", "Population", "Cards", "Reps", "Active min", "Active days", "Share of reps", "Share of active time", "Status"],
        [
            [
                row["language"],
                row["population"],
                f"{row['card_count']:,}",
                f"{row['reps']:,}",
                row["active_minutes"],
                f"{row['active_days']}/{mix['window']['calendar_days']}",
                f"{row['share_of_reps_pct']}%",
                f"{row['share_of_active_time_pct']}%",
                row["coverage_status"],
            ]
            for row in mix["cell_totals"]
        ],
    )
    lines += ["", "### Language totals", ""]
    lines += render_table(
        ["Language", "Reps", "Active min", "Mean active min/day", "Active-time share"],
        [
            [row["language"], f"{row['reps']:,}", row["active_minutes"], row["mean_active_minutes_per_day"], f"{row['share_of_active_time_pct']}%"]
            for row in mix["language_totals"]
        ],
    )
    lines += ["", "### Systematic-starvation candidates", "", "The label is a deterministic coverage flag, not a causal diagnosis: a populated cell with activity on at most 20% of the 60 calendar days.", ""]
    candidates = mix["systematically_starved_candidates"]
    lines += render_table(
        ["Language", "Population", "Cards", "Reps", "Active days", "Status"],
        [[row["language"], row["population"], row["card_count"], row["reps"], row["active_days"], row["coverage_status"]] for row in candidates] or [["—", "—", "—", "—", "—", "none"]],
    )
    lines += ["", "### Daily mix: reps and active minutes by cell", "", "Each cell entry is `language/population: reps, active minutes`; empty means no measured reps that day.", ""]
    lines += render_table(
        ["Date", "Total reps", "Total active min", "Cells"],
        [[row["date"], row["total_reps"], row["total_active_minutes"], "; ".join(row["cells_compact"]) or "—"] for row in mix["daily"]],
    )
    lines += ["", "## Rating profile", "", "Percentages are within each displayed grouping.", "", "### By language and population", ""]
    lines += render_table(
        ["Language", "Population", "Reps", "Again", "Hard", "Good", "Easy"],
        [
            [cell["language"], cell["population"], cell["rep_count"], *[f"{cell['percentages'][label]}% ({cell['counts'][label]:,})" for label in ("again", "hard", "good", "easy")]]
            for cell in rating["by_cell"]
        ],
    )
    lines += ["", "### By maturity band", ""]
    lines += render_table(
        ["Maturity", "Reps", "Again", "Hard", "Good", "Easy"],
        [[row["maturity_band"], row["rep_count"], *[f"{row['percentages'][label]}% ({row['counts'][label]:,})" for label in ("again", "hard", "good", "easy")]] for row in rating["by_maturity"]],
    )
    lines += ["", "### By language, population, and maturity", ""]
    lines += render_table(
        ["Language", "Population", "Maturity", "Reps", "Again", "Hard", "Good", "Easy"],
        [
            [row["language"], row["population"], row["maturity_band"], row["rep_count"], *[f"{row['percentages'][label]}% ({row['counts'][label]:,})" for label in ("again", "hard", "good", "easy")]]
            for row in rating["by_cell_maturity"]
        ],
    )
    lines += ["", "## Summary", "", report["summary"], ""]
    return "\n".join(lines)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"missing source collection: {SOURCE}")

    connection = sqlite3.connect(f"file:{SOURCE.resolve()}?mode=ro&immutable=1", uri=True)
    register_unicase(connection)
    try:
        current_cards = connection.execute("""
            SELECT c.id AS card_id, d.name AS deck_name, n.tags AS tags
            FROM cards c
            LEFT JOIN decks d ON d.id = c.did
            LEFT JOIN notes n ON n.id = c.nid
        """).fetchall()
        current_notes = connection.execute("SELECT count(*) FROM notes").fetchone()[0]
        current_decks = connection.execute("SELECT count(*) FROM decks").fetchone()[0]
        revlog_total = connection.execute("SELECT count(*) FROM revlog").fetchone()[0]
        revlog_rows = connection.execute("""
            SELECT r.id AS ts_ms, r.cid AS card_id, r.ease, r.ivl, r.time, r.type
            FROM revlog r
            ORDER BY r.id
        """).fetchall()
    finally:
        connection.close()

    card_meta: dict[int, dict[str, object]] = {}
    card_count_by_cell: Counter[tuple[str, str]] = Counter()
    cards_by_reason: Counter[str] = Counter()
    for card_id, deck_name, tags in current_cards:
        language, population, reason = classify_deck(deck_name, tags)
        cell = (language, population)
        card_meta[int(card_id)] = {
            "language": language,
            "population": population,
            "reason": reason,
            "deck_name": deck_name or "",
        }
        card_count_by_cell[cell] += 1
        cards_by_reason[reason] += 1

    orphaned_revlog_rows = 0
    events: list[dict[str, object]] = []
    reps_by_reason: Counter[str] = Counter()
    seconds_by_cell: dict[tuple[str, str], list[int]] = defaultdict(list)
    raw_seconds_by_cell: dict[tuple[str, str], list[int]] = defaultdict(list)
    cards_with_reps_by_cell: dict[tuple[str, str], set[int]] = defaultdict(set)
    rating_by_cell: dict[tuple[str, str], Counter[int]] = defaultdict(Counter)
    rating_by_maturity: dict[str, Counter[int]] = defaultdict(Counter)
    rating_by_cell_maturity: dict[tuple[str, str, str], Counter[int]] = defaultdict(Counter)

    for ts_ms, card_id, ease, interval, time_ms, revlog_type in revlog_rows:
        card_id = int(card_id)
        if card_id not in card_meta:
            orphaned_revlog_rows += 1
            continue
        metadata = card_meta[card_id]
        cell = (str(metadata["language"]), str(metadata["population"]))
        raw_time_ms = int(time_ms)
        capped_time_ms = min(raw_time_ms, TIME_CAP_MS)
        maturity = maturity_band(int(revlog_type), int(interval))
        event = {
            "ts_ms": int(ts_ms),
            "local_ts": iso_local(int(ts_ms)),
            "local_date": local_date(int(ts_ms)),
            "card_id": card_id,
            "language": cell[0],
            "population": cell[1],
            "mapping_reason": metadata["reason"],
            "ease": int(ease),
            "ivl": int(interval),
            "revlog_type": int(revlog_type),
            "maturity_band": maturity,
            "raw_time_ms": raw_time_ms,
            "capped_time_ms": capped_time_ms,
        }
        events.append(event)
        seconds_by_cell[cell].append(capped_time_ms)
        raw_seconds_by_cell[cell].append(raw_time_ms)
        cards_with_reps_by_cell[cell].add(card_id)
        reps_by_reason[str(metadata["reason"])] += 1
        rating_by_cell[cell][int(ease)] += 1
        rating_by_maturity[maturity][int(ease)] += 1
        rating_by_cell_maturity[(cell[0], cell[1], maturity)][int(ease)] += 1

    events.sort(key=lambda event: int(event["ts_ms"]))
    if not events:
        raise SystemExit("no joinable revlogs found")

    end_date = local_date(int(events[-1]["ts_ms"]))
    mix_start = end_date - timedelta(days=MIX_DAYS - 1)
    session_start = end_date - timedelta(days=SESSION_DAYS - 1)

    global_values: list[int] = []
    global_values_by_population: dict[str, list[int]] = defaultdict(list)
    for cell, values in seconds_by_cell.items():
        global_values.extend(values)
        global_values_by_population[cell[1]].extend(values)

    def planning_constant(cell: tuple[str, str], values: list[int]) -> tuple[int, str]:
        if len(values) >= THIN_CELL_REPS:
            return int(round(quantile(values, 0.5) or 0)), "cell_median"
        population_values = global_values_by_population[cell[1]]
        if len(population_values) >= THIN_CELL_REPS:
            return int(round(quantile(population_values, 0.5) or 0)), "global_population_median"
        return int(round(quantile(global_values, 0.5) or 0)), "global_median"

    all_cells = set(card_count_by_cell) | set(seconds_by_cell)
    seconds_cells = []
    for cell in ordered_cells(all_cells):
        language, population = cell
        capped_values = seconds_by_cell.get(cell, [])
        raw_values = raw_seconds_by_cell.get(cell, [])
        capped_stat = stats([float(value) for value in capped_values])
        raw_stat = stats([float(value) for value in raw_values])
        recommended_ms, planning_source = planning_constant(cell, capped_values)
        at_or_above_cap = sum(value >= TIME_CAP_MS for value in raw_values)
        seconds_cells.append({
            "language": language,
            "population": population,
            "card_count": card_count_by_cell[cell],
            "cards_with_reps": len(cards_with_reps_by_cell.get(cell, set())),
            "rep_count": len(capped_values),
            "capped_time_ms": capped_stat,
            "raw_time_ms": raw_stat,
            "at_or_above_60s_count": at_or_above_cap,
            "at_or_above_60s_pct": pct(at_or_above_cap, len(raw_values)),
            "recommended_planning_ms": recommended_ms,
            "recommended_planning_seconds": round_seconds(recommended_ms),
            "planning_source": planning_source,
        })

    global_median_ms = int(round(quantile(global_values, 0.5) or 0))
    global_fallbacks = []
    for population in POPULATION_ORDER:
        values = global_values_by_population.get(population, [])
        if not values:
            continue
        if len(values) >= THIN_CELL_REPS:
            fallback_ms = int(round(quantile(values, 0.5) or 0))
            fallback_source = "global_population_median"
        else:
            fallback_ms = global_median_ms
            fallback_source = "global_median"
        global_fallbacks.append({
            "population": population,
            "rep_count": len(values),
            "capped_time_ms": stats([float(value) for value in values]),
            "planning_constant_ms": fallback_ms,
            "planning_constant_seconds": round_seconds(fallback_ms),
            "planning_source": fallback_source,
        })
    global_fallbacks.append({
        "population": "all",
        "rep_count": len(global_values),
        "capped_time_ms": stats([float(value) for value in global_values]),
        "planning_constant_ms": global_median_ms,
        "planning_constant_seconds": round_seconds(global_median_ms),
        "planning_source": "global_median",
    })

    session_events = [event for event in events if session_start <= event["local_date"] <= end_date]
    sessions = cluster_sessions(session_events)
    all_dates = [session_start + timedelta(days=index) for index in range(SESSION_DAYS)]
    daily_session_accumulator: dict[date, dict[str, int]] = {
        day: {"sessions": 0, "reps": 0, "active_ms": 0, "elapsed_ms": 0} for day in all_dates
    }
    for session in sessions:
        day = date.fromisoformat(str(session["date"]))
        accumulator = daily_session_accumulator[day]
        accumulator["sessions"] += 1
        accumulator["reps"] += int(session["reps"])
        accumulator["active_ms"] += int(round(float(session["active_seconds_capped"]) * 1000))
        accumulator["elapsed_ms"] += int(round(float(session["elapsed_seconds_estimate"]) * 1000))

    daily_session_rows = [
        {
            "date": str(day),
            "sessions": accumulator["sessions"],
            "reps": accumulator["reps"],
            "active_minutes": round(accumulator["active_ms"] / 60_000, 3),
            "elapsed_minutes": round(accumulator["elapsed_ms"] / 60_000, 3),
        }
        for day, accumulator in daily_session_accumulator.items()
    ]
    active_minutes_by_day = [row["active_minutes"] for row in daily_session_rows]
    elapsed_minutes_by_day = [row["elapsed_minutes"] for row in daily_session_rows]
    sessions_by_day = [row["sessions"] for row in daily_session_rows]
    study_day_rows = [row for row in daily_session_rows if row["reps"] > 0]
    active_session_seconds = [float(session["active_seconds_capped"]) for session in sessions]
    elapsed_session_seconds = [float(session["elapsed_seconds_estimate"]) for session in sessions]
    language_count_distribution = Counter(int(session["language_count"]) for session in sessions)
    transition_counts: Counter[str] = Counter()
    for session in sessions:
        sequence = [str(language) for language in session["language_reps"]]
        # The dictionary is sorted for reporting, so transition pairs are
        # computed directly from the event list below instead of this summary.
        _ = sequence
    for left, right in zip(session_events, session_events[1:]):
        if int(left["ts_ms"]) == int(right["ts_ms"]):
            continue
        # Only count transitions within the same gap-defined session.
        if int(right["ts_ms"]) - int(left["ts_ms"]) <= SESSION_GAP_MS and left["language"] != right["language"]:
            transition_counts[f"{left['language']} → {right['language']}"] += 1

    time_of_day_accumulator = {
        hour: {
            "hour": f"{hour:02d}:00",
            "session_starts": 0,
            "start_active_ms": 0,
            "reps": 0,
            "rep_active_ms": 0,
        }
        for hour in range(24)
    }
    for session in sessions:
        start_hour = datetime.fromisoformat(str(session["start"])).hour
        row = time_of_day_accumulator[start_hour]
        row["session_starts"] += 1
        row["start_active_ms"] += int(round(float(session["active_seconds_capped"]) * 1000))
    for event in session_events:
        hour = datetime.fromisoformat(str(event["local_ts"])).hour
        row = time_of_day_accumulator[hour]
        row["reps"] += 1
        row["rep_active_ms"] += int(event["capped_time_ms"])
    time_of_day = [
        {
            "hour": row["hour"],
            "session_starts": row["session_starts"],
            "start_active_minutes": round(row["start_active_ms"] / 60_000, 3),
            "reps": row["reps"],
            "rep_active_minutes": round(row["rep_active_ms"] / 60_000, 3),
        }
        for row in time_of_day_accumulator.values()
    ]
    session_histogram = {
        "0-15_min": 0,
        "15-30_min": 0,
        "30-60_min": 0,
        "60-120_min": 0,
        "120+_min": 0,
    }
    for seconds in active_session_seconds:
        minutes = seconds / 60
        if minutes < 15:
            key = "0-15_min"
        elif minutes < 30:
            key = "15-30_min"
        elif minutes < 60:
            key = "30-60_min"
        elif minutes < 120:
            key = "60-120_min"
        else:
            key = "120+_min"
        session_histogram[key] += 1

    daily_summary = {
        "calendar_days": SESSION_DAYS,
        "study_days": len(study_day_rows),
        "sessions_per_calendar_day": stats([float(value) for value in sessions_by_day]),
        "sessions_per_study_day": round(mean([row["sessions"] for row in study_day_rows]) if study_day_rows else 0, 4),
        "active_minutes_per_calendar_day": stats([float(value) for value in active_minutes_by_day]),
        "active_minutes_per_study_day": stats([float(row["active_minutes"]) for row in study_day_rows]),
        "elapsed_minutes_per_calendar_day": stats([float(value) for value in elapsed_minutes_by_day]),
        "elapsed_minutes_per_study_day": stats([float(row["elapsed_minutes"]) for row in study_day_rows]),
    }
    mixed_sessions = sum(int(session["language_count"]) > 1 for session in sessions)
    interleaved_sessions = sum(bool(session["interleaved"]) for session in sessions)
    language_interleaving = {
        "single_language_sessions": len(sessions) - mixed_sessions,
        "single_language_pct": pct(len(sessions) - mixed_sessions, len(sessions)),
        "mixed_language_sessions": mixed_sessions,
        "mixed_language_pct": pct(mixed_sessions, len(sessions)),
        "interleaved_sessions": interleaved_sessions,
        "interleaved_pct": pct(interleaved_sessions, len(sessions)),
        "language_transitions": dict(sorted(transition_counts.items())),
    }
    session_anatomy = {
        "window": {
            "start": str(session_start),
            "end": str(end_date),
            "calendar_days": SESSION_DAYS,
            "joinable_reps": len(session_events),
        },
        "session_count": len(sessions),
        "daily_summary": daily_summary,
        "session_length_seconds": {
            "active": stats(active_session_seconds),
            "elapsed": stats(elapsed_session_seconds),
        },
        "session_length_histogram_active": session_histogram,
        "languages_per_session": {str(key): value for key, value in sorted(language_count_distribution.items())},
        "language_interleaving": language_interleaving,
        "time_of_day": time_of_day,
        "daily": daily_session_rows,
        "sessions": sessions,
    }

    mix_events = [event for event in events if mix_start <= event["local_date"] <= end_date]
    mix_dates = [mix_start + timedelta(days=index) for index in range(MIX_DAYS)]
    mix_daily_accumulator: dict[date, dict[tuple[str, str], dict[str, int]]] = {
        day: defaultdict(lambda: {"reps": 0, "active_ms": 0}) for day in mix_dates
    }
    for event in mix_events:
        cell = (str(event["language"]), str(event["population"]))
        accumulator = mix_daily_accumulator[event["local_date"]][cell]
        accumulator["reps"] += 1
        accumulator["active_ms"] += int(event["capped_time_ms"])

    mix_cell_accumulator: dict[tuple[str, str], dict[str, object]] = {
        cell: {"reps": 0, "active_ms": 0, "active_days": set()} for cell in all_cells
    }
    for day, cell_map in mix_daily_accumulator.items():
        for cell, accumulator in cell_map.items():
            total = mix_cell_accumulator.setdefault(cell, {"reps": 0, "active_ms": 0, "active_days": set()})
            total["reps"] += accumulator["reps"]
            total["active_ms"] += accumulator["active_ms"]
            total["active_days"].add(day)
    total_mix_reps = sum(int(value["reps"]) for value in mix_cell_accumulator.values())
    total_mix_active_ms = sum(int(value["active_ms"]) for value in mix_cell_accumulator.values())
    mix_cell_totals = []
    for cell in ordered_cells(set(mix_cell_accumulator)):
        value = mix_cell_accumulator[cell]
        reps = int(value["reps"])
        active_days = len(value["active_days"])
        if reps == 0:
            coverage_status = "never_observed"
        elif active_days <= MIX_DAYS * 0.20:
            coverage_status = "rarely_observed"
        else:
            coverage_status = "observed"
        mix_cell_totals.append({
            "language": cell[0],
            "population": cell[1],
            "card_count": card_count_by_cell[cell],
            "reps": reps,
            "active_minutes": round(int(value["active_ms"]) / 60_000, 3),
            "active_days": active_days,
            "zero_days": MIX_DAYS - active_days,
            "share_of_reps_pct": pct(reps, total_mix_reps),
            "share_of_active_time_pct": pct(int(value["active_ms"]), total_mix_active_ms),
            "coverage_status": coverage_status,
        })
    mix_language_accumulator: dict[str, dict[str, object]] = defaultdict(
        lambda: {"reps": 0, "active_ms": 0, "active_days": set()}
    )
    for (language, _population), value in mix_cell_accumulator.items():
        total = mix_language_accumulator[language]
        total["reps"] += int(value["reps"])
        total["active_ms"] += int(value["active_ms"])
        total["active_days"].update(value["active_days"])
    mix_language_totals = []
    for language in sorted(
        mix_language_accumulator,
        key=lambda value: LANGUAGE_ORDER.index(value) if value in LANGUAGE_ORDER else len(LANGUAGE_ORDER),
    ):
        value = mix_language_accumulator[language]
        mix_language_totals.append({
            "language": language,
            "reps": int(value["reps"]),
            "active_minutes": round(int(value["active_ms"]) / 60_000, 3),
            "mean_active_minutes_per_day": round(int(value["active_ms"]) / 60_000 / MIX_DAYS, 3),
            "active_days": len(value["active_days"]),
            "share_of_active_time_pct": pct(int(value["active_ms"]), total_mix_active_ms),
        })
    mix_daily_rows = []
    for day in mix_dates:
        cell_map = mix_daily_accumulator[day]
        cells = []
        compact = []
        for cell in ordered_cells(set(cell_map)):
            accumulator = cell_map[cell]
            reps = accumulator["reps"]
            active_minutes = round(accumulator["active_ms"] / 60_000, 3)
            cells.append({
                "language": cell[0],
                "population": cell[1],
                "reps": reps,
                "active_minutes": active_minutes,
            })
            compact.append(f"{cell[0]}/{cell[1]}: {reps}, {active_minutes} min")
        total_reps = sum(row["reps"] for row in cells)
        total_active_minutes = round(sum(row["active_minutes"] for row in cells), 3)
        mix_daily_rows.append({
            "date": str(day),
            "total_reps": total_reps,
            "total_active_minutes": total_active_minutes,
            "cells": cells,
            "cells_compact": compact,
        })
    systematic_candidates = [
        row for row in mix_cell_totals
        if row["card_count"] > 0 and row["active_days"] <= MIX_DAYS * 0.20
    ]
    mix_history = {
        "window": {"start": str(mix_start), "end": str(end_date), "calendar_days": MIX_DAYS, "joinable_reps": len(mix_events)},
        "daily": mix_daily_rows,
        "cell_totals": mix_cell_totals,
        "language_totals": mix_language_totals,
        "systematic_starvation_rule": "card_count > 0 and activity on at most 20% of the 60 calendar days",
        "systematically_starved_candidates": systematic_candidates,
    }

    rating_cells = []
    for cell in ordered_cells(set(rating_by_cell)):
        data = ratings(rating_by_cell[cell])
        rating_cells.append({"language": cell[0], "population": cell[1], **data})
    rating_maturity = []
    for maturity in MATURITY_ORDER:
        if maturity not in rating_by_maturity:
            continue
        data = ratings(rating_by_maturity[maturity])
        rating_maturity.append({"maturity_band": maturity, **data})
    rating_cell_maturity = []
    for language, population, maturity in sorted(
        rating_by_cell_maturity,
        key=lambda key: (
            LANGUAGE_ORDER.index(key[0]) if key[0] in LANGUAGE_ORDER else len(LANGUAGE_ORDER),
            POPULATION_ORDER.index(key[1]) if key[1] in POPULATION_ORDER else len(POPULATION_ORDER),
            MATURITY_ORDER.index(key[2]) if key[2] in MATURITY_ORDER else len(MATURITY_ORDER),
        ),
    ):
        data = ratings(rating_by_cell_maturity[(language, population, maturity)])
        rating_cell_maturity.append({"language": language, "population": population, "maturity_band": maturity, **data})
    rating_profile = {
        "by_cell": rating_cells,
        "by_maturity": rating_maturity,
        "by_cell_maturity": rating_cell_maturity,
    }

    cap_at_or_above_count = sum(value >= TIME_CAP_MS for values in raw_seconds_by_cell.values() for value in values)
    cap_over_count = sum(value > TIME_CAP_MS for values in raw_seconds_by_cell.values() for value in values)
    mapping_audit = {
        "cards_by_reason": dict(sorted(cards_by_reason.items())),
        "reps_by_reason": dict(sorted(reps_by_reason.items())),
        "orphaned_revlog_rows": orphaned_revlog_rows,
        "mapped_cells": [
            {"language": cell[0], "population": cell[1], "cards": card_count_by_cell[cell], "reps": len(seconds_by_cell.get(cell, []))}
            for cell in ordered_cells(all_cells)
        ],
    }

    active_mean_minutes = float(daily_summary["active_minutes_per_calendar_day"]["mean"])
    active_median_minutes = float(daily_summary["active_minutes_per_calendar_day"]["median"])
    days_120_to_180 = sum(120 <= float(row["active_minutes"]) <= 180 for row in daily_session_rows)
    language_daily_summary = ", ".join(
        f"{row['language']} {row['mean_active_minutes_per_day']:.1f} min"
        for row in mix_language_totals
    )
    summary = (
        f"Across the last {SESSION_DAYS} calendar days ({session_start}–{end_date}), the account recorded "
        f"{len(sessions):,} gap-defined sessions on {len(study_day_rows)} study days. Capped active time averaged "
        f"{active_mean_minutes:.1f} minutes/day (median {active_median_minutes:.1f}), with "
        f"{days_120_to_180} days in the owner's 120–180 minute 2–3 hour band; elapsed session time and capped active time "
        f"are reported separately because Anki caps each rep at 60 seconds. The 60-day mix is the measured per-day "
        f"language/population baseline, including {len(systematic_candidates)} populated cells flagged as rarely observed or never observed "
        f"under the stated coverage rule. In that 60-day mix, mean active minutes/day were {language_daily_summary}; "
        f"that is materially less than the owner's 20–30 minutes per named language and stable 2–3 hour daily gym-block model "
        f"on days where the active-time distribution falls outside that band, and the session/language-interleaving tables "
        f"show the actual anatomy rather than assuming one block per language."
    )

    report = {
        "report": {
            "id": "DJ-C1",
            "title": "study-telemetry census",
            "deterministic": True,
            "read_only_source": True,
        },
        "source": {
            "path": str(SOURCE.relative_to(ROOT)),
            "current_cards": len(current_cards),
            "current_notes": current_notes,
            "current_decks": current_decks,
            "revlog_rows_total": revlog_total,
            "revlog_rows_joined": len(events),
            "orphaned_revlog_rows": orphaned_revlog_rows,
            "min_revlog_local": iso_local(int(events[0]["ts_ms"])),
            "max_revlog_local": iso_local(int(events[-1]["ts_ms"])),
        },
        "methods": {
            "timezone": LOCAL_TZ_NAME,
            "deck_separator": "\\x1f or ::",
            "session_gap_minutes": SESSION_GAP_MS / 60_000,
            "session_gap_rule": "new session only when the gap is greater than the threshold",
            "time_cap_ms": TIME_CAP_MS,
            "thin_cell_rep_threshold": THIN_CELL_REPS,
            "planning_constant_rule": "cell capped median for cells with at least 30 reps; otherwise global population capped median; otherwise global capped median",
            "podcast_tag_rules": list(PODCAST_TAG_RULES),
            "maturity_rule": "revlog type 0=learning, 2=relearning, 3=filtered; review ivl <=21 young, >21 mature",
            "historical_context_only": [
                "docs/research/tenses-profiles/",
                "docs/research/legacy_estate/DECKS.md",
                "docs/research/legacy_estate_work/",
            ],
        },
        "mapping_audit": mapping_audit,
        "seconds_per_rep": {
            "cap_effect": {
                "time_cap_ms": TIME_CAP_MS,
                "rep_count": len(events),
                "at_or_above_60s_count": cap_at_or_above_count,
                "at_or_above_60s_pct": pct(cap_at_or_above_count, len(events)),
                "raw_gt_60s_count": cap_over_count,
            },
            "cells": seconds_cells,
            "global_fallbacks": global_fallbacks,
        },
        "session_anatomy": session_anatomy,
        "mix_history": mix_history,
        "rating_profile": rating_profile,
        "summary": summary,
    }

    JSON_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MD_OUT.write_text(build_markdown(report), encoding="utf-8")
    print(f"wrote {JSON_OUT}")
    print(f"wrote {MD_OUT}")
    print(summary)


if __name__ == "__main__":
    main()
