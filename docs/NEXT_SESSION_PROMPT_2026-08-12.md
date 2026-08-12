# Paste-prompt for the successor coordinator session (written 2026-08-12)

Read docs/COORDINATOR_HANDOFF_2026-08-11.md (including its 08-12 Rome
update) and take over as coordinator. Verify live state before acting
(queues, systemd units, the oxylabs-recovery timer — its probe script
depends on a session-local env file; rebuild from the Render env API if
gone). Then work these mandates, largely as codex subagent lanes:

## Standing mandate: KEEP THE SYSTEM BUSY
The owner is away ~7 more days. Minting and voicing run themselves.
Your job is to find and launch MORE productive work — treat idle
GPU-hours, idle codex credits, and idle pipeline capacity as waste.
Propose-then-run: anything reversible and inside standing doctrine
(pilot-first for new content formats, verification non-negotiable,
consoles for owner decisions) proceeds without waiting; genuinely new
directions go to the owner as short console/summary items first.

## Mandate 1: German course completeness audit (second pass)
We claim the 21-unit German course is "done". Prove it or fix it:
- Coverage: map EVERY Hammer 7th-ed section (146 extracted sections in
  docs/research/grammar_books/de_hammer_ref/) against lesson REF:
  citations across the 21 committed lessons. List sections never
  taught. Judge materiality (a C1 learner's loss) per gap.
- Exercises: per unit, compare the workbook's exercise sets
  (de_hammer_work/chapters/chNN.json) against what the plans selected
  (plans/de_*.plan.json) and what the hygiene gate dropped. Where
  coverage is thin (e.g. wortbildung kept only 6, zahlen 15,
  rechtschreibung 3, partikeln 0), decide: acceptable (chapter is
  lesson-shaped) or fix via (a) relaxing specific over-strict gate
  exclusions after review, or (b) commissioning ORIGINAL exercises in
  the established formats (owner-approved verification bar applies —
  these would be llm-generated provenance, keep them clearly marked
  and hostile-audited).
- Output: a coverage report + a punch-list; execute the fixes as codex
  lanes (lesson patches ride the existing per-unit pipeline: commit →
  enrich → seed → voice in the daily window → rebuild → re-upload;
  the delivery endpoint re-imports GUID-stable).

## Mandate 2: identify the Romance-language equivalents
The owner owns/has downloaded advanced-student equivalents of the
German pair (Hammer's reference grammar + Practising German Grammar
workbook) for FRENCH, SPANISH, PORTUGUESE, ITALIAN. A dedicated agent
must IDENTIFY the exact titles/editions (the classic Routledge
Reference Grammars + Practising-series companions and their strongest
alternatives per language, advanced/C1 level). Deliverables: per
language, the reference grammar + exercise book pairing (title,
author, edition, ISBN), confidence, and any known extraction quirks
(PDF vs EPUB). The owner will re-download them manually from your
list; the course factory (DE_UNITS pattern, course_select, enrichment,
delivery) then generalizes per language. Also propose the unit
registry sketch per language once books are known.

## Also on the board (from the ledger's open items)
- Flagged-review remediation phase 2 (17 European cards; diagnosis in
  docs/research/flagged_reviews/ — review, fix, re-deliver, and settle
  the flag-clearing mechanism with the owner).
- fancy_vocab hostile audit (75 chunks) — run it on our codex lane,
  then merge ×5 + seed + voice (the last unmerged exercises2 topic).
- Oxylabs outage: babysit the recovery timer; if >48h total, ask the
  owner to file a ticket.
- /lingq + /triage remain untapped — surface gently, never nag.
