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
    verbs: list[str] = field(default_factory=lambda: TOP_VERBS_ES)
    # Free-text constraints handed to the generator prompt.
    guidance: str = ""
    # Verification mode (docs/GRAMMAR_STRATEGY.md §8):
    #   "morph" — Tier A: answer checked against the morphology table.
    #   "blind" — Tier B: K independent blind solvers must all reproduce
    #             the answer from the sentence alone (correctness AND
    #             uniqueness in one test). For closed-class topics.
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


def topics_for(lang: str) -> list[Topic]:
    if lang == "es":
        return PILOT_TOPICS_ES
    return []


def topic_by_key(key: str) -> Topic | None:
    for t in PILOT_TOPICS_ES:
        if t.key == key:
            return t
    return None
