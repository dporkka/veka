"""Research-only lexical risk audit for Veka 0.5.

All weights and distances are transparent DESIGN HEURISTICS, not phonetic,
corpus-frequency, intelligibility, or error-rate measurements. Neither this
module nor the CLI changes the canonical dictionary.
"""
from __future__ import annotations

import csv
import itertools
import math
from functools import lru_cache
from pathlib import Path

from .core import (
    CONSONANTS, CODAS, DIPHTHONGS, VOWELS,
    Lexicon, VekaError, _syllable_info, validate_word,
)

DEFAULT_PRIORITIES = Path(__file__).resolve().parents[1] / "data" / "lexical_priors_v05.csv"
SCHEMA_VERSION = "veka.lexical-risk.v05"
# Experiment parameters, not a model learned from human speech.
ONSET_COST = 1.35
NUCLEUS_COST = 1.75
CODA_COST = 0.80
TONE_COST = 0.60
SIMILARITY_RADIUS = 2.75


def load_priorities(path: str | Path, lex: Lexicon) -> dict[str, float]:
    """Import bounded, explicitly assumed exposure/consequence scores.

    Default 1x1 for unlisted ROOTS. Reject malformed and ambiguous inputs.
    Multiplies assumed exposure by assumed consequence, without claiming
    these are corpus frequencies or measured harms.
    """
    weights = {e.form: 1.0 for e in lex.values() if e.kind == "root"}
    try:
        with Path(path).open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != ["form", "exposure", "consequence"]:
                raise VekaError("lexical priority CSV requires form,exposure,consequence")
            seen = set()
            for row in reader:
                form = row["form"]
                if form in seen or form not in weights:
                    raise VekaError(f"duplicate, unknown or non-root priority: {form}")
                seen.add(form)
                try:
                    a, b = (int(row[k]) for k in ("exposure", "consequence"))
                except (ValueError, TypeError, KeyError) as exc:
                    raise VekaError(f"noninteger lexical priority: {form}") from exc
                if not 1 <= a <= 10 or not 1 <= b <= 10:
                    raise VekaError(f"lexical priority outside 1..10: {form}")
                weights[form] = float(a * b)
    except UnicodeError as exc:
        raise VekaError("priority file encoding is not valid UTF-8") from exc
    return weights


@lru_cache(maxsize=8192)
def contrast_distance(a: str, b: str) -> float:
    """Transparent surface-feature distance for two canonical syllables.

    These are symbolic onset/nucleus/coda/tone units, not measured
    perceptual distances. Especially do NOT interpret this as an
    acoustic confusability or speech-recognition probability.
    """
    x, y = _syllable_info(a), _syllable_info(b)
    return (ONSET_COST * (x[0] != y[0])
            + NUCLEUS_COST * (x[1] != y[1])
            + CODA_COST * (x[2] != y[2])
            + TONE_COST * (x[3] != y[3]))


def _pair_penalty(a: str, b: str, weights: dict[str, float]) -> float:
    distance = contrast_distance(a, b)
    proximity = max(0.0, 1.0 - distance / SIMILARITY_RADIUS)
    return math.sqrt(weights.get(a, 1.0) * weights.get(b, 1.0)) * proximity ** 2


def _root_forms(lex: Lexicon) -> list[str]:
    return sorted(e.form for e in lex.values() if e.kind == "root")


def _candidate_forms(lex: Lexicon):
    occupied = set(lex)
    occupied_plain = {form.translate(str.maketrans("áéíóú", "aeiou"))
                      for form in occupied if "-" not in form}
    for onset, nucleus, coda in itertools.product(
            ("", *CONSONANTS), (*VOWELS, *DIPHTHONGS), CODAS):
        candidate = onset + nucleus + coda
        if candidate not in occupied_plain and candidate not in occupied and validate_word(candidate):
            yield candidate


def _articulation_proxy(form: str) -> float:
    """Tie-breaker heuristic; NOT measured milliseconds or speaking effort."""
    onset, nucleus, coda, _ = _syllable_info(form)
    return (0.15 * (not onset) + 0.20 * (nucleus in DIPHTHONGS)
            + 0.15 * bool(coda))


def propose_replacements(lex: Lexicon, weights: dict[str, float],
                         target: str, limit: int = 5) -> list[dict]:
    """Generate isolated, NOT adopted, candidate forms for one primitive root.

    Each candidate is compared with the UNCHANGED lexicon and cannot be
    combined with other proposals without a fresh global collision audit.
    Existing compounds referencing the root would need a migration.
    """
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise VekaError("candidate limit must be 1..100")
    if target not in lex or lex[target].kind != "root":
        raise VekaError(f"replacement target must be an existing root: {target}")
    others = [f for f in _root_forms(lex) if f != target]
    # Crucially, the NEW candidate inherits target's assumed priority.
    weight = weights.get(target, 1.0)
    current_penalty = sum(_pair_penalty(target, other, weights) for other in others)
    proposals = []
    compound_impact = sum(e.kind == "compound" and
                          target in (e.head, e.modifier) for e in lex.values())
    for form in _candidate_forms(lex):
        candidate_weights = dict(weights)
        candidate_weights[form] = weight
        proposed_penalty = sum(_pair_penalty(form, other, candidate_weights) for other in others)
        proposed_penalty += _articulation_proxy(form) * 0.20 * weight
        improvement = current_penalty - proposed_penalty
        if improvement <= 1e-9:
            continue
        proposals.append({
            "candidate": form,
            "current_structural_penalty": round(current_penalty, 5),
            "candidate_structural_penalty": round(proposed_penalty, 5),
            "structural_gain": round(improvement, 5),
            "affected_existing_compounds": compound_impact,
            "human_validated": False,
            "canonical": False,
        })
    proposals.sort(key=lambda row: (-row["structural_gain"], row["candidate"]))
    return proposals[:limit]


def audit_compound_surfaces(lex: Lexicon, sample_limit: int = 5) -> dict:
    """Audit cases where lexical compound and noun+adjective phrase sound alike.

    No audible hyphen is specified, so these share segmental sequences.
    That does not imply divergent meanings or proven comprehension errors.
    """
    if not isinstance(sample_limit, int) or not 0 <= sample_limit <= 10000:
        raise VekaError("sample_limit must be 0..10000")
    compounds = [e for e in lex.values() if e.kind == "compound"]
    examples = []
    for e in compounds:
        if (e.head in lex and e.modifier in lex
                and lex[e.head].pos == "noun" and lex[e.modifier].pos == "adjective"
                and e.form == e.head + "-" + e.modifier):
            examples.append({"compound": e.form, "spoken_tokens": e.head + " " + e.modifier,
                             "interpretation": "lexical noun or ordinary noun-adjective phrase"})
    return {"compounds": len(compounds),
            "noun_adjective_surface_equivalents": len(examples),
            "examples": examples[:sample_limit],
            "spoken_word_boundaries_tested": False,
            "meaning_conflicts_established": 0,
            "warning": "A silent hyphen is not an audible boundary; surface equivalence alone does not prove semantic ambiguity."}


def audit_lexical_risk(lex: Lexicon, weights: dict[str, float], *,
                       targets: list[str] | None = None,
                       top: int = 10, candidates: int = 5,
                       profile: str | None = None) -> dict:
    """Rank prioritized near pairs and trial substitutions; never alter lex."""
    if not isinstance(top, int) or not 0 <= top <= 100:
        raise VekaError("top must be 0..100")
    if not isinstance(candidates, int) or not 1 <= candidates <= 100:
        raise VekaError("candidates must be 1..100")
    target_names = ["mi", "ne", "ran"] if targets is None else targets
    if len(set(target_names)) != len(target_names) or len(target_names) > 20:
        raise VekaError("targets must be unique, up to 20")
    roots = _root_forms(lex)
    ranked = []
    total = 0.0
    for a, b in itertools.combinations(roots, 2):
        penalty = _pair_penalty(a, b, weights)
        total += penalty
        if penalty > 0:
            ranked.append({"a": a, "b": b,
                           "symbolic_distance": round(contrast_distance(a, b), 4),
                           "weighted_structural_penalty": round(penalty, 5)})
    ranked.sort(key=lambda r: (-r["weighted_structural_penalty"], r["a"], r["b"]))
    proposals = {target: propose_replacements(lex, weights, target, candidates)
                 for target in target_names}
    chosen_profile = profile or ("tonal" if any(
        any(mark in form for mark in "áéíóú") for form in roots) else "toneless")
    return {
        "schema_version": SCHEMA_VERSION,
        "profile": chosen_profile,
        "root_count": len(roots),
        "assumed_priority_rows": sum(weights.get(word, 1.0) != 1 for word in roots),
        "total_structural_penalty": round(total, 5),
        "scored_near_pairs": len(ranked),
        "top_risk_pairs": ranked[:top],
        "proposals": proposals,
        "compound_surfaces": audit_compound_surfaces(lex),
        "acoustically_validated": False,
        "frequency_measured": False,
        "human_participants": 0,
        "canonical_lexicon_modified": False,
        "warning": "Only symbolic structural screening with assumed priorities. Not speech data, lexical frequency, perceptual error, global optimization, or permission to adopt proposals.",
    }
