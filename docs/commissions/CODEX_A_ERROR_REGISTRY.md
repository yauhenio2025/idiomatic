# Codex commission A: merged personal-error registry (all 5 languages)

> Substantial, hours-scale task. Work dir: `/home/admin/projects/idiomatic-data/errmine/`
> (OUTSIDE the public repo — this is personal lesson data and the output
> stays local). Read-only context from the repo:
> `docs/research/error-profiles/*.md`, `docs/GRAMMAR_STRATEGY.md` §3-4,
> `docs/commissions/ERROR_PROFILE_PROPOSAL.md`.

## Goal

One validated, deduplicated, categorized registry of every error this
learner has made in 5+ years of lessons, as
`/home/admin/projects/idiomatic-data/errmine/personal_errors.jsonl` —
the data spine for the F3 error-correction format, error-aware
generation prompts, the F4 interference deck, and the Wave-5 planner
prior.

## Inputs (all in the work dir)

- `xlsx_{fr,pt,es,de,it}.jsonl` — 10,314 teacher rows 2019-2022:
  {correct, error (null = vocab-expansion, not an error), vocab/use/pron
  booleans, translation, lang, date}. The corrected element usually sits
  in (parentheses) or [brackets] inside `correct`.
- `teachee_{fr,pt,es,de}.jsonl` — 3,502 lesson notes 2022-2024:
  {deck, fields:[english_prompt, target_answer_with_IPA,...]}. Mostly
  vocab-teaching; a minority are error remediations — detect by content.
- `anki_errors_decks.json` — imported copy of the xlsx (cross-check
  only; NEVER double-count against xlsx rows).

## Output schema (one JSON object per line)

{"id": stable int, "lang": "fr|pt|es|de|it",
 "kind": "error|reteach|vocab_gap",   // error = attested wrong form;
                                       // reteach = same item re-taught
                                       // across eras without recorded
                                       // wrong form; vocab_gap = pure
                                       // vocabulary expansion
 "wrong": str|null, "right": str, "gloss_en": str|null,
 "category": one of the CONTROLLED VOCABULARY below,
 "subcategory": free text,
 "why": one-line rule in English,
 "interference_source": "es|pt|it|fr|en|ru|null",
 "occurrences": int,                  // merged count across sources
 "first_seen": "YYYY-MM-DD"|null, "last_seen": "YYYY-MM-DD"|null,
 "sources": ["xlsx"|"teachee", ...],
 "unit_hint": existing-or-proposed unit key from the profiles, or null,
 "confidence": "high|medium|low"}

CONTROLLED CATEGORY VOCABULARY (align with the five profiles §2):
preposition_selection, verb_prep_regime, gender, agreement,
article_quantifier, word_order, negation, pronoun_clitic, relative,
tense_selection, verb_morphology, subjunctive, passive, case,
adjective_ending, light_verb_collocation, interference_lexical,
interference_morphological, false_friend, fixed_phrase, derivation,
numbers_dates, pronunciation, vocabulary.

## Method requirements

1. Parse the bracket/parenthesis convention in `correct` to isolate the
   corrected element; reconstruct full wrong sentence where `error`
   holds only the wrong fragment.
2. Dedup WITHIN and ACROSS eras by (lang, normalized wrong→right pair);
   a recurrence increments `occurrences` and extends first/last_seen —
   recurrence data is the fossilization signal, never discard it.
3. Categorize EVERY row (including the ~3,615 vocab rows — kind=
   vocab_gap with category=vocabulary and a subcategory theme). Detect
   Teachee error-remediations vs plain vocab by content.
4. Second pass: re-read your own output per language and fix
   miscategorizations; note systematic uncertainty in the report.
   Cross-check totals against the per-language profile counts in the
   repo (docs/research/error-profiles/) — flag discrepancies >10% per
   category in the report rather than silently matching them.
5. Deterministic + reproducible: write the pipeline as
   `build_registry.py` in the work dir (runnable end-to-end); LLM-style
   judgment calls should be embedded as explicit rule tables/word lists
   in the script where feasible.

## Deliverables (all in the work dir, NOT committed to the repo)

1. `personal_errors.jsonl` — the registry.
2. `build_registry.py` — reproducible builder.
3. `REGISTRY_REPORT.md` — counts by lang×kind×category, top-50
   fossils by occurrences, interference direction matrix
   (source_lang × target_lang × category, counts), discrepancies vs
   the five profiles, known limitations.
4. `f3_ready_{lang}.jsonl` — per language, the kind=error entries with
   confidence=high, ready for F3 card generation (superset of the
   profiles' 40-pair seeds; aim for everything defensible, not a
   round number).

## Hard rules

- Never write anything under `/home/admin/projects/idiomatic/` (the
  public repo). No git operations anywhere.
- Do not invent errors: `wrong` must be attested in the sources (or
  null for reteach/vocab_gap).
- Keep diacritics/casing verbatim from sources.
