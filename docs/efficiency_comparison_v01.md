# Veka cross-language communication-efficiency instrument (v0.1, noncanonical)

**Status: structural pilot, not an empirical ranking.** The frozen canonical
Veka 0.3 grammar and 0.4 lexicon remain unchanged. An empty observational CSV
is not a study. The tool contains no synthesized language speech, recruited
participants, independent semantic review, or recorded comprehension results.

## Quick start

```sh
python3 -m veka efficiency-audit
python3 -m veka efficiency-score  # observed=false; zero trials
python3 -m veka efficiency-template --output /tmp/my-aligned-utterances.json
python3 -m veka efficiency-audit --manifest /tmp/my-aligned-utterances.json
```

The default dataset is a **frozen ten-item snapshot** of existing canonical
lesson examples in `data/efficiency_manifest_v01.json`, with editorial
translations in English (`en`), Mandarin (`zh`) and Brazilian Portuguese
(`pt-BR`). Future lesson edits cannot silently change this corpus. It does not
create new translations or imply that the readings are independently verified.
The source manifest is an editable copy; the exporter rejects overwriting
existing files.

## Extend the manifest safely

The manifest has `schema_version=veka.efficiency-manifest.v01`, a nonblank
`provenance` string, and nonempty `items`. Each unique item has `id`,
strict-canonical `veka`, and nonempty `variants` indexed by a supported
language code: `en`, `zh`, `pt-BR`, `id`, `tr`, `eo`, `ia`, `ja`, `vi`, or `es`.
These stand for English, Mandarin, Brazilian Portuguese, Indonesian, Turkish,
Esperanto, Interlingua, Japanese, Vietnamese, and Spanish respectively.

A variant has exactly six fields:

```json
{
  "text": "Human-authored target-language sentence.",
  "status": "editorial_unverified",
  "review_id": null,
  "spoken_syllables": null,
  "morphemes": null,
  "ambiguity_risk": null
}
```

For an *actual independent human review* change `status` to
`independently_reviewed` and supply a pseudonymous `review_id`; the three
manual metrics may remain `null` or be annotated. Strictly positive integer
`spoken_syllables` and `morphemes` represent the reviewed utterance's **spoken
form**, not its written length; `ambiguity_risk` is an optional **ordinal**
rating from 0 through 3, with a preregistered rubric: 0 = no salient alternative
meaning under the task context, 1 = weak alternative, 2 = plausible alternative
requiring clarification, 3 = consequential ambiguity. Different assessors may
disagree. A reviewer ID is self-reported evidence **only**, not authenticated
editorial provenance.

For Chinese, provide human-audited syllable counts: *characters are not a
reliable substitute*, especially with Latin fragments and numbers. For English
and Portuguese, do not derive spoken syllables from raw letter counts. For
Turkish and Esperanto, do not equate orthographic words with morphemes.
The tool computes **Veka-only** syllable and morpheme counts from the canonical
one-syllable-per-morpheme design and rejects Veka utterances that cannot be
parsed and counted. Count foreign proper names separately after adding an
explicit phonetic protocol, rather than guessing their Veka pronunciation.
Per-language orthographic character counts are only descriptive: **never
compare character counts across scripts as a language-efficiency ranking**.

A reviewer must assess semantic fidelity, tense/aspect, information content,
register, familiarity, lexical alternatives, and pragmatic context across
languages. In particular, some curated beginner translations differ in overt
article use or tense/aspect and are **not a validated parallel corpus**.
Record the wording chosen before running participants, and document the
selection process and independent reviewers outside the program.

## Observational scoring, if real trials are later collected

`data/efficiency_trials_v01.csv` is a header-only eight-column template:
`participant_id,background_family,item_id,language,correct,elapsed_ms,repair_ms,critical_error`.

```sh
python3 -m veka efficiency-score \
  --manifest /secure/reviewed-utterances.json \
  --trials /secure/pseudonymous-measurements.csv \
  --output /secure/observed-summary.json
```

Each observation must reference a manifest item and a presented language.
Non-Veka observations **require** independently reviewed comparator status;
the checker rejects duplicate item exposure to a single participant. `correct`
and `critical_error` are exactly `0` or `1` (never both 1).
`elapsed_ms` must be positive and `repair_ms` nonnegative. Both contribute
to denominator time. Only pseudonymous participant IDs are supported.
The `correct_per_minute` statistic is:

```text
60,000 × number of correctly recovered meanings
——————————————————————————————————————————————
sum of elapsed_ms + repair_ms (including incorrect trials)
```

The report includes **descriptive** language-level counts and balanced
background-family × item cells. Balanced cells are NOT randomized, matched
pairs or an inference of statistical power. Group participants by first/home
language as well as proficiency, not merely broad language family, when
collecting an actual study. Do not store names, recordings, or identifying
metadata in the repository.

## Experimental requirements before a language-design decision

1. Specify target populations, learner proficiency and equal exposure/training.
   Recruit independent participants across English, Mandarin, Portuguese,
   Indonesian, Turkish, and other chosen backgrounds; balance within groups.
2. Have independent bilingual reviewers verify each meaning-matched stimulus.
   Include low-frequency lexical contrasts, everyday repair situations,
   numeric precision, negation, tense, and scope—not only easy beginner items.
3. Preregister the *primary* endpoint: total elapsed-plus-repair time per
   correctly recovered meaning. Define critical error noninferiority and
   confidence intervals **before** collecting data. Measure comprehension
   independently of pronunciation and lexical recognition.
4. Counterbalance item language and speakers/listeners; prevent repeat-item
   leakage; record genuine acoustic speech under comparable conditions.
5. Publish uncertainty, individual language-background results, exclusions,
   and failure modes. No optimization or canonical adoption follows from
   raw syllable count, reviewer annotation, unbalanced comparisons, or a
   favorable observed mean alone.

Existing Veka `communication-audit` supplies synthetic **structural** contrast
coverage, while `conversation-score` evaluates separate 100-scenario
observational dialogue tasks. Neither is a substitute for verified translation
equivalence or a controlled comparative comprehension study.
