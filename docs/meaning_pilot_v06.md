# Veka 0.6 — blinded meaning-recovery pilot packet

**Research preparation only (November 2026). No human audio, responses, or
communication improvements are demonstrated by this software.**

The earlier `study-assign` CLI emitted **researcher assignments**, including
the correct meaning, conditions and target utterances. That output must **not**
be distributed as a participant sheet: it would compromise blinding.

`meaning-plan` is a new, separately named opt-in command that turns the
existing 32 paired items (`data/study_items_v03.json`) into **three distinct**
CSV outputs. Existing `study-assign` behavior is preserved for compatibility.

## Prepare materials (example pseudonym, NO participant enrolled)

```sh
mkdir -p /tmp/veka-meaning-P001
python -m veka meaning-plan \
  --participant P001 --arm 0 \
  --participant-csv /tmp/veka-meaning-P001/participant.csv \
  --key-csv /tmp/veka-meaning-P001/researcher.csv \
  --recording-csv /tmp/veka-meaning-P001/recordings.csv
```

All three outputs are private file modes on POSIX machines; the latter two
are **researcher-only** and must never be distributed to participants.
No WAV files are produced. Clip identifiers are opaque, content-fingerprinted
by item, selected condition, text and context, and stable across participant
IDs and trial-order seeds. Reuse audio banks only for the **same frozen
stimulus**. Confirm truly independent human recordings, playback calibration,
consent, and blinding before allowing a session to begin.

Participant CSV fields: `trial_id`, `audio_id`, `context_json`,
`response_text`, `elapsed_ms`, `repairs`. They contain **no target
meaning, reference translation, condition, item ID, or correct answer**.
Context is deliberately visible: the compact register requires mutually
established discourse referents. A researcher must review context cards to
ensure no target action, negation, or response is accidentally revealed.

Researcher key includes the expected meaning, selected utterance,
condition, category, critical flag and item ID. The recording manifest
includes the Veka text to be read by a **consenting trained human speaker**.
Record actual human responses, repair requests and timing in restricted
research storage; do not commit any such output to this repository.

## Experiment design and scoring limitations

- Explicitly randomize `arm=0` or `arm=1` at enrollment, stratified by
  language background; do **not** infer arm from participant identifiers.
  Each participant sees an item at most once; opposite arms reverse which
  form is shown for every meaning.
- These 32 short constructed items are **not representative** of natural
  conversations. The eight uncompressible controls remain in the packet.
- This generator verifies that both variants produce equivalent **parser
  role structures** under their declared contexts. It cannot show that
  humans understand the same thing, that the context is realistic, or that
  a translated answer is semantically equivalent.
- Pre-register training criterion, sample-size rationale, scoring rubric,
  critical-mistake margin, response deadline, repairs, exclusions, speaker
  and listener language groups and quiet/noise conditions before gathering
  data. Blind independent human raters to the condition and adjudicate
  meaning fields according to the approved rubric.
- The existing `python -m veka score` reports **descriptive statistics** on
  complete *manually adjudicated* rows using the
  `data/study_trial_template.csv` schema. The new participant sheet is
  **not automatically score-compatible**; it requires an audited manual
  coding/export step using the researcher key. No automatic translation or
  human-authenticity check is claimed.
- The purpose is measuring total **correctly recovered propositions per
  minute**, including unsuccessful attempt time and repair overhead, not
  raw syllables per minute. The ABX `listening-plan` separately measures
  phonetic discrimination, not semantic comprehension.

**Go/no-go:** freeze the protocol and independently collect actual consenting
participants and calibrated recordings; only then estimate uncertainty
across participants/items/speakers. Keep canonical Veka unchanged if evidence
is inadequate or inconclusive.
