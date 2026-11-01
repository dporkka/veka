# Veka 0.3 phonology and perception risk evaluation

## Empirical baseline and warnings

Coupé et al. (2019) estimated similar typical spoken-language information rates across a sample of 17 languages because syllable-level density and articulation speed trade off. **That observation is not a proof that engineered languages can exceed typical natural language communication rates.** [Source](https://pmc.ncbi.nlm.nih.gov/articles/PMC6984970/).

Redford and Diehl (1999) found final consonants less identifiable than initial consonants in tested CVC contexts. [Source](https://pubmed.ncbi.nlm.nih.gov/10489711/). Dubno and Levitt (1981) measured context-dependent consonant confusions under noise. [Source](https://pubmed.ncbi.nlm.nih.gov/7217523/). Hence edit distance between spellings is merely a cheap *first screening heuristic*, not an acoustic model or a validated predictor.

## Sound design

- Provisional IPA: `p b t d k g m n f v s z h l ɾ j w`, vowels `/a e i o u/`. Actual speaker accents and r-realization require specification and training.
- No compulsory stress contrasts, no consonant clusters, largely CV/CVC.
- Lexical tonal distinction: level vs rising, with only **four** current tonal roots (`pái`, `pál`, `lé`, `vén`). This limited utilization is an important reason to test a tone-free variant.
- The restricted rising tone has provisional relative pitch target mid→high; absolute Hz is speaker-specific. Pitch perception must be tested with different talkers, ages, and tone-language backgrounds.
- Coda consonants are particularly risky under speech masking, so critical short markers and numbers should be tested, not assumed intelligible.

## Instrumented audit

`python -m veka audit --output data/phonology_audit.json` evaluates distinct **form pairs** and reports the contrast type. Current lexicon has 1,025 entries, 317 atomic roots, 4 rising-tone roots, and only one established level/rising minimal pair (`pal`/`pál`). The auditory-risk count also includes many single-coda contrasts. **Do not interpret a count of these pairs as a modeled recognition error rate.**

The decimal words were selected to have pairwise orthographic Levenshtein distance >= 2, also >= 2 from designated grammatical operator markers. That does **not** guarantee distance from all vocabulary or perceptual confusability across speakers. Consonant voicing and syllable-final information may deteriorate in noise.

## Tone-free experimental variant

`data/tone_free_ablation.csv` contains four candidate substitutions for rising-tone roots. This is an **alternative experimental condition**, not a replacement for canonical Veka or a demonstrated improvement. Some candidate replacements use different consonants/codas and may introduce new confusions; their acoustic duration, learnability and speaker production cost must be measured. In particular, comparing tone and no-tone conditions also changes lexical memorization and segmental cues. Preregister and counterbalance the learning cohorts; do not interpret an uncontrolled difference as the independent effect of pitch.

## Next go/no-go decision

First test the 7 contrast pairs in `data/phonology_abx_pairs.json`, particularly pronoun contrasts (`mi`/`ni`, `mi`/`ti`), future/progressive (`fu`/`du`), negation markers (`ne`/`no`), and the established tone pair (`pal`/`pál`). Record human speech by multiple speakers, using independently produced A/B/X tokens and matched recording levels. Determine confusion matrices with confidence intervals, and compare quiet vs controlled noise in a secondary condition.

**Recommendation:** do not enlarge the tone inventory until participants show that tone adds perceptual throughput rather than extra production and decoding burden. There are hundreds of available toneless syllables, so lexical tone is not currently necessary for 317 primitive roots.
