# Veka 0.5 — typed derivation and correlative semantics (experimental)

**Status:** opt-in, machine-tested research prototype. **Not canonical Veka.** No acoustic, reading, learnability, or semantic-validation results from human speakers have been collected. The canonical `data/lexicon.csv` is unchanged at 1,025 entries; the existing head-first noun–adjective compounds remain unchanged. Both Veka 0.4 research extensions (international word-recognition candidates and explicitly selected tonal/toneless profiles) are available.

## Why this scope

The highest-leverage import from Ido and Esperanto is a small number of **predictably interpreted operations**, not wholesale borrowing of affix spellings, romance roots, or grammatical inflection. The primary value is to reuse 66 existing verb roots. Each derivation has one transparent role, input class, output class, and deterministic morpheme boundary. The existing parser enforces valency. All operations require a canonical *verb root*; arbitrary compound stacking and silent category conversion are rejected.

The six proposed operator syllables are not proposed canonical vocabulary. They are phonotactically legal, mutually different, unused in either canonical or 0.4 toneless lexical profile, and at least two orthographic edits from every critical logical/grammatical particle in `veka.phonology.CRITICAL_OPERATORS`. **Edit distance is not a validated auditory confusion metric.** The forms may change after listening studies.

## Typed verb derivations

| Operation | Proposed suffix | Input | Output | Narrow interpretation |
|---|---|---|---|---|
| `agent` | `rik` | any verb root | noun | subject participant in the action |
| `patient` | `mol` | transitive verb root | noun | direct-object participant in the action |
| `instrument` | `zas` | any verb root | noun | possible instrument used for the action |
| `place` | `dai` | any verb root | noun | place where the action occurs |
| `repeat` | `koin` | any verb root | verb | repeated action, preserving original valency |
| `passive_able` | `vau` | transitive verb root | adjective | entity capable of undergoing the action as the direct object |

Illustrative examples (experimental, not accepted by the **default** parser):

- `dak-rik` — agent of `dak` (send), not an unnamed grammatical subject.
- `dak-mol` — direct-object participant of sending, not sender.
- `dak-koin` — send again, preserving transitive valency.
- `dak-vau` — capable of being sent, not capable of sending.
- `Mi pa dak-koin mel.` — a simple past-tense clause with an experimental derived predicate.

These definitions are **possible semantic classes**, not existence claims. `instrument(V)` does not assert that the action has a tool. `place(V)` does not assert that there is a dedicated building for it. `agent(V)` does not imply a profession or habitual performance. `repeat(V)` does not automatically specify the event's identity in discourse. No causative is introduced: causing another person to perform an intransitive verb requires explicit argument-binding semantics that the v0.5 parser does not yet support.

### Parsing and collision rules

- `ROOT-SUFFIX` is exactly two Veka syllabic segments separated by an existing hyphen. Only **canonical verb roots** are eligible, except the selected tonal/toneless root substitutions in their own named profiles.
- The complete generated form must be phonotactically valid and unused in the selected input lexicon; every operator marker must also be unused. A collision fails closed instead of overriding a dictionary entry.
- A matching reverse decoder maps every generated word to **one** (root, operation, class, valency, interpretation) record. Nested derivation, e.g. `dak-rik-koin`, is not implemented.
- `experimental_lexicon` makes a fresh copy and generates 356 candidate entries in the selected profile. It never mutates the canonical lexicon. The default parser rejects new forms until explicitly opted into that expanded lexicon.
- The validator proves surface and parser contracts, **not** what real speakers hear or infer.

## Esperanto-style correlative grid — semantic contract only

The matrix includes **six series** (`question`, `this`, `that`, `some`, `every`, `none`) crossed with **four dimensions** (`person`, `thing`, `place`, `time`), yielding 24 typed cells. Each cell has a deterministic `series:dimension` identity.

Only **four cells** can currently reuse existing Veka noun phrases without inventing forms: `kis ren` (some person), `al ren` (every person), `kis nus` (some time), and `al nus` (every time). These are **existing constructions**, not new single-word correlatives. The others deliberately have `surface: null` and `status: semantic_design_only`, because Veka has not yet accepted new forms for thing/place/question/demonstrative/negative quantification. In particular, `none` cannot be replaced by `ne` (predicate negation) or `na` (propositional negation): quantifier scopes would differ.

An open semantic cell is a **design specification**, not a way to express that meaning in accepted Veka. This prevents a false claim of grammar coverage.

## Commands

```sh
python -m unittest discover -s tests -v
python -m veka experimental-audit
python -m veka experimental-audit --profile toneless
python -m veka experimental-derive dak agent
python -m veka experimental-derive fok repeat --profile toneless
python -m veka parse 'Mi pa dak-koin mel.' --experimental-v05 --strict
python -m veka parse 'Mi fok-koin mel.' --experimental-v05 --profile toneless --strict
python -m veka experimental-correlative every person
python -m veka experimental-correlative question place
```

By default `python -m veka parse 'Mi pa dak-koin mel.'` must fail. Explicit opt-in is required for any experimental derivative. Core numeral syntax, logical particles, positional arguments, and fixed SVO order are unchanged.

## Validation and deployment gates

1. **Mechanically verified now:** 356 non-shadowing derivatives, one-to-one reverse derivation, sound-shape legality, preservation of original transitive/intransitive valency, explicit rejection of invalid transformations, optional integration with the reference parser, compatibility with both tone profiles, preservation of all 1,025 dictionary entries, and complete regression test coverage.
2. **Still unsupported:** grammatical question/negative/demonstrative correlatives, full multi-quantifier binding, comparison, relative clauses, causal/permissive modality, instrument selection constraints, recursions beyond the current grammar, and pragmatic sense disambiguation. Unsupported forms must remain rejected.
3. **Before any adoption:** pre-register speech and learning experiments with different first-language backgrounds; include clean and noisy recordings, randomized lexical identification, semantic paraphrase, and conversation repair. Compare comprehended propositions per total time and critical-error rates against the unchanged Veka 0.3/0.4 control. Test candidate suffixes for confusion with existing roots and each other in actual audio rather than relying on string edit distances.
4. **Governance:** promote no candidate to `data/lexicon.csv` until there is human evidence, agreement about semantics, a reviewed migration story for canonical spellings, and no unacceptable regression in established comprehension.

## Source integration note

Two distinct Veka 0.4 bundles were combined here: the international-recognition prototype and the experimental tonal/toneless-profile prototype. The latter also tightened punctuation handling, bounded recursive possession, and rejected invalid or duplicated listener study conditions. Both corresponding test suites are included. The GitHub repository `dporkka/veka` was empty at the time this source bundle was assembled, so this artifact has not been pushed to a repository branch.
