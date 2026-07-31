# F3 personal-error cards

F3 turns teacher-attested rows from `personal_errors` into ordinary verified
`grammar_items` with `fmt='f3'`. Each language has one appended, active
curriculum topic in its numbered “9 … errors” cluster. These topics use the
warning symbol and localized correction prompt, but are excluded from LLM
generation because their source material is already attested.

Candidate suitability, ranking, and field mapping are pure functions. Clean
single-word corrections remain valid—false friends and derivational errors are
useful cards—while empty and bracket-mangled source fragments are skipped.
Eligible rows are active, high-confidence errors without an `f3_item_id`, then
ranked by occurrences and recency. Conversion stores the new grammar item ID
back on the source row so reruns cannot duplicate it; a sentence-uniqueness
collision is logged and reported as skipped while selection continues to the
next ranked usable row. The transaction rechecks the source pair and its
explanation fields under a row lock before inserting, avoiding stale cards
during a concurrent registry refresh.

The frozen Anki model, GUID formula, templates, and 14 fields are unchanged.
The wrong form goes in `Sentence`, the correction in `Answer` and
`SentenceFull`, the source gloss (or category) in `GlossEn`, and the attested
explanation in `Why`. F3 audio speaks the correction and corrected phrase. The
admin conversion endpoint performs only this fast DB work and does not rebuild
the deck automatically; the existing grammar rebuild remains a separate,
intentional volume-control step.

The F3 tests are deterministic and database-free. They cover suitability,
ordering, `f3_item_id` deduplication, all five curriculum mappings, literal
frozen-model metadata, front/back field rendering, and corrected F3 audio.
