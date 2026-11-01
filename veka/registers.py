"""Opt-in Veka register policy: syntax provenance, never speaker-safety certification.

Core is the existing strict canonical atomic grammar. Precise additionally permits
canonical, fully scoped v0.3 propositional logic. Research permits the opt-in v0.5
and v0.6 parsers and the separate experimental toneless lexicon.

Nothing in this module changes parsing, word meanings, or the canonical lexicon.
"""
from __future__ import annotations

from .core import VekaError, parse
from .discourse import parse_discourse
from .extended import parse_extended
from .logic import parse_logic
from .profiles import PROFILES, load_profile

REGISTERS = ("core", "precise", "research")
PARSERS = (
    ("core", "atomic", parse),
    ("precise", "logic", parse_logic),
    ("research", "extended", parse_extended),
    ("research", "discourse", parse_discourse),
)


def _contains_material_if(node: object) -> bool:
    if isinstance(node, dict):
        if node.get("op") == "if":
            return True
        return any(_contains_material_if(value) for value in node.values())
    if isinstance(node, (list, tuple)):
        return any(_contains_material_if(value) for value in node)
    return False


def inspect_register(
    utterance: str, *, profile: str = "tonal", max_register: str = "core"
) -> dict:
    """Parse with the least experimental permitted grammar; fail closed.

    A caller requesting the research tier still learns whether its utterance
    actually uses core or precise grammar. A toneless lexicon always makes the
    *effective* register research, even when its sentence grammar is canonical.
    """
    if max_register not in REGISTERS:
        raise VekaError(f"unknown maximum register: {max_register!r}")
    if profile not in PROFILES:
        raise VekaError(f"unsupported vocabulary profile: {profile!r}")
    if profile != "tonal" and max_register != "research":
        raise VekaError("toneless lexicon is research-only; use --max-register research")
    if not isinstance(utterance, str) or not utterance.strip():
        raise VekaError("utterance must be nonempty text")

    lex = load_profile(profile)
    permitted = set(REGISTERS[: REGISTERS.index(max_register) + 1])
    for tier, parser_name, parser in PARSERS:
        if tier not in permitted:
            continue
        try:
            if parser_name in ("atomic", "logic", "extended"):
                parsed = parser(utterance, lex, strict=True)
            else:
                parsed = parser(utterance, lex)
        except VekaError:
            continue
        # A bare atom in the logic parser must not be promoted to a distinct
        # precise interpretation. The canonical strict atomic path owns it.
        if parser_name == "logic" and parsed.get("op") == "atom":
            continue

        effective = "research" if profile != "tonal" else tier
        limitations = [
            "Only machine-tested syntax; no measured human comprehension or speech efficiency.",
            "Parser acceptance does not certify real-world truth or communication safety.",
        ]
        if _contains_material_if(parsed):
            limitations.append(
                "The formal fi operator is material implication, not a causal or counterfactual if."
            )
        if tier == "research":
            limitations.append(
                "The v0.5/v0.6 grammar is opt-in research, not canonical Veka."
            )
        if profile != "tonal":
            limitations.append(
                "The toneless lexicon is an unvalidated experimental substitution set."
            )
        return {
            "schema_version": "veka.register-check.v08",
            "utterance": utterance,
            "register": effective,
            "grammar_register": tier,
            "allowed_through": max_register,
            "parser": parser_name,
            "profile": profile,
            "canonical_grammar": tier != "research",
            "canonical_lexicon": profile == "tonal",
            "human_comprehension_validated": False,
            "communication_safety_certified": False,
            "limitations": limitations,
            "ast": parsed,
        }
    raise VekaError(
        f"utterance not accepted in {max_register!r} register: "
        "unknown form, unsupported syntax, missing argument, or unlicensed scope"
    )
