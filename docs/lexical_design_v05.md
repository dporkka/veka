# Veka 0.5 — lexical risk screening (research-only)

**Status:** executable structural screening, not a phonetic model, a lexical frequency corpus, a listening result, or a change to standard Veka. This builds on the canonical 0.3 grammar and v0.4 international-word pilot. **All 1,025 dictionary entries remain unchanged.**

## Objective and trust boundary

Veka seeks low *total time to correct communication*, including teaching, listener uncertainty, clarification, and repairs. This audit identifies *hypotheses worth testing*, not the chance a listener confuses two sounds. No human speech has been measured. Existing word forms and the parser remain canonical; candidate substitutions are **never** automatically adopted, converted, or added to the lexicon.

The old audit counts every one-feature root pair equally. The new audit makes editorial priorities visible and produces a ranked *symbolic* warning list, including functional markers and digits. Its 50 non-default priorities in `data/lexical_priors_v05.csv` are provisional and have no empirical source.

## Reproduce

From the root of the repository (Python 3.10+, standard library only):

```sh
python -m unittest discover -s tests -v
python -m veka lexical-risk --top 15 --target mi --target ne --target ran
python -m veka lexical-risk --profile toneless --top 15 --target mi --target ne
python -m veka lexical-risk --priorities data/lexical_priors_v05.csv \
  --target mi --candidates 5 --output /tmp/veka-v05-research.json
```

Do not pass these proposed substitutions to the standard `parse` command: they are **not** words of canonical Veka. Do not pool two independently ranked proposals without another global collision and near-pair audit.

## Transparent provisional ranking

Each valid monosyllabic root is represented by onset, nucleus, coda and a rising-tone bit, as defined by `_syllable_info`. The symbolic distance between forms is

`D = 1.35*[onset different] + 1.75*[nucleus different] + 0.80*[coda different] + 0.60*[tone different]`.

The assumed `exposure` and `consequence` scores are integers 1–10; the product gives each listed root a priority. Unlisted roots default to 1. For a pair `a, b`, a nonnegative structural screening penalty is

`P(a,b) = sqrt(weight[a] * weight[b]) * max(0, 1 - D(a,b)/2.75)^2`.

These coefficients are **arbitrary design hypotheses**. Notably, the model (1) treats each onset substitution as equally different, (2) does not account for syllable-position, assimilation, coarticulation, accents, word frequency, cross-talk, attention, or actual acoustic spectra, and (3) cannot predict confusion probabilities or communication time. A high score is a *test-priority flag*, not a claim that words are unsafe.

Replacement candidates are all **unused level-tone legal monosyllables** excluding both occupied forms and level-tone spellings of occupied rising-tone roots. They inherit the target root's assumed priority, keep all other forms fixed, and are ranked by decreasing change in that target's local pair-penalty, with a small *unmeasured* proxy penalty for codas, diphthongs and missing onsets. No algorithm is authorized to modify core vocabulary, morphology, compounds, or experimental Interlingua candidates.

The change in a target's local structural penalty is **not** equivalent to reducing global communicative cost: alternative candidates may be harder to pronounce, learn, distinguish in context, or relate to existing compounds. Candidate lists for two different targets are independent and may conflict if applied together.

## Compound-vs-phrase segmentation

The dictionary contains **708** transparent noun-adjective compounds. The current specification says the hyphen does not create an audible pause. Consequently, `ren-sak` (lexical 'expert') and `ren sak` ('knowledgeable person') have the same symbolic spoken token sequence. This audit reports these *surface equivalents*, not 708 proven semantic mistakes: a transparent compound and its corresponding descriptive phrase can have almost the same intended meaning.

**Design requirement before expanding productive morphology:** explicitly choose either:

1. **Semantic alias:** spoken compounds and the corresponding noun-adjective phrases have equivalent compositional semantics. Treat the hyphen as an orthographic/lexicographic convention, not an information-bearing sound.
2. **Lexicalized distinction:** if a compound truly has a different meaning, provide a perceptible word boundary or morphology, and test it in natural speech.

Do not add a marker to all 708 compounds without measurement; extra syllables may be worse than accepting transparent aliases.

## Human falsification protocol

1. **Pre-register criteria** before collecting data. State target user groups, independent held-out items, sample-size rationale and a critical-error noninferiority margin. Use the protocol in `docs/listening_protocol_v03.md`; it does not currently contain human observations.
2. **Separate acoustic recognition from language learning.** Use independently recorded A/B/X tokens from multiple speakers, including `mi/ni`, `mi/ti`, `ne/no`, `ran/ren`, and other top near-pairs. Balance noise and quiet conditions; measure by speaker, listener, language background, and contrast. Do not reuse a recording for A and X.
3. **Test proposals in complete language utterances**, not just isolated words. Independently train groups to the canonical forms or an explicitly isolated *candidate profile*. Collect time to teaching criterion, recall, communicative accuracy, repairs, utterance durations and confidence. Blind scorers to condition when possible.
4. **Evaluate actual discourse segmentation** with corpus-driven novel noun-adjective phrases, established compound meanings, unrelated distractors and contexts with multiple candidate referents.
5. **Compare correct-message throughput**, not orthographic edit distance, syllable count or accuracy on selected phrases alone. Report uncertainty, participant/item effects and subgroup error patterns, including all null and adverse findings.

When there is no convincing advantage under preregistered criteria, **do nothing**: preserve the canonical forms. New candidate forms should require a versioned change and a migration plan, especially for roots referenced in established compounds.

## Boundaries

- `canonical_lexicon_modified = false`, `acoustically_validated = false`, `frequency_measured = false`, and `human_participants = 0` are intentional.
- The tool does not synthesize human recordings, invent data, choose future canonical vocabulary or calculate validated acoustic/confusion probabilities.
- The stable international-word trial and its evidence files are independent; neither a structural improvement nor an international resemblance establishes multilingual recognition.
- Future learning: replace assumed priors with *documented, licensed, representative* spoken usage estimates and replace symbolic distance heuristics with preregistered human confusion matrices.
