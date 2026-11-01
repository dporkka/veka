"""v0.10 source-lead validation and participant-blind first-sight packet."""
import csv
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.global_comprehension import EVIDENCE_FIELDS, read_global_csv
from veka.international import read_candidates, generate_recognition_manifest, write_csv
from veka.international_plan import build_international_plan, read_review_priorities
from veka.international_session import (read_international_manifest, write_international_session,
                                        prepare_international_judge_sheet)

ROOT = Path(__file__).resolve().parents[1]


class SourceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")
        cls.candidates = read_candidates(ROOT / "data/international_candidates_v10.csv")
        cls.priorities = read_review_priorities(ROOT / "data/international_priorities_v10.csv")
        cls.leads = read_global_csv(ROOT / "data/international_source_leads_v10.csv", EVIDENCE_FIELDS)

    def test_source_ledger_is_an_unverified_research_queue(self):
        self.assertGreaterEqual(len(self.leads), 12)
        self.assertTrue(all(row["attestation_verified"] == "no"
                            and row["semantic_equivalent"] == "unknown"
                            and not row["semantic_reviewer"] for row in self.leads))
        report = build_international_plan(self.candidates, self.lex, self.priorities, self.leads)
        self.assertEqual(report["source_leads_pending_review"], len(self.leads))
        self.assertEqual(report["verified_attestations_claimed"], 0)
        self.assertFalse(report["adoption_authorized"])
        music = next(item for item in report["queue"] if item["gloss"] == "music")
        self.assertGreaterEqual(music["source_leads_pending_review"], 3)
        self.assertEqual(music["next_action"], "review_source_leads")
        self.assertEqual(music["verified_families"], 0)
        self.assertTrue(music["source_links"])

    def test_malformed_or_claimed_verified_leads_fail_closed(self):
        samples = [
            [dict(self.leads[0], source_url="javascript:alert(1)")],
            [dict(self.leads[0], semantic_equivalent="yes")],
            [dict(self.leads[0], attestation_verified="yes")],
            [dict(self.leads[0], candidate_form="mu-zi-ka")],
            [self.leads[0], self.leads[0]],
            [dict(self.leads[0], source_url="https://example.org/\nX")],
        ]
        for invalid in samples:
            with self.subTest(invalid=invalid):
                with self.assertRaises(VekaError):
                    build_international_plan(self.candidates, self.lex, self.priorities, invalid)


class InternationalSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")
        cls.candidates = read_candidates(ROOT / "data/international_candidates_v10.csv")

    def test_blind_balanced_participant_sessions(self):
        a, key_a = generate_recognition_manifest(self.candidates, self.lex, "VKA101")
        b, key_b = generate_recognition_manifest(self.candidates, self.lex, "VKA102")
        self.assertEqual(len(a), 24)
        self.assertEqual(len(b), 24)
        by_a = {row["concept_id"]: row["condition"] for row in key_a}
        by_b = {row["concept_id"]: row["condition"] for row in key_b}
        self.assertTrue(all(by_a[cid] != by_b[cid] for cid in by_a))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "participant.csv"
            output = Path(directory) / "participant.json"
            write_csv(path, a)
            read = read_international_manifest(path)
            result = write_international_session(read, output)
            data = json.loads(output.read_text(encoding="utf8"))
            self.assertEqual(len(data["trials"]), 24)
            self.assertFalse(result["answer_key_embedded"])
            self.assertFalse(result["human_data_collected"])
            self.assertEqual(set(data), {"schema_version", "participant_id", "trials"})
            self.assertTrue(all(set(row) == {"trial_id", "presented_form"}
                                for row in data["trials"]))
            with self.assertRaises(VekaError):
                write_international_session(read, output)  # fail closed on overwrite

    def test_reject_answer_key_prefilled_and_bad_ids(self):
        visible, key = generate_recognition_manifest(self.candidates, self.lex, "VKA101")
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "sheet.csv"
            write_csv(file, key)
            with self.assertRaises(VekaError):
                read_international_manifest(file)
            for edit in ({"response_gloss": "music"},
                         {"trial_id": "C07-123456789abcdef0"},
                         {"presentation_modality": "audio"},
                         {"participant_id": "../secret"}):
                modified = [dict(row) for row in visible]
                modified[0].update(edit)
                file = Path(directory) / ("bad_" + next(iter(edit)) + ".csv")
                write_csv(file, modified)
                with self.assertRaises(VekaError):
                    read_international_manifest(file)

    def test_existing_browser_supports_both_blinded_schema_versions(self):
        page = (ROOT / "site/cognate-study.html").read_text(encoding="utf8")
        self.assertIn("veka.cognate-session.v07", page)
        self.assertIn("veka.international-session.v10", page)
        self.assertIn("session.trials.length", page)
        self.assertNotIn("if(index>=18)", page)
        self.assertNotIn("if(index<18)", page)

    def test_browser_responses_require_manual_adjudication(self):
        visible, key = generate_recognition_manifest(self.candidates, self.lex, "VKA101")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            key_file = base / "private_key.csv"
            response_file = base / "responses.csv"
            judge_file = base / "judge.csv"
            write_csv(key_file, key)
            response_rows = [{
                "participant_id": row["participant_id"],
                "trial_id": row["trial_id"],
                "presented_form": row["presented_form"],
                "response_gloss": "unsure",
                "response_ms": "1250",
                "prior_exposure": "no",
                "first_language": "English",
                "language_background_family": "Indo-European",
                "timing_interrupted": "no",
            } for row in visible]
            write_csv(response_file, response_rows)
            result = prepare_international_judge_sheet(key_file, response_file, judge_file)
            with judge_file.open(encoding="utf8", newline="") as stream:
                judged = list(csv.DictReader(stream))
            self.assertEqual(len(judged), 24)
            self.assertTrue(all(r["correct"] == "" and r["repair_count"] == ""
                                for r in judged))
            self.assertTrue(all("condition" not in row for row in judged))
            self.assertEqual(result["manually_scored"], 0)
            self.assertFalse(result["human_benefit_established"])
            with self.assertRaises(VekaError):
                prepare_international_judge_sheet(key_file, response_file, judge_file)
            response_rows[0]["presented_form"] = "a-fo"
            tampered = base / "tampered.csv"
            write_csv(tampered, response_rows)
            with self.assertRaises(VekaError):
                prepare_international_judge_sheet(key_file, tampered, base / "bad_judge.csv")

    def test_cli_export_no_key_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.csv"
            target = Path(directory) / "session.json"
            visible, _ = generate_recognition_manifest(self.candidates, self.lex, "VKA101")
            write_csv(manifest, visible)
            result = subprocess.run([sys.executable, "-m", "veka", "international-session",
                                     "--manifest", str(manifest), "--output", str(target)],
                                    cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(target.read_text(encoding="utf8"))
            self.assertEqual(data["schema_version"], "veka.international-session.v10")
            self.assertNotIn("target_gloss", target.read_text(encoding="utf8"))
            self.assertNotIn("condition", target.read_text(encoding="utf8"))
