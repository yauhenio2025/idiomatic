"""Grammar Course tests: deterministic, with no network or DB."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import zipfile
from pathlib import Path

import pytest

from idiomatic.grammar import course
from idiomatic.grammar.exercises2 import MODEL_ID as X2_MODEL_ID
from idiomatic.grammar.podcast_cards import MODEL_ID as PODCAST_MODEL_ID


_FROZEN_LESSON_FIELDS = [
    "LessonId",
    "Unit",
    "Seq",
    "Lang",
    "FrontHTML",
    "BackHTML",
    "FrontAudio",
    "BackAudio",
    "FrontImage",
    "BackImage",
    "Extra1",
    "Extra2",
    "Extra3",
    "Extra4",
]

_FROZEN_EXERCISE_FIELDS = [
    "ItemId",
    "Lang",
    "Unit",
    "Block",
    "Instruction",
    "PromptHTML",
    "SolutionHTML",
    "AltsHTML",
    "SourceRef",
    "HammerRefs",
    "Provenance",
    "SolutionAudio",
    "Extra1",
    "Extra2",
    "Extra3",
]

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _frontmatter(*, series: str = "grammar-course-lesson", lang: str = "de",
                 unit: str = "kasus") -> str:
    return f"""---
series: {series}
lang: {lang}
unit: {unit}
title: "Fixture unit"
unit_label: "Kasus (cases)"
---
"""


def _card(seq: int, *, front_extra: str = "", refs: str = "2.1") -> str:
    return f"""[CARD]
TITLE: Front {seq}
REF: {refs}
Narrate front {seq}.
TL: Der Zug war nicht pünktlich.
{front_extra}[SIDE]
TITLE: Back {seq}
REF: {refs}
Narrate back {seq}.
SHOW: Back note {seq}
TL-: Der Zug war nicht pünktlich.
"""


def _lesson_source(n_cards: int = 8, **kwargs: str) -> str:
    cards = "".join(_card(seq) for seq in range(1, n_cards + 1))
    return _frontmatter(**kwargs) + "\n## SCRIPT\n" + cards


def _write_lesson(tmp_path: Path, source: str, *, lang: str = "de",
                  unit: str = "kasus") -> Path:
    path = tmp_path / f"{lang}_{unit}.md"
    path.write_text(source, encoding="utf-8")
    return path


def _exercise(item_id: str, **overrides: object) -> dict:
    raw: dict = {
        "id": item_id,
        "instruction": "Add the missing endings.",
        "prompt": "Wir sprachen mit Maria Simon, d___ Filmschauspielerin.",
        "solution_html":
            "Wir sprachen mit Maria Simon, <mark>der</mark> Filmschauspielerin.",
        "alternatives": [],
        "hammer_refs": ["2.6"],
        "source_ref": "PGG Kap. 2, Üb. 14, Nr. 1",
        "provenance": "book-verbatim",
    }
    raw.update(overrides)
    return raw


def _exercises_payload(blocks: dict[int, list[dict]], *, lang: str = "de",
                       unit: str = "kasus") -> dict:
    return {
        "lang": lang,
        "unit": unit,
        "blocks": [
            {"block": block, "exercises": items}
            for block, items in blocks.items()
        ],
    }


def _write_exercises(tmp_path: Path, payload: dict, *, lang: str = "de",
                     unit: str = "kasus") -> Path:
    path = tmp_path / f"{lang}_{unit}.exercises.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Frozen shape
# ---------------------------------------------------------------------------


class TestFrozenShape:
    def test_lesson_model_identity(self) -> None:
        assert course.LESSON_MODEL_ID == 1_820_190_001
        assert course.LESSON_FIELDS == _FROZEN_LESSON_FIELDS
        model = course.make_lesson_model()
        assert [field["name"] for field in model.fields] == _FROZEN_LESSON_FIELDS
        assert len(model.templates) == 1

    def test_exercise_model_identity(self) -> None:
        assert course.EXERCISE_MODEL_ID == 1_820_190_002
        assert course.EXERCISE_FIELDS == _FROZEN_EXERCISE_FIELDS
        model = course.make_exercise_model()
        assert [field["name"] for field in model.fields] == _FROZEN_EXERCISE_FIELDS
        assert len(model.templates) == 1

    def test_model_ids_disjoint_from_existing_ranges(self) -> None:
        taken = {PODCAST_MODEL_ID, X2_MODEL_ID}
        assert course.LESSON_MODEL_ID not in taken
        assert course.EXERCISE_MODEL_ID not in taken
        assert course.LESSON_MODEL_ID != course.EXERCISE_MODEL_ID

    def test_deck_id_range_disjoint_from_pool_and_exercises(self) -> None:
        deck_id = course._deck_id("Any::Deck")
        assert 1_930_000_000 <= deck_id < 1_990_000_000


# ---------------------------------------------------------------------------
# GUID discipline
# ---------------------------------------------------------------------------


class TestGuids:
    def test_lesson_guid_stable_and_distinct(self) -> None:
        assert course.lesson_guid("de", "kasus", 1) == \
            course.lesson_guid("de", "kasus", 1)
        assert course.lesson_guid("de", "kasus", 1) != \
            course.lesson_guid("de", "kasus", 2)
        assert course.lesson_guid("de", "kasus", 1) != \
            course.lesson_guid("it", "kasus", 1)

    def test_exercise_guid_distinct_namespace(self) -> None:
        assert course.exercise_guid("de", "kasus", "1") != \
            course.lesson_guid("de", "kasus", 1)
        assert course.exercise_guid("de", "kasus", "a") != \
            course.exercise_guid("de", "kasus", "b")


# ---------------------------------------------------------------------------
# Lesson parsing
# ---------------------------------------------------------------------------


class TestLessonParsing:
    def test_parses_valid_lesson(self, tmp_path: Path) -> None:
        lesson = course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(10))
        )
        assert lesson.lang == "de"
        assert lesson.unit == "kasus"
        assert lesson.unit_label == "Kasus (cases)"
        assert len(lesson.cards) == 10
        first = lesson.cards[0]
        assert first.front.refs == ("2.1",)
        assert first.front.display[0].kind == "tl"
        assert any(seg.kind == "speech" for seg in first.front.segments)

    def test_rejects_wrong_series(self, tmp_path: Path) -> None:
        with pytest.raises(course.CourseSourceError, match="series"):
            course.parse_course_lesson(_write_lesson(
                tmp_path, _lesson_source(8, series="grammar-walk-cards")
            ))

    def test_rejects_card_count_out_of_bounds(self, tmp_path: Path) -> None:
        for n_cards in (7, 13):
            with pytest.raises(course.CourseSourceError, match="8-12"):
                course.parse_course_lesson(_write_lesson(
                    tmp_path, _lesson_source(n_cards)
                ))

    def test_requires_ref_per_side(self, tmp_path: Path) -> None:
        source = _lesson_source(8).replace("REF: 2.1\nNarrate front 1.",
                                           "Narrate front 1.", 1)
        with pytest.raises(course.CourseSourceError, match="REF:"):
            course.parse_course_lesson(_write_lesson(tmp_path, source))

    def test_rejects_bad_ref_id(self, tmp_path: Path) -> None:
        source = _lesson_source(8).replace("REF: 2.1", "REF: not-a-ref", 1)
        with pytest.raises(course.CourseSourceError, match="§-id"):
            course.parse_course_lesson(_write_lesson(tmp_path, source))

    def test_accepts_chapter_refs_and_lettered_subsections(
        self, tmp_path: Path
    ) -> None:
        source = _lesson_source(8).replace(
            "REF: 2.1", "REF: 2.2.2a, Ch. 18", 1
        )
        lesson = course.parse_course_lesson(_write_lesson(tmp_path, source))
        assert lesson.cards[0].front.refs == ("2.2.2a", "Ch. 18")

    def test_svg_sidecar_must_exist(self, tmp_path: Path) -> None:
        source = _lesson_source(8).replace(
            "REF: 2.1\nNarrate front 1.",
            "REF: 2.1\nSVG: missing.svg\nNarrate front 1.", 1,
        )
        with pytest.raises(course.CourseSourceError, match="does not exist"):
            course.parse_course_lesson(_write_lesson(tmp_path, source))

    def test_visual_is_optional(self, tmp_path: Path) -> None:
        lesson = course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(8))
        )
        assert lesson.cards[0].front.svg_file is None
        assert course._visual_field(lesson, lesson.cards[0].front) == ""

    def test_filename_must_match_lang_unit(self, tmp_path: Path) -> None:
        path = tmp_path / "de_other.md"
        path.write_text(_lesson_source(8), encoding="utf-8")
        with pytest.raises(course.CourseSourceError, match="filename"):
            course.parse_course_lesson(path)

    def test_side_html_carries_sources_footer(self, tmp_path: Path) -> None:
        lesson = course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(8))
        )
        html_out = course.side_html(lesson.cards[0].front)
        assert "cl-refs" in html_out
        assert "Hammer §2.1" in html_out


# ---------------------------------------------------------------------------
# Exercise parsing + hygiene gate
# ---------------------------------------------------------------------------


class TestExerciseParsing:
    def test_parses_valid_file(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise("c02-e14-i01")]}
        ))
        exercises = course.parse_exercises_file(path)
        assert len(exercises) == 1
        assert exercises[0].block == 1
        assert exercises[0].hammer_refs == ("2.6",)

    def test_rejects_solution_without_mark(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise("x1", solution_html="Kein Highlight hier.")]}
        ))
        with pytest.raises(course.CourseSourceError, match="mark"):
            course.parse_exercises_file(path)

    def test_rejects_solution_with_blank_placeholder(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise(
                "x1",
                solution_html="Wir sprachen mit d___ <mark>der</mark> Frau.",
            )]}
        ))
        with pytest.raises(course.CourseSourceError, match="placeholder"):
            course.parse_exercises_file(path)

    def test_rejects_markup_beyond_mark(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise(
                "x1",
                solution_html='<script>x</script> <mark>der</mark> Frau.',
            )]}
        ))
        with pytest.raises(course.CourseSourceError, match="only <mark>"):
            course.parse_exercises_file(path)

    def test_rejects_unknown_provenance(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise("x1", provenance="llm-freestyle")]}
        ))
        with pytest.raises(course.CourseSourceError, match="provenance"):
            course.parse_exercises_file(path)

    def test_rejects_duplicate_ids_across_blocks(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise("x1")], 2: [_exercise("x1")]}
        ))
        with pytest.raises(course.CourseSourceError, match="duplicate"):
            course.parse_exercises_file(path)

    def test_rejects_missing_hammer_refs(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise("x1", hammer_refs=[])]}
        ))
        with pytest.raises(course.CourseSourceError, match="hammer_refs"):
            course.parse_exercises_file(path)

    def test_filename_must_encode_lang_and_unit(self, tmp_path: Path) -> None:
        path = tmp_path / "kasus.json"
        path.write_text("{}", encoding="utf-8")
        with pytest.raises(course.CourseSourceError, match="filename"):
            course.parse_exercises_file(path)

    def test_solution_html_escapes_outside_marks(self) -> None:
        raw = _exercise("x1", solution_html="A & B <mark>c < d</mark> e")
        parsed = course._parse_exercise(
            Path("de_kasus.exercises.json"), "de", "kasus", 1, raw
        )
        rendered = course.exercise_solution_html(parsed)
        assert "&amp;" in rendered
        assert "<mark>c &lt; d</mark>" in rendered


# ---------------------------------------------------------------------------
# Interleave arithmetic
# ---------------------------------------------------------------------------


class TestInterleave:
    def _lesson(self, tmp_path: Path, n_cards: int = 8) -> course.CourseLesson:
        return course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(n_cards))
        )

    def _exercises(self, tmp_path: Path,
                   blocks: dict[int, int]) -> list[course.CourseExercise]:
        payload = _exercises_payload({
            block: [_exercise(f"b{block}i{i}") for i in range(count)]
            for block, count in blocks.items()
        })
        return course.parse_exercises_file(_write_exercises(tmp_path, payload))

    def test_positions_follow_card_then_block(self, tmp_path: Path) -> None:
        lesson = self._lesson(tmp_path)
        exercises = self._exercises(tmp_path, {1: 3, 2: 2})
        plan = course.interleave_plan(lesson, exercises)
        kinds = [(kind, key) for kind, key, _due in plan[:8]]
        assert kinds == [
            ("lesson", "1"),
            ("exercise", "b1i0"), ("exercise", "b1i1"), ("exercise", "b1i2"),
            ("lesson", "2"),
            ("exercise", "b2i0"), ("exercise", "b2i1"),
            ("lesson", "3"),
        ]

    def test_dues_are_contiguous_unique_one_based(self, tmp_path: Path) -> None:
        lesson = self._lesson(tmp_path)
        exercises = self._exercises(tmp_path, {1: 5, 3: 4, 8: 2})
        plan = course.interleave_plan(lesson, exercises)
        dues = [due for _kind, _key, due in plan]
        assert dues == list(range(1, len(plan) + 1))
        assert len(plan) == 8 + 11

    def test_empty_blocks_let_cards_run_consecutively(
        self, tmp_path: Path
    ) -> None:
        lesson = self._lesson(tmp_path)
        plan = course.interleave_plan(lesson, [])
        assert [kind for kind, _key, _due in plan] == ["lesson"] * 8

    def test_block_beyond_card_count_is_an_error(self, tmp_path: Path) -> None:
        lesson = self._lesson(tmp_path)
        exercises = self._exercises(tmp_path, {9: 1})
        with pytest.raises(ValueError, match="block"):
            course.interleave_plan(lesson, exercises)

    def test_unit_mismatch_is_an_error(self, tmp_path: Path) -> None:
        lesson = self._lesson(tmp_path)
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        payload = _exercises_payload(
            {1: [_exercise("x1")]}, unit="plurals"
        )
        exercises = course.parse_exercises_file(
            _write_exercises(other_dir, payload, unit="plurals")
        )
        with pytest.raises(ValueError, match="belongs to"):
            course.interleave_plan(lesson, exercises)


# ---------------------------------------------------------------------------
# Deck naming
# ---------------------------------------------------------------------------


class TestDeckNames:
    def test_production_names_compose_from_estate_root(self) -> None:
        lesson_deck, exercise_deck = course.course_deck_names(
            "de", "Kasus (cases)"
        )
        assert lesson_deck == "DE German::2 Grammar::Kasus (cases)::1 Lesson"
        assert exercise_deck == "DE German::2 Grammar::Kasus (cases)::2 Exercises"

    def test_pilot_root_override(self) -> None:
        lesson_deck, exercise_deck = course.course_deck_names(
            "de", "Kasus (cases)",
            root_override="ZZ Grammar Course Pilot (disposable)",
        )
        assert lesson_deck == "ZZ Grammar Course Pilot (disposable)::1 Lesson"
        assert exercise_deck == \
            "ZZ Grammar Course Pilot (disposable)::2 Exercises"


# ---------------------------------------------------------------------------
# APKG build
# ---------------------------------------------------------------------------


def _open_collection(apkg_path: Path, tmp_path: Path) -> sqlite3.Connection:
    extract = tmp_path / "apkg_extract"
    extract.mkdir(exist_ok=True)
    with zipfile.ZipFile(apkg_path) as bundle:
        bundle.extractall(extract)
    return sqlite3.connect(extract / "collection.anki2")


class TestBuild:
    def _build(self, tmp_path: Path, blocks: dict[int, int] | None = None):
        lesson = course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(8))
        )
        payload = _exercises_payload({
            block: [_exercise(f"b{block}i{i}") for i in range(count)]
            for block, count in (blocks or {1: 3, 2: 2}).items()
        })
        exercises = course.parse_exercises_file(
            _write_exercises(tmp_path, payload)
        )
        out = tmp_path / "unit.apkg"
        result = course.build_course_apkg(
            out_path=out,
            lesson=lesson,
            exercises=exercises,
            root_override="ZZ Grammar Course Pilot (disposable)",
        )
        return out, result

    def test_build_counts_and_audio_pending(self, tmp_path: Path) -> None:
        out, result = self._build(tmp_path)
        assert out.exists()
        assert result["notes"] == 8 + 5
        assert result["lesson_cards"] == 8
        assert result["exercises"] == 5
        # 8 fronts + 8 backs + 5 solutions, all pending in the fixture build
        assert result["audio_pending"] == 21

    def test_due_positions_encode_interleave(self, tmp_path: Path) -> None:
        out, _result = self._build(tmp_path)
        conn = _open_collection(out, tmp_path)
        rows = conn.execute(
            "SELECT c.due, n.mid, n.flds FROM cards c JOIN notes n "
            "ON c.nid = n.id ORDER BY c.due"
        ).fetchall()
        dues = [row[0] for row in rows]
        assert dues == list(range(1, 14))
        # Row 1 is lesson card 1; rows 2-4 its block; row 5 lesson card 2.
        assert rows[0][1] == course.LESSON_MODEL_ID
        assert rows[1][1] == course.EXERCISE_MODEL_ID
        assert rows[4][1] == course.LESSON_MODEL_ID
        conn.close()

    def test_two_subdecks_and_tags(self, tmp_path: Path) -> None:
        out, _result = self._build(tmp_path)
        conn = _open_collection(out, tmp_path)
        decks = json.loads(
            conn.execute("SELECT decks FROM col").fetchone()[0]
        )
        names = {deck["name"] for deck in decks.values()}
        assert "ZZ Grammar Course Pilot (disposable)::1 Lesson" in names
        assert "ZZ Grammar Course Pilot (disposable)::2 Exercises" in names
        tags_rows = conn.execute("SELECT tags FROM notes").fetchall()
        all_tags = " ".join(row[0] for row in tags_rows)
        assert "idiomatic-course-lesson" in all_tags
        assert "idiomatic-course-exercise" in all_tags
        assert "idiomatic-course-block::de::kasus::c01" in all_tags
        assert "idiomatic-course-src::book-verbatim" in all_tags
        assert course.AUDIO_PENDING_TAG in all_tags
        conn.close()

    def test_lesson_guids_survive_rebuild(self, tmp_path: Path) -> None:
        out, _result = self._build(tmp_path)
        conn = _open_collection(out, tmp_path)
        guids_first = sorted(
            row[0] for row in conn.execute("SELECT guid FROM notes")
        )
        conn.close()
        out2, _result = self._build(tmp_path)
        conn = _open_collection(out2, tmp_path)
        guids_second = sorted(
            row[0] for row in conn.execute("SELECT guid FROM notes")
        )
        conn.close()
        assert guids_first == guids_second


# ---------------------------------------------------------------------------
# Copyright guard
# ---------------------------------------------------------------------------


class TestCopyrightGuard:
    def test_book_local_path_is_gitignored(self) -> None:
        """Book-derived exercise content must never be committable."""
        probe = _REPO_ROOT / "idiomatic" / "grammar" / "data" / "course" \
            / "book_local" / "de_kasus.exercises.json"
        try:
            completed = subprocess.run(
                ["git", "check-ignore", "-q", str(probe)],
                cwd=_REPO_ROOT,
                capture_output=True,
                timeout=30,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("git unavailable")
        assert completed.returncode == 0, \
            "idiomatic/grammar/data/course/book_local/ must be gitignored"

    def test_book_local_dir_constant_points_inside_ignored_path(self) -> None:
        assert course.BOOK_LOCAL_DIR.name == "book_local"
        assert course.BOOK_LOCAL_DIR.parent.name == "course"
