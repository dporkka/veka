# Veka 0.7 — source-linked internationalism review packet

**Scope:** follow-up to [the noncanonical cognate pilot](cognate_pilot_v07.md).
The 12 entries in `data/cognate_source_leads_v07.csv` are **source-linked
unreviewed leads**, not verified multilingual attestations or spontaneous
recognition findings. Canonical vocabulary and parser remain unchanged.

## Research coverage

| Concept | Adapted Veka trial form | Unreviewed source-language leads |
| --- | --- | --- |
| taxi (N01) | `tak-si` | South Levantine Arabic, Japanese, Swahili, Malay |
| hotel (N02) | `ho-tel` | South Levantine Arabic, Japanese, Swahili, Indonesian |
| robot (N03) | `ro-bo` | Hindi, Japanese, Swahili, Indonesian |

The source-backed forms and references are stored **per language** in the CSV,
not inferred from family membership. Most examples are contact-driven
internationalisms, borrowed directly or indirectly from European languages.
**Genealogically separate recipient languages do not establish independent
origins or independent familiarity.** Arabic loanword variants can be
regional; do not extrapolate their use to all Arabic varieties.

`ro-bo` omits a final consonant present in Hindi, Japanese, and Indonesian
donor terms, while Swahili `roboti` has an additional final vowel.
`ho-tel` contrasts with Japanese `hoteru` and Swahili `hoteli`. Sound
similarity and the actual conversational register require separate testing.

The linked Wiktionary articles are public lexicographic leads, not
independent attestations certified by project reviewers. This packet
contains only brief headword strings and citations, rather than dictionary
entry text. Preserve source attribution and check downstream CC BY-SA
requirements before republishing substantial derived text. For methods and
cross-language borrowing classification, see
[World Loanword Database](https://wold.clld.org/) (Haspelmath & Tadmor, 2009),
which is **not claimed to contain these specific 12 observations**.

## Commands

```bash
python -m veka cognate-leads
python -m veka cognate-leads --output /tmp/veka-cognate-review.json
python -m unittest discover -s tests -p 'test_cognate_leads_v07.py' -v
```

`--candidates` and `--leads` allow testing alternate experimental datasets.
The audit checks schema integrity, matching concepts and candidate forms,
unique language records, source URL shape, declared family/branch, and
the reviewer-state transition. It **does not fetch source URLs**, check
whether the lexicographic claim is true, validate genealogy, or infer
listeners' comprehension. No data collection or source review is performed
by a successful command.

## Independent human review procedure

1. Inspect each article at its original URL, preferably alongside a
   locally authoritative dictionary for that language. Confirm the term's
   actual register, meaning, variant, and script/transliteration.
2. Record the meaning of the intended Veka referent, especially alternatives
   such as Arabic `funduq` for hotel. Distinguish word existence from
   normal usage, spoken similarity, and comprehension.
3. Have a named independent reviewer mark `semantic_equivalent=yes` or
   `no` and then `attestation_verified=yes` **only after** inspecting
   the source and sense. Reviewer identity is an assertion in data, not
   cryptographic proof of human review.
4. Retain original URL, family, branch, spelling, and explanatory notes.
   If the source is unreliable, replace the link and review again; do not
   count an unsupported lexical item as verified.
5. Rerun `cognate-leads`. Only verified equivalent records contribute to
   its verified-language and verified-family counts. Even then, a
   cross-family source list is not a measured recognition probability.
6. Transfer individually reviewed records to the separate
   `data/cognate_evidence_v07.csv` schema only after manually checking the
   concept mapping; that older evidence schema needs `citation`,
   `reviewer`, and `verified`. The existence of these research leads
   must not silently populate canonical or accepted vocabulary files.

## Study execution and promotion gate

The existing `cognate-manifest` command creates blinded participant
materials with ten addition items and eight root replacements, balanced
between experimental and control arms. Sample packets alone are **not**
actual participants or trials. Recruit language-diverse human participants,
randomly assign the two complementary arms, and collect first-sight sense
judgments separately from listening-in-noise and post-training recall.
Record duration, repairs, prior exposure, and pronunciation variants.
Maintain a separate researcher key and independently adjudicate acceptable
synonyms. Report results by actual language background rather than
combining borrowed forms as if each were an independent cognate.

Do not adopt a word until independently validated donor evidence and
reproducible human data show a **net benefit in correctly understood meaning
per unit time**, including speaking, learning and repairs.
