"""Veka 0.6 blinded ABX pilot packet and descriptive scorer.

Study logistics, not human findings. File/WAV checks cannot certify the
speaker identity, lexical pronunciation, human responses or actual SNR.
No third-party dependencies; all CSV inputs and outputs are versioned.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import re
import wave
from collections import Counter, defaultdict
from pathlib import Path

from .core import Lexicon, VekaError, _syllable_info
from .profiles import PROFILES

DATA = Path(__file__).resolve().parents[1] / "data"
DEFAULT_CONTRASTS = DATA / "listening_contrasts_v06.csv"
CONTRAST_COLUMNS = ["contrast_id", "a", "b", "category", "critical", "profile"]
RESPONSE_COLUMNS = [
    "trial_id", "a_audio", "b_audio", "x_audio", "response", "elapsed_ms",
]
KEY_COLUMNS = [
    "trial_id", "participant_id", "profile", "contrast_id", "category",
    "critical", "condition", "talker", "a_form", "b_form", "x_form",
    "correct_option", "a_audio", "b_audio", "x_audio",
]
RECORDING_COLUMNS = ["audio_id", "trial_id", "slot", "form", "talker", "condition", "recorded"]
CONDITIONS = ("quiet", "noise_plus5db")
CLIP_RE = re.compile(r"clip_[0-9a-f]{12}_[0-9]{5}\.wav\Z")
ID_RE = re.compile(r"[A-Za-z0-9_-]{1,40}\Z")
TALKER_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,20}\Z")
MAX_WAV_BYTES = 25 * 1024 * 1024


def read_csv(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise VekaError("invalid CSV headers")
        return list(reader)


def load_contrasts(path: str | Path, lex: Lexicon, profile: str) -> list[dict]:
    if profile not in PROFILES:
        raise VekaError("unknown listening profile")
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != CONTRAST_COLUMNS:
            raise VekaError("contrast CSV header does not match schema")
        rows = list(reader)
    if not rows:
        raise VekaError("contrast list is empty")
    seen_id, seen_pairs, selected = set(), set(), []
    for r in rows:
        if (None in r or any(not isinstance(r.get(col), str) for col in CONTRAST_COLUMNS)
                or not ID_RE.fullmatch(r["contrast_id"])
                or r["critical"] not in ("yes", "no")
                or r["profile"] not in ("both", *PROFILES)
                or r["category"] not in ("pronoun", "negation", "aspect", "grammar",
                                          "number", "tone", "coda", "control")):
            raise VekaError("invalid contrast row")
        if r["contrast_id"] in seen_id:
            raise VekaError("duplicate contrast identifier")
        seen_id.add(r["contrast_id"])
        pair_key = (r["profile"], tuple(sorted((r["a"], r["b"]))))
        if pair_key in seen_pairs:
            raise VekaError("duplicate contrast pair")
        seen_pairs.add(pair_key)
        if r["a"] == r["b"]:
            raise VekaError("contrast needs two different forms")
        if r["profile"] not in ("both", profile):
            continue
        for form in (r["a"], r["b"]):
            if form not in lex or lex[form].kind != "root":
                raise VekaError(f"contrast word missing in chosen profile: {form}")
            _syllable_info(form)
        selected.append(r)
    if not selected:
        raise VekaError("no valid contrasts for chosen profile")
    return selected


def make_packet(pairs: list[dict], participant_id: str, talkers: tuple[str, ...],
                profile: str, seed: int = 20261101, arm: int = 0):
    """Make participant-blind trials, restricted key and recording job sheet.

    A/B orientation flips by explicitly assigned enrollment arm, not a
    demographic property or inferred participant ID. Within each pair,
    talker and channel, one trial has X=A, one has X=B.
    """
    if (not isinstance(participant_id, str) or not ID_RE.fullmatch(participant_id)
            or profile not in PROFILES or arm not in (0, 1) or type(arm) is not int
            or type(seed) is not int
            or not 1 <= len(talkers) <= 8
            or any(not isinstance(t, str) or not TALKER_RE.fullmatch(t) for t in talkers)
            or len(set(talkers)) != len(talkers)):
        raise VekaError("invalid participant, profile, arm, seed or talker identifiers")
    if not pairs or len(pairs) > 50:
        raise VekaError("study must contain 1..50 contrasts")
    # Verify inputs even for an injected/mutated custom list.
    seen = set()
    for p in pairs:
        if (not all(k in p for k in CONTRAST_COLUMNS)
                or p["contrast_id"] in seen or p["a"] == p["b"]
                or p["critical"] not in ("yes", "no")
                or p["profile"] not in ("both", profile)):
            raise VekaError("invalid packet contrast")
        seen.add(p["contrast_id"])
        _syllable_info(p["a"])
        _syllable_info(p["b"])
    schedule = []
    for pi, pair in enumerate(pairs):
        for ti, talker in enumerate(talkers):
            for ci, condition in enumerate(CONDITIONS):
                swapped = (arm + pi + ti + ci) % 2
                a_form, b_form = (pair["b"], pair["a"]) if swapped else (pair["a"], pair["b"])
                for x_form in (pair["a"], pair["b"]):
                    schedule.append((pair, condition, talker, a_form, b_form, x_form))
    bank_spec = {"schema": "veka.abx-bank.v06", "profile": profile, "arm": arm,
                 "talkers": list(talkers), "pairs": [dict(p) for p in pairs]}
    bank_id = hashlib.sha256(json.dumps(bank_spec, sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
    # Allocate opaque clip names BEFORE participant-specific trial shuffling.
    # The same arm can reuse one independently recorded A/B/X stimulus bank
    # across listeners; the other arm has a distinct, noncolliding bank.
    # Assignments still randomize presentation order separately per participant.
    prepared = []
    for i, details in enumerate(schedule):
        clip_ids = tuple(f"clip_{bank_id}_{arm * 10000 + i * 3 + slot + 1:05d}.wav"
                         for slot in range(3))
        prepared.append((details, clip_ids))
    rng = random.Random(f"veka-v06:{seed}:{participant_id}:{arm}:{profile}")
    rng.shuffle(prepared)
    participant, key, recordings = [], [], []
    for i, (details, clips) in enumerate(prepared, 1):
        pair, condition, talker, a, b, x = details
        trial_id = f"trial_{i:04d}"
        for (slot, form), audio_id in zip((("A", a), ("B", b), ("X", x)), clips):
            recordings.append(dict(audio_id=audio_id, trial_id=trial_id,
                                   slot=slot, form=form, talker=talker,
                                   condition=condition, recorded="no"))
        participant.append(dict(trial_id=trial_id,
                                a_audio=clips[0], b_audio=clips[1], x_audio=clips[2],
                                response="", elapsed_ms=""))
        key.append(dict(trial_id=trial_id, participant_id=participant_id, profile=profile,
                        contrast_id=pair["contrast_id"], category=pair["category"],
                        critical=pair["critical"], condition=condition, talker=talker,
                        a_form=a, b_form=b, x_form=x,
                        correct_option="A" if x == a else "B",
                        a_audio=clips[0], b_audio=clips[1], x_audio=clips[2]))
    return participant, key, recordings


def write_packet(packet: tuple[list[dict], list[dict], list[dict]],
                 participant_path: str | Path, key_path: str | Path,
                 recording_path: str | Path):
    destinations = [Path(x) for x in (participant_path, key_path, recording_path)]
    if (len({p.resolve() for p in destinations}) != 3
            or any(p.exists() for p in destinations)):
        raise VekaError("packet output paths must be distinct, new files")
    written = []
    try:
        for path, (rows, columns) in zip(destinations, zip(
                packet, (RESPONSE_COLUMNS, KEY_COLUMNS, RECORDING_COLUMNS))):
            with path.open("x", encoding="utf-8", newline="") as output:
                written.append(path)
                writer = csv.DictWriter(output, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
    except (OSError, ValueError, csv.Error):
        for path in written:
            path.unlink(missing_ok=True)
        raise


def _verify_wav_files(recordings: list[dict], audio_root: str | Path) -> dict:
    """Structural WAV and independent-take check, NOT a human audio verifier."""
    root = Path(audio_root)
    hashes = set()
    min_rate = 10**9
    for row in recordings:
        name = row["audio_id"]
        if not CLIP_RE.fullmatch(name) or row["recorded"] != "yes":
            raise VekaError(f"missing or unconfirmed recorded WAV: {name}")
        path = root / name
        if (path.is_symlink() or not path.resolve().is_relative_to(root.resolve())
                or not path.is_file() or path.stat().st_size > MAX_WAV_BYTES):
            raise VekaError(f"missing/oversized WAV file: {name}")
        try:
            with wave.open(str(path), "rb") as audio:
                rate = audio.getframerate()
                frames = audio.getnframes()
                channels = audio.getnchannels()
                sample_width = audio.getsampwidth()
            if (not 8000 <= rate <= 192000 or not 1 <= channels <= 2
                    or sample_width not in (1, 2, 3, 4)
                    or not int(0.10 * rate) <= frames <= int(30 * rate)):
                raise VekaError(f"bad WAV metadata/duration: {name}")
            min_rate = min(min_rate, rate)
            digest = hashlib.sha256(path.read_bytes()).digest()
        except (wave.Error, EOFError, OSError) as exc:
            raise VekaError(f"invalid WAV: {name}") from exc
        if digest in hashes:
            raise VekaError("identical recording reused across A/B/X or trials")
        hashes.add(digest)
    return {"wav_file_count": len(hashes), "minimum_sample_rate_hz": min_rate,
            "waveform_identity_checked": True, "human_authenticity_verified": False,
            "snr_verified": False}


def _aggregate(rows: list[dict]) -> dict:
    n = len(rows)
    correct = sum(r["correct"] for r in rows)
    total_ms = sum(r["elapsed_ms"] for r in rows)
    return dict(n=n, correct=correct, accuracy=round(correct / n, 4),
                mean_elapsed_ms=round(total_ms / n, 2),
                correct_decisions_per_minute=round(correct * 60000 / total_ms, 3))


def score_packet(key: list[dict], responses: list[dict],
                 recordings: list[dict], audio_root: str | Path) -> dict:
    """Only score complete, joined responses with existing independent WAVs.

    The returned data describe supplied trial responses. They cannot certify
    volunteers, actual speech, signal-to-noise ratios or comprehension.
    """
    if not key or not responses or not recordings:
        raise VekaError("key, responses and recordings must all be nonempty")
    keys = {}
    for k in key:
        if set(k) != set(KEY_COLUMNS) or k["trial_id"] in keys:
            raise VekaError("bad or repeated answer-key row")
        if (k["correct_option"] not in ("A", "B") or k["a_form"] == k["b_form"]
                or k["x_form"] not in (k["a_form"], k["b_form"])
                or k["correct_option"] != ("A" if k["x_form"] == k["a_form"] else "B")
                or k["condition"] not in CONDITIONS or k["critical"] not in ("yes", "no")):
            raise VekaError("inconsistent answer-key target or channel")
        keys[k["trial_id"]] = k
    if len({k["participant_id"] for k in key}) != 1 or len({k["profile"] for k in key}) != 1:
        raise VekaError("answer key must belong to exactly one participant and profile")
    blocks = defaultdict(list)
    for k in key:
        blocks[(k["contrast_id"], k["talker"], k["condition"])].append(k)
    for block in blocks.values():
        if (len(block) != 2 or Counter(k["correct_option"] for k in block) != Counter({"A": 1, "B": 1})
                or len({(k["a_form"], k["b_form"]) for k in block}) != 1
                or len({k["x_form"] for k in block}) != 2):
            raise VekaError("ABX key lost balanced targets or A/B consistency")
    expected = {}
    for k in key:
        for slot in ("A", "B", "X"):
            audio_id = k[slot.lower() + "_audio"]
            if audio_id in expected:
                raise VekaError("repeated audio ID in answer key")
            expected[audio_id] = (k["trial_id"], slot, k[slot.lower() + "_form"],
                                  k["talker"], k["condition"])
    if len(recordings) != len(expected):
        raise VekaError("recording schedule is incomplete")
    seen_audio = set()
    for r in recordings:
        if set(r) != set(RECORDING_COLUMNS):
            raise VekaError("recording columns do not match schema")
        audio_id = r["audio_id"]
        if audio_id in seen_audio or expected.get(audio_id) != (
                r["trial_id"], r["slot"], r["form"], r["talker"], r["condition"]):
            raise VekaError("recording metadata mismatch or duplicated ID")
        seen_audio.add(audio_id)
    _verify_wav_files(recordings, audio_root)
    if len(responses) != len(key):
        raise VekaError("missing, duplicate or extra participant observations")
    seen_responses = set()
    scored = []
    for r in responses:
        if set(r) != set(RESPONSE_COLUMNS):
            raise VekaError("response columns do not match study schema")
        trial_id = r["trial_id"]
        if trial_id not in keys or trial_id in seen_responses:
            raise VekaError("unknown or duplicate trial")
        seen_responses.add(trial_id)
        k = keys[trial_id]
        if any(r[name] != k[name] for name in (
                "a_audio", "b_audio", "x_audio")):
            raise VekaError("participant sheet metadata differs from answer key")
        try:
            ms = float(r["elapsed_ms"])
        except (ValueError, TypeError) as exc:
            raise VekaError("elapsed_ms must be a positive finite number") from exc
        if not math.isfinite(ms) or ms <= 0 or ms > 600000:
            raise VekaError("elapsed_ms outside allowed range")
        if r["response"] not in ("A", "B"):
            raise VekaError("each trial needs one A/B response")
        scored.append({"trial_id": trial_id, "condition": k["condition"],
                       "contrast_id": k["contrast_id"], "talker": k["talker"],
                       "critical": k["critical"] == "yes",
                       "correct": int(r["response"] == k["correct_option"]),
                       "elapsed_ms": ms,
                       "expected": k["correct_option"], "observed": r["response"]})
    per_condition = {}
    for cond in CONDITIONS:
        group = [r for r in scored if r["condition"] == cond]
        if group:
            per_condition[cond] = _aggregate(group)
    per_pair = []
    for contrast in sorted({r["contrast_id"] for r in scored}):
        group = [r for r in scored if r["contrast_id"] == contrast]
        confusion = {
            "A_as_A": sum(r["expected"] == "A" and r["observed"] == "A" for r in group),
            "A_as_B": sum(r["expected"] == "A" and r["observed"] == "B" for r in group),
            "B_as_A": sum(r["expected"] == "B" and r["observed"] == "A" for r in group),
            "B_as_B": sum(r["expected"] == "B" and r["observed"] == "B" for r in group),
        }
        per_pair.append(dict(contrast_id=contrast, **_aggregate(group),
                             critical=any(r["critical"] for r in group),
                             response_position_confusion=confusion))
    all_stats = _aggregate(scored)
    return {
        "schema_version": "veka.abx-report.v06",
        "participant_count": 1,
        "n_trials": all_stats["n"], "correct": all_stats["correct"],
        "accuracy": all_stats["accuracy"],
        "correct_decisions_per_minute": all_stats["correct_decisions_per_minute"],
        "critical_errors": sum(r["critical"] and not r["correct"] for r in scored),
        "per_condition": per_condition,
        "per_pair": per_pair,
        "per_talker": {t: _aggregate([r for r in scored if r["talker"] == t])
                       for t in sorted({r["talker"] for r in scored})},
        "wav_file_count": len(recordings),
        "independent_recording_bytes_checked": True,
        "human_authenticity_verified": False,
        "snr_verified": False,
        "population_effect_estimated": False,
        "warning": "Only supplied observations and structurally valid, distinct WAV files. No independent verification of human voice, real participants, calibrated SNR, training, or population-level inference. ABX decision rate is NOT correct-message communication throughput.",
    }
