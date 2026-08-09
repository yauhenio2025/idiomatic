"""Grammar Course narration lane tests: no network, no DB, no ffmpeg."""

from __future__ import annotations

import asyncio
import json
import re
import sqlite3
import zipfile
from pathlib import Path

import pytest

from idiomatic import db, local_tts
from idiomatic.grammar import course

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _frontmatter(*, lang: str = "de", unit: str = "kasus") -> str:
    return f"""---
series: grammar-course-lesson
lang: {lang}
unit: {unit}
title: "Fixture unit"
unit_label: "Kasus (cases)"
---
"""


def _card(seq: int, *, front_body: str | None = None) -> str:
    front_body = front_body if front_body is not None else (
        f"Narrate front {seq}.\nTL: Der Zug war nicht pünktlich.\n"
    )
    return f"""[CARD]
TITLE: Front {seq}
REF: 2.1
{front_body}[SIDE]
TITLE: Back {seq}
REF: 2.1
Narrate back {seq}.
SHOW: Back note {seq}
TL-: Der Zug war nicht pünktlich.
"""


def _lesson(tmp_path: Path, *, n_cards: int = 8,
            front1: str | None = None) -> course.CourseLesson:
    cards = _card(1, front_body=front1) + "".join(
        _card(seq) for seq in range(2, n_cards + 1)
    )
    path = tmp_path / "de_kasus.md"
    path.write_text(
        _frontmatter() + "\n## SCRIPT\n" + cards, encoding="utf-8"
    )
    return course.parse_course_lesson(path)


def _exercise_payload(item_id: str = "pgg-c02-e14-i1") -> dict:
    return {
        "id": item_id,
        "instruction": "Add the missing endings.",
        "prompt": "Wir sprachen mit Maria Simon, d___ Filmschauspielerin.",
        "solution_html":
            "Wir sprachen mit Maria Simon, <mark>der</mark> "
            "Filmschauspielerin.",
        "alternatives": [],
        "hammer_refs": ["2.6"],
        "source_ref": "PGG Kap. 2, Üb. 14, Nr. 1",
        "provenance": "book-verbatim",
    }


def _exercises(tmp_path: Path, items: list[dict] | None = None,
               block: int = 1) -> list[course.CourseExercise]:
    payload = {
        "lang": "de", "unit": "kasus",
        "blocks": [{"block": block,
                    "exercises": items or [_exercise_payload()]}],
    }
    path = tmp_path / "de_kasus.exercises.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return course.parse_exercises_file(path)


# ---------------------------------------------------------------------------
# Spoken text + speech segments
# ---------------------------------------------------------------------------


class TestSpokenText:
    def _exercise(self, solution: str) -> course.CourseExercise:
        raw = _exercise_payload()
        raw["solution_html"] = solution
        return course._parse_exercise(
            Path("de_kasus.exercises.json"), "de", "kasus", 1, raw
        )

    def test_unwraps_marks_and_keeps_sentence(self) -> None:
        exercise = self._exercise(
            "Tobias <mark>sieht seinem</mark> Bruder <mark>ähnlich.</mark>"
        )
        assert course.solution_spoken_text(exercise) == \
            "Tobias sieht seinem Bruder ähnlich."

    def test_strips_bracketed_prompt_fragments(self) -> None:
        exercise = self._exercise(
            "Sie mussten [der weite Weg] <mark>den weiten Weg</mark> "
            "zu Fuß gehen."
        )
        assert course.solution_spoken_text(exercise) == \
            "Sie mussten den weiten Weg zu Fuß gehen."

    def test_strips_parenthetical_key_commentary(self) -> None:
        exercise = self._exercise(
            "<mark>sechs Flaschen deutschen Wein "
            "(deutschen Weines sounds old-fashioned)</mark>"
        )
        assert course.solution_spoken_text(exercise) == \
            "sechs Flaschen deutschen Wein"

    def test_raises_when_nothing_speakable_remains(self) -> None:
        exercise = self._exercise("<mark>(all commentary)</mark>")
        with pytest.raises(ValueError, match="speakable"):
            course.solution_spoken_text(exercise)

    def test_speech_segments_exclude_pauses_keep_order(
        self, tmp_path: Path
    ) -> None:
        lesson = _lesson(tmp_path, front1=(
            "First line.\n[PAUSE:1200]\nTL: Der Zug war nicht pünktlich.\n"
            "Closing line.\n"
        ))
        speech = course.speech_segments(lesson.cards[0].front)
        assert [seg.lang for seg in speech] == ["en", "de", "en"]
        assert speech[0].text == "First line."


# ---------------------------------------------------------------------------
# Queue row builders (the §6 seeding contract)
# ---------------------------------------------------------------------------


class TestJobRows:
    def test_lesson_rows_one_per_speech_segment(self, tmp_path: Path) -> None:
        lesson = _lesson(tmp_path)
        rows = local_tts.course_lesson_job_rows(lesson)
        # fixture: front = EN + TL (2), back = EN + TL- (2) per card
        assert len(rows) == 8 * 2 * 2
        assert {row["source_kind"] for row in rows} == \
            {local_tts.COURSE_LESSON_SOURCE_KIND}
        first_front = [row for row in rows
                       if row["note_key"] == "course:de:kasus:1:front"]
        assert [row["clip_kind"] for row in first_front] == ["seg000", "seg001"]
        assert [row["lang"] for row in first_front] == ["en", "de"]
        assert first_front[0]["source_key"] == \
            "course:v1:de:kasus:1:front:seg000"

    def test_row_hash_and_path_are_consistent(self, tmp_path: Path) -> None:
        lesson = _lesson(tmp_path)
        row = local_tts.course_lesson_job_rows(lesson)[0]
        assert row["content_hash"] == local_tts.content_hash(
            row["text"], row["lang"]
        )
        assert row["staged_path"] == local_tts.course_staged_path(
            row["source_key"], row["lang"], row["content_hash"]
        )
        assert re.fullmatch(
            r"grammar/course/local_qwen/v1/en/idcrs_v1_en_[0-9a-f]{12}"
            r"_[0-9a-f]{20}\.mp3",
            row["staged_path"],
        )

    def test_exercise_rows_voice_the_solution_in_target_lang(
        self, tmp_path: Path
    ) -> None:
        exercises = _exercises(tmp_path)
        rows = local_tts.course_exercise_job_rows(exercises)
        assert len(rows) == 1
        row = rows[0]
        assert row["source_kind"] == local_tts.COURSE_EXERCISE_SOURCE_KIND
        assert row["clip_kind"] == "solution"
        assert row["lang"] == "de"
        assert row["note_key"] == "course:de:kasus:pgg-c02-e14-i1"
        assert row["text"] == \
            "Wir sprachen mit Maria Simon, der Filmschauspielerin."

    def test_clip_kinds_satisfy_the_schema_constraint(
        self, tmp_path: Path
    ) -> None:
        lesson = _lesson(tmp_path)
        rows = local_tts.course_expected_job_rows(
            lesson, _exercises(tmp_path)
        )
        for row in rows:
            assert local_tts.COURSE_CLIP_KIND.fullmatch(row["clip_kind"])

    def test_schema_file_carries_the_extended_clip_kind_check(self) -> None:
        schema = (_REPO_ROOT / "db" / "schema.sql").read_text(encoding="utf-8")
        assert "'solution'" in schema
        assert "seg[0-9]{3}" in schema

    def test_expected_path_dispatch_covers_course_kinds(
        self, tmp_path: Path
    ) -> None:
        lesson = _lesson(tmp_path)
        rows = local_tts.course_expected_job_rows(
            lesson, _exercises(tmp_path)
        )
        for row in (rows[0], rows[-1]):
            assert local_tts._expected_path_for_job(row) == row["staged_path"]

    def test_block_mismatch_fails_the_plan(self, tmp_path: Path) -> None:
        lesson = _lesson(tmp_path)
        exercises = _exercises(tmp_path, block=9)
        with pytest.raises(ValueError, match="block"):
            local_tts.course_expected_job_rows(lesson, exercises)


# ---------------------------------------------------------------------------
# Seeding (db faked)
# ---------------------------------------------------------------------------


class TestSeed:
    def test_seed_counts_lesson_and_exercise_jobs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _lesson(tmp_path)  # writes de_kasus.md
        exercises_payload = {
            "lang": "de", "unit": "kasus",
            "blocks": [{"block": 1, "exercises": [_exercise_payload()]}],
        }
        seeded: list[list[dict]] = []

        async def fake_seed(rows: list[dict]) -> dict[str, int]:
            seeded.append(rows)
            return {"inserted": len(rows), "requeued": 0, "unchanged": 0}

        monkeypatch.setattr(db, "seed_local_tts_jobs", fake_seed)
        result = asyncio.run(local_tts.seed_course_audio(
            "de", "kasus",
            exercises_payload=exercises_payload,
            lesson_dir=tmp_path,
        ))
        assert result["lesson_segment_jobs"] == 32
        assert result["exercise_solution_jobs"] == 1
        assert result["jobs"] == 33
        assert len(seeded[0]) == 33

    def test_seed_rejects_traversal_shaped_unit(self) -> None:
        with pytest.raises(ValueError, match="invalid unit"):
            asyncio.run(local_tts.seed_course_audio("de", "../etc"))

    def test_seed_rejects_payload_unit_mismatch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _lesson(tmp_path)

        async def fake_seed(rows: list[dict]) -> dict[str, int]:
            raise AssertionError("must not reach the DB")

        monkeypatch.setattr(db, "seed_local_tts_jobs", fake_seed)
        payload = {
            "lang": "de", "unit": "plurals",
            "blocks": [{"block": 1, "exercises": [_exercise_payload()]}],
        }
        with pytest.raises(ValueError, match="mismatch"):
            asyncio.run(local_tts.seed_course_audio(
                "de", "kasus", exercises_payload=payload,
                lesson_dir=tmp_path,
            ))


# ---------------------------------------------------------------------------
# Completion matching (the tool's strict/graceful split)
# ---------------------------------------------------------------------------


class TestMatchCompletions:
    def test_partitions_matched_stale_missing(self, tmp_path: Path) -> None:
        lesson = _lesson(tmp_path)
        expected = local_tts.course_lesson_job_rows(lesson)
        current = {**expected[0]}
        stale = {**expected[1], "content_hash": "f" * 64}
        match = local_tts.match_course_completions(
            expected[:3], [current, stale]
        )
        assert set(match["matched"]) == {expected[0]["source_key"]}
        assert match["stale"] == [expected[1]["source_key"]]
        assert match["missing"] == [expected[2]["source_key"]]


# ---------------------------------------------------------------------------
# Stitching (fakes; the ffmpeg boundary stays untested here)
# ---------------------------------------------------------------------------


class TestStitch:
    def _fakes(self, tmp_path: Path):
        calls: dict[str, object] = {}

        def silence(work_dir: Path, ms: int) -> Path:
            return Path(f"/fake/silence_{ms}.mp3")

        def level(clip: Path) -> Path:
            return clip.with_name(f"{clip.stem}_lvl.mp3")

        def uniform(clip: Path) -> Path:
            return clip.with_name(f"{clip.stem}_u.mp3")

        def concat(pieces: list[Path], out: Path) -> Path:
            calls["pieces"] = list(pieces)
            calls["out"] = out
            return out

        return calls, silence, level, uniform, concat

    def test_piece_order_pause_and_gap(self, tmp_path: Path) -> None:
        lesson = _lesson(tmp_path, front1=(
            "First line.\n[PAUSE:1200]\nTL: Der Zug war nicht pünktlich.\n"
            "Closing line.\n"
        ))
        side = lesson.cards[0].front
        calls, silence, level, uniform, concat = self._fakes(tmp_path)
        clips = {0: Path("/c/a.mp3"), 1: Path("/c/b.mp3"),
                 2: Path("/c/c.mp3")}
        out = course.stitch_side_narration(
            side, clips,
            out_path=tmp_path / "out.mp3", work_dir=tmp_path / "work",
            silence_fn=silence, concat_fn=concat, level_fn=level,
            uniform_fn=uniform,
        )
        assert out == tmp_path / "out.mp3"
        names = [piece.name for piece in calls["pieces"]]
        # speech, explicit pause, speech, breathing gap, speech
        assert names == [
            "a_lvl_u.mp3", "silence_1200.mp3", "b_lvl_u.mp3",
            f"silence_{course.BETWEEN_SPEECH_MS}.mp3", "c_lvl_u.mp3",
        ]

    def test_missing_segment_clip_is_an_error(self, tmp_path: Path) -> None:
        lesson = _lesson(tmp_path)
        side = lesson.cards[0].front
        calls, silence, level, uniform, concat = self._fakes(tmp_path)
        with pytest.raises(ValueError, match="missing segment"):
            course.stitch_side_narration(
                side, {0: Path("/c/a.mp3")},
                out_path=tmp_path / "out.mp3", work_dir=tmp_path / "work",
                silence_fn=silence, concat_fn=concat, level_fn=level,
                uniform_fn=uniform,
            )


# ---------------------------------------------------------------------------
# Build integration: audio-pending drops exactly where clips resolved
# ---------------------------------------------------------------------------


class TestBuildWithAudio:
    def test_partial_voicing_builds_and_tags_only_pending(
        self, tmp_path: Path
    ) -> None:
        lesson = _lesson(tmp_path)
        exercises = _exercises(tmp_path)
        front = tmp_path / "c1_front.mp3"
        back = tmp_path / "c1_back.mp3"
        solution = tmp_path / "solution.mp3"
        for clip in (front, back, solution):
            clip.write_bytes(b"ID3fake-mp3-bytes")
        out = tmp_path / "unit.apkg"
        result = course.build_course_apkg(
            out_path=out,
            lesson=lesson,
            exercises=exercises,
            root_override="ZZ Grammar Course Pilot (disposable)",
            lesson_audio={
                (1, "front"): course.SideAudio(path=front),
                (1, "back"): course.SideAudio(path=back),
            },
            exercise_audio={"pgg-c02-e14-i1": solution},
        )
        # 8 cards ×2 sides + 1 exercise = 17 slots; 3 voiced
        assert result["audio_pending"] == 14

        extract = tmp_path / "extract"
        extract.mkdir()
        with zipfile.ZipFile(out) as bundle:
            bundle.extractall(extract)
        conn = sqlite3.connect(extract / "collection.anki2")
        rows = conn.execute(
            "SELECT flds, tags FROM notes ORDER BY id"
        ).fetchall()
        conn.close()
        by_id = {row[0].split("\x1f")[0]: row for row in rows}
        voiced_lesson = by_id["course:de:kasus:1"]
        assert "[sound:c1_front.mp3]" in voiced_lesson[0]
        assert course.AUDIO_PENDING_TAG not in voiced_lesson[1]
        pending_lesson = by_id["course:de:kasus:2"]
        assert course.AUDIO_PENDING_TAG in pending_lesson[1]
        voiced_exercise = by_id["course:de:kasus:pgg-c02-e14-i1"]
        assert "[sound:solution.mp3]" in voiced_exercise[0]
        assert course.AUDIO_PENDING_TAG not in voiced_exercise[1]


# ---------------------------------------------------------------------------
# Payload parsing parity
# ---------------------------------------------------------------------------


class TestPayloadParsing:
    def test_payload_and_file_loaders_agree(self, tmp_path: Path) -> None:
        payload = {
            "lang": "de", "unit": "kasus",
            "blocks": [{"block": 1, "exercises": [_exercise_payload()]}],
        }
        from_payload = course.parse_exercises_payload(
            payload, name="de_kasus.exercises.json"
        )
        assert from_payload == _exercises(tmp_path)

    def test_payload_rejects_unknown_lang(self) -> None:
        with pytest.raises(course.CourseSourceError, match="lang"):
            course.parse_exercises_payload(
                {"lang": "xx", "unit": "kasus", "blocks": []},
                name="payload.json",
            )
