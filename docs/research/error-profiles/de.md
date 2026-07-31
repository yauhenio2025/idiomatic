# Learner Error Profile — German (de)

> Mined 2026-07-31 from teacher-marked 1:1 lesson data. Two sources,
> two eras: a 2019 lesson-notes spreadsheet and 2022–2024 Teachee
> lesson decks. German has the largest *correction* corpus of the five
> languages but — like Italian — almost no rows where the learner's
> wrong form was deliberately recorded: the `error` field is null on
> **all 346** xlsx rows. The direct error evidence is ~28 utterances
> where the transcript *retained the learner's actual mistake
> uncorrected*, and those cluster overwhelmingly in one place:
> **NP-internal agreement (gender × case × adjective ending)** — the
> same "backbone of de grammar" GRAMMAR_STRATEGY §3 already names.
> The errors repeat across the 5-year span, i.e. they are fossilized.

## 1. Data inventory

| Source | Rows | Recorded `error` field | Vocab flag | Use flag | Pron flag |
|---|---|---|---|---|---|
| `xlsx_de.jsonl` | 346 | **0** (null on every row) | 194 | 149 (incl. 1 use+pron) | 4 (incl. 1 use+pron) |
| `teachee_de.jsonl` | 379 notes, 28 lesson decks | n/a (no error field) | ~277 EN-prompt→DE cards + 102 DE-only cards | — | IPA auto-attached to nearly every card |

- **xlsx era coverage**: despite the "2019–2021" label, every row is
  from **nine lessons in April 2019** (04/02–04/30; the ISO-looking
  dates `2019-02-04` etc. are day/month-swapped exports of 02/04, 05/04,
  08/04). One month of data, ~38 rows/lesson.
- **Teachee era coverage**: Oct 2022 – Dec 2024, 28 lesson decks
  (7–22 notes each). Note anatomy: `[EN prompt, DE answer + auto-IPA]`
  (277) or DE-only phrase (102). These are overwhelmingly
  vocab/phrasing expansion — the DE line is the *teacher's* target
  phrase. A minority (~12) retain the learner's erroneous production
  verbatim in the DE line (listed in §2/§3); the EN prompts themselves
  are speech-to-text and often garbled ("He needs you to criticize the
  knowledge to criticize"), so EN-side weirdness is ASR noise, not
  learner error.
- **The crucial caveat**: with `error` always null, the xlsx `use` rows
  record *what the teacher supplied*, with the corrected element in
  (parentheses) — teacher-priority signal, not error signal. BUT the
  transcripts were taken live and ~16 xlsx rows + ~12 Teachee rows
  kept the learner's actual wrong form in the surrounding text. Those
  ~28 verbatim slips are the only ground truth here, and they are
  remarkably consistent (§3).
- **No pron profile is really possible**: 4 flagged rows total (§5).
- **Capture gap**: Teachee notes stop Dec 2024. Same recommendation as
  the it profile — the add-on is the natural live error-capture channel
  going forward.

## 2. Grammar/usage taxonomy — the 149 `use`-flagged xlsx rows

Every use row hand-categorized by what the teacher corrected
(script-counted; categories are the corrected element's type):

| # | Category | n | Share |
|---|---|---|---|
| 1 | Lexical word choice (right word for the concept) | 60 | 40% |
| 2 | Collocation / idiom (multi-word unit) | 30 | 20% |
| 3 | **Compound noun supplied** (learner circumlocuted) | 22 | 15% |
| 4 | Prefix / separable-verb precision | 8 | 5% |
| 5 | Verb/noun + preposition government (incl. da-compounds) | 7 | 5% |
| 6 | Preposition usage, place/time | 7 | 5% |
| 7 | **NP agreement/case/gender — retained verbatim errors** | 6 | 4% |
| 8 | Structural other (lassen-causative, conjunctions, `lange her`, determiner) | 6 | 4% |
| 9 | Genitive constructions | 2 | 1% |
| 10 | Passive | 1 | 1% |

Real examples per top category (verbatim from source; parentheses =
teacher's correction mark):

**Lexical choice (60)** — the bread and butter of the lessons:
- "Es kann ein bisschen (stressig) sein."
- "Alles lief (reibungslos)"
- "Jetzt kann man den Umweltschutz als (Ausrede) benutzen"
- "Dieser Modelagentur ist nicht (seriös), wenn du weißt, was ich meine."
- "Fördermittel, die / Zuschüsse, die / Subventionen, die"

**Collocation/idiom (30)**:
- "Ich habe irgendwo (den Faden verloren)"
- "Man muss ein Examen (ablegen)"
- "…ohne dabei die Wettbewerbsfähigkeit (aufs Spiel zu setzen)"
- "Amerika war immer (der Spitzenreiter in Sachen Technologie)."
- "Es gibt mehr (prekäre Beschäftigung)"

**Compound noun supplied (22)** — a distinctly German pattern: the
learner talks around a concept, the teacher hands back the compound:
- "Die (Flughafendurchsagen) sind auf Chinesisch"
- "Also bestimmte (Verhaltensnormen)"
- "Die (Vorstandsvorsitzenden) dieser Unternehmen"
- "Sie wollen neue (Datenschutzgesetze) einführen"
- "2 Stunden Zahnarzt und dann zwei Stunden (Steuerbehörde)"

**Prefix/separable-verb precision (8)**:
- "Man (öffnet) eine Tür oder eine Box" vs "man (eröffnet) einen
  Flughafen oder ein Einkaufszentrum" (explicit minimal pair taught)
- "In Amerika würden sie mich nicht (reinlassen oder durchlassen)"
- "Der Film ist (rausgekommen)"; "Unbestimmte Artikel (rauszupicken)"

**Verb+preposition government (7)**:
- "Es (kommt darauf an), auf welche Disziplinen man sich spezialisiert"
- "Sie haben (daraus eine Serie) gemacht."
- "Um die Bürger davon zu (überzeugen), …"
- "Sie haben eine Strategie, (die über 5G hinausgeht)"

**NP agreement/case/gender — retained errors (6)**: see §3, this is
the profile's core finding.

Secondary structural signal — constructions the teacher *repeatedly
supplied* across BOTH eras (learner avoidance/deficit, even though no
error was logged):

- **werden-passive: ~35 instances** (20 xlsx + 15 Teachee). "Das Buch
  (wurde geschrieben).", "Sprachlehrer konnten noch nicht (ersetzt
  werden).", "Es hätte letztes Jahr (veröffentlicht werden sollen)",
  Teachee 2024: "Sie werden von Le Pen 'geduldet'", "Als Trump gewählt
  wurde". The passive keeps being fed for five years.
- **Genitive constructions: 15 xlsx rows** ("die Größe Ihres
  Binnenmarktes", "Nach dem Kollaps (des Kommunismus)", "die (Aufgabe
  meiner Presseagentin)") — while the learner's own accepted phrasing
  uses von: "die besten Verteidiger **vom Kapitalismus**", "Die
  Wichtigkeit **von** Führungskräften" (Teachee). Genitive avoidance.
- **Dative verbs: 8+** — gehören taught 3× ("Sie gehören (diesem
  japanischen Unternehmen)", "Du (gehörst) mir", Teachee "Sie gehören
  Soros"), plus supplied "diesen Themen viel Zeit widmen", "dem Druck
  widerstehen", "Es hat diesen Zwängen gut entsprochen" — and the two
  verbatim dative errors in §3.
- **Konjunktiv II: ~8 supplied** ("Es hätte … veröffentlicht werden
  sollen", "das sei die Aufgabe…", Teachee "Ohne diesen Podcast hätte
  ich sie nie geschrieben", "Kapitalismus wäre nicht profitabel").
- **Directional preposition with country names: 3×** "(fliege ich in
  die Türkei)", "Lass dich (in der Türkei) nicht verhaften".

## 3. Recurring structural patterns (fossilization candidates)

The verbatim retained errors, both eras. Categories ordered by weight:

**A. Adjective/determiner endings (6 verbatim, 2019→2024 — fossilized):**
- 2019: "Der (härtester Konkurrent)" → der härteste Konkurrent
- 2019: "Er hat sehr (tiefgründiger Schlüsse) daraus gezogen" → tiefgründige Schlüsse
- 2019: "haben keinen (kohärentes Weltbild)" → kein kohärentes Weltbild
- 2024: "Meine ultimative Ziel ist daraus einen Film zu machen" → Mein ultimatives Ziel
- 2024: "Es kommen noch zwölf weiterer" → zwölf weitere
- Teachee era: "Ich brauche ein größtmöglichstes Publikum" → größtmögliches (double superlative)

**B. Noun gender on high-frequency nouns (4 verbatim):** das Ziel
("Meine ultimative Ziel" — Russian *цель* is feminine), das Programm
("Du kannst **den Programm** sagen" — dative + gender), die Agentur
("**Dieser** Modelagentur ist nicht seriös"), feminine agent nouns
("Sie war deine **Presseagent**" → Presseagentin).

**C. Object case — dative vs accusative (4 verbatim):**
- "Sie tun damit (jemanden einen Gefallen)" → jemandem
- "Du kannst den Programm sagen" → dem Programm (dative object)
- "Damit konnte er **seiner Stadt** mit Strom versorgen" → seine Stadt (versorgen + acc)
- "Sie verfüttern Menschen an **Schweinen**" → an Schweine (Wechselpräposition, direction → acc)

**D. Spurious -(e)n / dative-plural hypercorrection (3 verbatim):**
"50 **Schillingen** pro Watt", "einen 2 Stunden langen **Spielfilmen**
drehen", "höhere **Honorar**" (missing plural, the mirror image).
Related: weak-noun declension taught ("Es geht um (einen Jungen, der)").

**E. Verb agreement slips under load (3 verbatim):** "Darauf (achten
ich) nicht so sehr" → achte; "Skype benutzen meinen Bildschirm" →
benutzt; "Obwohl ich das in meinem eigenen Buch widerlegt haben" → habe.

**F. Spurious/missed reflexive:** "Das hat (sich globale Auswirkungen)"
→ Das hat globale Auswirkungen (blend of *sich auswirken* × *Auswirkungen haben*).

**G. Passive avoidance** (35 supplied instances, §2) — never produced
wrong, apparently just not produced.

**H. Genitive avoidance** — von-phrases where written register wants
genitive ("Verteidiger vom Kapitalismus"); 15 genitive constructions
teacher-supplied.

**I. öffnen/eröffnen-type prefix minimal pairs** — explicitly drilled
in-lesson; 8 prefix-verb corrections.

**J. Compound-noun circumlocution** — 22 corrections; a production
habit, not a grammar error; feeds vocab, not drills.

**K. da-compound + verb government** ("kommt darauf an", "daraus …
gemacht", "dreht sich darum", "hängt von … ab") — 7 corrections +
several vocab-flagged repeats.

**L. in die Türkei / country-name articles** — 3 corrections, classic
Russian-L1 transfer (articleless *в Турцию*).

## 4. Vocabulary profile

What keeps being taught (194 xlsx vocab rows + 277 Teachee EN→DE cards)
is strikingly uniform in register — **journalistic/intellectual
Bildungssprache for the learner's professional life** (public
intellectual: books, podcasts, talks, tech criticism):

- **Politics & geopolitics** (~25%): letzte Diktatur Europas,
  Oppositionsbewegung, Staatsbürgerschaft, der EU beitreten,
  Europawahlen, Friedensverhandlungen, Einflussgebiet,
  Präsidentschaftswahlen, eine Regierung bilden.
- **Tech / platforms / AI** (~20%): Datenschutzgesetze,
  Glasfaser-Internet, Algorithmen, Stichwörter, Spracherkennung,
  Musterabgleich, "dass KI keine Blase ist", Datei hochladen.
- **Media, publishing, his own career** (~20%): Verlag, Erstautoren,
  Literaturagentur, Bucherlöse, Vorschuss, Honorare, Verfilmung,
  den Podcast vertonen, Tontechniker, Presseagentin, Publikum.
- **Economy & labor** (~15%): Gewerkschaften, Löhne,
  Arbeitslosenquoten, prekäre Beschäftigung, Steuererklärung,
  Fördermittel/Zuschüsse/Subventionen, bedingungsloses Grundeinkommen,
  Aktienkurs.
- **Academia & philosophy** (~10%): Vorherbestimmung, Nährboden für
  den Kapitalismus, Examen ablegen, Gutachten ausstellen,
  Studiengebühren, Fachgebiet.
- **Everyday/travel** (~10%): Nickerchen, Bergwanderungen, beim
  Zahnarzt, Muskeln tun weh, wählerisch/mäkelig.

Register gaps the teacher fills: compounds (§2 cat. 3), nominalized
style ("Ein ständiges In-Frage-Stellen", "Bewusstwerden"), precision
adverbs (anfangs, teilweise, scherzhaft, höchstwahrscheinlich,
rechtlich gesehen). This is exactly the idiom pipeline's register —
grammar decks should reuse this domain vocabulary in drill sentences.

## 5. Pronunciation profile

Only 4 flagged rows (all April 2019): "Überall", "Ich", "Echt",
"eine wichtige Veranstaltung". Thin — but internally consistent:
3 of 4 contain the palatal fricative **[ç]** (i**ch**, e**ch**t,
wi**ch**tige) and the fourth targets **/yː/ + stress** (Überall) —
textbook Russian-L1 problem sounds. Teachee auto-attaches IPA to
nearly every card (pron attention persisted through 2024) but encodes
no error information. Verdict: not enough data for a pron unit; if
audio drills come, bias minimal pairs toward [ç]/[x]/[ʃ] and ü/i.

## 6. Curriculum mapping

Existing + planned units vs this evidence:

| Unit | Status | Evidence from this data | Strength | Action |
|---|---|---|---|---|
| de_gender (1 Genus) | active | 4 verbatim gender errors incl. 2024 (das Ziel, das Programm, die Agentur, -in agent nouns); every §3-A error is also a gender-dependent ending | **strong** | Keep active. Bias noun sampling toward Russian↔German gender mismatches (цель/Ziel, программа/Programm) and -in agent nouns. |
| de_prep_fest (2 Präpositionen) | active | no recorded case error after a fixed preposition; preposition errors observed are semantic choice (beim Zahnarzt, am späten Nachmittag) | weak | Keep small; don't top up ahead of the units below. |
| de_prep_wechsel (2 Präpositionen) | active | 1 verbatim ("an Schweinen" → an Schweine) + in die Türkei taught 3× | moderate | Keep. Add direction-with-geography frames (in die Türkei / im Iran / nach Italien). |
| de_adj_endings (3 Adjektive) | planned | **6 verbatim errors spanning 2019→2024** — the single largest verified error class; all three declension patterns hit (weak "der härtester", strong "tiefgründiger Schlüsse", mixed "keinen kohärentes / Meine ultimative") | **strongest in the dataset** | **BUILD FIRST.** Tier A verifiable today (gender table + declension matrix already vendored). F1 cloze on the ending, F5 landmark card per pattern. |
| de_verb_core (4 Verben) | planned | agreement slips exist but are performance noise (achte/benutzt/habe); the real verb-side deficits are passive + Konjunktiv II (below) | moderate | Build second, but scope it to what the data shows: presens/perfect agreement is NOT the gap — weight passive and KII forms, or split them out (below). |

New units the data justifies (proposed keys; clusters — existing
"1 Genus", "2 Präpositionen", "3 Adjektive", "4 Verben", plus one new
cluster "5 Kasus"):

| Proposed unit | Cluster | Evidence | Priority |
|---|---|---|---|
| `de_passiv` — werden/wurde/worden forms + passive with modals | 4 Verben | ~35 teacher-supplied passives across 2019–2024; zero spontaneous production recorded; incl. "hätte veröffentlicht werden sollen" | high (right after de_adj_endings; can ship as the first half of de_verb_core) |
| `de_dativ_verben` — dative-object verbs + jemandem/jemanden | 5 Kasus | 4 verbatim case errors (§3-C); gehören taught 3×, widmen/widerstehen/entsprechen supplied | high |
| `de_n_deklination` — weak nouns + no -en on acc.sg./unit nouns | 5 Kasus | §3-D: Schillingen, Spielfilmen, Honorar; "(einen Jungen, der)" taught | medium (small unit, ~15 cards) |
| `de_genitiv` — genitive NP chains in written register | 5 Kasus | 15 supplied constructions + documented von-avoidance | medium |
| `de_konjunktiv2` — hätte/wäre/würde + KII passive | 4 Verben | ~8 supplied instances, incl. reported speech *sei* | low/later |
| (not a grammar unit) Komposita/Wortbildung | — | 22 compound corrections = circumlocution habit | route to the idiom/vocab pipeline, not drills |

Verification note: de_adj_endings, de_dativ_verben, de_n_deklination
and de_genitiv are all Tier A (declension matrix + gender table +
small verb/noun lists); de_passiv forms are Tier A against verbecc/
kaikki participles; only KII selection needs Tier B blind-fill.

## 7. F3 seed list — 30 real error pairs

Items 1–26 are **verbatim** learner productions retained in the
transcripts (xlsx April 2019 unless noted; T = Teachee 2022–24).
Items 27–30 are minimal reconstructions from corrections where the
lesson explicitly recorded the contrast.

```json
[
  {"wrong": "Der härtester Konkurrent", "right": "der härteste Konkurrent", "why": "Weak adjective ending after definite article: der + -e, never -er.", "category": "adj_endings"},
  {"wrong": "Er hat sehr tiefgründiger Schlüsse daraus gezogen", "right": "Er hat sehr tiefgründige Schlüsse daraus gezogen", "why": "Strong plural accusative without article takes -e.", "category": "adj_endings"},
  {"wrong": "Sie haben keinen kohärentes Weltbild", "right": "Sie haben kein kohärentes Weltbild", "why": "das Weltbild is neuter: kein (no ending) + -es on the adjective.", "category": "gender+adj_endings"},
  {"wrong": "Meine ultimative Ziel ist, daraus einen Film zu machen", "right": "Mein ultimatives Ziel ist, daraus einen Film zu machen", "why": "das Ziel is neuter (Russian цель is feminine — transfer trap): mein + -es.", "category": "gender+adj_endings"},
  {"wrong": "Es kommen noch zwölf weiterer", "right": "Es kommen noch zwölf weitere", "why": "Strong plural nominative after a bare numeral takes -e.", "category": "adj_endings"},
  {"wrong": "Ich brauche ein größtmöglichstes Publikum", "right": "Ich brauche ein größtmögliches Publikum", "why": "größtmöglich already contains the superlative — no second -st.", "category": "adj_morphology"},
  {"wrong": "Du kannst den Programm sagen, was es hervorheben soll", "right": "Du kannst dem Programm sagen, was es hervorheben soll", "why": "sagen takes a dative addressee; das Programm → dem.", "category": "case_dative"},
  {"wrong": "Sie tun damit jemanden einen Gefallen", "right": "Sie tun damit jemandem einen Gefallen", "why": "Person = dative, thing = accusative: jemandem einen Gefallen tun.", "category": "case_dative"},
  {"wrong": "Sie verfüttern Menschen an Schweinen", "right": "Sie verfüttern Menschen an Schweine", "why": "verfüttern an + accusative (direction, Wechselpräposition).", "category": "prep_case"},
  {"wrong": "Damit konnte er seiner Stadt mit Strom versorgen", "right": "Damit konnte er seine Stadt mit Strom versorgen", "why": "jemanden mit etwas versorgen — the recipient is accusative.", "category": "case_verb_government"},
  {"wrong": "Dieser Modelagentur ist nicht seriös", "right": "Diese Modelagentur ist nicht seriös", "why": "die Agentur, nominative subject → diese.", "category": "gender"},
  {"wrong": "Sie war deine Presseagent", "right": "Sie war deine Presseagentin", "why": "Female referent needs the -in agent noun.", "category": "gender_derivation"},
  {"wrong": "Warum dieser Frau so viel Geld zur Verfügung hatte", "right": "Warum diese Frau so viel Geld zur Verfügung hatte", "why": "Subject stays nominative: diese Frau.", "category": "case"},
  {"wrong": "Darauf achten ich nicht so sehr", "right": "Darauf achte ich nicht so sehr", "why": "1sg present -e; fronted element forces subject-verb inversion, not plural.", "category": "verb_agreement"},
  {"wrong": "Skype benutzen meinen Bildschirm als Lautsprecher", "right": "Skype benutzt meinen Bildschirm als Lautsprecher", "why": "3sg subject → benutzt.", "category": "verb_agreement"},
  {"wrong": "Obwohl ich das in meinem eigenen Buch widerlegt haben", "right": "Obwohl ich das in meinem eigenen Buch widerlegt habe", "why": "Auxiliary agrees with ich: habe.", "category": "verb_agreement"},
  {"wrong": "Das hat sich globale Auswirkungen", "right": "Das hat globale Auswirkungen", "why": "Auswirkungen haben is not reflexive (blend with sich auswirken).", "category": "reflexive"},
  {"wrong": "50 Schillingen pro Watt", "right": "50 Schilling pro Watt", "why": "Currency/measure nouns stay uninflected after numerals — no dative-plural -en.", "category": "noun_number"},
  {"wrong": "Damit kann man einen 2 Stunden langen Spielfilmen drehen", "right": "Damit kann man einen 2 Stunden langen Spielfilm drehen", "why": "Accusative singular — no -en on the noun (Spielfilm is not a weak noun).", "category": "noun_number"},
  {"wrong": "Sie wollen höhere Honorar für ihre Vorträge", "right": "Sie wollen höhere Honorare für ihre Vorträge", "why": "Plural das Honorar → die Honorare.", "category": "noun_number"},
  {"wrong": "Er hat Klager eingereicht", "right": "Er hat Klage eingereicht", "why": "Klage einreichen — the noun is die Klage.", "category": "noun_form"},
  {"wrong": "die katholische Mess", "right": "die katholische Messe", "why": "die Messe keeps its final -e.", "category": "noun_form"},
  {"wrong": "Untertitel sind zum lesen da", "right": "Untertitel sind zum Lesen da", "why": "zum + nominalized infinitive is capitalized: zum Lesen.", "category": "nominalization"},
  {"wrong": "Sie stellen es so da, als würden sie sich nur um das Wohlergehen der Gesellschaft kümmern", "right": "Sie stellen es so dar, als würden sie sich nur um das Wohlergehen der Gesellschaft kümmern", "why": "darstellen — separable prefix dar-, not the adverb da.", "category": "prefix_verb"},
  {"wrong": "Sie wollen nicht, das sich chinesische Technologie in anderen Ländern ausbreitet", "right": "Sie wollen nicht, dass sich chinesische Technologie in anderen Ländern ausbreitet", "why": "Conjunction dass, not the article/pronoun das.", "category": "conjunction"},
  {"wrong": "Ich hätte gern ein Bier mit ohne Alkohol", "right": "Ich hätte gern ein Bier ohne Alkohol", "why": "One preposition: ohne Alkohol (or: ein alkoholfreies Bier).", "category": "preposition"},
  {"wrong": "Man öffnet einen Flughafen", "right": "Man eröffnet einen Flughafen", "why": "öffnen = physically open; eröffnen = inaugurate an institution/venue (documented in-lesson minimal pair).", "category": "prefix_verb"},
  {"wrong": "Ich fliege nach Türkei", "right": "Ich fliege in die Türkei", "why": "Feminine country names take the article: in die Türkei / in der Türkei (Russian-L1 article drop; correction taught 3×).", "category": "prep_place"},
  {"wrong": "Es geht um einen Junge, der sehr innovativ ist", "right": "Es geht um einen Jungen, der sehr innovativ ist", "why": "der Junge is a weak noun: -n in all cases but nominative (correction marked in-lesson).", "category": "weak_noun"},
  {"wrong": "Sie sind die besten Verteidiger vom Kapitalismus", "right": "Sie sind die besten Verteidiger des Kapitalismus", "why": "Written register prefers the genitive over von + dative.", "category": "genitive"}
]
```

## 8. Bottom line

1. Build **de_adj_endings now** — the only error class with six
   verbatim instances spanning both eras, and it is Tier-A verifiable
   with assets already in the repo.
2. Then **de_passiv** (or de_verb_core weighted to passive + KII):
   35 supplied passives, zero produced.
3. Open a **"5 Kasus" cluster**: de_dativ_verben, de_n_deklination,
   de_genitiv — every verbatim case error lands there.
4. Drill sentences should reuse the learner's professional register
   (politics/tech/media vocabulary of §4), which doubles as vocab
   maintenance.
5. Restart error capture: no data since Dec 2024; the add-on is the
   natural channel for a live `_errors` feed into F3.
