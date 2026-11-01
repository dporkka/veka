# Veka 0.7 — Global comprehension research layer

**Status:** implementable, machine-tested data contract; **not a new canonical language release**.
No verified donor attestations, audio, participants, or human comprehension observations ship with this layer. Existing Veka 0.3/0.4/0.5/0.6 parsers, tonal profiles, 317 primitive roots and 708 compounds are unchanged.

## Objective

Minimize total time to **correctly understood meaning**, not mere word length or the number of languages displaying a similar spelling. Use a cross-family audit to propose *hypotheses* and observed, preregistered comprehension trials to decide whether international forms outperform familiarizable core roots. An ancestor language or shared borrowing alone is not proof of universal recognizability.

This layer reuses the eight candidate forms in `data/international_candidates_v04.csv`, and the existing international manifest command; it **never adds** synonyms to `data/lexicon.csv`, interprets draft words as canonical, or changes production grammar.

## Commands

Run in a clean Veka repository checkout:

```sh
python3 -m unittest discover -s tests -v
python3 -m veka global-audit
python3 -m veka global-audit --evidence data/global_evidence_v07.csv --output global_review.json
python3 -m veka international-manifest --participant P001 --output /secure/p001.csv --answer-key /secure/p001_key.csv
python3 -m veka global-score --trials data/global_trials_v07.csv --output descriptive_results.json
```

The `--candidates` option on both commands selects an alternate experimental queue with the existing Veka 0.4 candidate schema, **not** an alternate canonical vocabulary. Output is descriptive JSON. `global-audit` reports zero recognized participants and disallows adoption even with many attested languages. `global-score` reports `observed=false` on the header-only template, not a fabricated zero-percent recognition estimate.

## Evidence intake: `data/global_evidence_v07.csv`

Each CSV row represents a single candidate concept and a specific language:

| Column | Required interpretation |
| --- | --- |
| `concept_id`, `candidate_form` | Must exactly match a structurally valid Veka 0.4 candidate |
| `language` | Specific language variety, not a national population |
| `language_family`, `language_branch` | Reviewed genealogical labels; family is the primary independent coverage unit |
| `attested_form` | The donor word as documented, *not* the proposed Veka pronunciation |
| `source_url` | Inspectable `https://` or `http://` source when verified |
| `semantic_reviewer` | Named or pseudonymous person who checked sense equivalence |
| `attestation_verified` | `yes` or `no` |
| `semantic_equivalent` | `yes`, `no`, or `unknown`; verified items require an explicit decision |
| `notes` | Suggested: transliteration, exact sense, register, pronunciation, borrowing history and license |

A claimed match counts toward coverage **only** when `attestation_verified=yes`, `semantic_equivalent=yes`, an inspectable source URL is supplied, and a reviewer is recorded. These are **entered human assertions**; the software cannot inspect a URL, establish borrowing provenance, certify lexical licensing, or prove that a person understands the term.

Several Indo-European languages count as **one** genealogical family, even when their branches differ. Families are never treated as population-weighted probabilities. Duplicate concept-language records, unknown candidates and inconsistent schemas fail closed. A non-cognate loan from an unrelated family is still a *borrowed term*; do not label independently attested loanwords as genetically related roots.

Start with the 100-concept research queue, expanding only after recording provenance for languages across diverse groups. Suggested sampling strata: Romance, Germanic, Indo-Aryan, Sinitic, Semitic, Bantu, Austronesian, Austroasiatic, Dravidian, Turkic and representative indigenous American languages. These strata overlap genealogical families; **do not** treat them as an exhaustive or statistically representative sample of humanity.

Useful documented datasets include:
- World Loanword Database: https://wold.clld.org/
- Concepticon: https://concepticon.clld.org/
- Lexibank: https://lexibank.clld.org/
- PHOIBLE: https://phoible.org/
- CLICS: https://clics.clld.org/

Check each upstream dataset's attribution and license before distributing derived text or copying word lists. Do not scrape or reproduce data without permission.

## Observed human comprehension: `data/global_trials_v07.csv`

| Column | Interpretation |
| --- | --- |
| `participant_id` | Pseudonymous stable identifier |
| `language_background_family` | Predeclared stratum for the participant, not an inferred identity |
| `concept_id` | One of the structurally valid candidate concepts |
| `condition` | `core` or `candidate` |
| `correct` | Expert-adjudicated semantic accuracy: `1` or `0` |
| `elapsed_ms` | Positive measured duration for comprehension response |
| `repair_ms` | Nonnegative additional measured clarification/repair duration |
| `critical_error` | `1` for a consequential misinterpretation; implies `correct=0` |

Forbid repeated presentation of the same concept to one participant in the scoring dataset (including under a different condition); the scorer rejects it. Assign one consistent family per participant. Blinded, independently produced speech recordings, condition randomization, trial order balancing, counterbalancing, training exposure and the definition of a "critical" error must be separately enforced by the study operator. The existing `international-manifest` command can create blinded recognition packets and answer keys, but it is **not** a complete speech study or automated trial logger.

The scorer reports:
- Correct answers and observed proportion correct by condition.
- Total observed response + repair time and correct meanings per minute.
- Critical error counts.
- Per-family descriptive statistics and missing comparator coverage.
- Per-concept descriptive statistics and family-level comparator presence (not inferential rankings).

It deliberately does **not** estimate confidence intervals, adjust for unequal concept mixes, establish causation, prove language-family representativeness or produce a winner. Pooled averages can hide underperforming cohorts: inspect both sides for each predeclared group, concept, speaker, and test environment. Compare real **speech** separately from first-sight **reading**, and separate no-training familiarity from post-training memory.

Store consent forms, raw participant identities, audio and answer keys outside the public repository. Do not commit real participant-level data, recordings, private details or research consent forms to this repository.

## Human pilot and decision gate

1. Preregister precise meanings, strata, primary endpoint, critical-error threshold, recruitment exclusions, and an analysis plan. Assign a pilot large enough to estimate variance, then calculate a suitable confirmatory sample size; a fixed group-size guess is not evidence of adequate power.
2. Have speakers across diverse language backgrounds try candidate forms and current Veka core words; separately record multi-talker, independently produced ABX pronunciation stimuli with quiet/noisy listening conditions. Existing Veka 0.6 listening tools can help, but cannot substitute for human audio or annotations.
3. Randomize candidate versus core exposure within a controlled design; prevent any participant seeing the same concept in both forms before initial testing. Blind answer adjudicators to the hypothesis where possible.
4. Evaluate unfamiliar, realistic dialogues, comprehension errors, reaction time, delayed learning, speech production, repairs and critical negation/number/reference mistakes. Disaggregate by language background and speaker.
5. Only propose a **versioned, reviewed** canonical migration if verified provenance, practical cross-group gains in total correct-message throughput and predeclared critical-error noninferiority gates are all supported by measured evidence. No automatic promotion tool is authorized.

## Other language-family ideas — compatibility policy

- **Sino-Tibetan/Austronesian:** retain short particle grammar and compositional compounds. Current noun–adjective compounds and equivalent phrases have the same spoken sequence; **treat them as semantic aliases unless a future lexicalization rule introduces an audible distinction and is separately tested**. Do not add a marker to all 708 compounds merely to avoid theoretical ambiguity.
- **Dravidian/Austronesian:** prototype inclusive/exclusive first-person plural only in separately tested, opt-in materials. Keep canonical `ni` unchanged.
- **Austroasiatic/Sinitic:** keep topic and context-based ellipsis opt-in, with explicit roles in consequential communication. Veka 0.6 has experimental topic/focus but no proven speech benefit.
- **Indo-European/Afroasiatic/Niger-Congo:** consider attested international loans and transparent derivation as alternatives, *not* wholesale grammatical gender, noun-class agreement or consonant templates.
- **All backgrounds:** preserve a Latin-letter interoperability standard while separately measuring accessibility and learnability of the experimental featural script.

**Release gate:** Until results exist, the best vocabulary change is *no canonical vocabulary change*.
