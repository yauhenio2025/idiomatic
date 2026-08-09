# Personal Study DJ — commission (owner vision, 2026-08-09)

> "There will need to be some kind of an empowered DJ that will keep
> track of everything that I'm studying and will then adjust what to
> serve me accordingly." Captured as the umbrella initiative over all
> content systems. Experimentation should start "the sooner the
> better" — the idea that the owner will know which decks to open,
> among everything we mint, is "extremely unrealistic."

## The problem

Study time is fixed and scarce: ~2-3 h/day (gym sessions, possibly
split morning/afternoon/evening), so ~20-30 min per language including
Mandarin. The content estate is large and growing (expressions/Fluency,
grammar drills, exercises2 waves, tenses, translation, podcasts/lessons,
rescue, future Grammar Course units). Manually choosing decks does not
scale; the mix per session should be COMPUTED.

## The brain

Server-side orchestrator, activated on every post-study sync ("always
activated by the statistics of what I do in the gym once I come back
and synchronize"):

1. INPUTS: synced revlogs (proven headless AnkiWeb pull), per-card
   populations and tags (lesson vs exercise vs expression …), curriculum
   position (unit progress, wave coverage), per-card observed
   seconds/rep (revlog time field) for time budgeting.
2. COMPUTES per language: what mix of card populations moves the
   curriculum forward given the minutes available — due reviews first,
   then a weighted new-card mix (expressions vs grammar vs exercises vs
   listening), weights adjusted by weakness clustering (shared machinery
   with the Hub weakness policies and the Grammar Course telemetry).
3. OUTPUTS a SESSION PLAN: per-language time budget, card quotas per
   population, and an explicit card-selection spec.
4. ESCALATES: may resurface lessons, commission new lessons/exercises
   (Grammar Course loop), or raise video-pipeline priorities — all
   through existing generate→verify→build lanes, never bypassing gates.

## Delivery mechanism (architecture sketch)

Filtered/custom decks are CLIENT-side objects, so the DJ does not ship
them as apkgs: the server publishes the session plan as JSON; the
Idiomatic ADD-ON materializes it on profile open as filtered deck(s)
under a sort-first root (e.g. `0 Today`) — one per language, or one
combined multi-language session (owner mused both ways; pilot decides;
configurable). The owner's job reduces to: open Anki, study `0 Today`.
Time-budget fill uses observed seconds/card so a 25-minute Italian
slot really is ~25 minutes.

## Dashboard

A DJ panel in the idiomatic dashboard: today's plan and why (which
weaknesses drove the weights), time-budget settings, commission queue,
history of plans vs actual study. Decision delivery to the owner
happens via interactive console pages (multiple choice + comment box —
voice-dictation friendly), NEVER as MD files to read (owner directive
2026-08-09).

## Pilot (start after the Hub cutover lands)

ONE language (Italian), one week: DJ computes a daily session plan from
real revlogs; add-on materializes the filtered deck; owner studies it
at the gym; plans-vs-actuals reviewed. No commissioning loop in the
pilot — mix computation and delivery only. Pilot-first doctrine
applies: nothing multi-language until the Italian loop feels right.

## Owner-ratified design principle (2026-08-09)

Exercises must be ATOMIC, individually-graded cards — never mixed
inside lesson/explanation cards: "once we flip the card, we're not
measuring anything... once we turn [it] into a single exercise card,
we'll actually be able to respond to that card and not to the entirety
of the unit's grammar as a whole." This principle binds the Grammar
Course design and all future content formats: measurement granularity
= card granularity.
