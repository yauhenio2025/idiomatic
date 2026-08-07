#!/usr/bin/env python3
"""Mechanical gate for illustration-prompt chunks (see
docs/commissions/ILLUSTRATION_PROMPTS_COMMISSION.md). Usage:
  illu_prompts_gate.py <output.json> [more.json...]
Exit 0 = all pass. Prints one line per violation. Over-flagging is by
design — a human (or the orchestrator) adjudicates NEAR flags by reading.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

CAST = {
    "es": {"penelope_cruz", "javier_bardem", "cristina_kirchner", "rosalia",
           "nadia_calvino", "pedro_sanchez"},
    "de": {"juju", "capital_bra", "angela_merkel", "luisa_neubauer",
           "sahra_wagenknecht", "jurgen_klopp"},
    "fr": {"marion_cotillard", "timothee_chalamet", "catherine_deneuve",
           "kylian_mbappe", "christine_lagarde", "emmanuel_macron"},
    "it": {"elodie", "fedez", "sophia_loren", "jannik_sinner",
           "giorgia_meloni", "roberto_saviano"},
    "pt": {"anitta", "wagner_moura", "dilma_rousseff", "kevinho",
           "marina_silva", "fernando_haddad"},
}
SHARED = {"james_gandolfini", "edie_falco", "michael_imperioli",
          "lorraine_bracco", "steven_van_zandt", "brian_cox", "sarah_snook",
          "kieran_culkin", "jeremy_strong", "matthew_macfadyen",
          "nicholas_braun", "j_smith_cameron", "karl_marx",
          "friedrich_engels", "jean_paul_sartre", "simone_de_beauvoir",
          "john_lennon", "paul_mccartney", "christiane_amanpour"}

FIGURATIVE = re.compile(
    r"\blike a\b|\blike an\b|\bas if\b|\bsymboli|\bmetaphor|\brepresent"
    r"|\bevok", re.IGNORECASE)
TEXTY = re.compile(
    r"\bsign\b|\blabel|\bletter|\bword\b|\bwords\b|\btext\b|\blogo|\bbrand"
    r"|\bwriting\b|\bwritten\b|\bcaption|\bposter with\b", re.IGNORECASE)
STYLE = re.compile(
    r"ligne claire|comic style|photorealist|watercolor|oil painting"
    r"|pixel art|anime\b|cartoon style", re.IGNORECASE)
IDENTITY = re.compile(
    r"reference (image|photo|sheet)|copy (his|her|their) (face|exact)"
    r"|the (man|woman|person) from the", re.IGNORECASE)


def gate(path):
    errs = []
    E = errs.append
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [f"{path}: unreadable JSON: {e}"]
    m = re.match(r"([a-z]{2})_illu_b\d+", Path(path).stem)
    lang = m.group(1) if m else ""
    allowed = CAST.get(lang, set()) | SHARED
    inp = Path(str(path).replace("/output/", "/input/"))
    by_id = {}
    if inp.exists():
        for x in json.loads(inp.read_text(encoding="utf-8")):
            by_id[x["expression_id"]] = x
    slug_use = Counter()
    shared_use = 0
    for i, x in enumerate(data):
        tag = f"{Path(path).name}[{i}] expr {x.get('expression_id')}"
        a = x.get("anchor") or {}
        for field in ("semantic_hook", "setting", "absurd_element"):
            if not str(a.get(field) or "").strip():
                E(f"{tag}: anchor.{field} empty")
        cast = a.get("cast") or []
        if not (1 <= len(cast) <= 2):
            E(f"{tag}: anchor.cast must have 1-2 slugs")
        for s in cast:
            if s not in allowed:
                E(f"{tag}: unknown/foreign slug {s!r}")
            slug_use[s] += 1
            if s in SHARED:
                shared_use += 1
        blob = " ".join(str(a.get(k) or "") for k in
                        ("semantic_hook", "setting", "absurd_element"))
        if FIGURATIVE.search(a.get("setting") or ""):
            E(f"{tag}: figurative language in setting "
              f"({FIGURATIVE.search(a['setting']).group(0)!r})")
        if TEXTY.search(blob):
            E(f"{tag}: text-in-image request ({TEXTY.search(blob).group(0)!r})")
        if STYLE.search(blob):
            E(f"{tag}: style words belong to the renderer")
        src = by_id.get(x.get("expression_id"))
        vs = x.get("variations") or []
        if src:
            want = [ex["example_id"] for ex in src["examples"]]
            got = [v.get("example_id") for v in vs]
            if want != got:
                E(f"{tag}: variation example_ids {got} != input {want}")
        for j, v in enumerate(vs):
            ins = v.get("inserts") or []
            if not (1 <= len(ins) <= 2):
                E(f"{tag}.var[{j}]: needs 1-2 inserts")
            for k in ins:
                if k.get("slug") not in cast:
                    E(f"{tag}.var[{j}]: insert slug {k.get('slug')!r} "
                      f"not in anchor.cast")
                act = str(k.get("action") or "")
                if not act.strip():
                    E(f"{tag}.var[{j}]: empty action")
                if FIGURATIVE.search(act):
                    E(f"{tag}.var[{j}]: figurative language in action "
                      f"({FIGURATIVE.search(act).group(0)!r})")
                if STYLE.search(act) or IDENTITY.search(act):
                    E(f"{tag}.var[{j}]: style/identity words in action")
    if data:
        top, n = slug_use.most_common(1)[0] if slug_use else ("", 0)
        if n > max(2, len(data) * 0.25):
            E(f"{Path(path).name}: slug {top!r} overused ({n}/{len(data)} "
              f"expressions)")
        if shared_use > max(1, len(data) // 6):
            E(f"{Path(path).name}: shared-wing overuse ({shared_use} uses)")
    return errs


def main():
    total = 0
    for p in sys.argv[1:]:
        errs = gate(p)
        for e in errs:
            print("FAIL", e)
        if not errs:
            print("PASS", p)
        total += len(errs)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
