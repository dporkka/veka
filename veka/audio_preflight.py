"""Advisory PCM recording preflight for Veka ABX study banks.

These are signal-level heuristics, not speech authentication, listener
comprehension, pronunciation verification or SNR measurement.
"""
from __future__ import annotations

import hashlib
import math
import struct
import wave
from collections import defaultdict
from pathlib import Path

from .core import VekaError
from .listening_v06 import RECORDING_COLUMNS, CONDITIONS, _verify_wav_files


def _pcm_samples(data: bytes, sample_width: int):
    """Yield normalized PCM samples for little-endian WAV, including unsigned 8-bit."""
    if sample_width == 1:
        for value in data:
            yield (value - 128) / 128
    elif sample_width in (2, 4):
        fmt = "<" + ("h" if sample_width == 2 else "i")
        scale = float(1 << (8 * sample_width - 1))
        for (value,) in struct.iter_unpack(fmt, data):
            yield value / scale
    else:
        for offset in range(0, len(data), 3):
            yield int.from_bytes(data[offset:offset + 3], "little", signed=True) / (1 << 23)


def _analyze_wav(path: Path) -> tuple[dict, bytes]:
    pcm_digest = hashlib.sha256()
    try:
        with wave.open(str(path), "rb") as audio:
            rate = audio.getframerate()
            channels = audio.getnchannels()
            width = audio.getsampwidth()
            declared_frames = audio.getnframes()
            # The structural verifier has already checked the supported format
            # and bounded the file size before this function is called.
            frame_count = sample_count = 0
            sum_values = sum_squares = clipped_samples = 0
            while True:
                chunk = audio.readframes(4096)
                if not chunk:
                    break
                if len(chunk) % (width * channels):
                    raise VekaError(f"truncated WAV sample data: {path.name}")
                pcm_digest.update(chunk)
                frame_count += len(chunk) // (width * channels)
                for value in _pcm_samples(chunk, width):
                    sample_count += 1
                    sum_values += value
                    sum_squares += value * value
                    clipped_samples += abs(value) >= 0.995
            if frame_count != declared_frames or not sample_count:
                raise VekaError(f"truncated WAV audio data: {path.name}")
    except (wave.Error, EOFError, OSError, ValueError, struct.error, ZeroDivisionError) as exc:
        raise VekaError(f"invalid or truncated WAV: {path.name}") from exc

    rms = math.sqrt(sum_squares / sample_count)
    mean = sum_values / sample_count
    rms_dbfs = 20 * math.log10(rms) if rms else -math.inf
    clipping = clipped_samples / sample_count
    warnings = []
    # Conservative triage triggers, not calibrated thresholds or pass/fail science.
    if rms_dbfs < -45:
        warnings.append("near_silence")
    if clipping >= 0.01:
        warnings.append("possible_clipping")
    if abs(mean) >= 0.1:
        warnings.append("large_dc_offset")
    return {
        "duration_seconds": round(frame_count / rate, 4),
        "sample_rate_hz": rate,
        "sample_width_bytes": width,
        "channels": channels,
        "rms_dbfs": round(rms_dbfs, 2) if math.isfinite(rms_dbfs) else None,
        "dc_fraction": round(mean, 4),
        "clipped_fraction": round(clipping, 4),
        "warnings": warnings,
    }, pcm_digest.digest()


def audit_recordings(recordings: list[dict], audio_root: str | Path) -> dict:
    """Audit a *completed* ABX recording manifest; fail closed on malformed banks.

    Warnings flag clips for independent listening and operator adjudication.
    'No warnings' does not indicate human voice, accurate lexical production,
    genuine independent takes, or a calibrated noise condition.
    """
    if not recordings:
        raise VekaError("recording manifest is empty")
    by_trial = defaultdict(list)
    seen = set()
    for row in recordings:
        if (set(row) != set(RECORDING_COLUMNS)
                or any(not isinstance(row[key], str) for key in RECORDING_COLUMNS)
                or row["audio_id"] in seen
                or row["slot"] not in ("A", "B", "X")
                or row["condition"] not in CONDITIONS):
            raise VekaError("invalid or duplicate recording manifest row")
        seen.add(row["audio_id"])
        by_trial[row["trial_id"]].append(row)
    for rows in by_trial.values():
        forms = {r["slot"]: r["form"] for r in rows}
        if (len(rows) != 3 or set(forms) != {"A", "B", "X"}
                or forms["A"] == forms["B"]
                or forms["X"] not in (forms["A"], forms["B"])
                or len({r["talker"] for r in rows}) != 1
                or len({r["condition"] for r in rows}) != 1):
            raise VekaError("recording manifest has incomplete or inconsistent ABX trial")
    _verify_wav_files(recordings, audio_root)
    # Scan only paths previously validated as in-root regular files by the
    # same verifier as the scorer; never expose raw audio in the JSON report.
    clips, seen_pcm = [], set()
    for row in sorted(recordings, key=lambda r: r["audio_id"]):
        metrics, digest = _analyze_wav(Path(audio_root) / row["audio_id"])
        if digest in seen_pcm:
            raise VekaError("identical PCM audio reused across A/B/X or trials")
        seen_pcm.add(digest)
        clips.append({"audio_id": row["audio_id"], **metrics})
    return {
        "schema_version": "veka.audio-preflight.v01",
        "clip_count": len(clips),
        "review_count": sum(bool(clip["warnings"]) for clip in clips),
        "clips": clips,
        "pcm_identity_checked": True,
        "manual_review_required": True,
        "human_speech_verified": False,
        "snr_verified": False,
        "pronunciation_verified": False,
        "independent_takes_verified": False,
        "thresholds": {
            "near_silence_rms_dbfs_below": -45,
            "clipping_sample_absolute_fraction_at_least": 0.995,
            "clipping_samples_share_at_least": 0.01,
            "dc_absolute_fraction_at_least": 0.1,
        },
        "note": "Signal screening only. A researcher must listen to every recording, verify provenance and calibrate noise externally.",
    }
