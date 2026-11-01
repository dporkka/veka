# Offline dialogue-response collection (research-only v0.12)

**Not a new grammar or evidence of comprehension.** This procedure packages
human-authored, independently reviewed *target-language* dialogue stimuli into
participant-only JSON. The browser records unscored responses locally. It does
not verify the stimuli, contact participants, perform semantic adjudication,
collect research records on a server, or insert observations into the benchmark.

## Preparation by an independent researcher

1. Select two to forty distinct scenario IDs from
   `data/everyday_dialogues_v09.json`, after documenting expected meanings.
2. For each selected scenario, obtain an independently reviewed translation
   of the two dialogue turns in the assigned condition. Record translator and
   second reviewer identities, proficiency and date in a separate **private**
   provenance log. Text below is schema illustration, not approved Veka syntax.
3. Assign an opaque pseudonym and unique trial IDs. Each participant must see
   a given semantic scenario at most once, regardless of language condition.
   Randomize condition and trial order as part of a separately preregistered
   study protocol. This tool does **not** balance or randomize them.
4. Store a UTF-8 CSV with exactly these fields (in order):

```csv
participant_id,trial_id,scenario_id,language,context,utterance
```

`participant_id` must be 2–64 letters, numbers, `_` or `-`; trial IDs must use
`D01-` and 16 lowercase hexadecimal digits. `scenario_id` must occur in the
frozen 100-scenario corpus. `language` is one of `veka`, `globasa`,
`esperanto`, `interlingua`, `indonesian`. `context` and `utterance` must be
plain, nonempty, trimmed text of at most 2,000 characters without control
characters, spreadsheet-formula prefixes or hidden answers. The manifest is
**researcher-only**, because scenario identifiers are linkable to meaning
requirements. No correctness or key columns are accepted.

## Create and conduct the offline session

```sh
python3 -m veka conversation-session \
  --manifest /secure/researcher-manifest.csv \
  --output /secure/participant-S001.json
```

The command refuses overwrites and creates a participant-only JSON with
restricted permissions on systems supporting POSIX permissions. Its payload
contains only a pseudonym and an ordered set of opaque trial IDs, assigned
language labels, context text and utterance text; it contains **no scenario
ID, reference answer, meaning key, score or reviewer assertion**.

Open `site/conversation-study.html` directly in a modern browser without a
server or network connection. Load the participant JSON, provide the
researcher-assigned language-background family label, and obtain consent.
The participant answers the second turn of each dialogue in their own words
(or "I don't know"). The page uses `textContent`, not HTML injection, when
rendering supplied stimuli. It flags window/tab interruptions, and makes no
claims about calibrated reaction-time measurements. No input is sent by the
page to a remote service. Reloading the page loses unexported responses.

At completion the participant may **optionally** export a private unscored CSV
with the fields:

```csv
participant_id,trial_id,language,response_text,response_ms,timing_interrupted,background_family
```

Free text is spreadsheet-formula neutralized in the exported CSV. This changes
only suspicious output prefixes, not their display. The researcher must
securely join the participant data with the *researcher-only* scenario mapping
and independently adjudicate meaning correctness and critical errors. Exclude
or separately analyze interrupted timing observations under preregistered
rules; don't silently treat them as calibrated reaction times.

## Subsequent scoring remains explicitly human-gated

`python3 -m veka conversation-score` consumes a **different** CSV schema:
`participant_id,background_family,scenario_id,language,correct,elapsed_ms,repair_ms,critical_error`.
That scored file must only be produced after independent human review and
confirmed timing and clarification/repair records. The offline page collects
only first-response time. It does **not** measure actual repair duration, so
never invent `repair_ms=0` to satisfy the scoring contract if repair was
not observed. Do not infer `correct` by text matching and never declare that
parser acceptance establishes semantic equivalence.

This pipeline is not a substitute for recruitment, informed consent review,
stimulus licensing, translator review, prospective registration, acoustic
quality control, blind adjudication or statistically powered analysis. See
`docs/language_transfer_v01.md` for recommended study design and the
critical-error noninferiority gate. **No human participant results are shipped.**
