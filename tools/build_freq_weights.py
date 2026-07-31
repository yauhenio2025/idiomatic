#!/usr/bin/env python3
"""Build tense/person frequency weights for the grammar curriculum.

The source is hermitdave/FrequencyWords' OpenSubtitles 2018 per-form lists.
Downloads are pinned to a commit and cached, so a second run can be fully
offline.  The emitted files are deliberately aggregate (normalized weights),
not copies of the source frequency lists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
import unicodedata
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from idiomatic.grammar import morphology  # noqa: E402
from idiomatic.grammar.curriculum import topic_by_key, topics_for  # noqa: E402


LANGS = ("es", "fr", "it", "pt", "de")
SOURCE_REVISION = "525f9b560de45753a5ea01069454e72e9aa541c6"
SOURCE_URL = (
    "https://raw.githubusercontent.com/hermitdave/FrequencyWords/"
    f"{SOURCE_REVISION}/content/2018/{{lang}}/{{lang}}_full.txt"
)
SOURCE_REPOSITORY = "https://github.com/hermitdave/FrequencyWords"
SOURCE_CORPUS = "OPUS OpenSubtitles 2018"
SOURCE_LICENSE = "CC BY-SA 4.0"

# An untagged list cannot tell these common noun/function-word readings from
# the finite verb.  A conservative factor prevents a subtitle count for e.g.
# French *porte* (door) from making *porter* look artificially dominant.
KNOWN_HOMOGRAPHS = {
    "es": frozenset({
        "como", "cuenta", "dicho", "era", "hecho", "para", "puesto", "sal", "vino",
    }),
    "fr": frozenset({
        "compte", "été", "fait", "livre", "marche", "mort", "passé", "porte",
    }),
    "it": frozenset({
        "conto", "detto", "fatto", "parte", "passato", "porta", "sale", "stato",
    }),
    "pt": frozenset({
        "como", "conta", "dito", "era", "estado", "feito", "para", "passado", "rio",
    }),
    "de": frozenset(),
}

PT_GENERATION_PERSONS = ("1s", "3s", "1p", "3p")

DE_WERDEN_PRESENT = {
    "1s": "werde", "2s": "wirst", "3s": "wird",
    "1p": "werden", "2p": "werdet", "3p": "werden",
}
DE_WERDEN_PRETERITE = {
    "1s": "wurde", "2s": "wurdest", "3s": "wurde",
    "1p": "wurden", "2p": "wurdet", "3p": "wurden",
}
DE_SEIN_PRESENT = {
    "1s": "bin", "2s": "bist", "3s": "ist",
    "1p": "sind", "2p": "seid", "3p": "sind",
}
DE_MODAL_PRESENT = {
    "müssen": {
        "1s": "muss", "2s": "musst", "3s": "muss",
        "1p": "müssen", "2p": "müsst", "3p": "müssen",
    },
    "können": {
        "1s": "kann", "2s": "kannst", "3s": "kann",
        "1p": "können", "2p": "könnt", "3p": "können",
    },
    "sollen": {
        "1s": "soll", "2s": "sollst", "3s": "soll",
        "1p": "sollen", "2p": "sollt", "3p": "sollen",
    },
    "dürfen": {
        "1s": "darf", "2s": "darfst", "3s": "darf",
        "1p": "dürfen", "2p": "dürft", "3p": "dürfen",
    },
}


@dataclass(frozen=True)
class Cell:
    unit: str
    verb: str
    person: str
    # Alternatives inside one group are averaged; groups are then averaged
    # equally.  Ordinary cells have one group with one surface.  German has
    # four equally weighted passive categories, with four alternatives in
    # the modal category.
    surface_groups: tuple[tuple[str, ...], ...]


def _norm(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _tokens(surface: str) -> tuple[str, ...]:
    tokens = []
    for raw in _norm(surface).split():
        token = raw.strip(".,;:!?¡¿\"'«»()[]{}")
        if token:
            tokens.append(token)
    return tuple(tokens)


def _load_de_participles() -> dict[str, str]:
    path = ROOT / "idiomatic" / "grammar" / "data" / "de_participles.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _eligible_persons(lang: str, unit: str) -> tuple[str, ...]:
    if lang == "pt":
        return PT_GENERATION_PERSONS
    # Imperative units have narrower production policies than the source
    # paradigm.  Weight only cells the generator is actually allowed to use.
    overrides = {
        "es_cmd_tu": ("2s",),
        "es_cmd_usted": ("3s", "1p", "3p"),
        "es_cmd_neg": ("2s", "3s", "3p"),
    }
    return overrides.get(unit, morphology.PERSONS)


def _ordinary_cells(
    lang: str,
) -> tuple[list[Cell], dict[str, list[str]], dict[str, tuple[str, ...]], int]:
    cells: list[Cell] = []
    units: dict[str, list[str]] = {}
    unit_persons: dict[str, tuple[str, ...]] = {}
    missing = 0
    for topic in topics_for(lang):
        if not topic.mood or not topic.tense or not topic.verbs:
            continue
        units[topic.key] = list(topic.verbs)
        persons = _eligible_persons(lang, topic.key)
        unit_persons[topic.key] = persons
        for verb in topic.verbs:
            for person in persons:
                surface = morphology.lookup(
                    lang, verb, topic.mood, topic.tense, person
                )
                if surface:
                    cells.append(Cell(topic.key, verb, person, ((surface,),)))
                else:
                    missing += 1
    return cells, units, unit_persons, missing


def _german_cells(
) -> tuple[list[Cell], dict[str, list[str]], dict[str, tuple[str, ...]], int]:
    topic = topic_by_key("de_passiv")
    if topic is None:
        raise RuntimeError("de_passiv is missing from the live curriculum")
    participles = _load_de_participles()
    cells: list[Cell] = []
    missing = 0
    for verb in topic.verbs:
        participle = participles.get(verb)
        for person in morphology.PERSONS:
            if participle is None:
                missing += 1
                continue
            modal_surfaces = tuple(
                f"{participle} werden {forms[person]}"
                for forms in DE_MODAL_PRESENT.values()
            )
            groups = (
                (f"{participle} {DE_WERDEN_PRESENT[person]}",),
                (f"{participle} {DE_WERDEN_PRETERITE[person]}",),
                (f"{participle} worden {DE_SEIN_PRESENT[person]}",),
                modal_surfaces,
            )
            cells.append(Cell(topic.key, verb, person, groups))
    return (
        cells,
        {topic.key: list(topic.verbs)},
        {topic.key: morphology.PERSONS},
        missing,
    )


def curriculum_cells(
    lang: str,
) -> tuple[list[Cell], dict[str, list[str]], dict[str, tuple[str, ...]], int]:
    if lang == "de":
        return _german_cells()
    return _ordinary_cells(lang)


def source_path(cache_dir: Path, lang: str) -> Path:
    return cache_dir / SOURCE_REVISION / f"{lang}_full.txt"


def download_source(cache_dir: Path, lang: str, *, offline: bool,
                    refresh: bool) -> Path:
    destination = source_path(cache_dir, lang)
    if destination.exists() and not refresh:
        return destination
    if offline:
        raise FileNotFoundError(
            f"offline source is missing: {destination}; run once without --offline"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        SOURCE_URL.format(lang=lang),
        headers={"User-Agent": "idiomatic-frequency-builder/1"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, prefix=f".{lang}.", delete=False
        ) as tmp:
            temporary = Path(tmp.name)
            while chunk := response.read(1024 * 1024):
                tmp.write(chunk)
    temporary.replace(destination)
    return destination


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wanted_frequencies(path: Path, wanted: set[str]) -> dict[str, int]:
    frequencies: dict[str, int] = {}
    with path.open(encoding="utf-8") as source:
        for number, line in enumerate(source, 1):
            try:
                word, raw_count = line.rstrip("\n").rsplit(" ", 1)
                word = _norm(word)
                if word in wanted:
                    frequencies[word] = frequencies.get(word, 0) + int(raw_count)
            except (ValueError, UnicodeError) as exc:
                raise ValueError(f"malformed frequency row {path}:{number}") from exc
    return frequencies


def _short_token_factor(token: str) -> float:
    letters = sum(character.isalpha() for character in token)
    if letters <= 1:
        return 0.05
    if letters == 2:
        return 0.15
    if letters == 3:
        return 0.40
    return 1.0


def _surface_score(lang: str, surface: str, frequencies: dict[str, int],
                   analysis_ambiguity: int, nonfinite_collision: bool,
                   cross_lemma_collision: bool) -> float:
    tokens = _tokens(surface)
    if not tokens:
        return 0.0
    adjusted = []
    for token in tokens:
        count = float(frequencies.get(token, 0))
        count *= _short_token_factor(token)
        if token in KNOWN_HOMOGRAPHS[lang]:
            count *= 0.10
        adjusted.append(count)
    if not all(adjusted):
        return 0.0
    # A geometric mean lets both the lexical form and a person-marked
    # auxiliary affect a compound, without pretending unigram counts are a
    # phrase-frequency corpus.
    score = math.exp(sum(math.log1p(value) for value in adjusted) / len(adjusted)) - 1
    if nonfinite_collision:
        # Portuguese regular future-subjunctive 1s/3s forms, for example,
        # are identical to the much more frequent infinitive.  Equal-split
        # ambiguity is still too optimistic, so retain only a tenth.
        score *= 0.10
    if cross_lemma_collision:
        # Equal division is an upper bound when the same spelling belongs to
        # different lexemes (Spanish cree = creer indicative / crear
        # subjunctive).  Apply an additional conservative uncertainty factor.
        score *= 0.10
    return score / max(analysis_ambiguity, 1)


def _morphology_ambiguity(
    lang: str, cells: list[Cell]
) -> tuple[dict[str, int], frozenset[str], frozenset[str]]:
    """Analysis counts and high-risk collisions for each exact surface."""
    analyses: dict[str, set[tuple[str, ...]]] = defaultdict(set)
    nonfinite: set[str] = set()
    finite: set[str] = set()
    if lang == "es":
        for (lemma, mood, tense), forms in morphology._load_es().items():
            for person, surface in forms.items():
                normalized = _norm(surface)
                analyses[normalized].add((lemma, mood, tense, person))
                (nonfinite if "infinit" in mood or "infinit" in tense else finite).add(
                    normalized
                )
    elif lang in ("fr", "it", "pt"):
        for lemma, moods in morphology._load_verbecc(lang).items():
            for mood, tenses in moods.items():
                for tense, forms in tenses.items():
                    for person, surface in forms.items():
                        normalized = _norm(surface)
                        analyses[normalized].add((lemma, mood, tense, person))
                        (
                            nonfinite
                            if "infinit" in mood or "infinit" in tense
                            else finite
                        ).add(normalized)
    else:
        for cell in cells:
            for group in cell.surface_groups:
                for surface in group:
                    analyses[_norm(surface)].add(
                        (cell.unit, cell.verb, cell.person, surface)
                    )
    return (
        {surface: len(values) for surface, values in analyses.items()},
        frozenset(nonfinite & finite),
        frozenset(
            surface
            for surface, values in analyses.items()
            if len({analysis[0] for analysis in values}) > 1
        ),
    )


def raw_scores(lang: str, cells: list[Cell], frequencies: dict[str, int]) -> dict[Cell, float]:
    ambiguity, nonfinite_collisions, cross_lemma_collisions = _morphology_ambiguity(
        lang, cells
    )

    result = {}
    for cell in cells:
        group_scores = []
        for group in cell.surface_groups:
            alternatives = []
            for surface in group:
                normalized = _norm(surface)
                alternatives.append(_surface_score(
                    lang,
                    normalized,
                    frequencies,
                    ambiguity.get(normalized, 1),
                    normalized in nonfinite_collisions,
                    normalized in cross_lemma_collisions,
                ))
            group_scores.append(sum(alternatives) / len(alternatives))
        result[cell] = sum(group_scores) / len(group_scores)
    return result


def build_language(lang: str, source: Path, build_date: str) -> tuple[dict, list[tuple[Cell, float]]]:
    cells, unit_verbs, unit_persons, missing = curriculum_cells(lang)
    wanted = {
        token
        for cell in cells
        for group in cell.surface_groups
        for surface in group
        for token in _tokens(surface)
    }
    frequencies = wanted_frequencies(source, wanted)
    scores = raw_scores(lang, cells, frequencies)

    normalized: dict[Cell, float] = {}
    for unit in unit_verbs:
        unit_cells = [cell for cell in cells if cell.unit == unit]
        maximum = max((scores[cell] for cell in unit_cells), default=0.0)
        for cell in unit_cells:
            normalized[cell] = round(scores[cell] / maximum, 6) if maximum else 0.0

    output: dict[str, object] = {
        "_meta": {
            "schema_version": 1,
            "language": lang,
            "build_date": build_date,
            "source": {
                "name": "hermitdave/FrequencyWords 2018 full list",
                "repository": SOURCE_REPOSITORY,
                "revision": SOURCE_REVISION,
                "corpus": SOURCE_CORPUS,
                "license": SOURCE_LICENSE,
                "sha256": sha256(source),
            },
            "normalization": (
                "ambiguity-adjusted effective unigram count divided by the "
                "maximum cell score within each unit"
            ),
            "compound_policy": (
                "geometric mean of component-token counts; German de_passiv "
                "averages present, preterite, perfect, and modal categories"
            ),
            "homograph_policy": (
                "split exact forms shared by lemmas/persons; penalize very "
                "short forms, cross-lemma and finite/nonfinite collisions, "
                "and a conservative per-language known-homograph list"
            ),
            "eligible_persons": list(
                PT_GENERATION_PERSONS if lang == "pt" else morphology.PERSONS
            ),
            "unit_person_overrides": {
                unit: list(persons)
                for unit, persons in unit_persons.items()
                if persons != (
                    PT_GENERATION_PERSONS if lang == "pt" else morphology.PERSONS
                )
            },
            "unit_count": len(unit_verbs),
            "weighted_cell_count": len(cells),
            "zero_weight_cell_count": sum(value == 0 for value in normalized.values()),
            "missing_morphology_cell_count": missing,
        }
    }
    if lang == "de":
        output["_meta"]["scope_note"] = (  # type: ignore[index]
            "German currently has one verb-list unit, de_passiv. The unknown "
            "participle for archivieren remains at zero rather than being guessed."
        )
    elif lang == "pt":
        output["_meta"]["scope_note"] = (  # type: ignore[index]
            "Brazilian curriculum policy excludes tu/vós (2s/2p) cells."
        )

    by_key = {(cell.unit, cell.verb, cell.person): value for cell, value in normalized.items()}
    for unit, verbs in unit_verbs.items():
        output[unit] = {
            verb: {
                person: by_key.get((unit, verb, person), 0.0)
                for person in unit_persons[unit]
            }
            for verb in verbs
        }
    ranked = sorted(normalized.items(), key=lambda pair: pair[1], reverse=True)
    return output, ranked


def _build_date(argument: str | None) -> str:
    if argument:
        return date.fromisoformat(argument).isoformat()
    if epoch := os.environ.get("SOURCE_DATE_EPOCH"):
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).date().isoformat()
    return date.today().isoformat()


def print_summary(lang: str, ranked: list[tuple[Cell, float]]) -> None:
    positive = [pair for pair in ranked if pair[1] > 0]
    print(f"\n{lang.upper()} highest 10")
    for cell, weight in positive[:10]:
        print(f"{cell.unit}\t{cell.verb}\t{cell.person}\t{weight:.6f}")
    print(f"{lang.upper()} lowest 10 positive")
    for cell, weight in reversed(positive[-10:]):
        print(f"{cell.unit}\t{cell.verb}\t{cell.person}\t{weight:.6f}")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--languages", nargs="+", choices=LANGS, default=list(LANGS))
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        / "idiomatic" / "frequency-words",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "idiomatic" / "grammar" / "data",
    )
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--build-date", help="ISO date; defaults to today")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    if args.offline and args.refresh:
        raise SystemExit("--offline and --refresh cannot be combined")
    build_date = _build_date(args.build_date)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for lang in args.languages:
        source = download_source(
            args.cache_dir, lang, offline=args.offline, refresh=args.refresh
        )
        output, ranked = build_language(lang, source, build_date)
        destination = args.output_dir / f"freq_weights_{lang}.json"
        serialized = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
        if len(serialized.encode("utf-8")) >= 500_000:
            raise RuntimeError(f"output exceeds 500 KB: {destination}")
        destination.write_text(serialized, encoding="utf-8")
        print(f"wrote {destination} ({len(serialized.encode('utf-8')):,} bytes)")
        if args.summary:
            print_summary(lang, ranked)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
