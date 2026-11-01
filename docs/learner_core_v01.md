# Veka learner-core audit v0.1 — curricular exposure, not language frequency

**Status:** read-only teaching/research diagnostic. The Veka 0.4 canonical roots,
0.3 grammar, parser semantics, tones, and 708 existing transparent compounds
remain unchanged. This tool does not create new words or assert comprehension.

## Purpose

Veka has 1,025 canonical dictionary headwords, but only **317 atomic roots**.
The remaining **708 registered noun–adjective compounds** are structurally
transparent aliases of the corresponding phrases, with silent hyphens. Their
presence in the dictionary must not be mistaken for 708 additional unrelated
forms a new learner needs to memorize. In particular `ren-sak` is decomposed
into existing roots `ren` + `sak`, not ranked as a 318th primitive root.
This is a structural teaching policy, not proof that every compound is
pragmatically transparent or requires zero learning effort.

## Run

```sh
python3 -m veka learner-core --budget 20
# Use a separate, researcher-curated, strictly parser-accepted Veka corpus:
printf 'sentence\nMi gos.\nTi gos.\n' > /private/canonical-examples.csv
python3 -m veka learner-core --sentences-csv /private/canonical-examples.csv --budget 2
```

Default inputs: the 16 canonical examples from the four-level curriculum
(`data/beginner_lessons_v09.json`) and the 10 progressive examples in
`veka/lessons.py`. The Mandarin and Portuguese translations of the same
ten sentences are **not** independent observed Veka occurrences. Identical
sentences appearing in both sources are counted once.

At this revision there are 26 listed examples but **19 distinct sentences**,
containing **30 distinct primitive roots**. A 20-root selection lexically
covers **14 of 19** example sentences. These are exact corpus statistics, not
claims about general language coverage, learnability or reading speed.

## How the ranking works

- First teaching stage (levels 1–4, followed by the trilingual lessons).
- Then number of *distinct teaching sentences* containing the root.
- Then token repetitions within those sentences, then alphabetical root form.
- A `--budget` of 20 selects the first 20 observed roots (or fewer if the
  supplied examples contain fewer). It does **not** invent replacements,
  mark any root as empirically high-frequency, or optimize a learning curve.
- `coverage.uncovered_examples[].missing_roots` identifies exactly which
  primitive roots block lexical coverage of each teaching sentence.
- `critical_contrasts` lists `mi/ti`, `ne/na`, and `ran/ren` as
  editorial high-consequence **review targets**, with observed lesson counts.
  `na` is absent from the current teaching examples, even though `ne`
  appears. Absence is a curriculum gap, not evidence of listener confusion.

Optional CSV input has **exactly one column**, `sentence`, containing 1–500
distinct canonical sentences, at most 1 MiB. The strict canonical parser
must accept every sentence. Unknown words, proper names not in the canonical
lexicon, experimental grammar, duplicate sentences and nontransparent
compounds fail closed. No response judgments, participant labels or answer
keys are accepted in this unscored input. Supplying a larger text file does
not by itself make the source corpus representative.

## Scientific and design limits

The ranking is conditional on the *existing editorial teaching material*, not
a measured language-frequency distribution. The separate 100-scenario
English-only everyday corpus currently has no approved Veka translations and
is excluded. The printed `natural_language_frequency_measured=false` and
`human_comprehension_validated=false` are intentional.

Do **not** use this ranking alone to adopt international roots, remove
canonical vocabulary, certify safety-critical distinctions or calculate
learning-time savings. A future representative, provenance-checked corpus of
actual communication could improve prioritization, but independent meaning
review and multi-background speaker/listener evaluation remain separate tasks.
If evidence is missing or negative, preserve the canonical language.
