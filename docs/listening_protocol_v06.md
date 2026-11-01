# Veka 0.6 — proposed human listening pilot (no observations collected)

This is a **study design**, not a completed experiment. It must not be used to claim performance benefits for Veka. Input stimuli: `data/discourse_stimuli_v06.json`. The seven entries are *examples*, not a powered or balanced experiment.

## Preparation
1. Recruit at least two native/fluent trained Veka producers only **after** the language has a documented pronunciation training procedure. If fluent speakers do not yet exist, label audio as *novice-produced* and avoid claiming native performance.
2. Record each utterance independently in quiet conditions with standardized distance/gain. Record at least two separate takes by each speaker. Do not fabricate or synthesize purported human recordings.
3. Prepare matched controls, randomized trials, and unrelated fillers; counterbalance speaker, condition, and presentation order. Avoid placing a target right next to its contrast, which invites simple memory strategies.
4. Recruit listeners with diverse first-language backgrounds. Preregister sample sizes and primary hypotheses. Pilot enough to estimate variance before powering a confirmatory study.
5. Train listeners on syntax, grammar markers and vocabulary **without exposing the answers** to evaluation items.

## Endpoint definitions
- Primary: correctly recovered propositions per minute over speaking, listening and clarification time, with explicit marking of critical reversal mistakes and misunderstandings.
- Secondary: interpretation accuracy for focus, location restricted quantifiers, before/after temporal ordering, word recognition, error repair count, response latency, and learner training duration.
- Contrast Veka marked/control conditions and tonal/toneless phonological profiles *separately*. Do not equate lower syllable count with better efficiency.
- Include a no-context condition and quiet/noisy sound presentation. Record participant IDs and language backgrounds in consented pseudonymous form.
- Blind coders to hypotheses when possible; define a coding rubric and double-code a subset for inter-rater reliability.

## Current pilot items and cost
`data/discourse_stimuli_v06.json` has seven mechanically validated pairs for the grammar's topic, focus, quantifier-domain and temporal markers. This dataset is *not randomized*, does not contain audio or participant responses, and is not sufficient for statistical inference.

In these deliberately chosen examples, marking increases syllable counts for the topic/focus/domain pairs, while the two temporal forms are equal length to their before/after contrasts. These raw counts are *structural description*, not observed throughput or semantic recognition rates.

## Go/no-go criteria
Before recording, declare an allowable critical-error rate and a practical minimum gain in correct meanings/minute against controls. If any manipulation raises critical errors or increases total communication time, revise or remove it regardless of parser correctness. More tests in Python cannot replace actual speaker/listener evidence.

## Separate Veka 0.6 phonetic ABX protocol

The [blinded ABX listening pilot](abx_protocol_v06.md) independently tests root-form discrimination, uses opaque audio IDs and fails closed on missing recordings. It does **not** measure semantic comprehension or the grammar-specific dialogue hypotheses in this document. The two protocols must not have their endpoints conflated. Neither has human results.
