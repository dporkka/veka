"""Source-linked cognate leads stay unreviewed until independently checked."""
import csv
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.cognates import read_pilot
from veka.cognate_review import read_cognate_leads, audit_cognate_leads

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


class CognateLeadReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(DATA / "lexicon.csv")
        cls.candidates = read_pilot(DATA / "cognate_candidates_v07.csv")
        cls.leads = read_cognate_leads(DATA / "cognate_source_leads_v07.csv")

    def test_sourced_leads_are_not_verified_or_accepted(self):
        report = audit_cognate_leads(self.candidates, self.leads, self.lex)
        self.assertEqual(report["lead_count"], 12)
        self.assertEqual(report["pending_review"], 12)
        self.assertEqual(report["verified_equivalent"], 0)
        self.assertEqual(report["adopted_count"], 0)
        self.assertFalse(report["recognition_measured"])
        self.assertEqual(set(report["by_concept"]), {"N01", "N02", "N03"})
        self.assertEqual(report["by_concept"]["N01"]["source_leads"], 4)
        self.assertEqual(report["by_concept"]["N03"]["verified_families"], 0)

    def test_invalid_reference_candidate_or_source_rejected(self):
        for replacement in ({"concept_id": "unknown"}, {"candidate_form": "no"},
                            {"source_url": "javascript:alert(1)"},
                            {"source_url": "https://user:password@example.org/x"},
                            {"attestation_verified": "yes"}, {"semantic_equivalent": "yes"}):
            leads = [dict(x) for x in self.leads]
            leads[0].update(replacement)
            with self.subTest(replacement=replacement), self.assertRaises(VekaError):
                audit_cognate_leads(self.candidates, leads, self.lex)

    def test_duplicate_language_and_invalid_family_fail_closed(self):
        with self.assertRaises(VekaError):
            audit_cognate_leads(self.candidates, self.leads + [dict(self.leads[0])], self.lex)
        leads = [dict(x) for x in self.leads]
        leads[0]["language_family"] = ""
        with self.assertRaises(VekaError):
            audit_cognate_leads(self.candidates, leads, self.lex)

    def test_reviewer_assertions_count_families_not_languages(self):
        leads = [dict(x) for x in self.leads]
        for i, row in enumerate(leads[:2]):
            row["semantic_reviewer"] = "human-reviewer"
            row["attestation_verified"] = "yes"
            row["semantic_equivalent"] = "yes"
            row["language_family"] = "Afroasiatic"
            row["language"] = "Arabic" if i == 0 else "Egyptian Arabic"
        report = audit_cognate_leads(self.candidates, leads, self.lex)
        self.assertEqual(report["verified_equivalent"], 2)
        self.assertEqual(report["by_concept"]["N01"]["verified_families"], 1)
        self.assertFalse(report["recognition_measured"])

    def test_cli_reports_source_leads_without_human_verification(self):
        import json
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, '-m', 'veka', 'cognate-leads'],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['pending_review'], 12)
        self.assertEqual(report['verified_equivalent'], 0)

    def test_strict_csv_rejects_bad_field_count_and_unterminated_quotes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text(
                ",".join(self.leads[0].keys()) + "\n" +
                ",".join(["x"] * (len(self.leads[0]) + 1)) + "\n")
            with self.assertRaises(VekaError):
                read_cognate_leads(path)
            path.write_text(",".join(self.leads[0].keys()) + '\n"unterminated')
            with self.assertRaises(VekaError):
                read_cognate_leads(path)


if __name__ == "__main__":
    unittest.main()
