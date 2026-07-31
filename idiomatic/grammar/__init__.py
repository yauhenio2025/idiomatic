"""Grammar-exercise pipeline.

Strategy and research: docs/GRAMMAR_STRATEGY.md. LLM generates items,
the deterministic morphology layer verifies every conjugated form
before anything reaches a deck. Static F3 cards instead use teacher-attested
personal-error pairs, while F4 cards use reviewed cross-language contrast
pairs; both are compiled deterministically without LLM generation.
"""
