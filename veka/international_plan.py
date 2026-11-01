"""Explicitly hypothetical 100-concept international-root research plan.

Never changes the canonical lexicon, accepted grammar, or parser profiles.
Editor-assigned exposure tiers are only a prioritization heuristic, not
corpus frequencies, recognition probabilities, or empirical superiority.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from .core import Lexicon, VekaError
from .lexical_readiness import build_lexical_readiness

PRIORITY_COLUMNS = ("concept_id", "exposure_tier", "review_note")
VERSION = "veka.international-plan.v10"


def read_review_priorities(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != PRIORITY_COLUMNS:
            raise VekaError("international priorities require concept_id,exposure_tier,review_note")
        rows = list(reader)
        if not rows or any(None in row or any(not isinstance(row.get(k), str)
                                             for k in PRIORITY_COLUMNS) for row in rows):
            raise VekaError("invalid international priority rows")
        return rows


def build_international_plan(candidates: list[dict], lex: Lexicon,
                             priorities: list[dict], evidence: list[dict]) -> dict:
    """Audit a full research queue; never rank *word quality* or authorize adoption."""
    if not candidates or len(candidates) != len(priorities):
        raise VekaError("one review-priority row required per research concept")
    priority_by_id = {}
    for row in priorities:
        if not set(PRIORITY_COLUMNS).issubset(row):
            raise VekaError("invalid international review priority")
        cid = row["concept_id"]
        if not cid or cid in priority_by_id or not row["review_note"].strip():
            raise VekaError("duplicate, empty or unexplained international priority")
        try:
            tier = int(row["exposure_tier"])
        except (TypeError, ValueError) as exc:
            raise VekaError(f"invalid exposure tier for {cid}") from exc
        if str(tier) != row["exposure_tier"] or not 1 <= tier <= 5:
            raise VekaError(f"exposure tier must be an integer 1..5: {cid}")
        priority_by_id[cid] = (tier, row["review_note"])
    candidate_ids = {row["concept_id"] for row in candidates}
    if len(candidate_ids) != len(candidates) or set(priority_by_id) != candidate_ids:
        raise VekaError("review priorities must match the full unique concept queue")

    # Reuse existing strict canonical mappings, phonotactics, evidence and review gates.
    readiness = build_lexical_readiness(candidates, lex, evidence, [])
    compounds_by_root = Counter()
    for entry in lex.values():
        if entry.kind == "compound":
            compounds_by_root[entry.head] += 1
            compounds_by_root[entry.modifier] += 1

    # The written compound hyphen is silent. Flag identical undelimited
    # surface strings, including differing hypothetical syllable partitions.
    # This is a text-only proxy, NOT an acoustic confusion measurement.
    by_surface = defaultdict(set)
    for form in lex:
        by_surface[form.replace("-", "")].add(form)
    for item in readiness["candidates"]:
        form = item["candidate_form"]
        if form:
            by_surface[form.replace("-", "")].add(form)

    queue = []
    for item in readiness["candidates"]:
        cid = item["concept_id"]
        tier, note = priority_by_id[cid]
        affected = compounds_by_root[item["core_form"]]
        extra = item["added_syllables_vs_core"]
        form = item["candidate_form"]
        collisions = sorted(by_surface[form.replace("-", "")] - {form}) if form else []
        action = ("repair_spoken_surface_collision" if collisions
                  else item["next_action"])
        # Editorial sampling ORDER only. Not a likelihood, utility or acceptance score.
        priority = tier * 100 - max(0, extra or 0) * 10 - affected * 3
        queue.append({
            "concept_id": cid, "gloss": item["gloss"],
            "core_form": item["core_form"],
            "candidate_form": item["candidate_form"],
            "structural_status": item["structural_status"],
            "structural_reasons": item["structural_reasons"],
            "added_syllables_vs_core": extra,
            "existing_compounds_affected": affected,
            "assumed_exposure_tier": tier,
            "editorial_review_note": note,
            "review_priority": priority,
            "next_action": action,
            "spoken_surface_collisions": collisions,
            "verified_families": item["verified_families"],
            "recognition_measured": False,
            "predicted_comprehension_rate": None,
            "false_friend_review_required": bool(item["candidate_form"]),
            "adoption_authorized": False,
        })
    queue.sort(key=lambda r: (-r["review_priority"], r["concept_id"]))
    return {
        "schema_version": VERSION, "concept_count": len(queue),
        "draft_count": sum(bool(r["candidate_form"]) for r in queue),
        "rejected_drafts": sum(r["structural_status"] == "rejected" for r in queue),
        "not_proposed": sum(r["structural_status"] == "not_proposed" for r in queue),
        "next_actions": dict(sorted(Counter(r["next_action"] for r in queue).items())),
        "canonical_root_count": sum(e.kind == "root" for e in lex.values()),
        "canonical_compound_count": sum(e.kind == "compound" for e in lex.values()),
        "canonical_changes": 0, "adoption_authorized": False,
        "human_benefit_established": False, "frequency_measured": False,
        "editorial_priority_only": True,
        "queue": queue,
        "warning": (
            "All loanword forms are unverified hypotheses. Exposure tiers are subjective; "
            "verified donor attestations and multilingual first-sight, delayed-retention, "
            "pronunciation and speech-in-noise studies are required. "
            "Undelimited spelling overlaps are structural proxies, not measured acoustic confusion. "
            "No form is accepted by the parser or eligible for automatic adoption."
        ),
    }
