# Commission: Exercises 2.0 pilot — ES CONNECTING (42 rich notes)

> For the codex CLI agent. Context: docs/research/legacy-excercises-audit.md.
> This is the approved-format pilot for reviving a 2023-era exercise corpus.
> The learner is an advanced (C1+) speaker of Spanish who also studies
> Portuguese, Italian, French and German, and works professionally in
> tech criticism / geopolitics / media commentary. Target variety:
> **European Spanish** (flag meaningful LatAm divergences, don't mix them in).

## Input

`idiomatic/grammar/data/exercises2/es_connecting_pilot_input.json` —
42 objects `{id, en, old_back}`. `en` is an English discourse
connector or argumentative move. `old_back` is the 2023 machine
translation: **reference only, known to be unreliable** (the audit found
mistranslations in this corpus). Never copy it without independently
deciding it is right. If it is wrong or unnatural, ignore it.

## Output 1 — `idiomatic/grammar/data/exercises2/es_connecting_pilot.json`

A JSON array, one object per input item, ALL fields present:

| field | content |
|---|---|
| `id` | copy from input |
| `en` | copy from input (trim trailing commas/ellipses only if senseless) |
| `category` | one of: `result`, `concession`, `contrast`, `condition`, `reformulation`, `generalization`, `stance`, `structuring`, `addition` |
| `es_main` | the single best Spanish rendering an educated native would use in serious speech/writing. Not necessarily the most literal one. |
| `es_alts` | 0–3 genuinely interchangeable alternatives (array of strings). Only forms a native would actually use; empty array is fine. |
| `register` | one line: where `es_main` sits (formal/neutral/colloquial; spoken vs written; e.g. "written-formal; in speech prefer X") |
| `trap` | one line on a REAL pitfall for this learner — an EN/PT/IT/FR interference error, a false friend, or a legacy-gloss error worth un-learning (e.g. why a tempting literal rendering is wrong). Empty string if nothing genuine. Never invent a trap. |
| `example_es` | ONE sentence (18–30 words) using `es_main` naturally, in the learner's professional register: tech criticism, platform regulation, geopolitics, Cold War history, media. It must read like a sentence from El País opinion or a policy essay, not a textbook. |
| `example_en` | faithful English translation of `example_es` |
| `cloze` | `example_es` with the connector replaced by `{{c1::…}}` (Anki cloze syntax; cloze exactly the connector string as it appears in the sentence) |
| `note` | anything the reviewer must know: uncertainty, divergence from `old_back` and why, LatAm variant if meaningful. Empty string if nothing. |

### A fully worked example (quality bar — match this)

```json
{
  "id": "esc10",
  "en": "Be that as it may",
  "category": "concession",
  "es_main": "Sea como fuere",
  "es_alts": ["Sea como sea", "En cualquier caso"],
  "register": "Sea como fuere is written-formal (fuere = fossilized future subjunctive); in speech, Sea como sea is the natural choice.",
  "trap": "The legacy gloss 'Aunque' is wrong: aunque subordinates a clause, while Sea como fuere is a free-standing discourse move that concedes everything before it and pivots.",
  "example_es": "Sea como fuere, la comisión no puede seguir aplazando una regulación seria de los mercados de datos mientras las plataformas consolidan su posición dominante.",
  "example_en": "Be that as it may, the commission cannot keep postponing serious regulation of data markets while the platforms consolidate their dominant position.",
  "cloze": "{{c1::Sea como fuere}}, la comisión no puede seguir aplazando una regulación seria de los mercados de datos mientras las plataformas consolidan su posición dominante.",
  "note": "Diverges from old_back ('Aunque'), which mistranslates the item."
}
```

## Output 2 — `idiomatic/grammar/data/exercises2/es_connecting_pilot_preview.md`

Human review document: one section per item showing all fields readably
(EN → main + alts, register, trap, example with translation). At the top,
a summary block: how many items diverge materially from `old_back`, and a
list of those ids with a one-line reason each. At the bottom, a list of
items you are least confident about (min 3 — be honest, not modest).

## Verification pass (mandatory, after drafting all 42)

Re-walk every item as a hostile reviewer, in a separate pass:

1. Equivalence: does `es_main` mean what `en` means, in the discourse
   function sense (not word-by-word)? Connectors are function words —
   matching function beats matching lexemes.
2. Naturalness: would a native columnist actually write `example_es`?
   No translationese, no calques.
3. Register coherence: `example_es` register matches the `register` line.
4. Cloze well-formed: `{{c1::…}}` wraps exactly the connector, sentence
   still grammatical when the cloze is blanked.
5. Alternatives really interchangeable in the example sentence.
6. JSON validity + schema: run
   `python3 -c "import json;d=json.load(open('idiomatic/grammar/data/exercises2/es_connecting_pilot.json'));assert len(d)==42;ks={'id','en','category','es_main','es_alts','register','trap','example_es','example_en','cloze','note'};[k for x in d for k in (ks-set(x),) if k and 1/0]"`
   and make it pass.

Record fixes made during this pass in the item's `note` field
("self-review: changed X to Y because…").

## Hard rules

- Do NOT run any git command. Do not commit, stage, or push.
- Write ONLY the two output files listed above. No code changes.
- No placeholder content: every field authored for every item.
- Where you are genuinely unsure, say so in `note` — an honest flag is
  worth more than a confident guess.
