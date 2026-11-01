"""Veka 0.6 preregistered listening-pilot infrastructure tests.

Synthetic WAV fixtures in this file validate FILE PLUMBING ONLY.
They do not constitute any human speech or experimental result.
"""
import csv
import hashlib
import io
import json
import math
import tempfile
import unittest
import wave
from collections import Counter, defaultdict
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from veka.core import VekaError
from veka.profiles import load_profile
from veka.listening_v06 import (
    load_contrasts, make_packet, score_packet, read_csv,
    write_packet, RESPONSE_COLUMNS, KEY_COLUMNS, RECORDING_COLUMNS,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRASTS = ROOT / "data/listening_contrasts_v06.csv"


def sample_wav(path: Path, index: int):
    # Test-only distinguishable arbitrary waveforms; NOT Veka speech.
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(bytes([index % 250 + 1, (index // 250) % 250 + 1]) * 3200)


def csv_write(path, rows, columns):
    with Path(path).open("w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


class PilotPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tonal = load_profile("tonal")
        cls.toneless = load_profile("toneless")

    def test_curated_contrasts_have_known_forms_and_tone_exclusion(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")
        tonefree = load_contrasts(CONTRASTS, self.toneless, "toneless")
        self.assertGreaterEqual(len(pairs), 10)
        self.assertEqual(len(tonefree), len(pairs) - 1)
        self.assertEqual(sum(p["category"] == "tone" for p in pairs), 1)
        self.assertFalse(any(p["category"] == "tone" for p in tonefree))

    def test_invalid_or_duplicate_contrasts_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "c.csv"
            columns = ["contrast_id", "a", "b", "category", "critical", "profile"]
            for cases in [
                [["bad", "mi", "mi", "pronoun", "yes", "both"]],
                [["bad", "unknown", "mi", "pronoun", "yes", "both"]],
                [["dup", "mi", "ni", "pronoun", "yes", "both"],
                 ["dup", "mi", "ti", "pronoun", "yes", "both"]],
                [["bad", "mi", "ni", "pronoun", "maybe", "both"]],
                [["bad", "mi", "ni", "pronoun", "yes", "guess"]],
            ]:
                with self.subTest(cases=cases):
                    csv_write(f, [dict(zip(columns, row)) for row in cases], columns)
                    with self.assertRaises(VekaError):
                        load_contrasts(f, self.tonal, "tonal")

    def test_blinding_and_block_balance_with_independent_audio_ids(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")
        participant, key, recordings = make_packet(pairs, "P012", ("S01", "S02"), "tonal", seed=17, arm=0)
        self.assertEqual(len(key), len(pairs) * 2 * 2 * 2)
        self.assertEqual(len(participant), len(key))
        self.assertEqual(len(recordings), len(key) * 3)
        self.assertEqual(set(participant[0]), set(RESPONSE_COLUMNS))
        self.assertNotIn("condition", participant[0])
        self.assertNotIn("talker", participant[0])
        self.assertEqual(set(key[0]), set(KEY_COLUMNS))
        self.assertEqual(set(recordings[0]), set(RECORDING_COLUMNS))
        self.assertTrue(all(row["response"] == "" and not any(
            forbidden in row for forbidden in ("correct_option", "a_form", "x_form", "contrast_id"))
                            for row in participant))
        self.assertEqual(len({r["audio_id"] for r in recordings}), len(recordings))
        self.assertTrue(all(r["recorded"] == "no" for r in recordings))
        groups = defaultdict(Counter)
        for row in key:
            groups[(row["contrast_id"], row["talker"], row["condition"])][row["correct_option"]] += 1
        self.assertTrue(all(counts == Counter({"A": 1, "B": 1}) for counts in groups.values()))
        self.assertEqual({row["condition"] for row in key}, {"quiet", "noise_plus5db"})

    def test_reproducible_allocation_and_explicit_balancing_arm(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")
        p0 = make_packet(pairs, "P013", ("S01",), "tonal", seed=77, arm=0)
        self.assertEqual(p0, make_packet(pairs, "P013", ("S01",), "tonal", seed=77, arm=0))
        p1 = make_packet(pairs, "P013", ("S01",), "tonal", seed=77, arm=1)
        self.assertNotEqual(p0[1], p1[1])
        self.assertEqual(len(p0[1]), len(p1[1]))
        with self.assertRaises(VekaError):
            make_packet(pairs, "bad/id", ("S01",), "tonal")
        with self.assertRaises(VekaError):
            make_packet(pairs, "P001", ("S01", "S01"), "tonal")
        with self.assertRaises(VekaError):
            make_packet(pairs, "P001", ("S01",), "tonal", arm=2)

    def test_recorded_stimuli_can_be_reused_across_participants_in_same_arm(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")[:3]
        packet_a = make_packet(pairs, "P013", ("S01", "S02"), "tonal", seed=77, arm=0)
        packet_b = make_packet(pairs, "P014", ("S01", "S02"), "tonal", seed=77, arm=0)
        packet_c = make_packet(pairs, "P014", ("S01", "S02"), "tonal", seed=77, arm=1)
        def bank(packet):
            return sorted((r["audio_id"], r["form"], r["talker"],
                           r["condition"], r["slot"]) for r in packet[2])
        self.assertEqual(bank(packet_a), bank(packet_b))
        self.assertNotEqual(packet_a[0], packet_b[0])
        self.assertTrue({r["audio_id"] for r in packet_a[2]}.isdisjoint(
            {r["audio_id"] for r in packet_c[2]}))

    def test_different_stimulus_definitions_never_share_clip_identifiers(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")[:3]
        original = make_packet(pairs, "P013", ("S01",), "tonal", seed=77, arm=0)
        reordered = make_packet(pairs[::-1], "P013", ("S01",), "tonal", seed=77, arm=0)
        reduced = make_packet(pairs[:2], "P013", ("S01",), "tonal", seed=77, arm=0)
        get_ids = lambda packet: {r["audio_id"] for r in packet[2]}
        self.assertTrue(get_ids(original).isdisjoint(get_ids(reordered)))
        self.assertTrue(get_ids(original).isdisjoint(get_ids(reduced)))

    def test_writer_refuses_overwrites_and_aliasing(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")
        packet = make_packet(pairs, "P001", ("S01",), "tonal")
        with tempfile.TemporaryDirectory() as d:
            paths = [Path(d) / n for n in ("participant.csv", "key.csv", "recordings.csv")]
            write_packet(packet, *paths)
            self.assertEqual(len(read_csv(paths[0])), len(packet[0]))
            with self.assertRaises(VekaError):
                write_packet(packet, *paths)
            with self.assertRaises(VekaError):
                write_packet(packet, paths[0], paths[0], paths[2])

    def test_scoring_requires_complete_genuine_wav_files_and_responses(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")[:2]
        participant, key, recordings = make_packet(
            pairs, "P001", ("S01",), "tonal", seed=1, arm=0)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            answers = [dict(r, response=k["correct_option"], elapsed_ms="1200")
                       for r, k in zip(participant, key)]
            # Participant and key are independently sorted by the SAME trial_id, not
            # necessarily presentation order: match responses by trial ID.
            by_key = {k["trial_id"]: k for k in key}
            answers = [dict(r, response=by_key[r["trial_id"]]["correct_option"], elapsed_ms="1200")
                       for r in participant]
            with self.assertRaises(VekaError):
                score_packet(key, answers, recordings, root)
            for index, row in enumerate(recordings):
                sample_wav(root / row["audio_id"], index)
                row["recorded"] = "yes"
            scored = score_packet(key, answers, recordings, root)
            self.assertEqual(scored["n_trials"], len(key))
            self.assertEqual(scored["correct"], len(key))
            self.assertFalse(scored["human_authenticity_verified"])
            self.assertFalse(scored["snr_verified"])
            self.assertEqual(scored["per_condition"]["quiet"]["accuracy"], 1.0)
            self.assertEqual(scored["per_condition"]["noise_plus5db"]["accuracy"], 1.0)
            self.assertEqual(len(scored["per_pair"]), 2)
            self.assertTrue(all(item["correct"] == item["n"] for item in scored["per_pair"]))

            duplicate = [dict(r) for r in recordings]
            (root / duplicate[1]["audio_id"]).write_bytes((root / duplicate[0]["audio_id"]).read_bytes())
            with self.assertRaises(VekaError):
                score_packet(key, answers, duplicate, root)

    def test_incorrect_abx_response_is_counted_as_critical_error(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")[:1]
        participant, key, recordings = make_packet(pairs, "P099", ("S01",), "tonal")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for i, recording in enumerate(recordings):
                sample_wav(root / recording["audio_id"], i)
                recording["recorded"] = "yes"
            by_id = {row["trial_id"]: row for row in key}
            answers = [dict(r, response=by_id[r["trial_id"]]["correct_option"],
                            elapsed_ms="1500") for r in participant]
            answers[0]["response"] = "B" if answers[0]["response"] == "A" else "A"
            result = score_packet(key, answers, recordings, root)
            self.assertEqual(result["correct"], result["n_trials"] - 1)
            self.assertEqual(result["critical_errors"], 1)
            confusion = result["per_pair"][0]["response_position_confusion"]
            self.assertEqual(confusion["A_as_B"] + confusion["B_as_A"], 1)
            self.assertFalse(result["population_effect_estimated"])

    def test_scoring_rejects_missing_duplicate_extraneous_and_invalid_answers(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")[:1]
        participant, key, recordings = make_packet(pairs, "P001", ("S01",), "tonal")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for index, row in enumerate(recordings):
                sample_wav(root / row["audio_id"], index)
                row["recorded"] = "yes"
            lookup = {k["trial_id"]: k for k in key}
            answers = [dict(r, response=lookup[r["trial_id"]]["correct_option"], elapsed_ms="1000")
                       for r in participant]
            corrupted = [answers[:-1], answers + answers[:1],
                         [dict(answers[0], trial_id="invented")] + answers[1:],
                         [dict(answers[0], response="C")] + answers[1:],
                         [dict(answers[0], elapsed_ms="NaN")] + answers[1:]]
            for rows in corrupted:
                with self.subTest(rows=len(rows)), self.assertRaises(VekaError):
                    score_packet(key, rows, recordings, root)

    def test_scoring_rejects_tampered_target_balance(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")[:1]
        participant, key, recordings = make_packet(pairs, "P008", ("S01",), "tonal")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for i, row in enumerate(recordings):
                sample_wav(root / row["audio_id"], i)
                row["recorded"] = "yes"
            answers = [dict(row,
                            response=next(k["correct_option"] for k in key
                                          if k["trial_id"] == row["trial_id"]),
                            elapsed_ms="1000") for row in participant]
            tampered = [dict(row) for row in key]
            tampered[0]["x_form"] = (
                tampered[0]["b_form"] if tampered[0]["correct_option"] == "A"
                else tampered[0]["a_form"])
            tampered[0]["correct_option"] = (
                "A" if tampered[0]["x_form"] == tampered[0]["a_form"] else "B")
            with self.assertRaises(VekaError):
                score_packet(tampered, answers, recordings, root)

    def test_scoring_rejects_symlinked_recording(self):
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")[:1]
        participant, key, recordings = make_packet(pairs, "P008", ("S01",), "tonal")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "audio"
            root.mkdir()
            for i, row in enumerate(recordings):
                sample_wav(root / row["audio_id"], i)
                row["recorded"] = "yes"
            (root / recordings[0]["audio_id"]).unlink()
            outside = Path(d) / "outside.wav"
            sample_wav(outside, 109)
            try:
                (root / recordings[0]["audio_id"]).symlink_to(outside)
                by_id = {k["trial_id"]: k for k in key}
                answers = [dict(r,
                                response=by_id[r["trial_id"]]["correct_option"],
                                elapsed_ms="1000") for r in participant]
                with self.assertRaises(VekaError):
                    score_packet(key, answers, recordings, root)
            finally:
                outside.unlink(missing_ok=True)

    def test_cli_generates_separate_files_without_claiming_human_data(self):
        from veka.__main__ import main
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            paths = [root / name for name in ("participant.csv", "key.csv", "recordings.csv")]
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(["listening-plan", "--participant", "PTEST",
                             "--talker", "S01", "--arm", "1",
                             "--participant-csv", str(paths[0]),
                             "--key-csv", str(paths[1]),
                             "--recording-csv", str(paths[2])])
            self.assertEqual(code, 0)
            status = json.loads(stdout.getvalue())
            self.assertFalse(status["human_results_collected"])
            self.assertFalse(status["audio_recorded"])
            self.assertTrue(all(p.exists() for p in paths))
            self.assertEqual(len(read_csv(paths[0])), len(read_csv(paths[1])))

    def test_cli_scores_completed_file_based_synthetic_fixture(self):
        from veka.__main__ import main
        pairs = load_contrasts(CONTRASTS, self.tonal, "tonal")[:1]
        participant, key, recordings = make_packet(pairs, "P101", ("S01",), "tonal")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            by_id = {r["trial_id"]: r for r in key}
            answers = [dict(r, response=by_id[r["trial_id"]]["correct_option"],
                            elapsed_ms="2000") for r in participant]
            for i, row in enumerate(recordings):
                sample_wav(root / row["audio_id"], i)
                row["recorded"] = "yes"
            kpath, rpath, spath = (root / p for p in ("key.csv", "recordings.csv", "responses.csv"))
            csv_write(kpath, key, KEY_COLUMNS)
            csv_write(rpath, recordings, RECORDING_COLUMNS)
            csv_write(spath, answers, RESPONSE_COLUMNS)
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["listening-score", "--key-csv", str(kpath),
                             "--responses-csv", str(spath),
                             "--recording-csv", str(rpath), "--audio-root", str(root)])
            self.assertEqual(code, 0)
            scored = json.loads(output.getvalue())
            self.assertEqual(scored["schema_version"], "veka.abx-report.v06")
            self.assertEqual(scored["correct"], scored["n_trials"])
            self.assertFalse(scored["human_authenticity_verified"])


if __name__ == "__main__":
    unittest.main()
