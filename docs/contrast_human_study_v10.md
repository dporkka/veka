# Veka contrast review and human-study readiness (v0.10)

**Status:** Proposed editorial workflow and preregistration checklist, not
completed human research. Veka's canonical grammar, word forms, parser,
tonal profile, and research-only profiles are unchanged.

## First gate — independent editorial review

Prior to using the six grammar contrasts as public-facing authoritative
teaching material, recruit **two independently working qualified reviewers
per language** (English, Mandarin, Brazilian Portuguese). Confirm out of
band that they are different people with appropriate bilingual language
skills, and that neither sees the other's answers before submitting.

Generate separate sheets (store privately, not in Git):

```sh
python3 -m veka contrast-review-export --lang en --reviewer E01 --output /private/en-a.csv
python3 -m veka contrast-review-export --lang en --reviewer E02 --output /private/en-b.csv
python3 -m veka contrast-review-check --lang en --first /private/en-a.csv --second /private/en-b.csv
# Repeat, with different reviewers, for --lang zh and --lang pt-BR
```

Each export contains **12 rows** (A and B for each of six existing grammar
contrasts). Reviewers **must not edit** the source columns
`language,item_id,variant,feature,sentence,translation,focus` or their
pseudonymous `reviewer_id`. Each reviewer individually fills in:

- `semantic_fidelity`: `accept`, `revise`, or `unsure`; check the
  source utterance's intended meaning, negation, quantifier, time and roles.
- `naturalness`: same values; check that the localized interpretation is
  idiomatic while retaining the intended meaning.
- `contrast_clarity`: same values; check whether the *change* between A
  and B is explained intelligibly to a first-time learner.
- `notes`: required for any `revise` or `unsure`, otherwise optional.

A blank judgment is **pending**, not a pass. The audit fails closed on missing
or extra rows, schema drift, changed source/translation/focus strings, duplicate
keys, malformed CSV, unlicensed values, or unexplained concerns. Distinct
pseudonyms are enforced, but do **not** establish true reviewer independence.
The audit can return `ready_for_manual_editorial_signoff=true` **only**
when all six contrasts have two complete all-`accept` assessments. That
state remains **a request for manual sign-off**, never a translation
certification, measured learner outcome, or automatic merge gate.

Review item disagreement requires a human adjudicator to edit the teaching
source, then generate *new* sheets and rerun reviews for the revised version.
Do not silently normalize or overwrite the original judgments. Store sheet
provenance, reviewer qualifications, dated approvals and versioned consent
out of band. Obtain permission for any externally authored translations.

## Second gate — actual human comprehension (not yet executed)

**Keep the six published drills as training illustrations, not blinded
assessment items.** Exposing both Veka and translated answers makes any
recognition score on the same phrases uninterpretable. Before enrollment:

1. Two independent editors author a **held-out** set of new, unseen
   canonical sentences and minimal pairs with the same six structural
   targets. Freeze all prompts, intended semantics, distractors, mappings,
   and response acceptability rubrics. Strict parsing verifies syntax and
   intended changed parser fields only; humans must independently establish
   sense/pragmatics. Never automatically infer full translations from parse.
2. Preregister learning budget, recruitment, consent, prior exposure,
   exclusion rules, response timing, missing-data handling, randomization,
   scoring adjudication, and sample size/power assumptions. No claim about
   statistical significance is permitted without real observations.
3. Recruit independently identified English, Mandarin, and Brazilian
   Portuguese dominant-language **strata**, record actual language
   history/multilingualism, and include further language families before
   claiming global applicability. Brazilian Portuguese and English share
   historical language-family ancestry: do not interpret 3 strata as 3
   independent language families.
4. Allocate participants to fixed lesson and held-out test lists with an
   independently generated seed. Balance form order, lesson exposure,
   sentence concepts, distractor labels, and speech modality across
   participant IDs. Keep researcher answer keys out of participant
   manifests and ensure the participant UI cannot access them.
5. Prefer a small pilot for content quality first, then a preregistered
   confirmatory study. Record response correctness by blinded bilingual
   adjudicators, time to correct recovery **including clarification and
   repair**, and high-consequence role/negation/quantifier errors.
6. Report per-stratum accuracy, interval estimates, retention after a
   prespecified delay, time-to-criterion, repairs, attrition and
   misinterpretation severity. Do not average away a severe subgroup
   regression with better results from an easier cohort.

**No participant manifests, consent responses, recordings or human outcomes
are included in this PR.** The reviewed teaching drills are not a blinded
human-comprehension benchmark.

## Third gate — tonal versus toneless listening

Use Veka's **existing** blinded v0.6 listening/ABX pipeline and v0.9
recording preflight rather than making new incompatible audio formats.

```sh
python3 -m veka listening-plan --help
python3 -m veka listening-preflight --help
python3 -m veka listening-score --help
```

Preregister separately for `tonal` and experimental `toneless` profiles.
Ensure the sound items actually differ by profile: **most examples in the
six reading contrasts contain no rising-tone roots**, so simply switching
their label does *not* test tone. Select licensed high-risk root minimal pairs,
including pronouns, negation, numbers, and rising-tone contrasts, and verify
all text/phonology identities with the respective profile and human review.

Arrange independently performed real WAV recordings from several talkers,
prosodic consistency checks, quiet/noise conditions, and speaker/listener
randomization. Use preflight as a **format/quality screen**: it cannot prove
speaker identity, pronunciation correctness, true SNR, or listener
comprehension. Only score after recordings and real complete responses exist.
Record paired confusion, accent sensitivity, repairs and critical errors.
Do not prefer the toneless profile based on a symbolic near-pair count.

## Final adoption decisions

New international roots are tracked in
`docs/international_root_plan_v10.md`; they are not part of this editorial
gate. Keep all replacement candidates **noncanonical** until qualified
source/sense and phonological review, independent human recognition and
retention results, predeclared critical-error noninferiority, and a versioned
migration for existing 317 roots and 708 compounds. Inconclusive means
preserve canonical Veka.

No experiment, cross-language superiority claim or reviewer identity is
certified by this repository's machine tests.
