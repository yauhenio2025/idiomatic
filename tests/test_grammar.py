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
        if t.verify == "morph"
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


def test_every_topic_has_cluster_and_seed_rows_complete():
    from idiomatic.grammar.curriculum import (
        GRAMMAR_LANGS, PLANNED_UNITS, topics_for, unit_seed_rows,
    )
    for lang in GRAMMAR_LANGS:
        for t in topics_for(lang):
            assert t.cluster, f"{t.key} has no cluster"
    rows = unit_seed_rows()
    keys = [r["key"] for r in rows]
    assert len(keys) == len(set(keys)), "duplicate unit keys in seed"
    n_topics = sum(len(topics_for(lang)) for lang in GRAMMAR_LANGS)
    assert len(rows) == n_topics + len(PLANNED_UNITS)
    for r in rows:
        assert r["cluster"] and r["label"] and r["status"] in ("active", "planned")
    # active units sort before planned ones within a language
    assert all(r["sort_order"] >= 1000 for r in rows
               if r["status"] == "planned")


def test_apkg_subdecks_per_cluster(tmp_path: Path):
    """Items from different clusters land in different subdecks; GUIDs
    stay the pure (lang, id) function they were before subdecks."""
    import json
    import sqlite3
    import zipfile
    from idiomatic.grammar.curriculum import topics_for
    items = [{"id": 1, "topic": "es_preterito", "infinitive": "tener",
              "sentence": "Ayer el gobierno ___ (tener) que rectificar su postura.",
              "answer": "tuvo", "gloss_en": "g", "why_en": ""},
             {"id": 2, "topic": "es_cmd_tu", "infinitive": "poner",
              "sentence": "Por favor, ___ (poner) la mesa antes de cenar.",
              "answer": "pon", "gloss_en": "g", "why_en": ""}]
    labels = {t.key: (t.label, t.symbol) for t in PILOT_TOPICS_ES}
    clusters = {t.key: t.cluster for t in topics_for("es")}
    out = tmp_path / "g.apkg"
    n = build_grammar_apkg(out_path=out, lang="es", items=items,
                           topic_labels=labels, topic_clusters=clusters)
    assert n == 2
    with zipfile.ZipFile(out) as z:
        z.extract("collection.anki2", tmp_path)
    con = sqlite3.connect(tmp_path / "collection.anki2")
    decks = json.loads(con.execute("SELECT decks FROM col").fetchone()[0])
    names = {d["name"] for d in decks.values()}
    assert "Idiomatic Grammar ES::1 Tiempos" in names
    assert "Idiomatic Grammar ES::4 Imperativo" in names
    # note GUIDs are unchanged by the subdeck split
    import hashlib
    guids = {g for (g,) in con.execute("SELECT guid FROM notes")}
    expect = {hashlib.sha1(f"idiomatic-grammar::es::{i}".encode()
                           ).hexdigest()[:16] for i in (1, 2)}
    assert guids == expect
    # deck ids are stable functions of the full deck name
    from idiomatic.grammar.apkg import _deck_id, deck_name_for
    assert deck_name_for("es", "1 Tiempos") == "Idiomatic Grammar ES::1 Tiempos"
    assert deck_name_for("es", "") == "Idiomatic Grammar ES"
    ids = {int(k) for k in decks if decks[k]["name"].startswith("Idiomatic")}
    assert _deck_id("Idiomatic Grammar ES::1 Tiempos") in ids


def test_full_sentence_text():
    from idiomatic.grammar.audio import full_sentence_text
    assert (full_sentence_text("Ayer el ministro ___ (negar) las acusaciones.",
                               "negó", "negar")
            == "Ayer el ministro negó las acusaciones.")
    assert full_sentence_text("Sin blank aquí.", "x", "y") == "Sin blank aquí."


def test_apkg_with_audio(tmp_path: Path):
    audio_dir = tmp_path / "media"
    audio_dir.mkdir()
    (audio_dir / "idg_es_1.mp3").write_bytes(b"\xff\xfb" + b"\x00" * 100)
    items = [{"id": 1, "topic": "es_preterito", "infinitive": "tener",
              "sentence": "Ayer el gobierno ___ (tener) que rectificar su postura.",
              "answer": "tuvo", "gloss_en": "g", "why_en": ""},
             {"id": 2, "topic": "es_preterito", "infinitive": "hacer",
              "sentence": "Anoche la oposición ___ (hacer) público el informe.",
              "answer": "hizo", "gloss_en": "g", "why_en": ""}]
    labels = {t.key: (t.label, t.symbol) for t in PILOT_TOPICS_ES}
    out = tmp_path / "g.apkg"
    build_grammar_apkg(out_path=out, lang="es", items=items, topic_labels=labels,
                       audio={1: "idg_es_1.mp3"}, audio_dir=audio_dir)

    import json
    import sqlite3
    import zipfile
    with zipfile.ZipFile(out) as z:
        media_map = json.loads(z.read("media"))
        z.extract("collection.anki2", tmp_path)
    assert "idg_es_1.mp3" in media_map.values()
    con = sqlite3.connect(tmp_path / "collection.anki2")
    rows = {f.split("\x1f")[0]: f for (f,) in
            con.execute("SELECT flds FROM notes")}
    assert "[sound:idg_es_1.mp3]" in rows["1"]   # item 1 has audio in Extra1
    assert "[sound:" not in rows["2"]            # item 2 text-only


def test_blind_topic_static_checks():
    t = topic_by_key("es_clitics_selo")
    good = {"sentence": "¿Le entregaste las llaves al portero? Sí, ___ di esta mañana.",
            "answer": "se las"}
    assert verify_item(t, good) == (True, "")
    assert "inventory" in verify_item(t, dict(good, answer="le las"))[1]
    # word-boundary leak: 'los' in the sentence must NOT flag answer 'lo'
    t2 = topic_by_key("es_clitics_dir")
    ok, why = verify_item(t2, {"sentence": "¿Compraste los libros? Sí, ___ compré ayer.",
                               "answer": "lo"})
    assert why != "answer leaks in sentence"
    # a real leak still flags
    assert verify_item(t2, {"sentence": "Lo vi ayer y ___ saludé.",
                            "answer": "lo"}) == (False, "answer leaks in sentence")


def test_por_para_inventory():
    t = topic_by_key("es_por_para")
    assert verify_item(t, {"sentence": "El tren sale ___ Madrid a las ocho.",
                           "answer": "para"})[0]
    assert not verify_item(t, {"sentence": "x ___ y", "answer": "de"})[0]


def test_verb_prep_bank_loads_into_prompt():
    from idiomatic.grammar.generate import build_prompt
    t = topic_by_key("es_verb_prep")
    p = build_prompt(t, 12)
    assert "Pairs to draw from" in p
    # The bank is randomly SAMPLED into the prompt, so never assert
    # specific verbs (that made this test flaky ~1 run in 3) — assert
    # the structural shape: several "verb + prep — gloss (trap: …)"
    # lines drawn from the bank's closed preposition inventory.
    import re
    pair_lines = re.findall(r"^- \S+ \+ (a|de|en|con|por|para|contra) — .+\(trap: ",
                            p, flags=re.MULTILINE)
    assert len(pair_lines) >= 5, p[-500:]


def test_de_article_verification():
    t = topic_by_key("de_prep_fest")
    good = {"sentence": "Er kam gestern mit ___ Zug aus Berlin zurück.",
            "noun": "Zug", "prep": "mit", "case": "dat", "definite": True,
            "answer": "dem"}
    assert verify_item(t, good) == (True, "")
    assert "wrong article" in verify_item(t, dict(good, answer="den"))[1]
    assert "governs" in verify_item(t, dict(good, case="akk", answer="den"))[1]
    assert "not in bank" in verify_item(t, dict(good, prep="zwecks"))[1]
    assert "two-way" in verify_item(
        t, dict(good, prep="in", sentence="Er stieg in ___ Zug."))[1]
    # genitive with masculine noun → surface form would change → reject
    gen = {"sentence": "Während ___ Krieg litt die Stadt sehr.",
           "noun": "Krieg", "prep": "während", "case": "gen",
           "definite": True, "answer": "des"}
    assert "genitive with m/n" in verify_item(t, gen)[1]
    # feminine genitive is fine
    genf = {"sentence": "Während ___ Woche arbeitet sie in Hamburg.",
            "noun": "Woche", "prep": "während", "case": "gen",
            "definite": True, "answer": "der"}
    assert verify_item(t, genf) == (True, "")

    tg = topic_by_key("de_gender")
    g = {"sentence": "___ Regierung hat die Reform gestern beschlossen.",
         "noun": "Regierung", "case": "nom", "definite": True, "answer": "die"}
    assert verify_item(tg, g) == (True, "")
    assert "must be nominative" in verify_item(tg, dict(g, case="akk"))[1]
    assert "not in gender DB" in verify_item(
        tg, dict(g, noun="Xyzfoo", sentence="___ Xyzfoo ist da."))[1]

    tw = topic_by_key("de_prep_wechsel")
    w = {"sentence": "Er hängt das Bild an ___ Wand im Wohnzimmer.",
         "noun": "Wand", "prep": "an", "case": "akk", "definite": True,
         "answer": "die"}
    assert verify_item(tw, w) == (True, "")
    assert "Wechsel" in verify_item(tw, dict(w, prep="mit"))[1]


def test_romance_verb_verification():
    from idiomatic.grammar.curriculum import topics_for
    fr = {t.key: t for t in topics_for("fr")}
    it = {t.key: t for t in topics_for("it")}
    pt = {t.key: t for t in topics_for("pt")}
    # Each language keeps its seven morphology units; additional formats such
    # as the attested F3 unit are deliberately appended to the curriculum.
    assert all(sum(t.verify == "morph" for t in topics.values()) == 7
               for topics in (fr, it, pt))

    t = fr["fr_passe_compose"]
    good = {"infinitive": "aller", "person": "3s",
            "sentence": "Hier soir, le ministre ___ (aller) au sommet européen.",
            "answer": "est allé"}
    assert verify_item(t, good) == (True, "")
    assert "wrong form" in verify_item(t, dict(good, answer="a allé"))[1]

    t = it["it_passato_remoto"]
    good = {"infinitive": "fare", "person": "3s",
            "sentence": "Nel 1968 il governo ___ (fare) una scelta decisiva.",
            "answer": "fece"}
    assert verify_item(t, good) == (True, "")
    assert not verify_item(t, dict(good, answer="fecette"))[0]

    t = pt["pt_futuro_subjuntivo"]
    good = {"infinitive": "fazer", "person": "3s",
            "sentence": "Quando o governo ___ (fazer) a reforma, o país vai mudar.",
            "answer": "fizer"}
    assert verify_item(t, good) == (True, "")
    # wrong-mood slips get caught
    assert not verify_item(t, dict(good, answer="fará"))[0]
    # tu and vós are banned — Brazilian drills are você-based
    for person, ans in (("2s", "fizeres"), ("2p", "fizerdes")):
        bad = dict(good, person=person, answer=ans)
        assert "Brazilian" in verify_item(t, bad)[1]


def test_every_fip_unit_cell_exists():
    from idiomatic.grammar.curriculum import topics_for
    missing = []
    for lang in ("fr", "it", "pt"):
        for t in topics_for(lang):
            for v in t.verbs:
                if m.lookup(lang, v, t.mood, t.tense, "3s") is None:
                    missing.append((t.key, v))
    assert not missing, missing


def test_compound_agreement_tolerance():
    from idiomatic.grammar.curriculum import topics_for
    fr = {t.key: t for t in topics_for("fr")}
    it = {t.key: t for t in topics_for("it")}
    t = fr["fr_passe_compose"]
    fem = {"infinitive": "aller", "person": "3s",
           "sentence": "Hier, la ministre ___ (aller) au sommet européen.",
           "answer": "est allée"}
    assert verify_item(t, fem) == (True, "")          # feminine agreement OK
    wrong_aux = dict(fem, infinitive="monter", answer="a monté",
                     sentence="Hier, la ministre ___ (monter) au podium.")
    assert "wrong form" in verify_item(t, wrong_aux)[1]  # aux still strict
    # avoir participle restored after the 'eu'-collision fix
    assert m.lookup("fr", "avoir", "indicatif", "passé composé", "2p") == "avez eu"
    ti = it["it_passato_prossimo"]
    fem_it = {"infinitive": "andare", "person": "3p",
              "sentence": "Ieri le giornaliste ___ (andare) alla conferenza.",
              "answer": "sono andate"}
    assert verify_item(ti, fem_it) == (True, "")


def test_vocab_lines_injection():
    from idiomatic.grammar.generate import build_prompt
    t = topic_by_key("es_preterito")
    vocab = [{"term": "desprovista de", "gloss": "devoid of", "status": 0},
             {"term": "concretado", "gloss": None, "status": 1}]
    p = build_prompt(t, 5, extra_vocab=vocab)
    assert "OPTIONAL vocabulary" in p
    assert "desprovista de — devoid of" in p
    assert "- concretado" in p
    assert "never as the blank" in p
    # without vocab the prompt is unchanged
    assert "OPTIONAL vocabulary" not in build_prompt(t, 5)


def test_lingq_row_parsing():
    from idiomatic.lingq import _row_from_card
    card = {"pk": 123, "term": " desprovista de ", "fragment": "x",
            "status": 0, "extended_status": None, "notes": "",
            "hints": [{"locale": "en", "text": "devoid of"}],
            "tags": ["news"], "srs_due_date": "2026-08-01T00:00:00Z"}
    r = _row_from_card("es", card)
    assert r["term"] == "desprovista de" and r["lingq_id"] == 123
    assert r["hints"] == [{"locale": "en", "text": "devoid of"}]
    assert _row_from_card("es", {"pk": None, "term": "x"}) is None
    assert _row_from_card("es", {"pk": 1, "term": "  "}) is None
