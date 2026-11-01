# Veka 0.3 — formal grammar and semantics

**Status:** experimental, restricted, mechanically validated subset. Standard library only. This is not a complete grammar for unrestricted human speech.

## Sound inventory (unchanged from v0.2)

Consonants (romanization): `p b t d k g m n f v s z h l r y w`; vowels `a e i o u`; diphthongs `ai au oi` (when appearing as single syllabic nuclei). The character `y` denotes /j/, not the English vowel. `r` is provisionally an alveolar tap /ɾ/. Each monosyllabic form has the shape `(C)(V|D)(C)` with codas `n l s k` and restrictions. Restricted rising-tone vowels `á é í ó ú` apply only on open or sonorant-final syllables. Level-tone notation is unmarked. A hyphen joins two roots without adding an audible pause.

Syllable capacity is **932 distinct permitted forms** under the implementation, including level and rising variants. This is not 932 easily learnable or highly distinctive spoken morphemes. The v0.2 statement “936” was an uncorrected upper-bound calculation. The current 1,025 headwords use compounds and therefore do not require 1,025 independent syllables.

## Formal grammar (surface form)

The whitespace-separated romanized grammar has **no implicit logical precedence**:

```ebnf
utterance     = proposition | imperative ;
proposition   = atomic_statement | not_scope | binary_scope ;
not_scope     = "na", proposition, "yu" ;
binary_scope  = ("zi" | "oi" | "fi"), proposition, "ve", proposition, "yu" ;
atomic_statement = noun_phrase, ["pa"|"fu"], ["du"], ["ne"], predicate, ["ke"] ;
predicate     = (verb, [noun_phrase], ["to", noun_phrase],
                 ["en", noun_phrase], [time_lexeme]) | ("es", adjective,
                 ["to", noun_phrase], ["en", noun_phrase], [time_lexeme]);
imperative    = "ha", ["fu"], ["du"], ["ne"], verbal_predicate ;
noun_phrase  = ["al"|"kis"], head, ["lu"], {adjective},
               [numeral, ["su", unit]], ["de", noun_phrase] ;
numeral      = "wen", ["sin"], digit, {digit}, ["dis", digit, {digit}] ;
digit        = "nul"|"ran"|"kuk"|"zun"|"sok"|"gel"|"tak"|"pil"|"bos"|"mus" ;
unit         = "rel" | "sek" | "vos" | "wok" ;
```

The EBNF describes language intention; the reference parser further applies the executable rules in `veka/core.py` and `veka/logic.py` and only accepts the supported single-clause subset. In particular, noun phrases are not freely interchangeable with predicates, and valency is checked.

## Numbers

Decimal digits are positional, base 10. Every number begins with `wen`. Distinct digits are spoken **separately**; there is no unspecified grouping.

| Digit | Veka | Digit | Veka |
|---:|---|---:|---|
| 0 | nul | 5 | gel |
| 1 | ran | 6 | tak |
| 2 | kuk | 7 | pil |
| 3 | zun | 8 | bos |
| 4 | sok | 9 | mus |

- `wen ran kuk nul` = 120
- `wen nul dis nul gel` = 0.05
- `wen sin ran sok dis gel nul` = -14.50 (decimal scale is retained)
- `sil wen ran dis gel su wok` = 1.5 liters of water
- `ren wen kuk` = exactly two people

`sin` (negative) is not `ne` (clause negation). `dis` is the decimal point; `su` introduces an explicitly typed unit. Leading zeros, a dangling decimal point, negative zero, numerals longer than 64 digits, unmarked numeric sequences, and exponential shorthand are rejected. The parsing API returns the number as a **string**, not a floating-point value, preserving exact decimal digits. `read_number` and `spell_number` are reversible over this canonical syntax.

Unit words: `sek` second (SI), `rel` meter (SI), `vos` kilogram (SI), `wok` liter (accepted non-SI metric unit). No conversion or exponentiation grammar yet. Nominalized quantitative expressions are not a general-purpose equation language.

## Logic and quantification

Logical words are fully scoped with a **start word, operand separator, and end word**. They are not English conjunctions that merely appear between sentences.

- `zi A ve B yu` means A **AND** B.
- `oi A ve B yu` means A **OR** B, inclusive.
- `fi A ve B yu` means the **material implication** A→B. It does not assert causation or temporal order.
- `na A yu` means **NOT A**.

Example:

`Na zi mi gos ve ti gos yu yu.` = NOT (I go AND you go).

`Zi na mi gos yu ve ti gos yu.` = (NOT I go) AND (you go).

The two parses have structurally different abstract syntax trees. Nested operators are supported to a maximum of 16 levels and 256 tokens. `ve`, `yu` are mandatory scope delimiters, not optional punctuation. `ne` negates an atomic predicate, while `na` negates a whole propositional expression. The logical evaluator operates only on explicit externally provided truth values for atoms.

`al ren pa gos` = every person went; `kis ren pa gos` = some person went. A clause may use only **one quantified noun phrase**. `al ren pa ne gos` assigns the predicate's negative meaning **inside** the universal quantifier. `na al ren pa gos yu` puts negation **outside** the universal. The vocabulary defines neither the contextual domain nor whether a real-world statement is true. Two quantifiers in one atomic clause (e.g. every person sees some person) are intentionally rejected because variable binding and order of scope are not yet defined.

Exact quantities cannot combine with universal/existential quantifiers or the `lu` plural marker on the same noun phrase. **Numerals in a possessor noun phrase do not quantify the head noun.**

## Recoverability safety rules

The compact register may omit roles only when every omitted valency-required argument has **exactly one declared candidate in jointly shared discourse**. This is not an automated inference that humans share the same context. `--strict` bans such omissions and the potentially ambiguous `sa` pronoun. High-consequence instructions should be in the explicit register, with quantities, units, negation, and reference made overt.

## Still unsupported

Relative clauses, open-ended recursive relative constructions, quantifier scope over multiple participants, modality, tense-aspect interactions beyond the simple particle order, universal domain restriction, arithmetical operators, comparisons, time zones, physical quantity dimensions beyond the four unit labels, and robust dialogue pragmatics. The parser should reject rather than silently reinterpret these constructions.
