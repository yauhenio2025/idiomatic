# Asset Factory — famous-cast & famous-places amendment

> Deliverable of `docs/commissions/FAMOUS_CAST_ADDENDUM_COMMISSION.md`.
> Amends `docs/ASSET_FACTORY_STRATEGY.md` (cast §2, settings §1.5, schema
> §3.2, decisions §8). Session 2026-08-06. Status: **awaiting user review —
> nothing here is committed to.**
>
> **Probe verdict up front (honest):** the idea survives, conditionally.
> Recognizability after ligne-claire stylization is a **per-face property,
> not a yes/no on the concept**. A craggy, high-distinctiveness face
> (Brian Cox) stayed recognizable through stylization AND through insertion
> into a factory setting. A smooth, conventionally attractive face
> (Edie Falco) failed twice at the fast 4-step tier — including a
> caricature-strength retry — and only approached likeness in the slow
> max-quality mode. Consequence: famous casting works, but the roster must
> be **selected for stylization survival** and every face must pass a
> **per-face recognizability gate** before enrollment. Details §2.

---

## 1. The exclusion list — extracted, not guessed

**Rule (user's own, hard):** figures bound in the Mandarin Memory Palace
encode phonetics (initial sound → actor). None of them may appear in the
idiomatic cast; reuse would cross-wire two mnemonic systems.

### 1.1 Sources parsed

All under `~/projects/mandarin-videos/`:

| file | contributes |
|---|---|
| `data/actors.json` (41) | Sound → Actor real names |
| `data/actor-signoff.json` + `data/actor-signature-wardrobe-2026-06-15.json` (55 ids, identical key set) | the full current registry names |
| `data/actor-archetype-snapshot-2026-05-28.json` (25) | archetype de-brand names |
| `data/actor-audit-2026-07-20.json` | audit names |
| `data/actor-backfill-snapshot-2026-04-11.json` (3,020 rows) | historical actor names incl. retired |
| `worker/batch_first10_words.py` (`REDACT_PATTERNS`, `ACTOR_ARCHETYPES`, `PLACARD_OVERRIDES`) | aliases, de-brands, engine-filter tells |

### 1.2 The do-not-cast roster (union of all sources): 60 anchors

Bipasha Ray · Brian Eno · Bugs Bunny · Chapayev · Charlie Chaplin ·
Chicherina · chukcha · Clay Shirky · coolio · Cucaracha (Georgian police
officer) · DIck Shriver / Richard H Shriver · Diora / Diora Ziyaeva ·
Donald Duck · Droog from Clockwork Orange · Fernando Flores · Forrest Gump ·
George Soros · Gulliver · Ho Chi Minh · Hulk · Ioana Bestiuc · Ivan Krastev ·
Jill Rasmussen AUBG · John from Minsk · Justin Timberlake · lenny ·
Leonard Benardo · Lisa Brodey · Lupin (Netflix) · Mao Zedong ·
Mark Maksimchuk · Miuccia Prada · Mumu the dog · **Napoleon** · Nikki Rhodes ·
Ninja Turtle · nutracker · Peter Oser · Pia Manchini · Pinochet ·
Queen Elizabeth I · **Roy** · Shirley Manson · Shurik (Brilliantovaya Ruka) ·
Super Mario · Terry Winograd · Tica Moreno · Tim Wu · **Tina (Roy's
secretary)** · U2 Bono · Vijay Prashad · Warren Brodey · Winnie the Pooh ·
Woody · Yuliana Beleva · **Yuri Gagarin** · Zoolander · Жучка (Zhuchka) ·
(+ alias variants counted above).

Bolded entries are the ones that already vetoed "obvious" idiomatic picks
during this session (see §1.5) — proof the extraction was worth doing.

**Likeness ring (treated as excluded):** palace characters ARE these real
faces — casting the face casts the character:
Tom Hanks (Forrest Gump/Woody) · Ben Stiller (Zoolander) · Omar Sy (Lupin) ·
Malcolm McDowell (the Droog) · Aleksandr Demyanenko (Shurik; Yuri Nikulin
flagged too given the film-title ambiguity) · Boris Babochkin (Chapayev).

**REDACT tells (63 names/marks):** the worker's engine-filter scrub list
(Madonna, Beyoncé, Mick Jagger, Bruce Springsteen, Saakashvili, Robin
Williams, Stan Lee, Sherlock, franchise marks…). Not memory-hygiene
exclusions per se, but any candidate matching this list is **banned at the
video-escalation rung** (it is literally the list of what cloud filters
fight over) and flagged everywhere else.

### 1.3 The reproducible check

Verdicts: `EXCLUDED` (full-name or surname match vs an anchor) > `REDACT`
(likeness ring / worker REDACT list) > `NEAR` (shares a name token — human
judgment) > `OK`. Every cast candidate in this doc carries its verdict.
Re-run any time:

```python
#!/usr/bin/env python3
"""Mandarin Memory Palace exclusion checker (famous-cast amendment).
No args: print roster. Args or stdin lines: check candidate names."""
import json, re, sys, unicodedata
from pathlib import Path

DATA = Path.home() / "projects/mandarin-videos/data"
WORKER = Path.home() / "projects/mandarin-videos/worker/batch_first10_words.py"

def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()

def load_roster():
    names = {}
    def add(name, src):
        name = (name or "").strip()
        if not name or name.startswith("[TBD"):
            return
        key = " ".join(norm(name)) or name.lower()
        names.setdefault(key, [name, set()])[1].add(src)
    for x in json.load(open(DATA / "actors.json")):
        add(x.get("Actor"), "actors.json")
    for x in json.load(open(DATA / "actor-signature-wardrobe-2026-06-15.json")):
        add(x.get("name"), "signoff55")
    for x in json.load(open(DATA / "actor-archetype-snapshot-2026-05-28.json")):
        add(x.get("name"), "archetype-snapshot")
    for x in json.load(open(DATA / "actor-audit-2026-07-20.json")):
        add(x.get("name"), "audit-2026-07-20")
    for r in json.load(open(DATA / "actor-backfill-snapshot-2026-04-11.json")):
        add((r.get("actor") or {}).get("name"), "backfill-snapshot")
    return names

LIKENESS_RING = {
    "Tom Hanks": "IS Forrest Gump (fu-) / Woody voice",
    "Ben Stiller": "IS Zoolander",
    "Omar Sy": "IS Lupin, Netflix (lu-)",
    "Malcolm McDowell": "IS the Droog from Clockwork Orange (ru-)",
    "Aleksandr Demyanenko": "IS Shurik (shu-)",
    "Yuri Nikulin": "Brilliantovaya Ruka lead (shu- attribution ambiguity)",
    "Boris Babochkin": "IS Chapayev (ch-)",
}

def load_redact_names():
    src = WORKER.read_text()
    alts = re.findall(r'r"\\b\((.*?)\)\\b"', src, re.S)
    toks = set()
    for a in alts:
        a = re.sub(r'"\s*\n\s*r"', "", a)
        for t in a.split("|"):
            t = t.replace("\\xe9", "é").strip()
            if re.fullmatch(r"[A-Za-zé\- ]+", t) and t[:1].isupper():
                toks.add(t)
    return toks

def check(candidate, roster, redact):
    ctoks = norm(candidate)
    ckey = " ".join(ctoks)
    csurname = ctoks[-1] if ctoks else ""
    hits = []
    for key, (display, srcs) in roster.items():
        rtoks = key.split()
        if ckey == key:
            return ("EXCLUDED", f"full-name match: {display}")
        if csurname and len(csurname) > 2 and rtoks and csurname == rtoks[-1]:
            hits.append(("EXCLUDED", f"surname match: {display}"))
        elif set(ctoks) & {t for t in rtoks if len(t) > 2}:
            hits.append(("NEAR", f"shares token with anchor: {display}"))
    for ln, why in LIKENESS_RING.items():
        if " ".join(norm(ln)) == ckey:
            hits.insert(0, ("REDACT", f"likeness ring: {why}"))
    for t in redact:
        if " ".join(norm(t)) == ckey or (len(ctoks) > 1 and set(norm(t)) >= set(ctoks)):
            hits.insert(0, ("REDACT", f"worker REDACT list: '{t}'"))
    if hits:
        hits.sort(key=lambda h: {"EXCLUDED": 0, "REDACT": 1, "NEAR": 2}[h[0]])
        return hits[0]
    return ("OK", "")

if __name__ == "__main__":
    roster, redact = load_roster(), load_redact_names()
    cands = sys.argv[1:] or [l.strip() for l in sys.stdin if l.strip()]
    if not cands:
        for key in sorted(roster):
            d, s = roster[key]
            print(f"{d:45s} [{', '.join(sorted(s))}]")
    else:
        for c in cands:
            v, why = check(c, roster, redact)
            print(f"{v:9s} {c:35s} {why}")
```

Commission B should land this as `tools/exclusion_check.py` and wire
`factory_actors.exclusion_checked` to it (§7).

### 1.4 Standing policy (goes in every factory doc)

**Living-person policy (as amended by user verdict 2026-08-06):**
famous-likeness assets are for the user's private study material only —
never shared decks, never published artifacts, never public anything.

**Rescinded 2026-08-06:** the original "reference photos and likeness
renders never leave the laptop" clause. The user explicitly rejected it
("never gave it") and directed cloud generation of cast sheets for
quality: refs may be sent to image APIs (DashScope/Qwen first — no
likeness filter observed; ByteDance untested) via the server's
`/admin/genmedia-render`. The private-use-only rule above still stands;
so does the local-lane preference for high-volume insertions (cost).

### 1.5 What the check vetoed this session

`Napoleon` (EXCLUDED — palace anchor; would have been the obvious FR
history pick), `Yuri Gagarin` (EXCLUDED — obvious Eastern-bloc icon),
`Omar Sy` (REDACT — he IS the palace's Lupin; he was the natural FR
man-~35), `Logan Roy` as a caption name (EXCLUDED — surname collision with
palace "Roy" + "Tina (Roy's secretary)"; see the first-names-only rule
§3.4). NEAR flags requiring only awareness: Brian Cox (shares "Brian" with
Brian Eno — different person, different face), John Lennon ("John" token vs
John from Minsk), Richard David Precht ("Richard" token vs Richard H
Shriver). Also noted: the palace's `lenny` is unidentified — if it turns
out to be Lenny Kravitz, re-run the check before casting any Lenny.

---

## 2. The recognizability probe — results (6/6 renders, $0)

Protocol per commission: 2 faces outside the exclusion list (checked §1.5),
one male one female, Sopranos/Succession principals: **Brian Cox** (NEAR,
documented) and **Edie Falco** (OK). One Wikimedia Commons reference photo
each, laptop-only under `/srv/ai-models/outputs/factory/refs/`. All renders
Edit-2511 (single-model batch, `/free` issued after; queue confirmed empty
before starting — the server wasn't even running and was started for the
probe, then memory freed).

| # | render | file (`/srv/ai-models/outputs/`) | verdict |
|---|---|---|---|
| 1 | Falco → 4-step ligne claire | `probe_falco_style_00001_.png` | **FAIL** — generic blonde; could be several actresses |
| 2 | Cox → 4-step ligne claire | `probe_cox_style_00001_.png` | **PASS** — brow, jowls, scowl, hair, even the Logan-ish vest+cravat read instantly |
| 3 | Falco caricature-strength retry | `probe_falco_style_v2_00001_.png` | **FAIL, worse** — the model exaggerated a generic smile schema, not *her* features |
| 4 | Cox inserted into café setting (sheet as image2) | `probe_cox_insert_00001_.png` | **PASS** — same character at panel scale; minor wardrobe drift (sleeves recolored) |
| 5 | Falco inserted (v1 sheet) | `probe_falco_insert_00001_.png` | **FAIL** — identity lost; **plus a new failure mode: the 2-ref edit drained the setting to monochrome lineart** |
| 6 | Falco max-quality (no-LoRA, 40 steps, cfg 3, ~7 min) | `probe_falco_maxq_00001_.png` | **PROMISING** — markedly closer facial geometry (plausibly her), but came out as uncolored lineart; color control needs an iteration the 6-render budget didn't allow |

Side-by-side (LOCAL ONLY, never upload — living-person policy):
`/srv/ai-models/outputs/factory/probe_sidebyside.html`.

### 2.1 What this means (the honest generalization)

1. **The concept is not killed, but it is filtered.** Recognition survives
   stylization when it lives in *line-expressible geometry*: heavy brows,
   jowls, distinctive nose, signature hair/glasses/mustache, silhouette.
   It dies when identity lives in subtle proportions and skin — exactly
   what flat ligne claire discards. This matches caricature research
   (recognition = deviation from the norm face): faces near the norm have
   nothing for the style to keep.
2. **Roster consequence:** the casting matrix (§3) carries a
   **stylization-survival prior** per candidate (H/M/L). Prefer H; L
   candidates are listed only when the user's recognition of the person is
   overwhelming (they may still fail the gate).
3. **Process consequence — per-face gate:** every enrolled face must pass:
   (i) sheet render → the user names the person cold ("who is this?" with
   no hint); (ii) standard insertion → still nameable at panel scale.
   Two failed sheet attempts = the candidate is dropped to the fallback
   (next candidate in the slot, or fictional). This slots into the §2.5
   signoff flow as a new state (§7).
4. **Sheet rendering moves to max-quality mode** (no-LoRA, 40–50 steps,
   ~7 min/sheet). Render #6 shows the 4-step Lightning shortcut is itself
   a likeness-killer for medium faces; sheets are one-time frozen assets
   (≤50 × 7 min ≈ 6 h GPU, one-time) so the slow path is affordable.
   Insertions stay 4-step: render #4 proves identity is carried by the
   sheet, and per-night insertion volume needs the fast tier.
5. **New auto-QA gate:** the color-drain failure (render #5) — add a
   palette-saturation check comparing inserted panel vs source setting
   (the strategy §4.4 palette gate catches all-black, not de-colorization).
6. **Fallback if the user's own gate-testing disagrees with my reads:**
   caricature-strength prompting did NOT help (render #3) — the honest
   fallback for weak faces is *recast the slot*, not prompt harder.

---

## 3. The casting matrix

Frame: per-language core cast of 6 role slots (strategy §2.1) drawn from
that culture's icons, plus pan-cultural shared wings (the user's Sopranos /
Succession move, friend-pairs, correspondents). 2–3 candidates per slot;
**bold** = recommended. Columns: exclusion verdict (§1.3 checker, all run
this session) · stylization-survival prior (§2.1) · flags for the user
(deceased / politically live / "parasocial" = a figure from the user's
actual daily info diet, which maximizes recognizability but may feel odd
as study material — user's call as a class, decision D3).

### 3.1 Per-language casts (30)

**ES**
| slot | candidates (verdict · survival · flags) |
|---|---|
| woman ~35 | **Rossy de Palma** (OK · H — famously angular Picasso face) · Penélope Cruz (OK · M) · Úrsula Corberó (OK · L–M) |
| man ~35 | **Álvaro Morte** (OK · H — El Profesor glasses+beard) · Javier Bardem (OK · H — heavy brow) · Antonio Banderas (OK · M) |
| woman ~70 | **Carmen Maura** (OK · M–H — Almodóvar matriarch) · Ángela Molina (OK · M) |
| young ~19 | **Rosalía** (OK · H — signature brows/hair) · Ester Expósito (OK · L–M) · Aitana (OK · L) |
| prof. woman ~50 | **Ana Pastor** (OK · M — news anchor, user's register) · Maribel Verdú (OK · M) |
| prof. man ~45 | **Jordi Évole** (OK · H — glasses+scruff; parasocial) · Iñaki Gabilondo (OK · H — age 83, flag) |

**DE**
| slot | candidates |
|---|---|
| woman ~35 | **Sandra Hüller** (OK · M–H — Toni Erdmann/Anatomy of a Fall) · Paula Beer (OK · L–M) · Diane Kruger (OK · L) |
| man ~35 | **Franz Rogowski** (OK · H — instantly distinctive face+lip) · Daniel Brühl (OK · M — Good Bye Lenin! resonance) · Tom Schilling (OK · M) |
| woman ~70 | **Angela Merkel** (OK · **VH** — the haircut+posture are line-art native; retired but flag politically-adjacent) · Katharina Thalbach (OK · H) · Senta Berger (OK · M) |
| young ~19 | **Bill Kaulitz** (OK · VH — style icon) · Jamal Musiala (OK · M) · Luisa Neubauer (OK · L–M; politically live flag) |
| prof. woman ~50 | **Marietta Slomka** (OK · M–H — heute-journal; parasocial) · Anne Will (OK · M) |
| prof. man ~45 | **Jan Böhmermann** (OK · H — glasses+smirk; media-critic resonance; parasocial) · Christian Drosten (OK · M–H) · Richard David Precht (NEAR "Richard" token · H — silver mane) |

**FR**
| slot | candidates |
|---|---|
| woman ~35 | **Adèle Exarchopoulos** (OK · M) · Marion Cotillard (OK · M) · Léa Seydoux (OK · L–M) |
| man ~35 | **Pierre Niney** (OK · H — brows/nose) · Louis Garrel (OK · H) · Tahar Rahim (OK · M) — *Omar Sy vetoed: REDACT/likeness ring (§1.5)* |
| woman ~70 | **Catherine Deneuve** (OK · H — iconic hair) · Isabelle Huppert (OK · H) · Josiane Balasko (OK · M–H) |
| young ~19 | **Kylian Mbappé** (OK · H — globally iconic) · Angèle (OK · M) |
| prof. woman ~50 | **Léa Salamé** (OK · M–H; parasocial) · Florence Aubenas (OK · M — Le Monde reporter, deep resonance) · Christine Lagarde (OK · VH — silver crop+scarves; flag politically live, ECB) |
| prof. man ~45 | **Edwy Plenel** (OK · **VH** — THE mustache; Mediapart, media-critic resonance) · Fabrice Luchini (OK · H) · Raphaël Glucksmann (OK · M; flag politically live) |

**IT**
| slot | candidates |
|---|---|
| woman ~35 | **Alba Rohrwacher** (OK · H — pale, angular) · Monica Bellucci (OK · M–H) · Matilda De Angelis (OK · M) |
| man ~35 | **Luca Marinelli** (OK · H — Martin Eden) · Pierfrancesco Favino (OK · H) · Riccardo Scamarcio (OK · M) |
| woman ~70 | **Milena Vukotic** (OK · M–H — Fantozzi's Pina, deep-cut comedy resonance) · Sophia Loren (OK · H — age 91, flag) · Ornella Muti (OK · M) |
| young ~19 | **Damiano David** (OK · VH — eyeliner+tattoos) · Jannik Sinner (OK · H — red curls) · Victoria De Angelis (OK · M) |
| prof. woman ~50 | **Lilli Gruber** (OK · VH — red bob; Otto e mezzo/La7, literally the user's channel roster; parasocial) · Milena Gabanelli (OK · M) · Lucia Annunziata (OK · M) |
| prof. man ~45 | **Lucio Caracciolo** (OK · H — white mane+beard; Limes — the user's own `title_filter`; strongest parasocial flag in the whole matrix) · Toni Servillo (OK · H — the Jep face) · Roberto Saviano (OK · M–H; flag: lives under police escort — politically live) |

**PT** (Brazil-leaning, matching the corpus: BBC Brasil, CartaCapital, piauí)
| slot | candidates |
|---|---|
| woman ~35 | **Fernanda Torres** (OK · H — post-Oscar ubiquity; age 60, slot flexes) · Taís Araújo (OK · H) · Alice Braga (OK · M) |
| man ~35 | **Wagner Moura** (OK · H) · Lázaro Ramos (OK · H) · Selton Mello (OK · M–H) |
| woman ~70 | **Fernanda Montenegro** (OK · **VH** — THE face of Brazilian cinema; 96, flag) · Regina Casé (OK · VH — hair+smile) |
| young ~19 | **Anitta** (OK · M–H) · Endrick (OK · M — actually 19) · Bruna Marquezine (OK · L–M) |
| prof. woman ~50 | **Miriam Leitão** (OK · M–H — GloboNews economics; parasocial) · Maju Coutinho (OK · H) |
| prof. man ~45 | **William Bonner** (OK · H — the Jornal Nacional face) · Pedro Bial (OK · VH — bald+glasses) |

### 3.2 Shared wings (≈15) — the user's pan-cultural move

**Family wing — the Sopranos household** (plays домашние scenes in any
language; note the probe result):
Edie Falco / Carmela (OK · **probe-FAILED at 4-step**; enroll only if she
passes the max-quality gate) · James Gandolfini / Tony (OK · VH · flag
deceased 2013) · Michael Imperioli / Christopher (OK · H) · Lorraine
Bracco (OK · M–H) · Steven Van Zandt / Silvio (OK · VH — the hair; flag:
Springsteen-adjacent, "Bruce Springsteen" is a REDACT tell, Van Zandt
himself is clean).

**Power wing — the Succession ensemble** (boss/boardroom/politics scenes):
Brian Cox / Logan (NEAR "Brian" token · VH · **probe-PASSED both stages**) ·
Sarah Snook / Shiv (OK · M–H) · Kieran Culkin / Roman (OK · M–H) · Jeremy
Strong / Kendall (OK · M) · Matthew Macfadyen / Tom (OK · M) · Nicholas
Braun / Greg (OK · H — the height is a silhouette anchor) · J.
Smith-Cameron / Gerri (OK · M).
**Roy-collision rule (from §1.5):** the palace owns the name "Roy". If this
wing is approved, the registry stores actor real names, and every caption /
typeset label uses **first names only** (LOGAN, SHIV, GREG…) — the string
"Roy" never appears in any idiomatic asset. Decision D4.

**Friends wing — famous historical pairs** (the user's von-Restorff-friendly
suggestion; deceased-historical = likeness-risk-free and filter-free):
**Marx & Engels** (OK·OK · VH — two beards, public domain, and squarely the
user's intellectual register) · **Sartre & de Beauvoir** (OK·OK · VH —
glasses/wall-eye + headband) · Lennon & McCartney (NEAR "John" token / OK ·
H · Lennon deceased).

**Cross-language correspondents (strategy §2.1's 2 shared figures):**
**Christiane Amanpour** (OK · H) · **Ryszard Kapuściński** (OK · M–H —
Eastern-European resonance, patron saint of the world wing; deceased 2007) ·
wildcard: Tintin (OK · native ligne claire by definition · flag: Moulinsart
is litigious IP — local lane only, never video, never anything shared).

### 3.3 Size arithmetic

30 per-language + 5 Sopranos + 7 Succession + 6 pairs + 2 correspondents ≈
**50 at full build-out** — the top of the user's 40–50 band. Recommended
v1 enrollment order: probe-passed + VH/H candidates first (~25 faces),
gate the rest in as review capacity allows. The strategy's original 32
remains the floor if the user trims wings (decision D2/D6).

### 3.4 Hybrid recommendation for the everyday wing (argued, per commission)

**Recommendation: hybrid.** Famous faces for the 6 core slots + shared
wings; **fictional bit parts** (shopkeeper, waiter, random passerby —
the tier below recurring roles). Three reasons:
1. **Salience economics:** von Restorff cuts both ways — if every walk-on
   is famous, famousness stops being distinctive and the anchors dilute
   (same logic as the weirdness budget, §4.3).
2. **Probe economics:** each famous face costs a max-quality sheet + a
   recognizability gate + exclusion bookkeeping. Bit parts don't get
   enough panel-time to amortize that; fictional extras are free and
   proven (pilot cast held identity across beats).
3. **Risk surface:** every additional real face is another likeness to
   police at the video rung and in any future sharing decision. Keep the
   real-face roster exactly as large as the memory-anchor benefit, no
   larger.

---

## 4. The famous-places register

Places are **filter-free** (no likeness, no living-person constraint) —
they work in BOTH lanes, including cloud Nano Banana and the video rung.
This asymmetry matters: famous places can ship anywhere the factory
renders, while famous faces are local-lane-only (§5).

### 4.1 Plausible lane — famous counterpart per mined setting

The strategy's 14 settings (§1.5 there) each get a famous default; the
per-language flavor rule carries over (flavored for the 5 conversation
hosts). "Famous" here = recognizable-to-this-user architecture and dressing;
prompts describe the place, typeset never names it (names in art = garble
risk).

| # | setting | famous counterpart (plausible lane) | per-language variants where natural |
|---|---|---|---|
| 1 | open-plan office | the Waystar-Royco floor (glass + skyline) | — |
| 2 | boss's office | Logan's corner office; alt: the Godfather study (dark wood) | — |
| 3 | family kitchen / dinner table | the Soprano kitchen-island + dinner table | PT: Montenegro-era Rio apartment kitchen; IT: Fantozzi-flat kitchen |
| 4 | living room | the Soprano den; alt: the Simpsons couch (cartoon, zero risk) | — |
| 5 | café / bar | **Café de Flore** (FR) as the archetype | ES: Chocolatería San Ginés; IT: Caffè Florian; PT: Confeitaria Colombo; DE: Café Einstein |
| 6 | street / city square | Abbey Road crossing (crossing view!) | ES: Plaza Mayor; IT: Piazza Navona; PT: Copacabana sidewalk mosaic; DE: Hackescher Markt; FR: Rue Crémieux |
| 7 | shop / market | La Boqueria (ES archetype) | PT: Mercado Municipal SP; DE: KaDeWe food hall; IT: Rialto market; FR: Marché d'Aligre |
| 8 | classroom / exam hall | Sorbonne amphitheater | — |
| 9 | stadium | one per language: Camp Nou · Westfalenstadion (yellow wall) · Stade de France · San Siro · **Maracanã** | (this row IS per-language) |
| 10 | station / airport / trail | Gare de Lyon hall; trail: **Camino de Santiago** waymark / Cinque Terre path | — |
| 11 | newsroom | **the Washington Post newsroom** (All the President's Men) | IT: a La7 open floor; FR: Le Monde glass HQ |
| 12 | TV studio / press conf | **the White House briefing room**; talk-set: the Otto e mezzo studio | — |
| 13 | parliament corridor / ministry | **the West Wing corridor**; per-lang: Bundestag dome walkway · Palais Bourbon · Montecitorio · Planalto ramp · Congreso lions | (per-language natural) |
| 14 | platform world | NASA Mission Control rows; server hall: CERN data centre | — |

### 4.2 Weird lane — the wildcard pool

Deliberately incongruous locations for weird-person-in-weird-place
pairings: the Louvre (Mona Lisa room) · **Chernobyl control room**
(user-proposed; NB the user's own Belarusian resonance — kept because they
named it) · ISS module · Sistine Chapel · Versailles Hall of Mirrors ·
Pompeii street · Titanic grand staircase · UN General Assembly hall ·
Kremlin St George Hall · LHC tunnel · Antarctic research station ·
Machu Picchu terrace · Red Square at night · a Vegas casino floor ·
Area 51 hangar. (Hogwarts-tier franchise interiors deliberately left out —
IP filters at the video rung; the pool above is real-world and free.)

### 4.3 The weirdness budget: **1 strip in 6 (~17%), hard cap 20%**

Justification from the memory literature, applied honestly:
- The **bizarreness effect is mixed-list-dependent** (McDaniel & Einstein
  1986 and the replication line): bizarre items are remembered better than
  common ones *only when a minority within a mixed set*; in pure-bizarre
  lists the advantage disappears. Weirdness is a **relational** resource —
  it spends the contrast the plausible majority builds up.
- **Von Restorff isolation** likewise requires a stable norm to violate.
  At 50% weird there is no norm; at ~15–20% each weird strip lands on a
  backdrop of plausibility.
- In Anki the "list" is the review session: at 1-in-6, a 10–20 card
  session surfaces 1–3 weird strips — isolated enough to pop, frequent
  enough to matter.
- The plausible lane also carries **semantic encoding** (scene ≈ meaning
  context, the strategy's whole §1 investment); weird placement trades
  that away, so it must be *bought* deliberately, not sprinkled freely.

**Assignment rule (deterministic, not vibes):** weird placements are
assigned first to items that have *earned* salience spending — rescue
items at strike ≥2 (comics already tried, still failing) always draw from
the weird pool; the remainder of the ~17% is a seeded-random sprinkle over
ordinary items (seed = expression id, reproducible). The strategy's
plausibility default stays the norm for everything else. Weird pairings
prefer a **semantic hook when one exists** ("estar en las nubes" → ISS)
and pure incongruity otherwise. Number is decision D5.

---

## 5. Engine / likeness policy per pipeline stage

The original strategy chose fictional faces because mandarin's CLOUD
filters made real faces expensive (REDACT/archetype machinery). Idiomatic's
comic pipeline is LOCAL — no filter exists on the laptop. Codify the lanes:

| stage | engine | likeness allowed? | policy |
|---|---|---|---|
| cast sheets | local Edit-2511, **max-quality mode** (§2.1.4) | YES | from `refs/` photo; laptop-only artifacts |
| settings (t2i, no people) | local 2512 **or cloud Nano Banana** | n/a — none by construction | famous places fine in both lanes (§4 asymmetry) |
| insertions (cast into panels) | local Edit-2511, 4-step | YES | sheet as image2; **never sent to any cloud engine** |
| no-cast panels, glyphs, diagram PNGs | local or cloud | NO likeness content | cloud OK precisely because likeness-free |
| typeset / stitch | PIL, anywhere | n/a | names appear typeset-only; first-names-only for Succession (§3.2) |
| **video escalation** | MiniMax / Seedance / Veo (cloud only) | implicit, via panel refs | fallback ladder below |

**Video-rung fallback ladder** (inherits mandarin's filter fights —
`hh_worker.py` adapters, `REDACT_RE`, `ACTOR_ARCHETYPES`, placard
de-brands):
1. **Panels-as-refs, names-scrubbed:** the approved comic panels go up as
   image refs (likeness implicit); the text prompt is wardrobe-and-action
   only (`_wardrobe_only` discipline), passed through `REDACT_RE`, and
   **never contains a real name**. MiniMax first (measured most
   likeness-tolerant), Seedance second (rights filter aggressive), Veo
   only on explicit user pick.
2. **On filter rejection:** apply the mandarin identity-de-brand playbook —
   archetype description instead of the person ("a gruff white-haired
   media patriarch in a burgundy vest"), placard-style de-brands if any
   text badge appears. The user accepts likeness drift at this rung
   (their stated position) — the comic remains the identity anchor.
3. **Exhausted / budget error:** skip escalation for the item, comic stays
   hero. Budget/balance errors are TERMINAL, never rung-advance (mandarin
   rule, kept).
Candidates carrying a REDACT-tell name (§1.2) skip straight to step 2's
description style or are simply not escalated.

---

## 6. Sheet-sourcing workflow

1. **Source**: one clean, frontal, well-lit reference photo per approved
   candidate from the internet (Wikimedia Commons preferred — clean
   licensing and high resolution; the probe used it).
2. **Store**: `/srv/ai-models/outputs/factory/refs/` — laptop-only by
   convention. This directory is **never** uploaded, committed, synced, or
   referenced by any server path. (It lives outside every git repo; the
   factory upload endpoint (strategy §3.3) only ever receives approved
   FINAL strips, which is enforced by the uploader whitelisting
   `factory/<lang>/` paths — commission B acceptance item.)
3. **Stylize**: Edit-2511 max-quality (no-LoRA, 40–50 steps) → ligne-claire
   cast sheet, front bust + full body + ¾ (strategy §2.3 spec unchanged),
   fixed outfit with 2–3 signature elements.
4. **Gate**: the user names the person cold; insertion check; two failed
   sheets = recast the slot (§2.1.3).
5. **Register**: the **stylized sheet** is what `factory_actors` stores and
   what every insertion consumes as image2. The photo never enters the
   registry; `ref_photo_local_path` records its laptop location as a
   convention string only (§7).
6. **Naming**: registry rows carry real names (the user must recognize
   who's who in the Cast page); cards typeset names only (letter-perfect,
   free) — and never the string "Roy" (§3.2).

---

## 7. Schema deltas for commission B (strategy §3.2 amendment)

```
factory_actors  (additions)
    real_name            TEXT        -- NULL for fictional bit parts (§3.4)
    famous_source        TEXT        -- show/film/era ("Succession", "Måneskin")
    exclusion_checked    BOOLEAN NOT NULL DEFAULT FALSE
    exclusion_verdict    TEXT        -- 'OK' | 'NEAR: <note>' (EXCLUDED/REDACT
                                     -- rows are simply never inserted)
    ref_photo_local_path TEXT        -- laptop convention string, NEVER a
                                     -- server path; server code never reads it
    survival_prior       TEXT        -- 'VH'|'H'|'M'|'L' (§2.1)
    likeness_lane        TEXT NOT NULL DEFAULT 'local_only'
                                     -- 'local_only' (real faces) | 'any'
                                     -- (fictional); video rung checks this
```

Casting-matrix approval states (extends the §2.5 flow; sheet-hash demotion
rule unchanged):

```
proposed → user_picked → sheet_rendered → gate_passed → approved → retired
                              ↑ (2 failed gates → back to proposed with
                                 next candidate, or slot goes fictional)
```

`exclusion_checked` must be TRUE (with verdict recorded) before
`user_picked` can be entered — the Cast page enforces it and links the
checker output. No other schema changes; `factory_settings` needs nothing
(famous places are just prompt content + a `famous_name` note column if
desired — optional, not required).

---

## 8. Amended user-decision list

Replaces strategy §8 items 1–2; items 3–9 there stand unchanged.

- **D1 — Casting frame.** Approve the famous-cast amendment as probed:
  famous faces selected for stylization survival, per-face recognizability
  gate, max-quality sheets. (The probe says yes-with-filter, not
  unconditional yes — §2.)
- **D2 — Roster picks.** Pick 1 winner per slot from the §3 matrix (bold =
  recommendation), including explicit OK/veto on every flagged candidate:
  deceased (Gandolfini, Kapuściński, Sartre/Beauvoir, Lennon, Marx/Engels),
  politically live (Merkel, Lagarde, Glucksmann, Saviano, Neubauer),
  advanced age (Montenegro 96, Loren 91, Gabilondo 83).
- **D3 — The parasocial class.** Faces from your actual daily info diet
  (Caracciolo, Gruber, Évole, Slomka, Böhmermann, Salamé, Leitão, Bonner):
  maximum recognizability, but you'll study grammar with the people who
  narrate your news. In or out, as a class?
- **D4 — The Roy collision. RESOLVED (user, 2026-08-06):** the palace's
  "Roy" is a DIFFERENT person, unrelated to the Succession family — no
  collision exists. Succession wing stays; no captioning restriction
  required (comics naturally use first names anyway).
- **D5 — Weirdness budget.** 1-in-6 (~17%), hard cap 20%, strike-≥2 items
  first + seeded sprinkle (§4.3). Approve the number or set your own.
- **D6 — Cast size & hybrid.** ≈50 at full build-out (§3.3) with fictional
  bit parts below the recurring tier (§3.4). Approve hybrid + size, or trim
  to the 32 floor.
- **D7 — Edie Falco / weak-face policy.** She failed the 4-step probe. Rule
  on the general policy: candidates that fail the gate twice are recast
  (recommended), even when the person is a named part of your original
  vision.
- **D8 — Tintin wildcard.** Native ligne claire, litigious IP: enroll as
  third correspondent (local lane only, never video, never shared), or skip.

---

*Probe artifacts (all laptop-local, living-person policy):
`/srv/ai-models/outputs/probe_{falco,cox}_*.png`,
`/srv/ai-models/outputs/factory/refs/`,
`/srv/ai-models/outputs/factory/probe_sidebyside.html`.
Exclusion roster reproducible via §1.3 script.*
