# Veka Beginner 0.1 — stable learning profile

**Curriculum version:** 0.1
**Underlying language:** canonical Veka 0.4 tonal vocabulary and Veka 0.3 reference grammar
**Status:** machine-checked controlled teaching exercises, not a new language release.

## Why this exists

New learners need **one stable target** and short exchanges they can read, say and ask. This curriculum does not adopt 0.5–0.7 experiments or edit any of the 1,025 locked headwords. Every sentence is accepted by the existing strict reference parser.

Latin romanization is the primary teaching script. Rising-tone accent marks in canonical vocabulary must be preserved; the alternative toneless profile remains experimental. The SVG featural script is not standardized input text.

## Start here

From the repository root, with Python 3.10 or newer:

    python -m veka learn list
    python -m veka learn show B01
    python -m veka learn quiz B01 --question 1 --seed 6
    # Choose a letter from the displayed multiple-choice answers:
    python -m veka learn quiz B01 --question 1 --seed 6 --answer A

The **dependency-free local web learner** uses the same curriculum as the CLI. From the repository root:

    python -m http.server 8765 --bind 127.0.0.1

Open http://127.0.0.1:8765/site/ in a browser. Do not open the HTML via the file:// protocol because the page fetches JSON over HTTP. No analytics, external libraries, synthesis, network AI or learner-response uploads are included. The browser tracks quiz progress only in memory for the current session.

## Beginner grammar

| Syntax | Meaning | Sample |
| --- | --- | --- |
| mi, ti, ni | I, you, we | Mi gos. — I go. |
| Subject + verb + object | fixed word order | Mi rok sau. — I read a book. |
| pa, fu | past, future | Mi pa dak mel. — I sent a message. |
| ne | predicate negation | Mi ne sen mel. — I do not understand the message. |
| ke | yes/no question suffix | Ti sen mel ke? — Do you understand the message? |
| en | location marker | Mi pau en nik. — I work in the office. |
| to | recipient marker | Mi fu nak sil to ti. — I will give water to you. |
| adjectives after nouns | modifiers | Mi lin he mik. — I see a broken tool. |
| wen + separate digits | exact positional number | sil wen ran dis gel su wok — 1.5 liters of water |

All required verb arguments are explicit. The beginner profile does not introduce experimental ellipsis, unrestricted subordinate clauses, logical precedence shortcuts, relative references or generalized quantifier scope.

## The controlled corpus

data/beginner_dialogues_v01.json includes **25 human-authored four-turn teaching exchanges, 100 utterances**. Each Veka clause is mechanically parsed using the strict reference grammar. The paired English meanings are **editorial interpretations**, not machine-proven translations, externally reviewed bilingual translations, or demonstrated natural conversations.

- Four consecutive sentences constitute a teaching exercise, **not** evidence that two people communicated successfully.
- The curriculum repeats a restricted number of syntactic patterns and is **not** a representative real-world conversation corpus or a proficiency certification.
- Standalone responses (such as ya, "yes") and many social expressions cannot be used with the current strict clause parser. Those are legitimate future grammar design tasks.
- Syntax checking does not validate the exact semantics of English articles, real-world truth, conversational intent, speech, listening accuracy, tone, or pragmatics.

## Next real-world improvements

1. Keep canonical vocabulary, grammar and frozen contract hashes unchanged; use separate versioned experimental proposals for additions.
2. Review English meanings with bilingual humans before teaching them as authoritative.
3. Collect conversation gaps, focusing first on greetings, acknowledgment, clarification, consent, apologies, uncertain statements, comparison and polite requests.
4. Train actual speakers, record real audio, and test pronouns, negation, numbers and phonological near-pairs in varied accents and noise.
5. Compare correct, held-out meaning recovery per minute (including repairs and learning effort) against an equally trained baseline.
6. Avoid using experimental Veka for safety-critical instructions.

**Distribution blocker:** There is no explicit repository license. See docs/licensing_decision.md before redistributing or hosting material beyond permissions actually granted by copyright owners.
