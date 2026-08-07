# Illustration-prompts commission (corpus-wide, per-chunk codex)

> Goal: an image-generation brief for EVERY example sentence in the
> fluency-expressions corpus (17,112 sentences across 2,858 expressions,
> de/es/fr/it/pt). The briefs drive local rendering (Fedora + Mac idle
> power); images embed into the EXISTING Anki cards as an extra field.
> One brief per sentence, grouped under one ANCHOR per expression.

## Input

`idiomatic/grammar/data/illustration_prompts/input/<lang>_illu_bNN.json` — a JSON array of
expression objects:

```json
{
  "expression_id": 439,
  "lang": "es",
  "idiom": "a primera hora",
  "explanation_en": "…literal meaning + usage notes…",
  "examples": [
    {"example_id": 2503, "en_text": "…", "target_text": "…"},
    …up to 6…
  ]
}
```

## Output

`idiomatic/grammar/data/illustration_prompts/output/<lang>_illu_bNN.json` — a JSON array,
one object PER INPUT EXPRESSION, same order:

```json
{
  "expression_id": 439,
  "idiom": "a primera hora",
  "anchor": {
    "semantic_hook": "one sentence: how the idiom's LITERAL wording is
      staged visually (e.g. 'a primera hora' = 'at the first hour' ->
      a giant clock face whose hand points at 1, dawn light)",
    "setting": "the reusable scene WITHOUT people and WITHOUT text —
      concrete objects, place, light. 2-4 sentences. Must contain the
      hook and ONE absurd/surreal memorable element.",
    "cast": ["slug", "optional_second_slug"],
    "absurd_element": "one phrase naming the deliberate absurdity"
  },
  "variations": [
    {
      "example_id": 2503,
      "inserts": [
        {"slug": "pedro_sanchez",
         "action": "sits bolt upright in bed reaching for a briefcase,
           hair comically perfect, the giant dawn clock outside the
           window pointing at 1"}
      ],
      "scene_adjust": "optional short phrase if the anchor setting needs
        a sentence-specific prop (else empty string)"
    },
    …one per example, same order as input…
  ]
}
```

## Hard rules (each verified by the gate and/or audit; violations = redo)

1. **Anchor constancy.** One semantic hook + one setting + the same cast
   across ALL of an expression's variations. Variations change ACTION,
   pose, emotion, props — never the place or the people.
2. **Semantic hook = the idiom's LITERAL wording made visible.** Use
   `explanation_en` (it states the literal translation). The hook is
   architecture/objects, not captions.
3. **Sentence fidelity.** Each variation depicts ITS sentence's concrete
   situation (the sentence text appears on the card next to the image —
   they must match). The en_text tells you the situation.
4. **Absurdity mandate.** Every anchor setting contains exactly one
   striking surreal element (scale distortion, impossible physics,
   surreal weather, wrong-material objects…). Memorable > plausible.
   The absurd element must AMPLIFY the hook, not compete with it.
5. **Literal visible language only.** Describe what a camera would see.
   BANNED in `setting`/`action`: "like a …", "as if", "symboliz…",
   "metaphor…", "represent…", "evok…" — a diffusion model draws the
   comparison object literally (a coat "like a collapsed figure"
   produced a corpse).
6. **No text in images.** Never request signs, labels, letters, words,
   numbers-as-text, logos, brands. Clocks/dials are fine (hands, not
   digits).
7. **Cast discipline.** ≤ 2 people per image; most variations need ONE.
   Use the language's own roster for that language's expressions;
   shared-wing members allowed anywhere sparingly (≤1 in 6 expressions).
   Only these slugs exist:
   - es: penelope_cruz javier_bardem cristina_kirchner rosalia
     nadia_calvino pedro_sanchez
   - de: juju capital_bra angela_merkel luisa_neubauer
     sahra_wagenknecht jurgen_klopp
   - fr: marion_cotillard timothee_chalamet catherine_deneuve
     kylian_mbappe christine_lagarde emmanuel_macron
   - it: elodie fedez sophia_loren jannik_sinner giorgia_meloni
     roberto_saviano
   - pt: anitta wagner_moura dilma_rousseff kevinho marina_silva
     fernando_haddad
   - shared: james_gandolfini edie_falco michael_imperioli
     lorraine_bracco steven_van_zandt brian_cox sarah_snook
     kieran_culkin jeremy_strong matthew_macfadyen nicholas_braun
     j_smith_cameron karl_marx friedrich_engels jean_paul_sartre
     simone_de_beauvoir john_lennon paul_mccartney christiane_amanpour
   Rotate within the roster across expressions (no slug on >25% of a
   chunk's expressions). Match demographics to the sentence when it
   implies one (a doctor's patient, a grandmother, a teenager…).
8. **Action lines are pose/emotion/position ONLY.** The renderer appends
   the identity-copy phrasing and style prefix itself. Do not mention
   reference images, sheets, faces, or style in `action`.
9. **Style-free content.** No "ligne claire", "comic", "photorealistic",
   color-palette or lighting-style words in any field — the renderer
   owns style. (Scene-light like "dawn light" is content, that's fine.)

## Workflow per chunk

```
codex exec -s workspace-write "Read docs/commissions/ILLUSTRATION_PROMPTS_COMMISSION.md
and author idiomatic/grammar/data/illustration_prompts/output/<lang>_illu_bNN.json for
input chunk idiomatic/grammar/data/illustration_prompts/input/<lang>_illu_bNN.json. Follow
every hard rule. Self-check against the gate before finishing:
.venv/bin/python tools/illu_prompts_gate.py idiomatic/grammar/data/illustration_prompts/output/<lang>_illu_bNN.json"
```

Gate must pass (0 errors) before a chunk counts as delivered. Sessions
may revise landed outputs — merges are idempotent re-reads of the latest
files, never appends.

## Sizing

~12 expressions (≈70 sentences) per chunk:
de 52 · es 38 · fr 38 · it 68 · pt 45 chunks ≈ 241 total. Pilot = one
es chunk, user-reviewed before the campaign fans out.
