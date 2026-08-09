"""Personal Study DJ — slices 1-2: OBSERVER + PLANNER.

Commission: docs/commissions/PERSONAL_DJ_COMMISSION.md. The DJ watches
what the owner actually studies (synced revlogs) and computes a daily
SESSION PLAN per language: due reviews first, then a weighted new-card
mix, all time-costed from observed seconds-per-rep. Slice 3 (a separate
add-on package) materializes the plan as filtered decks under `0 Today`.

Pipeline (daily, worker-scheduled via maybe_run_dj, or forced via
POST /admin/dj-run):

  1. PULL     — headless download-only AnkiWeb sync. REUSED from
                rescue_autopilot._pull_collection_blocking (the proven
                recipe; never reimplemented). Scratch collection in a
                temp dir, deleted after; never uploads.
  2. OBSERVE  — compute_observations(): per active language, classify
                every card into a POPULATION by its deck lane under the
                estate roots (anki_tree.ANKI_ROOTS), count due backlog
                and new-card reservoir, take the median seconds/rep per
                population from the revlog (priors where thin), and the
                last 7 days' actual study distribution. Cached to
                kv_store['dj_observations_last'] — the dashboard reads
                the cache, never triggers a pull.
  3. PLAN     — build_plan(): pure arithmetic from observations +
                per-language minute budgets (kv_store['dj_budgets'],
                defaults in DEFAULT_BUDGETS_MIN, owner-editable via
                POST /admin/dj-budgets). Persisted to the dj_plans
                table (one row per day, regeneration overwrites).
  4. REPORT   — kv_store['dj_last_report'], shown on the /dj page.

CARD POPULATIONS
    Deck lane under `<XX Language>::` decides the population:
      1 Expressions → expressions      5 Translation → translation
      2 Grammar     → grammar          6 My Errors   → my_errors
      3 Tenses      → tenses           7 Rescue      → rescue
      4 Exercises   → exercises        8 Pimsleur    → pimsleur
    plus the tag override: notes tagged `idiomatic-podcast` (the podcast
    lesson cards, which live inside the grammar lane) → podcast_lesson.
    Cards sitting in a filtered deck classify by their original deck
    (cards.odid). Decks outside the six roots (Default, zz Dormant,
    0 Today leftovers) are excluded and reported as `unclassified`.

SESSION PLAN SCHEMA (PLAN_SCHEMA_VERSION = 1) — the contract slice 3
consumes. All minutes are floats rounded to 0.1; all searches are Anki
browser-syntax strings the add-on runs verbatim.

    {
      "schema": 1,
      "for_day": "YYYY-MM-DD",            # UTC date the plan is for
      "generated_at": "…ISO8601…",
      "observations_at": "…ISO8601…",     # snapshot the plan was built from
      "budgets_min": {"de": 25, …},       # the budgets used
      "languages": [                       # only langs with budget > 0
        {
          "lang": "it",
          "anki_root": "IT Italian",       # from anki_tree.anki_root
          "deck_name": "0 Today::IT Italian",  # where slice 3 materializes
          "budget_min": 25,
          "due": {                         # REVIEWS FIRST — never dropped
            "cards": 132,
            "est_minutes": 18.4,
            "overflow": false,             # true ⇒ dues alone exceed budget
            "overflow_minutes": 0,         # est_minutes - budget when overflow
            "by_population": {"expressions": {"cards": 90, "est_minutes": 11.2}, …},
            "search": "deck:\"IT Italian\" is:due -is:suspended",
            "limit": 132,                  # = cards; the search is authoritative
            "order": "due"                 # sort field for find_cards
          },
          "new": {
            "minutes_available": 6.6,      # max(0, budget - due.est_minutes)
            "mix": [                       # one line per planned population
              {
                "population": "grammar",
                "weight": 0.32,            # renormalized over non-empty pops
                "cards": 4,
                "est_minutes": 3.1,
                "secs_per_new_card": 30.0, # secs_per_rep × NEW_CARD_TIME_FACTOR
                "reservoir": 210,
                "search": "deck:\"IT Italian::2 Grammar\" is:new -tag:idiomatic-podcast",
                "order": "due_position",   # keep authored due positions —
                                           # they encode curriculum interleave
                "reasoning": "…human-readable arithmetic…"
              }, …
            ]
          },
          "notes": ["…per-language caveats: overflow, priors, empty lanes…"]
        }, …
      ],
      "totals": {"est_minutes": …, "due_cards": …, "new_cards": …,
                 "langs_overflowing": […]}
    }

    Slice 3 materialization contract (mechanical, no decisions):
    per language, resolve due.search (find_cards, order by due, truncate
    to due.limit), then each mix line's search (order by due position,
    truncate to line.cards); build ONE filtered deck named deck_name
    with the union via a `cid:` search, dues first. Counts are estimates
    from the nightly snapshot — the searches re-run client-side at
    materialization time and are authoritative. Serve the plan to the
    add-on from GET /dj/plan (agent token).

NOT in this slice: the weakness engine (weakness_weights() below is the
documented identity hook), the commissioning loop, any add-on code.

Hard rules honored: the pulled snapshot is opened read-only; nothing
here touches the live collection or uploads to AnkiWeb.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import statistics
import tempfile
import time
from datetime import date, datetime, timezone
from typing import Any

import structlog

from . import db
from .anki_tree import ANKI_ROOTS, anki_root
from .settings import get_settings

log = structlog.get_logger()

PLAN_SCHEMA_VERSION = 1

KV_OBSERVATIONS = "dj_observations_last"
KV_BUDGETS = "dj_budgets"
KV_LAST_REPORT = "dj_last_report"
KV_LAST_RUN_TS = "dj_last_run_ts"

# Per-language daily study budgets (minutes). Owner-editable via
# POST /admin/dj-budgets; ~25 min/language matches the owner's stated
# 2-3 h/day across six languages, Mandarin slightly shorter.
DEFAULT_BUDGETS_MIN: dict[str, int] = {
    "de": 25, "es": 25, "fr": 25, "it": 25, "pt": 25, "zh": 20,
}

POPULATIONS = (
    "expressions", "grammar", "tenses", "exercises", "translation",
    "my_errors", "rescue", "pimsleur", "podcast_lesson", "other",
)

# Estate lane number → population (see CLAUDE.md "ANKI ESTATE TREE").
_LANE_POPULATION = {
    "1": "expressions", "2": "grammar", "3": "tenses", "4": "exercises",
    "5": "translation", "6": "my_errors", "7": "rescue", "8": "pimsleur",
}

def _due_search(root: str, exclude_populations: frozenset[str] = frozenset()) -> str:
    """Due search spec for a language root, minus owner-excluded lanes."""
    terms = [f'deck:"{root}"', "is:due", "-is:suspended"]
    for pop in sorted(exclude_populations):
        lane = _POP_DECK.get(pop)
        if lane:
            terms.append(f'-deck:"{root}::{lane}"')
    return " ".join(terms)


# Population → lane deck component, for composing search specs.
_POP_DECK = {
    "expressions": "1 Expressions", "grammar": "2 Grammar",
    "tenses": "3 Tenses", "exercises": "4 Exercises",
    "translation": "5 Translation", "my_errors": "6 My Errors",
    "rescue": "7 Rescue", "pimsleur": "8 Pimsleur",
}

PODCAST_TAG = "idiomatic-podcast"

# Seconds-per-rep priors, used until a population has MIN_OBS_FOR_MEDIAN
# observed reps in the 90-day revlog window. Chosen from the estate's
# card shapes: recognition cards are fast (expressions/tenses), typed or
# production exercises slower, translation slower still, podcast lesson
# slides are 1-2 minute audio listens.
SECS_PER_REP_PRIORS: dict[str, float] = {
    "expressions": 8.0, "grammar": 12.0, "tenses": 7.0, "exercises": 20.0,
    "translation": 25.0, "my_errors": 10.0, "rescue": 10.0,
    "pimsleur": 30.0, "podcast_lesson": 90.0, "other": 10.0,
}
MIN_OBS_FOR_MEDIAN = 20
REVLOG_WINDOW_DAYS = 90       # secs/rep observation window
MAX_REP_MS = 60_000           # Anki's own per-rep cap; defend anyway

# A new card costs more than one review rep the day it's introduced:
# first exposure plus the same-day learning steps (~2-3 reps). Factor
# applied to the population's secs/rep when budgeting new cards.
NEW_CARD_TIME_FACTOR = 2.5

# v1 new-card mix: simple curriculum-forward defaults. Grammar leads
# (the active initiative), expressions are the core fluency lane,
# exercises/tenses/translation follow, small trickles for the personal
# lanes. pimsleur (external audio course) and unclassified get nothing.
# Weights renormalize over populations that actually have new cards.
NEW_MIX_WEIGHTS_V1: dict[str, float] = {
    "grammar": 0.30, "expressions": 0.25, "exercises": 0.15,
    "tenses": 0.10, "translation": 0.08, "podcast_lesson": 0.05,
    "my_errors": 0.05, "rescue": 0.02,
}

_ROOT_TO_LANG = {root: lang for lang, root in ANKI_ROOTS.items()}


# ---------------------------------------------------------------------------
# OBSERVER — pure sqlite over the pulled snapshot (unit-testable)
# ---------------------------------------------------------------------------

def _deck_components(name: str) -> list[str]:
    """Deck name → components. Modern collections separate with \\x1f,
    legacy/apkg names with `::` — accept both."""
    sep = "\x1f" if "\x1f" in name else "::"
    return name.split(sep)


def classify_deck(name: str) -> tuple[str, str] | None:
    """Deck name → (lang, population), or None when the deck is outside
    the six estate roots (Default, zz Dormant, 0 Today, …)."""
    parts = _deck_components(name)
    lang = _ROOT_TO_LANG.get(parts[0])
    if lang is None:
        return None
    if len(parts) == 1:
        return lang, "other"
    lane_no = parts[1].split(" ", 1)[0]
    return lang, _LANE_POPULATION.get(lane_no, "other")


def _load_deck_classes(con: sqlite3.Connection) -> dict[int, tuple[str, str] | None]:
    """did → classification. Modern schema keeps decks in a table;
    legacy schema 11 keeps them as JSON in col.decks."""
    try:
        rows = con.execute("SELECT id, name FROM decks").fetchall()
    except sqlite3.OperationalError:
        raw = con.execute("SELECT decks FROM col LIMIT 1").fetchone()
        decks = json.loads(raw[0]) if raw and raw[0] else {}
        rows = [(int(did), d["name"]) for did, d in decks.items()]
    return {did: classify_deck(name) for did, name in rows}


def _has_podcast_tag(tags: str) -> bool:
    return PODCAST_TAG in tags.split()


def compute_observations(colpath: str, now_ms: int | None = None) -> dict:
    """Read the pulled collection (read-only) into the observation dict
    the planner consumes. Approximations, documented:

    - "due today" uses collection-day arithmetic from col.crt without
      the rollover-hour offset (drift ≤ a few hours at day edges);
    - cards inside filtered decks classify by their original deck
      (odid) and, for review cards, compare their original due (odue);
    - manual reschedules (revlog ease 0) never count as study.
    """
    now_ms = now_ms or int(time.time() * 1000)
    now_s = now_ms // 1000
    con = sqlite3.connect(f"file:{colpath}?mode=ro", uri=True)
    try:
        crt = con.execute("SELECT crt FROM col LIMIT 1").fetchone()[0]
        today_day = int((now_s - crt) // 86400)
        deck_class = _load_deck_classes(con)

        def zero() -> dict[str, Any]:
            return {"due": {}, "new_reservoir": {}, "_times": {}, "last7": {}}

        langs: dict[str, dict] = {}
        unclassified = 0

        for did, odid, queue, due, odue, tags in con.execute(
                "SELECT c.did, c.odid, c.queue, c.due, c.odue, n.tags "
                "FROM cards c JOIN notes n ON n.id = c.nid"):
            cls = deck_class.get(odid or did)
            if cls is None:
                unclassified += 1
                continue
            lang, pop = cls
            if _has_podcast_tag(tags):
                pop = "podcast_lesson"
            L = langs.setdefault(lang, zero())
            if queue == 0:                                   # new
                L["new_reservoir"][pop] = L["new_reservoir"].get(pop, 0) + 1
            elif queue == 1:                                 # intraday learn
                if due <= now_s:
                    L["due"][pop] = L["due"].get(pop, 0) + 1
            elif queue in (2, 3):                            # review / day learn
                eff_due = odue if (odid and odue) else due
                if eff_due <= today_day:
                    L["due"][pop] = L["due"].get(pop, 0) + 1
            # queues -1/-2/-3 (suspended/buried) and 4 (preview): excluded

        window_cutoff = now_ms - REVLOG_WINDOW_DAYS * 86400 * 1000
        seven_cutoff = now_ms - 7 * 86400 * 1000
        for rid, time_ms, ease, did, odid, tags in con.execute(
                "SELECT r.id, r.time, r.ease, c.did, c.odid, n.tags "
                "FROM revlog r JOIN cards c ON c.id = r.cid "
                "JOIN notes n ON n.id = c.nid WHERE r.id > ?",
                (window_cutoff,)):
            if ease <= 0:                                    # manual entries
                continue
            cls = deck_class.get(odid or did)
            if cls is None:
                continue
            lang, pop = cls
            if _has_podcast_tag(tags):
                pop = "podcast_lesson"
            L = langs.setdefault(lang, zero())
            t = min(int(time_ms or 0), MAX_REP_MS)
            if t > 0:
                L["_times"].setdefault(pop, []).append(t)
            if rid > seven_cutoff:
                d = L["last7"].setdefault(pop, {"reps": 0, "minutes": 0.0})
                d["reps"] += 1
                d["minutes"] += t / 60000
    finally:
        con.close()

    for L in langs.values():
        times_by_pop: dict[str, list[int]] = L.pop("_times", {})
        spr: dict[str, dict] = {}
        for pop in POPULATIONS:
            times = times_by_pop.get(pop, [])
            if len(times) >= MIN_OBS_FOR_MEDIAN:
                spr[pop] = {"secs": round(statistics.median(times) / 1000, 2),
                            "n_obs": len(times), "source": "observed"}
            else:
                spr[pop] = {"secs": SECS_PER_REP_PRIORS[pop],
                            "n_obs": len(times), "source": "prior"}
        L["secs_per_rep"] = spr
        for d in L["last7"].values():
            d["minutes"] = round(d["minutes"], 1)

    return {
        "schema": 1,
        "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "langs": langs,
        "unclassified_cards": unclassified,
    }


# ---------------------------------------------------------------------------
# PLANNER — pure arithmetic (unit-testable)
# ---------------------------------------------------------------------------

def weakness_weights(lang: str, base: dict[str, float],
                     observations: dict) -> dict[str, float]:
    """THE WEAKNESS HOOK. v1: identity. This is where weakness
    clustering (shared machinery with the Hub weakness policies and the
    Grammar Course telemetry) will reshape the new-card mix — e.g. boost
    `grammar` when a unit's exercise failures cluster, or `rescue` when
    the struggle list grows. Signature is the contract: takes the
    per-language base weights + the full observation dict, returns
    adjusted weights (need not sum to 1 — the planner renormalizes)."""
    return dict(base)


def _spr(obs_lang: dict, pop: str) -> float:
    entry = (obs_lang.get("secs_per_rep") or {}).get(pop)
    if entry:
        return float(entry["secs"])
    return SECS_PER_REP_PRIORS[pop]


def _new_search(root: str, pop: str) -> str:
    if pop == "podcast_lesson":
        return f'deck:"{root}" is:new tag:{PODCAST_TAG}'
    lane = _POP_DECK[pop]
    base = f'deck:"{root}::{lane}" is:new'
    if pop == "grammar":                 # podcast lessons live in this lane
        base += f" -tag:{PODCAST_TAG}"
    return base


def build_plan(observations: dict, budgets_min: dict[str, int], for_day: str,
               generated_at: str | None = None,
               exclude_populations: frozenset[str] = frozenset()) -> dict:
    """Observations + budgets → the session plan (schema in the module
    docstring). Pure and deterministic given its inputs.

    ``exclude_populations`` (owner curation, settings
    ``dj_exclude_populations``): populations the owner has ruled out of
    study entirely — their dues are REPORTED in a note but never
    planned, and their decks are subtracted from the due search spec.
    First entry (2026-08-09): pimsleur — batch-imported, beneath level,
    never opted in ("we don't need to study everything there —
    certainly not pimsleur")."""
    generated_at = generated_at or datetime.now(timezone.utc).isoformat(
        timespec="seconds")
    languages = []
    total_minutes = 0.0
    total_due = total_new = 0
    overflowing: list[str] = []

    for lang in sorted(budgets_min):
        budget = int(budgets_min[lang])
        if budget <= 0 or lang not in ANKI_ROOTS:
            continue
        root = anki_root(lang)
        obs = (observations.get("langs") or {}).get(lang) or {}
        notes: list[str] = []

        # --- due reviews first — never silently dropped -------------------
        due_by_pop = {}
        due_cards = 0
        due_minutes = 0.0
        excluded_due = 0
        for pop, n in sorted((obs.get("due") or {}).items()):
            if pop in exclude_populations:
                excluded_due += n
                continue
            est = n * _spr(obs, pop) / 60
            due_by_pop[pop] = {"cards": n, "est_minutes": round(est, 1)}
            due_cards += n
            due_minutes += est
        if excluded_due:
            excluded_names = ", ".join(sorted(
                p for p in exclude_populations
                if (obs.get("due") or {}).get(p)))
            notes.append(
                f"excluded by owner curation ({excluded_names}): "
                f"{excluded_due} due cards not planned")
        due_minutes = round(due_minutes, 1)
        overflow = due_minutes > budget
        overflow_minutes = round(due_minutes - budget, 1) if overflow else 0
        if overflow:
            overflowing.append(lang)
            notes.append(
                f"OVERFLOW: dues alone need ~{due_minutes} min against a "
                f"{budget}-min budget (+{overflow_minutes} min). All dues "
                "stay in the plan; no new cards today.")

        # --- remaining minutes → weighted new-card mix --------------------
        new_minutes = 0.0 if overflow else round(budget - due_minutes, 1)
        reservoir = obs.get("new_reservoir") or {}
        weights = weakness_weights(lang, NEW_MIX_WEIGHTS_V1, observations)
        eligible = {p: w for p, w in weights.items()
                    if w > 0 and reservoir.get(p, 0) > 0}
        mix = []
        if new_minutes > 0 and eligible:
            wsum = sum(eligible.values())
            for pop in sorted(eligible, key=lambda p: -eligible[p]):
                w = eligible[pop] / wsum
                minutes_pop = new_minutes * w
                per_card = _spr(obs, pop) * NEW_CARD_TIME_FACTOR
                n = min(int(minutes_pop * 60 // per_card), reservoir[pop])
                if n <= 0:
                    continue
                spr_src = (obs.get("secs_per_rep") or {}).get(pop, {})
                reasoning = (
                    f"{w:.0%} of {new_minutes} new-card min = "
                    f"{minutes_pop:.1f} min ÷ {per_card:.0f}s/new card "
                    f"({_spr(obs, pop):.0f}s/rep"
                    f"{' prior' if spr_src.get('source') == 'prior' else ''}"
                    f" × {NEW_CARD_TIME_FACTOR}) → {n} cards "
                    f"(reservoir {reservoir[pop]})")
                mix.append({
                    "population": pop,
                    "weight": round(w, 3),
                    "cards": n,
                    "est_minutes": round(n * per_card / 60, 1),
                    "secs_per_new_card": round(per_card, 1),
                    "reservoir": reservoir[pop],
                    "search": _new_search(root, pop),
                    "order": "due_position",
                    "reasoning": reasoning,
                })
                total_new += n
        elif new_minutes > 0:
            notes.append("no new-card reservoir in any weighted population")
        for pop, entry in sorted((obs.get("secs_per_rep") or {}).items()):
            if entry.get("source") == "prior" and (
                    pop in due_by_pop or any(m["population"] == pop
                                             for m in mix)):
                notes.append(
                    f"secs/rep for {pop} is a prior "
                    f"({entry.get('n_obs', 0)} obs < {MIN_OBS_FOR_MEDIAN})")
        if not obs:
            notes.append("no observation data for this language "
                         "(nothing under its root in the snapshot)")

        languages.append({
            "lang": lang,
            "anki_root": root,
            "deck_name": f"0 Today::{root}",
            "budget_min": budget,
            "due": {
                "cards": due_cards,
                "est_minutes": due_minutes,
                "overflow": overflow,
                "overflow_minutes": overflow_minutes,
                "by_population": due_by_pop,
                "search": _due_search(root, exclude_populations),
                "limit": due_cards,
                "order": "due",
            },
            "new": {"minutes_available": new_minutes, "mix": mix},
            "notes": notes,
        })
        total_due += due_cards
        total_minutes += min(due_minutes, budget) + sum(
            m["est_minutes"] for m in mix)

    return {
        "schema": PLAN_SCHEMA_VERSION,
        "for_day": for_day,
        "generated_at": generated_at,
        "observations_at": observations.get("computed_at"),
        "budgets_min": {k: int(v) for k, v in sorted(budgets_min.items())},
        "languages": languages,
        "totals": {
            "est_minutes": round(total_minutes, 1),
            "due_cards": total_due,
            "new_cards": total_new,
            "langs_overflowing": overflowing,
        },
    }


# ---------------------------------------------------------------------------
# Persistence — budgets (kv) + plans (dj_plans table)
# ---------------------------------------------------------------------------

def validate_budgets(budgets: Any) -> dict[str, int]:
    """Owner-input validation for /admin/dj-budgets. Full-dict semantics:
    unknown langs refused, minutes int 0..180 (0 = language paused)."""
    if not isinstance(budgets, dict) or not budgets:
        raise ValueError("budgets must be a non-empty object")
    out: dict[str, int] = {}
    for lang, minutes in budgets.items():
        if lang not in ANKI_ROOTS:
            raise ValueError(f"unknown language {lang!r}")
        if not isinstance(minutes, int) or isinstance(minutes, bool) or \
                not (0 <= minutes <= 180):
            raise ValueError(f"{lang}: minutes must be an int in 0..180")
        out[lang] = minutes
    return out


async def load_budgets() -> dict[str, int]:
    raw = await db.kv_get(KV_BUDGETS)
    stored = {}
    if raw:
        try:
            stored = validate_budgets(json.loads(raw))
        except (ValueError, TypeError):
            log.warning("dj.budgets_garbled_kv")
    return {**DEFAULT_BUDGETS_MIN, **stored}


async def save_budgets(budgets: dict[str, int]) -> dict[str, int]:
    merged = {**DEFAULT_BUDGETS_MIN, **validate_budgets(budgets)}
    await db.kv_set(KV_BUDGETS, json.dumps(merged))
    return merged


async def save_plan(plan: dict) -> None:
    pool = await db.get_pool()
    await pool.execute(
        """
        INSERT INTO dj_plans (day, schema_version, generated_at, plan)
        VALUES ($1, $2, NOW(), $3::jsonb)
        ON CONFLICT (day) DO UPDATE SET
            schema_version = EXCLUDED.schema_version,
            generated_at = NOW(),
            plan = EXCLUDED.plan
        """, date.fromisoformat(plan["for_day"]), plan["schema"],
        json.dumps(plan, ensure_ascii=False))


async def load_plan(day: str | None = None) -> dict | None:
    """One plan row: exact day when given, else the latest."""
    pool = await db.get_pool()
    if day:
        row = await pool.fetchrow(
            "SELECT day, schema_version, generated_at, plan FROM dj_plans "
            "WHERE day = $1", date.fromisoformat(day))
    else:
        row = await pool.fetchrow(
            "SELECT day, schema_version, generated_at, plan FROM dj_plans "
            "ORDER BY day DESC LIMIT 1")
    if row is None:
        return None
    plan = row["plan"]
    if isinstance(plan, str):        # asyncpg jsonb without codec
        plan = json.loads(plan)
    return {
        "day": row["day"].isoformat(),
        "schema_version": row["schema_version"],
        "generated_at": row["generated_at"].isoformat(),
        "plan": plan,
    }


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

async def run_dj(force: bool = False) -> dict:
    s = get_settings()
    report: dict[str, Any] = {
        "ran_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pull": None, "plan_day": None, "totals": None,
        "notes": [], "errors": [],
    }
    if not s.dj_enabled and not force:
        report["notes"].append("DJ disabled (dj_enabled)")
        return report
    await db.kv_set(KV_LAST_RUN_TS, str(int(time.time())))

    # -- 1. PULL + 2. OBSERVE (reuse the autopilot's proven pull) ----------
    observations: dict | None = None
    if not s.ankiweb_hkey:
        report["errors"].append(
            "ANKIWEB_HKEY not configured — no pull; using cached observations")
    else:
        from . import rescue_autopilot
        try:
            with tempfile.TemporaryDirectory(prefix="dj-") as wd:
                colpath = await asyncio.to_thread(
                    rescue_autopilot._pull_collection_blocking, wd)
                observations = await asyncio.to_thread(
                    compute_observations, colpath)
                await db.kv_set(KV_OBSERVATIONS, json.dumps(
                    observations, ensure_ascii=False))
                report["pull"] = "ok"
        except Exception as e:  # noqa: BLE001 — plan from cache if we can
            report["errors"].append(f"pull/observe failed: {repr(e)[:200]}")
            log.warning("dj.pull_failed", err=repr(e)[:300])

    if observations is None:
        raw = await db.kv_get(KV_OBSERVATIONS)
        if raw:
            observations = json.loads(raw)
            report["notes"].append(
                f"planned from cached observations "
                f"({observations.get('computed_at')})")

    # -- 3. PLAN -----------------------------------------------------------
    if observations is None:
        report["errors"].append("no observations available — no plan built")
    else:
        budgets = await load_budgets()
        excluded = frozenset(
            p.strip() for p in
            get_settings().dj_exclude_populations.split(",") if p.strip())
        plan = build_plan(
            observations, budgets,
            for_day=datetime.now(timezone.utc).date().isoformat(),
            exclude_populations=excluded)
        await save_plan(plan)
        report["plan_day"] = plan["for_day"]
        report["totals"] = plan["totals"]

    # -- 4. REPORT ---------------------------------------------------------
    await db.kv_set(KV_LAST_REPORT, json.dumps(report, ensure_ascii=False))
    log.info("dj.done", plan_day=report["plan_day"],
             errors=len(report["errors"]))
    return report


async def maybe_run_dj() -> None:
    """Worker hook (janitor cadence): run when the daily interval has
    elapsed. Self-gating, atomic claim, never raises."""
    try:
        s = get_settings()
        if not s.dj_enabled:
            return
        if not await db.kv_claim_interval(
                KV_LAST_RUN_TS, s.dj_interval_hours * 3600):
            return
        await run_dj()
    except Exception as e:  # noqa: BLE001 — the worker loop must survive
        log.warning("dj.crashed", err=repr(e)[:300])
