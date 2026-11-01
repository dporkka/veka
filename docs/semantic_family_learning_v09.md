# Veka v0.9 research learning aids: structural families and editorial readings

**Status:** opt-in tooling, not a canonical language version. The canonical 0.4
lexicon, 0.3 grammar, and all frozen 0.6 compatibility sources are unchanged.
This change has **no human recognition, pronunciation, or comprehension results**.

## Motivation

Interlingua demonstrates the value of recognizable word families and readable
ordinary expressions. Veka cannot copy historic stem alternations, uncontrolled
semantic extension, or European-first loanword selection while claiming to
optimize cross-language comprehension. Instead it should make its *existing*
structural relations inspectable and provide explicitly limited reading aids.

## Commands

```sh
python -m veka family dak
python -m veka family kun --limit 5 --format json
python -m veka family ren-sak --no-cues
python -m veka family fok --profile toneless
python -m veka beginner 'Mi pa dak mel.' --families --readings
python -m veka beginner 'Mi sen kun.' --families --no-cues --format json
python -m unittest discover -s tests -v
```

The family tool derives its records from the canonical lexicon's already
recorded noun-head/adjective-modifier relationships and the separate
v0.5 typed event operators. A **compound** is a compositional surface
alias with a silent hyphen, **not a new semantic atom**. A **derivative** is
v0.5 research syntax, **not canonical vocabulary**; the strict parser
continues to reject it. Its role/argument mapping comes from the existing
`extended.derive` implementation, which enforces verb valency. The tool
does not create new compounds or suffixes.

`core:<form>` lexeme IDs identify existing roots in the *frozen canonical
lexicon* even when showing a toneless profile spelling. These IDs are
**not externally validated sense IDs**. A gloss can be broader than a
dictionary sense; compounds, related roots and derived forms are not
necessarily synonyms. International associations use the preexisting
v0.4 candidate queue; they remain unverified, noncanonical and hidden by
`--no-cues`.

The `beginner --families` mode annotates content words while preserving
the original parsed sentence and strict validation. `--readings` looks up
only the small, literal examples in `data/editorial_readings_v09.json`.
Available editorial languages are English and Brazilian Portuguese.
Unlisted or semantically unsupported sentences receive **no translation**.
Editor-written examples have not been validated by native speakers or
language-learning trials; these are guidance, not a translation engine.

## Validation and adoption criteria

Technical tests must prove:

1. All 1,025 canonical entries and their frozen sources are unchanged.
2. No research derivative, loan, or novel compound becomes accepted by
   `parse(..., strict=True)`.
3. Subject, object, tense, quantification and negation remain the same when
   the display enhancements are toggled.
4. Foreign-profile aliases preserve canonical lexical identities.
5. A word with no available editorial example yields `null`, not a guess.

To validate human benefit, preregister a randomized experiment comparing:
(A) default Veka glosses; (B) Veka with word-family explanations; and
(C) Veka with family explanations and international associations. Equalize
training time and concept coverage. Evaluate *held-out* reading and listening
items, immediate semantic identification, delayed retention, error-repair time
and critical negation/pronoun/quantity misunderstandings. Separate English,
Romance, and unrelated language-family cohorts rather than counting
closely related languages as independent evidence. Use actual participants,
independent audio, anonymized answers, and independent adjudication.

The existing `international-manifest`, `cognate-*` and `global-score`
tools can provide research infrastructure, but they do **not** currently
evaluate this three-condition teaching comparison. No superiority claim
or canonical word replacement is justified until real observed results
establish both improvement and noninferior critical-error performance.
