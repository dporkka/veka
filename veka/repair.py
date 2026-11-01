"""Opt-in exact-quotation and conversation-repair grammar research.

No canonical lexemes, grammar rules or independently understood meanings are
created here. All quoted utterances must parse strictly under canonical core
syntax; repair references must be anchored to a supplied, matching prior AST.
"""
from __future__ import annotations

import unicodedata

from .core import Lexicon, VekaError, parse, validate_word

MARKERS = {
    "re-pe-ta": "repetition_request",
    "kon-fi-ra": "confirmation_request",
    "ko-re-ta": "correction",
    "ko-ta-ra": "quotation",
}
CLOSE = "yu"
DEFAULT_MAX_WORDS = 96


def _tokens(text: str, max_words: int) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        raise VekaError("repair utterance must be nonempty text")
    s = unicodedata.normalize("NFC", text.strip())
    if s[-1] in ".?!":
        s = s[:-1]
    if not s or any(char in s for char in ".?!"):
        raise VekaError("repair utterance permits only one optional terminal punctuation mark")
    words = s.split()
    if len(words) > max_words:
        raise VekaError("repair utterance exceeds word bound")
    return words


def _core_quote(words: list[str], lex: Lexicon) -> dict:
    if not words:
        raise VekaError("empty quoted clause")
    if any(token.casefold() in MARKERS or token.casefold() == CLOSE for token in words):
        raise VekaError("nested or unclosed repair quotation")
    try:
        result = parse(" ".join(words), lex, strict=True)
    except VekaError as exc:
        raise VekaError(f"quoted clause must be strict canonical core: {exc}") from exc
    if result["mood"] != "statement":
        raise VekaError("quotation of imperative commands is not supported")
    return {"surface": " ".join(words), "ast": result,
            "canonical_core_syntax": True}


def _verified_prior(prior: str | None, quoted: dict, lex: Lexicon,
                    max_words: int) -> bool:
    if prior is None:
        raise VekaError("repair request/correction requires explicit prior utterance")
    words = _tokens(prior, max_words)
    old = _core_quote(words, lex)
    if old["ast"] != quoted["ast"]:
        raise VekaError("quoted source does not match the supplied prior utterance")
    return True


def parse_repair(text: str, lex: Lexicon, *, prior: str | None = None,
                 max_words: int = DEFAULT_MAX_WORDS) -> dict:
    """Parse a structurally explicit research repair, never infer speaker intent.

    Syntax:
      ko-ta-ra clause yu                      quote, no assertion
      re-pe-ta clause yu                      request repeat of matching prior
      kon-fi-ra clause yu                     request confirm matching prior
      ko-re-ta source yu replacement yu       propose explicit correction
    """
    if isinstance(max_words, bool) or not isinstance(max_words, int) or not 3 <= max_words <= 128:
        raise VekaError("max_words must be integer 3..128")
    if not isinstance(lex, Lexicon):
        raise VekaError("repair parser needs an explicit Veka lexicon")
    if not all(validate_word(k) and k not in lex for k in MARKERS):
        raise VekaError("repair markers must be noncanonical, phonotactically legal words")
    if len({marker.replace("-", "") for marker in MARKERS}) != len(MARKERS):
        raise VekaError("repair markers collide without spoken hyphens")

    words = _tokens(text, max_words)
    opener = words[0].lower()
    if opener not in MARKERS:
        raise VekaError("unknown repair operator")
    act = MARKERS[opener]
    closers = [index for index, word in enumerate(words) if word.lower() == CLOSE]
    expected = 2 if act == "correction" else 1
    if len(closers) != expected or closers[-1] != len(words) - 1:
        raise VekaError("repair requires exactly one yu per quoted clause at its end")
    source = _core_quote(words[1:closers[0]], lex)

    if act == "quotation":
        if prior is not None:
            raise VekaError("standalone quotation must not claim linkage to a prior turn")
        bound = False
        replacement = None
    else:
        bound = _verified_prior(prior, source, lex, max_words)
        replacement = None
        if act == "correction":
            if source["ast"]["question"]:
                raise VekaError("correction of a question is unsupported; quote an assertion")
            replacement = _core_quote(words[closers[0] + 1:closers[1]], lex)
            if replacement["ast"]["question"]:
                raise VekaError("correction replacement must be an assertion")
            if source["ast"] == replacement["ast"]:
                raise VekaError("correction must change a parsed proposition")

    result = {
        "schema_version": "veka.repair.v01",
        "register": "research",
        "operator": opener,
        "act": act,
        "quote": source,
        "quoted_prior_verified": bound,
        "quoted_prior_comparison": "strict core AST equality" if bound else None,
        "asserts_quoted_proposition": False,
        "canonical_grammar_changed": False,
        "canonical_lexicon_changed": False,
        "human_comprehension_validated": False,
        "spoken_comprehension_validated": False,
        "pragmatic_intent_verified": False,
        "limitations": [
            "An overt formal protocol, not adopted Veka conversational grammar.",
            "A matching prior AST does not prove shared human understanding or intended reference.",
            "Hyphens are silent; spoken segmentation and marker intelligibility remain untested.",
        ],
    }
    if replacement is not None:
        result.update({
            "replacement": replacement,
            "scope_sequence": ["quoted_prior", "replacement"],
            "source_asserted": False,
            "replacement_proposition_presented": True,
            "replacement_truth_verified": False,
        })
    return result
