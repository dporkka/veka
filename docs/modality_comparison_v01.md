# Veka modal scope and typed comparisons — opt-in research v0.1

**Status:** mechanically tested, experimental grammar, not canonical Veka.
No replacement of existing Veka vocabulary, grammar, profiles or parser behavior
is authorized. Neither natural-language intelligibility nor human improvement
has been demonstrated.

The canonical 0.3 grammar intentionally does not claim complete modality or
comparative syntax. Interlingua supports ordinary ways to express these ideas;
this Veka prototype isolates overt meanings before deciding how they should
eventually be taught or spoken.

## Design: modality over one explicit proposition

```ebnf
modal = modal_marker, assertive_core, "yu"
      | "na", modal_marker, assertive_core, "yu", "yu" ;
modal_marker = "a-bi-li" | "po-si-bi" | "de-be-ri" ;
```

| Research marker | Structural intention | Example |
| --- | --- | --- |
| `a-bi-li` | Dynamic ability/capacity of the overt subject to realize P | `A-bi-li Mi gos yu.` |
| `po-si-bi` | Epistemic possibility that P obtains | `Po-si-bi Ti gos yu.` |
| `de-be-ri` | Deontic obligation regarding an explicit subject's action P | `De-be-ri Mi dak mel yu.` |

These modal predicates are **not** claims that P is true. The obligation
operator does not identify who imposed the obligation, its legal status,
permission or any normative justification. The ability operator does not
establish real physical capability, volition, or animate-agent semantics.

The scope of negation is overt:

- `Na a-bi-li mi gos yu yu.` = ¬ABILITY(I go)
- `A-bi-li mi ne gos yu.` = ABILITY(¬(I go))

They are **different** and cannot be interchanged. The inner proposition
must parse under strict canonical Core with overt required arguments.
Questions, imperatives, unspecified referent `sa`, quantifiers, tense/aspect
particles, subordinate clauses and nested modalities are rejected until their
modal scope is formalized. There is no natural-language predictive/causal
conditional interpretation.

## Design: narrow comparisons between exact comparable quantities

```ebnf
comparison = comparator, operand, "ve", operand, "yu" ;
comparator = "ga-val" | "ga-min" | "ga-pal" ;
operand = canonical_noun_root, "wen", canonical_digits, ["su", canonical_unit] ;
```

- `ga-val`: strictly greater than.
- `ga-min`: strictly less than.
- `ga-pal`: numerically equal to (not object identity).

The canonical number and unit parser is reused. Both operands must use
**the same accepted noun root** and **the same explicit unit** (or both
unitless). Compounds, modifiers, ownership, quantification, implicit unit
conversions and mixed dimensions are forbidden. Comparisons evaluate **only
the supplied literal numbers** using exact decimal arithmetic, including
retained fractional spellings. They do not independently measure water,
people or any other physical quantity.

Examples:

```text
Ga-val sil wen ran dis gel su wok ve sil wen ran su wok yu.
Ga-min ren wen ran ve ren wen kuk yu.
Ga-pal ren wen kuk ve ren wen kuk dis nul yu.
```

The first states that the literal quantity 1.5 liters of water is greater
than the literal quantity 1 liter of water. It does **not** assert that
any actual water samples have those volumes.

## CLI and compatibility

```sh
python3 -m veka modal-compare 'A-bi-li Mi gos yu.'
python3 -m veka modal-compare 'Na a-bi-li mi gos yu yu.'
python3 -m veka modal-compare 'A-bi-li mi ne gos yu.'
python3 -m veka modal-compare 'Ga-val sil wen ran dis gel su wok ve sil wen ran su wok yu.'
python3 -m veka modal-compare 'Po-si-bi Mi fok mel yu.' --profile toneless
```

The operator family is **deliberately separate** from `parse`, `logic`,
`extend`, `discourse` and `register-check`; those commands must still
reject unregistered constructions. The output identifies research status
and separately flags computed numeric truth, verification of real-world
facts, normative claims and human comprehension.

All six research markers use Veka-valid syllables and avoid undelimited
surface collisions with the canonical lexical headwords. This does not
prove the words are acoustically distinguishable: the written hyphens
are silent and some component syllables are established canonical roots.
There are no native-speaker recordings, listening tests or learning trials.

Before any canonical promotion, independent multilingual reviewers must
validate intended meanings and semantic scope; record speech and assess
error rates in quiet/noise; compare total training + production + repair
time with unmarked expressions; and publish versioned compatibility
migration. Until then **no canonical lexical or grammar change**.
