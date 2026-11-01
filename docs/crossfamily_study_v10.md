# Veka 0.10: source screening and stratified first-sight comprehension protocol

**Research only.** These are source-screening observations and planned experiments, not an independently adjudicated lexical dictionary, actual human outcomes, an approved vocabulary replacement, or a validated universal language.

## First screening: international trial `R03` (music)

The source-linked, *noncanonical* form `mu-si-ka` is tested against current Veka `woi` (music). The source-screening data are in [`data/music_source_screening_v10.csv`](../data/music_source_screening_v10.csv). Web sources were inspected or indexed on 2026-11-01; observations remain `independent_review_status=pending`, and **no** values are transferred to accepted `global_evidence_v07.csv` or `cognate_evidence_v07.csv`. Citation URLs and very short headwords are retained; source text is not redistributed.

| Language / family | Attested everyday word | Public reference | Interpretation for Veka |
| --- | --- | --- | --- |
| English / Indo-European | `music` | [Cambridge English–Portuguese dictionary](https://dictionary.cambridge.org/dictionary/english-portuguese/music) | Similar origin, different pronunciation; not evidence English beginners recognize `mu-si-ka` |
| Portuguese / Indo-European | `música` | [Cambridge Portuguese–English dictionary](https://dictionary.cambridge.org/pt/dicionario/portugues-ingles/musica) | Closest written resemblance; not a measured recognition outcome |
| Swahili / Niger-Congo | `muziki` | [Wiktionary lexical entry](https://en.wiktionary.org/wiki/muziki) | Documented borrowing, differently pronounced; check native usage and register |
| Indonesian / Austronesian | `musik` | [Wiktionary Indonesian section](https://en.wiktionary.org/wiki/musik) | Dutch borrowing; same borrowed word family, not an independent root |
| Mandarin / Sino-Tibetan | `音乐` (`yīnyuè`) | [Wiktionary Mandarin section](https://en.wiktionary.org/wiki/%E9%9F%B3%E6%A8%82) | Negative lexical-recognition example: a common native term unlike `mu-si-ka` |

**Important:** Cambridge and the university Swahili dictionary search entries may not be fully fetchable by automated clients; indexed search results and page inspection are not equivalent to a native-speaker semantic review. A scholar or fluent independent reviewer must verify sense, script, register, transliteration, and current usage. Reviewer claims should be entered only after that work. Portuguese and English count as *one* genealogical family; Swahili and Indonesian have separate recipient families but may share the same European borrowing chain. The script should never treat language-family coverage as a measured probability of recognizing Veka.

## A blocked design, without invented participant outcomes

`cohort-plan` takes a **researcher-supplied roster of pseudonyms** and assigns an equal number of participants in each background stratum to the two complementary word-list arms. For example, English-L1, Portuguese-L1, Mandarin-L1, Swahili-L1 and Japanese-L1 can each be stratified separately; a participant must be assigned to a prespecified primary stratum and record multilingual exposure for later analysis. This is blocking by language background, **not** the impossible claim that all speakers of a language learn identically.

The underlying `cognate-manifest` currently contains 18 concepts: 10 additions and 8 replacements. Within each arm it presents each concept **once**. Replacement words are split between core and international forms; additions between nonce controls and international forms. The other arm reverses assignments. Condition labels and target English glosses are in a researcher-only CSV; participant sheets contain only presented forms and blank answers. Trial order uses a deterministic seed, which must remain researcher-only while participants are tested. Run a new assessment separately for *spoken* comprehension; the first-sight visual/word study does not establish audio intelligibility.

### Commands

Prepare a **private roster outside the repository** using the headers in [`cohort_roster_template_v10.csv`](../data/cohort_roster_template_v10.csv). Supply real pseudonymous study enrollments, for example:

```csv
participant_id,background_stratum
P101,English-L1
P102,English-L1
P201,Portuguese-L1
P202,Portuguese-L1
P301,Mandarin-L1
P302,Mandarin-L1
```

These are illustrative identifiers, **not actual recruited humans**. Do not publish a populated roster. At least two (and an even number of) participants are required per stratum; real confirmatory studies need power analysis and substantially more than two. This criterion ensures arm balance, **not statistical adequacy**.

```sh
python3 -m veka cohort-plan \
  --roster /secure/private/cohort-roster.csv \
  --participants-dir /secure/study-participant-sheets \
  --researcher-dir /secure/study-researcher-keys \
  --seed 20261101
```

All output directories must **not yet exist**, must have existing parents, and may not overlap or nest. Files and directories are created with owner-only permissions on POSIX systems. Keep the entire researcher directory inaccessible to participants; each participant should receive **only their own** sheet. No network collection or distribution occurs. The command deliberately refuses to overwrite old runs.

### Execution and decision gates

1. Preregister the exact meaning inventory, acceptable answer synonyms, time limits, knowledge/exposure questionnaire, exclusions and critical misunderstanding criteria. Recruit actual consenting participants from multiple linguistic backgrounds. Do not place names, contacts, audio, responses or sensitive profiles in the public repository.
2. Use the plan to randomize groups; give each participant only their form sheet with no key. Collect **actual** first-sight free-text guesses, response times, repair requests, and optional prior exposure, blinded against target meaning.
3. Independently adjudicate responses using the researcher key, before analyzing the competing hypothesis. Analyze at the **participant and concept** levels: accuracy, false friends, median response time, and uncertainty intervals. Report per-language results and cumulative teaching time; do not pool a borrowed term across languages and claim universal recognition.
4. Design a separate listening experiment using genuine, independent human productions, multiple talkers and controlled noise. A lexical cognate that is easy to read might be hard to hear.
5. Before changing Veka's published roots, require preregistered superiority in *correctly understood meanings per total interaction time* and noninferiority for consequential misunderstandings. Disclose the sample, variance, population coverage and any added syllable/typing costs. If no strong benefit, preserve the old root.

### Known limitations and responsibilities

`cohort-plan` checks CSV integrity, pseudonym safety, unique IDs, arm balancing, answer-key separation, and overwrite resistance. It cannot authenticate actual participants, enforce consent, prevent participants screenshotting or guessing conditions, measure fluency, or prove random assignment in a third-party recruitment process. Neither a generated sheet nor a fabricated response CSV is evidence of efficacy. All 1,025 core entries and Veka grammars remain unchanged.
