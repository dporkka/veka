"""Blinded meaning-recovery packet builder for existing Veka 0.3 stimuli.

No recorded audio or humans, no automatic semantic judgments and no claim of
improved comprehension. The original study-assign command is preserved.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import re
from pathlib import Path

from .core import Discourse, VekaError, parse
from .profiles import load_profile
from .study import validate_items

ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
PARTICIPANT_FIELDS = ("trial_id", "audio_id", "context_json", "response_text", "elapsed_ms", "repairs")


def make_meaning_packet(items: list[dict], participant_id: str, *, arm: int,
                        seed: int = 20261101) -> tuple[list[dict], list[dict], list[dict]]:
    """Generate participant-only responses, a sealed meaning key and recording jobs.

    Arm is allocated externally (0/1), never determined by participant IDs.
    One presentation of each meaning; recordings reuse opaque content-addressed
    clip references across participants with the same assigned condition.
    """
    if (not isinstance(participant_id, str) or not ID.fullmatch(participant_id)
            or type(arm) is not int or arm not in (0, 1) or type(seed) is not int):
        raise VekaError("invalid participant id, randomized arm or seed")
    validate_items(items)
    if len(items) < 2 or len(items) > 128 or len(items) % 2:
        raise VekaError("meaning pilot requires an even number of 2..128 items")
    lex = load_profile("tonal")
    arranged = []
    for index, item in enumerate(items):
        if (not ID.fullmatch(str(item["item_id"])) or type(item["critical"]) is not int
                or item["critical"] not in (0, 1)):
            raise VekaError("unsafe item identity or critical flag")
        try:
            context = Discourse(**{field: tuple(values) for field, values in item["context"].items()})
            explicit = parse(item["explicit"], lex, context=context)
            compact = parse(item["compact"], lex, context=context)
        except (TypeError, KeyError, ValueError) as exc:
            raise VekaError(f"invalid meaning stimulus {item['item_id']}") from exc
        # Parsing alone isn't a human comprehension result. It *does* ensure
        # both training variants have identical deterministic role semantics.
        if explicit != dict(compact, compressed=False):
            raise VekaError(f"meaning variants differ structurally: {item['item_id']}")
        condition = ("explicit", "compact")[(index + arm) % 2]
        utterance = item[condition]
        context_json = json.dumps(item["context"], ensure_ascii=False, sort_keys=True,
                                  separators=(",", ":"))
        fingerprint = json.dumps(
            [item["item_id"], condition, utterance, context_json],
            ensure_ascii=False, separators=(",", ":"))
        audio_id = "meaning_" + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:24] + ".wav"
        arranged.append((item, condition, utterance, context_json, audio_id))
    random.Random(f"veka-meaning:{seed}:{participant_id}:{arm}").shuffle(arranged)
    participant, key, recording = [], [], []
    for index, (item, condition, utterance, context_json, audio_id) in enumerate(arranged, 1):
        trial_id = f"M{index:04d}"
        participant.append({
            "trial_id": trial_id, "audio_id": audio_id, "context_json": context_json,
            "response_text": "", "elapsed_ms": "", "repairs": ""})
        key.append({
            "trial_id": trial_id, "participant_id": participant_id,
            "item_id": item["item_id"], "condition": condition,
            "category": item["category"], "critical": item["critical"],
            "meaning": item["meaning"], "utterance": utterance,
            "context_json": context_json, "audio_id": audio_id})
        recording.append({
            "audio_id": audio_id, "item_id": item["item_id"],
            "condition": condition, "utterance": utterance, "recorded": "no"})
    return participant, key, recording


def write_meaning_packet(packet: tuple[list[dict], list[dict], list[dict]],
                         participant_path: str | Path, key_path: str | Path,
                         recording_path: str | Path) -> dict:
    paths = [Path(path) for path in (participant_path, key_path, recording_path)]
    if len({p.resolve() for p in paths}) != 3 or any(p.exists() for p in paths):
        raise VekaError("three distinct, new study files are required")
    if any(not r for r in packet):
        raise VekaError("empty study output")
    created = []
    try:
        for path, rows in zip(paths, packet):
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(path)
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
    except (OSError, ValueError, csv.Error):
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return {
        "schema_version": "veka.meaning-plan.v06",
        "trials": len(packet[0]),
        "explicit": sum(row["condition"] == "explicit" for row in packet[1]),
        "compact": sum(row["condition"] == "compact" for row in packet[1]),
        "participant_csv": str(paths[0]), "researcher_key": str(paths[1]),
        "recording_manifest": str(paths[2]),
        "audio_recorded": False, "human_data_collected": False,
        "semantic_equivalence_machine_checked": True,
        "warning": "Researcher key and recording manifest must not be shared with participants.",
    }
