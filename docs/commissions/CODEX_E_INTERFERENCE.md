# Codex commission E: interference direction matrix + F4 contrast bank

> Work dir: /home/admin/projects/idiomatic-data/ — write ONLY inside
> its `interference/` subdirectory. This is personal-lesson-derived
> data and stays OUT of the public repo. Read-only context from the
> repo: docs/research/error-profiles/*.md, docs/commissions/
> ERROR_PROFILE_PROPOSAL.md (Phase 3 + outside-the-box #3),
> docs/GRAMMAR_STRATEGY.md §4 (F4 format; Pan 2025 evidence).
> Data inputs: errmine/personal_errors.jsonl, errmine/f3_ready_*.jsonl.

## Goal

The learner's #1 systemic weakness is cross-language interference
(54% of pt verbatim errors, 42% of es) with zero curriculum coverage.
Build the data layer for the F4 cross-language contrast deck.

## Tasks

1. **Direction matrix** (`interference/matrix.md` + `matrix.json`):
   from the registry rows where interference_source is set, compute
   source_lang × target_lang × category counts. Include per-cell top
   example pairs. State honestly where source attribution is
   uncertain (pan-Romance forms attributable to several languages).
2. **Contrast-pair bank** (`interference/f4_pairs_{target_lang}.json`):
   for each target language, the drillable contrast pairs — his
   attested confusion + the two languages' correct forms side by side:
   {"target_lang", "source_lang", "concept_en", "correct_target",
    "false_form" (what he says), "source_form" (the correct form in
    the source language that causes the leak), "category", "why",
    "occurrences", "attested": true|false}.
   Core = attested pairs from the registry (todavia/todavía,
   contento/contente, fato/feito, che/que, inserir/insertar...).
   Extend each attested pair's FAMILY with closely related
   high-frequency pairs the profiles imply (mark attested:false).
   Target ≥40 pairs for pt and es, ≥25 for fr and it, de only where
   Russian/English transfer pairs are attested.
3. **F4 card design proposal** (`interference/F4_DESIGN.md`): how the
   pairs become cards inside the FROZEN 14-field model (read
   idiomatic/grammar/apkg.py for the fields; no template changes
   possible): propose 2-3 concrete card shapes (e.g. front shows the
   concept + source-language form, learner produces the target form;
   or a same-frame minimal pair), field mapping, deck placement
   (cluster "10 Interferenze"-style per language vs one cross-language
   deck — argue ONE recommendation), verification path (answers come
   from the bank = deterministic), and a phased rollout suggestion.

## Rules

No git operations anywhere. No writes outside
/home/admin/projects/idiomatic-data/interference/. Verbatim forms from
the registry stay verbatim (diacritics intact). Machine-readable JSON
must parse; include a _meta header element with provenance + counts.
