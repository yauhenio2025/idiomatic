# Commission: Famous-cast & famous-places amendment to the Asset Factory

> Follow-up to docs/ASSET_FACTORY_STRATEGY.md (committed). The user has
> amended the cast/settings design before deciding its §8 questions.
> This session THINKS IT THROUGH, PROBES the one technical risk, and
> produces the amended casting plan for user approval. Small scoped
> generation is allowed (see §Probe); no schema or product code.

## The amendment (user, 2026-08-05, condensed)

Replace the invented fictional cast with **famous people the user already
knows deeply** — recognizable faces are pre-paid memory anchors. Examples
of the intent: the family wing cast as the Sopranos or the Roys
(Succession); famous historical friend-pairs for the friends wing.
~40–50 stable characters. Same move for places: famous locations (the
Louvre, the White House, the Chernobyl reactor hall) instead of — or
layered onto — generic settings, ideally *plausibly relevant* to the
scene, or at least "not completely insane," with deliberate
weird-person-in-weird-place pairings as a salience tool (von Restorff).
Reference portraits are easy to source from the internet; pre-render
stylized cast sheets and settings from them.

**Hard memory-hygiene constraint (user's own rule):** figures already
bound in the Mandarin Memory Palace ENCODE PHONETICS there (initial
sounds → actors). Reusing any of them in idiomatic would cross-wire two
mnemonic systems. Their registry is the exclusion list.

## What this session must deliver

`docs/ASSET_FACTORY_FAMOUS_CAST.md` containing:

1. **Exclusion list, extracted not guessed** — parse
   `~/projects/mandarin-videos/data/actors.json`, `actor-signoff.json`,
   `actor-portraits.json`, `actor-templates.json` (+ the archetype/audit
   snapshots) into the definitive do-not-cast roster (real names +
   any aliases/archetype de-brands mandarin uses). Every proposed
   idiomatic cast member must be checked against it, and the check
   must be reproducible (a small script or documented grep, listed in
   the doc).
2. **The casting matrix** — map the strategy's role slots (§2.1: 6 roles
   × 5 languages + shared figures, now expandable toward the user's
   40–50) to famous ensembles, exploiting the per-language structure:
   each language's cast drawn from THAT culture's icons the user
   plausibly knows (cinema, TV, music, politics-adjacent-but-safe,
   history), plus the pan-cultural ensembles the user named (Sopranos,
   Succession) for family/power wings. For EVERY slot propose 2–3
   candidates with one-line rationale (recognizability to THIS user —
   media-critic, film-literate, Eastern-European background — beats
   global fame). Flag any candidate whose casting could feel off
   (recently deceased, politically live, personally known to the user)
   for the user to judge. Living-person policy: private study material
   only, never shared/published decks or public artifacts — state this
   in the doc as a standing rule of the factory.
3. **The famous-places register** — for each of the strategy's 14 mined
   settings, propose a famous counterpart (plausible lane: newsroom →
   the Post's newsroom; parliament corridor → the White House West Wing;
   café → Café de Flore / Rick's Café) AND a weird-lane wildcard pool
   (Louvre, Chernobyl control room, ISS module…) with a **weirdness
   budget rule**: what fraction of strips draw a deliberately
   incongruous location (propose a number, justify from memory
   research; the strategy's plausibility default stays the norm).
   Famous places are filter-free (no likeness) so they also work in the
   cloud lane — note this asymmetry.
4. **Engine/likeness policy per pipeline stage** — the reason the
   original strategy chose fictional faces was mandarin's CLOUD filter
   pain; idiomatic's comic pipeline is LOCAL (no filters). Codify:
   likeness renders are local-only (Qwen t2i/Edit); the Nano Banana
   cloud lane gets likeness-free work only (settings, no-cast panels);
   the video-escalation rung inherits mandarin's known filter fights —
   specify the fallback ladder there (panels-as-refs may carry likeness
   implicitly; if an engine balks, the mandarin identity-de-brand
   playbook applies, and the user accepts drift at the video rung or
   skips escalation for that item).
5. **Sheet-sourcing workflow** — reference photo (internet) → local
   Edit-2511 stylization into the ligne-claire cast sheet → the photo
   itself never leaves the laptop, never uploads to the server, is
   cached under a `refs/` dir excluded from any sync; the STYLIZED sheet
   is what the factory registry stores. Naming: real names in the
   registry (the user must recognize who's who), typeset-only in cards
   as before.
6. **Schema deltas** for commission B (strategy §3.2): `factory_actors`
   gains `real_name`, `famous_source` (show/film/era), `exclusion_checked
   BOOLEAN`, `ref_photo_local_path` (laptop-only convention, never a
   server path); casting-matrix approval states.
7. **Amended user-decision list** — rewrite strategy §8 items 1–2 into
   the famous-cast frame: roster picks per slot (present as a clickable
   checklist artifact if convenient — the verdicts-page downloads
   pattern from 2026-08-05 works well), weirdness budget, cast size
   (32 vs the user's 40–50), and whether the everyday wing ALSO goes
   famous or stays fictional (hybrid option: famous for world-wing +
   family, fictional for shopkeeper-tier bit parts — argue it).

## §Probe — the one thing to TEST, not argue (required)

**Recognizability after stylization** is the make-or-break: a famous
face that survives ligne-claire stylization as *recognizably them* is a
memory anchor; one that doesn't is just a fictional character with legal
baggage. Protocol (≤6 local renders total, batch-by-model, /free after,
check no other session is mid-queue):
- Pick 2 faces clearly OUTSIDE the mandarin exclusion list, one male one
  female, from the user's likely-known tier (e.g. a Sopranos or
  Succession principal — session's choice after the exclusion check).
- Source one clean reference photo each (internet, laptop-only).
- Render: (a) Edit-2511 "redraw this person in clean European ligne
  claire comic style" from the photo; (b) insert that stylized person
  into an existing factory setting (reuse
  /srv/ai-models/outputs/pipe_setting_00001_.png) via the standard
  insertion recipe with the stylized sheet as image2.
- Judge honestly: is (a) recognizable? Does (b) SURVIVE the insertion
  still recognizable? Include the images in the deliverable (local
  paths + a small side-by-side artifact is fine — but that artifact must
  stay private/unshared per the living-person policy).
- If recognizability fails, say so loudly and propose the fallback
  (caricature-strength prompting, higher-step stylization, or the
  hybrid fictional cast) — do not soften the result.

## Read for context

docs/ASSET_FACTORY_STRATEGY.md (the base being amended);
~/llms/qwen-image/LOCAL_QWEN_IMAGE.md (stack + comic-pipeline findings);
the worked-examples artifact …7e47d809…; mandarin-videos'
REDACT/archetype machinery (`worker/batch_first10_words.py`) for what
cloud filters did to famous faces there.

## Hard rules

- No product code, no schema changes; the ≤6 probe renders are the only
  generation. Write the deliverable and STOP (orchestrator commits).
- Reference photos and any likeness renders stay on the laptop; nothing
  likeness-bearing is uploaded, committed, or publicly shared.
- Every proposed cast member: exclusion-checked against the mandarin
  registry, with the check shown.
- End by printing the amended decision list to the terminal.
