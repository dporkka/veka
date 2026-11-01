"""A bounded, fail-closed *self-attested* dual-review pipeline for Veka comparators.

Nothing here authenticates reviewer identity, semantic equivalence, or language
expertise. No candidates or human results are invented.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import os
import unicodedata
from pathlib import Path

from .core import VekaError
from .efficiency import PSEUDONYM, audit_efficiency, default_manifest

REVIEW_LANGUAGES = ("id", "tr", "eo", "ia")
REVIEW_FIELDS = (
    "reviewer_id", "item_id", "language", "source_digest",
    "veka_source", "english_reference", "mandarin_reference",
    "portuguese_reference", "target_text", "meaning_equivalent",
    "natural", "critical_ambiguity", "review_notes",
)
REVIEW_LIMIT = 40
REVIEW_SINGLE_LANGUAGE_ROWS = 10


def _digest(item: dict) -> str:
    references = item["variants"]
    source = [item["id"], item["veka"],
              references["en"]["text"], references["zh"]["text"],
              references["pt-BR"]["text"]]
    return hashlib.sha256(json.dumps(source, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8")).hexdigest()


def _items(manifest: dict) -> dict:
    audit_efficiency(manifest)
    frozen = {item['id']: item for item in default_manifest()['items']}
    result = {}
    for item in manifest['items']:
        baseline = frozen.get(item['id'])
        if (baseline is None or item['veka'] != baseline['veka']
                or any(lang not in item['variants'] or
                       item['variants'][lang] != baseline['variants'][lang]
                       for lang in ('en', 'zh', 'pt-BR'))):
            raise VekaError('source meaning or canonical Veka changed from frozen comparison')
        result[item['id']] = item
    if set(result) != set(frozen):
        raise VekaError('review plan requires the ten-item v0.1 reference corpus')
    return result


def build_review_packet(manifest: dict, reviewer_id: str, *, language: str | None = None) -> list[dict[str, str]]:
    """Blank reviewer rows, by one language (10) or all languages (40)."""
    if not isinstance(reviewer_id, str) or not PSEUDONYM.fullmatch(reviewer_id):
        raise VekaError("invalid reviewer pseudonym")
    if language is not None and language not in REVIEW_LANGUAGES:
        raise VekaError("unsupported review language")
    languages = (language,) if language else REVIEW_LANGUAGES
    rows = []
    for item in _items(manifest).values():
        reference = item["variants"]
        for lang in languages:
            rows.append({
                "reviewer_id": reviewer_id, "item_id": item["id"],
                "language": lang, "source_digest": _digest(item),
                "veka_source": item["veka"],
                "english_reference": reference["en"]["text"],
                "mandarin_reference": reference["zh"]["text"],
                "portuguese_reference": reference["pt-BR"]["text"],
                "target_text": "", "meaning_equivalent": "",
                "natural": "", "critical_ambiguity": "", "review_notes": "",
            })
    return rows


def _validated_candidates(rows: list[dict], expected: dict) -> tuple[str, dict]:
    """A candidate author supplies wording, never review verdicts."""
    author, by_key = _validate_packet(rows, expected)
    for row in by_key.values():
        if not row["target_text"] or any(row[field] for field in (
                "meaning_equivalent", "natural", "critical_ambiguity")):
            raise VekaError("candidate sheet requires complete text and no reviewer verdicts")
    return author, by_key


def build_candidate_rating_packet(manifest: dict, candidates: list[dict],
                                  reviewer_id: str) -> list[dict[str, str]]:
    """Bind both reviewers to the same independently authored candidate wording."""
    expected = _items(manifest)
    author, by_key = _validated_candidates(candidates, expected)
    if reviewer_id == author:
        raise VekaError("candidate author cannot review their own wording")
    active = {lang for _, lang in by_key}
    language = next(iter(active)) if len(active) == 1 else None
    rows = build_review_packet(manifest, reviewer_id, language=language)
    for row in rows:
        row["target_text"] = by_key[(row["item_id"], row["language"])]["target_text"]
    return rows


def write_review_packet(rows: list[dict[str, str]], output: str | Path) -> None:
    """Refuse overwrites and restrict reviewer material to the owning user."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(output, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def read_review_csv(path: str | Path) -> list[dict[str, str]]:
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, strict=True)
            if tuple(reader.fieldnames or ()) != REVIEW_FIELDS:
                raise VekaError("invalid dual-review CSV header")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("cannot read dual-review CSV") from exc
    if (len(rows) not in (REVIEW_SINGLE_LANGUAGE_ROWS, REVIEW_LIMIT) or any(
            not isinstance(row, dict) or set(row) != set(REVIEW_FIELDS)
            or any(type(row[key]) is not str for key in REVIEW_FIELDS)
            for row in rows)):
        raise VekaError("dual-review sheet needs 10 or 40 complete rows")
    return rows


def _validate_packet(rows: list[dict], expected: dict) -> tuple[str, dict]:
    if not isinstance(rows, list) or len(rows) not in (REVIEW_SINGLE_LANGUAGE_ROWS, REVIEW_LIMIT):
        raise VekaError("dual-review packet needs 10 or 40 rows")
    seen = set()
    reviewer = None
    by_key = {}
    for row in rows:
        if (not isinstance(row, dict) or set(row) != set(REVIEW_FIELDS)
                or any(type(value) is not str for value in row.values())):
            raise VekaError("invalid or unexpected review columns")
        rid = row["reviewer_id"]
        if not PSEUDONYM.fullmatch(rid):
            raise VekaError("invalid reviewer pseudonym")
        if reviewer is None:
            reviewer = rid
        if reviewer != rid:
            raise VekaError("one sheet must belong to one reviewer")
        key = (row["item_id"], row["language"])
        if (key in seen or key[0] not in expected
                or key[1] not in REVIEW_LANGUAGES):
            raise VekaError("invalid or duplicate review target")
        seen.add(key)
        item = expected[key[0]]
        refs = item["variants"]
        if any(row[k] != v for k, v in (
            ("source_digest", _digest(item)),
            ("veka_source", item["veka"]),
            ("english_reference", refs["en"]["text"]),
            ("mandarin_reference", refs["zh"]["text"]),
            ("portuguese_reference", refs["pt-BR"]["text"]),
        )):
            raise VekaError("source comparison anchor changed")
        target = row["target_text"]
        if target:
            if (len(target) > 1000 or target != target.strip()
                    or unicodedata.normalize("NFC", target) != target
                    or target[0] in "=+@-" or not target.strip()
                    or any(not ch.isprintable() for ch in target)):
                raise VekaError("unsafe or malformed target translation")
        elif any(row[k] for k in ("meaning_equivalent", "natural", "critical_ambiguity")):
            raise VekaError("blank translation cannot receive approval flags")
        for flag in ("meaning_equivalent", "natural"):
            if row[flag] not in ("", "yes", "no", "uncertain"):
                raise VekaError("invalid semantic or naturalness verdict")
        if row["critical_ambiguity"] not in ("", "yes", "no", "uncertain"):
            raise VekaError("invalid ambiguity verdict")
        notes = row["review_notes"]
        if (len(notes) > 400 or any(not ch.isprintable() for ch in notes)
                or notes.lstrip().startswith(("=", "+", "-", "@"))):
            raise VekaError("review notes must be printable, bounded and CSV-safe")
        by_key[key] = row
    active_languages = {lang for _, lang in by_key}
    if (len(active_languages) not in (1, len(REVIEW_LANGUAGES))
            or set(by_key) != {(ident, lang) for ident in expected for lang in active_languages}):
        raise VekaError("incomplete language-specific review packet")
    return reviewer, by_key


def evaluate_reviews(a: list[dict], b: list[dict], manifest: dict | None = None,
                     *, candidates: list[dict] | None = None) -> dict:
    """Agreeing attestations enable a *provisional* reviewed manifest export.

    Does not establish that reviewers are independent humans or correct.
    """
    manifest = default_manifest() if manifest is None else manifest
    expected = _items(manifest)
    reviewer_a, rows_a = _validate_packet(a, expected)
    reviewer_b, rows_b = _validate_packet(b, expected)
    if reviewer_a == reviewer_b:
        raise VekaError("two distinct pseudonymous reviewer sheets required")
    if set(rows_a) != set(rows_b):
        raise VekaError("reviewer sheets disagree on target set")
    if candidates is not None:
        author, candidate_rows = _validated_candidates(candidates, expected)
        if author in (reviewer_a, reviewer_b):
            raise VekaError("candidate author must differ from both reviewers")
        if set(candidate_rows) != set(rows_a):
            raise VekaError("candidate and reviewer targets differ")
        if any(rows_a[k]["target_text"] != candidate_rows[k]["target_text"]
               or rows_b[k]["target_text"] != candidate_rows[k]["target_text"]
               for k in candidate_rows):
            raise VekaError("reviewer text differs from locked candidate")
    active_languages = tuple(lang for lang in REVIEW_LANGUAGES if any(
        key[1] == lang for key in rows_a))
    result_rows = []
    accepted = []
    for item in expected.values():
        for lang in active_languages:
            key = (item["id"], lang)
            first, second = rows_a[key], rows_b[key]
            def decided(r):
                return bool(r["target_text"]) and all(r[f] in ("yes", "no") for f in (
                    "meaning_equivalent", "natural", "critical_ambiguity"))
            if not decided(first) or not decided(second):
                status = "pending"
            elif (first["meaning_equivalent"] == second["meaning_equivalent"] == "yes"
                  and first["natural"] == second["natural"] == "yes"
                  and first["critical_ambiguity"] == second["critical_ambiguity"] == "no"
                  and first["target_text"] == second["target_text"]):
                status = "accepted"
                accepted.append((item["id"], lang, first["target_text"]))
            else:
                status = "blocked"
            result_rows.append({"item_id": item["id"], "language": lang, "status": status})
    publishable = len(accepted) == len(expected) * len(active_languages)
    reviewed = None
    if publishable:
        reviewed = copy.deepcopy(manifest)
        lookups = {item["id"]: item for item in reviewed["items"]}
        for ident, lang, target in accepted:
            evidence = json.dumps(
                [ident, lang, target, *sorted((reviewer_a, reviewer_b)),
                 _digest(expected[ident])],
                ensure_ascii=False, separators=(",", ":"))
            fingerprint = "dual-" + hashlib.sha256(evidence.encode("utf-8")).hexdigest()[:20]
            lookups[ident]["variants"][lang] = {
                "text": target, "status": "independently_reviewed",
                "review_id": fingerprint, "spoken_syllables": None,
                "morphemes": None, "ambiguity_risk": None,
            }
        reviewed["provenance"] += (
            f"; {len(accepted)} reviewed comparator candidates, "
            + ("from a source-locked author sheet" if candidates is not None
               else "with matching independently supplied wording")
            + "; two self-declared reviewer IDs, identity unverified")
        audit_efficiency(reviewed)
    return {
        "schema_version": "veka.efficiency-review.v02",
        "languages": list(active_languages), "items": len(expected),
        "review_sheets_supplied": 2, "candidate_source_locked": candidates is not None,
        "accepted": len(accepted),
        "pending": sum(row["status"] == "pending" for row in result_rows),
        "blocked": sum(row["status"] == "blocked" for row in result_rows),
        "publishable": publishable, "reviewed_manifest": reviewed,
        "reviewer_independence_authenticated": False,
        "translation_fidelity_independently_verified_by_tool": False,
        "human_efficiency_measured": False,
        "canonical_changes": 0, "rows": result_rows,
        "warning": ("These are self-declared reviewer attestations only; reviewer identity, "
                    "expertise and genuine independence cannot be validated by this tool. "
                    "Consensus text does not establish semantic equivalence, and no human "
                    "communication study is performed."),
    }
