# Veka 0.4 — Interlingua-inspired international vocabulary research layer

**Status (2026-11-01):** executable *experiment design*, not an accepted vocabulary reform. It preserves the Veka 0.3 grammar, the 1,025 canonical dictionary rows, the phonology, the 708 existing compounds, and the exact-number/logic system. **No international candidate is a canonical Veka word.** A candidate is not automatically accepted by the parser, lexicon, or SVG writer.

## Motivation and design separation

Interlingua's method suggests maximizing the probability a learner can recognize an existing international term on first encounter. Veka's different objective is minimizing the time needed for *correctly understood meaning*, including teaching, production, listening, misunderstanding, and repair. International-looking forms can improve initial reading recognition for some audiences while adding syllables, phonotactic risks, and unequal cultural advantages.

Three deliberately separate resources are included:

1. **Canonical core:** `data/lexicon.csv` — unchanged; 317 root entries plus 708 established noun–adjective compounds. No international synonym is interpreted by the Veka 0.3 parser.
2. **Research queue:** `data/international_candidates_v04.csv` — 100 exact core concepts (nouns, verbs, adjectives), with eight **illustrative, unverified** adapted draft forms. The other 92 rows have no proposed borrowing. Neither forms nor possible donor spellings are verified historical Interlingua or multilingual attestations.
3. **Evidence log:** `data/international_evidence_v04.csv` — an **empty** template with fields `concept_id,language,language_family,attested_form,citation,reviewer,verified`. Do not mark a source verified without a real, inspectable citation and a human check of the word's meaning.

The eight draft proposals, in order, are:

| Meaning | Canonical root | Experimental form | Orthographic inspiration (unverified) | Syllables: core → draft |
|---|---|---|---|---|
| data | `do` | `da-ta` | data | 1 → 2 |
| music | `woi` | `mu-si-ka` | musica | 1 → 3 |
| language | `nol` | `lin-gu-a` | lingua | 1 → 3 |
| information | `kun` | `in-fo-ma-si-on` | informacion | 1 → 5 |
| computer | `za` | `ko-pu-ta` | computador | 1 → 3 |
| rice | `tos` | `ri-se` | rice | 1 → 2 |
| digital (adjective) | `vel` | `di-gi-tal` | digital | 1 → 3 |
| school | `vik` | `se-ko-la` | escola | 1 → 3 |

Each is only a **possible stimulus for humans to test**; the structural checker cannot establish familiarity, natural pronunciation, accurate semantics across languages, or independent source-family coverage. For example `ko-pu-ta` is only an approximate adaptation, not a translation validated for all speakers.

## Deterministic tools

From the repository root, using Python 3.10+ and no external dependencies:

```bash
python make_international_v04.py
python -m veka international-audit --output my_audit.json
python -m veka international-family
python -m veka international-family --noun ren --adjective sak
python -m veka international-family --noun sil --adjective bon
python -m veka international-manifest --participant P001 \
  --output participant_p001.csv --answer-key researcher_key_p001.csv
# Once manually judged trial outcomes exist, then and only then:
python -m veka international-score \
  --answer-key researcher_key_p001.csv --annotated observed_trials.csv
python -m unittest discover -s tests -v
```

`international-audit` checks exact canonical gloss/POS mappings, duplicates, Veka sound rules, forbidden grammatical/pronoun segments, full-form collisions with the canonical dictionary, and word lengths (2–8 syllables for optional draft terms, no tone). It reports structurally testable vs rejected forms and any genuinely documented evidence coverage; it never declares a form adopted or claims to measure recognition. The grammar still rejects every unregistered proposed form.

`international-family` audits the **existing noun-root + adjective-root** template, including every established compound's recorded head and modifier. Unregistered combinations such as `sil-bon` are flagged *hypothetical*; no automatic dictionary entries or new agent/tool/place/result suffix operators are invented. Such operators would require independent semantic definitions, collision checks, parser support, and a versioned proposal.

`international-manifest` creates a randomized **participant-facing sheet without translations or condition labels**, and a separate researcher answer key with target meanings. The same meaning is never repeated to the same participant; complementary pseudonymous participant IDs can receive opposite conditions. Assign IDs randomly to participants so an ID pattern cannot correlate with language background. The distributed sample sheets have **blank response fields and zero human observations**; `international-score` refuses incomplete or unjudged results.

## Multilingual evidence protocol

Do **not** treat English/French/Portuguese/Spanish as four independent language-family attestations, or treat written similarity as a recognition-rate estimate. For each concept and candidate:

1. Record the precise referent/sense and part of speech. Ambiguous English glosses (for example `data`) require additional sense annotation before field testing.
2. Collect attributable, independently checked written/spoken forms and **source links** from a range of genealogically and geographically diverse languages. Suggested strata: Sinitic, Indo-Aryan, Romance, Germanic, Semitic, Austronesian, Bantu, etc. Avoid over-weighting several languages from one related group. The evidence tool currently deduplicates by concept and language, and counts the manually labeled *top-level family* once per concept; nested subfamily weighting is future work.
3. Record original orthography, transliteration standards, phonological transcription where possible, and likely false friends in separately reviewed annotations (not implemented as automatic derivation). **Do not guess donor etymologies or infer global recognition.**
4. Document any adaptation and its phonetic cost explicitly. Veka restricts one consonant onset, a small set of nuclei, and codas `n/l/s/k`; most unmodified long international loanwords are invalid. The draft forms here are deliberately segmented with hyphens.
5. Keep every draft unregistered until a trial justifies it against existing short roots and transparent compounds.

A verified attestation must have `verified=yes`, a nonempty `citation`, and a named human `reviewer` (a pseudonym may be used); `verified=no` is not counted. Even a verified source does **not** prove a participant can recognize the resulting Veka loan.

## Human study design (not yet carried out)

**Primary reading endpoint:** correct first-sight semantic identification, with expert adjudication of synonyms and meaning scope. Secondary: elapsed response time, prior exposure, confidence, and lexical learning retention after a prespecified delay. **Speech endpoint** must be a separate recorded study using diverse native-language speakers, natural independently recorded tokens, quiet/noise conditions, and comprehension/repair measurement. These data do not exist in the artifact.

Use stratified random allocation across language backgrounds and education, blind the adjudicators to condition, and pre-register inclusion/exclusion and noninferiority criteria. One condition per concept per participant prevents within-session direct contamination. A paired or mixed-effects study can later model participant and item effects; the included scorer only provides simple descriptive statistics and **cannot estimate an effect or confidence interval**. Include non-European strata in recruitment rather than only learning from Romance-language familiarity.

**Recommended go/no-go for promoting an international synonym:** require validated donor provenance, evidence of meaning consistency, demonstrable initial comprehension or faster acquisition across target learner groups, no unacceptable decline in listening accuracy, and a positive net effect on communication time including extra syllables and repairs. Predefine numerical thresholds before data collection. If evidence is inconclusive, **keep the canonical core unchanged**.

## Non-goals and known limitations

- Not an Interlingua translation engine, phonological transliterator, global corpus, or recognition prediction model.
- Not a general morphological generator, licensed international lexicon, or semantic equivalence proof.
- Not a claim that the 100-concept queue is frequency representative, and not proof of equitable language-group performance.
- No real recordings, participant observations, verified external citations, adoption decisions, grammar changes, or canonical root changes.
- The phonotactic screen excludes grammatical particles in loan syllable segmentation as a conservative heuristic; acoustically similar longer forms still require testing.
