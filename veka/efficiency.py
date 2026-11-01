"""Reproducible, noncanonical efficiency instrument; not a language ranking.

Veka syllables are structural counts. Other languages require human phonetic
annotation: orthographic characters and whitespace tokens are not syllables.
Self-declared translation reviews are not independently authenticated.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from .core import VekaError, parse, syllabify
from .profiles import DATA, load_profile

SCHEMA = "veka.efficiency-manifest.v01"
TRIAL_FIELDS = ("participant_id", "background_family", "item_id", "language",
                "correct", "elapsed_ms", "repair_ms", "critical_error")
COMPARATORS = frozenset(("en", "zh", "pt-BR", "id", "tr", "eo", "ia", "ja", "vi", "es"))
VARIANT_FIELDS = frozenset(("text", "status", "review_id",
                            "spoken_syllables", "morphemes", "ambiguity_risk"))
PSEUDONYM = re.compile(r"[A-Za-z0-9_-]{2,64}\Z", re.ASCII)
ITEM_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{1,63}\Z", re.ASCII)


def default_manifest() -> dict:
    """Load the frozen 10-item v0.1 editorial snapshot, independent of lesson edits."""
    try:
        doc = json.loads((DATA / "efficiency_manifest_v01.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise VekaError("cannot load bundled efficiency manifest") from exc
    return doc


def _positive_int(value: object, limit: int = 1000) -> bool:
    return type(value) is int and 0 < value <= limit


def _text(value: object, max_length: int = 1000) -> bool:
    return (isinstance(value, str) and bool(value.strip())
            and value == value.strip() and len(value) <= max_length
            and all(ch.isprintable() for ch in value))


def audit_efficiency(doc: dict) -> dict:
    """Validate aligned readings and compute ONLY comparable Veka structural facts."""
    if (not isinstance(doc, dict) or set(doc) != {"schema_version", "provenance", "items"}
            or doc["schema_version"] != SCHEMA or not _text(doc["provenance"])
            or not isinstance(doc["items"], list)
            or not 1 <= len(doc["items"]) <= 500):
        raise VekaError("invalid efficiency manifest")
    lex = load_profile("tonal")
    seen = set()
    languages = {"veka"}
    output = []
    reviewed = 0
    for item in doc["items"]:
        if (not isinstance(item, dict) or set(item) != {"id", "veka", "variants"}
                or not isinstance(item["id"], str) or not ITEM_ID.fullmatch(item["id"])
                or item["id"] in seen or not _text(item["veka"])
                or not isinstance(item["variants"], dict) or not item["variants"]
                or len(item["variants"]) > len(COMPARATORS)):
            raise VekaError("invalid or repeated efficiency item")
        seen.add(item["id"])
        try:
            parse(item["veka"], lex, strict=True)
            words = item["veka"].rstrip(".?!").split()
            spoken = sum(len(syllabify(word.lower())) for word in words)
        except VekaError as exc:
            raise VekaError(f'{item["id"]}: invalid or uncountable canonical Veka') from exc
        variants = {}
        for language, entry in sorted(item["variants"].items()):
            if language not in COMPARATORS or not isinstance(entry, dict) or set(entry) != VARIANT_FIELDS:
                raise VekaError(f'{item["id"]}: invalid comparator language or annotation fields')
            if not _text(entry["text"]):
                raise VekaError(f'{item["id"]}: blank or invalid comparator text')
            status = entry["status"]
            if status not in ("editorial_unverified", "independently_reviewed"):
                raise VekaError(f'{item["id"]}: unknown review status')
            if status == "editorial_unverified":
                if any(entry[k] is not None for k in (
                        "review_id", "spoken_syllables", "morphemes", "ambiguity_risk")):
                    raise VekaError(f'{item["id"]}: manual metrics require a review')
            else:
                if (not isinstance(entry["review_id"], str)
                        or not PSEUDONYM.fullmatch(entry["review_id"])):
                    raise VekaError(f'{item["id"]}: independently reviewed item needs reviewer ID')
                reviewed += 1
                for key in ("spoken_syllables", "morphemes"):
                    if entry[key] is not None and not _positive_int(entry[key]):
                        raise VekaError(f'{item["id"]}: invalid {key}')
                risk = entry["ambiguity_risk"]
                if risk is not None and (type(risk) is not int or not 0 <= risk <= 3):
                    raise VekaError(f'{item["id"]}: ambiguity must be ordinal 0..3')
            languages.add(language)
            variants[language] = {
                "text": entry["text"], "status": status,
                "review_id": entry["review_id"],
                "orthographic_characters": sum(ch.isalnum() for ch in entry["text"]),
                "spoken_syllables": entry["spoken_syllables"],
                "morphemes": entry["morphemes"],
                "ambiguity_risk": entry["ambiguity_risk"],
            }
        output.append({
            "id": item["id"],
            "veka": {"text": item["veka"], "words": len(words),
                     "morphemes": spoken, "spoken_syllables": spoken,
                     "strict_core_parse": True},
            "variants": variants,
        })
    return {
        "schema_version": "veka.efficiency-audit.v01",
        "items": len(output), "languages": sorted(languages),
        "veka_parse_passes": len(output), "independently_reviewed_variants": reviewed,
        "rows": output, "comprehension_measured": False,
        "language_efficiency_ranked": False, "canonical_changes": 0,
        "warning": ("Veka counts rely on its one-syllable-per-morpheme Core design. "
                    "Other-language syllables, morphemes and ambiguity are unknown unless "
                    "manually annotated. Reviewer IDs/status are self-declared, not authenticated. "
                    "Different scripts' character counts cannot be compared as communication cost. "
                    "Editorial readings have not been certified semantically equivalent."),
    }


def read_efficiency_trials(path: str | Path) -> list[dict[str, str]]:
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, strict=True)
            if tuple(reader.fieldnames or ()) != TRIAL_FIELDS:
                raise VekaError("invalid efficiency trial CSV header")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("cannot read efficiency trial CSV") from exc
    if any(set(r) != set(TRIAL_FIELDS) or any(type(r[k]) is not str for k in TRIAL_FIELDS)
           for r in rows):
        raise VekaError("malformed efficiency trial CSV row")
    return rows


def _stats(rows: list[dict]) -> dict:
    total_ms = sum(r["duration_ms"] for r in rows)
    correct = sum(r["correct"] for r in rows)
    return {"trials": len(rows), "correct": correct,
            "critical_errors": sum(r["critical_error"] for r in rows),
            "total_ms": total_ms,
            "correct_per_minute": round(correct * 60000 / total_ms, 4) if total_ms else None}


def score_efficiency_trials(rows: list[dict[str, str]], manifest: dict) -> dict:
    """Descriptive throughput; no human result is invented by an empty trial file."""
    audited = audit_efficiency(manifest)
    variants = {r["id"]: r["variants"] for r in audited["rows"]}
    seen = set()
    participants = {}
    normalized = []
    for row in rows:
        if (not isinstance(row, dict) or set(row) != set(TRIAL_FIELDS)
                or any(type(v) is not str for v in row.values())):
            raise VekaError("malformed efficiency observation")
        pid, family, ident, language = (
            row[name] for name in ("participant_id", "background_family", "item_id", "language"))
        if (not PSEUDONYM.fullmatch(pid) or not re.fullmatch(r"[A-Za-z][A-Za-z -]{1,63}", family, re.ASCII)
                or ident not in variants
                or (language != "veka" and (language not in variants[ident]
                    or variants[ident][language]["status"] != "independently_reviewed"))):
            raise VekaError("trial item/language must exist and comparator translation be reviewed")
        if (pid, ident) in seen:
            raise VekaError("participant repeated the same meaning across conditions")
        seen.add((pid, ident))
        if pid in participants and participants[pid] != family:
            raise VekaError("participant background changed")
        participants[pid] = family
        if row["correct"] not in ("0", "1") or row["critical_error"] not in ("0", "1"):
            raise VekaError("correct/critical_error must be 0 or 1")
        if row["correct"] == "1" and row["critical_error"] == "1":
            raise VekaError("critical error cannot be marked correct")
        for key in ("elapsed_ms", "repair_ms"):
            value = row[key]
            if (not value.isascii() or not value.isdecimal() or not 1 <= len(value) <= 13
                    or (key == "elapsed_ms" and int(value) == 0)):
                raise VekaError("invalid elapsed or repair milliseconds")
        normalized.append({"background_family": family, "item_id": ident,
                           "language": language, "correct": int(row["correct"]),
                           "critical_error": int(row["critical_error"]),
                           "duration_ms": int(row["elapsed_ms"]) + int(row["repair_ms"])})
    cells = defaultdict(set)
    for item in normalized:
        cells[(item["background_family"], item["item_id"])].add(item["language"])
    paired = sum("veka" in langs and len(langs) > 1 for langs in cells.values())
    return {
        "schema_version": "veka.efficiency-score.v01",
        "observed": bool(normalized), "participants": len(participants),
        "trial_count": len(normalized),
        "by_language": {lang: _stats([r for r in normalized if r["language"] == lang])
                        for lang in sorted({r["language"] for r in normalized})},
        "paired_cells": paired, "unpaired_cells": len(cells) - paired,
        "canonical_changes": 0, "comparative_benefit_established": False,
        "warning": ("Only descriptive elapsed-plus-repair throughput. Supplied responses, "
                    "participant independence, editorial review claims, randomization, and "
                    "semantic equivalence are not authenticated; no inference or winner."),
    }
