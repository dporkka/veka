# Veka 0.11 — first-sight practice and active recall (noncanonical)

**Status:** offline teaching aid. No vocabulary, grammar, pronunciation, parser semantics,
official spelling or international word has changed. This does **not** establish
human comprehension, language proficiency, speaking speed, or translation equivalence.

Interlingua's strongest practical benefit is familiarity at first sight,
particularly among speakers of Romance languages and English. Veka currently
cannot claim equivalent immediate comprehensibility. Instead of assuming
that a familiar-looking adapted form is recognized across language families,
this tool helps learners practice **existing** parser-checked Veka utterances
while the separate international-root research tracks investigate replacements.

## Try the two independent tasks

Recognition: read a canonical Veka sentence and select the corresponding
**curated editorial** translation among three options.

```sh
python3 -m veka practice --lang en --mode recognition --seed 42
python3 -m veka practice --lang zh --mode recognition --seed 42 --format json
```

Recall: read a teaching translation and write back the **taught Veka surface**.
It does not ask learners to translate unseen sentences or judge synonyms.

```sh
python3 -m veka practice --lang pt-BR --mode recall --seed 42
```

To self-check, save a UTF-8 file of submitted answers, without including
the correct text or any answer-key column:

```csv
question_id,response
L03,Mi pa dak mel.
```

```sh
python3 -m veka practice-check --responses /path/to/responses.csv \
  --lang pt-BR --mode recall --seed 42
```

The checker uses the **same** language, mode, seed, count and profile as
the question command. For recognition, responses are **A**, **B**, or **C**,
not text. For recall, an answer matches only if it has the same taught
words and structure, ignoring letter case, repeated whitespace and one
optional final period. A plausible alternative translation can be
linguistically valid and still be graded *incorrect* here; the checker has
**no semantic equivalence model**. Feedback includes the taught target for
incorrect submissions; unanswered items stay unanswered.

The order and distractors are reproducible from a seed. This is **not**
research-grade randomized assignment or a blinded comprehension study:
learners can inspect the source code and the taught answers, and there is
no participant recruitment, hidden key, baseline, delayed recall, audio,
or independent human adjudication. The practice system stores no learner
history and submits no data to a server.

## Version and compatibility boundaries

- Ten existing editorial sentence examples, and their English, Mandarin
  and Brazilian Portuguese translations, from `veka/lessons.py`.
- Both explicit phonological profiles work; canonical remains tonal.
- Experimental international forms are **never** substituted for accepted roots.
- The generated questions exclude answer keys and parser glosses.
- Responses are validated strictly: exact `question_id,response` CSV
  columns, unique known IDs, and valid recognition labels.
- To change accepted Veka vocabulary or grammar, require a separate,
  versioned proposal, semantic and compatibility tests, and independent
  comparative human evidence. No self-practice score can authorize that.

## Remaining highest-priority language work

1. Run real multilingual first-sight, retention, audio and repair studies
   on independently attested international-root candidates. The present
   datasets contain no verified human recognition results.
2. Close restricted quantifier, comparison, modality and conversational
   repair gaps in an **opt-in** grammar with explicit semantic contracts.
3. Only after evidence, consider canonical revisions with migration.
