# Codex commission K: promote the four Romance planned units to live

> Work dir: /home/admin/projects/idiomatic-wt/promotions (isolated
> worktree). No git ops; `uv run pytest tests/` green. Read:
> curriculum.py (PLANNED_UNITS + how es_clitics_* / es_por_para are
> built — these are the templates), generate.py (blind verification,
> answer_set, bank plumbing), the evidence: docs/research/
> error-profiles/{fr,pt,it,es}.md curriculum-mapping sections, and
> docs/commissions/ERROR_PROFILE_PROPOSAL.md.

## Units to implement (move from PLANNED_UNITS to real Topics; keys
are LIVE tags — never rename)

1. `fr_pronoms_y_en` (cluster stays "4 Pronoms"): y/en cloze,
   answer_set [y, en], blind K=3. Evidence: là→y 22×, missing en 11×.
   Guidance must force antecedent recoverability (the thing y/en
   stands for appears in the sentence/preceding clause).
2. `pt_clitic_placement` ("4 Clíticos"): BRAZILIAN placement —
   infinitive+enclisis (-á-lo/-ê-lo/-i-lo), comigo/conosco, proclisis
   defaults. Mixed answer set: build a small bank
   (grammar/data/pt_clitic_placement.json, ~40 frames from the pt
   profile's attested errors: procuraros→procurá-los, com nós→conosco)
   + blind K=3. BR only — tu/vós forms rejected.
3. `it_clitici_ci_ne` ("4 Clitici"): ci/ne cloze, answer_set
   [ci, ne, ce ne], blind K=3; include the procomplementari the 2019
   remedial block drilled (farcela, cavarsela, fregarsene) as frames
   in a small bank (grammar/data/it_clitici_ci_ne.json, ~40 entries).
4. `es_ser_estar` ("7 Ser/Estar"): SMALL scope per the user decision —
   estar+participle/state focus (1 recorded error in 6 years; this
   unit exists for coverage, not remediation). answer_set = forms of
   ser/estar (present + imperfect + preterite 3s/3p is enough), blind
   K=3, target_size stays 12; note in guidance that items must make
   the ser/estar choice the ONLY decision.

Mechanics: remove the four from PLANNED_UNITS (the DB seeding
promotes planned→active automatically); GERMAN planned units stay
planned (commission L owns them). New banks are generated content —
they contain NO personal data, so repo data files are fine; follow
es_verb_prep.json quality conventions (_meta header, validation
notes). Tests per unit: bank loads (where present), prompt builds,
verify accepts a correct item and rejects a wrong one; seed-row count
updated (63 - 4 planned + 4 active = still 63 total rows).
