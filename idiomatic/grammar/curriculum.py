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
    #   "attested" — teacher-attested personal-error pair; never generated
    #                 or sent through an LLM verifier.
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
    "es_mis_errores": "9 Mis errores",
    "de_gender": "1 Genus",
    "de_prep_fest": "2 Präpositionen", "de_prep_wechsel": "2 Präpositionen",
    "de_meine_fehler": "9 Meine Fehler",
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


F3_TOPICS: dict[str, Topic] = {
    "fr": Topic(
        "fr_mes_erreurs", "fr", "Corrige : ce que j'ai dit", "", "", "⚠",
        cluster="9 Mes erreurs", verbs=[], verify="attested",
    ),
    "pt": Topic(
        "pt_meus_erros", "pt", "Corrija: o que eu disse", "", "", "⚠",
        cluster="9 Meus erros", verbs=[], verify="attested",
    ),
    "es": Topic(
        "es_mis_errores", "es", "Corrige: lo que dije", "", "", "⚠",
        cluster=CLUSTER_BY_KEY["es_mis_errores"], verbs=[], verify="attested",
    ),
    "it": Topic(
        "it_miei_errori", "it", "Correggi: quello che ho detto", "", "", "⚠",
        cluster="9 I miei errori", verbs=[], verify="attested",
    ),
    "de": Topic(
        "de_meine_fehler", "de", "Korrigiere: was ich gesagt habe", "", "", "⚠",
        cluster=CLUSTER_BY_KEY["de_meine_fehler"], verbs=[], verify="attested",
    ),
}


def topics_for(lang: str) -> list[Topic]:
    if lang == "es":
        base = PILOT_TOPICS_ES
    elif lang == "de":
        base = TOPICS_DE
    else:
        base = _FIP_TOPICS.get(lang, [])
    f3_topic = F3_TOPICS.get(lang)
    return [*base, f3_topic] if f3_topic is not None else list(base)


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
    for lang in GRAMMAR_LANGS:
        for topic in topics_for(lang):
            if topic.key == key:
                return topic
    return None
