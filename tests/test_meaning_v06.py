"""Blinded meaning-recovery pilot: machine contracts only, no human data."""
import csv
import json
import os
import subprocess
import sys
import stat
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.meaning_v06 import make_meaning_packet, write_meaning_packet

ROOT = Path(__file__).resolve().parents[1]
ITEMS = json.loads((ROOT / "data/study_items_v03.json").read_text(encoding="utf-8"))


class BlindedMeaningTests(unittest.TestCase):
    def test_all_items_are_balanced_and_produce_blind_participant_sheet(self):
        participant, key, recording = make_meaning_packet(ITEMS, "P001", arm=0, seed=23)
        self.assertEqual(len(participant), 32)
        self.assertEqual(len(key), 32)
        self.assertEqual(len(recording), 32)
        self.assertEqual(len({r["item_id"] for r in key}), 32)
        self.assertEqual(sum(r["condition"] == "explicit" for r in key), 16)
        self.assertEqual(sum(r["condition"] == "compact" for r in key), 16)
        self.assertEqual(len({r["audio_id"] for r in participant}), 32)
        self.assertEqual({r["response_text"] for r in participant}, {""})
        self.assertEqual({r["elapsed_ms"] for r in participant}, {""})
        self.assertFalse(set(participant[0]) & {"meaning", "utterance", "condition", "critical", "item_id"})
        self.assertEqual(set(participant[0]), {"trial_id", "audio_id", "context_json", "response_text", "elapsed_ms", "repairs"})
        self.assertTrue(all(r["recorded"] == "no" for r in recording))

    def test_opposite_arms_reverse_each_meaning_with_stable_audio_bank(self):
        a=make_meaning_packet(ITEMS, "P001", arm=0, seed=23)
        b=make_meaning_packet(ITEMS, "P002", arm=1, seed=23)
        c=make_meaning_packet(ITEMS, "P999", arm=0, seed=9)
        ak={r["item_id"]:r for r in a[1]}
        bk={r["item_id"]:r for r in b[1]}
        ck={r["item_id"]:r for r in c[1]}
        self.assertTrue(all(ak[k]["condition"]!=bk[k]["condition"] for k in ak))
        self.assertTrue(all(ak[k]["audio_id"]==ck[k]["audio_id"] for k in ak))
        self.assertEqual(a, make_meaning_packet(ITEMS, "P001", arm=0, seed=23))

    def test_meaning_mismatch_or_invalid_items_fail_closed(self):
        for bad in (
            ITEMS + [ITEMS[0]],
            [dict(ITEMS[0], compact="Ti pa gos.")] + ITEMS[1:],
            [dict(ITEMS[0], explicit="Mi xyz mel.")] + ITEMS[1:],
            [dict(ITEMS[0], item_id="../bad")] + ITEMS[1:],
        ):
            with self.subTest(change=bad[0]), self.assertRaises(VekaError):
                make_meaning_packet(bad, "P001", arm=0)
        for participant, arm in (("",0),("P/unsafe",0),("P001",True),("P001",3)):
            with self.subTest(participant=participant, arm=arm), self.assertRaises(VekaError):
                make_meaning_packet(ITEMS, participant, arm=arm)

    def test_writes_separate_private_files_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            p,k,r=(Path(d)/v for v in ("participant.csv","researcher.csv","recording.csv"))
            packet=make_meaning_packet(ITEMS,"P001",arm=0)
            result=write_meaning_packet(packet,p,k,r)
            self.assertFalse(result["human_data_collected"])
            self.assertFalse(result["audio_recorded"])
            with p.open(newline="") as f:
                self.assertNotIn("meaning",next(csv.DictReader(f)))
            if os.name=="posix":
                self.assertEqual(stat.S_IMODE(k.stat().st_mode),0o600)
                self.assertEqual(stat.S_IMODE(r.stat().st_mode),0o600)
            with self.assertRaises(VekaError):
                write_meaning_packet(packet,p,k,r)
            with self.assertRaises(VekaError):
                write_meaning_packet(packet,p,p,r)

    def test_cli_participant_output_has_no_researcher_fields(self):
        with tempfile.TemporaryDirectory() as d:
            p,k,r=(Path(d)/v for v in ("participant.csv","researcher.csv","recording.csv"))
            run=subprocess.run(
                [sys.executable, "-m", "veka", "meaning-plan",
                 "--participant", "P123", "--arm", "1",
                 "--participant-csv", str(p), "--key-csv", str(k),
                 "--recording-csv", str(r)],
                capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 0, run.stderr)
            public=json.loads(run.stdout)
            self.assertEqual(public["trials"], 32)
            self.assertFalse(public["human_data_collected"])
            self.assertNotIn("meaning", public)
            self.assertNotIn("utterance", public)
            self.assertNotIn("condition", public)
            self.assertNotIn("recorded WAV", run.stdout)
            with p.open(encoding="utf-8", newline="") as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows), 32)
            self.assertFalse(any("meaning" in r or "condition" in r for r in rows))

    def test_immutable_audio_ids_change_when_stimulus_changes(self):
        original=make_meaning_packet(ITEMS,"P001",arm=0)[1]
        changed=[dict(r) for r in ITEMS]
        changed[0]["explicit"]="Mi fu dak mel to ti sun"
        changed[0]["meaning"]="I will send you the message tomorrow"
        altered=make_meaning_packet(changed,"P001",arm=0)[1]
        self.assertNotEqual(
            next(r for r in original if r["item_id"]=="ellipsis-01")["audio_id"],
            next(r for r in altered if r["item_id"]=="ellipsis-01")["audio_id"])
