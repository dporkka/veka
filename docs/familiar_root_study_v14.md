# Seven-form familiar vocabulary study (v1.4, noncanonical)

This is a **reproducible research snapshot** of the seven proposed substitutions
in draft [PR #46](https://github.com/dporkka/veka/pull/46) at
`d984b5dd72051996fc552e198f6e94d8c972b13d`.
It does **not** merge that experimental parser or endorse replacing any root.

The research manifest is `data/familiar_candidates_v14.csv`. The seven
proposed pairings are `woi/mu-si-ka` (music), `vik/se-ko-la` (school),
`sau/bu-ku` (book), `noi/os-pi-tal` (hospital), `dik/ka-me-ra`
(camera), `hek/dok-ta` (doctor), `ru/me-tal` (metal). All are
`unverified_draft` with no accepted lexical or pronunciation status.
The inherited `doctor` meaning is ambiguous across a physician,
academic title and general professional titles; use a preregistered rubric.

## Controlled seven-form written first-sight study

A valid study still requires actual independently consented participants.
For a *private*, pseudonymous roster (with unrelated identifiers such as
P01, P02 instead of `English1`), use:

```sh
python3 -m veka root-study-plan \
  --candidates data/familiar_candidates_v14.csv \
  --roster /private/roster.csv \
  --participants-dir /private/familiar-participants \
  --researcher-dir /private/familiar-keys
```

It creates seven blank trials per participant. Assignment reverses
core-versus-candidate exposure across **complementary pairs within each
background stratum**. Each meaning is equally represented by condition within
each stratum, but because seven is odd, one participant has 4 candidate and
3 canonical words while their matched partner has 3 candidate and 4 canonical
words. This is balanced **per concept and stratum**, not perfectly within
every participant. It must not be interpreted as a recruitment record.

After returning all seven responses and recording real response times and prior
exposure, follow the independent manual-review protocol in
[root adjudication v1.3](root_adjudication_v13.md). Both commands MUST use
the **same candidate manifest** used at planning time:

```sh
python3 -m veka root-study-review \
  --candidates data/familiar_candidates_v14.csv \
  --key /private/familiar-keys/researcher-key.csv \
  --responses-dir /private/returned-familiar-responses \
  --output /private/familiar-review.csv

# First perform independent, condition-blind semantic judgments in the CSV:
python3 -m veka root-study-score \
  --candidates data/familiar_candidates_v14.csv \
  --key /private/familiar-keys/researcher-key.csv \
  --responses-dir /private/returned-familiar-responses \
  --reviews /private/familiar-review.csv
```

The CLI rejects a study key that does not match the provided candidate
vocabulary; it does not silently reclassify older trial data. The default
eight-form v1.2 protocol is unchanged when no `--candidates` is given.

## Evidence constraints and decisions

The seven forms are visually plausible in **some** languages, but their
individual cross-family recognizability, lexical sense-equivalence, phonological
accessibility, listening intelligibility and delayed retention are **unknown**.
No actual human outcomes are bundled or implied by synthetic test fixtures.
Indonesian and Swahili loanword resemblance is not proof of distinct inherited
origins. The Portuguese word `data` is a useful example of why false-friend
screens matter, though `data` is *not one of these seven pilot forms*.
Pre-register acceptable senses for all seven words, explicitly note
nonmatching Mandarin forms and confusable loanword senses, screen prior
exposure and run independent blinded assessment. Raw response spreadsheets and
keys must remain private.

The reports contain only descriptive group and item outcomes. They **do not**
establish benefit, require migration of any of the existing 36 associated
registered compounds, or authorize changing `data/lexicon.csv`. A later
versioned compatibility proposal should address compound migration, collisions,
spoken confusability and legacy materials **only after evidence exists**.

## Verification

```sh
python3 -m unittest discover -s tests -p test_familiar_root_study_v14.py -v
make validate
```
