#!/usr/bin/env python3
"""Machine-neutral rubric for the corpus-image QA loop (Q-Judger).

Maps illustration briefs (idiomatic/grammar/data/illustration_prompts/)
into the Q-Judger checklist prompt format, and classifies judge scores
into pass/fail + repair actions. No model dependencies — importable by
the judge runner (Mac) and the repair runners (both machines).

See docs/IMAGE_QA.md and docs/commissions/IMAGE_QA_LOOP_COMMISSION.md.
"""
import json
import re
from pathlib import Path

RUBRIC_VERSION = 1

# Gender per cast slug (mirrors the render fleet's FEM set).
FEM = {"penelope_cruz", "cristina_kirchner", "rosalia", "nadia_calvino",
       "juju", "angela_merkel", "luisa_neubauer", "sahra_wagenknecht",
       "marion_cotillard", "catherine_deneuve", "christine_lagarde",
       "elodie", "sophia_loren", "giorgia_meloni", "anitta",
       "dilma_rousseff", "marina_silva", "edie_falco", "lorraine_bracco",
       "sarah_snook", "j_smith_cameron", "simone_de_beauvoir",
       "christiane_amanpour"}

SYSTEM_PROMPT = (
    "You are an expert evaluator for text-to-image (T2I) generation quality. "
    "Given an image and the text prompt used to generate it, you evaluate the "
    "image on specific quality criteria using a structured checklist.")

# Same scaffold as the official Qwen-Image-Bench judge.py; the checklist
# is ours. "<image>" is split out and replaced by the actual image at
# inference time.
USER_PROMPT_TEMPLATE = """\
# Text Prompt Used to Generate the Image
{prompt}

# Generated Image
<image>

# Evaluation Dimension
{level1_dim}

# Scoring Rules
- **0 (Fail)**: Clear defect present. Would noticeably reduce image quality.
- **1 (Pass)**: No defect. Meets baseline expectations.
- **2 (Excel)**: Exceptionally executed. Only when concrete excellence is observable.
- **N/A**: This criterion does not apply to this image/prompt.

# Evaluation Checklist
{format_checklist}

# Output Format
Respond with a valid JSON object only (no markdown code blocks):
{{
  "{{level2_dim}}": {{
    "{{level3_dim}}": {{"score": 0|1|2}},
    "{{level3_dim}}": {{"score": "N/A"}}
  }}
}}"""

LEVEL1_DIM = "Alignment"

# check key -> (fail class, hard?)  — soft checks fail only as a pair.
CHECK_CLASS = {
    ("People", "Person Count"): ("identity", True),
    ("People", "Gender Presence"): ("identity", True),
    ("People", "Distinct Individuals"): ("identity", True),
    ("People", "Identity Coherence"): ("identity", True),
    ("Action", "Action Person 1"): ("action", True),
    ("Action", "Action Person 2"): ("action", True),
    ("Anchor", "Absurd Element"): ("absurd", True),
    ("Anatomy", "Anatomical Fidelity"): ("anatomy", True),
    ("Composition", "Focal Point"): ("bland", False),
    ("Composition", "Memorability"): ("bland", False),
}

# fail class -> repair action, in escalation-priority order.
REPAIR_BY_CLASS = {
    "absurd": "reroll_full",
    "bland": "reroll_full",
    "identity": "reroll_inserts",
    "action": "reroll_inserts",
    "anatomy": "targeted_edit",
}
REPAIR_PRIORITY = ["reroll_full", "reroll_inserts", "targeted_edit"]

MAX_REPAIRS = 2  # verdicts allowed per image: 1 initial + MAX_REPAIRS


def load_brief_index(prompts_dir):
    """example_id -> brief record, joining output (anchor/inserts) with
    input (sentence texts) chunks under <prompts_dir>/{output,input}/."""
    prompts_dir = Path(prompts_dir)
    index = {}
    for out_file in sorted((prompts_dir / "output").glob("*_illu_b*.json")):
        chunk = out_file.stem
        lang = chunk.split("_")[0]
        in_file = prompts_dir / "input" / out_file.name
        sentences = {}
        if in_file.exists():
            for expr in json.load(open(in_file)):
                for ex in expr["examples"]:
                    sentences[ex["example_id"]] = ex
        for expr in json.load(open(out_file)):
            for var in expr["variations"]:
                eid = var["example_id"]
                sent = sentences.get(eid, {})
                index[eid] = {
                    "example_id": eid,
                    "expression_id": expr["expression_id"],
                    "idiom": expr["idiom"],
                    "lang": lang,
                    "chunk": chunk,
                    "anchor": expr["anchor"],
                    "inserts": var["inserts"],
                    "scene_adjust": var.get("scene_adjust") or "",
                    "en_text": sent.get("en_text", ""),
                    "target_text": sent.get("target_text", ""),
                }
    return index


def gender(slug):
    return "WOMAN" if slug in FEM else "MAN"


def build_prompt_text(rec):
    """Reconstruct the generation intent the judge scores against."""
    people = []
    for ins in rec["inserts"]:
        people.append(f"a {gender(ins['slug'])} who {ins['action']}")
    if len(people) == 1:
        people_line = f"Exactly ONE person is required: {people[0]}."
    else:
        people_line = (f"Exactly TWO people are required: {people[0]}; "
                       f"and {people[1]}. They are two different "
                       f"individuals.")
    parts = [
        f"Scene: {rec['anchor']['setting']}",
    ]
    if rec["scene_adjust"]:
        parts.append(f"Added prop: {rec['scene_adjust']}")
    parts += [
        people_line,
        ("Deliberate surreal element that must be visible: "
         f"{rec['anchor']['absurd_element']}."),
        ("Style: flat European ligne-claire comic. The small circular "
         "photo chip(s) in the bottom-right corner and the thin black "
         "outer border are compositing overlays added after generation "
         "— IGNORE them for every check; judge only the drawn scene."),
    ]
    if rec["en_text"]:
        parts.append(f'The image illustrates this sentence: "{rec["en_text"]}"')
    return "\n".join(parts)


def build_checklist(rec):
    """Return the checklist text for this brief, in the judge's
    '## Level2\\n- Level3: question' format."""
    ins = rec["inserts"]
    n = len(ins)
    genders = [gender(i["slug"]) for i in ins]
    lines = ["## People"]
    lines.append(
        f"- Person Count: Excluding the circular photo chip(s) in the "
        f"bottom-right corner, does the drawn scene contain exactly "
        f"{'ONE person' if n == 1 else 'TWO people'}? Score 0 if more or "
        f"fewer people appear.")
    if n == 1:
        lines.append(
            f"- Gender Presence: Is the person clearly a {genders[0]}?")
        if genders[0] == "WOMAN":
            coh = ("Is the woman free of contradictory identity features "
                   "such as a beard, moustache, or a second blended face?")
        else:
            coh = ("Does the man have a single coherent face and identity, "
                   "with no second blended face or merged features?")
        lines.append(f"- Identity Coherence: {coh}")
    else:
        g1, g2 = genders
        if g1 == g2:
            gp = (f"Are both people clearly {g1}s?")
        else:
            gp = (f"Is there exactly one {g1} and one {g2}?")
        lines.append(f"- Gender Presence: {gp}")
        lines.append(
            "- Distinct Individuals: Are they two clearly SEPARATE "
            "individuals, each with their own complete body and face — "
            "not merged, not sharing limbs or heads, and not blended "
            "into one person with mixed features (for example a woman "
            "with a beard)?")
    lines.append("## Action")
    for j, i in enumerate(ins):
        lines.append(
            f"- Action Person {j + 1}: Does the {gender(i['slug']).lower()} "
            f"perform this action: \"{i['action']}\"?")
    lines.append("## Anchor")
    lines.append(
        f"- Absurd Element: Is this element clearly visible in the scene: "
        f"\"{rec['anchor']['absurd_element']}\"?")
    lines.append("## Anatomy")
    lines.append(
        "- Anatomical Fidelity: Does every drawn person have exactly two "
        "arms, two legs, two hands, and one head, with no extra, missing, "
        "duplicated, or merged limbs or fingers? (Comic-style simplified "
        "hands are fine; wrong counts are not.)")
    lines.append("## Composition")
    lines.append(
        "- Focal Point: Does the image have a clear focal point and "
        "readable staging, rather than a cluttered or aimless layout?")
    lines.append(
        "- Memorability: Is the image visually striking and memorable "
        "rather than bland and generic?")
    return "\n".join(lines)


def build_user_prompt(rec):
    return USER_PROMPT_TEMPLATE.format(
        prompt=build_prompt_text(rec),
        level1_dim=LEVEL1_DIM,
        format_checklist=build_checklist(rec))


def extract_json(text):
    """Pull the first balanced JSON object out of judge output (thinking
    text and code fences tolerated). Returns dict or None."""
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = text.replace("```json", "```")
    if "```" in text:
        m = re.search(r"```(.*?)```", text, flags=re.S)
        if m:
            text = m.group(1)
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    return None


def flatten_scores(score_json):
    """{(level2, level3): score} with scores normalized to 0|1|2|'N/A'."""
    flat = {}
    if not isinstance(score_json, dict):
        return flat
    for l2, subs in score_json.items():
        if not isinstance(subs, dict):
            continue
        for l3, cell in subs.items():
            s = cell.get("score") if isinstance(cell, dict) else cell
            if isinstance(s, str) and s.strip().isdigit():
                s = int(s.strip())
            if s in (0, 1, 2):
                flat[(l2, l3)] = s
            else:
                flat[(l2, l3)] = "N/A"
    return flat


def classify(score_json, rec):
    """-> (verdict, fail_classes, repair_action, checks) where checks is
    {'Level2/Level3': score}. Unparseable/missing hard checks fail safe
    ('judge_error' verdict so the loop retries rather than repairs)."""
    flat = flatten_scores(score_json)
    if not flat:
        return "judge_error", [], None, {}
    n = len(rec["inserts"])
    expected = [k for k in CHECK_CLASS
                if not (n == 1 and k[1] in ("Distinct Individuals",))
                and not (n == 2 and k[1] in ("Identity Coherence",))
                and not (n == 1 and k[1] == "Action Person 2")]
    fail_classes = []
    soft_fails = 0
    checks = {}
    for key in expected:
        cls, hard = CHECK_CLASS[key]
        score = flat.get(key, None)
        checks["/".join(key)] = score if score is not None else "missing"
        if score == 0:
            if hard:
                if cls not in fail_classes:
                    fail_classes.append(cls)
            else:
                soft_fails += 1
    if soft_fails >= 2 and "bland" not in fail_classes:
        fail_classes.append("bland")
    verdict = "fail" if fail_classes else "pass"
    repair = None
    if fail_classes:
        actions = {REPAIR_BY_CLASS[c] for c in fail_classes}
        repair = next(a for a in REPAIR_PRIORITY if a in actions)
    return verdict, fail_classes, repair, checks


def load_partition(partition_file):
    """chunk name -> machine ('mac'|'fedora'). Chunks absent from the
    file default to 'fedora' (the night miner sweeps everything else)."""
    p = Path(partition_file)
    if not p.exists():
        return {}
    return json.load(open(p))


def owner_of(chunk, partition):
    return partition.get(chunk, "fedora")
