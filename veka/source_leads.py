"""Sourced dictionary leads are review leads, never verified Veka donor evidence.

The v0.10 source-screening CSV uses research IDs (R03) rather than the
canonical 100-concept IDs (C002). Join only by *unique exact draft form*,
not by inference from gloss, reference ID, language family or similarity.
"""
from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse

from .core import VekaError

SCREENING_FIELDS = (
    "concept_id", "candidate_form", "language", "language_family",
    "attested_form", "source_url", "source_access", "relation_to_draft",
    "independent_review_status", "notes",
)
SOURCE_ACCESS = {"page_reviewed", "search_result_reviewed"}
RELATIONS = {"related_loan_family", "unrelated_common_translation"}
# This is only a staging tool. Independently verified donor assertions are
# recorded in the existing separate global evidence file after human review.
REVIEW_STATUSES = {"pending"}


def read_screening_leads(path: str | Path) -> list[dict[str, str]]:
    """Load exact-schema, unreviewed source leads without network fetching."""
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != SCREENING_FIELDS:
                raise VekaError("incorrect screening lead CSV schema")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("cannot read screening lead CSV") from exc
    if any(not isinstance(row, dict) or set(row) != set(SCREENING_FIELDS)
           or any(not isinstance(value, str) for value in row.values())
           for row in rows):
        raise VekaError("malformed screening lead CSV row")
    return rows


def audit_screening_leads(leads: list[dict[str, str]],
                          candidates: list[dict]) -> list[dict]:
    """Validate ALL supplied leads; match exact candidate form only.

    Does not infer meaning equivalence or etymological independence from
    the research reference ID, language-family labels, or source link.
    """
    by_form: dict[str, str] = {}
    for candidate in candidates:
        form = candidate.get("candidate_form")
        if not isinstance(form, str):
            raise VekaError("invalid candidate form in lead review")
        if form:
            if form in by_form:
                raise VekaError("ambiguous duplicate candidate form in lead review")
            by_form[form] = candidate["concept_id"]
    seen = set()
    checked = []
    for row in leads:
        if not isinstance(row, dict) or set(row) != set(SCREENING_FIELDS):
            raise VekaError("invalid screening lead columns")
        if any(not isinstance(value, str) for value in row.values()):
            raise VekaError("nontext screening lead value")
        if any(not row[field].strip() for field in SCREENING_FIELDS):
            raise VekaError("empty screening lead field")
        if row["candidate_form"] not in by_form:
            raise VekaError("lead draft form not found in candidate research queue")
        key = (row["candidate_form"], row["language"].strip().casefold())
        if key in seen:
            raise VekaError("duplicate language lead for draft form")
        seen.add(key)
        if (row["source_access"] not in SOURCE_ACCESS or
            row["relation_to_draft"] not in RELATIONS or
            row["independent_review_status"] not in REVIEW_STATUSES):
            raise VekaError("unsupported screening lead evidence/review status")
        url = row["source_url"]
        try:
            parsed = urlparse(url)
            valid = (parsed.scheme == "https" and bool(parsed.hostname)
                     and not parsed.username and not parsed.password
                     and not any(c.isspace() or ord(c) < 32 for c in url))
        except ValueError:
            valid = False
        if not valid:
            raise VekaError("invalid screening lead source URL")
        checked.append({
            "concept_id": by_form[row["candidate_form"]],
            "research_reference_id": row["concept_id"],
            "candidate_form": row["candidate_form"],
            "language": row["language"],
            "language_family": row["language_family"],
            "sourced_form": row["attested_form"],
            "source_url": url,
            "source_access": row["source_access"],
            "relation_to_draft": row["relation_to_draft"],
            "review_status": row["independent_review_status"],
            "notes": row["notes"],
            "accepted_as_attestation": False,
            "independent_etymology_established": False,
            "human_recognition_measured": False,
        })
    return sorted(checked, key=lambda item: (
        item["concept_id"], item["language"].casefold()
    ))
