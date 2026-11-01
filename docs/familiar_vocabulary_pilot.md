# Familiar vocabulary pilot, version 1

This is a working, **experimental lexical profile**, not a change to canonical
Veka. It replaces seven nouns and their registered compositional compounds while
preserving Core grammar, meanings, valency, logical particles and numbers. It is
a starting point for the requested vocabulary reform, not a complete reform.

| Core | Pilot | Meaning | Caution |
|---|---|---|---|
| woi | mu-si-ka | music | Recognizable in some languages; not universal |
| vik | se-ko-la | school | Adapted spelling; recognizability untested |
| sau | bu-ku | book | Familiar in some languages; not universal |
| noi | os-pi-tal | hospital | Adapted pronunciation; meaning needs review |
| dik | ka-me-ra | camera | Meaning and recognition need review |
| hek | dok-ta | doctor | Doctor versus physician sense requires review |
| ru | me-tal | metal | Indonesian and Mandarin common terms differ |

These editorial proposals reuse the existing international candidate list. They
are not validated multilingual attestations or evidence of better learning.
They add syllables and likely favor some language backgrounds. Grammar and
pronunciation regularity are retained at the cost of less familiar spellings.

```sh
python3 -m veka.familiar parse 'Mi sen mu-si-ka.'
python3 -m veka.familiar convert to-familiar 'Mi sen woi-val.'
python3 -m veka.familiar convert to-core 'Mi sen mu-si-ka-val.'
```

The dedicated parser accepts strict Core clauses in the pilot lexicon; it
rejects old replaced forms even when capitalized. Existing default commands,
other profiles, teaching materials and the canonical dictionary are unchanged.
Registered compounds follow their replaced head and retain their meanings. The
conversion utility works on whole lexicon tokens and preserves basic case and
punctuation; it is not a translator, grammar validator, or safe for a proper
name that happens to equal a replaced word. Treat source and destination as
explicitly versioned; do not mix them in one utterance. Hyphens separate
syllables as in existing Veka. Neither spelling checks nor exact surface
collision checks establish acoustic distinctness.

Before widening or standardizing the profile, review each intended sense and
false friends, compare first-sight understanding and retention for diverse
language backgrounds, test pronunciation and noisy listening, and audit all
lessons and downstream tools. No human outcomes are currently available.

## Source review and limits

These are first-pass dictionary checks of donor forms, not independent
verification of semantic equivalence, pronunciation or recognition of the
adapted Veka words. Related forms and loanwords across different languages
are not independent etymological origins.

- **Music:** Portuguese *música*, Indonesian *musik*, Swahili *muziki*;
  Mandarin 音乐 (*yīnyuè*) differs. [Music translations](https://en.wiktionary.org/wiki/music).
- **School:** Portuguese *escola* and Indonesian *sekolah*; the latter is a
  loan through Malay from Portuguese. Swahili *shule* is less similar.
  [Indonesian escola-related form](https://en.wiktionary.org/wiki/sekolah);
  [school translations](https://en.wiktionary.org/wiki/school).
- **Book:** Indonesian *buku* and English *book* are similar; Portuguese
  *livro* and Swahili *kitabu* differ. [Book translations](https://en.wiktionary.org/wiki/book/translations).
- **Hospital:** Swahili *hospitali* is similar, whereas standard Indonesian
  *rumah sakit* differs. [Hospitali](https://en.wiktionary.org/wiki/hospitali);
  [rumah sakit](https://en.wiktionary.org/wiki/rumah_sakit).
- **Camera:** Brazilian Portuguese *câmera* and Indonesian/Swahili *kamera*
  resemble the proposal; Mandarin terms differ. [Camera translations](https://en.wiktionary.org/wiki/camera);
  [kamera](https://en.wiktionary.org/wiki/kamera).
- **Doctor:** Indonesian *dokter* and Swahili *daktari* can mean physician;
  Portuguese *doutor* can be a title and English *doctor* can refer to a
  doctorate holder. The inherited Core gloss is simply `doctor`, so the
  pilot does not resolve this ambiguity. [Physician translations](https://en.wiktionary.org/wiki/physician);
  [doctor](https://en.wiktionary.org/wiki/doctor).
- **Metal:** Portuguese *metal* and Swahili *metali* resemble the proposal;
  Indonesian *logam* and Mandarin 金属 (*jīnshǔ*) differ.
  [Metal translations](https://en.wiktionary.org/wiki/metal);
  [Chinese 金属](https://en.wiktionary.org/wiki/%E9%87%91%E5%B1%9E).

These sources are useful leads, not corpus-frequency estimates or a substitute
for independent dictionary and speaker review. The core meanings remain exactly
as recorded in the dictionary; do not infer that a familiar-looking spelling
communicates the intended sense without teaching.

## Short practice

These are editorial teaching glosses, not independently checked translations.
`mi` means I, `rin` need, `lin` see, `vo` buy, and `pa` marks past.

| Veka | English | Portuguese | Mandarin |
|---|---|---|---|
| Mi rin dok-ta. | I need a doctor. | Preciso de um médico. | 我需要医生。 |
| Mi lin ka-me-ra. | I see a camera. | Vejo uma câmera. | 我看见一台相机。 |
| Mi pa vo bu-ku. | I bought a book. | Comprei um livro. | 我买了一本书。 |

The first example uses the physician interpretation of `dok-ta` for teaching;
the inherited `doctor` gloss still needs an explicit sense decision. These
sentences illustrate the pilot but do not establish natural use or translation
quality. The parser checks structure, not the translations.
