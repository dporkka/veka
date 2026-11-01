# Veka 0.3 — executable listening-study packet and pre-registration checklist

**No human speech has been recorded and no participant results have been collected.** This package contains condition assignments, scoring code, audio recording instructions and blank response templates, not an experimental claim.

## Objectives

**Primary hypothesis:** among listeners trained to criterion, contextual omission will reduce *total elapsed time per correctly recovered proposition including all repairs*, without materially increasing semantic errors, relative to explicit Veka. The benchmark is intended to measure pragmatic communication efficiency, not compression ratios alone.

**Secondary hypotheses:** high-priority short-word contrasts and the lexical tone contrast are recognizable in quiet and speech-shaped noise; a tone-free alternative may match or exceed tonal Veka on the composite outcome. These are hypotheses, not predictions validated by human data.

## Listening experiment A: 32 paired semantic items

`data/study_items_v03.json` contains 24 constructed compressible meaning pairs and 8 no-compression controls. The controls appear verbatim in both conditions and ensure that the study does not pretend every message can be compressed. All items are very simple and should **not** be interpreted as a representative sample of natural discourse.

- For each participant, run `python -m veka study-assign --participant P001 --output assignment_P001.csv` to obtain a deterministic, counterbalanced assignment. A participant receives exactly one expression per meaning. Assignments have 16 explicit and 16 compact trials per participant. Consecutive IDs alternate the assignment arm; trial order is independently pseudo-randomized.
- Teach and test the exact required lexical inventory, grammatical roles, and tone rules before the recorded comprehension phase. Record training time and comprehension-to-criterion, separately from timed test performance.
- Prior to each trial, show a neutral context card specifying relevant participants, objects and prior conversation, **without revealing the target answer**. In compact Veka, the intended speaker/listener common ground must be known to both parties. Replace artificial context oracles with genuinely shared dialogue in a later ecological study.
- Have trained human speakers record **each item and condition separately**, at natural comfortable speed, with identical microphones, distances, and repeatable quality controls. `recording_id` in the assignment CSV is a placeholder, **not a generated WAV**. Independent takes must be used for an appropriate test.
- Ask listeners to recover agent, action, patient, recipient, time, negation, and number/unit where present. Use both forced-choice and occasional typed answers, to prevent a test based entirely on answer guessing. Randomize the position of choices and blind the scorer.
- Record elapsed time from utterance onset until a correct or failed interpretation, including listening/replay, clarification questions, and repairs. Set a maximum trial length before recruitment; failed attempts contribute their full time. Capture a confidence score from 0 to 1 after each attempt.
- Use only simulated high-consequence tasks. Do not deploy Veka in actual medical, legal, safety or payment operations.

### Main response CSV

`data/study_trial_template.csv` remains the canonical score input: `participant_id, trial_id, condition, elapsed_ms, repairs, correct, confidence, critical`. Use each manifest `item_id` for `trial_id`. Condition is `explicit` or `compact`. A semantic response is correct only if **all preregistered meaning-critical fields match**.

`python -m veka score collected_trials.csv` reports success rate, correct messages per minute, median attempt duration, mean repairs, critical errors, subjective confidence and Brier score. This tool does not impute missing participants, test hypotheses or calculate inferential confidence intervals. For inferential analyses, preregister paired comparisons with participant-cluster bootstrap; use power analysis after an initial pilot.

## Listening experiment B: ABX phoneme tests

`data/phonology_abx_pairs.json` supplies seven pairs including one tone pair, two high-stakes pronoun contrasts and two weak-coda examples. The `generate_abx_assignments` function produces four randomized trials per pair with exactly two X=A and two X=B. 

- Human talkers should record A, B and X independently; NEVER reuse the same waveform for A and X. Otherwise listeners may identify matching acoustics instead of phoneme identity.
- Normalize presentation loudness but do not distort pitch or flatten lexical tone. Report sampling rate, recording location, microphones, native-language exposure, and playback level.
- Primary ABX score = proportion of correct X=A/B selections per pair, listener, talker and condition. Produce confusion matrices; compare quiet and +5 dB SNR after calibrated pilot recordings. Report effect sizes and uncertainty rather than relying on a single accuracy average.
- Contrast segmental and tonal items separately and collect explicit responses for tone perception, not merely written recognition.

## Suggested preregistered pilot gates

The following are **proposed decision criteria**, not evidence or universal safety standards:

1. Before testing efficiency, require at least 90% accuracy on a held-out, untimed understanding test and demonstrate that listeners understand the contextual omission rule.
2. If an essential agent/negation/number contrast falls below 95% in quiet listening, redesign it or add spoken redundancy and retest. This threshold is a conservative design target, not a statistically certified risk bound.
3. Only claim throughput benefit if the participant-paired *correct messages per minute* improves and the comprehension difference satisfies a **predeclared** non-inferiority margin. Establish that margin and the sample size before looking at outcomes.
4. Report errors in critical items separately, plus all sample exclusions, repairs, participant training times, and tone-language exposure. The current pilot cannot prove population-level superiority over English or any other natural language.

## Consent and privacy

Recruit adults with informed consent; store only pseudonymous IDs in manifests and response CSVs. Keep consent and identifiable recordings in access-controlled storage with explicit retention and withdrawal terms. Participants should understand that the recordings assess an experimental invented language and are not demonstrations of general intelligence or language aptitude.
