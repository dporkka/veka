"""Globasa-inspired selection checks for the existing Veka research queue."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.international import read_candidates
from veka.international_plan import read_review_priorities
from veka.root_review import build_root_review, near_spelling_forms

ROOT = Path(__file__).resolve().parents[1]


class RootReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")
        cls.candidates = read_candidates(ROOT / "data/international_candidates_v10.csv")
        cls.priorities = read_review_priorities(ROOT / "data/international_priorities_v10.csv")

    def review(self, concept="C002", evidence=None):
        return build_root_review(concept, self.candidates, self.lex,
                                 self.priorities, evidence or [])

    def test_music_card_has_two_separate_experimental_arms(self):
        data = self.review()
        self.assertEqual(data["schema_version"], "veka.root-review.v01")
        self.assertEqual(data["concept_id"], "C002")
        self.assertEqual(data["canonical"]["form"], "woi")
        self.assertEqual(data["canonical"]["gloss"], "music")
        self.assertEqual(data["comparison_arms"][0]["condition"], "core")
        self.assertEqual(data["comparison_arms"][1]["form"], "mu-si-ka")
        self.assertFalse(data["comparison_arms"][1]["accepted_vocabulary"])
        self.assertFalse(data["adoption_authorized"])
        self.assertFalse(data["human_benefit_established"])
        self.assertEqual(data["etymology"]["verified_independent_origins"], None)
        self.assertEqual(data["etymology"]["review_status"], "not_established")

    def test_unproposed_concept_does_not_invent_vocabulary(self):
        data = self.review("C009")
        self.assertEqual(data["comparison_arms"], [
            {"condition": "core", "form": data["canonical"]["form"], "accepted_vocabulary": True}
        ])
        self.assertEqual(data["candidate"]["status"], "not_proposed")
        self.assertEqual(data["source_records"], [])
        self.assertIsNone(data["candidate"]["spelling_near_pairs"])

    def test_near_pairs_check_insertion_deletion_and_substitution_on_undelimited_surface(self):
        found = near_spelling_forms("da-ta", ("da-to", "da", "da-tan", "data", "woi"))
        self.assertEqual([r["form"] for r in found],
                         ["data", "da-tan", "da-to"])
        self.assertEqual(found[0]["edits"], 0)
        self.assertTrue(found[0]["silent_hyphen_ambiguity"])
        self.assertTrue(all(r["edits"] <= 1 for r in found))
        self.assertEqual(near_spelling_forms("", ("da-to",)), [])

    def test_spelling_risk_marks_whether_near_pair_is_canonical(self):
        report = self.review("C056")
        nearby = {r["form"]: r for r in report["candidate"]["spelling_near_pairs"]}
        self.assertIn("dis", nearby)
        self.assertTrue(nearby["dis"]["accepted_vocabulary"])
        self.assertFalse(report["adoption_authorized"])

    def test_attestations_do_not_prove_etymological_independence_or_recognition(self):
        def record(language, family, branch):
            return {
                "concept_id": "C002", "candidate_form": "mu-si-ka",
                "language": language, "language_family": family,
                "language_branch": branch, "attested_form": "musika",
                "source_url": "https://example.org/dictionary",
                "semantic_reviewer": "R1", "attestation_verified": "yes",
                "semantic_equivalent": "yes", "notes": "fictional fixture",
            }
        records = [record("English", "Indo-European", "Germanic"),
                   record("Portuguese", "Indo-European", "Romance"),
                   record("Swahili", "Niger-Congo", "Bantu")]
        result = self.review(evidence=records)
        self.assertEqual(result["etymology"]["attested_language_families_claimed"], 2)
        self.assertIsNone(result["etymology"]["verified_independent_origins"])
        self.assertEqual(len(result["source_records"]), 3)
        self.assertFalse(result["human_benefit_established"])
        self.assertFalse(result["adoption_authorized"])

    def test_unknown_concept_and_invalid_evidence_fail_closed(self):
        with self.assertRaises(VekaError):
            self.review("C999")
        with self.assertRaises(VekaError):
            self.review(evidence=[{"concept_id": "C002", "source_url": "https://example.org"}])

    def test_readable_concept_card_keeps_experimental_labels(self):
        from veka.root_review import format_root_review
        report = self.review()
        shown = format_root_review(report)
        self.assertIn("woi", shown)
        self.assertIn("mu-si-ka", shown)
        self.assertIn("unverified", shown)
        self.assertIn("no human", shown.lower())
        p = subprocess.run([sys.executable, "-m", "veka", "root-review",
                            "C002", "--format", "text"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("woi", p.stdout)
        self.assertIn("mu-si-ka", p.stdout)

    def test_cli_json_and_rejected_unknown_concept(self):
        cmd = [sys.executable, "-m", "veka", "root-review", "C002"]
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["canonical"]["form"], "woi")
        self.assertFalse(data["adoption_authorized"])
        bad = subprocess.run(cmd[:-1] + ["INVALID"], cwd=ROOT,
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("VEKA ERROR", bad.stderr)


if __name__ == "__main__":
    unittest.main()
