"""Pilot curriculum: Spanish, verb morphology core.

Topic design follows docs/GRAMMAR_STRATEGY.md §3-4: KOFI-style
one-form-per-card, frequency-first verb pools, tense signaled by an
in-language cue INSIDE the sentence (never "3rd person plural future"),
plus a small symbol on the card. Topics are deliberately mixed at
review time (single deck) — interleaving confusable tenses is the
point, not an accident.

The planner (P3) will eventually pick topics from telemetry; for the
pilot the batch is stratified across this list.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# High-frequency Spanish verbs present in the Jehle DB. Ordering roughly
# tracks corpus frequency; irregular-heavy on purpose — regulars transfer
# from patterns, irregulars must be drilled.
TOP_VERBS_ES = [
    "ser", "estar", "tener", "hacer", "poder", "decir", "ir", "ver", "dar",
    "saber", "querer", "llegar", "pasar", "deber", "poner", "parecer",
    "quedar", "creer", "hablar", "llevar", "dejar", "seguir", "encontrar",
    "llamar", "venir", "pensar", "salir", "volver", "tomar", "conocer",
    "vivir", "sentir", "mirar", "contar", "empezar", "esperar", "buscar",
    "entrar", "trabajar", "escribir", "perder", "producir", "pedir",
    "recibir", "recordar", "terminar", "permitir", "aparecer", "conseguir",
    "comenzar", "servir", "sacar", "necesitar", "mantener", "leer", "caer",
    "crear", "abrir", "oír", "morir", "traer",
    "construir", "jugar", "dormir", "elegir", "repetir", "traducir",
]
# NB: every verb here must exist in the Jehle DB — enforced by a test;
# 'cambiar'/'considerar' were dropped for that reason (not in Jehle).


@dataclass
class Topic:
    key: str                 # stable id, used in tags + telemetry
    lang: str
    label: str               # human label for dashboards
    mood: str                # morphology.py lookup key ("" for closed-class)
    tense: str
    symbol: str              # tiny on-card cue, KOFI-style
    # Anki subdeck this unit's cards live in: "Idiomatic Grammar {LANG}::
    # {cluster}". Numbered so Anki sorts them. Assigned via CLUSTER_BY_KEY
    # below (es/de) or units_fip.json (fr/it/pt); strings are FINAL per
    # docs/commissions/GRAMMAR_FRONTEND_COMMISSION.md — renaming one would
    # orphan the existing Anki subdeck and re-split the user's collection.
    cluster: str = ""
    verbs: list[str] = field(default_factory=lambda: TOP_VERBS_ES)
    # Free-text constraints handed to the generator prompt.
    guidance: str = ""
    # Verification mode (docs/GRAMMAR_STRATEGY.md §8):
    #   "morph" — Tier A: answer checked against the morphology table.
    #   "blind" — Tier B: K independent blind solvers must all reproduce
    #             the answer from the sentence alone (correctness AND
    #             uniqueness in one test). For closed-class topics.
    #   "bank_blind" — Tier A bank metadata/answer check, then Tier B.
    #   "fr_gender" / "pt_gender" / "it_noun" — deterministic facts
    #             from the named unit bank.
    verify: str = "morph"
    # For blind topics: the closed inventory the answer must come from
    # (None = no inventory check). Multi-word entries allowed ("se lo").
    answer_set: list[str] | None = None
    # Optional JSON bank in grammar/data/ whose entries seed the generator
    # prompt (e.g. verb+preposition regimes, codex-produced, human-reviewed).
    bank: str | None = None


PILOT_TOPICS_ES: list[Topic] = [
    Topic("es_pres_irreg", "es", "Presente (irregulares)", "indicativo", "presente", "⊙",
          verbs=["ser", "estar", "tener", "hacer", "poder", "decir", "ir", "ver",
                 "saber", "querer", "poner", "venir", "salir", "seguir", "oír",
                 "traer", "conocer", "dar", "caer", "construir"],
          guidance="Focus on the irregular cells (yo-go forms, stem changes, "
                   "ser/ir/estar). Cue words like 'ahora', 'normalmente', "
                   "'todos los días'."),
    Topic("es_preterito", "es", "Pretérito indefinido", "indicativo", "pretérito", "←",
          guidance="Completed past events. Strong preterites (tuvo, hizo, pudo, "
                   "dijo, vino, puso, supo) get priority. Cues: 'ayer', "
                   "'el año pasado', 'en 2008', 'de repente'."),
    Topic("es_imperfecto", "es", "Imperfecto", "indicativo", "imperfecto", "〜←",
          guidance="Habitual/background past. Cues: 'antes', 'de niño', "
                   "'mientras', 'todos los veranos', 'en aquella época'."),
    Topic("es_futuro", "es", "Futuro simple", "indicativo", "futuro", "→",
          guidance="Predictions and promises; include irregular stems (tendrá, "
                   "habrá, podrá, saldrá, dirá). Cues: 'mañana', 'el próximo "
                   "año', 'dentro de poco'."),
    Topic("es_condicional", "es", "Condicional", "indicativo", "condicional", "⇢?",
          guidance="Hypotheticals, polite requests, future-in-the-past. "
                   "Irregular stems again. Cues: 'si pudiera…', 'en tu lugar', "
                   "'dijo que…'."),
    Topic("es_subj_pres", "es", "Subjuntivo presente", "subjuntivo", "presente", "〰",
          guidance="Sentence MUST contain an unambiguous subjunctive trigger "
                   "(quiero que, es posible que, para que, ojalá, no creo que). "
                   "The trigger is the cue."),
    Topic("es_subj_imp", "es", "Subjuntivo imperfecto", "subjuntivo", "imperfecto", "〰←",
          guidance="Triggers in past tense or si-clauses (quería que, si "
                   "tuviera, como si). Use the -ra forms (Jehle's imperfecto "
                   "subjunctive rows are -ra)."),
    Topic("es_perfecto", "es", "Pretérito perfecto", "indicativo", "pretérito perfecto", "◄⊙",
          guidance="Present-relevant past. Cues: 'ya', 'todavía no', 'hoy', "
                   "'esta semana', 'alguna vez'."),
    # --- Wave 1 additions (2026-07-29): commands + past conditionals ------
    Topic("es_cmd_tu", "es", "Imperativo — tú", "imperativo afirmativo", "presente", "❗",
          verbs=["tener", "poner", "hacer", "decir", "salir", "venir", "ir",
                 "ser", "dar", "estar", "hablar", "mirar", "escribir", "leer",
                 "abrir", "seguir", "pedir", "contar", "volver", "empezar"],
          guidance="INFORMAL commands to tú ONLY (person=2s; never 1s, never "
                   "other persons). The sentence must make the informal "
                   "register obvious: talking to a friend, colleague, child "
                   "('Por favor, ___ (tener) paciencia con tu hermano'). "
                   "Prioritize the eight irregulars (ten, pon, haz, di, sal, "
                   "ven, ve, sé)."),
    Topic("es_cmd_usted", "es", "Imperativo — usted/ustedes", "imperativo afirmativo", "presente", "❗🎩",
          guidance="FORMAL commands: usted (person=3s) or ustedes (3p), plus "
                   "an occasional nosotros 'let's' (1p). Never 1s or 2s. "
                   "Context must signal formality: official, professional, "
                   "customer-facing ('Señor director, ___ (tener) en cuenta "
                   "nuestra propuesta')."),
    Topic("es_cmd_neg", "es", "Imperativo negativo", "imperativo negativo", "presente", "⛔",
          guidance="Negative commands, mixed registers: tú (2s), usted (3s), "
                   "ustedes (3p). Never 1s. The answer INCLUDES the 'no' "
                   "('no hables', 'no vaya'). Do NOT write a separate 'no' in "
                   "the sentence outside the blank — the blank carries it: "
                   "'Por favor, ___ (hablar) tan rápido.'"),
    Topic("es_cond_perf", "es", "Condicional perfecto", "indicativo", "condicional perfecto", "⇢?◄",
          guidance="Past hypotheticals — the would-have apodosis: 'Si hubiera "
                   "sabido la verdad, ___ (actuar) de otra manera.' The "
                   "si-clause (or an equivalent like 'en tu lugar', 'con más "
                   "tiempo') is the cue. Answer is the full compound form "
                   "('habría actuado')."),
    Topic("es_plusc_subj", "es", "Pluscuamperfecto de subjuntivo", "subjuntivo", "pluscuamperfecto", "〰◄",
          guidance="The si-clause (or 'ojalá', 'como si') of past "
                   "counterfactuals: 'Si ___ (saber) la verdad, habría "
                   "actuado de otra manera.' Use -ra forms ('hubiera "
                   "sabido'), full compound in the answer."),
    # --- Wave 2 additions (2026-07-29): closed-class, blind-verified ------
    Topic("es_clitics_dir", "es", "Clíticos — objeto directo", "", "", "🔗",
          verify="blind",
          answer_set=["lo", "la", "los", "las", "me", "te", "nos", "os"],
          guidance="Direct-object pronoun. The antecedent must appear "
                   "earlier in the sentence (or in a quoted question) with "
                   "unambiguous gender+number: '¿Has leído el informe? Sí, "
                   "___ terminé anoche.' Vary gender/number/person. The "
                   "blank contains ONLY the pronoun."),
    Topic("es_clitics_ind", "es", "Clíticos — objeto indirecto", "", "", "🔗➡",
          verify="blind",
          answer_set=["le", "les", "me", "te", "nos", "os"],
          guidance="Indirect-object pronoun, incl. the redundant clitic with "
                   "an explicit 'a X' phrase: '___ mandé el borrador a la "
                   "editora ayer.' → 'le'. Number of the a-phrase decides "
                   "le vs les. The blank contains ONLY the pronoun."),
    Topic("es_clitics_selo", "es", "Clíticos — combinaciones (se lo)", "", "", "🔗🔗",
          verify="blind",
          answer_set=["se lo", "se la", "se los", "se las", "me lo", "me la",
                      "me los", "me las", "te lo", "te la", "te los", "te las",
                      "nos lo", "nos la", "nos los", "nos las"],
          guidance="Double clitic cluster. Both objects must be recoverable "
                   "from the sentence: '¿Le entregaste las llaves al portero? "
                   "Sí, ___ di esta mañana.' → 'se las' (le+las → se las, "
                   "NEVER 'le las'). Direct-object gender/number must be "
                   "unambiguous from the antecedent."),
    Topic("es_verb_prep", "es", "Régimen preposicional", "", "", "🧲",
          verify="blind",
          answer_set=["a", "de", "en", "con", "por", "para", "contra"],
          bank="es_verb_prep.json",
          guidance="The blank is ONLY the preposition governed by the verb "
                   "(regime pairs are supplied below — use those verbs, one "
                   "per sentence, and that exact preposition sense). The "
                   "verb must sit right before or near the blank: 'El plan "
                   "consiste ___ reducir la deuda.' → 'en'."),
    Topic("es_por_para", "es", "Por vs para", "", "", "⚖",
          verify="blind",
          answer_set=["por", "para"],
          guidance="One blank where exactly one of por/para is correct and "
                   "the reason is a nameable rule (cause vs purpose, "
                   "duration/exchange/means vs destination/deadline/"
                   "recipient/opinion). Avoid contexts where both are "
                   "grammatical with different meanings — the sentence must "
                   "force one reading. State the rule in 'why'."),
    Topic("es_muy_mucho", "es", "Muy, mucho, tan y tanto", "", "", "∑",
          verify="blind",
          answer_set=["muy", "mucho", "mucha", "muchos", "muchas",
                      "mucho más", "tan", "tanto"],
          bank="es_muy_mucho.json",
          guidance="Use one banked contrast: muy before an adjective/adverb; "
                   "agreeing mucho before a noun; invariable mucho/tanto "
                   "after a verb; mucho más for a comparative; tan for "
                   "equal degree. In a 24-card batch target 8 muy, 8 agreeing "
                   "mucho forms, 4 mucho más, and 4 tan/tanto. Never accept "
                   "'muy más'."),
]


TOPICS_DE: list[Topic] = [
    # verify="de_art": deterministic — noun gender from the vendored table,
    # case from context/prep bank, article from the declension matrix.
    Topic("de_gender", "de", "Genus — der/die/das", "", "", "🚻",
          verify="de_art",
          guidance="The blank is the DEFINITE article of a singular noun in "
                   "the NOMINATIVE (the noun must be the subject, case=nom): "
                   "'___ Verhandlung dauerte drei Stunden.' Choose common "
                   "nouns whose gender is NOT guessable from the ending "
                   "(avoid -ung/-heit/-keit/-chen except occasionally)."),
    Topic("de_prep_fest", "de", "Feste Präpositionen + Kasus", "", "", "🧭",
          verify="de_art", bank="de_preps.json",
          guidance="The blank is the article (definite or indefinite) "
                   "directly after a FIXED-case preposition from the bank "
                   "below (never an/auf/in/über/unter/vor/hinter/neben/"
                   "zwischen): 'Er kam mit ___ Zug.' Genitive prepositions "
                   "ONLY with feminine nouns ('während ___ Woche'). State "
                   "prep, noun, case, definite in the JSON."),
    Topic("de_prep_wechsel", "de", "Wechselpräpositionen", "", "", "↔",
          verify="de_art_blind", bank="de_preps.json",
          guidance="The blank is the article after one of the nine two-way "
                   "prepositions (an, auf, hinter, in, neben, über, unter, "
                   "vor, zwischen). The verb must make motion (→akk) or "
                   "location (→dat) unambiguous: 'Er hängt das Bild an ___ "
                   "Wand.' vs 'Das Bild hängt an ___ Wand.' Mix both "
                   "readings ~50/50. State prep, noun, case, definite."),
    Topic("de_dativ_verben", "de", "Verben mit Dativobjekt", "", "", "➡",
          verify="bank_blind", bank="de_dativ_verben.json",
          guidance="Choose one banked verb and blank its complete dative "
                   "noun phrase. Give the nominative citation phrase in "
                   "parentheses, keep true dative objects distinct from "
                   "prepositional phrases, and state verb and case in the "
                   "JSON. Ditransitives must make the recipient explicit."),
]


# Topic-cluster map for the es/de units (fr/it/pt carry theirs in
# units_fip.json). One subdeck per cluster; every unit key MUST appear here
# (enforced by a test).
CLUSTER_BY_KEY: dict[str, str] = {
    "es_pres_irreg": "1 Tiempos", "es_preterito": "1 Tiempos",
    "es_imperfecto": "1 Tiempos", "es_futuro": "1 Tiempos",
    "es_condicional": "1 Tiempos", "es_perfecto": "1 Tiempos",
    "es_subj_pres": "2 Subjuntivo", "es_subj_imp": "2 Subjuntivo",
    "es_cond_perf": "3 Condicionales", "es_plusc_subj": "3 Condicionales",
    "es_cmd_tu": "4 Imperativo", "es_cmd_usted": "4 Imperativo",
    "es_cmd_neg": "4 Imperativo",
    "es_clitics_dir": "5 Pronombres", "es_clitics_ind": "5 Pronombres",
    "es_clitics_selo": "5 Pronombres",
    "es_por_para": "6 Preposiciones", "es_verb_prep": "6 Preposiciones",
    "es_muy_mucho": "9 Grado y cantidad",
    "de_gender": "1 Genus",
    "de_prep_fest": "2 Präpositionen", "de_prep_wechsel": "2 Präpositionen",
    "de_dativ_verben": "5 Kasus",
}

for _t in PILOT_TOPICS_ES + TOPICS_DE:
    _t.cluster = CLUSTER_BY_KEY[_t.key]


# Units that exist only as curriculum intent (grammar_units rows with
# status='planned', no Topic/generation yet) — the "what's NEXT per
# language" layer of the dashboard tree. Candidates from
# docs/GRAMMAR_STRATEGY.md §3. When one is implemented, move it into the
# real topic list (same key!) and delete it here; boot seeding then flips
# its DB row from planned to active.
PLANNED_UNITS: list[dict] = [
    {"key": "es_ser_estar", "lang": "es", "cluster": "7 Ser/Estar",
     "label": "Ser vs estar", "symbol": "⚖"},
    {"key": "de_adj_endings", "lang": "de", "cluster": "3 Adjektive",
     "label": "Adjektivendungen", "symbol": "🖌"},
    {"key": "de_verb_core", "lang": "de", "cluster": "4 Verben",
     "label": "Verbformen — Kern", "symbol": "⚙"},
    {"key": "fr_pronoms_y_en", "lang": "fr", "cluster": "4 Pronoms",
     "label": "Pronoms y / en", "symbol": "🔗"},
    {"key": "it_clitici_ci_ne", "lang": "it", "cluster": "4 Clitici",
     "label": "Clitici ci / ne", "symbol": "🔗"},
    {"key": "pt_clitic_placement", "lang": "pt", "cluster": "4 Clíticos",
     "label": "Colocação pronominal", "symbol": "🔗"},
]


def _load_fip_topics() -> dict[str, list[Topic]]:
    """fr/it/pt verb-core units from grammar/data/units_fip.json (specs
    drafted by codex, tense keys corrected to the verbecc tables; pt is
    BRAZILIAN Portuguese by user directive — você-based, tu/vós rejected
    in verify_item — see Wave 4 in docs/GRAMMAR_STRATEGY.md §8)."""
    import json
    from pathlib import Path
    raw = json.loads((Path(__file__).parent / "data" / "units_fip.json"
                      ).read_text(encoding="utf-8"))
    return {
        lang: [Topic(u["key"], lang, u["label"], u["mood"], u["tense"],
                     u["symbol"], cluster=u["cluster"], verbs=u["verbs"],
                     guidance=u["guidance"])
               for u in units]
        for lang, units in raw.items()
    }


_FIP_TOPICS = _load_fip_topics()


# Bank-backed lexical/agreement units. These append to the verb-core lists
# loaded above, preserving those units' existing sort order and stable keys.
_BANK_TOPICS: dict[str, list[Topic]] = {
    "fr": [
        Topic("fr_quantites_de", "fr", "Quantités — de / des", "", "", "∑",
              cluster="7 Articles & quantités", verify="blind",
              answer_set=[
                  "beaucoup de", "beaucoup d'", "trop de", "trop d'",
                  "assez de", "assez d'", "peu de", "peu d'", "plus de",
                  "plus d'", "moins de", "moins d'", "pas de", "pas d'",
                  "d'autres", "la plupart des", "la plupart d'entre eux",
                  "bien des", "de", "d'",
              ],
              bank="fr_quantites_de.json",
              guidance="Use one banked quantity construction and preserve "
                       "its reading: indefinite quantities and negated "
                       "objects take de/d'; d'autres marks additional "
                       "items; la plupart and bien des keep their banked "
                       "forms. Formal adjective+noun rows must retain an "
                       "explicit careful-written-language cue."),
        Topic("fr_prep_lieux", "fr", "Prépositions de lieu", "", "", "📍",
              cluster="5 Prépositions", verify="bank_blind",
              answer_set=["à", "en", "au", "aux", "dans le", "dans la",
                          "dans les", "dans l'"],
              bank="fr_prep_lieux.json",
              guidance="Choose one banked place and use its exact "
                       "preposition; never infer it from spelling. Put one "
                       "blank immediately before the place, keep movement "
                       "versus location neutral, draw at least half the "
                       "batch from high-priority cities/countries, and cap "
                       "regions/islands at one fifth."),
        Topic("fr_genre_noyau", "fr", "Genre — noms fréquents", "", "", "🚻",
              cluster="6 Genre & accord", verify="fr_gender",
              bank="fr_genre_noyau.json",
              guidance="Choose one banked noun in its stated sense and "
                       "blank only the controlled indefinite article un/une. "
                       "Return the exact noun in the JSON so its gender can "
                       "be checked deterministically. Pin mode as method, "
                       "livre as book, and politique as policy; interleave "
                       "the banked suffix-family contrasts only after the 19 "
                       "personal core nouns."),
        Topic("fr_an_annee", "fr", "An / année et durées", "", "", "📅",
              cluster="7 Articles & quantités", verify="blind",
              answer_set=["an", "An", "ans", "année", "années", "jour",
                          "jours", "journée", "matin", "matinée", "soir",
                          "soirée"],
              bank="fr_an_annee.json",
              guidance="Preserve one banked fixed expression or forced "
                       "construal: measurement versus experienced period, "
                       "calendar point versus full event/duration, or "
                       "time-of-day label versus elapsed block. Avoid free "
                       "contexts where both choices are defensible."),
    ],
    "it": [
        Topic("it_genere_plurali", "it", "Genere, articoli e plurali", "", "", "🚻↔",
              cluster="5 Genere e plurali", verify="it_noun",
              bank="it_genere_plurali.json",
              guidance="Choose one banked noun and test exactly one declared "
                       "target: singular article+noun, plural article+noun, "
                       "or plural alone. Include the citation noun outside "
                       "the blank so metadata stays checkable. Mix il/i, "
                       "lo/gli, both l' patterns, "
                       "and la/le before interleaving regular, invariant, and "
                       "irregular plurals. Preserve the banked sense for "
                       "gender-changing body and collective forms."),
        Topic("it_reggenze_verbali", "it", "Reggenze verbali", "", "", "🧲",
              cluster="6 Reggenze", verify="bank_blind",
              answer_set=["a", "come", "con", "da", "di", "in", "per", "su"],
              bank="it_reggenze_verbali.json",
              guidance="Choose one exact banked verb sense and blank only "
                       "its preposition. Preserve other argument markers, "
                       "and add enough lexical context to disambiguate verbs "
                       "with more than one regime, especially pensare and "
                       "credere. Initial batches must include cercare di, "
                       "permettere a qualcuno di, partecipare a, and "
                       "guadagnare come."),
    ],
    "pt": [
        Topic("pt_gender_core", "pt", "Gênero, artigos e concordância", "", "", "🚻",
              cluster="5 Gênero & Artigos", verify="pt_gender",
              bank="pt_gender_core.json",
              guidance="Use Brazilian Portuguese. For noun rows, blank a "
                       "controlled definite or indefinite article and return "
                       "the exact noun key. For numeral, agreement, and "
                       "contraction frames, use the canonical bank example "
                       "with its full answer blanked. Prioritize -ma/-agem "
                       "traps, core "
                       "news nouns, dois/duas, agreeing hundreds, and "
                       "article contractions."),
        Topic("pt_regencia_verbal", "pt", "Regência verbal", "", "", "🧲",
              cluster="6 Regência", verify="bank_blind",
              answer_set=["Ø", "a", "ao", "com", "de", "em", "na", "no",
                          "para", "por", "que", "às"],
              bank="pt_regencia_verbal.json",
              guidance="Use careful professional Brazilian Portuguese and "
                       "one exact banked sense. Blank only the regime marker; "
                       "the literal answer Ø means no preposition. Keep full "
                       "banked contractions as answers and preserve country "
                       "articles where required. Initial batches must include "
                       "tentar Ø, conseguir Ø, decidir Ø, and ir Ø before "
                       "broader expansion."),
    ],
}


def topics_for(lang: str) -> list[Topic]:
    if lang == "es":
        return PILOT_TOPICS_ES
    if lang == "de":
        return TOPICS_DE
    return _FIP_TOPICS.get(lang, []) + _BANK_TOPICS.get(lang, [])


GRAMMAR_LANGS = ["es", "de", "fr", "it", "pt"]


def unit_seed_rows() -> list[dict]:
    """Rows for db.seed_grammar_units — every implemented Topic (active)
    plus PLANNED_UNITS (planned, sorted after the real ones)."""
    rows = []
    for lang in GRAMMAR_LANGS:
        for i, t in enumerate(topics_for(lang)):
            rows.append({"key": t.key, "lang": lang, "cluster": t.cluster,
                         "label": t.label, "symbol": t.symbol,
                         "status": "active", "sort_order": i})
    for i, u in enumerate(PLANNED_UNITS):
        rows.append({**u, "status": "planned", "sort_order": 1000 + i})
    return rows


def topic_by_key(key: str) -> Topic | None:
    all_topics = PILOT_TOPICS_ES + TOPICS_DE
    for ts in _FIP_TOPICS.values():
        all_topics = all_topics + ts
    for ts in _BANK_TOPICS.values():
        all_topics = all_topics + ts
    for t in all_topics:
        if t.key == key:
            return t
    return None
