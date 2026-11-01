"""Human editorial-review *administration*, not automatic translation validation.

Keeps a frozen mapping of canonical teaching items to editorial prose.
Two reviewer sheets are individually filled; separate pseudonyms alone do
not prove reviewer independence or competence.
"""
from __future__ import annotations

import csv
import os
import re
from pathlib import Path

from .contrast_drills import make_contrast_drills
from .core import VekaError
from .learner_locales import LANGUAGES

COLUMNS = (
    "reviewer_id", "language", "item_id", "variant", "feature",
    "sentence", "translation", "focus",
    "semantic_fidelity", "naturalness", "contrast_clarity", "notes",
)
JUDGMENTS = ("semantic_fidelity", "naturalness", "contrast_clarity")
PERMITTED = frozenset({"", "accept", "revise", "unsure"})
ID = re.compile(r"[A-Za-z0-9_-]{1,40}\Z", re.ASCII)


def _expected(language: str) -> dict[tuple[str, str], dict[str, str]]:
    packet = make_contrast_drills(language, profile="tonal")
    expected = {}
    for pair in packet["pairs"]:
        for variant in ("a", "b"):
            row = {
                "language": language,
                "item_id": pair["id"],
                "variant": variant.upper(),
                "feature": pair["feature"],
                "sentence": pair[variant]["sentence"],
                "translation": pair[variant]["editorial_translation"],
                "focus": pair["focus"],
            }
            expected[(row["item_id"], row["variant"])] = row
    if len(expected) != 12:
        raise VekaError("unexpected number of canonical review items")
    return expected


def write_review_template(language: str, reviewer_id: str, output: str | Path) -> dict:
    """Produce a blank, exact-version reviewer sheet; refuse overwrites."""
    if language not in LANGUAGES or not isinstance(reviewer_id, str) or not ID.fullmatch(reviewer_id):
        raise VekaError("invalid language or reviewer pseudonym")
    rows = []
    for item in _expected(language).values():
        rows.append({
            "reviewer_id": reviewer_id, **item,
            **{judgment: "" for judgment in JUDGMENTS},
            "notes": "",
        })
    destination = Path(output)
    created = False
    try:
        # Explicitly private even when the caller's umask would create 0644.
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    except (OSError, csv.Error, UnicodeError) as exc:
        if created:
            destination.unlink(missing_ok=True)
        raise VekaError("cannot create a new editorial review sheet (no overwrites)") from exc
    return {
        "schema_version": "veka.contrast-review.v1",
        "language": language, "reviewer_id": reviewer_id,
        "rows": len(rows), "output": str(output),
        "human_review_collected": False,
        "canonical_vocabulary_changed": False,
        "notice": "Blank reviewer template; no reviewer judgments were collected.",
    }


def _read_review(language: str, path: str | Path, expected: dict) -> tuple[str, dict]:
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != COLUMNS:
                raise VekaError("review sheet header mismatch")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("cannot read strict review CSV") from exc
    if len(rows) != len(expected):
        raise VekaError("review sheet is incomplete or has extra rows")
    seen = {}
    reviewer_ids = set()
    for row in rows:
        if (set(row) != set(COLUMNS)
                or any(not isinstance(row.get(column), str) for column in COLUMNS)):
            raise VekaError("malformed review row or unexpected column")
        reviewer = row["reviewer_id"]
        if not ID.fullmatch(reviewer):
            raise VekaError("invalid reviewer pseudonym")
        reviewer_ids.add(reviewer)
        key = (row["item_id"], row["variant"])
        if key in seen or key not in expected:
            raise VekaError("duplicate or unknown review item")
        # Compare to a freshly generated canonical source, not a user-editable
        # copy of the expected meanings, so outdated/tampered sheets fail.
        if any(row[field] != expected[key][field] for field in expected[key]):
            raise VekaError("review content differs from current canonical teaching item")
        if any(row[field] not in PERMITTED for field in JUDGMENTS):
            raise VekaError("review score must be blank, accept, revise or unsure")
        if len(row["notes"]) > 2000:
            raise VekaError("review note is too long")
        if (any(row[field] in ("revise", "unsure") for field in JUDGMENTS)
                and not row["notes"].strip()):
            raise VekaError("revise or unsure judgment requires an explanation")
        seen[key] = row
    if len(seen) != len(expected) or len(reviewer_ids) != 1:
        raise VekaError("review sheet is missing items or mixes reviewers")
    return next(iter(reviewer_ids)), seen


def check_review_sheets(language: str, first: str | Path, second: str | Path) -> dict:
    """Report pending/conflicts without certifying reviewers or translations."""
    if language not in LANGUAGES:
        raise VekaError("unsupported reviewer language")
    if Path(first).resolve() == Path(second).resolve():
        raise VekaError("review sheets must use distinct paths")
    expected = _expected(language)
    first_id, a = _read_review(language, first, expected)
    second_id, b = _read_review(language, second, expected)
    if first_id == second_id:
        raise VekaError("editorial reviews must have distinct reviewer pseudonyms")
    pending = 0
    flagged = []
    for key in expected:
        annotations = [a[key], b[key]]
        for field in JUDGMENTS:
            pending += sum(row[field] == "" for row in annotations)
        if any(row[field] in ("revise", "unsure") for row in annotations for field in JUDGMENTS):
            flagged.append(f"{key[0]}:{key[1]}")
    return {
        "schema_version": "veka.contrast-review-audit.v1",
        "language": language, "reviewer_ids": [first_id, second_id],
        "rows_per_reviewer": len(expected),
        "pending_judgments": pending,
        "flagged_items": flagged,
        "ready_for_manual_editorial_signoff": pending == 0 and not flagged,
        "independent_humans_verified": False,
        "translations_automatically_validated": False,
        "human_comprehension_measured": False,
        "canonical_vocabulary_changed": False,
        "notice": "Reviewer identities and qualifications must be verified out of band. "
                  "The machine can only audit recorded editorial decisions.",
    }
