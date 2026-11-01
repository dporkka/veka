# Globasa-informed root review (experimental, Veka v0.13 research tool)

**Status:** Read-only word-selection and learner-reference workflow. No canonical
lexicon, grammar, pronunciation, writing system or parser profile is modified.
This is an implementation of a *review process*, not a vocabulary reform or
proof that Globasa words are better for Veka.

## Why borrow this methodology?

[Globasa's official lexical development methodology](https://www.globasa.net/eng/max/metode-fe-lexiseleti)
starts by asking whether the desired meaning is already expressible with
existing vocabulary and word formation. Only then does it compare donor
languages, settle semantics and screen word forms for confusability.

Veka already has a frozen dictionary with 317 atomic roots and 708 registered
transparent compounds, a 100-concept research queue, evidence intake and
reproducible phonotactic checks. The new `root-review` command joins those
contracts *for one specified concept*, instead of constructing a new
dictionary, inventing language attestations or silently replacing roots.

The Globasa dictionary's [kitabu entry](https://menalari.globasa.net/eng/lexi/kitabu)
is an instructive case: similar loanwords are found in several recipient
languages but may share a borrowing history. **Recipient-language family
coverage must never be presented as independent etymological origin counts.**
Globasa's prescribed donor-language ranking is a design precedent, not an
automatic adoption criterion for Veka.

## Usage

```sh
python3 -m veka root-review C002 --format text
python3 -m veka root-review C002 --format json
python3 -m veka root-review C009 --format text  # no invented candidate
python3 -m veka root-review C002 --format text --lang zh
python3 -m veka root-review C002 --format text --lang pt-BR
python3 -m veka root-review C002 --output /tmp/veka-root-review.json
python3 -m veka international-plan
python3 -m veka lexical-readiness
python3 -m unittest discover -s tests -p 'test_root_review_v01.py' -v
```

The command accepts the existing v0.10 candidate/priorities CSV and v0.7
cross-family evidence CSV through `--candidates`, `--priorities` and
`--evidence`. The separate `--leads` flag defaults to
`data/music_source_screening_v10.csv`, a five-row, source-linked research
screening file. Its research reference `R03` joins canonical research concept
`C002` **only via unique exact candidate spelling** `mu-si-ka` (not by
guessing that the reference IDs are equivalent or that the source words share
a meaning). No source-screening row can count as a verified attestation;
only a separately reviewed `--evidence` record has that ability.

The optional `--lang en|zh|pt-BR` controls the readable word-gloss language.
JSON includes all three curated word-glosses, their actual source languages,
and an explicit English `(en)` fallback when a gloss is not in Veka's existing
teaching list. Word glosses are not verified sentence translations.

The tool validates **the entire input queue, all evidence, and all source
leads**, not merely the selected concept, to prevent malformed records from
being silently ignored. Unknown concepts, duplicate lead languages, unknown
candidate forms, non-HTTPS URLs, unsupported provenance statuses, and purported
independently verified screening leads all fail closed.

A concept card provides:

- Existing canonical root, part of speech, valency, registered compound samples
  and affected compound count; an accepted root already conveys the meaning.
- Experimental candidate and its **separate, not accepted** comparison arm.
  The paired Core/candidate conditions are descriptions, not study results.
- Structural phonotactic status, exact undelimited-surface collisions and
  one-character spelling near-pairs against existing forms and other
  structurally testable candidates. Hyphens are silent in Veka; edit distance
  removes them. This **does not measure acoustic similarity**. Reports distinguish
  registered vocabulary from other unverified candidate forms.
- Source attestations, including language, branch, claimed verification,
  claimed semantic equivalence and reviewer-supplied URLs/notes.
- **Separately labeled unreviewed source-screening leads**, including both
  related loanwords (English, Portuguese, Indonesian, Swahili) and a
  nonmatching Mandarin form. The screened file's five entries still require
  independent human sense, sound and borrowing-path review. An indexed search
  result is not source-page verification.
- Curated word-level learner glosses in English, Mandarin and Brazilian
  Portuguese, with transparent English fallback and no invented translations.
- A mandatory unresolved etymological-independence gate. Even claims of
  attestations from two different language families do not show two
  independently evolved roots or any probability of comprehension.
- The same next research action produced by the existing v0.10
  `international-plan`. It never automatically approves a word.

## Decision sequence before any vocabulary change

1. **Existing expression:** identify current canonical root and any relevant
   transparent compound. Do not add a new primitive merely to duplicate an
   existing compositional meaning.
2. **Meaning:** specify the intended sense, grammatical category, register,
   polysemy and false friends. For example, *doctor* versus *physician*
   requires a conscious semantic decision.
3. **Donor coverage:** independently verify source forms and senses with
   qualified reviewers. Record direct source URLs and borrowed-word origins.
   Language genealogy and loanword origin are different concepts; the current
   evidence CSV **does not contain a reviewed borrowing-chain graph**.
4. **Form:** compare recognizable candidate spellings against Veka phonotactics,
   protected grammatical roots, undelimited compound surfaces and written
   near-pairs. Flag near-pairs for *actual* spoken listening review; do not
   auto-reject or auto-adopt based on text edit distance.
5. **Human tests:** use existing Veka cohort/listening workflows for blinded,
   counterbalanced comparisons of first-sight recognition, delayed retention,
   pronounceability and listening in noise across unrelated language
   backgrounds. Predeclare critical misunderstanding limits and account for
   training, speaking and repair time.
6. **Decision:** maintain the canonical version when data are absent,
   inconclusive, or show unacceptable consequential confusion. A tested
   replacement would require a separate versioned migration, downstream
   teaching updates and explicit adoption approval.

## Relation to the familiar-vocabulary pilot

The separate draft [PR #46](https://github.com/dporkka/veka/pull/46)
proposes a **seven-word experimental vocabulary profile**. This feature does
not import that draft, rebase it, merge it or rename the canonical vocabulary.
Its existing international queue already contains comparable concepts such
as music and school. When the pilot is independently reviewed, its forms can
be represented as research candidates in a separately versioned input queue,
with collisions, compound dependencies and study results audited.

## Evidence boundaries

The default Veka **verified-attestation** and human-trial tables are **empty**,
so the root review contains zero verified source records but now shows five
**unreviewed** music-screening leads. There is no established human learning
benefit, independently reviewed loanword etymology, or license to adopt forms.
Reviewer labels are not independently authenticated; provenance URLs are
untrusted research input, not certified source quality. The word card is
English-first and machine-readable; the existing `beginner`, `lessons`
and `family` commands provide separate English, Mandarin and Portuguese
learning paths. The review's multilingual field is a *curated word gloss*, not
a full dictionary of verified cross-language senses or a translation engine.

Parser passing is not word comprehension, family coverage is not recognition,
and spelling edit distance is not phonetic or noise robustness. This tool
never changes the accepted headwords or makes a release decision.
