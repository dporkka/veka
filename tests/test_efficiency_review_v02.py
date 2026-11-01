"""No review-promotion without two independently declared agreeing reviews."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.efficiency import default_manifest, audit_efficiency
from veka.efficiency_review import (REVIEW_LANGUAGES, REVIEW_FIELDS,
                                    build_review_packet, write_review_packet,
                                    evaluate_reviews, read_review_csv)

ROOT = Path(__file__).resolve().parents[1]


class EfficiencyReviewTests(unittest.TestCase):
    def setUp(self):
        self.manifest = default_manifest()
        self.a = build_review_packet(self.manifest, "reviewer_A")
        self.b = build_review_packet(self.manifest, "reviewer_B")

    def completed(self):
        a, b = copy.deepcopy(self.a), copy.deepcopy(self.b)
        for rows in (a, b):
            for row in rows:
                # Synthetic test fixtures only. Never saved as real translations.
                row["target_text"] = f"test-example-{row['language']}-{row['item_id']}"
                row["meaning_equivalent"] = "yes"
                row["natural"] = "yes"
                row["critical_ambiguity"] = "no"
        return a, b

    def test_separate_independent_reviewers_per_language_and_incremental_adoption(self):
        manifest = self.manifest
        for lang in REVIEW_LANGUAGES:
            a = build_review_packet(manifest, f'{lang}_editor_a', language=lang)
            b = build_review_packet(manifest, f'{lang}_editor_b', language=lang)
            self.assertEqual(len(a), 10)
            self.assertEqual({row['language'] for row in a}, {lang})
            for packet in (a, b):
                for row in packet:
                    row.update(target_text=f'test-{lang}-{row["item_id"]}',
                               meaning_equivalent='yes', natural='yes', critical_ambiguity='no')
            report = evaluate_reviews(a, b, manifest)
            self.assertTrue(report['publishable'])
            self.assertEqual(report['accepted'], 10)
            self.assertEqual(report['languages'], [lang])
            manifest = report['reviewed_manifest']
            self.assertEqual(audit_efficiency(manifest)['independently_reviewed_variants'],
                             10 * (REVIEW_LANGUAGES.index(lang) + 1))
        for bad in ('xx', '', 'en'):
            with self.assertRaises(VekaError):
                build_review_packet(manifest, 'editor_01', language=bad)

    def test_review_packets_have_owner_only_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'review.csv'
            write_review_packet(self.a, path)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_blanked_40_item_packet_and_pending_gate(self):
        self.assertEqual(REVIEW_LANGUAGES, ("id", "tr", "eo", "ia"))
        self.assertEqual(len(self.a), 40)
        self.assertEqual(len({(r["item_id"], r["language"]) for r in self.a}), 40)
        self.assertTrue(all(not row["target_text"] for row in self.a))
        self.assertTrue(all(row["english_reference"] and row["mandarin_reference"] for row in self.a))
        report = evaluate_reviews(self.a, self.b, self.manifest)
        self.assertEqual(report["pending"], 40)
        self.assertEqual(report["accepted"], 0)
        self.assertEqual(report["blocked"], 0)
        self.assertFalse(report["publishable"])
        self.assertIsNone(report["reviewed_manifest"])
        self.assertFalse(report["human_efficiency_measured"])

    def test_two_agreeing_reviewers_produce_noncanonical_manifest(self):
        a, b = self.completed()
        report = evaluate_reviews(a, b, self.manifest)
        self.assertEqual(report["accepted"], 40)
        self.assertEqual(report["pending"], 0)
        self.assertTrue(report["publishable"])
        result = report["reviewed_manifest"]
        self.assertEqual(audit_efficiency(result)["independently_reviewed_variants"], 40)
        self.assertEqual(result["items"][0]["variants"]["id"]["spoken_syllables"], None)
        self.assertEqual(result["items"][0]["variants"]["id"]["status"], "independently_reviewed")
        self.assertFalse(report["human_efficiency_measured"])
        self.assertEqual(report["canonical_changes"], 0)
        self.assertFalse(report["reviewer_independence_authenticated"])

    def test_one_reviewer_or_same_reviewer_never_approves(self):
        a, b = self.completed()
        with self.assertRaises(VekaError):
            evaluate_reviews(a, a, self.manifest)
        b[0]["reviewer_id"] = a[0]["reviewer_id"]
        with self.assertRaises(VekaError):
            evaluate_reviews(a, b, self.manifest)
        b = build_review_packet(self.manifest, "reviewer_A")
        with self.assertRaises(VekaError):
            evaluate_reviews(a, b, self.manifest)

    def test_changed_source_readings_cannot_redefine_comparison(self):
        altered = copy.deepcopy(self.manifest)
        altered['items'][0]['variants']['en']['text'] = 'Changed reference meaning.'
        with self.assertRaises(VekaError):
            build_review_packet(altered, 'editor_001', language='id')
        with self.assertRaises(VekaError):
            evaluate_reviews(self.a, self.b, altered)

    def test_disagreement_and_rejection_block_publication(self):
        a, b = self.completed()
        b[0]["target_text"] = "another test translation"
        b[1]["meaning_equivalent"] = "no"
        b[2]["critical_ambiguity"] = "yes"
        report = evaluate_reviews(a, b, self.manifest)
        self.assertEqual(report["blocked"], 3)
        self.assertEqual(report["accepted"], 37)
        self.assertFalse(report["publishable"])
        self.assertIsNone(report["reviewed_manifest"])

    def test_anchor_tampering_duplicate_rows_malformed_csv_and_injection_fail(self):
        a, b = self.completed()
        mutations = []
        p = copy.deepcopy(a); p[0]["source_digest"] = "0" * 64; mutations.append(p)
        p = copy.deepcopy(a); p[0]["english_reference"] = "changed"; mutations.append(p)
        p = copy.deepcopy(a); p[1] = dict(p[0]); mutations.append(p)
        p = copy.deepcopy(a); p[0]["target_text"] = "=HYPERLINK(\"x\")"; mutations.append(p)
        p = copy.deepcopy(a); p[0]["reviewer_id"] = "other_reviewer"; mutations.append(p)
        p = copy.deepcopy(a); p.pop(); mutations.append(p)
        p = copy.deepcopy(a); p[0]["meaning_equivalent"] = "approved"; mutations.append(p)
        p = copy.deepcopy(a); p[0]["unexpected"] = "yes"; mutations.append(p)
        for invalid in mutations:
            with self.subTest(invalid=invalid[0]), self.assertRaises(VekaError):
                evaluate_reviews(invalid, b, self.manifest)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text(",".join(REVIEW_FIELDS)+"\n"+"one,two,three\n", encoding="utf-8")
            with self.assertRaises(VekaError):
                read_review_csv(path)

    def test_completed_dual_review_cli_export_is_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = self.completed()
            paths = [Path(tmp) / name for name in ('A.csv', 'B.csv')]
            for rows, path in zip((a, b), paths):
                write_review_packet(rows, path)
            output = Path(tmp) / 'consensus.json'
            args = [sys.executable, '-m', 'veka', 'efficiency-review-check',
                    '--review-a', str(paths[0]), '--review-b', str(paths[1]),
                    '--output', str(output)]
            run = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            self.assertEqual(audit_efficiency(json.loads(output.read_text()))[
                'independently_reviewed_variants'], 40)
            again = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)

    def test_per_language_cli_has_ten_rows_and_remains_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b, output = [Path(tmp) / name for name in ('id-a.csv', 'id-b.csv', 'result.json')]
            for ident, path in (('editor_id_A', a), ('editor_id_B', b)):
                run = subprocess.run([sys.executable, '-m', 'veka', 'efficiency-review-plan',
                                      '--language', 'id', '--reviewer', ident,
                                      '--output', str(path)],
                                     cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(len(read_review_csv(path)), 10)
            cmd = [sys.executable, '-m', 'veka', 'efficiency-review-check',
                   '--review-a', str(a), '--review-b', str(b)]
            report = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(report.returncode, 0, report.stderr)
            self.assertEqual(json.loads(report.stdout)['pending'], 10)
            self.assertEqual(json.loads(report.stdout)['languages'], ['id'])
            export = subprocess.run(cmd + ['--output', str(output)], cwd=ROOT,
                                    capture_output=True, text=True)
            self.assertEqual(export.returncode, 2)
            self.assertFalse(output.exists())

    def test_round_trip_csv_and_cli_rejects_unreviewed_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1, p2, output = [Path(tmp) / s for s in ("a.csv", "b.csv", "reviewed.json")]
            for reviewer, path in (("reviewer_A", p1), ("reviewer_B", p2)):
                cmd = [sys.executable, "-m", "veka", "efficiency-review-plan",
                       "--reviewer", reviewer, "--output", str(path)]
                run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(len(read_review_csv(path)), 40)
                again = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(again.returncode, 2)
            args = [sys.executable, "-m", "veka", "efficiency-review-check",
                    "--review-a", str(p1), "--review-b", str(p2),
                    "--output", str(output)]
            blocked = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 2)
            self.assertFalse(output.exists())
            self.assertIn("not approved", blocked.stderr)
            advisory = subprocess.run(args[:-2], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(advisory.returncode, 0, advisory.stderr)
            self.assertEqual(json.loads(advisory.stdout)["pending"], 40)


if __name__ == "__main__":
    unittest.main()
