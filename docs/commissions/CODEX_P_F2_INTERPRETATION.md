# Codex commission P: F2 structured-input format — design + item banks

> Work dir: /home/admin/projects/idiomatic (main repo). Write ONLY
> under `idiomatic/grammar/data/f2_*.json` + `docs/commissions/
> unit-specs/F2_DESIGN.md`. No git ops, NO code changes (the
> implementing session wires it later). Read: docs/GRAMMAR_STRATEGY.md
> §4 F2 + §3b (VanPatten PI, Henshaw 2012 — the FORM is the only cue
> to meaning), the error profiles' tense-SELECTION findings
> (pt fiz/fez person confusion, pt futuro-subjuntivo selection,
> fr passé-composé/imparfait, it passato-prossimo/imperfetto,
> es preterite/imperfect), idiomatic/grammar/apkg.py (frozen model).

## Goal

F2 = interpretation cards: the learner READS a form and must extract
what it means (aspect, person, completedness) — the complement to
production cloze. Never built. Design it inside the frozen model +
build the seed banks.

## Deliverables

1. **F2_DESIGN.md**: card shape inside the 14 frozen fields (front =
   sentence + a meaning QUESTION with 2-3 labeled options; answer =
   the correct option + why the FORM decides it), fmt='f2' conventions,
   verification approach (bank-attested items need none; generated
   variants need a design — propose one), how self-grading works with
   options on a think-then-reveal card, and which existing units each
   bank feeds (interleaving per Pan 2019: F2 items should MIX with the
   production cards of the same cluster, not form separate decks).
2. **Five banks** (~50 items each, [{"_meta": …}, …] convention):
   - f2_es_pret_impf.json — "¿Terminada o habitual?" pairs
   - f2_pt_person_aspect.json — fiz/fez + perfeito/imperfeito reading
   - f2_fr_pc_imparfait.json
   - f2_it_pp_imperfetto.json (+ passato remoto recognition rows)
   - f2_de_case_roles.json — who-does-what-to-whom via case morphology
     (Der Hund, den der Mann sieht … — subject or object?)
   Each item: {sentence, question, options, answer, why, contrast_form
   (the minimal-pair variant that flips the meaning)}. Linguistically
   impeccable; one unambiguous answer; news/professional register.
