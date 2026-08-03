# Commission: Italian rebuild of the legacy exercise corpus (per-chunk)

> For the codex CLI agent. One invocation processes ONE chunk file, named
> in the invocation prompt. Context: docs/research/legacy-excercises-audit.md
> — the 2023 "Italian" exercise deck was discovered to be a byte-identical
> copy of the French deck. Italian never existed. This commission creates it.

## Input

`idiomatic/grammar/data/exercises2/it_rebuild/input/<chunk>.json` — an
array of `{id, en, refs}`. `en` is the English source prompt. `refs`
holds the existing translations of the same prompt in up to four
languages (`es`, `fr`, `pt`, `de`) — use them to disambiguate sense,
register, and grammatical structure. They are aids, not sources of
truth: `en` is the source of truth, and the refs themselves have a known
~5-10% defect rate.

## Output

`idiomatic/grammar/data/exercises2/it_rebuild/output/<chunk>.json` —
same order, one object `{id, en, it, note}` per input item. `it` is the
Italian rendering. `note` is "" unless something must be flagged
(ambiguous prompt, defective refs, genuine uncertainty). Every input id
must appear exactly once.

## Authoring rules

- Italian a native editor would write. Function-equivalence over
  word-for-word: connectors get the Italian connector with the same
  discourse job; idioms get the Italian idiom.
- Topic conventions (infer the pattern from the refs of the chunk):
  - vocab topics (`big_tech_vocab`, `cold_war_vocab`, `fancy_vocab`,
    `geopolitics`): keep the article when the prompt has "the X"
    (il/lo/la/l'/i/gli/le), mirroring what es/fr do; definition-style
    prompts ("Term - definition…") keep the "Termine - definizione…" shape.
  - `commands`: formal Lei imperative, matching the usted/vous register
    of the refs (negative commands: "Non le parli…", not tu-forms).
  - `conditionals` / `tenses`: reproduce the tense architecture of the
    English (counterfactual → congiuntivo trapassato + condizionale
    passato, etc.); check how es/fr structured it.
  - `pronouns` / `relfexive`: clitic placement and combined clitics are
    the drilled feature — get them exactly right (glielo, se ne, ci si).
- If the English prompt is awkward machine-English ("the Technological
  solutionism"), translate the evident intent; flag truly broken prompts
  in `note` rather than skipping them.

## The one catastrophic failure mode

The legacy deck shipped French labeled as Italian. Therefore:
- NEVER output French. After drafting the full chunk, do a dedicated
  pass over every single `it` value and confirm it is Italian — watch
  for French articles (le/la/les/du/des used the French way), French
  spelling (é-participles, -tion, -ment adverbs where Italian has
  -zione/-mente), and wholesale French phrases.
- No `it` value may be identical to the chunk's `fr` ref for that item.
  (Rare legitimate one-word overlaps exist; if truly unavoidable,
  explain in `note`.)

## Verification pass (mandatory)

After drafting: re-walk each item checking (1) meaning matches `en`,
(2) the topic convention above is respected, (3) the French check just
described, (4) JSON validity — run
`python3 -c "import json,sys;i=json.load(open(sys.argv[1]));o=json.load(open(sys.argv[2]));assert [x['id'] for x in i]==[y['id'] for y in o];assert all(set(y)=={'id','en','it','note'} and y['it'].strip() for y in o)" <input> <output>`
with the real paths and make it pass. Record self-corrections in `note`.

## Hard rules

- No git commands. Write ONLY the single output file for your chunk.
- Every item authored; no placeholders, no skips.
- Honest flags in `note` beat confident guesses.
