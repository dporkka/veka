"""A single candidate can be assessed independently without fabricated agreement."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.efficiency import default_manifest
from veka.efficiency_review import (
    build_review_packet, build_candidate_rating_packet, evaluate_reviews,
    write_review_packet, read_review_csv
)

ROOT = Path(__file__).resolve().parents[1]


class CandidateBoundReviews(unittest.TestCase):
    def setUp(self):
        self.manifest = default_manifest()
        self.candidates = build_review_packet(self.manifest, "author_01", language="id")
        for row in self.candidates:
            row["target_text"] = f"synthetic-test-{row['item_id']}"
        self.first = build_candidate_rating_packet(self.manifest, self.candidates, "judge_01")
        self.second = build_candidate_rating_packet(self.manifest, self.candidates, "judge_02")

    def test_same_candidate_two_independent_verdicts_and_no_promoted_observations(self):
        for row in self.first + self.second:
            self.assertEqual(row["meaning_equivalent"], "")
            self.assertTrue(row["target_text"].startswith("synthetic-test-"))
            row.update(meaning_equivalent="yes", natural="yes", critical_ambiguity="no")
        report = evaluate_reviews(self.first, self.second, self.manifest,
                                  candidates=self.candidates)
        self.assertTrue(report["publishable"])
        self.assertEqual(report["accepted"], 10)
        self.assertEqual(report["candidate_source_locked"], True)
        self.assertFalse(report["reviewer_independence_authenticated"])
        self.assertFalse(report["human_efficiency_measured"])
        self.assertEqual(report["reviewed_manifest"]["items"][0]["variants"]["id"]["text"],
                         self.candidates[0]["target_text"])

    def test_candidate_cannot_be_blank_or_self_reviewed(self):
        incomplete = copy.deepcopy(self.candidates)
        incomplete[1]["target_text"] = ""
        with self.assertRaises(VekaError):
            build_candidate_rating_packet(self.manifest, incomplete, "judge_01")
        with self.assertRaises(VekaError):
            build_candidate_rating_packet(self.manifest, self.candidates, "author_01")
        with self.assertRaises(VekaError):
            evaluate_reviews(self.first, self.second, self.manifest, candidates=incomplete)

    def test_reviewers_cannot_substitute_another_candidate_or_change_source(self):
        a = copy.deepcopy(self.first)
        b = copy.deepcopy(self.second)
        for row in a + b:
            row.update(meaning_equivalent="yes", natural="yes", critical_ambiguity="no")
        for mutate in ("both_edit", "one_edit", "author_collision", "source_changed"):
            changed_a = copy.deepcopy(a)
            changed_b = copy.deepcopy(b)
            candidate = copy.deepcopy(self.candidates)
            if mutate == "both_edit":
                changed_a[0]["target_text"] = "alternate-valid-translation"
                changed_b[0]["target_text"] = "alternate-valid-translation"
            elif mutate == "one_edit":
                changed_b[0]["target_text"] = "alternate-valid-translation"
            elif mutate == "author_collision":
                changed_a[0]["reviewer_id"] = "author_01"
            else:
                candidate[0]["english_reference"] = "tampered source"
            with self.subTest(mutate=mutate), self.assertRaises(VekaError):
                evaluate_reviews(changed_a, changed_b, self.manifest, candidates=candidate)

    def test_declared_review_rejection_blocks_export(self):
        for row in self.first + self.second:
            row.update(meaning_equivalent="yes", natural="yes", critical_ambiguity="no")
        self.second[0]["meaning_equivalent"] = "no"
        report = evaluate_reviews(self.first, self.second, self.manifest,
                                  candidates=self.candidates)
        self.assertFalse(report["publishable"])
        self.assertEqual(report["blocked"], 1)
        self.assertIsNone(report["reviewed_manifest"])

    def test_csv_formula_in_notes_is_rejected(self):
        self.first[0]["review_notes"] = "=HYPERLINK(\"https://malicious.example\")"
        with self.assertRaises(VekaError):
            evaluate_reviews(self.first, self.second, self.manifest, candidates=self.candidates)
        self.first[0]["review_notes"] = "  +CMD()"
        with self.assertRaises(VekaError):
            evaluate_reviews(self.first, self.second, self.manifest, candidates=self.candidates)

    def test_cli_accepts_only_consistent_synthetic_two_reviewers(self):
        # Test-only synthetic text, never human evidence or checked-in measurements.
        with tempfile.TemporaryDirectory() as tmp:
            paths = {name: Path(tmp) / name for name in
                     ('candidate.csv', 'review-a.csv', 'review-b.csv', 'approved.json')}
            write_review_packet(self.candidates, paths['candidate.csv'])
            for name, rows in (('review-a.csv', self.first), ('review-b.csv', self.second)):
                for row in rows:
                    row.update(meaning_equivalent='yes', natural='yes',
                               critical_ambiguity='no')
                write_review_packet(rows, paths[name])
            cmd = [sys.executable, '-m', 'veka', 'efficiency-review-check',
                   '--candidates', str(paths['candidate.csv']),
                   '--review-a', str(paths['review-a.csv']),
                   '--review-b', str(paths['review-b.csv']),
                   '--output', str(paths['approved.json'])]
            run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(run.stdout)
            self.assertTrue(report['publishable'])
            self.assertTrue(report['candidate_source_locked'])
            self.assertEqual(report['accepted'], 10)
            data = json.loads(paths['approved.json'].read_text(encoding='utf-8'))
            self.assertEqual(data['items'][0]['variants']['id']['text'],
                             self.candidates[0]['target_text'])
            self.assertEqual(paths['approved.json'].stat().st_mode & 0o777, 0o600)
            again = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)

    def test_cli_bind_and_review_check_cannot_export_blank_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate.csv"
            ra = Path(tmp) / "review-a.csv"
            rb = Path(tmp) / "review-b.csv"
            out = Path(tmp) / "approved.json"
            write_review_packet(self.candidates, candidate)
            for reviewer, dest in (("judge_01", ra), ("judge_02", rb)):
                run = subprocess.run([sys.executable, "-m", "veka", "efficiency-review-bind",
                                      "--candidates", str(candidate), "--reviewer", reviewer,
                                      "--output", str(dest)], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(read_review_csv(dest)[0]["target_text"],
                                 self.candidates[0]["target_text"])
                self.assertEqual(dest.stat().st_mode & 0o777, 0o600)
                again = subprocess.run([sys.executable, "-m", "veka", "efficiency-review-bind",
                                        "--candidates", str(candidate), "--reviewer", reviewer,
                                        "--output", str(dest)], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(again.returncode, 2)
            run = subprocess.run([sys.executable, "-m", "veka", "efficiency-review-check",
                                  "--candidates", str(candidate), "--review-a", str(ra),
                                  "--review-b", str(rb), "--output", str(out)],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
