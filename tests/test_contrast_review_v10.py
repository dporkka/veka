"""Contract tests: separate human editorial review, never automatic validation."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError

ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def replace_rows(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class ContrastEditorialReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.first = Path(self.tmp.name) / "one.csv"
        self.second = Path(self.tmp.name) / "two.csv"

    def export(self, language="zh"):
        from veka.contrast_review import write_review_template
        write_review_template(language, "R01", self.first)
        write_review_template(language, "R02", self.second)
        return read_rows(self.first), read_rows(self.second)

    def test_templates_are_separate_complete_and_pending_by_default(self):
        from veka.contrast_review import check_review_sheets
        for language in ("en", "zh", "pt-BR"):
            with self.subTest(language=language):
                self.first.unlink(missing_ok=True)
                self.second.unlink(missing_ok=True)
                a, b = self.export(language)
                self.assertEqual(len(a), 12)
                self.assertEqual(len(b), 12)
                self.assertEqual({r["language"] for r in a}, {language})
                self.assertEqual({r["reviewer_id"] for r in a}, {"R01"})
                self.assertEqual({r["reviewer_id"] for r in b}, {"R02"})
                self.assertTrue(all(not r["semantic_fidelity"] for r in a))
                result = check_review_sheets(language, self.first, self.second)
                self.assertEqual(result["rows_per_reviewer"], 12)
                self.assertEqual(result["pending_judgments"], 72)
                self.assertFalse(result["ready_for_manual_editorial_signoff"])
                self.assertFalse(result["independent_humans_verified"])
                self.assertFalse(result["human_comprehension_measured"])

    def test_two_reviewers_unanimous_approvals_only_ready_for_manual_signoff(self):
        from veka.contrast_review import check_review_sheets
        a, b = self.export()
        for rows in (a, b):
            for row in rows:
                row.update(semantic_fidelity="accept", naturalness="accept",
                           contrast_clarity="accept")
        replace_rows(self.first, a)
        replace_rows(self.second, b)
        report = check_review_sheets("zh", self.first, self.second)
        self.assertTrue(report["ready_for_manual_editorial_signoff"])
        self.assertEqual(report["pending_judgments"], 0)
        self.assertEqual(report["flagged_items"], [])
        self.assertFalse(report["independent_humans_verified"])
        self.assertFalse(report["translations_automatically_validated"])

    def test_disagreements_and_uncertain_judgments_fail_gate(self):
        from veka.contrast_review import check_review_sheets
        a, b = self.export("pt-BR")
        for rows in (a, b):
            for row in rows:
                row.update(semantic_fidelity="accept", naturalness="accept",
                           contrast_clarity="accept")
        b[0]["semantic_fidelity"] = "revise"
        b[0]["notes"] = "Aspect needs clarification"
        a[2]["naturalness"] = "unsure"
        a[2]["notes"] = "Check register with independent speaker"
        replace_rows(self.first, a)
        replace_rows(self.second, b)
        report = check_review_sheets("pt-BR", self.first, self.second)
        self.assertFalse(report["ready_for_manual_editorial_signoff"])
        self.assertEqual(len(report["flagged_items"]), 2)
        self.assertEqual(report["pending_judgments"], 0)

    def test_reject_same_reviewer_tampering_duplicated_items_and_invalid_fields(self):
        from veka.contrast_review import check_review_sheets
        a, b = self.export()
        # Independently attested reviewers cannot share an identity.
        for row in b:
            row["reviewer_id"] = "R01"
        replace_rows(self.second, b)
        with self.assertRaises(VekaError):
            check_review_sheets("zh", self.first, self.second)

        for variant in ("alter_translation", "duplicate", "unknown_score",
                        "unexplained_rejection", "unexpected_language"):
            with self.subTest(variant=variant):
                b = read_rows(self.first)
                for row in b:
                    row["reviewer_id"] = "R02"
                if variant == "alter_translation":
                    b[0]["translation"] = "different teaching target"
                elif variant == "duplicate":
                    b[1]["item_id"] = b[0]["item_id"]
                    b[1]["variant"] = b[0]["variant"]
                elif variant == "unknown_score":
                    b[0]["semantic_fidelity"] = "probably"
                elif variant == "unexplained_rejection":
                    b[0]["naturalness"] = "revise"
                else:
                    b[0]["language"] = "en"
                replace_rows(self.second, b)
                with self.assertRaises(VekaError):
                    check_review_sheets("zh", self.first, self.second)

    def test_review_templates_are_private_to_creator_on_posix(self):
        import os
        import stat
        if os.name != "posix":
            self.skipTest("POSIX permissions only")
        self.export()
        for path in (self.first, self.second):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_no_overwrite_or_invalid_identifiers_or_partial_files(self):
        from veka.contrast_review import write_review_template, check_review_sheets
        self.export()
        with self.assertRaises(VekaError):
            write_review_template("zh", "R03", self.first)
        with self.assertRaises(VekaError):
            write_review_template("zh", "R/../../", Path(self.tmp.name) / "bad.csv")
        with self.assertRaises(VekaError):
            write_review_template("pt", "R03", Path(self.tmp.name) / "bad.csv")
        lines = self.second.read_text(encoding="utf-8").splitlines()
        self.second.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
        with self.assertRaises(VekaError):
            check_review_sheets("zh", self.first, self.second)

    def test_cli_export_and_check_never_claims_completed_review(self):
        for reviewer, path in (("R01", self.first), ("R02", self.second)):
            proc = subprocess.run(
                [sys.executable, "-m", "veka", "contrast-review-export",
                 "--lang", "en", "--reviewer", reviewer, "--output", str(path)],
                cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(json.loads(proc.stdout)["human_review_collected"])
        proc = subprocess.run(
            [sys.executable, "-m", "veka", "contrast-review-check",
             "--lang", "en", "--first", str(self.first), "--second", str(self.second)],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(json.loads(proc.stdout)["ready_for_manual_editorial_signoff"])


if __name__ == "__main__":
    unittest.main()
