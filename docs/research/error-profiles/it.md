# Learner Error Profile — Italian (it)

> Mined 2026-07-31 from teacher-marked 1:1 lesson data, 2019 era.
> Italian is the THINNEST of the five language datasets. Read §1 before
> trusting any count below: there are exactly **11 recorded production
> errors, all from a single lesson**. Everything else is teacher-assigned
> drill/vocab material, which carries *teacher-priority* signal but not
> *learner-error* signal. Frequency claims are impossible; this profile
> is a hypothesis sheet, not a statistics sheet.

## 1. Data inventory

| Source | Rows | With recorded error | Vocab flag | Use flag | Pron flag |
|---|---|---|---|---|---|
| `xlsx_it.jsonl` | 133 | **11** | 10 | 123 | **0** |
| `_errors::_it_errors` Anki deck | 194 notes (129 unique) | 13 notes carrying "my actual error:" (= the same 11 errors; 2 are duplicate notes) | — | — | — |

- **Overlap**: the deck is the xlsx re-imported, not an independent
  source. 193/194 deck notes normalize to an xlsx `correct` value; the
  1 non-match is the same row with mangled brackets
  ("Abbiamo una situazione dove) […IN PRIMO LUOGO ....]"). 65 deck notes
  are duplicates (fill-in-the-blank + vocab variants of the same row).
  The deck adds English translations and note-type tags but **zero new
  error rows**. Net unique dataset: 129 items.
- **Dates**: 2019-03-05 (74), 25/04/2019 (25), 18/04/2019 (17),
  18/05→20/06/2019 (14), 2019-08-09 (1), null (2). Despite the
  "2019–2021 era" label, every dated row is 2019; coverage is
  ~8 lessons over 5 months, then nothing.
- **Row anatomy** (this is the crucial caveat):
  - 11 rows = real error pairs (learner's actual utterance recorded).
    **All 11 from one lesson, 18/04/2019.**
  - 91 rows = corrected/target phrases with the key part in
    (parentheses) but **no recorded wrong form** — two teacher-assigned
    blocks: a 74-row drill set on *verbi procomplementari* (farcela,
    cavarsela, fregarsene, sentirsela, prendersela, avercela con…) from
    2019-03-05, and a 19-row discourse-connector upgrade set (dato che,
    per quanto riguarda, di conseguenza, ossia, tuttavia…) from
    25/04/2019, evidently from an essay/speech revision.
  - 31 rows = plain vocabulary items (previsione, moratoria,
    redditività, colosso…).
- **Teachee gap**: there are NO Teachee decks for Italian — the
  learner's Italian lessons ran outside Teachee, so unlike es/de/fr/pt
  there is no ongoing capture channel and no post-2019 data at all.
- **Statistical power, honestly**: n=11 errors from one conversation
  supports at most "these error types occurred at least once." No
  category can be called dominant with confidence; the 5/11 preposition
  share is suggestive only because the same error repeats within the
  lesson. Articles, auxiliaries, congiuntivo production, clitic
  production, pronunciation: **zero direct observations each**. Where
  the profile must guide curriculum, it should borrow from the
  cross-language pattern (§3) and from the es/fr/pt sibling profiles.

## 2. Grammar error taxonomy (n = 11 recorded errors)

All quotes verbatim from `xlsx_it.jsonl` (corrected part in parentheses
as in the source).

**Verb + preposition regime — 5/11** (the only repeated category)
- "cercare (di) ottimizzare...." ← said *"cercare a ...."*
- "io cerco (di) mettere il problema della tecnologia nel contesto..." ← said *"a"* — **same error twice in one lesson**
- "questo mi permette (di) ricevere gli inviti" ← said *"a"*
- "partecipare (a) qualche convegno" ← said *"in"*
- "ciò che guadagno (come) scrittore" ← said *"di"*

**Lexical selection / false friend — 3/11**
- "(il governo) della città" ← said *"la governanza"* (EN/FR *governance* calque; gender error rides along)
- "Una casa editrice (buona, migliore)" ← said *"brava"* (bravo = skilled person, not for institutions)
- "Questa è la prima (colonna)" ← said *"columna"* (Spanish word, verbatim)

**Tense/aspect: imperfetto vs passato prossimo — 1/11**
- "(c'è stato) un convegno in Turchia" ← said *"c'era"* (bounded past event → passato prossimo)

**Fixed expression — 1/11**
- "Il lavoro, (di per sé) è interessante" ← said *"per sé"*

**Agreement/form — 1/11**
- "Il mio libro si basa su un rapporto sulle città (intelligenti)" ← said *"intellegente"* (number agreement + misspelling)

**Romance/English interference sub-tally** (overlaps the above): ~5/11
plausibly interference-driven — *columna* (es), *cercare a* ×2
(fr *chercher à*), *partecipare in* (es *participar en* / en
*participate in*), *la governanza* (en/fr *governance*). Consistent
with the prior that Italian, studied alongside es/fr/pt, is the most
interference-prone of the four Romance languages for this learner.

**Categories with ZERO direct evidence** (asked for, not found):
articles il/lo/la (0), passato prossimo auxiliary choice essere/avere
(0), congiuntivo production errors (0 recorded; 1 implicit — the essay
set contains "Abbiamo bisogno di una nuova tecnologia che …(RIESCA)…",
the capitalized congiuntivo strongly suggesting the learner had used
indicative), clitics ci/ne production (0 — but see §3).

## 3. Recurring patterns (what repeats even at n=11)

1. **Verb-regime prepositions repeat within a single lesson**
   (*cercare a* twice, plus *permettere a*, *partecipare in*). This is
   also the pan-Romance pattern for this learner: the same
   regime-selection struggle should be cross-checked in the fr/es/pt
   profiles (fr *chercher à* is precisely what surfaces here as
   *cercare a*). Interference is the mechanism, prepositions are the
   symptom.
2. **The teacher's remedial choices are themselves data.** 74 of 133
   rows (56%) are a drill block on *verbi procomplementari* — ci/ne
   clitic clusters with agreement in compound tenses ("(me la sono
   presa)", "se l'è cavata", "non (se l'è sentita di)", "(Ce l'ho
   fatta)"). A teacher does not spend a whole session's homework on
   *fregarsene/cavarsela* paradigms unless the learner couldn't produce
   them. This is the strongest single signal in the dataset and it
   points exactly at the planned `it_clitici_ci_ne` unit — and at
   participle agreement with preposed clitics (la → l' + -a), which
   belongs to the passato-prossimo unit's "accordo" half.
3. **Register upgrading at C1**: the 19-row connector set (25/04/2019)
   shows the teacher pushing from serviceable to idiomatic discourse —
   *dato che, per quanto riguarda / riguardo / in merito a, di
   conseguenza, in quanto / essendo, ossia, tuttavia, nemmeno /
   neanche / neppure, per di più, insomma* — plus one structural fix:
   "Abbiamo una situazione (dove) […]" (relative *dove* → *in cui* /
   restructure). Advanced-learner profile: grammar mostly holds,
   cohesion devices and regime details are the frontier.

## 4. Vocabulary + pronunciation notes

- **Pronunciation: 0 rows flagged `pron`.** The dataset supports no
  pronunciation conclusions whatsoever.
- **Vocabulary** (10 `vocab`-flagged + 31 plain items): overwhelmingly
  the learner's professional register — publishing and political
  economy (*casa editrice, previsione, indagine di mercato, debito
  privato, seggi in parlamento, moratoria, sgombero, redditività,
  redditizio, colosso, manovalanza, giacimenti naturali*). One idiom
  block (avere fegato/naso/polso…, testa calda, in un batter d'occhio)
  inside the 2019-03-05 set. Data-quality note: one row contains a
  teacher/transcription typo, "complilare un modulo" (→ *compilare*).
- Vocab errors that were recorded are false friends, not gaps
  (*columna*, *governanza*, *brava*) — consistent with an advanced
  learner whose lexicon is large but Romance-entangled.

## 5. Curriculum mapping

Existing clusters: "1 Tempi", "2 Condizionale", "3 Congiuntivo",
"4 Clitici". Evidence strength scale: none / indirect / weak / direct.

| Unit | Cluster | Evidence | Recommended action |
|---|---|---|---|
| `it_presente_irregolari` | 1 Tempi | none | Keep as-is (foundational; no counter-evidence). |
| `it_passato_prossimo` (ausiliare e accordo) | 1 Tempi | indirect — no auxiliary error observed, but the procomplementari drill set is full of participle agreement with preposed clitics ("me la sono presa", "se l'è cavata") | Keep; when F3 lands, weight the *accordo* half (clitic + participle) over the auxiliary half. |
| `it_imperfetto` | 1 Tempi | direct (1) — "(c'è stato) un convegno" ← *c'era* | Keep; add F2 minimal-pair contrast cards imperfetto ↔ passato prossimo (the one attested tense error is exactly this selection). |
| `it_futuro_semplice` | 1 Tempi | none | Keep as-is. |
| `it_condizionale_presente` | 2 Condizionale | none | Keep as-is. |
| `it_congiuntivo_presente` | 3 Congiuntivo | weak (1 implicit) — "…tecnologia che …(RIESCA)…" corrected in the essay set | Keep; congiuntivo after *bisogno di … che* / relative clauses is worth one F2 batch. |
| `it_passato_remoto` | 1 Tempi | none | Keep (recognition-oriented; no production evidence either way). |
| `it_clitici_ci_ne` (PLANNED) | 4 Clitici | **strongest signal in the dataset** — 74-row teacher remedial block on ci/ne procomplementari | **Promote to next it build.** Scope it beyond bare ci/ne to the *verbi procomplementari* the teacher actually drilled: farcela, cavarsela, sentirsela, prendersela, fregarsene, avercela con, mettercela tutta, andarsene — including compound-tense agreement. |

**New unit candidates** (thin evidence, but it all points one way):

| Proposed unit | Cluster | Evidence | Note |
|---|---|---|---|
| `it_reggenze_verbali` (verb + preposition regime: cercare DI, permettere DI, riuscire A, partecipare A, guadagnare COME) | new "5 Reggenze" | direct (5/11 errors, one repeated) | Not a conjugation unit — no verbecc Tier-A table exists for regimes, so this must be an F3/F1-cloze unit seeded from §6 + a curated regime list; verification = curated lookup table, not conjugation. Cross-check against fr/es/pt sibling profiles: if regime errors recur there (expected), consider a shared F4 cross-language regime contrast batch. |
| `it_connettivi_discorso` (dato che, per quanto riguarda, ossia, tuttavia, per di più…) | — | indirect (19-row teacher upgrade set) | Borderline grammar/vocab; low priority; cheapest as F1 cloze from the 25/04/2019 sentences, which are already C1-register and self-authored (the learner's own essay content). |

Do NOT add units for articles, auxiliary selection, or pronunciation on
this dataset — zero observations is not evidence of mastery, but it is
also not evidence of need; those should be driven by the grammar loop's
own lapse statistics once decks are live.

## 6. F3 seed list (real error pairs, machine-readable)

11 attested pairs + 1 inferred (marked). All from 18/04/2019 except the
inferred one (25/04/2019).

```json
[
  {"wrong": "Questa è la prima columna", "right": "Questa è la prima colonna", "why": "Spanish 'columna' intruding; Italian is 'colonna'", "category": "interference-es"},
  {"wrong": "un rapporto sulle città intellegente", "right": "un rapporto sulle città intelligenti", "why": "plural agreement with 'città' + spelling: intelligenti", "category": "agreement"},
  {"wrong": "la governanza della città", "right": "il governo della città", "why": "'governance' calque; Italian uses 'il governo' (masc.)", "category": "false-friend"},
  {"wrong": "cercare a ottimizzare", "right": "cercare di ottimizzare", "why": "cercare takes DI + infinitive (fr 'chercher à' interference)", "category": "verb-preposition"},
  {"wrong": "io cerco a mettere il problema nel contesto", "right": "io cerco di mettere il problema nel contesto", "why": "cercare DI — same regime error, repeated", "category": "verb-preposition"},
  {"wrong": "questo mi permette a ricevere gli inviti", "right": "questo mi permette di ricevere gli inviti", "why": "permettere (a qcn) DI + infinitive", "category": "verb-preposition"},
  {"wrong": "partecipare in qualche convegno", "right": "partecipare a qualche convegno", "why": "partecipare A (es 'participar en' / en 'participate in' interference)", "category": "verb-preposition"},
  {"wrong": "ciò che guadagno di scrittore", "right": "ciò che guadagno come scrittore", "why": "role/capacity is 'come' + noun, not 'di'", "category": "verb-preposition"},
  {"wrong": "una casa editrice brava", "right": "una casa editrice buona", "why": "'bravo' = skilled (people); institutions/things take 'buono'", "category": "lexical-selection"},
  {"wrong": "Il lavoro, per sé è interessante", "right": "Il lavoro, di per sé è interessante", "why": "fixed phrase is 'di per sé' (in itself)", "category": "fixed-expression"},
  {"wrong": "C'era un convegno in Turchia", "right": "C'è stato un convegno in Turchia", "why": "bounded, completed event → passato prossimo, not imperfetto", "category": "tense-aspect"},
  {"wrong": "Abbiamo una situazione dove i soliti meccanismi non funzionano", "right": "Abbiamo una situazione in cui i soliti meccanismi non funzionano", "why": "relative 'dove' for abstract antecedent → 'in cui' (INFERRED from teacher's bracketed correction, wrong form not recorded verbatim)", "category": "relative-pronoun-inferred"}
]
```

## 7. Data-collection recommendation

The Italian pipeline is blind: no Teachee decks, no data since 2019,
while the learner still takes weekly Italian lessons. Until new errors
flow in, every it curriculum decision leans on a single 2019 lesson
plus cross-language borrowing. Cheapest fixes, in order:

1. **A live capture deck the add-on already understands.** Create
   `_errors::_it_errors_live` in the learner's collection with the same
   note shape as the old deck ("correct with (part)", "my actual
   error: …", date). During/after each lesson the learner (or teacher)
   adds notes. The `idiomatic_puller` add-on already runs on a QTimer
   with agent auth against the API — add a small "push new `_errors::*`
   notes" step next to the existing pull/ack, POSTing to a new
   agent-authed `/agent/lesson-errors` endpoint into a `learner_errors`
   table (lang, wrong, right, category NULL, source, noted_at). Zero
   new infrastructure; reuses token, timer, and delivery plumbing.
2. **Server-side classification, not manual.** A nightly (or
   on-ingest) Gemini pass fills `category` using the §2 taxonomy labels
   so the error profile and F3 seed pool regenerate mechanically.
   Bulk classification prompts are codex-delegable per the standing
   directive.
3. **Close the loop with the grammar decks.** F3 cards generated from
   §6 should carry their seed id; the planned `push_stats` revlog
   telemetry (GRAMMAR_STRATEGY §8) then tells us which attested errors
   are actually extinguished vs still lapsing — turning this static
   2019 snapshot into a moving profile.
4. **Until then**: treat es/fr/pt sibling profiles as proxy evidence
   for it, specifically for verb-regime prepositions, imperfect-vs-
   perfect aspect choice, and subjunctive triggers — the three areas
   where this thin dataset and pan-Romance interference already agree.
