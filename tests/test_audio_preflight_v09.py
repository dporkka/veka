"""Synthetic signal fixtures test preflight plumbing, NOT recorded Veka speech."""
import csv
import json
import math
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

from veka.core import VekaError
from veka.audio_preflight import audit_recordings

ROOT = Path(__file__).resolve().parents[1]


def write_wav(path, *, frequency=250, amplitude=0.3, dc=0.0, width=2, channels=1):
    rate = 16000
    values = []
    for n in range(3200):
        value = max(-1.0, min(0.9999, dc + amplitude * math.sin(2 * math.pi * frequency * n / rate)))
        if width == 1:
            sample = bytes([round(128 + value * 127)])
        elif width == 3:
            sample = round(value * (2**23 - 1)).to_bytes(3, "little", signed=True)
        else:
            bits = width * 8
            sample = round(value * (2**(bits-1)-1)).to_bytes(width, "little", signed=True)
        values.append(sample * channels)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(channels)
        out.setsampwidth(width)
        out.setframerate(rate)
        out.writeframes(b"".join(values))


def make_rows(root, *, width=2, channels=1):
    rows = []
    for i, slot in enumerate("ABX"):
        audio_id = f"clip_deadbeefcafe_{i+1:05d}.wav"
        write_wav(root / audio_id, frequency=250 + 80*i, width=width, channels=channels)
        rows.append({"audio_id": audio_id, "trial_id": "trial_0001",
                     "slot": slot, "form": "mi" if slot != "B" else "ni",
                     "talker": "S01", "condition": "quiet", "recorded": "yes"})
    return rows


class AudioPreflightTests(unittest.TestCase):
    def test_valid_pcm_reports_metrics_without_claiming_human_or_snr_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = make_rows(Path(directory))
            report = audit_recordings(rows, directory)
            self.assertEqual(report["schema_version"], "veka.audio-preflight.v01")
            self.assertEqual(report["clip_count"], 3)
            self.assertEqual(report["review_count"], 0)
            self.assertFalse(report["human_speech_verified"])
            self.assertFalse(report["snr_verified"])
            self.assertTrue(report["manual_review_required"])
            self.assertTrue(all(-15 < x["rms_dbfs"] < -10 for x in report["clips"]))
            self.assertTrue(all(x["warnings"] == [] for x in report["clips"]))

    def test_supported_pcm_widths_and_stereo_are_decoded_correctly(self):
        for width in (1, 2, 3, 4):
            with self.subTest(width=width), tempfile.TemporaryDirectory() as directory:
                rows = make_rows(Path(directory), width=width, channels=2)
                report = audit_recordings(rows, directory)
                self.assertEqual(report["review_count"], 0)
                self.assertEqual({item["sample_width_bytes"] for item in report["clips"]}, {width})
                self.assertEqual({item["channels"] for item in report["clips"]}, {2})

    def test_silence_clipping_and_dc_are_distinct_advisory_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = make_rows(root)
            write_wav(root / rows[0]["audio_id"], amplitude=0.0)
            write_wav(root / rows[1]["audio_id"], amplitude=0.0, dc=0.9999)
            write_wav(root / rows[2]["audio_id"], amplitude=0.1, dc=0.4)
            report = audit_recordings(rows, root)
            warnings = {row["audio_id"]: row["warnings"] for row in report["clips"]}
            self.assertIn("near_silence", warnings[rows[0]["audio_id"]])
            self.assertIn("possible_clipping", warnings[rows[1]["audio_id"]])
            self.assertIn("large_dc_offset", warnings[rows[2]["audio_id"]])
            self.assertEqual(report["review_count"], 3)

    def test_rejects_reused_pcm_when_wav_headers_differ(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = make_rows(root)
            source = root / rows[0]["audio_id"]
            destination = root / rows[2]["audio_id"]
            # Appending a trailing non-audio metadata byte changes the file hash
            # but not the decoded PCM frames.
            destination.write_bytes(source.read_bytes() + b"JUNK")
            with self.assertRaisesRegex(VekaError, "identical PCM"):
                audit_recordings(rows, root)

    def test_rejects_truncated_wav_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = make_rows(root)
            path = root / rows[1]["audio_id"]
            path.write_bytes(path.read_bytes()[:-200])
            with self.assertRaisesRegex(VekaError, "truncated WAV"):
                audit_recordings(rows, root)

    def test_rejects_incomplete_or_duplicate_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = make_rows(root)
            for bad in (rows[:2], rows + rows[:1], [dict(r, recorded="no") for r in rows],
                        [dict(r, slot="A") for r in rows],
                        [dict(r, unexpected="bad") for r in rows]):
                with self.subTest(bad=bad), self.assertRaises(VekaError):
                    audit_recordings(bad, root)

    def test_cli_prints_machine_readable_preflight_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = make_rows(root)
            manifest = root / "recording_jobs.csv"
            with manifest.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            run = subprocess.run([sys.executable, "-m", "veka", "listening-preflight",
                                  "--recording-csv", str(manifest), "--audio-root", str(root)],
                                 cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["clip_count"], 3)


if __name__ == "__main__":
    unittest.main()
