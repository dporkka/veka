# Veka 0.6 specification status and compatibility contract

**Status:** proposal and engineering contract, **not a new spoken-language release**.
As of 2026-11-01, the normative backwards-compatible language remains the
Veka 0.4 canonical lexicon and Veka 0.3 reference grammar. The Veka 0.5
morphology, correlatives, subordinate clauses, concise coordination,
and Veka 0.6 discourse structures remain **explicitly opt-in experiments**.

## Sources of authority

| Layer | Reference | Status |
|---|---|---|
| Canonical roots and compounds | `data/lexicon.csv` | Frozen by `data/canonical_contract_v06.json` |
| Core phonology and grammar | `docs/grammar_v03.md` | Frozen by the same manifest |
| 0.4 lexical profiles | `docs/design_review_v04.md` | Tonal canonical; toneless opt-in |
| 0.5 derivations, correlatives, clauses | `docs/grammar_v05.md` | Optional extension; not promoted |
| 0.5 lexical candidate ranking | `docs/lexical_design_v05.md` | Unmeasured research hypotheses |
| 0.6 topic/focus and temporal structures | `docs/grammar_v06.md` | Opt-in discourse parser |
| Veka 0.6 spoken semantics | This document | Clarification of existing forms only |

The manifest protects **bytes of canonical vocabulary and its grammar spec**.
It does not prove the implementation matches every sentence of the spec.
Changing a locked source requires a versioned compatibility proposal, a
migration path, tests, and an explicit manifest update. Ordinary bug fixes to
the reference parser are allowed if they preserve the documented grammar.

## Transparent compound policy: structural alias

All 708 canonical `noun-adjective` compounds are **transparent compounds**,
not separate audible semantic morphemes. Their written hyphen is silent, so
`ren-sak` and `ren sak` have the same segmental sequence and the same
compositional noun + adjective structure. A compact dictionary gloss such as
"expert" is a teaching convenience; it does not impose a distinct, audible
truth-conditional predicate or confer professional status.

An optional reference function, `normalize_nominal_surface(phrase, lex)`,
expands registered compounds to their two components while keeping overt
quantifiers, adjectives, quantities and possession unchanged. It validates
that the input is a **complete nominal phrase** before normalization. It
**does not** change the return value of `parse`, the canonical lexicon,
lexical identity, pragmatic context, or the spoken pronunciation.

- If a *future* compound must mean more than its composition, it requires an
  explicitly specified and perceptible morphological distinction and human
  listening validation; do not silently lexicalize the existing hyphen.
- Unregistered novel `head-modifier` forms are **not canonical words**.
- Spoken comprehension of a word/phrase pair is not established by AST
  normalization. The full 708-pair regression is a structural test only.

## Numeric scope collision

The form `wen` can be a canonical noun head or the exact-number marker.
The reference noun-phrase grammar only licenses the numeric marker **after**
the noun head (and modifiers), never *as* the head. Therefore:

- `Mi lin wen val.` is a noun phrase with an adjective, with **no number**.
- `Mi lin wen wen ran.` contains noun head `wen` followed by exact number 1.

The parser now extracts numeral semantics from legal positions rather than
treating every occurrence of `wen` as a number. This is a parser bug fix,
not a new grammatical interpretation.

## What must be tested before any canonical change

1. **Structural:** all existing core and experimental tests pass; complete
   compound alias coverage; seeded decimal encode/decode invariants;
   malformed input and scope markers fail closed; both profile variants work.
2. **Host execution:** exact-head hosted CI must run the test suite and research
   audits on supported Python versions via
   `.github/workflows/python-contract.yml`. Local checks are not hosted checks.
3. **Human communication:** preregister a cross-linguistic listener study
   including critical pronouns, negation, numerals, compound-vs-phrase
   distinction, and explicitly scoped clauses. Recruit and train actual
   participants; use independent human recordings, quiet/noise arms,
   held-out sentences, and report time to criterion, critical errors,
   confidence, clarification and correct messages per minute.
4. **Decision:** retain canonical forms if a candidate fails the predeclared
   critical-error noninferiority bound or fails to improve total correct
   communication time. No mock data can satisfy this gate.

The existing `docs/listening_protocol_v03.md`,
`docs/listening_protocol_v06.md`, and their study materials are
preparation, **not evidence**. Listening-pilot implementation is tracked
separately; this change deliberately does not write over its active worktree.

## What Veka 0.6 does *not* claim

No measured superiority over Esperanto, Interlingua, English, Portuguese
or other human languages. No operational speech-to-text, multi-party
referent resolution, full first-order logic, executable Veka programming
language, validated accessibility, Unicode-native script, or proven
phonological risk improvement. The experimental visual script remains
metadata-based SVG rendering, not standardized text encoding.

For international software development, keep **technical terminology and
stable semantic IDs as a separate opt-in registry** rather than overloading
ordinary Veka grammar. Do not replace conventional programming APIs until
multilingual developers demonstrably benefit.
