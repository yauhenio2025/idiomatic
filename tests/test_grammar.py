"""Deterministic grammar-pipeline tests (no network, no DB)."""

from pathlib import Path

from idiomatic.grammar import morphology as m
from idiomatic.grammar.apkg import build_grammar_apkg
from idiomatic.grammar.curriculum import PILOT_TOPICS_ES, topic_by_key
from idiomatic.grammar.generate import verify_item


def test_morphology_lookups():
    assert m.lookup("es", "hablar", "indicativo", "pretérito", "3s") == "habló"
    assert m.lookup("es", "ser", "subjuntivo", "imperfecto", "1s") == "fuera"
    assert m.lookup("es", "tener", "indicativo", "pretérito perfecto", "3p") == "han tenido"
    assert m.verify("es", "hacer", "indicativo", "futuro", "1s", "haré")[0]
    assert m.verify("es", "hablar", "indicativo", "pretérito", "3s", "hablo") == (False, "habló")


def test_every_pilot_verb_exists_in_morphology_db():
    missing = [
        (t.key, v)
        for t in PILOT_TOPICS_ES
        for v in t.verbs
        if m.lookup("es", v, t.mood, t.tense, "3s") is None
    ]
    assert not missing, missing


def test_verifier_rejects_bad_items():
    t = topic_by_key("es_preterito")
    good = {"infinitive": "tener", "person": "3s",
            "sentence": "Ayer el gobierno ___ (tener) que rectificar su postura.",
            "answer": "tuvo"}
    assert verify_item(t, good) == (True, "")
    assert not verify_item(t, dict(good, answer="tenía"))[0]      # wrong tense
    assert "accent" in verify_item(t, dict(good, answer="tuvó"))[1]
    assert not verify_item(t, dict(good, person="9x"))[0]
    assert not verify_item(t, dict(good, sentence="sin blank"))[0]
    leaky = dict(good, sentence="Ayer tuvo el gobierno ___ (tener) que rectificar.")
    assert verify_item(t, leaky) == (False, "answer leaks in sentence")


def test_apkg_build_and_guid_stability(tmp_path: Path):
    items = [{"id": 1, "topic": "es_preterito", "infinitive": "tener",
              "sentence": "Ayer el gobierno ___ (tener) que rectificar su postura.",
              "answer": "tuvo", "gloss_en": "g", "why_en": "w"}]
    labels = {t.key: (t.label, t.symbol) for t in PILOT_TOPICS_ES}
    out = tmp_path / "g.apkg"
    n1 = build_grammar_apkg(out_path=out, lang="es", items=items, topic_labels=labels)
    assert n1 == 1

    import json
    import sqlite3
    import zipfile
    with zipfile.ZipFile(out) as z:
        z.extract("collection.anki2", tmp_path)
    con = sqlite3.connect(tmp_path / "collection.anki2")
    guid, flds = con.execute("SELECT guid, flds FROM notes").fetchone()
    models = json.loads(con.execute("SELECT models FROM col").fetchone()[0])
    model = next(iter(models.values()))
    assert model["name"] == "Idiomatic Grammar Drill v1"
    assert len(model["flds"]) == 14
    assert "<b>tuvo</b>" in flds
    # GUID must be a pure function of (lang, item id) — rebuild and compare.
    out2 = tmp_path / "g2.apkg"
    build_grammar_apkg(out_path=out2, lang="es",
                       items=[dict(items[0], gloss_en="changed")],
                       topic_labels=labels)
    with zipfile.ZipFile(out2) as z:
        z.extract("collection.anki2", tmp_path / "b")
    con2 = sqlite3.connect(tmp_path / "b" / "collection.anki2")
    guid2 = con2.execute("SELECT guid FROM notes").fetchone()[0]
    assert guid == guid2
