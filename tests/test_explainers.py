"""Grammar-radio explainer tests: deterministic, with no network or DB."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sqlite3
import threading
from types import SimpleNamespace
import zipfile

import pytest

from idiomatic import gemini
from idiomatic.grammar.apkg import build_grammar_apkg
from idiomatic.grammar.explainers import (
    BETWEEN_SPEECH_MS,
    EXPLAINER_UNITS,
    EXPECTED_COUNTS,
    PAUSE_MS,
    ExplainerBuildError,
    ExplainerScript,
    ExplainerSourceError,
    FossilEvidence,
    RenderedExplainer,
    Segment,
    explainer_to_item,
    fossil_tags_for_item,
    load_explainers,
    parse_explainer,
    prebuilt_audio_map,
    render_explainer,
    route_segment,
)


_FROZEN_MODEL_ID = 1_820_130_001
_FROZEN_MODEL_NAME = "Idiomatic Grammar Drill v1"
_FROZEN_FIELDS = [
    "ItemId",
    "Lang",
    "Topic",
    "TenseLabel",
    "Symbol",
    "Sentence",
    "Answer",
    "SentenceFull",
    "GlossEn",
    "Why",
    "Extra1",
    "Extra2",
    "Extra3",
    "Extra4",
]


def _frontmatter(*, lang: str = "fr", slug: str = "fixture") -> str:
    return f"""---
lang: {lang}
slug: {slug}
title: "A title & a test"
takeaway: "Keep the raw <rule> in mind."
fossil_evidence:
  - ref: "docs/research/error-profiles/{lang}.md §1"
    count: 7
est_seconds: 30
---
"""


def _write_source(
    tmp_path: Path,
    body: str,
    *,
    lang: str = "fr",
    slug: str = "fixture",
    frontmatter: str | None = None,
) -> Path:
    path = tmp_path / f"{lang}_{slug}.md"
    source = frontmatter if frontmatter is not None else _frontmatter(lang=lang, slug=slug)
    path.write_text(source + "\n## SCRIPT\n\n" + body.strip() + "\n", encoding="utf-8")
    return path


def _script(
    tmp_path: Path,
    segments: tuple[Segment, ...],
    *,
    lang: str = "fr",
    slug: str = "radio-test",
    title: str = "Title & <topic>",
    takeaway: str = "Use <the rule> & remember it.",
) -> ExplainerScript:
    return ExplainerScript(
        path=tmp_path / f"{lang}_{slug}.md",
        lang=lang,
        slug=slug,
        title=title,
        takeaway=takeaway,
        fossil_evidence=(
            FossilEvidence("docs/research/error-profiles/test.md §1", 7),
            FossilEvidence("teacher-supplied audit", "~35 instances"),
        ),
        est_seconds=40,
        segments=segments,
        word_count=sum(len(segment.text.split()) for segment in segments),
    )


def _settings(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        data_dir=tmp_path,
        tts_provider="gemini",
        gemini_tts_model="fake-gemini-tts",
        elevenlabs_api_key=None,
        elevenlabs_model="fake-elevenlabs-tts",
    )


def test_canonical_corpus_contract_and_language_split():
    scripts = load_explainers()

    assert len(scripts) == 12
    assert Counter(script.lang for script in scripts) == EXPECTED_COUNTS
    identities = {(script.lang, script.slug) for script in scripts}
    assert len(identities) == len(scripts)

    for script in scripts:
        assert script.path.name == f"{script.lang}_{script.slug}.md"
        assert script.title and script.takeaway and script.fossil_evidence
        assert 300 <= script.word_count <= 450
        assert sum(segment.kind == "pause" for segment in script.segments) == 3
        assert all(
            segment.lang in {"en", script.lang}
            for segment in script.segments
            if segment.kind == "speech"
        )


def test_parser_routes_physical_lines_and_keeps_answer_label_english(tmp_path: Path):
    path = _write_source(
        tmp_path,
        """
English prose is spoken exactly once.

TL: Bonjour tout le monde.
[PAUSE]
Answer:
TL: Oui, exactement.
""",
    )

    parsed = parse_explainer(path, validate_contract=False)

    assert parsed.title == "A title & a test"
    assert parsed.takeaway == "Keep the raw <rule> in mind."
    assert parsed.fossil_evidence == (
        FossilEvidence("docs/research/error-profiles/fr.md §1", 7),
    )
    assert [
        (segment.kind, segment.text, segment.lang)
        for segment in parsed.segments
    ] == [
        ("speech", "English prose is spoken exactly once.", "en"),
        ("speech", "Bonjour tout le monde.", "fr"),
        ("pause", "", None),
        ("speech", "Answer:", "en"),
        ("speech", "Oui, exactement.", "fr"),
    ]


@pytest.mark.parametrize(
    "bad_line",
    ["TLL: Bonjour.", "Tl: Bonjour.", "EN: Read this.", "[WAIT]", "[PAUSE] trailing"],
)
def test_parser_rejects_unsupported_control_lines(tmp_path: Path, bad_line: str):
    path = _write_source(tmp_path, bad_line)

    with pytest.raises(ExplainerSourceError, match="unsupported control"):
        parse_explainer(path, validate_contract=False)


def test_contract_rejects_missing_immediate_answer_even_if_later_tl_exists(
    tmp_path: Path,
):
    filler = " ".join(["word"] * 310)
    path = _write_source(
        tmp_path,
        f"""{filler}
[PAUSE]
Self-test two includes a target prompt.
TL: Une invite, pas la réponse précédente.
[PAUSE]
TL: Deuxième réponse.
[PAUSE]
TL: Troisième réponse.
""",
    )

    with pytest.raises(ExplainerSourceError, match="must be followed by TL: answer"):
        parse_explainer(path)


def test_parser_rejects_missing_takeaway(tmp_path: Path):
    frontmatter = """---
lang: fr
slug: fixture
title: "Title"
fossil_evidence:
  - ref: "docs/research/error-profiles/fr.md §1"
    count: 1
est_seconds: 30
---
"""
    path = _write_source(tmp_path, "English.", frontmatter=frontmatter)

    with pytest.raises(ExplainerSourceError, match="missing frontmatter fields: takeaway"):
        parse_explainer(path, validate_contract=False)


@pytest.mark.parametrize(
    ("lang", "expected_voice"),
    [
        ("fr", "Aoede"),
        ("pt", "Orus"),
        ("es", "Fenrir"),
        ("de", "Charon"),
    ],
)
def test_segment_voice_routing_table(lang: str, expected_voice: str):
    english = route_segment(Segment("speech", "Listen.", "en", 1), lang)
    target = route_segment(Segment("speech", "Target.", lang, 2), lang)
    pause = route_segment(Segment("pause", "", None, 3), lang)

    assert english is not None and (english.lang, english.voice) == ("en", "Kore")
    assert target is not None and (target.lang, target.voice) == (lang, expected_voice)
    assert pause is None


def test_segment_voice_routing_rejects_language_mismatch():
    with pytest.raises(ValueError, match="does not match"):
        route_segment(Segment("speech", "Hola.", "es", 1), "fr")


def test_grammar_job_claim_is_synchronous_and_cross_mode():
    from idiomatic.grammar import service

    saved = service.get_state()
    try:
        service._state.clear()
        service._state["running"] = False
        assert service.claim_grammar_job("fr", "generation") is True
        assert service.get_state()["mode"] == "generation"
        assert service.claim_explainer_build("pt") is False
        service._state["running"] = False
        assert service.claim_explainer_build("pt") is True
        assert service.get_state()["mode"] == "explainers"
    finally:
        service._state.clear()
        service._state.update(saved)


@pytest.mark.parametrize(
    ("lang", "topic", "cluster"),
    [
        ("fr", "fr_ecoute", "0 Écoute"),
        ("pt", "pt_escuta", "0 Escuta"),
        ("es", "es_escucha", "0 Escucha"),
        ("de", "de_hoeren", "0 Hören"),
    ],
)
def test_card_mapping_is_raw_verified_and_localized(
    tmp_path: Path, lang: str, topic: str, cluster: str,
):
    script = _script(tmp_path, (), lang=lang, slug="lesson")
    media = f"idg_explainer_{lang}_lesson_0123456789ab.mp3"
    rendered = RenderedExplainer(script, tmp_path / media, media, 37.1254, ())

    item = explainer_to_item(rendered)

    assert EXPLAINER_UNITS[lang].cluster == cluster
    assert item == {
        "lang": lang,
        "topic": topic,
        "fmt": "explainer",
        "infinitive": None,
        "mood": None,
        "tense": None,
        "person": None,
        "sentence": "Title & <topic>",
        "answer": "Use <the rule> & remember it.",
        "gloss_en": "",
        "why_en": (
            "Fossil evidence: 7 (docs/research/error-profiles/test.md §1); "
            "~35 instances (teacher-supplied audit)"
        ),
        "status": "verified",
        "meta": {
            "slug": "lesson",
            "audio_filename": media,
            "duration_seconds": 37.125,
            "renderer_revision": "grammar-radio-v1-pause1500-gap200",
        },
    }


@pytest.mark.asyncio
async def test_renderer_injection_order_dedup_idempotence_and_content_hash(tmp_path: Path):
    segments = (
        Segment("speech", "Intro.", "en", 1),
        Segment("speech", "Answer:", "en", 2),
        Segment("speech", "Answer:", "en", 3),
        Segment("pause", "", None, 4),
        Segment("speech", "Bonjour.", "fr", 5),
        Segment("pause", "", None, 6),
        Segment("speech", "Prompt.", "en", 7),
        Segment("speech", "Réponse.", "fr", 8),
    )
    script = _script(tmp_path, segments)
    stage = tmp_path / "stage"
    synth_calls: list[tuple[str, str, str]] = []
    silence_calls: list[int] = []
    concat_sequences: list[list[str]] = []
    worker_threads: list[tuple[str, int]] = []
    event_loop_thread = threading.get_ident()

    async def fake_synthesize(
        text: str, *, voice: str, out: Path, lang: str = "en",
    ) -> None:
        synth_calls.append((text, voice, lang))
        out.write_text(f"T:{lang}:{voice}:{text}", encoding="utf-8")

    def fake_silence(root: Path, ms: int) -> Path:
        worker_threads.append((f"silence-{ms}", threading.get_ident()))
        silence_calls.append(ms)
        path = root / f"silence-{ms}.mp3"
        path.write_text(f"S:{ms}", encoding="utf-8")
        return path

    def fake_concat(pieces: list[Path], out: Path) -> Path:
        worker_threads.append(("concat", threading.get_ident()))
        sequence = [piece.read_text(encoding="utf-8") for piece in pieces]
        concat_sequences.append(sequence)
        out.write_text("stitched", encoding="utf-8")
        return out

    def fake_probe(path: Path) -> float:
        worker_threads.append(("probe", threading.get_ident()))
        assert path.read_text(encoding="utf-8") == "stitched"
        return 40.0

    kwargs = {
        "stage_dir": stage,
        "settings": _settings(tmp_path),
        "synthesize_fn": fake_synthesize,
        "silence_fn": fake_silence,
        "concat_fn": fake_concat,
        "probe_fn": fake_probe,
    }
    first = await render_explainer(script, **kwargs)

    assert PAUSE_MS == 1_500
    assert BETWEEN_SPEECH_MS == 200
    assert Counter(text for text, _voice, _lang in synth_calls) == Counter(
        {"Intro.": 1, "Answer:": 1, "Bonjour.": 1, "Prompt.": 1, "Réponse.": 1}
    )
    assert silence_calls == [1_500, 200]
    assert concat_sequences == [[
        "T:en:Kore:Intro.",
        "S:200",
        "T:en:Kore:Answer:",
        "S:200",
        "T:en:Kore:Answer:",
        "S:1500",
        "T:fr:Aoede:Bonjour.",
        "S:1500",
        "T:en:Kore:Prompt.",
        "S:200",
        "T:fr:Aoede:Réponse.",
    ]]
    assert first.constituent_keys.count("pause:1500") == 2
    assert first.constituent_keys.count("gap:200") == 3
    assert first.path.exists()
    assert first.media_filename.startswith("idg_explainer_fr_radio-test_")
    assert first.media_filename.endswith(".mp3")
    assert all(thread_id != event_loop_thread for _label, thread_id in worker_threads)

    # Unchanged source reuses every speech clip and the final stitched file.
    call_count = len(synth_calls)
    concat_count = len(concat_sequences)
    second = await render_explainer(script, **kwargs)
    assert len(synth_calls) == call_count
    assert len(concat_sequences) == concat_count
    assert second.media_filename == first.media_filename
    assert second.constituent_keys == first.constituent_keys

    # Editing one physical line invalidates only that clip, and changes the
    # content-addressed final media name while leaving the old revision intact.
    changed_segments = (replace(segments[0], text="Changed intro."), *segments[1:])
    changed = replace(script, segments=changed_segments)
    third = await render_explainer(changed, **kwargs)
    assert synth_calls[call_count:] == [("Changed intro.", "Kore", "en")]
    assert third.media_filename != first.media_filename
    assert first.path.exists() and third.path.exists()


@pytest.mark.asyncio
async def test_renderer_rejects_silence_marked_tts_and_does_not_publish(tmp_path: Path):
    script = _script(
        tmp_path,
        (Segment("speech", "This request degrades.", "en", 1),),
        slug="degraded",
    )
    concat_called = False

    async def degraded_synthesize(
        text: str, *, voice: str, out: Path, lang: str = "en",
    ) -> None:
        assert (text, voice, lang) == ("This request degrades.", "Kore", "en")
        out.write_bytes(b"placeholder audio")
        gemini.silence_marker(out).touch()

    def forbidden_concat(_pieces: list[Path], _out: Path) -> Path:
        nonlocal concat_called
        concat_called = True
        raise AssertionError("a degraded lesson must not be stitched")

    with pytest.raises(ExplainerBuildError, match="incomplete TTS segments"):
        await render_explainer(
            script,
            stage_dir=tmp_path / "stage",
            settings=_settings(tmp_path),
            synthesize_fn=degraded_synthesize,
            concat_fn=forbidden_concat,
            probe_fn=lambda _path: 1.0,
        )

    assert concat_called is False
    assert not list((tmp_path / "stage").glob("idg_explainer_*.mp3"))
    assert not list((tmp_path / "stage").glob(".*.building.mp3"))


def test_prebuilt_audio_map_accepts_only_safe_complete_explainer_media(tmp_path: Path):
    audio_dir = tmp_path / "grammar" / "fr"
    explainers_dir = audio_dir / "explainers"
    explainers_dir.mkdir(parents=True)
    valid = "idg_explainer_fr_prep-lieux_0123456789ab.mp3"
    empty = "idg_explainer_fr_empty_0123456789ab.mp3"
    (explainers_dir / valid).write_bytes(b"complete audio")
    (explainers_dir / empty).touch()
    items = [
        {"id": 1, "lang": "fr", "fmt": "explainer",
         "meta": {"slug": "prep-lieux", "audio_filename": valid}},
        {"id": "2", "lang": "fr", "fmt": "explainer",
         "meta": json.dumps({"slug": "prep-lieux", "audio_filename": valid})},
        {"id": 3, "lang": "fr", "fmt": "explainer",
         "meta": {"slug": "prep-lieux", "audio_filename": "../" + valid}},
        {"id": 4, "lang": "fr", "fmt": "explainer",
         "meta": {"slug": "wrong",
                  "audio_filename": "idg_explainer_es_wrong_0123456789ab.mp3"}},
        {"id": 5, "lang": "fr", "fmt": "explainer",
         "meta": {"slug": "empty", "audio_filename": empty}},
        {"id": 6, "lang": "fr", "fmt": "explainer",
         "meta": {"slug": "missing",
                  "audio_filename": "idg_explainer_fr_missing_0123456789ab.mp3"}},
        {"id": 7, "lang": "fr", "fmt": "f3",
         "meta": {"slug": "prep-lieux", "audio_filename": valid}},
        {"id": 8, "lang": "fr", "fmt": "explainer",
         "meta": {"slug": "another-lesson", "audio_filename": valid}},
    ]

    assert prebuilt_audio_map(items, audio_dir) == {
        1: f"explainers/{valid}",
        2: f"explainers/{valid}",
    }


@pytest.mark.parametrize(
    ("lang", "category", "slug"),
    [
        ("fr", "prep_place", "prep-lieux"),
        ("pt", "fut_subjunctive", "futuro-subjuntivo"),
        ("es", "light_verb", "light-verbs"),
        ("de", "gender+adj_endings", "adjektivendungen"),
    ],
)
def test_f3_fossil_tag_mapping(lang: str, category: str, slug: str):
    item = {"fmt": "f3", "lang": lang, "gloss_en": category}
    assert fossil_tags_for_item(item) == (f"idiomatic-fossil::{lang}::{slug}",)
    assert fossil_tags_for_item({**item, "fmt": "cloze"}) == ()
    assert fossil_tags_for_item({**item, "gloss_en": "unmapped"}) == ()


def test_f3_fossil_mapping_uses_registry_meta_not_presentation_gloss():
    item = {
        "fmt": "f3",
        "lang": "es",
        "gloss_en": "free learner-facing gloss",
        "meta": {
            "source_category": "light_verb_collocation",
            "source_unit_hint": "es_light_verbs",
        },
    }
    assert fossil_tags_for_item(item) == (
        "idiomatic-fossil::es::light-verbs",
    )


def test_explainer_apkg_keeps_frozen_model_subdeck_media_guid_and_tags(tmp_path: Path):
    audio_dir = tmp_path / "media"
    explainers_dir = audio_dir / "explainers"
    explainers_dir.mkdir(parents=True)
    media_name = "idg_explainer_fr_prep-lieux_0123456789ab.mp3"
    (explainers_dir / media_name).write_bytes(b"fake mp3 bytes")
    explainer = {
        "id": 101,
        "lang": "fr",
        "topic": "fr_ecoute",
        "fmt": "explainer",
        "infinitive": None,
        "sentence": "Cities & <countries>",
        "answer": "Use à & choose <country> forms.",
        "gloss_en": "",
        "why_en": "Fossil evidence: 56 < 100 & attested.",
        "meta": {"slug": "prep-lieux", "audio_filename": media_name},
    }
    f3 = {
        "id": 102,
        "lang": "fr",
        "topic": "fr_mes_erreurs",
        "fmt": "f3",
        "infinitive": None,
        "sentence": "en Berlin",
        "answer": "à Berlin",
        "gloss_en": "prep_place",
        "why_en": "Cities take à.",
    }
    audio = prebuilt_audio_map([explainer, f3], audio_dir)
    out = tmp_path / "grammar.apkg"

    count = build_grammar_apkg(
        out_path=out,
        lang="fr",
        items=[explainer, f3],
        topic_labels={"fr_mes_erreurs": ("Corrige : ce que j'ai dit", "⚠")},
        topic_clusters={"fr_mes_erreurs": "9 Mes erreurs"},
        audio=audio,
        audio_dir=audio_dir,
    )

    assert count == 2
    with zipfile.ZipFile(out) as package:
        media_map = json.loads(package.read("media"))
        unpacked = tmp_path / "unpacked"
        package.extract("collection.anki2", unpacked)
    assert list(media_map.values()) == [media_name]
    assert all("/" not in packaged_name for packaged_name in media_map.values())

    with sqlite3.connect(unpacked / "collection.anki2") as con:
        models = json.loads(con.execute("SELECT models FROM col").fetchone()[0])
        decks = json.loads(con.execute("SELECT decks FROM col").fetchone()[0])
        note_rows = con.execute("SELECT id, guid, flds, tags FROM notes").fetchall()
        card_decks = dict(con.execute("SELECT nid, did FROM cards"))

    assert set(models) == {str(_FROZEN_MODEL_ID)}
    model = models[str(_FROZEN_MODEL_ID)]
    assert model["name"] == _FROZEN_MODEL_NAME
    assert [field["name"] for field in model["flds"]] == _FROZEN_FIELDS
    assert len(model["tmpls"]) == 1
    assert "{{Extra1}}" not in model["tmpls"][0]["qfmt"]
    assert "{{Extra1}}" in model["tmpls"][0]["afmt"]

    notes = {}
    for note_id, guid, field_blob, tags_blob in note_rows:
        fields = dict(zip(_FROZEN_FIELDS, field_blob.split("\x1f"), strict=True))
        notes[fields["ItemId"]] = {
            "id": note_id,
            "guid": guid,
            "fields": fields,
            "tags": set(tags_blob.split()),
        }

    radio = notes["explainer:fr:prep-lieux"]
    assert radio["guid"] == hashlib.sha1(
        b"idiomatic-grammar-explainer::fr::prep-lieux"
    ).hexdigest()[:16]
    assert radio["fields"] == {
        "ItemId": "explainer:fr:prep-lieux",
        "Lang": "fr",
        "Topic": "fr_ecoute",
        "TenseLabel": "Grammar radio",
        "Symbol": "🎧",
        "Sentence": "Cities &amp; &lt;countries&gt;",
        "Answer": "Use à &amp; choose &lt;country&gt; forms.",
        "SentenceFull": "Cities &amp; &lt;countries&gt;",
        "GlossEn": "",
        "Why": "Fossil evidence: 56 &lt; 100 &amp; attested.",
        "Extra1": f"[sound:{media_name}]",
        "Extra2": "",
        "Extra3": "",
        "Extra4": "",
    }
    assert radio["fields"]["Extra1"].count("[sound:") == 1
    assert radio["tags"] == {
        "idiomatic-grammar",
        "grammar-radio",
        "fr_explainers",
        "fr_ecoute",
        "idiomatic-fossil::fr::prep-lieux",
    }
    assert notes["102"]["tags"] == {
        "idiomatic-grammar",
        "fr_mes_erreurs",
        "idiomatic-fossil::fr::prep-lieux",
    }

    deck_names = {int(deck_id): row["name"] for deck_id, row in decks.items()}
    assert deck_names[card_decks[radio["id"]]] == "Idiomatic Grammar FR::0 Écoute"
    assert (
        deck_names[card_decks[notes["102"]["id"]]]
        == "Idiomatic Grammar FR::9 Mes erreurs"
    )
