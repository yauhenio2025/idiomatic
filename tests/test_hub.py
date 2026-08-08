"""Expression Hub tests: identity recipes, frozen models, pilot builder,
and the durable-ID schema staging (ephemeral Postgres, same harness as
test_rescue.py). Deterministic, no network."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import zipfile
from pathlib import Path

import pytest

from idiomatic.hub import apkg as hub_apkg
from idiomatic.hub import identity


# --- identity recipes -------------------------------------------------------

def test_guid_recipes_match_design_doc():
    # Exact recipe from design §4.1/§4.2 — these strings are a frozen
    # migration contract; changing them orphans every future release.
    assert identity.hub_guid("es", 439) == hashlib.sha1(
        b"idiomatic-expression-hub-v1::es::439").hexdigest()[:16]
    assert identity.example_guid(2503) == hashlib.sha1(
        b"idiomatic-expression-example-v1::2503").hexdigest()[:16]


def test_pilot_guid_namespace_never_collides_with_production():
    prod = {identity.hub_guid("es", 439), identity.example_guid(2503)}
    pil = {identity.pilot_hub_guid("es", 439),
           identity.pilot_example_guid(2503)}
    assert prod.isdisjoint(pil)
    # and both are stable pure functions
    assert identity.pilot_hub_guid("es", 439) == identity.pilot_hub_guid("es", 439)


def test_source_key_recipe_matches_sql_backfill():
    # Python must mirror db/schema.sql's md5-based backfill exactly.
    phrase = "Está tirado en el suelo."
    expected = ("youtube:v1:abc123XYZ_-:p"
                + hashlib.md5(phrase.encode()).hexdigest()[:8])
    assert identity.source_key_youtube("abc123XYZ_-", source_phrase=phrase) == expected
    assert identity.source_key_youtube("abc123XYZ_-", row_id=77) == \
        "youtube:v1:abc123XYZ_-:r77"
    with pytest.raises(ValueError):
        identity.source_key_youtube("abc123XYZ_-")


def test_stable_keys_and_media_names():
    assert identity.stable_key_legacy(2503) == "legacy:2503"
    assert identity.stable_key_topup(9, 2, 3) == "topup:9:2:3"
    h8 = identity.hash8(b"bytes")
    assert len(h8) == 8 and int(h8, 16) >= 0
    assert identity.image_media_name(2503, "a1b2c3d4") == "idh_ex_2503_a1b2c3d4.jpg"
    assert identity.context_media_name(41, "deadbeef") == "idh_ctx_41_deadbeef.mp3"
    assert identity.expression_audio_media_name(41, "deadbeef") == \
        "idh_expr_41_deadbeef.mp3"
    assert identity.example_audio_media_name(2503, "en", "12345678") == \
        "idh_exau_2503_en_12345678.mp3"
    with pytest.raises(ValueError):
        identity.example_audio_media_name(2503, "de", "12345678")


# --- frozen model contracts -------------------------------------------------

def test_hub_model_frozen_shape():
    m = hub_apkg.make_hub_model()
    assert m.model_id == 1_820_180_001
    assert m.name == "Idiomatic Expression Hub v1"
    assert [f["name"] for f in m.fields] == [
        "ExpressionId", "Lang", "Expression", "GlossEN", "UsageLineEN",
        "KeySynonym", "FalseFriend", "ExamplesHTML", "SourcesHTML",
        "ContextAudio", "ExpressionAudio", "Extra1", "Extra2", "Extra3"]
    # TWO cards: the accepted TL-front hub card + the amended EN→TL
    # production card (owner amendment 1, binds at model freeze).
    assert [t["name"] for t in m.templates] == ["Hub", "EN -> expression"]
    # Amendment 2: the context clip is embedded on BOTH backs.
    for t in m.templates:
        assert "{{#ContextAudio}}" in t["afmt"]
    # The TL-front card leaks nothing: expression only on the front.
    hub_front = m.templates[0]["qfmt"]
    assert "{{Expression}}" in hub_front
    for leak in ("GlossEN", "UsageLineEN", "ExamplesHTML", "KeySynonym"):
        assert leak not in hub_front
    # The EN→TL front never shows the answer.
    en2tl_front = m.templates[1]["qfmt"]
    assert "{{Expression}}" not in en2tl_front
    assert "{{GlossEN}}" in en2tl_front
    # sort field = Expression (design §4.1)
    assert m.sort_field_index == 2


def test_example_model_frozen_shape():
    m = hub_apkg.make_example_model()
    assert m.model_id == 1_820_180_002
    assert m.name == "Idiomatic Expression Example v1"
    assert [f["name"] for f in m.fields] == [
        "ExpressionId", "ExampleId", "Lang", "English", "Target",
        "EnglishAudio", "TargetAudio", "Image", "Expression", "GlossEN",
        "SourceHTML", "Origin", "Extra1", "Extra2", "Extra3"]
    # exactly one template, ASCII arrow name (migration §5.1 distinguishes
    # it from the legacy Unicode-arrow template).
    assert [t["name"] for t in m.templates] == ["EN -> target"]
    front = m.templates[0]["qfmt"]
    # design §5.1: no image and no expression hint on the front.
    assert "{{Image}}" not in front and "{{Expression}}" not in front
    assert m.sort_field_index == 4


def test_deck_names_compose_from_anki_root():
    assert hub_apkg.hub_deck_name("es") == \
        "ES Spanish::1 Expressions::2 Expression Focus"
    assert hub_apkg.fluency_deck_name("de") == \
        "DE German::1 Expressions::1 Fluency"
    with pytest.raises(ValueError):
        hub_apkg.hub_deck_name("xx")
    assert hub_apkg.PILOT_DECK_ROOT == "ZZ Hub Pilot (disposable)"


# --- field compilation ------------------------------------------------------

def test_examples_html_grid():
    html_out = hub_apkg.build_examples_html([
        {"example_id": 2503, "target_text": "Trabaja <en> la sombra.",
         "en_text": "He works in the shadows.",
         "image_media": "idh_ex_2503_a1b2c3d4.jpg"},
        {"example_id": 2504, "target_text": "Otra frase.",
         "en_text": "Another sentence.", "image_media": None},
    ])
    # data-example-id set equality is the projection audit hook.
    assert 'data-example-id="2503"' in html_out
    assert 'data-example-id="2504"' in html_out
    assert html_out.count("rail-item") == 2
    assert '<img src="idh_ex_2503_a1b2c3d4.jpg"' in html_out
    assert html_out.count("<img") == 1  # no placeholder for the imageless row
    assert "&lt;en&gt;" in html_out     # text is escaped
    # Tile layout (owner verdict 2026-08-09): image ABOVE the sentence pair.
    first_tile = html_out.split("</div>\n")[0]
    assert first_tile.index("<img") < first_tile.index("rail-tl")


def test_hub_css_is_a_tile_grid():
    """Owner verdict 2026-08-09: ~3 tiles per row, responsive to 2/1."""
    css = hub_apkg.make_hub_model().css
    assert "display: grid" in css
    assert "repeat(3, 1fr)" in css
    assert "repeat(2, 1fr)" in css      # tablet/phone step-down
    assert css.count("@media") >= 2     # and a narrow-phone step-down
    assert ".card.night_mode .rail-item" in css


def test_sources_html_visible_title_and_url():
    out = hub_apkg.build_sources_html([
        {"title": "Erste <Fahrt>", "url": "https://www.youtube.com/watch?v=x"}])
    assert "Erste &lt;Fahrt&gt;" in out
    assert "https://www.youtube.com/watch?v=x" in out


# --- package assembly -------------------------------------------------------

def _pilot_fixture(tmp_path: Path) -> tuple[dict, dict, list[Path]]:
    img = tmp_path / "idh_ex_2503_a1b2c3d4.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0fakejpg")
    ctx = tmp_path / "idh_ctx_41_deadbeef.mp3"
    ctx.write_bytes(b"ID3fakemp3")
    hub = {
        "expression_id": 439, "lang": "es", "expression": "a primera hora",
        "gloss_en": "first thing in the morning",
        "usage_line_en": "Used for the earliest part of the working day.",
        "key_synonym": None, "false_friend": None,
        "examples": [
            {"example_id": 2503, "target_text": "Salió a primera hora.",
             "en_text": "He left first thing.",
             "image_media": "idh_ex_2503_a1b2c3d4.jpg"}],
        "sources": [{"title": "Noticias", "youtube_id": "iOUBSDg6wHI",
                     "url": "https://www.youtube.com/watch?v=iOUBSDg6wHI"}],
        "context_audio_media": "idh_ctx_41_deadbeef.mp3",
        "expression_audio_media": None,
    }
    example = {
        "expression_id": 439, "example_id": 2503, "lang": "es",
        "en_text": "He left first thing.",
        "target_text": "Salió a primera hora.",
        "en_audio_media": None, "tl_audio_media": None,
        "image_media": "idh_ex_2503_a1b2c3d4.jpg",
        "expression": "a primera hora",
        "gloss_en": "first thing in the morning",
        "source": {"title": "Noticias",
                   "url": "https://www.youtube.com/watch?v=iOUBSDg6wHI"},
        "origin": "initial",
    }
    return hub, example, [img, ctx]


def test_build_pilot_apkg_round_trip(tmp_path: Path):
    hub, example, media = _pilot_fixture(tmp_path)
    out = tmp_path / "pilot.apkg"
    n_hub, n_ex = hub_apkg.build_hub_apkg(
        out_path=out, hub_notes=[hub], example_notes=[example],
        media_files=media, pilot=True)
    assert (n_hub, n_ex) == (1, 1)

    with zipfile.ZipFile(out) as z:
        z.extract("collection.anki2", tmp_path / "x")
        media_map = json.loads(z.read("media"))
    packaged = set(media_map.values())
    assert {"idh_ex_2503_a1b2c3d4.jpg", "idh_ctx_41_deadbeef.mp3"} <= packaged

    con = sqlite3.connect(tmp_path / "x" / "collection.anki2")
    decks = json.loads(con.execute("SELECT decks FROM col").fetchone()[0])
    names = {d["name"] for d in decks.values()}
    assert "ZZ Hub Pilot (disposable)::Hub" in names
    assert "ZZ Hub Pilot (disposable)::Fluency" in names
    # No production destination may appear in a pilot build.
    assert not any("1 Expressions" in n for n in names)

    models = json.loads(con.execute("SELECT models FROM col").fetchone()[0])
    by_name = {m["name"]: m for m in models.values()}
    assert len(by_name["Idiomatic Expression Hub v1"]["tmpls"]) == 2
    assert len(by_name["Idiomatic Expression Example v1"]["tmpls"]) == 1

    # 2 hub cards (both directions) + 1 fluency card.
    assert con.execute("SELECT COUNT(*) FROM cards").fetchone()[0] == 3
    guids = {g for (g,) in con.execute("SELECT guid FROM notes")}
    assert guids == {identity.pilot_hub_guid("es", 439),
                     identity.pilot_example_guid(2503)}
    # The rail + context clip made it into the note fields.
    flds = con.execute(
        "SELECT flds FROM notes WHERE guid = ?",
        (identity.pilot_hub_guid("es", 439),)).fetchone()[0]
    assert 'data-example-id="2503"' in flds
    assert "[sound:idh_ctx_41_deadbeef.mp3]" in flds


def test_production_build_routes_to_estate_decks_and_prod_guids(tmp_path: Path):
    hub, example, media = _pilot_fixture(tmp_path)
    out = tmp_path / "prod.apkg"
    hub_apkg.build_hub_apkg(out_path=out, hub_notes=[hub],
                            example_notes=[example], media_files=media,
                            pilot=False)
    with zipfile.ZipFile(out) as z:
        z.extract("collection.anki2", tmp_path / "y")
    con = sqlite3.connect(tmp_path / "y" / "collection.anki2")
    decks = json.loads(con.execute("SELECT decks FROM col").fetchone()[0])
    names = {d["name"] for d in decks.values()}
    assert "ES Spanish::1 Expressions::2 Expression Focus" in names
    assert "ES Spanish::1 Expressions::1 Fluency" in names
    guids = {g for (g,) in con.execute("SELECT guid FROM notes")}
    assert guids == {identity.hub_guid("es", 439), identity.example_guid(2503)}


# --- phase-5 manifest compiler (F3) ------------------------------------------

from idiomatic.hub import phase5  # noqa: E402


def test_normalize_join_estate_rules():
    assert phase5.normalize_join(
        "[sound:x.mp3] <b>Œuvre</b>&nbsp; “d’été” — fin…  ") == \
        "œuvre \"d'été\" - fin..."
    # NFKC + casefold, accents preserved, whitespace collapsed
    assert phase5.normalize_join("  Ça  VA bien ") == "ça va bien"
    assert phase5.normalize_join("ﬁn") == "fin"  # NFKC ligature


def test_pool_to_example_fmap_covers_all_seven_legacy_fields():
    fmap = phase5.pool_to_example_fmap()
    assert len(fmap) == 7
    ex = hub_apkg.EXAMPLE_FIELDS
    assert fmap[0] == ex.index("English")
    assert fmap[4] == ex.index("Expression")
    assert fmap[6] == ex.index("SourceHTML")
    # target ID/spare fields are never fmap targets — they are filled
    # after the supported conversion.
    for name in ("ExpressionId", "ExampleId", "Lang", "Image", "Origin",
                 "Extra1", "Extra2", "Extra3"):
        assert ex.index(name) not in fmap.values()


def _fake_inputs():
    c1 = {"groups": [
        {"group_id": "g-quar", "disposition": "quarantine",
         "language": "es", "survivor": {"normalized_surface": "más bien"},
         "members": [{"note_id": 901}, {"note_id": 902}]},
        {"group_id": "g-merge", "disposition": "same-sense-merge",
         "language": "es", "survivor": {"normalized_surface": "x"},
         "members": [{"note_id": 903}]},
    ]}
    extract = {"expressions": [
        {"expression_id": 439, "lang": "es", "idiom": "a primera hora",
         "explanation_en": "Early.", "examples": [
             {"example_id": 2503, "en_text": "He left first thing.",
              "target_text": "Salió a primera hora."},
             {"example_id": 2504, "en_text": "Second.",
              "target_text": "Segunda frase."}]},
    ]}

    def card(cid, nid, tl, en, verdict="fresh-trivial", reps=0,
             cardinality=1):
        return {"card_id": cid, "note_id": nid, "note_guid": f"g{cid}",
                "language": "es", "model_id": 1820114700,
                "normalized_target": phase5.normalize_join(tl),
                "normalized_english": phase5.normalize_join(en),
                "verdict": verdict, "reps": reps, "revlog_rows": reps,
                "last_review_id": None,
                "join_key_cardinality": cardinality,
                "join_key_peer_card_ids": [],
                "type": 0, "queue": 0, "due": 100, "ivl": 0, "factor": 0,
                "lapses": 0, "left": 0, "odue": 0, "odid": 0}

    c2 = {"source_sha256": "s" * 64, "cards": [
        card(11, 21, "Salió a primera hora.", "He left first thing.",
             verdict="adoptable", reps=8),
        # duplicate binding for the same example — fewer reps, must defer
        card(12, 22, "SALIÓ a primera hora.", "He left first thing."),
        card(13, 23, "Segunda frase.", "Second."),
        card(14, 24, "No such sentence.", "Unjoined."),          # unjoined
        card(15, 25, "Par x.", "Pair x.", cardinality=2),        # join-key
    ]}
    return c1, c2, extract


def test_compile_manifest_joins_and_exclusions():
    c1, c2, extract = _fake_inputs()
    manifest = phase5.compile_manifest(
        c1=c1, c2=c2, extract=extract,
        input_checksums={"C1": "a" * 64, "C2": "b" * 64,
                         "server_extract": "c" * 64})
    counts = manifest["counts"]
    assert counts["conversions"] == 2
    assert counts["conversions_adoptable"] == 1
    assert counts["adopted_reps"] == 8
    assert counts["hub_notes"] == 1
    assert counts["joinkey_quarantine_cards"] == 1
    assert counts["c1_quarantine_groups"] == 1
    # the most-invested card won the duplicate example binding
    by_card = {c["card_id"]: c for c in manifest["conversions"]}
    assert 11 in by_card and by_card[11]["example_id"] == 2503
    reasons = {g["card_id"]: g["reason"]
               for g in manifest["gaps"]["deferred_cards"]}
    assert reasons[12] == "duplicate-example-binding"
    assert reasons[14] == "unjoined-bilingual-pair"
    # hub row: server example set, deterministic production GUID
    hub = manifest["hubs"][0]
    assert hub["expression_id"] == 439
    assert [e["example_id"] for e in hub["examples"]] == [2503, 2504]
    assert hub["target_guid"] == identity.hub_guid("es", 439)
    # C1 quarantine members recorded, never converted
    assert manifest["quarantine"]["c1_groups"][0]["member_note_ids"] == \
        [901, 902]
    # manifest self-checksum round-trips
    assert phase5.manifest_content_sha256(manifest) == \
        manifest["content_sha256"]


def test_compile_manifest_is_deterministic_apart_from_timestamp():
    c1, c2, extract = _fake_inputs()
    kwargs = dict(c1=c1, c2=c2, extract=extract,
                  input_checksums={"C1": "a" * 64})
    m1 = phase5.compile_manifest(**kwargs)
    m2 = phase5.compile_manifest(**kwargs)
    for m in (m1, m2):
        m.pop("generated_at"), m.pop("content_sha256")
    assert m1 == m2


def test_expectations_gate():
    phase5.check_expectations({"a": "1" * 64}, {"a": "1" * 64})
    with pytest.raises(phase5.ExpectationError):
        phase5.check_expectations({"a": "1" * 64}, {"a": "2" * 64})
    with pytest.raises(phase5.ExpectationError):
        phase5.check_expectations({"a": "1" * 64},
                                  {"a": "1" * 64, "b": "3" * 64})


def test_hub_fields_and_example_fill_shapes():
    c1, c2, extract = _fake_inputs()
    manifest = phase5.compile_manifest(c1=c1, c2=c2, extract=extract,
                                       input_checksums={})
    conv = manifest["conversions"][0]
    fill = phase5.example_field_fill(conv)
    assert fill == {"ExpressionId": "439", "ExampleId": "2503",
                    "Lang": "es", "Origin": "initial"}
    assert f"example::{conv['example_id']}" in phase5.example_tags(conv)
    fields = phase5.hub_fields(manifest["hubs"][0], gloss_en="early",
                               sources_html="<div class='src'>x</div>")
    assert len(fields) == len(hub_apkg.HUB_FIELDS)
    assert fields[hub_apkg.HUB_FIELDS.index("GlossEN")] == "early"
    assert 'data-example-id="2504"' in \
        fields[hub_apkg.HUB_FIELDS.index("ExamplesHTML")]
    # spares + amendment audio stay blank in phase 5 (media enrichment
    # happens at release build, not collection migration)
    for name in ("ContextAudio", "ExpressionAudio", "Extra1", "Extra2",
                 "Extra3"):
        assert fields[hub_apkg.HUB_FIELDS.index(name)] == ""


def test_manifest_load_rejects_tampering(tmp_path: Path):
    c1, c2, extract = _fake_inputs()
    manifest = phase5.compile_manifest(c1=c1, c2=c2, extract=extract,
                                       input_checksums={})
    path = tmp_path / "m.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert phase5.load_manifest(path)["counts"]["conversions"] == 2
    manifest["conversions"][0]["example_id"] = 9999
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        phase5.load_manifest(path)


# --- durable-ID schema staging (ephemeral Postgres) --------------------------

_SCHEMA = Path(__file__).resolve().parent.parent / "db" / "schema.sql"

pg_available = shutil.which("initdb") and shutil.which("pg_ctl")


@pytest.fixture(scope="module")
def pg_dsn(tmp_path_factory):
    if not pg_available:
        pytest.skip("postgres binaries not installed")
    import tempfile

    root = tmp_path_factory.mktemp("pg")
    data = root / "data"
    sock = Path(tempfile.mkdtemp(prefix="idiomatic_hubpg_"))
    subprocess.run(
        ["initdb", "-D", str(data), "-U", "postgres", "-A", "trust",
         "--no-sync"],
        check=True, capture_output=True)
    subprocess.run(
        ["pg_ctl", "start", "-D", str(data), "-w", "-l", str(root / "pg.log"),
         "-o", f"-k {sock} -p 54331 -c listen_addresses='' -F"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        yield {"host": str(sock), "port": 54331, "user": "postgres",
               "database": "postgres"}
    finally:
        subprocess.run(["pg_ctl", "stop", "-D", str(data), "-m", "immediate"],
                       check=False, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        shutil.rmtree(sock, ignore_errors=True)


def test_hub_schema_staging_round_trip(pg_dsn):
    import asyncio

    import asyncpg

    async def run() -> None:
        conn = await asyncpg.connect(**pg_dsn)
        try:
            sql = _SCHEMA.read_text(encoding="utf-8")
            await conn.execute(sql)
            await conn.execute(sql)  # boot migration re-runs; must be a no-op

            # Seed a video -> expression -> two source occurrences -> examples.
            vid = await conn.fetchval(
                """INSERT INTO videos (youtube_id, lang, title)
                   VALUES ('ytA_123', 'es', 'Noticias de hoy')
                   RETURNING id""")
            vid2 = await conn.fetchval(
                """INSERT INTO videos (youtube_id, lang, title)
                   VALUES ('ytB_456', 'es', 'Más noticias')
                   RETURNING id""")
            expr = await conn.fetchval(
                """INSERT INTO expressions (lang, text, normalized)
                   VALUES ('es', 'a primera hora', 'a primera hora')
                   RETURNING id""")
            i1 = await conn.fetchval(
                """INSERT INTO expression_idioms (expression_id, video_id,
                       lang, idiom_text, english_gloss, source_phrase_target)
                   VALUES ($1, $2, 'es', 'a primera hora', 'first thing',
                           'Salió a primera hora de la mañana.')
                   RETURNING id""", expr, vid)
            i2 = await conn.fetchval(
                """INSERT INTO expression_idioms (expression_id, video_id,
                       lang, idiom_text, english_gloss)
                   VALUES ($1, $2, 'es', 'a primera hora', 'first thing')
                   RETURNING id""", expr, vid2)
            for idiom, ords in ((i1, (1, 2)), (i2, (1,))):
                for o in ords:
                    await conn.execute(
                        """INSERT INTO expression_examples
                               (idiom_id, ord, en_text, target_text)
                           VALUES ($1, $2, $3, $4)""",
                        idiom, o, f"en {o}", f"tl {o}")

            # Re-apply: the idempotent backfills must resolve everything.
            await conn.execute(sql)

            row = await conn.fetchrow(
                "SELECT sense_key, content_version, status FROM expressions"
                " WHERE id = $1", expr)
            assert row["sense_key"] == "legacy-primary"
            assert row["content_version"] == 1 and row["status"] == "active"

            s1 = await conn.fetchrow(
                "SELECT source_key, source_title, source_url, status"
                " FROM expression_idioms WHERE id = $1", i1)
            # phrase-hash recipe, mirrored by identity.source_key_youtube
            assert s1["source_key"] == identity.source_key_youtube(
                "ytA_123", source_phrase="Salió a primera hora de la mañana.")
            assert s1["source_title"] == "Noticias de hoy"
            assert s1["source_url"] == "https://www.youtube.com/watch?v=ytA_123"
            assert s1["status"] == "active"
            s2 = await conn.fetchrow(
                "SELECT source_key FROM expression_idioms WHERE id = $1", i2)
            assert s2["source_key"] == identity.source_key_youtube(
                "ytB_456", row_id=i2)

            exs = await conn.fetch(
                """SELECT id, expression_id, source_id, position, stable_key,
                          source_kind, status
                     FROM expression_examples ORDER BY idiom_id, ord""")
            assert all(e["expression_id"] == expr for e in exs)
            assert [e["source_id"] for e in exs] == [i1, i1, i2]
            # positions renumber uniquely across BOTH occurrences
            assert [e["position"] for e in exs] == [1, 2, 3]
            assert all(e["stable_key"] == f"legacy:{e['id']}" for e in exs)
            assert all(e["source_kind"] == "initial" for e in exs)
            assert all(e["status"] == "published" for e in exs)

            # Re-running the backfill must never reshuffle positions.
            await conn.execute(sql)
            again = [e["position"] for e in await conn.fetch(
                "SELECT position FROM expression_examples"
                " ORDER BY idiom_id, ord")]
            assert again == [1, 2, 3]

            # Canonical-rail uniqueness: same (expression, position) rejected
            # for a second canonical published row.
            with pytest.raises(asyncpg.UniqueViolationError):
                await conn.execute(
                    """INSERT INTO expression_examples
                           (idiom_id, ord, en_text, target_text,
                            expression_id, position, stable_key)
                       VALUES ($1, 4, 'dup', 'dup', $2, 1, 'legacy:dup')""",
                    i1, expr)
            with pytest.raises(asyncpg.UniqueViolationError):
                await conn.execute(
                    """INSERT INTO expression_examples
                           (idiom_id, ord, en_text, target_text, stable_key)
                       VALUES ($1, 5, 'x', 'x', $2)""",
                    i1, exs[0]["stable_key"])

            # Bindings: one active hub binding per (profile, expression).
            await conn.execute(
                """INSERT INTO anki_note_bindings
                       (profile_key, note_id, note_guid, card_kind,
                        expression_id)
                   VALUES ('syllabus', 1001, $1, 'hub', $2)""",
                identity.hub_guid("es", expr), expr)
            with pytest.raises(asyncpg.UniqueViolationError):
                await conn.execute(
                    """INSERT INTO anki_note_bindings
                           (profile_key, note_id, note_guid, card_kind,
                            expression_id)
                       VALUES ('syllabus', 1002, 'otherguid', 'hub', $1)""",
                    expr)
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    """INSERT INTO anki_note_bindings
                           (profile_key, note_id, note_guid, card_kind,
                            expression_id)
                       VALUES ('syllabus', 1003, 'g3', 'fluency', $1)""",
                    expr)  # fluency requires example_id

            # Release ledger: one in-flight build per (collection, lang);
            # finalized rows must carry verified artifact facts.
            await conn.execute(
                """INSERT INTO anki_releases (collection_key, lang, kind)
                   VALUES ('main', 'es', 'snapshot')""")
            with pytest.raises(asyncpg.UniqueViolationError):
                await conn.execute(
                    """INSERT INTO anki_releases (collection_key, lang, kind)
                       VALUES ('main', 'es', 'delta')""")
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    """UPDATE anki_releases SET status = 'finalized'
                       WHERE collection_key = 'main' AND lang = 'es'""")

            # A BOUND expression is protected from hard deletion (RESTRICT
            # is deliberate: bindings exist only post-migration, when purge
            # must retire by status instead).
            with pytest.raises(asyncpg.ForeignKeyViolationError):
                await conn.execute(
                    "DELETE FROM expressions WHERE id = $1", expr)
            await conn.execute(
                "DELETE FROM anki_note_bindings WHERE expression_id = $1",
                expr)

            # THE live-behavior invariant: the /admin/purge-video statement
            # sequence (delete examples, then idiom rows, then the orphaned
            # expression) must still pass with the staged columns present —
            # today's collection has no bindings, so nothing may block it.
            await conn.execute(
                "DELETE FROM expression_examples WHERE idiom_id = ANY($1::bigint[])",
                [i1, i2])
            await conn.execute(
                "DELETE FROM expression_idioms WHERE video_id = $1", vid)
            await conn.execute(
                "DELETE FROM expression_idioms WHERE video_id = $1", vid2)
            await conn.execute(
                "DELETE FROM expressions WHERE id = $1", expr)
            assert await conn.fetchval(
                "SELECT COUNT(*) FROM expressions") == 0
        finally:
            await conn.close()

    asyncio.run(run())
