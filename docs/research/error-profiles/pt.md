# Learner Error Profile — Portuguese (pt)

> Mined 2026-07-31 from 5+ years of teacher-marked lesson notes for the
> repo owner. Target variety: **Brazilian Portuguese** (user directive).
> Learner studies es/fr/it/pt simultaneously → Romance interference is a
> first-class category, and the data confirms it is THE dominant one.
> Sources analyzed with scripts (counts are machine-derived, not
> hand-tallied); scratch scripts in the session scratchpad `errmine/`.

## 1. Data inventory

| Source | Rows | Era | Notes |
|---|---|---|---|
| `xlsx_pt.jsonl` | 4,521 | 2019-01 → 2022 | 2019: 1,577 · 2020: 1,345 · 2021: 1,074 · 2022: 525 |
| `teachee_pt.jsonl` | 1,400 | 2023-03 → 2024-12 | 43 lesson decks; 363 notes have an EN prompt field, 1,037 are PT-only |

xlsx flags: `vocab` 1,540 · `use` 1,091 · `pron` 1,078 · no flag 818
(flag combos are negligible: vocab+pron 4, use+pron 2).

Explicit `error` field non-null: **1,098 rows** (2019: 410, 2020: 452,
2021: 220, 2022: 16). This is the gold data for the taxonomy below.

Quality caveats:
- The `use` flag was effectively **2019-only** (1,080 of 1,091 uses).
  From 2020 on the teacher kept recording errors but under `vocab`/
  `pron`/no-flag rows — so the taxonomy is built on all 1,098
  error-bearing rows, not on the `use` flag.
- Dates come in two formats (`YYYY-MM-DD` and `DD/MM/YYYY`); naive
  4-char year slicing miscounts — normalize before grouping.
- For error-less rows the corrected element is usually marked in
  (parentheses); informative for what was taught, but the learner's
  actual utterance is unrecoverable.
- Teachee has **no IPA in practice** (13 false positives = slashes in
  "ruim/mau" style variants) and no explicit wrong-forms; its value is
  as a 2023-24 *remediation signal* — which old weaknesses the teacher
  was still packaging as flashcards years later (§3, §6).
- **Variety mixing: none found.** No EP markers anywhere (no
  tu-conjugation, "estar a + inf", telemóvel/autocarro/comboio/ecrã).
  Corrections consistently point BR: `aceder → acessar`, `aplicação →
  aplicativo`, `planear → planejar`, `em França → na França` (EP says
  "em França" — a BR-speaking teacher corrected it), `agenda → pauta`,
  `chamada → fazer uma ligação`. EP-looking learner forms (aceder,
  planear) are best read as Spanish interference, not EP exposure.

## 2. Grammar error taxonomy (n = 1,098 error rows)

Machine-categorized (regex rules + hand-map for stragglers; first-match
wins; 12 rows left genuinely "other").

| # | Category | n | % | Years seen |
|---|---|---|---|---|
| 1 | Romance interference — lexical/morph transfer (es, some it) | 588 | 53.6% | 2019-2022, all |
| 2 | Gender: articles/determiners incl. no/na contractions, dois/duas, uns/umas | 193 | 17.6% | all 4 years |
| 3 | English code-switch (vocab gap, said the EN word) | 53 | 4.8% | 2019-2021 |
| 4 | Semantic pairs / false friends (fato-feito, pedir-perguntar…) | 33 | 3.0% | 2019-2021 |
| 5 | Preposition & contraction selection (em+country, por/para, neste) | 32 | 2.9% | 2019-2022 |
| 6 | Verb+prep regime calques (tentar DE, conseguir A, vou A + inf) | 30 | 2.7% | 2019-2022 |
| 7 | Person confusion 1sg↔3sg in pretérito perfeito | 29 | 2.6% | 2019-2021 |
| 8 | ser/estar/ficar selection | 24 | 2.2% | all 4 years |
| 9 | PT-internal verb morphology botches (produzou, liu, compreu) | 19 | 1.7% | 2019-2021 |
| 10 | Clitics: enclisis to infinitive, comigo/conosco, possessive order | 18 | 1.6% | 2019-2021 |
| 11 | Numerals (dos→dois, quatros, cinco centos→quinhentos, media→meia) | 16 | 1.5% | all 4 years |
| 12 | Orthography/nasal minimal pairs mas/mais, sim/sem | 10 | 0.9% | 2019-2021 |
| 13 | Subjunctive selection (future subj. after quando/se; espero que) | 9 | 0.8% | 2020-2021 |
| 14 | Adjective/participle agreement (viagens permitidAs, sistema consideradO) | 9 | 0.8% | 2020 |
| 15 | Comparatives (mais grande→maior, tão→tanto, do que) | 8 | 0.7% | 2019-2021 |
| 16 | Possessives (mi→meu, minhas→meus) | 7 | 0.6% | 2019-2021 |
| 17 | Imperfect formation/selection (-avo/-ava, moria→morava) | 4 | 0.4% | 2019 |
| 18 | Noun plural morphology (volos→voos, canales→canais) | 4 | 0.4% | 2019 |
| 19 | Other | 12 | 1.1% | — |

### Examples per top category (verbatim: learner → teacher)

**1. Romance interference** (top recurring error lemmas with counts:
ningun ×7, contento ×7, perdo ×7, estudiar ×6, intento ×6, aceder ×6,
tarea ×6, datos ×5, errores ×5, retraso ×5, todavia ×5, prefirem ×5,
quere ×4, ponemos ×4, presentar-family ×15+):
- `todavia` → **ainda** não decidi  (es *todavía*)
- `perdo` → eu não **perco**  (unraised stem, es *pierdo*-shaped regularization)
- `contento` → estou **contente**  (es/it *contento*)
- `intento` → eu **tento**  (es *intento*)
- `prefirem` → eles **preferem**  (es *prefieren*)
- `racontar` → tenho que **contar**  (it *raccontare*)
- `mentre` → **enquanto**  (it *mentre*)
- `hay` → **tem** / não tem nada  (es *hay*)

**2. Gender.** Recurring nouns: programa ×11, idioma(s) ×9, tema(s) ×7,
mensagem ×5, viagem ×5, sistema ×3, problema ×6, site ×8, ordem ×2,
equipe ×2, lei ×3, voz ×2, cartões ×3; dois/duas ×9, uns/umas ×4:
- `uma` → **um** problema · `uma` → **um** programa · `as` → **os** idiomas
- `um` → **uma** mensagem · `este` → **esta** viagem
- `o lei / um novo lei` → **a** lei / **uma nova** lei
- `duas` → **dois** meses · `dois` → **duas** telas · `umas` → **uns** dias
- `na` → **no** site · `o meu` → **a minha** voz
- Greek -ma masculines + -agem feminines + ordem/lei/voz/equipe are the
  fossil core; still being re-taught in Teachee 2023-24 (duas/dois ×13,
  uns ×5 remediation notes).

**5. Preposition & contraction:**
- `em França` / `en francia` → **na** França · `em` → **na** Suíça · `em` → **no** Brasil
- `por` → trabalhava **para** prefeita · `para dois` → **por** duas razões · `para` → 3 aulas **por** semana
- `no este` → **neste** (×4) · `na uma` → **numa**
- `em` → viajar **de** carro / **de** trem · `a le` → **às** 5
- `no` → **ao** mesmo tempo (×4)

**6. Verb+prep regime (es/it calques):**
- `Eu vou a passar` → Eu **vou passar**  ("sem a" is the teacher's
  recurring margin note, ×5 — es *voy a + inf* calque)
- `tentei de` → **tentei** instalar · `tentam de formar` → **tentam formar** (tentar+de ×9 — it *tentare di*)
- `consigue a` → **consegue** procurar · `consegui a` → **consegui** convencer (conseguir+a ×5)
- `decidi de` → **decidi** mandar · `tem ser` → tem **que** ser
- `fazer um erro` → eu **erro** quando / **cometer** um erro

**7. Person confusion, pretérito perfeito (1sg↔3sg):**
- `fiz` → ele **fez** (×4) · `tive` → ela **teve** / `teve` → eu **tive**
- `escrevi` → ele **escreveu** · `criou` → eu **criei** · `começou` → eu **comecei**
- `aprendi` → você **aprendeu** · `entendeu` → eu **entendi** · `diz` → eu **disse** (×4)
- Plus -ir 1pl vowel: `desenvolvimos` → **desenvolvemos** (×3), `recibimos` → **recebemos**

**8. ser/estar/ficar:**
- `é` → não **está** pronto (×3) · `são` → livros que **estão** disponíveis (×4)
- `eu fui ocupado` → eu **estava** ocupado · `sou` → **estou** sempre ocupado
- `foram` → eles **ficaram** muito contentes · `foi` → ela **ficou** satisfeita
- `ser` → **estar** na moda · `ser` → vai **estar / ficar** pronto
- `é` → Zoom **foi** criado pelas pessoas (passive: ser+PP in pretérito)

**10. Clitics:**
- `procuraros` → **procurá-los** (×2) · `colocaros` → **colocá-los** (×2) · `usaros/combinaros/integraros/organizaros` → -á-los/-á-las
- `fazero` → **fazê-lo** · `terlo` → é melhor **tê-lo**
- `com nós` → **conosco** (×3) · `com eu` → trabalham **comigo**
- `o marido seu` → **o seu marido**

**13. Subjunctive selection (indicative/periphrastic future used instead):**
- `vou voltar` → **quando eu voltar**, eu vou ajustar os cartões
- `vou ter` → **quando eu tiver** mais tempo, vou testar · `ter` → quando **tiver** o manuscrito
- `se eu vou viajar` → **se eu viajar** · `ser` → quando a pandemia **for** controlada
- `vou voltar` → espero que **volte** · `são` → é possível que **seja**

## 3. Recurring structural patterns (fossilization candidates)

Ranked by (frequency × persistence across eras × still-remediated in
Teachee 2023-24). These are the highest-value drill targets:

1. **-ma nouns treated feminine** (problema, programa, sistema, tema,
   idioma) — every year 2019-2022. ~30 tokens.
2. **-agem/-em nouns treated masculine** (mensagem ×5, viagem ×5, ordem,
   origens) — plus lei, voz, equipe, fonte the other way.
3. **dois/duas + uns/umas gender-marked numerals flattened** — 13 xlsx
   errors + 13 Teachee re-teach notes in 2023-24. Textbook fossil.
4. **Periphrastic future in quando/se clauses instead of future
   subjunctive** — 7 errors 2020-21, 8 Teachee remediation notes
   2023-24 ("quando chegar", "se não fizer isso", "se eles conseguirem").
5. **`tentar de` + inf** (it. tentare di) — ×9 across 2019-2022.
6. **`conseguir a` + inf** (it. riuscire a) — ×5.
7. **`ir a` + inf** for future ("vou a passar") — ×5 ("sem a").
8. **1sg↔3sg swap in irregular pretérito** (fiz/fez, tive/teve,
   escrevi/escreveu, disse) — 29 tokens, 2019-2021.
9. **ser→estar with ready/available/busy/satisfied** (pronto,
   disponível, ocupado, satisfeito, terminado) — 24 tokens, all years;
   "estou contente" still on Teachee cards ×5 in 2023-24.
10. **`contento`** specifically — ×7, the single most persistent word.
11. **`perdo` → perco** (+ perço) — ×8; c/ç stem alternation of perder.
12. **Enclisis to infinitive misformed** (`procuraros` → procurá-los
    pattern) — ×10; Teachee still teaching -á-lo forms ×6 in 2023-24.
13. **`com nós`/`com eu` → conosco/comigo** — ×4 + Teachee ×3.
14. **em + country without article** (em França, em Suíça, em Brasil) —
    ×6; opposite direction never occurs.
15. **por/para swap both directions** — ×6.
16. **`todavia` = still** (es todavía; in pt it means "however") — ×5.
17. **`fato` said as `feito`** — ×4 in 2021 alone; Teachee re-teaches
    "aceitar o fato".
18. **mais/mas and sim/sem nasal minimal pairs** — ×10 (flagged both as
    use and pron; a pron-grammar hybrid).
19. **mais grande / mais pequena → maior/menor** — ×5.
20. **`presentar` family without a-** (presentar, presentação,
    presento…) — ×15; apresentar is the single most re-corrected verb
    stem.
21. **Spanish plural/lexical numbers** (dos, diez, cinco centos →
    quinhentos, cem e oito → cento e oito, media → meia) — ×16.
22. **pedir vs perguntar; levar vs trazer; saber vs conhecer** — ×5
    combined, classic Romance-learner semantic splits.
23. **1pl -ir verbs conjugated with -imos in present/perfect confusion**
    (desenvolvimos→desenvolvemos, recibimos→recebemos) — ×4.
24. **Imperfect formed with -o** (pensavo, estavo, moria — it. -avo) —
    ×4, 2019 only (self-resolved; low priority).

## 4. Vocabulary profile

What the teacher kept having to supply (1,540 xlsx vocab rows + ~1,000
Teachee vocab notes):

- **Domains** (keyword-bucket shares, both sources rank identically):
  1. tech/software/AI (programa, aplicativo, planilha, teclado, digitar,
     baixar, servidor, atalho, reconhecimento de voz, comandos) — the
     learner's daily work domain; Teachee 2023-24 adds a heavy
     **podcast/audio-production** cluster (episódio, efeitos sonoros,
     regravar, produtor, maratonar).
  2. publishing/academia (ensaio, manuscrito, editor, revisão, resenha,
     prazo, rascunho, palestra, citação).
  3. politics/media/news (imprensa, pauta, sindicatos, sanções, elites).
  4. travel/logistics (voo, visto, passaporte, feriado vs férias).
  5. Almost **no** household/daily-life vocab — lessons are
     professional-register conversation.
- **Register**: formal-intellectual discourse; connectives and hedges
  repeatedly taught (na verdade, pelo menos, mais pra frente, até agora,
  evidentemente, ou seja).
- **Word class pattern**: teacher packages nouns **with the article**
  ("a ordem", "o costume", "as sugestões") — implicit gender remediation
  running through the vocab channel too.
- **English code-switch rows (53)** are concentrated in tech/product
  talk: request, field, score, sort, track, target, deadline→prazo,
  background, warehouse — i.e., L1-domain leakage, not general poverty.

## 5. Pronunciation profile

1,078 pron-flagged rows; only 27 carry an explicit wrong form (the rest
mark words drilled in repetition). Orthographic-environment proxy counts
over the flagged items:

| Feature (proxy) | n | Sample items |
|---|---|---|
| ti/di/te/de environments (BR affrication [tʃi]/[dʒi]) | 153 | tarde, decidiu, apostila, frequentemente |
| Accented / stress-critical words | 152 | cérebro, útil, índice, razoáveis, mandá-lo |
| Final nasal -am/-em (diphthongized [ɐ̃w̃]/[ẽj̃]) | 84 | conseguiram, fizeram, viagem, seguem |
| Palatal fricatives x/ch/j/ge | 64 | xis, viajar, tecnologia, jornalistas |
| -ão/-ões/-ães nasals | 55 | cidadãos, funções, apresentações |
| ç words | 50 | especialização, começaram |
| rr [h] | 31 | ocorrer, carreira, guerra, concorrência |
| nh [ɲ] | 30 | conhecimento, vizinho, resenhas |
| word-initial r [h] | 24 | razoáveis, reiniciar, recursos |
| lh [ʎ] | 19 | trabalho, escolher, milhares |

Explicit pron substitutions recorded: `sim` for **sem** ×5 and `mas`
for **mais** ×3 (nasal /ẽ/-/ĩ/ and /aj/-/a/ contrasts — the only
minimal-pair confusions documented), `despois`→depois, `dizir`→dizer,
`leer`→ler (hiato collapse), plus es/it-shaped stress (`utile`→útil,
`obligatorio`→obrigatório). Takeaway: the pron problem is largely the
same interference problem (saying the es/it cognate), plus two real
phonemic contrasts (sem/sim, final nasal diphthongs) worth targeted
minimal-pair audio.

## 6. Curriculum mapping

Existing pt units (units_fip.json, all cluster "1 Tempos"/"2 Condicional"/
"3 Subjuntivo"; 82 cards live) + planned:

| Unit | Evidence from this profile | n mapped | Action |
|---|---|---|---|
| pt_presente_irregulares | perdo/perço→perco ×8, quere→quer ×4, ponemos→pomos ×4, eu faz→faço, trazo→trago, dizo→digo, possem→podem | ~20 | **Keep/raise slightly**; bias generation toward perder, querer, pôr, fazer, trazer, dizer, poder, preferir, conseguir eu/ele cells |
| pt_preterito_perfeito | person confusion ×29 + morphology botches (produzou→produziu, liu→leu, compreu→comprou, prepari, comeci, escuti, insistei→insisti) ×15 | **~44 — largest verb-form signal** | **Raise target_size**; weight eu-vs-ele contrast pairs of fazer/ter/escrever/dizer/começar/estar; add -ir 1pl (desenvolvemos) |
| pt_preterito_imperfeito | formation ×4 (2019 only, it-shaped -avo), selection era/estava overlaps ser/estar | ~8 | **Keep small**; the pt perfeito/imperfeito *selection* contrast (F2) is worth 1-2 cards but forms are learned |
| pt_futuro_simples | tendre→terei ×1 | 1 | **Lower** — learner correctly defaults to periphrastic future; synthetic future is not his error mode |
| pt_condicional_presente | podria→poderia ×1 | 1 | **Lower** |
| pt_subjuntivo_presente | espero que volte, é possível que seja | 2 | **Keep** (production avoidance likely under-represents it — errors show he substitutes indicative when forced) |
| pt_futuro_subjuntivo | quando/se + indicative-or-vou errors ×7; Teachee remediation ×8 in 2023-24 | **15 — strongest selection signal** | **Raise**; generate SELECTION items (quando/se triggers with periphrastic-future distractor), not just forms |
| pt_clitic_placement (PLANNED) | enclisis misformation ×10, conosco/comigo ×4, possessive order ×1; Teachee -á-lo notes ×6 | **~21** | **Activate now**; anchor on infinitive+o/a → -á-lo/-ê-lo/-i-lo, comigo/conosco, BR proclisis defaults |

### New units the data justifies

Proposed clusters continue the existing numbering (es already uses
"7 Ser/Estar" for the analogous planned unit):

| Proposed key | Cluster | Evidence | Content |
|---|---|---|---|
| `pt_gender_core` | **5 Gênero & Artigos** (new) | 193 gender + 9 agreement + 7 possessive + 16 numeral = **225 rows, every year, still remediated 2023-24** — the single biggest addressable category | -ma masculines (problema/programa/sistema/tema/idioma/clima), -agem feminines (viagem/mensagem), a ordem/lei/voz/equipe/fonte, o site/email/link; dois/duas, uns/umas, oitocentas; article+contraction agreement (no site, na ordem). F1 cloze + F3 |
| `pt_regencia_verbal` | **6 Regência** (new) | 30 verb-prep-regime + 32 preposition rows | tentar Ø, conseguir Ø, decidir Ø, ir Ø + inf; dedicar-se a, pertencer a; em+country with article (na França, no Brasil); por/para; de carro/de trem; ao mesmo tempo, de manhã, às 5 |
| `pt_ser_estar_ficar` | **7 Ser/Estar** (mirrors es_ser_estar) | 24 rows all years + Teachee "estou contente"/"ficou evidente"/"vai ficar pronto" | estar+pronto/disponível/ocupado/satisfeito/online; ficar for change-of-state & "vai ficar pronto"; ser for passive voice (foi criado) |
| `pt_es_contrastes` | **8 Interferência** (new) | 588 interference rows — but most are pure vocab; the drillable subset is the ~60 recurring lemmas | F4 cross-language contrast + F3 correction: todavia≠todavía, contento→contente, tarea→tarefa, aceder→acessar, retraso→atraso, prensa→imprensa, presentar→apresentar, olvidar→esquecer, lograr→conseguir, fato≠feito, mas≠mais, sim≠sem. Pan 2025 Exp. 4 supports deliberate es/pt mixing |

Not worth units: comparatives (8 rows — fold 2-3 F3 cards into
pt_gender_core or interference), imperfect formation (extinct after
2019), noun plurals (4 rows, extinct).

Format note: the two strongest signals (gender, interference) are NOT
verb-table units — they need the Tier B blind-fill verifier (Wave 2
mechanism) or closed answer banks, same as es_por_para/de_gender. A
gender answer bank is trivial (o/a/um/uma/dois/duas + noun list from
this profile); that makes `pt_gender_core` Tier A-verifiable and cheap
to ship first.

## 7. F3 seed list (40 best real error pairs, machine-readable)

Verbatim learner errors (wrong side = what he actually said, minimally
embedded in the attested context). Selected for recurrence/structure
over one-off slips.

```json
[
 {"wrong": "os programas... uma programa nova", "right": "os programas... um programa novo", "why": "-ma nouns (Greek origin) are masculine", "category": "gender"},
 {"wrong": "as idiomas", "right": "os idiomas", "why": "idioma is masculine despite -a", "category": "gender"},
 {"wrong": "um mensagem", "right": "uma mensagem", "why": "-agem nouns are feminine", "category": "gender"},
 {"wrong": "este viagem", "right": "esta viagem", "why": "viagem is feminine (-agem)", "category": "gender"},
 {"wrong": "um novo lei", "right": "uma nova lei", "why": "lei is feminine; adjective agrees", "category": "gender"},
 {"wrong": "o ideia", "right": "a ideia", "why": "ideia is feminine", "category": "gender"},
 {"wrong": "duas meses", "right": "dois meses", "why": "numerals 1-2 agree in gender: dois meses / duas semanas", "category": "gender"},
 {"wrong": "dois telas", "right": "duas telas", "why": "tela is feminine → duas", "category": "gender"},
 {"wrong": "umas dias", "right": "uns dias", "why": "dia is masculine → uns", "category": "gender"},
 {"wrong": "oitocentos pessoas", "right": "oitocentas pessoas", "why": "hundreds agree in gender", "category": "gender"},
 {"wrong": "na site", "right": "no site", "why": "site is masculine → no (em+o)", "category": "gender"},
 {"wrong": "o meu voz", "right": "a minha voz", "why": "voz is feminine; article+possessive agree", "category": "gender"},
 {"wrong": "eu vou a passar quatro dias lá", "right": "eu vou passar quatro dias lá", "why": "ir + infinitive takes NO preposition (unlike Spanish ir a)", "category": "verb_prep_regime"},
 {"wrong": "tentei de instalar", "right": "tentei instalar", "why": "tentar + infinitive, no 'de' (unlike Italian tentare di)", "category": "verb_prep_regime"},
 {"wrong": "tentam de formar", "right": "tentam formar", "why": "tentar + bare infinitive", "category": "verb_prep_regime"},
 {"wrong": "consegue a procurar", "right": "consegue procurar", "why": "conseguir + bare infinitive (unlike Italian riuscire a)", "category": "verb_prep_regime"},
 {"wrong": "consegui a convencer", "right": "consegui convencer", "why": "conseguir + bare infinitive", "category": "verb_prep_regime"},
 {"wrong": "decidi de mandar", "right": "decidi mandar", "why": "decidir + bare infinitive", "category": "verb_prep_regime"},
 {"wrong": "tem ser", "right": "tem que ser", "why": "obligation: ter QUE + infinitive", "category": "verb_prep_regime"},
 {"wrong": "fazer um erro", "right": "cometer um erro", "why": "collocation: cometer um erro (or the verb errar)", "category": "verb_prep_regime"},
 {"wrong": "eu fiz... não, ele fiz", "right": "ele fez", "why": "pretérito irregular: eu fiz / ele fez", "category": "person_confusion"},
 {"wrong": "ela tive covid", "right": "ela teve covid", "why": "eu tive / ele-ela teve", "category": "person_confusion"},
 {"wrong": "ele escrevi um livro", "right": "ele escreveu um livro", "why": "eu escrevi / ele escreveu", "category": "person_confusion"},
 {"wrong": "eu criou o sistema", "right": "eu criei o sistema", "why": "eu criei / ele criou", "category": "person_confusion"},
 {"wrong": "eu começou ontem", "right": "eu comecei ontem", "why": "eu comecei / ele começou", "category": "person_confusion"},
 {"wrong": "um jornalista me diz isso ontem", "right": "um jornalista me disse isso ontem", "why": "pretérito of dizer: disse (not present diz)", "category": "person_confusion"},
 {"wrong": "nós desenvolvimos o projeto no ano passado", "right": "nós desenvolvemos o projeto", "why": "-er verbs: -emos in 1pl (desenvolvemos); -imos is for -ir verbs", "category": "verb_morphology"},
 {"wrong": "não é pronto", "right": "não está pronto", "why": "temporary state/result → estar", "category": "ser_estar_ficar"},
 {"wrong": "livros que são disponíveis", "right": "livros que estão disponíveis", "why": "availability is a state → estar", "category": "ser_estar_ficar"},
 {"wrong": "eu fui ocupado a semana toda", "right": "eu estava ocupado a semana toda", "why": "ongoing past state → estar (imperfeito)", "category": "ser_estar_ficar"},
 {"wrong": "eles foram muito contentes com o resultado", "right": "eles ficaram muito contentes com o resultado", "why": "change of state → ficar", "category": "ser_estar_ficar"},
 {"wrong": "quando vai ser pronto?", "right": "quando vai ficar pronto?", "why": "becoming ready → ficar pronto", "category": "ser_estar_ficar"},
 {"wrong": "quando eu vou voltar, eu vou ajustar os cartões", "right": "quando eu voltar, eu vou ajustar os cartões", "why": "quando + future reference → futuro do subjuntivo", "category": "fut_subjunctive"},
 {"wrong": "quando eu vou ter mais tempo, vou testar", "right": "quando eu tiver mais tempo, vou testar", "why": "quando-clause about the future → tiver", "category": "fut_subjunctive"},
 {"wrong": "se eu vou viajar em janeiro...", "right": "se eu viajar em janeiro...", "why": "open future condition: se + futuro do subjuntivo", "category": "fut_subjunctive"},
 {"wrong": "quando a pandemia vai ser controlada", "right": "quando a pandemia for controlada", "why": "quando + future → for (ser, fut. subj.)", "category": "fut_subjunctive"},
 {"wrong": "posso procuraros depois", "right": "posso procurá-los depois", "why": "clitic after infinitive: drop -r, add -lo/-la/-los/-las (procurá-los)", "category": "clitic"},
 {"wrong": "é melhor terlo", "right": "é melhor tê-lo", "why": "ter + o → tê-lo (circumflex, hyphen)", "category": "clitic"},
 {"wrong": "eles querem trabalhar com nós", "right": "eles querem trabalhar conosco", "why": "com + nós → conosco (com + eu → comigo)", "category": "clitic"},
 {"wrong": "ainda estou contento com o plano", "right": "ainda estou contente com o plano", "why": "contente is invariable in -e (es/it contento is the calque)", "category": "interference"}
]
```

Remaining top-interference F3/F4 candidates for `pt_es_contrastes`
generation (wrong→right, no sentence needed): todavia→ainda,
tarea→tarefa, aceder→acessar, retraso→atraso, prensa→imprensa,
presentar→apresentar, olvidar→esquecer, lograr→conseguir, datos→dados,
errores→erros, cerrar→fechar, descargar→baixar, crear→criar,
mantener→manter, perguntar(ask for)→pedir, trago(take)→levo,
feito(fact)→fato, mas(more)→mais, sim(without)→sem, média(media)→mídia,
mais grande→maior, tão tempo→tanto tempo, em França→na França.
