"""Veka 0.7: audited cross-family evidence and descriptive *observed* trials.

Neither donor evidence nor this scorer proves first-sight comprehension or
authorizes canonical vocabulary changes. No network or external dependencies.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

from .core import Lexicon, VekaError
from .international import audit_candidates

EVIDENCE_FIELDS = (
    "concept_id", "candidate_form", "language", "language_family",
    "language_branch", "attested_form", "source_url", "semantic_reviewer",
    "attestation_verified", "semantic_equivalent", "notes",
)
TRIAL_FIELDS = (
    "participant_id", "language_background_family", "concept_id",
    "condition", "correct", "elapsed_ms", "repair_ms", "critical_error",
)


def read_global_csv(path: str | Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    """Reject schema drift, malformed rows, and silently truncated records."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != fields:
                raise VekaError(f"incorrect CSV schema: {path}")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError(f"cannot read global study CSV: {path}") from exc
    if any(set(row) != set(fields) or
           any(not isinstance(row[key], str) for key in fields)
           for row in rows):
        raise VekaError("malformed global study CSV row")
    return rows


def _sourced(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("https", "http") and bool(parsed.netloc) and not parsed.username
    except ValueError:
        return False


def audit_global_candidates(candidates: list[dict], lex: Lexicon,
                            evidence: list[dict]) -> dict:
    """Verify structural constraints and count independently labeled families.

    Language-family and semantic verification remain manual reviewer assertions.
    An Indo-European word in 10 languages still counts as ONE family.
    """
    structural = audit_candidates(candidates, lex)
    usable = {
        row["concept_id"]: row for row in structural["candidates"]
        if row["status"] == "structurally_testable"
    }
    by_candidate = defaultdict(list)
    seen = set()
    for row in evidence:
        if not isinstance(row, dict) or set(row) != set(EVIDENCE_FIELDS):
            raise VekaError("invalid global evidence columns")
        if any(not isinstance(v, str) for v in row.values()):
            raise VekaError("invalid global evidence value")
        cid = row["concept_id"]
        if cid not in usable or row["candidate_form"] != usable[cid]["candidate_form"]:
            raise VekaError("global evidence does not match a structurally testable candidate")
        if any(not row[field].strip() for field in (
            "language", "language_family", "language_branch", "attested_form"
        )):
            raise VekaError("language, family, branch and attested form are required")
        if row["attestation_verified"] not in ("yes", "no"):
            raise VekaError("attestation_verified must be yes or no")
        if row["semantic_equivalent"] not in ("yes", "no", "unknown"):
            raise VekaError("invalid semantic equivalence state")
        ident = (cid, row["language"].strip().casefold())
        if ident in seen:
            raise VekaError("duplicate concept-language attestation")
        seen.add(ident)
        if row["attestation_verified"] == "yes":
            if (not _sourced(row["source_url"]) or
                not row["semantic_reviewer"].strip() or
                row["semantic_equivalent"] == "unknown"):
                raise VekaError("verified attestation requires a URL, reviewer, and semantic decision")
        if row["attestation_verified"] == "yes" and row["semantic_equivalent"] == "yes":
            by_candidate[cid].append(row)

    detail = {}
    for cid, candidate in sorted(usable.items()):
        matched = by_candidate[cid]
        families = {r["language_family"].strip().casefold() for r in matched}
        branches = {
            (r["language_family"].strip().casefold(),
             r["language_branch"].strip().casefold()) for r in matched
        }
        detail[cid] = {
            "gloss": candidate["gloss"],
            "core_form": candidate["core_form"],
            "candidate_form": candidate["candidate_form"],
            "extra_syllables": candidate["added_syllables_vs_core"],
            "verified_languages": len(matched),
            "verified_families": len(families),
            "verified_branches": len(branches),
            "family_labels": sorted(families),
            "recognition_measured": False,
        }
    return {
        "schema_version": "veka.global.v07",
        "candidate_count": len(usable),
        "evidence_records": len(evidence),
        "verified_attestations": sum(len(v) for v in by_candidate.values()),
        "candidates": detail,
        "recognition_measured": False,
        "eligible_for_adoption": False,
        "warning": ("Sources, language families, and semantic equivalence are reviewer claims; "
                    "attestation does not establish first-sight or spoken comprehension. "
                    "No vocabulary change is authorized."),
    }


def _trial_number(value: str, *, positive: bool) -> int:
    if not value.isascii() or not value.isdecimal():
        raise VekaError("duration must be a nonnegative integer in milliseconds")
    n = int(value)
    if n <= 0 if positive else n < 0:
        raise VekaError("duration outside allowed range")
    return n


def _stats(rows: list[dict]) -> dict:
    count = len(rows)
    correct = sum(row["correct"] for row in rows)
    critical = sum(row["critical_error"] for row in rows)
    total_ms = sum(row["duration_ms"] for row in rows)
    return {
        "trials": count, "correct": correct,
        "critical_errors": critical, "total_ms": total_ms,
        "accuracy": correct / count if count else None,
        "correct_per_minute": correct * 60000 / total_ms if total_ms else None,
    }


def summarize_global_trials(trials: list[dict], candidates: dict[str, str]) -> dict:
    """Descriptive per-family measurements; NEVER an efficacy or adoption gate.

    One concept is exposed once per participant, even across conditions.
    Duration includes measured response elapsed time plus actual repair time.
    A participant must have one consistent language-family label.
    """
    if not candidates:
        raise VekaError("no candidate concepts provided")
    normalized = []
    seen = set()
    families_by_participant = {}
    for row in trials:
        if not isinstance(row, dict) or set(row) != set(TRIAL_FIELDS):
            raise VekaError("invalid global trial columns")
        if any(not isinstance(v, str) for v in row.values()):
            raise VekaError("invalid global trial value")
        participant = row["participant_id"].strip()
        family = row["language_background_family"].strip()
        cid = row["concept_id"]
        if not participant or not family or cid not in candidates:
            raise VekaError("unknown concept or missing participant/family")
        if row["condition"] not in ("core", "candidate"):
            raise VekaError("condition must be core or candidate")
        if row["correct"] not in ("0", "1") or row["critical_error"] not in ("0", "1"):
            raise VekaError("correct and critical_error must be 0 or 1")
        if row["correct"] == "1" and row["critical_error"] == "1":
            raise VekaError("a critical semantic error cannot be correct")
        key = (participant, cid)
        if key in seen:
            raise VekaError("participant exposed to the same concept more than once")
        seen.add(key)
        if participant in families_by_participant and families_by_participant[participant] != family:
            raise VekaError("participant has conflicting family labels")
        families_by_participant[participant] = family
        duration = _trial_number(row["elapsed_ms"], positive=True)
        duration += _trial_number(row["repair_ms"], positive=False)
        normalized.append({
            "participant_id": participant, "family": family,
            "concept_id": cid, "condition": row["condition"],
            "correct": int(row["correct"]), "critical_error": int(row["critical_error"]),
            "duration_ms": duration,
        })

    conditions = {c: _stats([r for r in normalized if r["condition"] == c])
                  for c in ("core", "candidate")}
    groups = {
        family: {c: _stats([r for r in normalized if r["family"] == family
                           and r["condition"] == c])
                 for c in ("core", "candidate")}
        for family in sorted({r["family"] for r in normalized})
    }
    balanced = sorted(f for f, data in groups.items()
                      if all(data[c]["trials"] for c in ("core", "candidate")))
    by_concept = {}
    for cid in sorted({r["concept_id"] for r in normalized}):
        subset = [r for r in normalized if r["concept_id"] == cid]
        concept_groups = {
            family: {condition: _stats([r for r in subset
                        if r["family"] == family and r["condition"] == condition])
                     for condition in ("core", "candidate")}
            for family in sorted({r["family"] for r in subset})
        }
        by_concept[cid] = {
            "candidate_form": candidates[cid],
            "conditions": {
                condition: _stats([r for r in subset if r["condition"] == condition])
                for condition in ("core", "candidate")
            },
            "balanced_families": sorted(
                family for family, data in concept_groups.items()
                if all(data[condition]["trials"] for condition in ("core", "candidate"))
            ),
        }
    return {
        "schema_version": "veka.global-trials.v07",
        "observed": bool(normalized),
        "participants": len(families_by_participant),
        "trials": len(normalized),
        "conditions": conditions,
        "groups": groups,
        "by_concept": by_concept,
        "family_coverage": sorted(groups),
        "balanced_families": balanced,
        "unbalanced_families": sorted(set(groups) - set(balanced)),
        "proven_better": False,
        "eligible_for_adoption": False,
        "warning": ("Descriptive observational results only; no confidence intervals, "
                    "randomization proof, power analysis, or critical-error safety gate. "
                    "Never infer improvement from pooled rates alone."),
    }
