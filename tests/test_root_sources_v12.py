"""Noncanonical source-review contract; source links are not human outcomes."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.international import read_candidates
from veka.root_sources import SOURCE_FIELDS, audit_root_sources, read_root_sources

ROOT = Path(__file__).resolve().parents[1]


class RootSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")
        cls.queue = read_candidates(ROOT / "data/international_candidates_v04.csv")
        cls.rows = read_root_sources(ROOT / "data/root_source_leads_v12.csv")

    def test_source_linked_packet_tracks_contrasts_and_no_human_verification(self):
        report = audit_root_sources(self.rows, self.lex, self.queue)
        self.assertEqual(report["schema_version"], "veka.root-sources.v12")
        self.assertGreaterEqual(report["source_leads"], 12)
        self.assertEqual(report["reviewer_approved_records"], 0)
        self.assertFalse(report["recognition_measured"])
        self.assertFalse(report["adoption_authorized"])
        self.assertEqual(report["canonical_changes"], 0)
        by_id = {r["concept_id"]: r for r in report["concepts"]}
        self.assertGreaterEqual(by_id["C001"]["false_friend_leads"], 1)
        self.assertGreaterEqual(by_id["C008"]["different_common_form_leads"], 1)
        self.assertGreaterEqual(by_id["C002"]["candidate_like_leads"], 1)
        self.assertTrue(all(r["review_status"] == "pending" for r in self.rows))

    def test_source_review_needs_explicit_attestor_but_does_not_count_recognition(self):
        row = dict(next(x for x in self.rows if x["concept_id"] == "C002"))
        row.update(review_status="approved", semantic_match="yes",
                   reviewer="independent-reviewer", review_note="sense verified in lexical entry")
        report = audit_root_sources([row], self.lex, self.queue)
        self.assertEqual(report["reviewer_approved_records"], 1)
        self.assertEqual(report["candidate_like_approved"], 1)
        self.assertFalse(report["recognition_measured"])
        self.assertFalse(report["adoption_authorized"])
        self.assertEqual(report["concepts"][0]["reviewer_claimed_families"], 1)

    def test_reviewers_cannot_approve_false_friend_as_matching_evidence(self):
        row = dict(next(x for x in self.rows if x["relation"] == "false_friend"))
        row.update(review_status="approved", semantic_match="yes",
                   reviewer="reviewer-1", review_note="invalid equivalence")
        with self.assertRaises(VekaError):
            audit_root_sources([row], self.lex, self.queue)

    def test_invalid_or_duplicate_sources_fail_closed(self):
        row = self.rows[0]
        variants = [
            [row, dict(row)],
            [dict(row, concept_id="missing")],
            [dict(row, candidate_form="different")],
            [dict(row, source_url="http://localhost/a")],
            [dict(row, source_url="https://example.com@localhost/a")],
            [dict(row, review_status="approved")],
            [dict(row, semantic_match="yes")],
            [dict(row, language_family="")],
            [dict(row, relation="invented")],
            [dict(row, reviewed="yes")],
        ]
        for broken in variants:
            with self.subTest(row=broken), self.assertRaises(VekaError):
                audit_root_sources(broken, self.lex, self.queue)

    def test_source_review_supports_country_code_dictionary_hosts(self):
        row = dict(self.rows[0], source_url="https://dictionnaire.fr/terme")
        self.assertEqual(audit_root_sources([row], self.lex, self.queue)["source_leads"], 1)

    def test_pending_records_are_not_misreported_as_verified_families(self):
        report = audit_root_sources(self.rows, self.lex, self.queue)
        self.assertEqual(report["reviewer_claimed_families_total"], 0)
        self.assertEqual(report["candidate_like_approved"], 0)
        self.assertGreater(report["unreviewed_leads"], 0)

    def test_strict_csv_schema_and_cli_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrong.csv"
            path.write_text("concept_id,language\\nC001,English\\n", encoding="utf-8")
            with self.assertRaises(VekaError):
                read_root_sources(path)
            p = subprocess.run([sys.executable, "-m", "veka", "root-sources"],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            report = json.loads(p.stdout)
            self.assertEqual(report["source_leads"], len(self.rows))
            self.assertFalse(report["adoption_authorized"])
            self.assertEqual(tuple(self.rows[0]), SOURCE_FIELDS)


if __name__ == "__main__":
    unittest.main()
