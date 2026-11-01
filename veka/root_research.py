"""Read-only atomic-root inventory and hypothetical international-form scenarios.

Never changes the lexicon, interprets simulated responses as real trials, or
authorizes adopting an international candidate.
"""
from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path

from .core import Lexicon, VekaError
from .international import audit_candidates

SCHEMA = "veka.root-research.v11"
PROTECTED_POS = frozenset({"pronoun", "particle", "digit", "unit", "time"})
WEIGHTS_PERCENT = {
    "recognition_acquisition": 35,
    "pronunciation_listening": 25,
    "compactness": 15,
    "semantic_clarity": 15,
    "cross_family_access": 10,
}
SCENARIO_COLUMNS = ("concept_id", "condition", "form", *WEIGHTS_PERCENT,
                    "critical_error_count", "scenario_note")


def build_root_inventory(lex: Lexicon, rows: list[dict]) -> dict:
    """Cover every root and dependency without assuming word frequency."""
    audit = audit_candidates(rows, lex)
    by_concept = {item["concept_id"]: item for item in audit["candidates"]}
    queue_by_root = {}
    for row in rows:
        form = row["core_form"]
        if form in queue_by_root:
            raise VekaError(f"duplicate research mapping for root: {form}")
        queue_by_root[form] = row

    head, modifier = Counter(), Counter()
    for entry in lex.values():
        if entry.kind != "compound":
            continue
        if (entry.head not in lex or entry.modifier not in lex
                or lex[entry.head].kind != "root"
                or lex[entry.modifier].kind != "root"):
            raise VekaError(f"compound has unresolved root: {entry.form}")
        head[entry.head] += 1
        modifier[entry.modifier] += 1

    roots = []
    for entry in sorted(lex.values(), key=lambda e: e.form):
        if entry.kind != "root":
            continue
        queued = queue_by_root.get(entry.form)
        candidate = by_concept.get(queued["concept_id"]) if queued else None
        if entry.pos in PROTECTED_POS:
            if queued:
                raise VekaError(f"structural root in replacement queue: {entry.form}")
            status = "protected_structural"
        elif not queued:
            status = "not_queued"
        elif candidate and candidate["status"] == "rejected":
            status = "repair_draft"
        elif candidate:
            status = "draft_needs_evidence"
        else:
            status = "needs_proposal"
        roots.append({
            "form": entry.form, "gloss": entry.gloss, "pos": entry.pos,
            "research_status": status,
            "concept_id": queued["concept_id"] if queued else None,
            "candidate_form": candidate["candidate_form"] if candidate else None,
            "candidate_structural_reasons": candidate["reasons"] if candidate else [],
            "head_compounds": head[entry.form],
            "modifier_compounds": modifier[entry.form],
            "dependent_compounds": head[entry.form] + modifier[entry.form],
            "migration_required_if_replaced": bool(head[entry.form] or modifier[entry.form]),
            "frequency_measured": False,
            "human_recognition_measured": False,
        })
    return {
        "schema_version": SCHEMA,
        "canonical_roots": len(roots),
        "canonical_compounds": sum(e.kind == "compound" for e in lex.values()),
        "queued_roots": len(queue_by_root),
        "unmapped_roots": len(roots) - len(queue_by_root),
        "proposed_candidates": sum(bool(row["candidate_form"]) for row in rows),
        "statuses": dict(sorted(Counter(r["research_status"] for r in roots).items())),
        "roots": roots,
        "canonical_changes": 0,
        "adoption_authorized": False,
        "warning": (
            "Coverage and compound dependencies are mechanical facts. Queue presence "
            "does not establish frequency, cross-language familiarity or superior "
            "human comprehension. No existing root is redefined."
        ),
    }


def read_scenarios(path: str | Path) -> list[dict]:
    """Read optional researcher-authored assumptions, not empirical results."""
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != SCENARIO_COLUMNS:
            raise VekaError("invalid scenario CSV headers; use the documented template")
        rows = list(reader)
    if any(None in row or any(not isinstance(row.get(k), str) for k in SCENARIO_COLUMNS)
           for row in rows):
        raise VekaError("incomplete scenario row")
    return rows


def _score(row: dict) -> dict:
    if not set(SCENARIO_COLUMNS).issubset(row):
        raise VekaError("scenario row missing required fields")
    if any(not isinstance(row[k], str) for k in SCENARIO_COLUMNS):
        raise VekaError("scenario values must be strings")
    if not row["scenario_note"].strip():
        raise VekaError("each scenario needs an explicit assumption note")
    factors = {}
    for name in WEIGHTS_PERCENT:
        try:
            value = float(row[name])
        except ValueError as exc:
            raise VekaError(f"invalid scenario factor: {name}") from exc
        if not math.isfinite(value) or not 0 <= value <= 100:
            raise VekaError(f"scenario factor must be finite 0..100: {name}")
        factors[name] = value
    if not row["critical_error_count"].isdecimal():
        raise VekaError("critical error count must be a nonnegative integer")
    return {
        "weighted": round(sum(factors[k] * w / 100 for k, w in WEIGHTS_PERCENT.items()), 4),
        "critical": int(row["critical_error_count"]),
        "note": row["scenario_note"].strip(),
    }


def compare_scenarios(rows: list[dict], lex: Lexicon, candidates: list[dict]) -> dict:
    """Rank explicitly hypothetical scenario deltas, never empirical benefit."""
    audited = audit_candidates(candidates, lex)
    valid = {r["concept_id"]: r for r in audited["candidates"]
             if r["status"] == "structurally_testable"}
    paired = {}
    for row in rows:
        if not set(SCENARIO_COLUMNS).issubset(row):
            raise VekaError("incomplete scenario")
        cid, condition = row["concept_id"], row["condition"]
        if cid not in valid:
            raise VekaError(f"unknown or invalid candidate: {cid}")
        if condition not in ("core", "candidate"):
            raise VekaError("condition must be core or candidate")
        expected = valid[cid]["core_form" if condition == "core" else "candidate_form"]
        if row["form"] != expected:
            raise VekaError(f"scenario form contradicts canonical mapping: {cid}")
        target = paired.setdefault(cid, {})
        if condition in target:
            raise VekaError(f"duplicate scenario condition: {cid}/{condition}")
        target[condition] = _score(row)

    comparisons = []
    for cid, pair in paired.items():
        if set(pair) != {"core", "candidate"}:
            raise VekaError(f"both comparison conditions required: {cid}")
        core, candidate = pair["core"], pair["candidate"]
        comparisons.append({
            "concept_id": cid,
            "core_form": valid[cid]["core_form"],
            "candidate_form": valid[cid]["candidate_form"],
            "added_syllables_vs_core": valid[cid]["added_syllables_vs_core"],
            "core_hypothetical_score": core["weighted"],
            "candidate_hypothetical_score": candidate["weighted"],
            "delta_points": round(candidate["weighted"] - core["weighted"], 4),
            "research_gate": "critical_error_review" if candidate["critical"] else "scenario_only",
            "critical_error_count_assumed": candidate["critical"],
            "assumptions": {"core": core["note"], "candidate": candidate["note"]},
            "human_benefit_established": False, "adoption_authorized": False,
        })
    comparisons.sort(key=lambda r: (-r["delta_points"], r["concept_id"]))
    return {
        "schema_version": "veka.root-scenario.v11",
        "weights_percent": WEIGHTS_PERCENT,
        "comparisons": comparisons,
        "evidence_observed": False,
        "human_benefit_established": False,
        "canonical_changes": 0,
        "adoption_authorized": False,
        "warning": (
            "User-authored scenario factors are uncalibrated assumptions, not recorded "
            "learner data or predicted recognition. Positive deltas do not justify "
            "lexicon changes; critical errors require independent review."
        ),
    }
