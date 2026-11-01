# Veka 0.5 proposal: spoken aesthetics (opt-in)

**Status:** experimental phonetic delivery advice and deterministic text heuristics.
**Compatibility:** Veka 0.3 tonal semantics and Veka 0.4 toneless semantics unchanged.
**Not evidence:** No audio, trained speakers, listener ratings, perception tests, or
comprehension results have been produced. A computed score is **not** a beauty
rating, a measured speaking speed, or a predictor of acoustic confusion.

## Design objective

Give ordinary conversation a fluid, recognizable cadence while minimizing the
total time required to communicate **correctly understood** meaning. Aesthetic
preference is subjective. Favor consistent vowels, simple transitions and
phrased delivery, not indiscriminate deletion of coda consonants.

## Normative pronunciation guidance (proposed)

- Retain the same phonemes as specified in `grammar_v03.md`: /a e i o u/
  without vowel reduction; single-tap /ɾ/ for romanized `r` (still provisional);
  maintain /l/, /s/ vs /z/, and /f/ vs /v/. Avoid inserting consonant clusters.
- Mostly even syllable pacing; natural phrase prominence is allowed but **not**
  new contrastive lexical stress. Use relaxed articulation only where it does
  not erase segmental contrasts. All licensed `n l s k` codas are still pronounced.
- **Tonal default:** Preserve any rising lexical tone (including `pái`,
  `pál`, `lé`, `vén`). Any phrase-final falling movement is secondary
  and must not turn a rising lexical tone into level-tone homophone.
- **Toneless experiment:** Mild phrase-level variation and a gentle final fall
  are allowed. The pilot does not introduce lexical tones. Do not presume that
  this will sound more beautiful or improve comprehension.
- Numbers, negation, quantifiers and scoped logic are high-consequence.
  Pronounce all tokens distinctly; do not elide `ne`, `na`, `ve`, `yu`,
  numeral digits or unit markers. Do not insert pauses that shift scope.
- Veka 0.4 does not define interrogative semantics. The prototype prosody
  command therefore rejects questions instead of inventing question grammar.

These are **recording guidelines**, not generated speech. No IPA-aligned
waveform or human speech is provided by the CLI.

## Opt-in scoring of candidate word forms

Use this for **proposed future words**, not automatic replacement of existing
roots. The tool accepts only legal canonical romanized forms: one permitted
syllable or a hyphenated compound; for example `ma-li`, not `mali`.

```sh
python -m veka aesthetics ma-li ma da dak --profile tonal
python -m veka aesthetics ma-li ma da dak --profile toneless
python -m veka prosody 'Mi pa dak mel.' --profile tonal
python -m veka prosody 'Mi fok mel.' --profile toneless
python -m unittest discover -s tests -v
```

The purely editorial `score_form` index is bounded to 0–100:

```text
35
+ 25 × fraction of open syllables
+ 15 × fraction ending open, /n/ or /l/
+ 12 × fraction beginning with /m n l ɾ j w/
+  8 × ratio of distinct vowel nuclei to syllable count
−  8 × fraction ending /s/ or /k/
− 10 × count of adjacent obstruent-coda + stop-onset boundaries
```

This intentionally favors open syllables and sonorants. These weights are
**arbitrary, not fitted**. The resulting number is useful for exploring
preferences but has no empirical validity.

`rank_candidates` additionally checks the current profile's 1,025 headwords
and designated digits/grammar markers. A new form is marked ineligible if it
already exists, is within one **orthographic edit** of any headword, is
within one edit of a critical marker/digit, **or contains a silent hyphen**
that requires a separate spoken-compound segmentation review. This is a **conservative text-only
screen**, not proof that an eligible form is easy to hear. It may reject useful
forms or accept acoustically confusable ones; use actual listener tests before
adopting any vocabulary. Ranking never modifies lexicon files.

## Spoken test design before a normative change

1. Create four conditions: tonal baseline, tonal guided cadence, toneless
   baseline, toneless guided cadence; teach lexical profiles separately and
   counterbalance speaker/condition exposure.
2. Collect independent human recordings from multiple speakers and accents at
   comparable loudness, with naturally paced and matched-rate versions.
3. Preregister primary outcomes: correctness per elapsed interaction time,
   critical-token/meaning error rate, and repair/repetition frequency.
   Independently collect blinded 1–7 pleasantness ratings and naturalness
   ratings; do not combine ratings with recognition into one opaque metric.
4. Include sentences with logical nesting, pronouns, digits, and negation as
   well as social conversation; compare clear and masked speech.
5. Report uncertainty, individual differences, learning burden, and subgroup
   contrasts. Do not replace canonical tonal Veka or rename headwords based
   solely on the text index or a small convenience sample.

## Reproducible blinded listening pilot (12 constructed meanings)

```sh
python -m veka spoken-study-assign \
  --participant S0001 --profile tonal --arm 0 \
  --output S0001-participant.csv --researcher-key S0001-researcher.csv
python -m veka spoken-study-assign \
  --participant S0002 --profile tonal --arm 1 \
  --output S0002-participant.csv --researcher-key S0002-researcher.csv
```

The `data/spoken_aesthetics_items_v05.json` pilot has six lexical-contrast
items and six controls, including one number, one scope expression, one
quantifier and one future marker. These are deliberately tiny constructed
materials, not a representative sample of fluent conversation. All items
must pass strict parsing in **both** lexical profiles. The CLI generates
12 assignments per participant: six baseline and six guided. Arms 0 and 1
swap delivery for every meaning, so no participant sees the same meaning
twice. Participants must be assigned to **one** lexical profile; do not
teach the other in their session. Allocate participants in balanced
profile × arm cohorts **before** recruitment/outcome review.

The participant CSV contains only opaque stimulus IDs and blank fields for
pleasantness (1 = very unpleasant, 7 = very pleasant), naturalness
(1 = very unnatural, 7 = very natural), comprehension response, elapsed
time, and repairs. The separate researcher CSV holds stimulus meaning,
conditions, written form, critical token flag and **placeholder** WAV
filenames. No recordings are created, and its `audio_recorded=false`
flag is literal. Keep the researcher key access-restricted and separate
from participant screens; filenames do not encode condition or profile.
Generate actual recordings from trained consenting human speakers,
using independent takes, fixed microphone position and calibrated level.
Verify each recording's condition and lexical form before testing.

**Preregister before testing:** a primary within-profile contrast of
guided vs baseline naturalness/pleasantness; a separate accuracy and
correct-meaning-time non-inferiority analysis with fixed margins, pilot
sample size and stopping/exclusion criteria. Use participants as clustering
units and randomize speaker order. High-stakes tokens must be reported
separately. Never use an unblinded aesthetic preference as evidence that
numbers, negation or scope are reliably audible. A small pilot can inform
recording instructions but cannot establish population-level preference.

Security/ethics: use pseudonymous IDs, obtain consent, protect raw
recordings, define retention and withdrawal procedures, and do not
record actual high-consequence tasks.

## Compatibility and limitations

- `parse`, `logic`, `profile`, `convert`, `number`, `lookup` and the
  lexicon are not changed. `aesthetics` and `prosody` are additive CLI verbs.
- `prosody` accepts a strictly parseable declarative Veka clause and returns
  delivery guidance **without changing the supplied text**; it does not
  synthesize audio. Unsupported and ambiguous constructions are rejected.
- Compound spelling includes hyphens; scores do not model syllable durations,
  cross-word coarticulation, breath groups, stress/accent variants or listener
  preferences. Rhythmic suggestions remain non-binding until experimentally
  tested.
