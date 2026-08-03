# Commission: Exercises 2.0 batch authoring (per-chunk, any language)

> For the codex CLI agent. One invocation processes ONE chunk file, named in
> the invocation prompt. This scales the approved ES CONNECTING pilot
> (docs/commissions/EXERCISES2_PILOT_COMMISSION.md — read it first; its
> quality bar, worked example, and verification stance apply in full) to the
> rest of the legacy corpus. The learner profile is unchanged: advanced (C1+)
> in es/pt/fr/it/de, professional register = tech criticism / geopolitics /
> media. Target varieties: European Spanish, Brazilian Portuguese, standard
> France French, standard German.

## Input

`idiomatic/grammar/data/exercises2/batches/input/<chunk>.json` — an array of
`{id, en, old_back}`. The chunk filename encodes the target language and
topic (`pt_connecting_b02.json` → lang `pt`, topic `connecting`). `old_back`
is the unreliable 2023 gloss: reference only, never copy without deciding
independently that it is right.

## Step 1 — Triage every item

The legacy list was scraped indiscriminately; not every item deserves a card.
For each input item decide `keep` or `drop`:

- **drop — trivial**: any C1 learner already owns it (bare "And", "Also",
  "First", "Of course", single transparent adverbs with nothing to teach).
- **drop — duplicate**: same discourse function as another KEPT item in this
  chunk with nothing distinct to teach; keep the best of the family and list
  the dropped variants as `alts` on the kept note where they genuinely fit.
- **drop — broken**: prompt is not a usable English item (self-referential
  scraps, orphaned fragments).
- **keep** everything with real teaching value: marked/formal connectors,
  items where the obvious literal rendering is wrong, argumentative frames,
  anything whose legacy gloss was defective (fixing it IS the value).

Expect to keep roughly half to two-thirds — but follow the material, not a
quota, and never drop an item to save work.

## Step 2 — Author rich notes for every kept item

Schema per note (generalized key names — NOT the pilot's `es_*` spelling):

```json
{
  "id": "<copy from input>",
  "en": "<copy from input>",
  "category": "result|concession|contrast|condition|reformulation|generalization|stance|structuring|addition",
  "tl": "<single best rendering>",
  "alts": ["…"],
  "register": "<one line>",
  "trap": "<one line or empty — real pitfalls only, never invented>",
  "example_tl": "<ONE 18-30 word sentence, professional register, reads like a native columnist>",
  "example_en": "<faithful translation>",
  "cloze": "<example_tl with {{c1::…}} around the connector; multi-part frames wrap each fixed arm in its own {{c1::…}}>",
  "note": "<uncertainty / material divergence from old_back / self-review record, or empty>"
}
```

`cloze` must reduce exactly to `example_tl` when the `{{c1::…}}` wrappers are
unwrapped — the builder enforces this. Language-specific interference traps
should target THIS learner: es↔pt↔it↔fr cross-contamination and en calques.

## Output — two files

1. `idiomatic/grammar/data/exercises2/batches/output/<chunk>_notes.json` —
   array of authored notes (kept items only, input order).
2. `idiomatic/grammar/data/exercises2/batches/output/<chunk>_triage.json` —
   array of `{id, en, verdict: "keep"|"drop", reason}` covering EVERY input
   item (one line each; for keeps, reason may be "").

## Verification pass (mandatory)

Re-walk every authored note as a hostile reviewer (equivalence, naturalness,
register coherence, cloze well-formedness, alternatives truly
interchangeable, trap factually true). Then run and pass:
`python3 -c "import json,sys;n=json.load(open(sys.argv[1]));t=json.load(open(sys.argv[2]));i=json.load(open(sys.argv[3]));import re;assert {x['id'] for x in i}=={y['id'] for y in t};k={y['id'] for y in t if y['verdict']=='keep'};assert {x['id'] for x in n}==k;[(x['cloze'],x['example_tl']) for x in n if re.sub(r'\\{\\{c1::(.*?)\\}\\}',r'\\1',x['cloze'])!=x['example_tl'] and 1/0]" <notes> <triage> <input>`
with the real paths. Record self-corrections in `note`.

## Hard rules

- No git commands. Write ONLY the two output files for your chunk.
- Every kept item fully authored — no placeholders.
- Honest uncertainty flags in `note` beat confident guesses.
