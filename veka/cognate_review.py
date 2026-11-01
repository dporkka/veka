"""Veka 0.7 noncanonical loanword leads: strict source and reviewer-state audit.

Research leads are not verified evidence. This module does not fetch URLs, alter
the canonical lexicon, validate the truth of cited content, or measure recognition.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from .core import Lexicon, VekaError
from .cognates import audit_pilot
from .global_comprehension import EVIDENCE_FIELDS, read_global_csv


def read_cognate_leads(path: str | Path) -> list[dict[str, str]]:
    return read_global_csv(path, EVIDENCE_FIELDS)


def _source_url_is_valid(value: str) -> bool:
    try:
        url = urlsplit(value)
        return (
            url.scheme in {"https", "http"} and bool(url.hostname)
            and url.username is None and url.password is None
            and not any(ord(c) < 32 or c.isspace() for c in value)
        )
    except ValueError:
        return False


def audit_cognate_leads(candidates: list[dict], leads: list[dict],
                        lex: Lexicon) -> dict:
    """Report review queue and manually asserted equivalence by language family.

    A cross-family loanword still has a shared borrowing history; family counts
    are not independent origins or validated recognition probabilities.
    """
    canonical = audit_pilot(candidates, lex)
    if canonical["rejected_count"]:
        raise VekaError("cannot review source leads for rejected candidates")
    by_id = {x["concept_id"]: x for x in candidates}
    seen = set()
    grouped = defaultdict(list)
    for row in leads:
        if not isinstance(row, dict) or set(row) != set(EVIDENCE_FIELDS):
            raise VekaError("incorrect loanword review lead columns")
        if any(not isinstance(v, str) for v in row.values()):
            raise VekaError("invalid loanword review lead value")
        cid = row["concept_id"]
        if cid not in by_id or row["candidate_form"] != by_id[cid]["candidate_form"]:
            raise VekaError("lead does not match the cognate candidate version")
        if any(not row[field].strip() for field in (
                "language", "language_family", "language_branch", "attested_form", "notes")):
            raise VekaError("missing lead metadata or lexical form")
        if not _source_url_is_valid(row["source_url"]):
            raise VekaError("lead requires a valid direct web source")
        identity = (cid, row["language"].strip().casefold())
        if identity in seen:
            raise VekaError("duplicate concept-language review lead")
        seen.add(identity)
        if row["attestation_verified"] not in ("yes", "no"):
            raise VekaError("invalid verification state")
        if row["semantic_equivalent"] not in ("yes", "no", "unknown"):
            raise VekaError("invalid semantic equivalence state")
        if row["attestation_verified"] == "yes":
            if not row["semantic_reviewer"].strip() or row["semantic_equivalent"] == "unknown":
                raise VekaError("verified records require an independent reviewer and sense decision")
        elif row["semantic_equivalent"] != "unknown":
            raise VekaError("unreviewed leads cannot assert semantic equivalence")
        grouped[cid].append(row)
    counts = {}
    for cid, rows in sorted(grouped.items()):
        equivalents = [r for r in rows if r["attestation_verified"] == "yes"
                       and r["semantic_equivalent"] == "yes"]
        counts[cid] = {
            "candidate_form": by_id[cid]["candidate_form"],
            "source_leads": len(rows),
            "pending_review": sum(r["attestation_verified"] == "no" for r in rows),
            "verified_equivalent": len(equivalents),
            "verified_families": len({r["language_family"].strip().casefold()
                                      for r in equivalents}),
            "verified_branches": len({
                (r["language_family"].strip().casefold(),
                 r["language_branch"].strip().casefold()) for r in equivalents
            }),
        }
    return {
        "schema_version": "veka.cognate-review.v07",
        "lead_count": len(leads),
        "pending_review": sum(r["pending_review"] for r in counts.values()),
        "verified_equivalent": sum(r["verified_equivalent"] for r in counts.values()),
        "adopted_count": 0,
        "recognition_measured": False,
        "by_concept": counts,
        "warning": (
            "Source-linked lexical leads require independent human semantic and "
            "pronunciation review. Even a verified borrowing does not prove "
            "first-sight recognition or justify vocabulary adoption."
        ),
    }
