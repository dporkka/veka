# Veka v0.9 — everyday learnability requirements and beginner lessons

**Status:** noncanonical teaching and research tooling. This does **not** revise
Veka's frozen v0.4 lexical contract, v0.3 grammar, or experimental v0.5/v0.6
syntax. No human learning, spoken comprehension, or superiority over another
language has been demonstrated.

## Starting to learn

```sh
python3 -m veka learn --level 1
python3 -m veka learn --level 2
python3 -m veka learn --level 3
python3 -m veka learn --level 4
python3 -m veka beginner 'Mi pa dak mel.'
```

The four levels have 16 distinct, **canonical-tonal**, strict-core sentences
checked with `inspect_register`. Each has an editorial English interpretation.
They cover subjects and tense markers; object arguments and negation; common
verbs; and quantified/decimal examples. Syntax acceptance is **not** a
judgment that a novice could understand the sentence, that translations are
unique, or that speakers have acquired the material. The JSON includes
`human_learning_validated: false`.

These are **starter examples**, not a fabricated 120–150-root frequency list.
Choose a beginner lexical set later from actual measured usage and teaching
costs across language backgrounds; frequency in English alone is not enough.

## Everyday dialogue requirements

```sh
python3 -m veka everyday-audit
python3 -m veka everyday-audit --domain clarification
python3 -m veka everyday-audit --domain teamwork --include-items
python3 -m unittest discover -s tests -p 'test_everyday_v09.py' -v
```

`data/everyday_dialogues_v09.json` contains **100 distinct two-turn English
scenarios**, 10 each across introductions, essentials, navigation, commerce,
scheduling, social interaction, clarification, planning, teamwork and numeracy.
Every row has an ID, domain, scenario name, two English turns, and heuristic
required-feature tags, e.g. `scope`, `comparison`, `repair`, or `urgency`.
All rows are marked `translation_status: not_attempted` and have **no Veka
translation**. This is a requirements inventory and should not be used to
claim that any feature is definitely missing, supported, or understood by
actual speakers. The report explicitly shows **zero machine-verified
translations** and `language_coverage_established: false`.

## Proposed next evaluation protocol

1. Select a representative, stratified subset by communicative goal and
   consequence of misunderstanding; do not teach answers from the test set.
2. Independently propose **two-turn Veka translations**, with trained human
   translators reviewing meaning and pragmatic fit. Record a frozen source
   utterance, English intent, grammar profile, register, and editorial notes.
3. Check each proposed Veka utterance with `register-check`, distinguishing
   `core`, `precise`, `research`, and rejected forms. Parser acceptance is
   a **syntax signal only**; independently evaluate intended semantics,
   discourse reference, conversational repair, and everyday conditional meaning.
4. Compare learner comprehension with a preregistered trial: balanced prior
   exposure; diverse native languages; held-out dialogs; independent human
   speakers; acoustic quiet/noise comparisons; delayed recall and teaching time.
5. Report accuracy, **correctly recovered meanings per total minute** including
   clarification and training cost, error severity, and uncertainty by speaker,
   listener and item. Keep the existing canonical grammar unchanged when
   evidence is insufficient or results are inconclusive.

### High-value grammar questions raised by the corpus

- **Clarification:** Can a learner ask for repetition, correct a referent, and
  distinguish `some` versus `all` without relying on an unshared context?
- **Everyday conditions:** Can the language distinguish predictive or causal
  "if" from v0.3's formal material implication operator `fi`?
- **Time:** Can it express ordinary recurring schedules, timezone references,
  approximations and dates, beyond exact decimal quantities?
- **Social speech:** Does it offer natural polite requests, apologies,
  refusals, corrections and disagreement?
- **Conversation:** Can two speakers carry a multi-turn exchange naturally
  without using experimental parsers as though they were canonical?

These are **questions** for future specification work, not claims that
certain constructions are impossible. See `docs/registers_v08.md`,
`docs/meaning_pilot_v06.md`, `docs/grammar_v05.md`, and
`docs/grammar_v06.md` for the existing grammar and experimental caveats.

## Preservation and validation

`make validate` runs the repository tests and existing structural research
audits; `python -m unittest discover -s tests -q` includes the new contracts.
The new files use only the Python standard library. They do not alter
`data/lexicon.csv`, `docs/grammar_v03.md`, `data/canonical_contract_v06.json`,
parsers or accepted vocabulary. Review the exact-head hosted CI before merge.
