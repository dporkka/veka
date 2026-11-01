# Veka v0.10 international-root research plan (NONCANONICAL)

**Status:** Hypothetical word candidates and editorial research triage only.
The published 0.4 tonal lexicon (317 primitive roots, 708 transparent
compounds), 0.3 grammar, 0.5/0.6 opt-in extensions, parser and existing
canonical contract are unchanged. This is **not** an accepted 'international'
speech or parser profile, and it is **not** evidence of human learning gains.

## Use

```sh
python3 -m veka international-plan
python3 -m veka international-plan --output /tmp/veka-international-plan.json
python3 -m veka international-audit --candidates data/international_candidates_v10.csv
python3 -m veka lexical-readiness --candidates data/international_candidates_v10.csv
python3 -m unittest discover -s tests -q
```

- `data/international_candidates_v10.csv`: same 100 concept IDs and canonical
  root/gloss mappings as v0.4; **24 unverified drafts, 76 unproposed**.
  Sixteen new proposals extend the original eight without editing those
  original research files. Most proposals are European-leaning and require
  genealogically diverse attestation and independent meaning checks.
- `data/international_priorities_v10.csv`: one explicitly **subjective**
  editorial exposure tier (1-5) and review reason for each concept. These
  are not measured spoken frequencies or recognition rates.
- `veka/international_plan.py`: deterministic, read-only prioritization using
  the existing `lexical_readiness` structural and evidence contracts.
  Ranks items by assumed exposure, extra syllable cost and number of
  canonical compounds affected; these are *study-planning* weights, not a
  language-quality, utility or adoption score.
- `tests/test_international_plan_v10.py`: schema, strict 100-concept mapping,
  structural review, collision safety, CLI, and preservation tests.

The CLI reports `rejected_drafts` and `spoken_surface_collisions` for
candidate words that collapse to the same undelimited letter sequence as a
canonical lexeme or another proposed form. The latter is a **text-only**
screen for possibly identical spoken word sequences, not measured acoustic
confusion; unresolved overlaps require repair. Every draft separately
requires false-friend, loan provenance, sense-equivalence, segmentation and
pronunciation review. Any rejected form is still noncanonical and must be
repaired before a study packet is built.

Ten initial proposals were **excluded** because they contained protected
grammatical/pronoun syllables (e.g. `a-ni-mal` contains `ni`).
Do not bypass reserved-syllable rules merely to preserve recognizable
spelling. Some other proposed forms deliberately lose parts of source
spellings. Those adaptations may destroy recognition and must be rejected
when real testing finds no benefit.

## Decisions and migration gate

1. Check meanings with Concepticon/CLICS and donor words using attributable,
   license-compatible sources. Count *genealogical families*, not languages
   in the same family, as independent provenance. Note when a loan originates
   in one family but spreads across many; attestation is not recognition.
2. Preregister comparison of canonical roots vs matched draft forms using
   speakers and learners from diverse families. Separate visual first-sight
   recognition from pronunciation, noisy speech recognition, delayed retention,
   learning time, and real phrase comprehension. Record confusion, repairs,
   and critical semantic errors. Do not simulate participants or recordings.
3. Study the tradeoff of 1-syllable current roots vs longer drafts and any
   root's existing compound dependencies. Beware that some drafts conflate
   senses (e.g. Portuguese `data` means calendar date).
4. Recommend a versioned canonical migration **only** if valid source review,
   preregistered measured benefit across groups and predeclared critical-error
   noninferiority succeed. Inconclusive means keep the existing form. Migrate
   old texts and all affected compounds explicitly; preserve semantic IDs
   when changing any surface spelling. Never silently accept synonyms.
5. Keep core grammar operators, number words, and critical pronouns stable
   unless an independent higher-bar experiment justifies their replacement.

The 100-concept dataset is an inherited **research sample**, not a
frequency-representative list or all 317 roots. Internationalisms for new
concepts such as taxi/hotel/robot are tracked in the separate
`cognate_candidates_v07.csv` addition pilot, not silently added here.

**Limitations:** No cross-family forms were independently verified, no
human trials have been collected, and no superiority to current Veka,
Interlingua or another language has been demonstrated. Realization of
word-specific pronunciation, semantic sense, and source/license review is
intentionally left to qualified human reviewers.
