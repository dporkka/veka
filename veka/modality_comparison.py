"""Research-only modal scope and comparable exact-decimal quantity statements.

Separate from all canonical and existing research parsers. Exposes syntax
structure, not real-world evidence, moral truth or speaker comprehension.
"""
from __future__ import annotations

from decimal import Decimal

from .core import Lexicon, VekaError, _normalize_sentence, parse, validate_word
from .numbers import parse_number_tokens

MODALS = {
    "a-bi-li": "dynamic_ability",
    "po-si-bi": "epistemic_possibility",
    "de-be-ri": "deontic_obligation",
}
COMPARATORS = {
    "ga-val": "greater_than",
    "ga-min": "less_than",
    "ga-pal": "equal_to",
}
UNITS = frozenset({"rel", "sek", "vos", "wok"})
CLOSE = "yu"
DIVIDER = "ve"
MAX_WORDS = 120


def _check_markers(lex: Lexicon) -> None:
    if not isinstance(lex, Lexicon):
        raise VekaError("explicit Veka lexical profile required")
    markers = {*MODALS, *COMPARATORS}
    lexical_surfaces = {form.replace("-", "") for form in lex}
    surfaces = [word.replace("-", "") for word in markers]
    if (not all(validate_word(word) for word in markers)
            or len(surfaces) != len(set(surfaces))
            or set(surfaces) & lexical_surfaces):
        raise VekaError("research marker collides with phonology or accepted vocabulary")


def _words(text: str) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        raise VekaError("empty modal/comparison utterance")
    if text.strip().endswith(("?", "!")):
        raise VekaError("modal/comparison grammar does not include spoken questions or commands")
    words = _normalize_sentence(text)
    if len(words) > MAX_WORDS:
        raise VekaError("research utterance exceeds word budget")
    return words  # preserve case for Unicode proper names in canonical clauses


def _assertive_core(words: list[str], lex: Lexicon) -> dict:
    if not words or any(w.lower() in {*MODALS, *COMPARATORS, CLOSE, DIVIDER} for w in words):
        raise VekaError("modal scope must contain one complete canonical core proposition")
    ast = parse(" ".join(words), lex, strict=True)
    if ast["mood"] != "statement" or ast["question"]:
        raise VekaError("modal scope must be assertive, not question or command")
    if ast["tense"] != "unspecified" or ast["progressive"]:
        raise VekaError("scope of temporal/aspect markers under modality is not defined")
    if any(ast.get(f"{role}_quantifier") is not None for role in
           ("subject", "object", "recipient", "location")):
        raise VekaError("scope of quantified phrases under modality is not defined")
    return ast


def _modal(words: list[str], lex: Lexicon) -> dict:
    outer_not = words[0].lower() == "na"
    start = 1 if outer_not else 0
    if len(words) <= start + 2 or words[start].lower() not in MODALS:
        raise VekaError("expected an explicit research modality operator")
    closers = [i for i, w in enumerate(words) if w.lower() == CLOSE]
    if (closers != ([len(words)-2, len(words)-1] if outer_not
                    else [len(words)-1])):
        raise VekaError("modality requires explicit yu; outer negation requires a second yu")
    ast = _assertive_core(words[start+1:closers[0]], lex)
    modality = MODALS[words[start].lower()]
    return {
        "kind": "modality",
        "operator": words[start].lower(),
        "modality": modality,
        "scope": {"kind": "canonical_assertion", "ast": ast},
        "negation_scope": ("outside_modality" if outer_not else
                           "inside_modality" if ast["negative"] else "none"),
        "semantics": {
            "modal": modality,
            "negation_outside_modal": outer_not,
            "negation_within_proposition": ast["negative"],
            "subject": ast["subject"],
        },
        "proposition_truth_verified": False,
        "modal_claim_verified": False,
        "normative_authority_established": False,
    }


def _numeric_operand(words: list[str], lex: Lexicon) -> dict:
    if len(words) < 3:
        raise VekaError("comparison operand needs a noun and exact numeral")
    noun = words[0]
    if noun not in lex or lex[noun].kind != "root" or lex[noun].pos != "noun":
        raise VekaError("comparison operand requires one canonical noun root")
    if words[1] != "wen":
        raise VekaError("comparison operand requires overt exact numeral marker wen")
    number, next_pos = parse_number_tokens(words, 1)
    remaining = words[next_pos:]
    if remaining and (len(remaining) != 2 or remaining[0] != "su"
                      or remaining[1] not in UNITS):
        raise VekaError("comparison operand requires at most one canonical unit")
    unit = remaining[1] if remaining else None
    # Reuse strict canonical grammar to enforce accepted numeric noun phrases;
    # the synthetic subject/predicate are validation scaffolding only.
    np = parse("Mi rin " + " ".join(words) + ".", lex, strict=True)
    if (np["object_quantity"] != number or np["object_unit"] != unit
            or np["object"] != " ".join(words)):
        raise VekaError("numeric operand is not a canonical exact noun phrase")
    return {"noun": noun, "number": number, "unit": unit}


def _comparison(words: list[str], lex: Lexicon) -> dict:
    words = [word.lower() for word in words]  # only strict canonical roots and decimal tokens
    if words[0] not in COMPARATORS:
        raise VekaError("expected an explicit comparison operator")
    if len(words) < 9 or words.count(DIVIDER) != 1 or words.count(CLOSE) != 1:
        raise VekaError("comparison requires two exact operands, one ve and one yu")
    if words[-1] != CLOSE:
        raise VekaError("comparison must end in yu")
    separator = words.index(DIVIDER)
    left = _numeric_operand(words[1:separator], lex)
    right = _numeric_operand(words[separator+1:-1], lex)
    if left["noun"] != right["noun"] or left["unit"] != right["unit"]:
        raise VekaError("cannot compare different noun concepts or measurement units")
    a, b = Decimal(left["number"]), Decimal(right["number"])
    relation = COMPARATORS[words[0]]
    holds = ((a > b) if relation == "greater_than" else
             (a < b) if relation == "less_than" else a == b)
    return {
        "kind": "quantity_comparison",
        "operator": words[0],
        "relation": relation,
        "left": left,
        "right": right,
        "numeric_relation_holds_for_literals": holds,
        "real_world_measurement_verified": False,
        "unit_conversion_performed": False,
        "comparable_dimensions_checked": True,
    }


def parse_modality_comparison(text: str, lex: Lexicon) -> dict:
    """Parse one explicit research construction; reject unsupported scope."""
    _check_markers(lex)
    words = _words(text)
    first = words[0].lower()
    if first in MODALS or first == "na":
        result = _modal(words, lex)
    elif first in COMPARATORS:
        result = _comparison(words, lex)
    else:
        raise VekaError("not a supported modal or comparison research utterance")
    return {
        "schema_version": "veka.modal-compare.v01",
        "register": "research",
        **result,
        "canonical_lexicon_changed": False,
        "canonical_grammar_changed": False,
        "human_comprehension_validated": False,
        "spoken_recognition_validated": False,
        "limitations": [
            "Research-only syntax, not accepted as canonical spoken Veka.",
            "No real-world truth, norm, physical measurement or speaker intention is established.",
            "Silent hyphens and marker intelligibility have not been tested with listeners.",
            "Only overt strictly parsed non-quantified single-clause modality and same-unit exact numeric comparisons are supported.",
        ],
    }
