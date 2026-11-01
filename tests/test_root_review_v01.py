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
from veka.root_sources import read_root_sources, audit_root_sources

ROOT = Path(__file__).resolve().parents[1]


class RootReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")
        cls.candidates = read_candidates(ROOT / "data/international_candidates_v10.csv")
        cls.priorities = read_review_priorities(ROOT / "data/international_priorities_v10.csv")

    def review(self, concept="C002", evidence=None, leads=None):
        if leads is None:
            leads = read_root_sources(ROOT / "data/root_source_leads_v12.csv")
        return build_root_review(concept, self.candidates, self.lex,
                                 self.priorities, evidence or [], leads=leads)

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

    def test_music_screening_leads_are_not_verified_attestations(self):
        report = self.review()
        self.assertEqual(len(report["source_leads"]), 4)
        self.assertEqual(report["source_records"], [])
        self.assertEqual(report["etymology"]["attested_language_families_claimed"], 0)
        self.assertTrue(all(row["review_status"] == "pending" for row in report["source_leads"]))
        self.assertTrue(all(row["accepted_as_attestation"] is False for row in report["source_leads"]))
        mandarin = next(r for r in report["source_leads"] if r["language"] == "Mandarin")
        self.assertEqual(mandarin["relation_to_draft"], "different_common_form")
        self.assertFalse(report["adoption_authorized"])

    def test_false_friend_and_school_leads_are_visible(self):
        data = self.review("C001")
        self.assertEqual(len(data["source_leads"]), 4)
        portuguese = next(r for r in data["source_leads"] if r["language"] == "Portuguese")
        self.assertEqual(portuguese["relation_to_draft"], "false_friend")
        self.assertFalse(portuguese["accepted_as_attestation"])
        self.assertEqual(len(self.review("C008")["source_leads"]), 5)
        self.assertEqual(self.review("C009")["source_leads"], [])

    def test_localized_dictionary_glosses_and_explicit_fallback(self):
        report = self.review()
        self.assertEqual(report["learner_glosses"]["zh"]["gloss"], "音乐")
        self.assertEqual(report["learner_glosses"]["pt-BR"]["gloss"], "música")
        self.assertEqual(report["learner_glosses"]["pt-BR"]["gloss_language"], "pt-BR")
        fallback = self.review("C009")
        self.assertEqual(fallback["learner_glosses"]["pt-BR"]["gloss_language"], "en")
        self.assertTrue(fallback["learner_glosses"]["pt-BR"]["gloss"].endswith("(en)"))
        from veka.root_review import format_root_review
        self.assertIn("音乐", format_root_review(report, language="zh"))
        self.assertIn("música", format_root_review(report, language="pt-BR"))
        process = subprocess.run([sys.executable, "-m", "veka", "root-review",
                                  "C002", "--format", "text", "--lang", "pt-BR"],
                                 cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("música", process.stdout)
        self.assertIn("unreviewed source leads: 4", process.stdout)

    def test_screening_leads_fail_closed_without_creating_attestations(self):
        import csv
        import tempfile
        leads = read_root_sources(ROOT / "data/root_source_leads_v12.csv")
        self.assertEqual(audit_root_sources(leads, self.lex, self.candidates)["source_leads"], 13)
        with self.assertRaises(VekaError):
            audit_root_sources(leads + [leads[0]], self.lex, self.candidates)
        with self.assertRaises(VekaError):
            audit_root_sources([dict(leads[0], candidate_form="fake")], self.lex, self.candidates)
        with self.assertRaises(VekaError):
            audit_root_sources([dict(leads[0], review_status="verified")], self.lex, self.candidates)
        with self.assertRaises(VekaError):
            audit_root_sources([dict(leads[0], source_url="file:///tmp/leak")], self.lex, self.candidates)
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "bad.csv"
            file.write_text("candidate_form,language\nmu-si-ka,English\n", encoding="utf8")
            with self.assertRaises(VekaError):
                read_root_sources(file)

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
