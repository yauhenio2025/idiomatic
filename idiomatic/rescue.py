"""Rescue Lab domain logic — format taxonomy, prompt templates, guards.

The format templates are the SEED PROMPTS distilled from the approved
pilot exemplars (docs/research/rescue_pilot1/content.json + round2.json)
with the item-specific content replaced by placeholders. They live in
code (not a table) for the same reason grammar/curriculum.py does: the
definition is versioned with the logic that fills it, and the dashboard
reads it via /ui/api/rescue/formats.

Hard user verdicts encoded here:
- Video is NOT a format. Never add it.
- polysemy_map: every sense ("door") must be TAUGHT, not just labeled —
  gloss + micro-example per sense, >= 2 senses. Enforced both at
  generate time (the template refuses to fill without senses) and at
  approve time (polysemy_approval_error).
- anatomy: the word must read strictly left-to-right or the format is
  void — the demand is baked into the template text.
- glyph: one permanent glyph per idiom, reused on every future asset.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .langs import LANG_NAMES

# Formats the generate endpoint can actually produce via genmedia today.
IMAGE_FORMATS = ("comic", "contrast", "polysemy_map", "anatomy", "poster",
                 "glyph")
# Legal in rescue_assets but authored outside the dashboard (hand-made
# SVG diagrams; ElevenLabs sentence audio) — /admin/rescue/generate
# refuses them with a pointer.
MANUAL_FORMATS = ("svg", "sentence_audio")
ALL_FORMATS = IMAGE_FORMATS + MANUAL_FORMATS

_PLACEHOLDERS_COMMON = {
    "idiom": "the expression, as spoken",
    "idiom_upper": "the expression, uppercased for banner lettering",
    "gloss": "one-line English gloss",
    "anchor": "the item's anchor line (mnemonic/etymology hook)",
    "lang_name": "language name (Spanish, Italian, …)",
    "scene_hint": "the failed sentence from the struggle snapshot, "
                  "falling back to the anchor",
}

FORMATS: dict[str, dict[str, Any]] = {
    "comic": {
        "name": "Comic strip",
        "kind": "image",
        "when_to_use": "Strike 1 default: narrative/humor encoding of one "
                       "concrete scene where the idiom is the natural thing "
                       "to say. Round-1 winner (comics > SVG > video).",
        "rules": [
            "The idiom is the ONLY text in the image, as a single speech "
            "bubble, verbatim.",
            "One small concrete everyday scene, not an abstract allegory.",
        ],
        "template": (
            "A crisp 3-panel comic strip in one image, clean European ligne "
            "claire style, warm muted colors, panels side by side with thin "
            "gutters. The strip tells one small, concrete everyday scene in "
            "which the {lang_name} expression «{idiom}» ({gloss}) is the "
            "natural thing to say — build the scene from this situation: "
            "{scene_hint}. The expression appears exactly once, in one "
            "speech bubble at the scene's turning point, and is the ONLY "
            "text in the whole image, EXACTLY: {idiom}"
        ),
    },
    "contrast": {
        "name": "Inside/outside contrast",
        "kind": "image",
        "when_to_use": "Recognition failures on spatial/prepositional "
                       "idioms: makes the preposition itself the picture "
                       "and teaches the opposite in the same glance.",
        "rules": [
            "Two zones, one boundary; the expression's zone warm, the "
            "opposite cool.",
            "Only three text elements: one label per zone + one caption.",
        ],
        "template": (
            "A single wide editorial illustration, contemporary flat style "
            "with rich warm/cool contrast. It encodes the SPATIAL LOGIC of "
            "the {lang_name} expression «{idiom}» ({gloss}) as one image: "
            "one zone that IS the expression, bathed in warm amber light, "
            "and the opposite zone in cool blue dusk, separated by one "
            "simple physical boundary. In each zone, small figures act out "
            "that side's meaning; a small elegant label names each zone. "
            "At the bottom, one clean caption line: {idiom} = {gloss}. "
            "Only these three pieces of text, nothing else. Build the "
            "scene from this anchor: {anchor}"
        ),
    },
    "polysemy_map": {
        "name": "Polysemy map",
        "kind": "image",
        "when_to_use": "Failures clustered on one sense of a multi-sense "
                       "word: one image holds every sense as sibling doors "
                       "so the brain files them together.",
        "rules": [
            "Requires >= 2 senses ON THE ITEM, each with gloss + "
            "micro-example — every door is taught, not just labeled "
            "(user rule, enforced at approval).",
            "One banner (the expression) + one small label per arch; no "
            "other text.",
        ],
        "template": (
            "One wide image divided into {n_senses} equal arched doorways, "
            "museum-poster flat style, warm palette. Above all the arches, "
            "one large elegant banner reads: {idiom_upper}. {senses_arches} "
            "Only these text elements: the banner and the one small label "
            "below each arch."
        ),
    },
    "anatomy": {
        "name": "Morphology anatomy",
        "kind": "image",
        "when_to_use": "Production (meaning→form) failures: the word "
                       "becomes an exploded machine whose parts act out "
                       "the morphology (prefix, stem, ending).",
        "rules": [
            "STRICT left-to-right letter order — the first pilot render "
            "scrambled the word and the format is void when that happens.",
            "Each morpheme a distinct material acting out its function.",
        ],
        "template": (
            "A technical-poster style illustration, annotated diagram "
            "aesthetic on deep slate background. The {lang_name} word "
            "'{idiom}' rendered huge as physical 3D letterforms in the "
            "center, each morpheme built from a different material that "
            "acts out its grammatical function — use this anchor to choose "
            "the materials: {anchor}. CRITICAL: the letters of '{idiom}' "
            "must read cleanly LEFT TO RIGHT in strict spelling order, "
            "every letter present exactly once, fully legible — a "
            "scrambled or reordered word makes the image unusable. One "
            "caption line at the bottom: {scene_hint}. The only text: the "
            "central word, at most two small annotation labels, and the "
            "caption."
        ),
    },
    "poster": {
        "name": "Iconic poster",
        "kind": "image",
        "when_to_use": "Recognition failures on metaphor idioms: the "
                       "metaphor's source domain as one flat emblem — one "
                       "still, instantly re-recognizable at review time "
                       "(replaces what video tried and failed at).",
        "rules": [
            "One emblem, no scene, no narrative; at most four colors.",
            "Bold lettering of the expression at the bottom; no other text.",
        ],
        "template": (
            "A minimalist mid-century poster, flat vector style, at most "
            "four colors. One single iconic emblem that fuses the literal "
            "source domain of the {lang_name} expression «{idiom}» with "
            "its figurative meaning ({gloss}) into one still composition — "
            "no scene, no narrative, instantly re-recognizable as a small "
            "thumbnail. Bold poster lettering at the bottom: {idiom_upper}. "
            "No other text. Metaphor to encode: {anchor}"
        ),
    },
    "glyph": {
        "name": "Idiom glyph",
        "kind": "image",
        "when_to_use": "Minted at strike 1 and PERMANENT: the one fixed "
                       "pictographic stamp reused on every future card and "
                       "asset of this idiom — the constant identity across "
                       "changing content.",
        "rules": [
            "One glyph per idiom, ever; approving it pins "
            "rescue_items.glyph_asset_id.",
            "Two colors, thick outlines, no gradients, NO text, legible "
            "at small size.",
        ],
        "template": (
            "One bold circular glyph centered on a neutral light "
            "background, app-icon style, thick outlines, exactly two "
            "colors, no gradients, no text anywhere. The glyph is the "
            "permanent minimal logo of the {lang_name} expression "
            "«{idiom}» ({gloss}): reduce the expression's core image to "
            "one pictogram that stays instantly readable at small size. "
            "Core image to reduce: {anchor}"
        ),
    },
    "svg": {
        "name": "SVG diagram",
        "kind": "manual",
        "when_to_use": "Structural/morphological encodings that need exact "
                       "text layout (tables, gears, gates). Hand-authored "
                       "in the night-slate style of the podcast cards — "
                       "not generated through image providers.",
        "rules": ["Authored outside the dashboard; no generation flow."],
        "template": None,
    },
    "sentence_audio": {
        "name": "Sentence audio",
        "kind": "manual",
        "when_to_use": "Personalized sentences with ElevenLabs audio (the "
                       "same per-language voices as the main decks). "
                       "Produced by the deck-build flow, not the image "
                       "generate panel.",
        "rules": ["Authored outside the dashboard; no generation flow."],
        "template": None,
    },
}


def format_placeholders(fmt: str) -> dict[str, str]:
    """Per-format placeholder documentation for the Formats page."""
    spec = FORMATS[fmt]
    if spec["template"] is None:
        return {}
    doc = {k: v for k, v in _PLACEHOLDERS_COMMON.items()
           if "{%s}" % k in spec["template"]}
    if fmt == "polysemy_map":
        doc["n_senses"] = "number of senses on the item"
        doc["senses_arches"] = ("one arch description per sense, built "
                                "from label + gloss + example_tl")
    return doc


def fill_template(fmt: str, item: Mapping[str, Any],
                  senses: Sequence[Mapping[str, Any]] = ()) -> str:
    """Substitute an item's fields into a format template.

    Raises ValueError for manual formats and for a polysemy_map on an
    item with < 2 senses (there is nothing meaningful to draw — the
    doors ARE the senses)."""
    spec = FORMATS.get(fmt)
    if spec is None:
        raise ValueError(f"unknown format {fmt!r}")
    if spec["template"] is None:
        raise ValueError(f"format {fmt!r} is authored manually — "
                         "no generation template")
    idiom = (item.get("idiom") or "").strip()
    gloss = (item.get("gloss") or "").strip() or "meaning unknown"
    # Trailing periods come off — the templates place their own
    # sentence-ending punctuation after these slots.
    anchor = ((item.get("anchor") or "").strip() or gloss).rstrip(".")
    snapshot = item.get("struggle_snapshot") or {}
    sentences = snapshot.get("failed_sentences") or []
    scene_hint = (sentences[0].strip() if sentences else anchor).rstrip(".")
    values = {
        "idiom": idiom,
        "idiom_upper": idiom.upper(),
        "gloss": gloss,
        "anchor": anchor,
        "lang_name": LANG_NAMES.get(item.get("lang", ""),
                                    str(item.get("lang", "")).upper()),
        "scene_hint": scene_hint,
    }
    if fmt == "polysemy_map":
        if len(senses) < 2:
            raise ValueError(
                "polysemy_map needs >= 2 senses with gloss + example "
                "(teach every door) — add senses on the item first")
        arches = " ".join(
            f"Through arch {i}: a concrete scene showing the sense "
            f"“{s['gloss']}” (as in: {s['example_tl']}); small label "
            f"below: {s['label']}."
            for i, s in enumerate(senses, 1))
        values["n_senses"] = str(len(senses))
        values["senses_arches"] = arches
    return spec["template"].format(**values)


def polysemy_approval_error(fmt: str, n_senses: int) -> str | None:
    """The 'teach every door' guard, applied at asset approval."""
    if fmt == "polysemy_map" and n_senses < 2:
        return ("cannot approve a polysemy_map for an item with "
                f"{n_senses} sense(s): the polysemy rule requires >= 2 "
                "senses, each with gloss + micro-example")
    return None


# --- struggle-snapshot upload validation ------------------------------------

def validate_struggles(payload: Any) -> tuple[list[dict], list[str]]:
    """Normalize an uploaded struggle snapshot (list of dicts) into
    rescue_items upsert rows. Returns (rows, errors); any error rejects
    the whole upload — snapshots are small and regenerated at will."""
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        payload = payload["items"]
    if not isinstance(payload, list) or not payload:
        return [], ["body must be a non-empty JSON list of struggle rows "
                    "(or {\"items\": [...]})"]
    rows, errors = [], []
    for i, raw in enumerate(payload):
        if not isinstance(raw, dict):
            errors.append(f"row {i}: not an object")
            continue
        lang = str(raw.get("lang") or "").strip().lower()
        idiom = str(raw.get("idiom") or "").strip()
        if len(lang) != 2 or not lang.isalpha():
            errors.append(f"row {i}: bad lang {raw.get('lang')!r}")
        if not idiom:
            errors.append(f"row {i}: missing idiom")
        fails_today = raw.get("fails_today", 0)
        fails_14d = raw.get("fails_14d", 0)
        if not (isinstance(fails_today, int) and fails_today >= 0
                and isinstance(fails_14d, int) and fails_14d >= 0):
            errors.append(f"row {i}: fails_today/fails_14d must be ints >= 0")
        sentences = raw.get("failed_sentences", [])
        if not (isinstance(sentences, list)
                and all(isinstance(s, str) and s.strip() for s in sentences)):
            errors.append(f"row {i}: failed_sentences must be a list of "
                          "non-empty strings")
        if errors and errors[-1].startswith(f"row {i}:"):
            continue
        rows.append({
            "lang": lang,
            "idiom": idiom,
            "gloss": str(raw.get("gloss") or "").strip() or None,
            "snapshot": {
                "fails_today": fails_today,
                "fails_14d": fails_14d,
                "failed_sentences": [s.strip() for s in sentences],
            },
        })
    return (rows, errors) if not errors else ([], errors)


def validate_senses(payload: Any) -> tuple[list[dict], list[str]]:
    """Validate a replace-all senses list for the item patch endpoint.
    Every sense must be fully taught: label, gloss, example_tl,
    example_en all non-empty (the data-level polysemy rule)."""
    if not isinstance(payload, list):
        return [], ["senses must be a list"]
    rows, errors = [], []
    for i, raw in enumerate(payload):
        if not isinstance(raw, dict):
            errors.append(f"sense {i}: not an object")
            continue
        row = {}
        for field in ("label", "gloss", "example_tl", "example_en"):
            value = str(raw.get(field) or "").strip()
            if not value:
                errors.append(f"sense {i}: {field} is required — every "
                              "door needs a gloss and a micro-example")
                break
            row[field] = value
        else:
            row["ord"] = i + 1
            rows.append(row)
    return (rows, errors) if not errors else ([], errors)
