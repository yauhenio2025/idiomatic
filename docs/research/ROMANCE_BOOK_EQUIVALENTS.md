# Romance-language equivalents of the German course book pair

> Research report, 2026-08-12. Identifies the exact reference-grammar +
> practice-workbook pairs for FR / ES / PT / IT, equivalent to the German
> pair (Hammer's German Grammar and Usage 7e + Practising German Grammar),
> for the 21-unit course factory (`idiomatic/grammar/course.py::DE_UNITS`).
> Sources: Routledge product pages (TOCs read via headless browser),
> Taylor & Francis pageplace preview files (front matter + full TOC,
> including the B&B 6e preview EPUB whose XHTML was parsed directly),
> Amazon/AbeBooks for ISBN cross-checks. All ISBNs below were seen on at
> least two independent sources.

## Executive summary

| Lang | Reference grammar | Workbook | Confidence |
|------|-------------------|----------|------------|
| DE (baseline) | Hammer's German Grammar and Usage, **7e** (Durrell, Routledge 2021, 9780367150235) | Practising German Grammar, **4e** (Durrell/Kohl/Kaiser, Routledge) | — (given) |
| FR | French Grammar and Usage, **5e** (Towell/Lamy/Hawkins, Routledge 2025, pbk **9781032444635**) | Practising French Grammar: A Workbook, **5e** (Lamy/Towell/Hawkins, Routledge 2025, pbk **9781032441405**) | **HIGH** |
| ES | A New Reference Grammar of Modern Spanish, **6e** (Butt/Benjamin/Moreira Rodríguez, Routledge 2019, pbk **9781138124011**) | Practising Spanish Grammar, **4e** (Howkins/Pountain/de Carlos, Routledge 2019, pbk **9781138339279**) | **HIGH** |
| IT | A Reference Grammar of Modern Italian, **2e** (Maiden/Robustelli, Routledge 2007, pbk **9780340913390**) | Practising Italian Grammar: A Workbook, **1e** (Bianchi/Boscolo/Harrison, Routledge 2004, pbk **9780340811443**) | **HIGH** (pair identity) / MEDIUM (book age, ebook format risk) |
| PT | Modern Brazilian Portuguese Grammar: A Practical Guide, **3e** (Whitlam/Silveira, Routledge 2023, pbk **9781032244334**) | Modern Brazilian Portuguese Grammar Workbook, **3e** (Whitlam/Silveira, Routledge 2023, pbk **9781032244426**) | **MEDIUM-HIGH** (no true "Routledge Reference Grammars" entry exists for Portuguese — see ghost-book warning) |

Series membership ground truth (from the series pages printed in the
FR 5e front matter, 2025): **Routledge Reference Grammars** = Italian 2e,
French 5e, Spanish 6e, Hammer's German 7e — *no Portuguese*.
**Practising Grammar Workbooks** = Italian, Spanish 4e, French 5e,
German 4e — *no Portuguese*.

### WARNING — ghost book, do not chase

**"Portuguese: A Comprehensive Grammar" (Routledge Comprehensive
Grammars, ISBN 9780415550093 hbk / 9780415550109 pbk, attributed to
Maria Inês Pedrosa da Silva Duarte, "Dec 2023")** appears in retail
metadata feeds (indie bookstore sites, AbeBooks) but is
**announced-never-published vaporware** (ISBN block registered ~2009,
date keeps slipping). It has **no product page on routledge.com** and is
**absent from Routledge's own catalogue search**, which lists Comprehensive
Grammars for Dutch, Japanese, Danish, Norwegian, Polish, Catalan, Chinese,
etc. — but not Portuguese. Do not try to download it.

---

## FRENCH

### A. Reference grammar — IDENTIFIED

- **Title**: *French Grammar and Usage* (Routledge Reference Grammars)
- **Authors**: Richard Towell, Marie-Noëlle Lamy, Roger Hawkins
  (author order changed in 5e; earlier editions "Hawkins & Towell")
- **Edition**: **5th edition, 2025** (published 2025-01-31; 1e Hodder 1997, 4e Routledge 2015)
- **Publisher**: Routledge
- **ISBN-13**: pbk **978-1-032-44463-5** (9781032444635); hbk 978-1-032-44791-9;
  ebk 978-1-003-37392-6 (DOI 10.4324/9781003373926)
- **Earlier edition materially different?** Moderately. 4e (2015, pbk
  9781138851115) has the **same 17-chapter macro-structure**, but 5e
  inserts new sections (e.g. 1.4 *Nouvelle Orthographe*, 4.15 adjective
  agreement in inclusive writing), updates examples, and adds
  chapter+section running headers — so section-level anchor numbers
  shift in places. Use 5e; it is what Practising French Grammar 5e keys to.

### B. Workbook — IDENTIFIED

- **Title**: *Practising French Grammar: A Workbook* (Practising Grammar Workbooks)
- **Authors**: Marie-Noëlle Lamy, Richard Towell, Roger Hawkins
- **Edition**: **5th edition, 2025** (published 2025-01-31, 314 pp)
- **Publisher**: Routledge
- **ISBN-13**: pbk **978-1-032-44140-5** (9781032441405); hbk 978-1-032-44798-8;
  ebk DOI 10.4324/9781003373957
- Chapters **mirror the grammar 1:1** (identical 17 chapter titles,
  verified on the Routledge TOC); back matter includes **"Answers to the
  exercises"** and a glossary. Instructor/student resource site:
  routledgelearning.com/frenchgrammarandusage.

### C. Alternative reference

Not needed — Hawkins/Towell/Lamy is the canonical advanced reference and
the exact series sibling of Hammer's. (Wiley-Blackwell's *A Comprehensive
French Grammar* (Price, 7e) exists but has no companion workbook and no
chapter parity with the Practising series.)

### D. Confidence

- Grammar: **HIGH** — same series, same publisher, same structure role as Hammer's.
- Workbook: **HIGH** — official companion, chapter-for-chapter mirror, answer key.

### E. Extraction quirks

- **Numbered anchors: yes, Hammer-style.** Three heading levels:
  chapter → `2.6` (section) → subsection; the user guide explicitly
  describes the `Chapter 2 / 2.6 / …` scheme, and 5e adds
  chapter+section running headers and denser cross-referencing.
- **Formats**: born-digital 2025 T&F title, sold as VitalSource eBook
  (EPUB + page-replica variants typical for current T&F). The public T&F
  preview is a text-layer PDF (no OCR needed in any case). EPUB should
  exist at retail; if only PDF is obtainable it is born-digital text.
- **Structure**: 17 chapters; workbook has concise summaries + exercises
  per chapter with answers in the back — same authoring shape as
  Practising German Grammar.

### Unit registry sketch (17 units — clean 1:1 chapter keying, like DE)

Keyed to *Practising French Grammar 5e* chapters = *French Grammar and
Usage 5e* chapters (identical numbering, verified against both TOCs):

```python
FR_UNITS: dict[str, tuple[int, str]] = {
    "substantifs":      (1,  "Substantifs (nouns)"),
    "determinants":     (2,  "Déterminants (articles & determiners)"),
    "pronoms":          (3,  "Pronoms (personal & impersonal pronouns)"),
    "adjectifs":        (4,  "Adjectifs (adjectives)"),
    "adverbes":         (5,  "Adverbes (adverbs)"),
    "nombres":          (6,  "Nombres & quantité (numbers, measurements, time)"),
    "conjugaison":      (7,  "Conjugaison (verb forms)"),
    "constructions":    (8,  "Constructions verbales (incl. pronominal verbs, valency)"),
    "accord":           (9,  "Accord du participe (verb & participle agreement)"),
    "temps":            (10, "Temps (tense: passé composé vs imparfait, etc.)"),
    "subjonctif":       (11, "Subjonctif & modaux (subjunctive, modal verbs, exclamatives)"),
    "infinitif":        (12, "Infinitif (infinitives)"),
    "prepositions":     (13, "Prépositions (prepositions)"),
    "interrogation":    (14, "Interrogation (question formation)"),
    "relatives":        (15, "Relatives (relative clauses)"),
    "negation":         (16, "Négation (negation)"),
    "conjonctions":     (17, "Conjonctions & liaison (linking constructions)"),
}
```

Hot-topic coverage: subjonctif = ch. 11; passé composé/imparfait = ch. 10;
pronominal verbs = ch. 8 (verb constructions); agreement of past
participle (the classic C1 pain point) gets its own unit via ch. 9.

---

## SPANISH

### A. Reference grammar — IDENTIFIED

- **Title**: *A New Reference Grammar of Modern Spanish* (Routledge Reference Grammars)
- **Authors**: John Butt, Carmen Benjamin, Antonia Moreira Rodríguez
- **Edition**: **6th edition, 2019** (published 2018-11/2019-01)
- **Publisher**: Routledge
- **ISBN-13**: pbk **978-1-138-12401-1** (9781138124011); hbk 9781138124004;
  ebk DOI 10.4324/9781315648446 (EPUB variant 9781317301028)
- **Earlier edition materially different?** **Yes — renumbered.** The 5e
  (2011) merged what 6e splits: articles are one chapter in 5e vs 6e
  ch. 3–4; personal pronouns one chapter vs 6e ch. 12–14; indicative
  tenses one chapter vs 6e ch. 17–18; nominalizers/cleft split into
  6e ch. 40–41. Chapter/section anchors are **not** portable between 5e
  and 6e, and Practising Spanish Grammar 4e mirrors the **6e**
  organization. Must use 6e.

Full 6e chapter list (extracted from the publisher preview EPUB
`contents.xhtml`): 1 Gender of nouns · 2 Plural of nouns · 3 The definite
article · 4 The indefinite article · 5 Adjectives · 6 Comparison of
adjectives and adverbs · 7 Demonstrative adjectives and pronouns ·
8 Neuter article and neuter pronouns · 9 Possessive adjectives and
pronouns · 10 Miscellaneous adjectives and pronouns · 11 Numerals ·
12 Personal pronouns, subject · 13 Personal pronouns used with
prepositions · 14 Personal pronouns, object · 15 *Le/les* and
*lo/la/los/las* · 16 Forms of Spanish verbs · 17 Use of indicative
(non-continuous) verb tenses · 18 … compound tenses · 19 Continuous forms
of verbs · 20 The subjunctive · 21 The imperative · 22 The infinitive ·
23 Participles · 24 The gerund · 25 Auxiliary verbs · 26 Personal *a* ·
27 Negation · 28 Questions and exclamations · 29 Conditional sentences ·
30 Pronominal verbs · 31 Verbs of becoming · 32 Passive and impersonal
sentences · 33 *Ser* and *estar* · 34 'There is/are' etc. · 35 Adverbs ·
36 Expressions of time · 37 Conjunctions and discourse markers ·
38 Prepositions · 39 Relative clauses and relative pronouns ·
40 Nominalizers · 41 Cleft sentences · 42 Word order · 43 Diminutive,
augmentative and pejorative suffixes · 44 Spelling, accent rules,
punctuation and word division.

### B. Workbook — IDENTIFIED

- **Title**: *Practising Spanish Grammar* (Practising Grammar Workbooks)
- **Authors**: Angela Howkins, Christopher J. Pountain, Teresa de Carlos
- **Edition**: **4th edition, 2019** (published 2019-01-23, 308 pp)
- **Publisher**: Routledge
- **ISBN-13**: pbk **978-1-138-33927-9** (9781138339279); hbk 9781138339262;
  ebk 9780429441165 (variants: pdf 9780429805202 / **epub 9780429805196** / mobi 9780429805189)
- 4e was **reorganized to "closely mirror" B&B 6e** (publisher's own
  description). 33 chapters incl. "General exercises" finale, plus
  **"Key to the Exercises"** (answer key) and glossary — verified on the
  Routledge TOC.

### C. Alternative reference

Not needed — Butt & Benjamin is *the* canonical advanced Spanish
reference (the book the prompt's German pair analogy names). No stronger
alternative exists at this level.

### D. Confidence

- Grammar: **HIGH** — series sibling of Hammer's, canonical, current edition verified.
- Workbook: **HIGH** — official companion (Routledge even sells a bundle,
  ISBN 9780367086725), 6e-aligned organization, answer key.

### E. Extraction quirks

- **Numbered anchors: yes, the densest of all four.** B&B numbers to
  three levels (e.g. §20.3.19 within The subjunctive) and cross-references
  constantly — ideal citation anchors, richer than Hammer's.
- **Formats**: **reflowable EPUB confirmed** — the publisher preview EPUB
  (OEBPS/*.xhtml + toc.ncx) was unzipped and parsed with ElementTree
  during this research; the retail 6e ebook is the same production. Best
  extraction target of the four languages. The workbook also has a
  dedicated epub ISBN (9780429805196).
- **Structure**: 44 short, sharply-scoped chapters; workbook exercises
  carry cross-references to B&B sections and answers are in the book.

### Unit registry sketch (24 units)

DE keys units to workbook chapters; do the same here. Practising Spanish
Grammar 4e chapters (verified TOC) are given first; B&B 6e chapters cited
for lesson-content extraction. 32 topical workbook chapters are merged
into 24 units (mergers noted):

```python
ES_UNITS: dict[str, tuple[int, str]] = {  # (PSG4 chapter, label)
    "sustantivos":    (1,  "Sustantivos (nouns; B&B 1-2)"),
    "articulos":      (2,  "Artículos (articles; B&B 3-4)"),
    "adjetivos":      (3,  "Adjetivos & comparación (PSG 3-4; B&B 5-6)"),
    "demostrativos":  (5,  "Demostrativos, neutro & posesivos (PSG 5-7; B&B 7-9)"),
    "numerales":      (8,  "Numerales (numbers; B&B 11)"),
    "pronombres":     (9,  "Pronombres personales (PSG 9; B&B 12-15: le/lo/la, leísmo)"),
    "conjugacion":    (10, "Conjugación (forms of verbs; B&B 16)"),
    "tiempos":        (11, "Tiempos de indicativo (PSG 11; B&B 17-19)"),
    "subjuntivo":     (12, "Subjuntivo (B&B 20)"),
    "imperativo":     (13, "Imperativo (B&B 21)"),
    "infinitivo":     (14, "Infinitivo, participio & gerundio (PSG 14; B&B 22-24)"),
    "modales":        (15, "Auxiliares modales: poder, saber, deber (B&B 25)"),
    "a_personal":     (16, "A personal (B&B 26)"),
    "negacion":       (17, "Negación (B&B 27)"),
    "interrogacion":  (18, "Preguntas & exclamaciones (B&B 28)"),
    "condicionales":  (19, "Oraciones condicionales (B&B 29)"),
    "pronominales":   (20, "Verbos pronominales, 'hacerse' & pasiva (PSG 20-22; B&B 30-32)"),
    "ser_estar":      (23, "Ser, estar & haber (B&B 33-34)"),
    "adverbios":      (24, "Adverbios & expresiones de tiempo (PSG 24-25; B&B 35-36)"),
    "conjunciones":   (26, "Conjunciones & marcadores (B&B 37)"),
    "preposiciones":  (27, "Preposiciones: por/para etc. (B&B 38)"),
    "relativas":      (28, "Relativas, nominalización & énfasis (PSG 28-29; B&B 39-41)"),
    "orden_palabras": (30, "Orden de palabras (B&B 42)"),
    "ortografia":     (32, "Ortografía, acentos & sufijos (PSG 31-32; B&B 43-44)"),
}
```

Hot-topic coverage: ser/estar = own unit (B&B 33); subjuntivo = own unit
(B&B 20, the biggest chapter in the book); por/para inside preposiciones
(B&B 38.14 area); pronoun le/lo battles = pronombres (B&B 15).

---

## ITALIAN

### A. Reference grammar — IDENTIFIED

- **Title**: *A Reference Grammar of Modern Italian* (Routledge Reference Grammars)
- **Authors**: Martin Maiden, Cecilia Robustelli
- **Edition**: **2nd edition, 2007** (published 2007-05-25; originally
  Hodder Arnold, now Routledge; hardback reissue 2015 ISBN 9781138170872).
  **No 3rd edition exists** (still "Second Edition" on the 2025 series page).
- **Publisher**: Routledge (Copyright 2007, 512 pp)
- **ISBN-13**: pbk **978-0-340-91339-0** (9780340913390); hbk reissue
  9781138170872; ebk DOI 10.4324/9780203783504 (ISBN 9780203783504)
- **Earlier edition materially different?** 1e (Arnold, 2000) is
  superseded; 2e revised/expanded with the same overall shape. Only 2e
  matters — it is the edition the workbook keys to and the only one in print.

Chapter list (verified on Routledge TOC): 1 Introduction · 2 Spelling and
pronunciation · 3 Nouns and adjectives · 4 The articles ·
5 Demonstratives · 6 Personal pronouns · 7 Relative structures ·
8 Interrogative structures · 9 Indefinite, quantifier and negative
pronouns and adjectives · 10 Possessives and related constructions ·
11 Prepositions · 12 Numerals and related expressions · 13 Adverbs and
adverbial constructions · 14 Forms of the verb · 15 Uses of the verb
forms · 16 Comparative, superlative and related constructions ·
17 Aspects of sentence structure · 18 Negative constructions ·
19 Conjunctions and discourse markers · 20 Word derivation ·
21 Time expressions · 22 Forms of address.

### B. Workbook — IDENTIFIED

- **Title**: *Practising Italian Grammar: A Workbook* (Practising Grammar Workbooks)
- **Authors**: Alessia Bianchi, Clelia Boscolo, Stephen Harrison
- **Edition**: **1st edition, 2004** (published 2004-03-26, 236 pp — only edition)
- **Publisher**: Routledge (orig. Hodder Arnold)
- **ISBN-13**: pbk **978-0-340-81144-3** (9780340811443); hbk reissue
  9781138169272; ebk 9780203768068
- Explicitly "designed as a companion volume to *A Reference Grammar of
  Modern Italian*". Its 21 chapters track M&R chapters 2–22 **offset by
  one** (workbook ch. N = M&R ch. N+1; M&R ch. 1 "Introduction" has no
  exercises): verified TOC = 1 Spelling and pronunciation · 2 Nouns and
  adjectives · 3 Articles · 4 Demonstratives · 5 Personal pronouns ·
  6 Relative structures · 7 Interrogative structures · 8 Indefinites and
  negative pronouns and adjectives · 9 Possessives · 10 Prepositions ·
  11 Numerals · 12 Adverbs · 13 Forms of the verb · 14 Uses of verb
  forms · 15 Comparatives and superlatives · 16 Aspects of sentence
  structure · 17 Negative constructions · 18 Conjunctions and discourse
  markers · 19 Word derivation · 20 Time expressions · 21 Forms of
  address. Answer key: series standard (the Routledge TOC listing
  truncates back matter; the print book carries worked answers — verify
  on download).

### C. Alternative reference

None stronger exists; Maiden & Robustelli **is** the book the prompt
names and the series sibling of Hammer's. (Routledge's *Modern Italian
Grammar* (Proudfoot/Cardo, 3e 2013) is the functional-series fallback —
solid but a practical guide, not a comprehensive reference; only relevant
if the M&R ebook proves unusable.)

### D. Confidence

- Grammar: **HIGH** on identity (unambiguous equivalent); the book is
  2007 vintage — content ages fine for grammar, but note it predates some
  orthography debates.
- Workbook: **HIGH** on identity (official companion). **MEDIUM** on
  extraction: 2004 Hodder production (see E).

### E. Extraction quirks

- **Numbered anchors: yes.** M&R numbers sections within chapters
  (chapter.section, e.g. 15.x for uses of verb forms) and the workbook
  cross-references the grammar — usable as citation anchors, though
  section granularity is coarser than B&B's three-level scheme.
- **Formats — the risk pair of the four.** Both books predate born-digital
  T&F production; official T&F ebooks exist (DOIs above) but are likely
  **print-replica PDF, not reflowable EPUB**. Circulating copies (e.g.
  archive.org scan of the workbook) are scans. Expect the IT lane to need
  the PDF-with-text-layer path rather than the EPUB/ElementTree path; a
  legit VitalSource copy has a text layer (no OCR), a scan does not.
- **Structure**: grammar ch. 15 ("Uses of the verb forms") is a monster
  chapter carrying tenses AND congiuntivo AND conditional — unit content
  extraction will slice it by section ranges.

### Unit registry sketch (21 units — 1:1 with workbook chapters, like DE)

```python
IT_UNITS: dict[str, tuple[int, str]] = {  # (workbook chapter, label); M&R chapter = wb+1
    "ortografia":     (1,  "Ortografia & pronuncia (M&R 2)"),
    "sostantivi":     (2,  "Sostantivi & aggettivi (M&R 3)"),
    "articoli":       (3,  "Articoli (M&R 4)"),
    "dimostrativi":   (4,  "Dimostrativi (M&R 5)"),
    "pronomi":        (5,  "Pronomi personali & clitici (M&R 6)"),
    "relative":       (6,  "Strutture relative (M&R 7)"),
    "interrogative":  (7,  "Strutture interrogative (M&R 8)"),
    "indefiniti":     (8,  "Indefiniti & negativi (M&R 9)"),
    "possessivi":     (9,  "Possessivi (M&R 10)"),
    "preposizioni":   (10, "Preposizioni (M&R 11)"),
    "numerali":       (11, "Numerali (M&R 12)"),
    "avverbi":        (12, "Avverbi (M&R 13)"),
    "coniugazione":   (13, "Coniugazione (forms of the verb; M&R 14)"),
    "tempi_modi":     (14, "Tempi & modi: congiuntivo, condizionale, passato (M&R 15)"),
    "comparativi":    (15, "Comparativi & superlativi (M&R 16)"),
    "sintassi":       (16, "Struttura della frase: si, passivo, ordine (M&R 17)"),
    "negazione":      (17, "Negazione (M&R 18)"),
    "congiunzioni":   (18, "Congiunzioni & segnali discorsivi (M&R 19)"),
    "derivazione":    (19, "Derivazione delle parole (M&R 20)"),
    "tempo_espr":     (20, "Espressioni di tempo (M&R 21)"),
    "allocutivi":     (21, "Forme allocutive: tu/Lei (M&R 22)"),
}
```

Editorial option: `tempi_modi` (wb 14 / M&R 15) is overweight — if a unit
needs splitting, carve congiuntivo out as a second unit keyed to the same
chapter with a section-range filter (M&R 15, congiuntivo sections), the
way DE separates tempora/konjunktiv even though Hammer folds moods together.

---

## PORTUGUESE

### A. Reference grammar — IDENTIFIED (with caveat)

There is **no Portuguese entry** in the Routledge Reference Grammars
series and no published Routledge Comprehensive Grammar (see ghost-book
warning above). The strongest Routledge-family equivalent:

- **Title**: *Modern Brazilian Portuguese Grammar: A Practical Guide*
  (Routledge Modern Grammars)
- **Authors**: John Whitlam, Agripino S. Silveira
- **Edition**: **3rd edition, 2023** (published 2022-12-30, 572 pp;
  1e 2011, 2e 2017)
- **Publisher**: Routledge
- **ISBN-13**: pbk **978-1-032-24433-4** (9781032244334); hbk and
  VitalSource eBook also available
- **Earlier edition materially different?** 2e (2017) has the same
  Part A shape; 3e adds "Notes for Spanish speakers" (useful for this
  owner's profile), revised exercises alignment, expanded coverage. Use 3e —
  it matches the 3e workbook.
- **Caveat**: Brazilian Portuguese focus (the owner should confirm BP is
  acceptable; for European Portuguese see C). Part A "Structures"
  (ch. 1–28) is a genuine reference grammar organized like the other
  registries; Part B (ch. 29–71) is functional/situational and can be
  ignored by the course factory or mined for drill sentences.

Part A chapter list (verified on Routledge TOC + preview PDF): 1
Pronunciation and spelling · 2 Gender and gender agreement · 3 Number and
number agreement · 4 Articles · 5 Adjectives and adverbs · 6 Numbers and
numerical expressions · 7 Personal pronouns · 8 Demonstratives ·
9 Possessives · 10 Relative pronouns · 11 Interrogatives ·
12 Exclamations · 13 Indefinite adjectives and pronouns · 14 Negatives ·
15 Regular verb conjugations · 16 Semi-irregular and irregular verbs ·
17 Gerunds, past participles, compound perfect tenses and the passive ·
18 Use of the tenses · 19 The infinitive · 20 The subjunctive · 21 The
imperative · 22 Reflexive verbs · 23 *Ser*, *estar* and *ficar* · 24 Verbs
used in auxiliary, modal and impersonal constructions · 25 Prepositions ·
26 Conjunctions · 27 Word order · 28 Word formation.

### B. Workbook — IDENTIFIED (no "Practising" companion exists for PT)

**Rank 1 (recommended):**

- **Title**: *Modern Brazilian Portuguese Grammar Workbook* (Modern Grammar Workbooks)
- **Authors**: John Whitlam, Agripino S. Silveira
- **Edition**: **3rd edition, 2023**
- **Publisher**: Routledge
- **ISBN-13**: pbk **978-1-032-24442-6** (9781032244426); hbk
  978-1-032-24446-4; ebk 978-1-003-27862-7
- Part A exercises keyed **1:1 to the Grammar's Part A chapters 1–28**
  (same numbering — verified in the preview: identical chapter list),
  cross-references from Part B to Part A, and a **comprehensive answer
  key**. This is functionally the "Practising Portuguese Grammar" that
  Routledge never made.

**Rank 2 (European-Portuguese alternative):**

- **Title**: *Gramática Ativa 2* (versão portuguesa, segundo o Novo
  Acordo Ortográfico), levels B1+/B2/C1
- **Authors**: Olga Mata Coimbra, Isabel Coimbra
- **Edition**: current Lidel printing (2017), 136 pp
- **Publisher**: Lidel (Lisbon)
- **ISBN-13**: **978-972-757-863-4** (9789727578634); Lidel also sells a
  36-month-access eBook. Note there is a separate *versão brasileira* —
  don't confuse the two.
- Two-page unit format (grammar point left, exercises right) with
  solutions in the back; the C1-level standard in EP classrooms. Weaker
  as a course-factory source (no prose reference text, no section
  numbering to cite), which is why it ranks second.

Rejected for rank: *Ponto de Encontro* activities manual (tied to a
Pearson textbook's lesson sequence, not a grammar registry);
*The Portuguese Subjunctive: A Grammar Workbook* (Gomes/Gonçalves,
Routledge 2020, ISBN 9780367441791) — excellent but single-topic; keep it
in mind as a supplement for the subjuntivo unit.

### C. Alternative reference grammar

- **Title**: *Portuguese: A Reference Manual*
- **Authors**: Sheila R. Ackerlind, Rebecca Jones-Kellogg
- **Edition**: 1st, **2011**
- **Publisher**: University of Texas Press
- **ISBN-13**: pbk **978-0-292-72673-4** (9780292726734); hbk
  9780292726635; Kindle edition exists
- Brazilian-focused but flags European variants; organized as a true
  reference manual. Use if a second citation source is wanted; UT Press
  ebook is not XHTML-friendly (Kindle/print-replica).
- For **European Portuguese** specifically, the only in-print Routledge
  reference is *Portuguese: An Essential Grammar*, 3e
  (Hutchinson/Lloyd/Sousa, ISBN 9781138234352) — but it is B1-ish
  "Essential" depth, not a C1 comprehensive grammar; not recommended as
  the course spine.

### D. Confidence

- Grammar: **MEDIUM-HIGH** — it is the best *existing* Routledge
  equivalent (the true series sibling does not exist). High confidence in
  the identification itself; the medium component is the BP-vs-EP fit,
  which is an owner decision, not a bibliographic uncertainty.
- Workbook: **HIGH** — official companion, 1:1 chapter parity, answer key.

### E. Extraction quirks

- **Numbered anchors: yes.** Modern Grammars use chapter.section.subsection
  numbering (e.g. 18.2.1 under "Use of the tenses") with Part B → Part A
  cross-references; anchors are citable like Hammer's.
- **Formats**: born-digital 2023 T&F production; ebook sold via
  VitalSource/Kindle; the T&F ebook family includes EPUB (the workbook's
  T&F preview is text-layer PDF; retail EPUB expected — same production
  pipeline as the ES workbook whose epub ISBN is explicit).
- **Structure**: only Part A (ch. 1–28) is registry material; Part B is
  situational. The workbook's Part A mirrors the grammar exactly, so the
  DE mechanism (unit = workbook chapter) ports cleanly. Audio companion
  website exists (irrelevant to extraction).

### Unit registry sketch (24 units)

Keyed to Workbook/Grammar **Part A** chapters (identical numbering in
both books — cite `MBPG3 ch. N`):

```python
PT_UNITS: dict[str, tuple[int, str]] = {  # (Part A chapter, label)
    "ortografia":     (1,  "Ortografia & pronúncia"),
    "concordancia":   (2,  "Género & número (ch. 2-3)"),
    "artigos":        (4,  "Artigos"),
    "adjetivos":      (5,  "Adjetivos & advérbios"),
    "numerais":       (6,  "Numerais"),
    "pronomes":       (7,  "Pronomes pessoais & colocação de clíticos"),
    "demonstrativos": (8,  "Demonstrativos & possessivos (ch. 8-9)"),
    "relativos":      (10, "Pronomes relativos"),
    "interrogativos": (11, "Interrogativos & exclamações (ch. 11-12)"),
    "indefinidos":    (13, "Indefinidos"),
    "negacao":        (14, "Negação"),
    "conjugacao":     (15, "Conjugação regular & irregular (ch. 15-16)"),
    "participios":    (17, "Gerúndio, particípios, perfeito composto & passiva"),
    "tempos":         (18, "Uso dos tempos"),
    "infinitivo":     (19, "Infinitivo (incl. infinitivo pessoal)"),
    "subjuntivo":     (20, "Subjuntivo/conjuntivo"),
    "imperativo":     (21, "Imperativo"),
    "reflexivos":     (22, "Verbos reflexivos"),
    "ser_estar":      (23, "Ser, estar & ficar"),
    "modais":         (24, "Auxiliares, modais & construções impessoais"),
    "preposicoes":    (25, "Preposições"),
    "conjuncoes":     (26, "Conjunções"),
    "ordem_palavras": (27, "Ordem das palavras"),
    "formacao":       (28, "Formação de palavras"),
}
```

Hot-topic coverage: the flagship PT topics all have dedicated chapters —
personal/inflected infinitive (ch. 19), ser/estar/**ficar** (ch. 23),
future subjunctive inside ch. 20, clitic placement inside ch. 7.

---

## Cross-language extraction summary for the pipeline

| Property | FR 5e pair | ES 6e/4e pair | IT 2e/1e pair | PT 3e pair |
|---|---|---|---|---|
| Numbered §§ anchors | yes (`10.4`) | yes, 3-level (`20.3.19`) | yes, coarser (`15.x`) | yes (`18.2.1`) |
| Reflowable EPUB | expected (born-digital 2025) | **confirmed** (XHTML parsed in this session) | **doubtful — likely print-replica PDF** | expected (born-digital 2023) |
| Workbook↔grammar chapter parity | 1:1, same numbers | mirrored, own 33-ch numbering + §-refs | 1:1 offset by one | 1:1, same numbers (Part A) |
| Workbook answer key | yes ("Answers to the exercises") | yes ("Key to the Exercises") | series standard (verify on download) | yes (comprehensive key) |
| Units proposed | 17 | 24 | 21 | 24 |

Recommended download order of preference per book: T&F/VitalSource EPUB →
T&F born-digital PDF (text layer, no OCR) → anything else. The Italian
pair is the only one where the EPUB path will probably fail; plan for the
PDF-text path there.
