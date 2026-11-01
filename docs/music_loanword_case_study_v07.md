# Music loanword case study — Veka 0.7 (research leads only)

**Status:** five source-linked *unreviewed* lexical leads for the existing `C002` (music) experimental candidate `mu-si-ka`. These are **not verified** attestations in Veka's research protocol and are not accepted vocabulary. The main `data/global_evidence_v07.csv` template remains blank.

## Why this case is useful

Modern Greek *μουσική*, Arabic *مُوسِيقَى*, Turkish *müzik*, Swahili *muziki*, and Malay *muzik* come from five **genealogical families**, but the sources report borrowing paths ultimately associated with the Ancient Greek word for music. They are evidence that a recognizable *word family spreads by contact*, **not** that these language families share an ancient cognate. Nor does one term in each language establish universal spontaneous recognition.

These are reviewer leads, not completed independent semantic analyses or listener data.

| Language | Linguistic family | Candidate lead | Documented link | Notes to verify |
| --- | --- | --- | --- | --- |
| Modern Greek | Indo-European | μουσική | https://en.wiktionary.org/wiki/μουσική | Modern use and ancient lineage; check historical meaning distinctions |
| Arabic | Afroasiatic | مُوسِيقَى | https://en.wiktionary.org/wiki/موسيقى | Source reports borrowing from Ancient Greek, not inherited Semitic root |
| Turkish | Turkic | müzik | https://en.wiktionary.org/wiki/müzik | Source reports borrowing through French; distinguish from Turkish *musiki* |
| Swahili | Niger-Congo | muziki | https://swahili-dictionary.com/swahili-english/muziki_muziki | University of Dar es Salaam TUKI dictionary, 2000; separate etymology claim supported by Wiktionary/Zawawi 1979 |
| Malay | Austronesian | muzik | https://en.wiktionary.org/wiki/muzik | Source reports English or Dutch borrowing; check pronunciation varieties and exact register |

For Swahili borrowing path research, see https://en.wiktionary.org/wiki/muziki and the bibliographic reference to Zawawi (1979). This evidence is not proof that the adapted Veka form `mu-si-ka` sounds alike in five speech communities.

## Review queue

```bash
python3 -m veka global-audit --evidence data/global_music_leads_v07.csv
python3 -m unittest discover -s tests -p test_music_evidence_v07.py -v
```

Expected with current lead file: **five pending review records, zero verified attestations, zero human comprehension observations**. No canonical word changes.

Review protocol:
1. Independently inspect the URL and record the exact sense, spelling, sound, source variety and etymological confidence. Notes currently summarize web entries rather than establish new independent research.
2. Decide whether a specific attested form expresses the intended music concept; record a reviewer identity and mark `semantic_equivalent=yes/no`. For `yes`, set `attestation_verified=yes` only after direct review, and retain a stable attributable source.
3. Independently evaluate whether adapted `mu-si-ka` is pronounceable, recognizable and distinguishable from the existing one-syllable `woi`. Do not equate Latin transcription with auditory similarity.
4. Recruit speakers from unrelated first-language backgrounds for blinded recognition tests, including populations where these loanwords are unfamiliar. Compare `woi`, `mu-si-ka`, and transparent phrase explanations. Preregister training, elapsed response time, repair time, and critical mistakes.
5. Do not update canonical `data/lexicon.csv` without an additional versioned migration and empirical noninferiority checks.

**License/provenance:** Lexical leads reference Wiktionary content (subject to its attribution and share-alike conditions) and the publicly accessible University of Dar es Salaam/TUKI dictionary. This repository stores only individual headword examples and URLs, not copied dictionary definitions. Review downstream redistribution terms separately.
