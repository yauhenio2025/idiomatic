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
    mood: str                # morphology.py lookup key
    tense: str
    symbol: str              # tiny on-card cue, KOFI-style
    verbs: list[str] = field(default_factory=lambda: TOP_VERBS_ES)
    # Free-text constraints handed to the generator prompt.
    guidance: str = ""


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
