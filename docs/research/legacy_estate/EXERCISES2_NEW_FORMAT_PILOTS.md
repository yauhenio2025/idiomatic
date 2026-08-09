# Exercises 2.0 new-format pilots — owner gates V1, V2, and P1

Status: **OWNER VERDICTS RECORDED 2026-08-09 — V1, V2, and P1 all approved
verbatim; bulk staging landed the same day (plans `wave4`/`wave5`/`wave6`).
See the dated OWNER VERDICT section below.**

The static review packet is
[`EXERCISES2_NEW_FORMAT_PILOTS.html`](EXERCISES2_NEW_FORMAT_PILOTS.html).
It renders the proposed front and back of every retained card, the full
triage (including drop reasons), source hashes, and the local-Qwen-only audio
placeholders. It does not build an APKG, call TTS, deliver a deck, or imply an
owner verdict.

## Gate summary

| Gate | Commissioned slice | Inputs | Keep / drop | Final gate | Bulk state |
|---|---|---:|---:|---|---|
| V1 | ES `FANCY_VOCAB` generic vocabulary | 30 | 14 / 16 | pass | approved 2026-08-09 — staged (`wave4`) |
| V2 | ES `GEOPOLITICS` term–definition | 30 | 30 / 0 | pass | approved 2026-08-09 — staged (`wave5`) |
| P1 | PT `BIG_TECH_PHRASES` shadowing | 30 | 30 / 0 | pass | approved 2026-08-09 — staged (`wave6`) |

The source manifests also pass byte-for-byte staging checks and the committed
cross-topic source report remains current at 20 exact-English groups. V1
correctly drops the specialist-topic copies of `Disruption` and `Ideology`.

## Independent linguistic audits

### V1 — generic vocabulary

All 30 rows were reviewed against the vocabulary addendum. Headword form,
articles/government, sense, alternatives, European-Spanish usage, example
length, translation, cloze reduction, and triage were checked. Three concrete
repairs were made:

- `it_fancy_vocab_095`: separated the Italian spelling interference from the
  different French accent-placement risk.
- `it_fancy_vocab_100`: distinguished grammatical-gender transfer from
  spelling transfer across the learner's languages.
- `it_fancy_vocab_102`: replaced a strained advertising-funded innovation
  phrase with native `paradigma tecnológico basado en la publicidad` and
  updated its translation, cloze, and audit note.

One deliberately empty trap remains; the format contract prefers an honest
empty field to an invented interference claim.

### V2 — term and corrected definition

All 30 terms, corrected Spanish definitions, examples, translations, clozes,
register labels, traps, and triage rows were reviewed. Eleven note rows and
one triage reason were repaired. Material changes include:

- removing unsafe near-synonym alternatives for accommodative monetary policy
  and black-swan events;
- treating the Belt and Road Initiative as the framework under which projects
  were financed, rather than as the financing agent;
- correcting unnatural or imprecise language for ocean-economy employment,
  capital controls, methane-reduction targets, and currency intervention;
- defining debt-trap diplomacy in terms of a creditor knowingly extending
  foreseeably unrepayable loans while retaining its disputed, accusatory
  status;
- widening digital currency beyond a mandatory public/private issuer;
- recording that emerging-market membership has no single official
  definition; and
- defining energy security as the capacity to guarantee sufficient,
  continuous, affordable supply, with resilience attributed to sources and
  infrastructure.

The remaining caveats are visible in the cards: `blue economy` is used in its
predominant ocean/coastal sense; debt-trap diplomacy is contested; digital
currency and digital sovereignty boundaries vary; emerging-market criteria
are institution-dependent; and `new Cold War` remains an attributed analogy.

### P1 — long-frame shadowing

All 30 Brazilian-Portuguese frames, reusable focus spans, cues, register
guidance, traps, and triage rows were reviewed. Three repairs were made:

- `it_big_tech_phrases_009`: narrowed `platform economy` to the source's
  gig-work sense with `economia de bicos`.
- `it_big_tech_phrases_011`: replaced ambiguous `sua adoção` with
  `a adoção dessa tecnologia`.
- `it_big_tech_phrases_024`: replaced generic stricter rules with the more
  precise `uma regulamentação mais rigorosa`.

Two semantic choices are intentionally left visible for owner review:
`pressão regulatória` is broader than “regulatory scrutiny” in row 003, and
`mecanismos de verificação de conteúdo` interprets the ambiguous “content
checks” in row 014. The length of the selected focus spans is itself part of
the P1 format verdict.

## Owner verdicts required

No bulk authoring starts until the corresponding answer is explicit:

1. **V1:** approve, revise, or reject the generic headword + production/cloze
   treatment for `FANCY_VOCAB`, `BIG_TECH_VOCAB`, and `COLD_WAR_VOCAB`.
2. **V2:** approve, revise, or reject the separate term–definition treatment,
   including whether the corrected target-language definition should freeze
   in the existing `Note` field for production.
3. **P1:** approve, revise, or reject the full-sentence rendering, selected
   focus spans, and the separate `Listen & Shadow` / `Cue & Produce` model.
   A representative phrase sample remains blocked until the already-delivered
   mixed-language local-Qwen pilot receives its listening verdict.

## OWNER VERDICT (2026-08-09)

> this looks good to me too - all three formats

All three gates closed as approvals, verbatim and without revisions:

1. **V1 approved** — the generic headword + production/cloze treatment ships
   for `FANCY_VOCAB`, `BIG_TECH_VOCAB`, and `COLD_WAR_VOCAB`.
2. **V2 approved** — the term–definition treatment ships for `GEOPOLITICS`,
   with the corrected target-language definition recorded in `note` exactly
   as piloted.
3. **P1 approved** — the full-sentence rendering, the selected focus spans,
   and the separate `Listen & Shadow` / `Cue & Produce` draft model ship for
   `BIG_TECH_PHRASES`.

Consequence: bulk staging was commissioned and landed the same day — plans
`wave4` (`FANCY_VOCAB`, 582/lang → 75 chunks), `wave5` (`BIG_TECH_VOCAB` +
`COLD_WAR_VOCAB` + `GEOPOLITICS`, 517/lang → 70 chunks), and `wave6`
(`BIG_TECH_PHRASES`, 90/lang → 15 chunks) in `tools/x2_wave_pipeline.py`,
staged as 160 forty-row chunk inputs with schema-v2 manifests under
`idiomatic/grammar/data/exercises2/batches/`. Authoring proceeds through
`EXERCISES2_BATCH_COMMISSION.md` plus the vocabulary and BIG_TECH_PHRASES
addenda. The committed duplicate doctrine stands: the 20 non-preferred
`FANCY_VOCAB` exact-EN copies stay staged, are flagged per chunk in the
`wave4` manifest, and are triage-dropped during authoring unless the
linguistic audit documents a distinct sense. Build and voicing remain
separate downstream gates of the normal Exercises 2.0 pipeline.

## Reproduction

```text
uv run python tools/x2_batch_gate.py es_fancy_vocab_pilot_b01 es_geopolitics_pilot_b01 pt_big_tech_phrases_pilot_b01
uv run python tools/x2_wave_pipeline.py stage vocab-pilot --check
uv run python tools/x2_wave_pipeline.py stage geopolitics-pilot --check
uv run python tools/x2_wave_pipeline.py stage phrases-pilot --check
uv run python tools/x2_wave_pipeline.py duplicate-report --check
uv run python tools/x2_pilot_preview.py --output docs/research/legacy_estate/EXERCISES2_NEW_FORMAT_PILOTS.html
```

Final review-packet SHA-256:
`5e387d89637e3f532c979f4e5a836fd1d7e767754e9ebc44d2f6be0a195ae5df`.
