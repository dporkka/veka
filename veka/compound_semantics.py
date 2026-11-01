"""Editorial audit for Veka noun-adjective compound/phrase surface equivalence.

This is NOT a semantic-equivalence classifier or a listener study.
No speech marker, lexeme, or canonical grammar rule is changed.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .core import Lexicon, VekaError
from .compounds import normalize_nominal_surface

SCHEMA_VERSION = "veka.compound-semantics.v06"
CLASSIFICATIONS = frozenset({"compositional_alias", "potential_lexicalization"})
REVIEW_FIELDS = ["compound", "classification", "evidence_note"]


def _compounds(lex: Lexicon) -> list:
    compounds = sorted(
        (e for e in lex.values() if e.kind == "compound"),
        key=lambda e: e.form,
    )
    for entry in compounds:
        head = lex.get(entry.head)
        modifier = lex.get(entry.modifier)
        if (head is None or head.pos != "noun" or modifier is None
                or modifier.pos != "adjective"
                or entry.form != f"{entry.head}-{entry.modifier}"):
            raise VekaError(f"compound lacks unique noun-adjective analysis: {entry.form}")
        if (normalize_nominal_surface(entry.form, lex)
                != normalize_nominal_surface(f"{entry.head} {entry.modifier}", lex)):
            raise VekaError(f"compound violates canonical surface alias: {entry.form}")
    return compounds


def load_compound_reviews(path: str | Path, lex: Lexicon) -> dict[str, dict]:
    """Load explicit editorial hypotheses; never infer human comprehension.

    Each review classifies one EXISTING compound. A reviewer must record a
    rationale, including when treating a lexicalized gloss as a semantic alias.
    """
    allowed = {entry.form for entry in _compounds(lex)}
    reviews: dict[str, dict] = {}
    try:
        with Path(path).open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != REVIEW_FIELDS:
                raise VekaError("compound review requires compound,classification,evidence_note")
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise VekaError("compound review contains malformed CSV fields")
                name = row["compound"]
                classification = row["classification"]
                note = row["evidence_note"].strip()
                if name not in allowed or name in reviews:
                    raise VekaError(f"duplicate or unknown compound review: {name}")
                if classification not in CLASSIFICATIONS or not note:
                    raise VekaError(f"invalid classification or missing rationale: {name}")
                reviews[name] = {"classification": classification, "evidence_note": note}
    except UnicodeError as exc:
        raise VekaError("compound review must use UTF-8") from exc
    return reviews


def audit_compound_semantics(
    lex: Lexicon, reviews: dict[str, dict] | None = None, *,
    top: int | None = None,
) -> dict:
    """Describe each written/spoken coincidence without guessing semantic identity."""
    if top is not None and (type(top) is not int or not 0 <= top <= 10000):
        raise VekaError("top must be 0..10000")
    compounds = _compounds(lex)
    supplied = {} if reviews is None else reviews
    known = {e.form for e in compounds}
    if set(supplied) - known:
        raise VekaError("review contains unknown canonical compound")
    items = []
    reviewed = 0
    for entry in compounds:
        review = supplied.get(entry.form)
        if review is not None:
            if not isinstance(review, dict):
                raise VekaError("review entry must be structured")
            classification = review.get("classification")
            note = review.get("evidence_note")
            if classification not in CLASSIFICATIONS or not isinstance(note, str) or not note.strip():
                raise VekaError(f"invalid review entry: {entry.form}")
            reviewed += 1
        else:
            classification, note = "unreviewed", ""
        semantic_alias = classification == "compositional_alias"
        items.append({
            "compound": entry.form,
            "spoken_form": f"{entry.head} {entry.modifier}",
            "dictionary_gloss": entry.gloss,
            "phrase_gloss": f"{lex[entry.modifier].gloss} {lex[entry.head].gloss}",
            "classification": classification,
            "evidence_note": note,
            "requires_context_for_distinct_meaning": not semantic_alias,
            "distinct_meaning_unverified": not semantic_alias,
            "human_listening_validated": False,
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "canonical_structural_policy": "compositional_alias",
        "total_compounds": len(compounds),
        "surface_equivalent_count": len(items),
        "reviewed_count": reviewed,
        "unreviewed_count": len(items) - reviewed,
        "items": items if top is None else items[:top],
        "human_listening_validated": False,
        "canonical_lexicon_modified": False,
        "warning": (
            "Editorial classifications are hypotheses, not audio/semantic evidence. "
            "Written hyphens have no specified audible boundary. "
            "An unreviewed phrase cannot be presumed to carry a distinct meaning."
        ),
    }
