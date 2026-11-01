"""Auditable source leads for Veka international roots; never adoption evidence.

Source URLs, language families and reviewers are declarations in input data.
No remote fetch, source authenticity claim, native-speaker verification, human
experiment inference, or canonical vocabulary modification is performed.
"""
from __future__ import annotations

import csv
import ipaddress
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from .core import Lexicon, VekaError
from .international import audit_candidates

SOURCE_FIELDS = (
    "concept_id", "candidate_form", "language", "language_family",
    "language_branch", "attested_form", "relation", "source_url",
    "source_note", "review_status", "semantic_match", "reviewer", "review_note",
)
RELATIONS = frozenset(("candidate_like", "false_friend", "different_common_form"))
REVIEW_STATUSES = frozenset(("pending", "approved", "rejected"))


def read_root_sources(path: str | Path) -> list[dict[str, str]]:
    """Read a complete, strictly shaped source packet; CSV never executes."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file, strict=True)
            if tuple(reader.fieldnames or ()) != SOURCE_FIELDS:
                raise VekaError("invalid root source CSV headers")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("cannot read root source CSV") from exc
    if any(set(row) != set(SOURCE_FIELDS)
           or any(not isinstance(row[field], str) for field in SOURCE_FIELDS)
           for row in rows):
        raise VekaError("incomplete or malformed source lead row")
    return rows


def _public_source_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        if (parsed.scheme != "https" or not host or parsed.username or
                parsed.password or parsed.port not in (None, 443) or
                "." not in host or host.endswith((
                    ".localhost", ".local", ".internal", ".test", ".invalid", ".example"
                )) or host.startswith("localhost.")):
            return False
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return True
        return address.is_global
    except (TypeError, ValueError):
        return False


def audit_root_sources(rows: list[dict[str, str]], lex: Lexicon,
                       candidates: list[dict]) -> dict:
    """Count sourced leads and explicit reviewer *claims* only.

    Source existence is not checked, and no review claim is authenticated.
    Candidate-like refers only to a preliminary resemblance hypothesis.
    """
    audit = audit_candidates(candidates, lex)
    viable = {item["concept_id"]: item for item in audit["candidates"]
              if item["status"] == "structurally_testable"}
    seen = set()
    groups = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(SOURCE_FIELDS):
            raise VekaError("root source row has unknown or missing columns")
        if any(not isinstance(value, str) for value in row.values()):
            raise VekaError("non-string source field")
        cid = row["concept_id"]
        if cid not in viable or row["candidate_form"] != viable[cid]["candidate_form"]:
            raise VekaError("source concept or proposed form is not a valid draft")
        for field in ("language", "language_family", "language_branch",
                      "attested_form", "source_note"):
            if not row[field].strip():
                raise VekaError(f"source lead missing required {field}")
        if not _public_source_url(row["source_url"]):
            raise VekaError("source URL must be a public HTTPS lexicographic link")
        if row["relation"] not in RELATIONS:
            raise VekaError("unknown source relation")
        if row["review_status"] not in REVIEW_STATUSES:
            raise VekaError("unknown source review status")
        if row["semantic_match"] not in ("yes", "no", "unknown"):
            raise VekaError("semantic_match must be yes, no or unknown")
        key = (cid, row["language"].casefold().strip())
        if key in seen:
            raise VekaError("duplicate source concept-language")
        seen.add(key)
        if row["review_status"] == "pending":
            if row["reviewer"].strip() or row["review_note"].strip() or row["semantic_match"] != "unknown":
                raise VekaError("pending source cannot assert a completed review")
        elif not row["reviewer"].strip() or not row["review_note"].strip():
            raise VekaError("reviewer and review_note required for claimed review")
        if row["review_status"] == "approved":
            if row["semantic_match"] != "yes":
                raise VekaError("approved lexical sense must match target concept")
            if row["relation"] == "false_friend":
                raise VekaError("false friend cannot be accepted as matching evidence")
        groups[cid].append(row)

    details = []
    for cid, group in sorted(groups.items()):
        approved = [r for r in group if r["review_status"] == "approved"]
        candidates_approved = [r for r in approved if r["relation"] == "candidate_like"]
        families = sorted({r["language_family"].strip().casefold() for r in candidates_approved})
        details.append({
            "concept_id": cid, "gloss": viable[cid]["gloss"],
            "core_form": viable[cid]["core_form"],
            "candidate_form": viable[cid]["candidate_form"],
            "source_leads": len(group),
            "candidate_like_leads": sum(r["relation"] == "candidate_like" for r in group),
            "false_friend_leads": sum(r["relation"] == "false_friend" for r in group),
            "different_common_form_leads": sum(
                r["relation"] == "different_common_form" for r in group),
            "pending_review": sum(r["review_status"] == "pending" for r in group),
            "reviewer_approved_records": len(approved),
            "reviewer_claimed_families": len(families),
            "reviewer_claimed_family_labels": families,
            "recognition_measured": False,
            "adoption_authorized": False,
        })
    return {
        "schema_version": "veka.root-sources.v12",
        "source_leads": len(rows),
        "concepts_with_leads": len(groups),
        "unreviewed_leads": sum(r["review_status"] == "pending" for r in rows),
        "reviewer_approved_records": sum(r["review_status"] == "approved" for r in rows),
        "candidate_like_approved": sum(r["review_status"] == "approved" and
                                      r["relation"] == "candidate_like" for r in rows),
        "reviewer_claimed_families_total": sum(r["reviewer_claimed_families"] for r in details),
        "concepts": details,
        "canonical_changes": 0,
        "recognition_measured": False,
        "human_benefit_established": False,
        "adoption_authorized": False,
        "warning": (
            "Source URLs and family labels are research assertions, not independently "
            "authenticated semantic review or measured cross-family recognition. "
            "A reviewer approval, if present, is a data claim not independently "
            "validated by software. Every proposed form remains noncanonical. "
            "False friends and contrasting common words must not be counted as "
            "support for candidate familiarity."
        ),
    }
