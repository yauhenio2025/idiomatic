"""Personal Study DJ tests — pure functions only (no network, no DB):
deck-lane classification, the observer over a fixture collection
snapshot, planner arithmetic incl. overflow flagging, and budget
validation."""

import sqlite3

import pytest

from idiomatic.dj import (
    DEFAULT_BUDGETS_MIN,
    MIN_OBS_FOR_MEDIAN,
    NEW_MIX_WEIGHTS_V1,
    build_plan,
    classify_deck,
    compute_observations,
    validate_budgets,
)

NOW_MS = 1_754_000_000_000          # fixed for determinism
NOW_S = NOW_MS // 1000
CRT = NOW_S - 100 * 86400           # collection day 100
DAY_MS = 86_400_000


# --- classification ---------------------------------------------------------

@pytest.mark.parametrize("name,expected", [
    ("IT Italian", ("it", "other")),
    ("IT Italian\x1f2 Grammar\x1f1 Tempi", ("it", "grammar")),
    ("ES Spanish::1 Expressions::1 Fluency", ("es", "expressions")),
    ("DE German\x1f6 My Errors\x1fArtikel", ("de", "my_errors")),
    ("PT Portuguese\x1f3 Tenses\x1f2 Exercises", ("pt", "tenses")),
    ("FR French\x1f7 Rescue", ("fr", "rescue")),
    ("ZH Mandarin\x1f8 Pimsleur", ("zh", "pimsleur")),
    ("IT Italian\x1fUnnumbered Deck", ("it", "other")),
    ("zz Dormant\x1fIT old stuff", None),
    ("0 Today\x1fIT Italian", None),
    ("Default", None),
])
def test_classify_deck(name, expected):
    assert classify_deck(name) == expected


# --- observer fixture -------------------------------------------------------

def _mk_collection(path, decks, notes, cards, revlog, *, legacy_decks=False):
    """Minimal modern-schema collection: col/decks/notes/cards/revlog with
    exactly the columns the observer reads. legacy_decks=True drops the
    decks table and stores the deck map as JSON in col.decks instead."""
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE col (id INTEGER PRIMARY KEY, crt INTEGER, decks TEXT);
        CREATE TABLE notes (id INTEGER PRIMARY KEY, tags TEXT);
        CREATE TABLE cards (id INTEGER PRIMARY KEY, nid INTEGER, did INTEGER,
                            queue INTEGER, due INTEGER, odue INTEGER,
                            odid INTEGER);
        CREATE TABLE revlog (id INTEGER PRIMARY KEY, cid INTEGER,
                             ease INTEGER, time INTEGER);
    """)
    if legacy_decks:
        import json
        blob = json.dumps({str(did): {"name": name.replace("\x1f", "::")}
                           for did, name in decks.items()})
        con.execute("INSERT INTO col VALUES (1, ?, ?)", (CRT, blob))
    else:
        con.execute("CREATE TABLE decks (id INTEGER PRIMARY KEY, name TEXT)")
        con.execute("INSERT INTO col VALUES (1, ?, NULL)", (CRT,))
        con.executemany("INSERT INTO decks VALUES (?, ?)", decks.items())
    con.executemany("INSERT INTO notes VALUES (?, ?)", notes)
    con.executemany("INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?)", cards)
    con.executemany("INSERT INTO revlog VALUES (?, ?, ?, ?)", revlog)
    con.commit()
    con.close()


DECKS = {
    1: "IT Italian",
    2: "IT Italian\x1f2 Grammar",
    3: "IT Italian\x1f2 Grammar\x1f1 Tempi",
    4: "IT Italian\x1f1 Expressions\x1f1 Fluency",
    5: "0 Today\x1fIT Italian",          # filtered deck — remap via odid
    6: "Default",
    7: "ES Spanish\x1f3 Tenses\x1f1 Production",
}

NOTES = [(i, "") for i in range(1, 8)] + [(8, " youtube idiomatic-podcast ")]

CARDS = [
    # (id, nid, did, queue, due, odue, odid)
    (1, 1, 3, 2, 100, 0, 0),           # review due today       → due grammar
    (2, 2, 3, 2, 101, 0, 0),           # due tomorrow           → not due
    (3, 3, 3, 0, 0, 0, 0),             # new                    → reservoir grammar
    (4, 4, 4, 1, NOW_S - 10, 0, 0),    # learning, due passed   → due expressions
    (5, 5, 4, -1, 100, 0, 0),          # suspended              → excluded
    (6, 6, 5, 2, 87, 99, 3),           # in filtered deck; odid=grammar,
                                       # odue 99 ≤ day 100      → due grammar
    (7, 7, 6, 0, 0, 0, 0),             # Default deck           → unclassified
    (8, 8, 2, 0, 0, 0, 0),             # tagged podcast in grammar lane
                                       #                        → new podcast_lesson
    (9, 1, 7, 3, 100, 0, 0),           # es day-learn due today → due tenses
    (10, 2, 4, 0, 0, 0, 0),            # new                    → reservoir expressions
]

REVLOG = (
    # 20 grammar reps 8 s each, older than 7 d (but inside 90 d)
    [(NOW_MS - 10 * DAY_MS - i, 1, 3, 8000) for i in range(20)]
    # 5 grammar reps 8 s each within the last 7 d
    + [(NOW_MS - 2 * DAY_MS - i, 1, 3, 8000) for i in range(5)]
    # manual reschedule (ease 0) — never counts as study
    + [(NOW_MS - 1 * DAY_MS, 1, 0, 50000)]
    # 3 expression reps → below MIN_OBS, prior applies; older than 7 d
    + [(NOW_MS - 20 * DAY_MS - i, 4, 3, 12000) for i in range(3)]
)


@pytest.fixture()
def observations(tmp_path):
    p = str(tmp_path / "collection.anki2")
    _mk_collection(p, DECKS, NOTES, CARDS, REVLOG)
    return compute_observations(p, now_ms=NOW_MS)


def test_observer_due_and_reservoir_by_population(observations):
    it = observations["langs"]["it"]
    assert it["due"] == {"grammar": 2, "expressions": 1}
    assert it["new_reservoir"] == {
        "grammar": 1, "podcast_lesson": 1, "expressions": 1}
    assert observations["langs"]["es"]["due"] == {"tenses": 1}
    assert observations["unclassified_cards"] == 1


def test_observer_secs_per_rep_observed_vs_prior(observations):
    spr = observations["langs"]["it"]["secs_per_rep"]
    assert spr["grammar"] == {"secs": 8.0, "n_obs": 25, "source": "observed"}
    assert spr["expressions"]["source"] == "prior"
    assert spr["expressions"]["n_obs"] == 3 < MIN_OBS_FOR_MEDIAN
    assert spr["expressions"]["secs"] == 8.0     # the documented prior


def test_observer_last7_distribution(observations):
    last7 = observations["langs"]["it"]["last7"]
    assert last7["grammar"] == {"reps": 5, "minutes": 0.7}   # 5 × 8 s
    assert "expressions" not in last7            # those reps were 20 d ago


def test_observer_legacy_decks_json_fallback(tmp_path):
    p = str(tmp_path / "legacy.anki2")
    _mk_collection(p, DECKS, NOTES, CARDS, REVLOG, legacy_decks=True)
    obs = compute_observations(p, now_ms=NOW_MS)
    assert obs["langs"]["it"]["due"] == {"grammar": 2, "expressions": 1}


# --- planner ----------------------------------------------------------------

def _obs(langs):
    return {"schema": 1, "computed_at": "2026-08-09T05:00:00+00:00",
            "langs": langs}


def _lang_obs(due=None, reservoir=None, spr=None):
    return {
        "due": due or {},
        "new_reservoir": reservoir or {},
        "secs_per_rep": {
            pop: {"secs": secs, "n_obs": 99, "source": "observed"}
            for pop, secs in (spr or {}).items()},
        "last7": {},
    }


def test_plan_due_first_then_weighted_new_mix():
    obs = _obs({"it": _lang_obs(
        due={"expressions": 60},
        reservoir={"grammar": 100, "expressions": 50},
        spr={"expressions": 10.0})})
    plan = build_plan(obs, {"it": 25}, "2026-08-09")
    assert plan["schema"] == 1
    (lang,) = plan["languages"]
    assert lang["anki_root"] == "IT Italian"
    assert lang["deck_name"] == "0 Today::IT Italian"
    # dues: 60 × 10 s = 10 min of the 25-min budget
    assert lang["due"]["cards"] == 60
    assert lang["due"]["est_minutes"] == 10.0
    assert lang["due"]["overflow"] is False
    assert lang["due"]["search"] == 'deck:"IT Italian" is:due -is:suspended'
    # 15 min remain; weights renormalize over grammar(.30)+expressions(.25)
    assert lang["new"]["minutes_available"] == 15.0
    mix = {m["population"]: m for m in lang["new"]["mix"]}
    assert set(mix) == {"grammar", "expressions"}
    g, e = mix["grammar"], mix["expressions"]
    assert g["weight"] == round(0.30 / 0.55, 3)
    # grammar: 8.18 min ÷ (12 s prior × 2.5) = 16 cards
    assert g["cards"] == 16 and g["secs_per_new_card"] == 30.0
    # expressions: 6.82 min ÷ (10 s observed × 2.5) = 16 cards
    assert e["cards"] == 16 and e["secs_per_new_card"] == 25.0
    assert plan["totals"]["due_cards"] == 60
    assert plan["totals"]["new_cards"] == 32
    assert plan["totals"]["langs_overflowing"] == []


def test_plan_overflow_flagged_never_dropped():
    obs = _obs({"it": _lang_obs(
        due={"expressions": 60}, reservoir={"grammar": 100},
        spr={"expressions": 10.0})})
    plan = build_plan(obs, {"it": 5}, "2026-08-09")
    (lang,) = plan["languages"]
    assert lang["due"]["overflow"] is True
    assert lang["due"]["overflow_minutes"] == 5.0     # 10 est − 5 budget
    assert lang["due"]["cards"] == 60                 # full debt reported
    assert lang["due"]["limit"] == 30                 # amortized: 5min/10s
    assert any("AMORTIZING" in n for n in lang["notes"])
    assert lang["new"]["mix"] == []                   # no new cards today
    assert plan["totals"]["langs_overflowing"] == ["it"]


def test_plan_search_specs_compose_from_estate_tree():
    obs = _obs({"de": _lang_obs(
        reservoir={"grammar": 50, "podcast_lesson": 5, "tenses": 30})})
    # 60-min budget so even the 90 s/slide podcast prior fits ≥ 1 card
    plan = build_plan(obs, {"de": 60}, "2026-08-09")
    mix = {m["population"]: m for m in plan["languages"][0]["new"]["mix"]}
    assert mix["grammar"]["search"] == \
        'deck:"DE German::2 Grammar" is:new -tag:idiomatic-podcast'
    assert mix["podcast_lesson"]["search"] == \
        'deck:"DE German" is:new tag:idiomatic-podcast'
    assert mix["tenses"]["search"] == 'deck:"DE German::3 Tenses" is:new'
    assert all(m["order"] == "due_position" for m in mix.values())


def test_plan_reservoir_caps_new_cards():
    obs = _obs({"it": _lang_obs(reservoir={"grammar": 2})})
    plan = build_plan(obs, {"it": 25}, "2026-08-09")
    (m,) = plan["languages"][0]["new"]["mix"]
    assert m["cards"] == 2                            # 25 min could fit 50


def test_plan_skips_paused_and_unknown_languages():
    obs = _obs({})
    plan = build_plan(obs, {"it": 0, "xx": 25, "zh": 20}, "2026-08-09")
    assert [lg["lang"] for lg in plan["languages"]] == ["zh"]
    assert any("no observation data" in n
               for n in plan["languages"][0]["notes"])


def test_plan_prior_populations_get_a_note():
    obs = _obs({"it": {
        "due": {"exercises": 10},
        "new_reservoir": {},
        "secs_per_rep": {"exercises": {"secs": 20.0, "n_obs": 4,
                                       "source": "prior"}},
        "last7": {}}})
    plan = build_plan(obs, {"it": 25}, "2026-08-09")
    assert any("prior" in n for n in plan["languages"][0]["notes"])


def test_new_mix_weights_documented_and_normalized():
    assert abs(sum(NEW_MIX_WEIGHTS_V1.values()) - 1.0) < 1e-9
    assert "pimsleur" not in NEW_MIX_WEIGHTS_V1      # external course lane
    assert "other" not in NEW_MIX_WEIGHTS_V1


# --- budgets ----------------------------------------------------------------

def test_default_budgets_match_commission():
    assert DEFAULT_BUDGETS_MIN == {
        "de": 25, "es": 25, "fr": 25, "it": 25, "pt": 25, "zh": 20}


def test_validate_budgets():
    assert validate_budgets({"it": 30, "zh": 0}) == {"it": 30, "zh": 0}
    for bad in [None, {}, {"xx": 25}, {"it": "25"}, {"it": 999},
                {"it": -1}, {"it": True}]:
        with pytest.raises(ValueError):
            validate_budgets(bad)


def test_owner_exclusions_drop_dues_and_amend_search():
    """Excluded populations (owner curation, e.g. pimsleur) are reported
    but never planned, and the due search subtracts their lanes."""
    from idiomatic import dj
    obs = {"langs": {"it": {
        "due": {"pimsleur": 1500, "expressions": 40},
        "new_reservoir": {},
        "secs_per_rep": {},
        "recent": {},
    }}}
    plan = dj.build_plan(obs, {"it": 25}, for_day="2026-08-09",
                         exclude_populations=frozenset({"pimsleur"}))
    (lang,) = plan["languages"]
    assert "pimsleur" not in lang["due"]["by_population"]
    assert lang["due"]["cards"] == 40
    assert any("excluded by owner curation" in n and "1500" in n
               for n in lang["notes"])
    assert '-deck:"IT Italian::8 Pimsleur"' in lang["due"]["search"]
    assert not lang["due"]["overflow"]


def test_overflow_amortizes_dues_to_budget_with_eta():
    from idiomatic import dj
    obs = {"langs": {"fr": {
        "due": {"expressions": 700},
        "new_reservoir": {},
        "secs_per_rep": {"expressions": {"secs": 8.0, "source": "prior"}},
        "recent": {},
    }}}
    plan = dj.build_plan(obs, {"fr": 8}, for_day="2026-08-09")
    (lang,) = plan["languages"]
    assert lang["due"]["overflow"]
    assert lang["due"]["limit"] < 700
    assert lang["due"]["limit"] == 60  # 8 min * 60s / 8s-per-rep
    assert any("AMORTIZING" in n and "days to clear" in n
               for n in lang["notes"])
