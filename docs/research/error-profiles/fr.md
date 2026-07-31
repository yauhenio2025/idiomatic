# Learner Error Profile — French (fr)

> Mined 2026-07-31 from 5+ years of teacher-marked errors (weekly 1:1
> lessons). Sources: `xlsx_fr.jsonl` (3,925 rows) + `teachee_fr.jsonl`
> (1,350 notes). Classification is heuristic (regex cascade over
> correct/error pairs, script-assisted) — counts are approximate but
> the ranking is robust; every quoted example is verbatim from the data.

## 1. Data inventory

| Source | Rows | Era | Notes |
|---|---|---|---|
| xlsx_fr.jsonl | 3,925 | dated 2021-06 → 2022-09 | 2,823 rows carry the single date 2021-06-04 → bulk import of the pre-2021 backlog; real span is ≈2019-2022 |
| — use-flagged | 2,670 (2,523 with recorded error) | | grammar-usage corrections — the core corpus |
| — vocab-flagged | 1,215 (936 with recorded error) | | 77% of "vocab" rows record what the learner actually said → mostly lexical *confusions*, not pure gaps |
| — pron-flagged | 101 | | mixed field orientation (correction sometimes in `error`, note like `ne prononce pas le "T"` in either field) |
| — flag combos | vocab+use 84, use+pron 4, no flag 28 | | |
| teachee_fr.jsonl | 1,350 | 2022-11 → 2024-11 (31 lesson decks) | 425 notes = [EN prompt, FR+IPA], 925 = FR+IPA only. 1,102/1,350 are 3+-word phrases (teacher teaches chunks). Almost all are *taught correct forms*; error status must be inferred by matching against xlsx-era trouble spots |

Quality caveats: IPA is concatenated to the French text with no
separator (and contains junk like `igʁɛk` for the letter y,
`undefined`); a few xlsx rows have swapped correct/error fields or
`xxx` placeholders; the parenthesis-marks-the-correction convention
holds for only ~1/3 of use rows (the rest: `correct` = full corrected
phrase, `error` = the wrong fragment). Tense/mood errors are likely
under-captured relative to real speech — a teacher typing during
conversation catches word-level slips more reliably than tense choice.

## 2. Grammar error taxonomy (use-flagged rows, n=2,523 classified)

Ranked by count. ~735 residual rows are lexical recasts/one-off
rephrasings that don't reduce to a grammar rule (plus stragglers of the
categories below — targeted pattern counts in §3 include those).

### 2.1 Preposition selection — ≈635 rows (25%)
The #1 category by far. Four sub-families:

**(a) General prep selection (475):** top confusion pairs from the swap
matrix: Ø→de 35, de→Ø 24, à→de 23, dans→à 22, dans→Ø 17, de→du 14,
dans→en 13, en→sur 11, pour→pendant 11, chez→dans 11, en→au 10.
- `dans la télévision` → `à la télévision`
- `pour 2, 3 jours` → `pendant 2, 3 jours`
- `quand je pense de ce mot` → `quand je pense à ce mot`
- `très proche à la mer` → `très proche de la mer`
- `en Zoom` → `sur Zoom`

**(b) Prep before infinitive (77):** the à/de/Ø regime.
- `c'est difficile à parler` → `c'est difficile de parler` (difficile/impossible + à: ~20×)
- `c'est très difficile trouver` → `très difficile de trouver` (Ø for de: 8×)
- `je cherche de m'isoler` → `je cherche à m'isoler` (chercher de: 10×)
- `j'ai commencé lire` / `on a commencé de parler` → `commencé à` (4×)
- `j'ai décidé à lire` → `j'ai décidé de lire`

**(c) Place prepositions (56):** `en + city` is a signature error
(es/it interference: *en Berlín*, *a/in* mapped wrong).
- `en Berlin` (9×), `en Paris` (6×), `en Rome` (5×), `en Barcelone` (4×) → `à`
- `en Chili` (5×), `en Brésil` (3×) → `au Chili`, `au Brésil`
- `dans l'Asie` → `en Asie`

**(d) Missed contractions (27):** `de les` → `des`, `à le` → `au`.
- `beaucoup de les activités` → `beaucoup d'activités`
- `autour de le concept` → `autour du concept`
- `la chute de la mur de Berlin` → `la chute du mur de Berlin`

### 2.2 Gender & agreement — ≈396 rows (16%)
**(a) Noun gender via determiner (297):** a stable personal list of
wrong-gender nouns, repeated across years. Top offenders: période (10),
fois (8 incl. `le première fois`), vie (6), mode (5), carrière (5),
présentation (4), site (4), parti (4), leçon (4), moyen (4),
processus (4), méthode (4), logiciel (3), cadre (3), question (3),
ville (3), conférence (3), région (3), livre (3).
- `ce période` → `cette période` · `mon vie` → `sa/ma vie` · `une processus` → `un processus`
- `le première fois` → `la première fois` · `mon leçon de chinois` → `ma leçon de chinois`

**(b) Adjective/participle agreement (49):**
- `beaucoup de personnes importants` → `importantes`
- `une politique très indépendant` → `indépendante`
- `Amérique Latin` → `Amérique Latine` (8× across vocab/use/pron)
- `des téléphones faits`… said `faites` (and the reverse elsewhere)

**(c) -al plural morphology (50):** `-als` instead of `-aux`.
- `les ennemis principals` → `principaux`
- `les marchés sont devenus globals` → `globaux`
- `les groupes socials` → `sociaux` · `les hôpitaux` said `les hospitaux`

### 2.3 Articles & quantifiers — ≈215 rows (9%)
**(a) `beaucoup/trop/assez + des` (161 classified; 138 by direct
pattern count):** THE single most repeated error in the corpus.
- `beaucoup des articles` (10+×), `beaucoup de l'argent` (15×) → `beaucoup d'articles`, `beaucoup d'argent`
- `des autres choses` → `d'autres choses`
- `la plupart d'eux` (5×) → `la plupart d'entre eux`
- Teachee corroboration: **"beaucoup" appears in 119 taught phrases
  2022-2024, zero occurrences of "beaucoup des"** — the teacher drilled
  the correct pattern for two more years.
**(b) Missing article with countries/languages:** `visiter Turquie` →
`visiter la Turquie`, `à Biélorussie` → `à la Biélorussie`, `qui
apprend japonais` → `le japonais`, `je connais Italie` → `l'Italie`.
**(c) Superlative missing second article (11):** see §2.6.

### 2.4 Verb morphology — 132 rows (5%)
Wrong form of the right tense; 3pl of irregular -ir/-re/-oir verbs is
the epicentre (matches shipped unit fr_present_irreguliers).
- `les images qui provient` → `proviennent` · `ils comprend vraiment` → `comprennent`
- `les régions choisent` → `choisissent` · `ils préfièrent` → `préfèrent` (stem vowel, also in pron rows)
- `nous était` → `nous étions` · `je prendais souvent` → `je prenais`
- `j'ai producé` → `j'ai produit` · `Comment tu as décrivé?` → `décrit`

### 2.5 an/année, jour/journée — ≈100 rows (4%)
A single lexico-grammatical opposition responsible for ~4% of all
errors; fully fossilized (recurs monthly through the corpus).
- `cet an` (7×), `chaque an` (5×) → `cette année`, `chaque année`
- `dans les ans 70/90/50/…` (28×) → `dans les années 70…`
- `derniers 5 ans` → `les 5 dernières années` (compound with §2.6)
- `beaucoup des ans` → `beaucoup d'années`

### 2.6 Word order — ≈130 rows (5%)
**(a) Adverb placement (60+):** adverb between subject and finite verb
(English order).
- `je déjà connais` → `je connais déjà` · `vous déjà savez que` → `vous savez déjà que`
- `il aussi parvient à créer` → `il parvient aussi à créer`
- `le gouvernement clairement veut` → `veut clairement`
- `on ne jamais arrivera` → `on n'arrivera jamais` · `qu'ils n'ont rencontré jamais` → `n'ont jamais rencontré`
**(b) NUM + dernier/premier/prochain order (73 by pattern + ~26 more in
residual ≈ 90-100):** massive, near-categorical.
- `les premières deux semaines` → `les deux premières semaines`
- `dans les derniers 10 ans` → `ces 10 dernières années`
- `les premières 60 sujets` → `les 60 premiers sujets`
- `dans les prochaines deux semaines` → `dans les deux prochaines semaines`
**(c) Superlative missing article (11):** `la chose plus grave` →
`la chose la plus grave`, `le numéro plus haut` → `le nombre le plus
élevé` (Italian pattern *la cosa più grave*).
**(d) Adjective placement:** `la solution meilleure` (5×), `la période
meilleure` (5×) → `la meilleure solution/période`.

### 2.7 Negation — ≈60 rows (2.4%)
**(a) Missing `pas` (43):** keeps only `ne` (Italian *non* pattern).
- `ce n'était très simple` → `ce n'était pas très simple`
- `ils n'utilisent les services` → `n'utilisent pas`
- `je n'ai autres options` → `je n'ai pas d'autres options`
**(b) Double negative with pas (11):** `ça n'intéresse pas personne` →
`ça n'intéresse personne`, `il n'y a pas aucune discussion` → `il n'y a
aucune discussion`, `personne ne pouvait pas` → `personne ne pouvait`.

### 2.8 Pronouns — ≈95 rows (3.8%)
**(a) y/en avoidance (27+; 22 `là`-for-`y` by direct count):** uses `là`
or omits the clitic entirely.
- `quand je retournerai là` → `quand j'y retournerai`
- `ils vont aller là` → `ils vont y aller`
- `nous avons déjà discuté X` → `nous en avons déjà discuté`
- `je n'ai pas une idée` → `je n'en ai aucune idée`
**(b) Relative qui/que (26 by direct count):** `que` as subject
relativizer (Italian *che* covers both).
- `des partis que critiquent` → `qui critiquent` · `une décision que va` → `qui va`
- `le magazine que suit` → `le magazine qui suit` · `une chose que consomme` → `qui consomme`
**(c) Other relatives (29):** missing dont/lequel/où — `des mécanismes
par laquelle` → `par lesquels`; Teachee 2022-24 then teaches 18
dont/lequel phrases → confirmed persistent gap.
**(d) Missing object clitic:** `j'ai déjà dit la dernière fois` → `je
l'ai déjà dit`, `comme ils déjà font` → `comme ils le font déjà`,
`ils veulent interviewer tous les deux` → `nous interviewer`.

### 2.9 Pronominal verbs — 15+ rows
Both directions: dropped `se` and spurious `se`.
- `on peut engager dans un débat` → `s'engager` · `travailler c'est comme reposer` → `se reposer`
- `les dépenses continuent à accroître` → `s'accroître` · `ce que ça va passer` → `ce qui va se passer`
- spurious: `il a dû se démissionner` → `démissionner` · `beaucoup de choses se sont changées` → `ont changé`

### 2.10 Tense/mood selection — ≈45 rows (1.8%) — NOTABLY RARE
tense_pc_impf 15 (`quand je partais de Zurich` → `quand je suis
parti`), subjunctive 13, future-after-quand 5, si-clause conditional 2,
aux choice 7 + `je suis réussi` 6 (`j'ai réussi`), missing aux
(`on découvert` → `on a découvert`, `je presque terminé` → `j'ai
presque terminé`). Tense *selection* is a minor error source for this
learner compared to gender/preps/articles — but note the capture
caveat in §1.

### 2.11 Syntactic calques & code-switching — ≈60 rows
- `est-ce que` for `c'est que` (6×): `L'avantage est-ce que` → `L'avantage c'est que` (frozen chunk misanalysis)
- `dans une façon/mode …` (28×) → `de manière/façon …`: `dans une façon compréhensive` → `de manière compréhensible`, `dans un mode permanent` → `de manière permanente`
- `la notre + N` (5×, Italian *la nostra*): `la notre maison` → `notre maison`
- `comme ça` for `tel` (4×): `un scénario comme ça` → `un tel scénario`
- `avant de + N` (6×): `avant de la pandémie` → `avant la pandémie`
- `après 2 ans` (5×) → `au bout de 2 ans`
- `faire + adj` → `rendre`: `faire le système plus démocratique` → `rendre le système plus démocratique`
- raw EN code-switch (8+): `save`, `traffic`, `to focus`, `a producer`
- Romance-verb inventions (17 in use +>30 in vocab): see §4.

## 3. Recurring structural patterns — fossilization candidates

Direct pattern counts over ALL error-bearing rows (n=3,501), ranked.
These are the drill targets; each recurred across multiple years.

| # | Pattern | Count | Fix |
|---|---|---|---|
| 1 | `beaucoup/trop des`, `de l'` | 138 | quantity word + de/d' invariable |
| 2 | an↔année, matin↔matinée, soir↔soirée | 102 | duration/appreciation -ée forms |
| 3 | dernier/premier/prochain BEFORE the numeral | 73 (+~26 residual) | `ces deux dernières années` |
| 4 | missing `pas` after ne | 43 | *non*≠`ne`: pas is obligatory |
| 5 | `en + city` | 36 | à + city, au/en + country |
| 6 | adverb before finite verb (`je déjà connais`) | 33 | adverb after finite verb |
| 7 | `dans les ans X0` | 28 | `dans les années X0` |
| 8 | `dans une façon/mode X` | 28 | `de manière/façon X` |
| 9 | `que` as subject relative | 26 | qui = subject, que = object |
| 10 | `là` for `y` / missing y | 22 | y replaces à+place |
| 11 | `difficile/impossible à + inf` | 20 | impersonal c'est … DE + inf |
| 12 | invented Romance verbs (insérir, transférir, mostrer…) | ~47 (use+vocab) | French infinitive form |
| 13 | wrong-gender core nouns (période, fois, méthode…) | ~297 | personal gender list |
| 14 | `-als` plurals | 50 | -al → -aux |
| 15 | superlative without 2nd article | 11 | `la chose LA plus grave` |
| 16 | double negation `pas rien/personne/aucun` | 11 | rien/personne replace pas |
| 17 | missing `en` partitive clitic | 11 | `nous EN avons discuté` |
| 18 | `chercher de` | 10 | chercher À + inf |
| 19 | `plus pire / plus mieux` | 10 | pire/mieux are already comparative |
| 20 | `je suis réussi` and avoir/être picks | 13 | réussir takes avoir |
| 21 | `est-ce que` for `c'est que` | 6 | L'avantage, c'est que… |
| 22 | `avant de + N` | 6 | avant + N directly |
| 23 | `après N ans` for elapsed time | 5 | au bout de N ans |
| 24 | `la plupart/beaucoup d'eux` | 8 | d'ENTRE eux after quantifiers |
| 25 | `la notre + N` | 5 | possessive det. has no article |

Persistence across eras: partie (la part→partie confusion, 16× in
xlsx) still being taught in Teachee 2023-24 (`les parties`, partie in
14 phrases); `de manière + adj` taught 15× in Teachee; `ces X
dernières années` shape taught 17×; dont/lequel relatives taught 18×.
Same holes, five years apart.

## 4. Vocabulary profile

936 of 1,215 vocab rows record what was actually said → the "vocab"
problem is dominantly *interference*, not absence:

- **Pan-Romance verb inventions** (es/pt/it morphology on French
  stems), the signature lexical error class: `incluir`(6), `insérir`(5),
  `transférir`(4), `gestir`(3), `attracter`(3), `invester`(3),
  `ralenter`(4), `impedir`(2), `expandir`(2), `mostrer`, `registrer`,
  `conquérer`, plus nouns `pensateur`(3)→penseur, `investiteurs`(3)
  →investisseurs, `la duration`(3)→durée, `une combination`(3)
  →combinaison, `stabile`(7)→stable, `semanal`(3)→hebdomadaire.
- **English faux amis / code-switch**: `effectif`(5)→efficace,
  `relevant`(3)→pertinent, `protests`(6)→manifestations,
  `incredible`(3)→incroyable, `ordonner`(3)→commander (to order),
  `repayer`(4)→rembourser, `manager`(2)→gérer, raw `to focus`,
  `to spend`, `inside`, `offline`.
- **Near-synonym pairs** repeatedly confused: part/partie (16),
  numéro/nombre (3+), procès/processus, temps/fois (`ce temps`→
  `cette fois-ci`), place/lieu, mode/manière/façon.
- **Domains** (top content words + Teachee decks): media & publishing
  (articles, magazine, maison d'édition, podcast(7), épisodes(6),
  chaîne, séries), politics/current affairs (manifestations(10),
  électeurs, gouvernement, parti, réformes), tech/work (logiciel, site,
  notification, mises à jour, processus(6), efficace(8)),
  pandemic-era (quarantaine(5), confinement, vaccin). Matches the
  learner's professional register (media/tech commentary).
- **Form factor**: Teachee is 82% multi-word chunks (1,102/1,350) —
  collocations and sentence frames, not single words. Vocab drills for
  this learner should be chunk-level.

## 5. Pronunciation profile (101 pron rows)

1. **Final-consonant rules, both directions** (~55 rows, the bulk):
   - Pronounced a silent final: coût "T" (6×), cours "S" (3×),
     chaos "S" (2×), aspect "C(T)" (2×), outils "L", vaccin "N",
     nom "M", nuit/format/attribut "T", plus the whole **-er/-ier R
     family** (premier, particulier(2), financier, boursiers, danger,
     conseiller, ouvrier, courrier — 9 rows).
   - Dropped a pronounced final: contact/impact "C,T" (4×), but/le
     but/BUT "T" (3×), sens "S" (2×), processus final "S", Madrid "D",
     net/Internet "T".
   - The -ct minimal contrast (aspect [ɛ] vs contact/impact [akt]) is
     drilled repeatedly — good F2-style contrast material.
2. **-tie = [si]**: démocratie (2×), bureaucratie — "t comme un s".
3. **Paragogic -é** (Italian/Spanish final-vowel habit): `sité` for
   site (4×), `tu payé`/`les utilisateurs payé` for paie(nt) (2×),
   `signifié` for signifie, `dédié` for dédie, `j'étude` for j'étudie.
4. **Intrusive/metathesized letters** (spelling-driven, cognate
   interference): `enterprise`(2), `Austriche`, `hospitaux`,
   `absolutement`, `commercielles`, `propaguer`, `prolonguer`,
   `plublié`, `interracte`.
5. **Stem vowel**: `préfière(nt)` for préfère(nt) (2×).
6. **False liaison**: `ils sont (z)arrivés`.
7. Isolated: `trè(?)` for trois, `magasin` for magazine (2×).

## 6. Curriculum mapping

Existing fr units (7 active + 1 planned) vs this evidence:

| Unit | Cluster | Evidence from data | Action |
|---|---|---|---|
| fr_present_irreguliers | 1 Temps | STRONG — verb_morph 132; 3pl irregulars (proviennent, comprennent, choisissent) are exactly this unit | Keep/raise target_size |
| fr_passe_compose | 1 Temps | MODERATE — aux choice 13 (`je suis réussi` 6×), missing aux 4, agreement in PC rare | Keep; bias items toward avoir/être verb choice, not endings |
| fr_imparfait | 1 Temps | WEAK-MODERATE — tense_pc_impf 15 | Keep small |
| fr_futur_simple | 1 Temps | WEAK — future-after-quand 5, almost no future-form errors | Lower |
| fr_conditionnel_present | 2 Conditionnel | WEAK — si-clause 2, near-zero conditional errors recorded | Lower |
| fr_subjonctif_present | 3 Subjonctif | WEAK-MODERATE — 13 subjunctive rows (mostly avoided rather than wrong; capture bias likely) | Keep small |
| fr_subjonctif_conjonctions | 3 Subjonctif | WEAK — barely attested | Keep small / lower |
| fr_pronoms_y_en (planned) | 4 Pronoms | STRONG — 27+ direct (là→y 22, missing en 11) + avoidance visible everywhere | PROMOTE to active — best-evidenced planned unit |

The shipped fr deck is inverted relative to this learner's actual
error mass: verb-tense units cover ~10% of his errors; prepositions +
gender/agreement + articles/quantities + word order = ~55% and have no
units. New units this data justifies (proposed clusters continue the
existing numbering):

| Proposed key | Cluster | Evidence | Content |
|---|---|---|---|
| fr_prep_lieux | 5 Prépositions | 56 rows, `en Berlin` 36× | à/en/au + city/country/region; dans/en/à static vs motion |
| fr_prep_verbes | 5 Prépositions | ~475-row bucket; chercher à, penser à/de, participer à, dépendre de… | verb+prep regime bank (mirror es_verb_prep; Lefff valency data already earmarked in strategy §5) |
| fr_prep_infinitif | 5 Prépositions | 77 rows | c'est difficile DE / commencer À / décider DE; à vs de after adj/noun |
| fr_genre_noyau | 6 Genre & accord | 297 rows; personal top-40 noun list extracted above | drill HIS wrong-gender nouns (période, fois, méthode, vie, moyen, processus, parti…) |
| fr_accord_pluriels | 6 Genre & accord | 49 + 50 rows | adjective agreement + -al→-aux |
| fr_quantites_de | 7 Articles & quantités | 161 rows; #1 single error | beaucoup/trop/assez de; pas de; d'autres; la plupart d'entre eux; articles with countries/languages |
| fr_ordre_mots | 8 Ordre des mots | ~130 rows | adverb placement; NUM+dernier order; superlative double article; adjective position (meilleur) |
| fr_negation | 8 Ordre des mots (or own) | 60 rows | obligatory pas; rien/personne/aucun replace pas; ne…que |
| fr_an_annee | 7 Articles & quantités | 102 rows | an/année, jour/journée, matin/matinée, soir/soirée |
| fr_relatives | 4 Pronoms | 55 rows + 18 Teachee teach-items | qui vs que; dont; lequel after prep |
| fr_verbes_pronominaux | 4 Pronoms | 15+ | se-dropping and spurious se |
| fr_calques (F3-heavy) | 9 Interférences | ~60 + 47 invented verbs | de manière+adj, un tel, rendre vs faire, c'est que, au bout de, la notre→notre; Romance verb inventions |

Format note: most of the above are closed-class or fixed-pattern
answers → Tier B blind-fill verification (already built, Wave 2), not
morphology tables. The F3 error-correction format (strategy §4,
"Later" wave item) is *directly* fed by §7 below — this learner's
`_errors`-deck instinct (strategy §2) plus 3,501 recorded real errors
make F3 the highest-leverage new format for French.

## 7. F3 seed list — 40 verbatim error pairs (machine-readable)

All `wrong` strings are the learner's actual recorded production;
recurring/structural errors preferred over one-off slips.

```json
[
  {"wrong": "J'apprends beaucoup des langues.", "right": "J'apprends beaucoup de langues.", "why": "quantity word + de invariable (beaucoup/trop/assez de)", "category": "quantifier_de"},
  {"wrong": "Il gagne beaucoup de l'argent.", "right": "Il gagne beaucoup d'argent.", "why": "beaucoup de + noun, no article", "category": "quantifier_de"},
  {"wrong": "La plupart d'eux sont d'accord.", "right": "La plupart d'entre eux sont d'accord.", "why": "quantifier + d'ENTRE + pronoun", "category": "quantifier_de"},
  {"wrong": "Il y a des autres choses.", "right": "Il y a d'autres choses.", "why": "des → d' before autres", "category": "quantifier_de"},
  {"wrong": "Je vais visiter Turquie.", "right": "Je vais visiter la Turquie.", "why": "country names take the definite article", "category": "article"},
  {"wrong": "J'habite en Berlin.", "right": "J'habite à Berlin.", "why": "à + city (en + fem. country)", "category": "prep_place"},
  {"wrong": "Il travaille en Chili.", "right": "Il travaille au Chili.", "why": "au + masculine country", "category": "prep_place"},
  {"wrong": "Je l'ai vu dans la télévision.", "right": "Je l'ai vu à la télévision.", "why": "à la télé/radio, sur internet", "category": "prep_place"},
  {"wrong": "Je pars pour 2, 3 jours.", "right": "Je pars pendant 2, 3 jours.", "why": "duration = pendant (pour only for intended future stay)", "category": "prep_selection"},
  {"wrong": "Quand je pense de ce mot...", "right": "Quand je pense à ce mot...", "why": "penser à qqch (penser de = opinion only)", "category": "verb_prep_regime"},
  {"wrong": "C'est très proche à la mer.", "right": "C'est très proche de la mer.", "why": "proche DE", "category": "verb_prep_regime"},
  {"wrong": "Je cherche de m'isoler.", "right": "Je cherche à m'isoler.", "why": "chercher À + infinitif", "category": "verb_prep_regime"},
  {"wrong": "On a commencé de parler.", "right": "On a commencé à parler.", "why": "commencer À + infinitif", "category": "verb_prep_regime"},
  {"wrong": "J'ai décidé à lire ce livre.", "right": "J'ai décidé de lire ce livre.", "why": "décider DE + infinitif", "category": "verb_prep_regime"},
  {"wrong": "C'est difficile à parler de ça.", "right": "C'est difficile de parler de ça.", "why": "impersonal c'est + adj + DE + inf", "category": "infinitive_prep"},
  {"wrong": "C'était impossible à imaginer que...", "right": "C'était impossible d'imaginer que...", "why": "c'est impossible DE + inf", "category": "infinitive_prep"},
  {"wrong": "C'est très difficile trouver un accord.", "right": "C'est très difficile de trouver un accord.", "why": "de is obligatory before the infinitive", "category": "infinitive_prep"},
  {"wrong": "avant de la pandémie", "right": "avant la pandémie", "why": "avant + noun directly (avant de only + infinitive)", "category": "prep_selection"},
  {"wrong": "Après 2 ans, j'ai changé de méthode.", "right": "Au bout de 2 ans, j'ai changé de méthode.", "why": "elapsed time = au bout de / X ans plus tard", "category": "calque"},
  {"wrong": "cet an", "right": "cette année", "why": "année for the span you're inside; an = counting unit", "category": "an_vs_annee"},
  {"wrong": "dans les ans 90", "right": "dans les années 90", "why": "decades = les années X0", "category": "an_vs_annee"},
  {"wrong": "les premières deux semaines", "right": "les deux premières semaines", "why": "numeral BEFORE premier/dernier/prochain", "category": "word_order"},
  {"wrong": "dans les derniers 10 ans", "right": "ces 10 dernières années", "why": "ces + NUM + dernières + années", "category": "word_order"},
  {"wrong": "Je déjà connais ce mot.", "right": "Je connais déjà ce mot.", "why": "adverb follows the finite verb", "category": "adverb_placement"},
  {"wrong": "Ce plan aussi a échoué.", "right": "Ce plan a aussi échoué.", "why": "aussi after the finite verb/auxiliary", "category": "adverb_placement"},
  {"wrong": "On ne jamais arrivera à ce point.", "right": "On n'arrivera jamais à ce point.", "why": "ne + verb + jamais", "category": "negation"},
  {"wrong": "Ce n'était très simple.", "right": "Ce n'était pas très simple.", "why": "pas is obligatory (unlike Italian non)", "category": "negation"},
  {"wrong": "Ça n'intéresse pas personne.", "right": "Ça n'intéresse personne.", "why": "personne/rien/aucun replace pas", "category": "negation"},
  {"wrong": "Il n'y a pas aucune discussion.", "right": "Il n'y a aucune discussion.", "why": "aucun replaces pas", "category": "negation"},
  {"wrong": "Quand je retournerai là...", "right": "Quand j'y retournerai...", "why": "y replaces à + place, before the verb", "category": "pronoun_y_en"},
  {"wrong": "Nous avons déjà discuté.", "right": "Nous en avons déjà discuté.", "why": "en replaces de + topic (discuter DE)", "category": "pronoun_y_en"},
  {"wrong": "des partis que critiquent le gouvernement", "right": "des partis qui critiquent le gouvernement", "why": "qui = subject relative (it. che covers both)", "category": "relative_qui_que"},
  {"wrong": "le magazine que suit ces sujets", "right": "le magazine qui suit ces sujets", "why": "qui = subject relative", "category": "relative_qui_que"},
  {"wrong": "Je suis réussi à venir.", "right": "J'ai réussi à venir.", "why": "réussir conjugates with avoir", "category": "aux_choice"},
  {"wrong": "Beaucoup de choses se sont changées.", "right": "Beaucoup de choses ont changé.", "why": "changer (intrans.) is not pronominal here", "category": "pronominal_verb"},
  {"wrong": "On peut engager dans un débat.", "right": "On peut s'engager dans un débat.", "why": "s'engager dans = pronominal", "category": "pronominal_verb"},
  {"wrong": "ce période", "right": "cette période", "why": "période is feminine (personal gender list)", "category": "gender"},
  {"wrong": "le première fois", "right": "la première fois", "why": "fois is feminine", "category": "gender"},
  {"wrong": "les ennemis principals", "right": "les ennemis principaux", "why": "-al → -aux in the plural", "category": "plural_aux"},
  {"wrong": "L'avantage est-ce que je ne perds aucune information.", "right": "L'avantage, c'est que je ne perds aucune information.", "why": "topic + c'est que (est-ce que = questions only)", "category": "calque"}
]
```

Runner-up seeds (also verbatim, for the second batch): `la chose plus
grave`→`la chose la plus grave`; `beaucoup plus pire`→`bien pire`;
`dans une façon compréhensive`→`de manière compréhensible`; `la notre
maison`→`notre maison`; `un scénario comme ça`→`un tel scénario`;
`faire le système plus démocratique`→`rendre…`; `la chute de la mur de
Berlin`→`du mur`; `insérir`→`insérer`; `ils comprend`→`ils
comprennent`; `je prendais`→`je prenais`.
