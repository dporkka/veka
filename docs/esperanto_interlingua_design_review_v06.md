# RFC: what Veka should borrow from Esperanto and Interlingua

**Date:** 2026-11-01  
**Status:** proposed, **noncanonical** design review; no Veka words or rules are changed by this RFC.  
**Compatibility:** preserve the 0.3 canonical 1,025-word dictionary, tonal/toneless profile separation, baseline `parse` behavior, exact-number semantics and fully scoped logic. The existing opt-in 0.5 `extend` layer remains experimental.

## Executive decision

Veka should borrow **Esperanto's transparent, teachable combinatorial morphology** and **Interlingua's attention to international recognition and minimal agreement**, but should not adopt either language's entire grammar or lexicon. Veka's objective is not fewest syllables per sentence, but **least total time to correctly recovered meaning** after teaching, production, hearing, clarification, and repair. An unmeasured gain in brevity or first-sight word familiarity is not evidence of a net gain.

The crucial finding is that much of the easy borrowing **is already present**:

- Esperanto-like machinery: Veka 0.5 already has 9 opt-in, typed event derivations (`-nes`, `-sul`, `-zel`, `-dil`, `-vuk`, `-kas`, `-mol`, `-koin`, `-vau`), and a 4 × 6 (24-form) correlative table.
- Interlingua-like machinery: Veka already uses fixed SVO/particles, without Esperanto-style obligatory adjective agreement or accusative marking, and has an **unverified** 100-concept international-word research queue with eight illustration-only candidates.
- More urgent than additional morphology: the 708 transparent noun-adjective compounds have an orthographic hyphen with **no audible boundary**, so a compound and an equivalent ordinary phrase can have identical spoken surfaces.
- Existing experimental extensions support strictly bounded relative and propositional clauses, while full multiquantifier binding, adverbial correlatives, comparison, reference resolution, and actual human comprehension validation remain absent.
- PR #9 separately proposes an opt-in 0.6 discourse/temporal layer. Avoid competing syntactic designs until that PR is reviewed and its exact-head validation is confirmed.

## Comparative decision table

| Source principle | Evidence | Decision for Veka | Reason |
|---|---|---|---|
| Esperanto: compositional roots and affixes | Esperanto Fundamento rule 11 and regular word endings | **Keep, refine** | Already partially implemented; concentrate on typed semantics, predictable valency and lexical boundaries rather than adding more affixes |
| Esperanto: systematic correlatives | Correlative paradigm; Veka already has 4 × 6 | **Expand only for demonstrated need** | A large fully populated table can create rare forms, lexical confusions and new scoping obligations |
| Esperanto: regular pronunciation | Fundamento rules 9–10 | **Keep romanized mapping regular; test tone** | Veka has four canonical rising-tone roots; the opt-in toneless profile is not empirically superior |
| Esperanto: adjective agreement and compulsory direct-object suffix | Fundamento rules 2–3 and 6 | **Do not borrow** | Veka's fixed SVO/valency grammar already identifies roles without repetitive marking |
| Interlingua: adjective invariance | IALA grammar §32 | **Keep** | Already fits Veka's simpler agreement-free grammar |
| Interlingua: immediately recognizable international roots | IALA vocabulary principles | **Research as optional lexical candidates** | Romance familiarity alone is not international accessibility, and longer forms may hurt speech efficiency |
| Interlingua: naturalistic alternative stems | IALA grammar §§146–150 | **Do not borrow** | Irregular derivational allomorphs increase memory and implementation cost |
| Interlingua: stylistic adjective position | IALA grammar §33 | **Do not borrow by default** | Optional position creates unnecessary parse alternatives unless human testing shows a benefit |
| Both: familiar and economical communication | Their design principles differ | **Measure the entire interaction** | Legibility, phonology, grammar and repair cost must be assessed together |

## P0 — resolve spoken compound identity before expanding the lexicon

**Current issue:** `ren-sak` (lexicalized compound, glossed 'expert') and `ren sak` ('knowledgeable person') have identical segmental sequences because the hyphen is silent. The lexical-risk audit reports 708 such potential pairs. This is a **type of structural ambiguity, not 708 proven comprehension errors**.

**Default proposed rule:** the spoken semantics of a productive noun-adjective compound are the same as those of its corresponding compositionally interpreted adjective phrase. The hyphen is a dictionary/spelling convention, not a semantic operator. If the lexical sense has drifted (for instance, 'expert' vs. 'knowledgeable person'), mark it as **lexicalized/noncompositional**, prohibit inference that its exact spoken identity is recoverable in isolation, and give it an unambiguous paraphrase in precision-critical contexts.

**Gate for a distinct spoken compound:** only adopt a separator or new word form if discourse listening tests show the distinct meaning must be recoverable **and** the candidate improves net comprehension after accounting for the added syllable. Do not silently introduce a compulsory separator into 708 forms.

**Proposed machine contract:** generate all canonical noun-adjective pairs; store `surface_tokens`, `compositional_gloss`, `dictionary_gloss`, and an explicit editorial `lexicalized` flag. Do not try to classify semantic drift using string similarity of English glosses. Reject a canonical lexicalized distinction without a documented spoken disambiguation policy.

## P1 — make derivations *semantically total where licensed*, not merely numerous

For every opt-in derivation operator, publish a machine-readable table with: input type, output type, participant role, argument mapping, aspect/causation presuppositions, stacking legality, scope behavior, and a counterexample.

Examples using **existing experimental** Veka expressions:

- `dak-nes` = participant who sends; **not automatically** paid courier.
- `dak-mol` = direct-object participant of sending; **not automatically** message.
- `gos-vuk` = cause another participant to go, only for a licensed intransitive base; not a generic transitive causative for all verbs.
- `dak-koin` = perform the sending event again; clarify whether 'again' implies a prior completed sending or can include failed attempts.
- `dak-kas` = *attempt* to reverse sending; must not imply that the reversal succeeds or is physically possible.

Before adding more operators, add metamorphic contract tests that check preservation of valency, predictable roles, invalid stacking rejection, and matched human paraphrase judgments. Avoid Interlingua-style irregular stem alternations and Esperanto-style affordance to freely create plausible but semantically ambiguous compounds.

## P1 — keep a transparent *international recognition* research track

Do not replace `do` ('data'), `nol` ('language'), `kun` ('information') or other one-syllable canonical roots simply because `da-ta`, `lin-gu-a` or `in-fo-ma-si-on` appear more recognizable in a few European languages. Those longer forms are **unverified experimental stimuli**, not adopted Veka.

The pilot should compare, per concept and participant:

1. first-sight **written semantic identification** (canonical / candidate / transparent paraphrase);
2. correct **spoken recognition** by independent talkers, both quiet and noise;
3. training time to a prespecified criterion, delayed recall and pronunciation;
4. cumulative **total correct-message time**, including clarification and repairs.

Sample at least several distinct language families, weight by **participants and target populations**, never count Portuguese, Spanish, French and Italian as four independent families, and record cognates, borrowings and false friends separately. A multilingual evidence citation is not a human intelligibility score. If data cannot reject a null benefit hypothesis, **retain the canonical form**. Favor recognizable spellings for a documented optional technical reading gloss rather than importing a parallel active spoken lexicon.

## P2 — finish high-utility conversation before adding new paradigms

Do **not** copy all Esperanto correlatives or Interlingua's permissive adjective placement. Prioritize these verified semantic needs instead:

1. **Quantifier scope and restricted domains.** Distinguish 'every person saw a message' (\u2200x\u2203y) from 'a message was seen by every person' (\u2203y\u2200x), with explicit domains and binding. Currently the canonical parser rejects two quantified roles; this is safer than inventing an interpretation. Review PR #9's location-restricted proposals separately.
2. **Negation polarity.** Specify that `ne` negates an atomic predicate while `na ... yu` scopes over a full proposition. Do not add a 'none/never' correlative series until its interaction with quantifiers and double negation has one unambiguous interpretation.
3. **Manner and quantity queries.** The `hon-wek` and `hon-gas` forms exist in the experimental matrix but are not yet accepted inside statements. Add typed adverbial positions only with explicit semantic categories and tests; avoid pretending the whole 24-cell table is conversationally implemented.
4. **Pragmatic reference and repair.** Provide overt clarification, self-correction and quotation mechanisms before optimizing longer discourse through context omission. Keep the explicit safety register separate from optional compact speech.
5. **Modality and comparison.** Define possibility, obligation, ability, comparative degree and negated scope with tests. Do not conflate truth-functional `fi` with causal/conditional natural-language 'if'.

For each addition, require at least one minimal-pair scenario where two structurally different utterances map to distinguishable semantic representations, plus an invalid-utterance test proving fail-closed behavior.

## P2 — revisit spoken and written ergonomics with humans

Esperanto's dependable spelling and Interlingua's familiar forms point to different advantages. Veka should preserve its deterministic romanization and test its featural script **separately**; the SVG metadata reader is not visual OCR or evidence of legibility. Current rising-tone versus toneless comparisons should include independent recordings from diverse speakers, accented productions, noise, unfamiliar listeners and high-cost words such as pronouns, negation and numerals.

No redesign should claim that fewer syllables automatically means faster transmission. An additional phonological boundary or syllable may improve communication if it prevents costly repairs.

## Proposed evaluation protocol and promotion policy

**Unit of optimization:** independently understood intended propositions per total interaction minute at a specified training budget and listener population. Include elapsed learning time, message production, listening, clarification, delayed recall, and critical errors as separately reported outcomes.

**Randomized comparisons:**
- A: existing canonical Veka baseline;
- B: one isolated morphology / compound policy change;
- C: one isolated international vocabulary or phonology candidate;
- D: familiar Esperanto/Interlingua examples used **as external benchmarks**, with equal training and task translations, **not** as simple translations presumed to be of identical complexity.

Do not pool learners of already-known source languages with true beginners without stratification. Randomize utterances and speaker/listener pairs; guard against repeated-target answer leakage; blind the adjudicator where possible. Pre-register error noninferiority margins and a sampling/power plan; do not declare arbitrary thresholds to be experimentally justified.

**Version gates:** (a) grammar specification and reversible migration, (b) property and regression tests, (c) acoustic/reading pilot, (d) cross-language replication, (e) only then promote to canonical Veka. Experimental `extend` grammar is not automatically language standard.

### Test scenarios for the next implementation PR

| Scenario | Required behavior |
|---|---|
| `ren-sak` vs `ren sak` | Explicitly document surface equivalence; no inferred lexical semantic difference without context |
| `dak-nes` / `dak-mol` | Agents and patients have distinct types and roles |
| `gos-vuk ti` | Causative preserves a unique overt causer and causee; disallow unauthorized transitive bases |
| `hon-wek` / `hon-gas` | Currently reject sentence insertion rather than silently guess manner/quantity slots |
| `ne` vs `na ... yu` | Distinct scope and formally documented quantifier interaction |
| Two quantified noun phrases | Continue fail-closed until explicit scope syntax exists |
| `da-ta` / `in-fo-ma-si-on` | Remain candidate-only; core parser must reject unregistered synonyms |
| Tense, modality, conditional nesting | Reject unsupported interpretations rather than fall back to plain material implication |

## Recommended order

1. **Now:** adopt this as a *decision record* only; preserve canonical Veka and complete the compound alias/lexicalization audit.
2. **Next:** finish typed derivational semantics and their executable property tests; audit total operator/segmental collision risk.
3. **Then:** close quantifier scope, polarity, manner/quantity and conversation-repair gaps, coordinating with PR #9.
4. **In parallel:** run genuine international-word first-sight and phonology listening studies.
5. **Later:** migrate canonical forms only on a measured, reproducible net gain with a backwards-compatibility plan.

## Sources and existing Veka documents

- Esperanto, *Fundamento de Esperanto*, rules 2, 3, 6, 9–11, 15: https://www.w.w.akademio-de-esperanto.org/fundamento/gramatiko_angla.html
- Esperanto correlative matrix (secondary overview): https://tamnd.github.io/brain/languages/esperanto/grammar/correlatives/
- Alexander Gode and Hugh Blair, *A Grammar of Interlingua* (1951), adjective §§31–34: https://adoneilson.com/int/gi/parts/adj.html
- Gode and Blair, Interlingua derivations and stem alternations §§146–150: https://adoneilson.com/int/gi/build/from_verb.html
- Veka: `docs/grammar_v03.md`, `docs/grammar_v05.md`, `docs/international_v04.md`, `docs/lexical_design_v05.md`, `docs/design_review_v04.md`.
- Related unmerged proposal: PR #9 (`feat(grammar): add Veka 0.6 discourse scope and temporal clauses`). Verify its status before merging overlapping syntax work.

**Evidence boundary:** This RFC reports grammar facts and current code/spec state; it presents design decisions as hypotheses. There is no Veka learner/speech experiment supporting superior worldwide efficiency.