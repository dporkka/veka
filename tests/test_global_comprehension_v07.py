"""Veka 0.7 contract: sourced family evidence and observed comprehension only."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.international import read_candidates
from veka.global_comprehension import (
    audit_global_candidates, summarize_global_trials, read_global_csv,
    EVIDENCE_FIELDS, TRIAL_FIELDS,
)

ROOT = Path(__file__).resolve().parents[1]


class GlobalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")
        cls.candidates = read_candidates(ROOT / "data/international_candidates_v04.csv")

    def sample(self, language, family, branch, **changes):
        row = {
            "concept_id": "C002", "candidate_form": "mu-si-ka",
            "language": language, "language_family": family, "language_branch": branch,
            "attested_form": "musika", "source_url": "https://example.org/lexicon",
            "semantic_reviewer": "linguist-1", "attestation_verified": "yes",
            "semantic_equivalent": "yes", "notes": "",
        }
        row.update(changes)
        return row

    def test_empty_evidence_never_means_international_or_measured(self):
        report = audit_global_candidates(self.candidates, self.lex, [])
        self.assertEqual(report["evidence_records"], 0)
        self.assertEqual(report["verified_attestations"], 0)
        self.assertEqual(report["candidate_count"], 8)
        self.assertFalse(report["recognition_measured"])
        self.assertFalse(report["eligible_for_adoption"])
        self.assertEqual(report["candidates"]["C002"]["verified_families"], 0)

    def test_multiple_romance_and_germanic_sources_are_one_indoeuropean_family(self):
        rows = [
            self.sample("Spanish", "Indo-European", "Romance"),
            self.sample("English", "Indo-European", "Germanic"),
            self.sample("Swahili", "Niger-Congo", "Bantu"),
        ]
        report = audit_global_candidates(self.candidates, self.lex, rows)
        music = report["candidates"]["C002"]
        self.assertEqual(music["verified_languages"], 3)
        self.assertEqual(music["verified_families"], 2)
        self.assertEqual(music["verified_branches"], 3)
        self.assertFalse(report["eligible_for_adoption"])
        self.assertFalse(music["recognition_measured"])

    def test_verification_requires_source_reviewer_and_semantic_equivalence(self):
        for change in (
            {"source_url": ""},
            {"source_url": "ftp://fake"},
            {"semantic_reviewer": ""},
            {"semantic_equivalent": "unknown"},
            {"language_family": ""},
        ):
            with self.subTest(change=change):
                with self.assertRaises(VekaError):
                    audit_global_candidates(self.candidates, self.lex,
                                            [self.sample("Spanish", "Indo-European", "Romance", **change)])

    def test_unverified_or_not_semantically_equivalent_is_not_counted(self):
        rows = [
            self.sample("Spanish", "Indo-European", "Romance",
                        attestation_verified="no", semantic_reviewer="", source_url="", semantic_equivalent="unknown"),
            self.sample("Swahili", "Niger-Congo", "Bantu", semantic_equivalent="no"),
        ]
        report = audit_global_candidates(self.candidates, self.lex, rows)
        self.assertEqual(report["verified_attestations"], 0)
        self.assertEqual(report["candidates"]["C002"]["verified_families"], 0)

    def test_mismatched_candidate_unknown_concept_and_duplicate_language_fail(self):
        known = self.sample("Spanish", "Indo-European", "Romance")
        for change in ({"candidate_form": "sil"}, {"concept_id": "C999"}):
            with self.subTest(change=change), self.assertRaises(VekaError):
                audit_global_candidates(self.candidates, self.lex, [dict(known, **change)])
        with self.assertRaises(VekaError):
            audit_global_candidates(self.candidates, self.lex,
                                    [known, dict(known, language="spanish")])

    def test_strict_csv_schema_has_no_silent_extra_fields(self):
        path = ROOT / "data/global_evidence_v07.csv"
        self.assertEqual(read_global_csv(path, EVIDENCE_FIELDS), [])
        with self.assertRaises(VekaError):
            read_global_csv(ROOT / "data/international_evidence_v04.csv", EVIDENCE_FIELDS)


class ObservedTrialsTests(unittest.TestCase):
    def record(self, participant, family, condition, correct, elapsed_ms, **changes):
        result = {
            "participant_id": participant, "language_background_family": family,
            "concept_id": "C002", "condition": condition,
            "correct": str(correct), "elapsed_ms": str(elapsed_ms),
            "repair_ms": "0", "critical_error": "0",
        }
        result.update(changes)
        return result

    def test_real_trials_report_both_conditions_per_family_without_fake_statistics(self):
        rows = [
            self.record("P01", "Indo-European", "core", 1, 2000),
            self.record("P02", "Indo-European", "candidate", 1, 1500),
            self.record("P03", "Austronesian", "core", 0, 1000, repair_ms="500"),
            self.record("P04", "Austronesian", "candidate", 1, 3000),
        ]
        result = summarize_global_trials(rows, {"C002": "mu-si-ka"})
        self.assertEqual(result["participants"], 4)
        self.assertTrue(result["observed"])
        self.assertEqual(result["family_coverage"], ["Austronesian", "Indo-European"])
        self.assertEqual(result["balanced_families"], ["Austronesian", "Indo-European"])
        self.assertEqual(result["conditions"]["core"]["correct"], 1)
        self.assertEqual(result["conditions"]["candidate"]["correct"], 2)
        self.assertEqual(result["by_concept"]["C002"]["candidate_form"], "mu-si-ka")
        self.assertEqual(result["by_concept"]["C002"]["conditions"]["core"]["trials"], 2)
        self.assertEqual(result["by_concept"]["C002"]["balanced_families"], ["Austronesian", "Indo-European"])
        self.assertAlmostEqual(result["conditions"]["core"]["correct_per_minute"], 60 / 3.5)
        self.assertFalse(result["proven_better"])  # descriptive pilot, no inference

    def test_missing_comparator_is_flagged_not_treated_as_a_win(self):
        result = summarize_global_trials([
            self.record("P01", "Indo-European", "candidate", 1, 1000)
        ], {"C002": "mu-si-ka"})
        self.assertEqual(result["balanced_families"], [])
        self.assertEqual(result["unbalanced_families"], ["Indo-European"])
        self.assertFalse(result["proven_better"])

    def test_bad_or_duplicate_responses_fail_closed(self):
        base = self.record("P01", "Indo-European", "core", 1, 1000)
        changes = (
            {"elapsed_ms": "0"}, {"elapsed_ms": "-10"}, {"elapsed_ms": "garbage"},
            {"correct": "maybe"}, {"critical_error": "1"},
            {"repair_ms": "-5"}, {"concept_id": "C999"},
            {"language_background_family": ""},
        )
        for change in changes:
            with self.subTest(change=change), self.assertRaises(VekaError):
                summarize_global_trials([dict(base, **change)], {"C002": "mu-si-ka"})
        with self.assertRaises(VekaError):
            summarize_global_trials([base, dict(base, condition="candidate")],
                                    {"C002": "mu-si-ka"})

    def test_critical_errors_are_counted_but_never_auto_approved(self):
        r = self.record("P01", "Sino-Tibetan", "candidate", 0, 1000,
                        critical_error="1", repair_ms="1000")
        result = summarize_global_trials([r], {"C002": "mu-si-ka"})
        self.assertEqual(result["conditions"]["candidate"]["critical_errors"], 1)
        self.assertEqual(result["conditions"]["candidate"]["correct_per_minute"], 0)
        self.assertFalse(result["proven_better"])

    def test_blank_trial_template_remains_unmeasured(self):
        self.assertEqual(read_global_csv(ROOT / "data/global_trials_v07.csv", TRIAL_FIELDS), [])
        self.assertFalse(summarize_global_trials([], {"C002": "mu-si-ka"})["observed"])


class GlobalCLITests(unittest.TestCase):
    def test_global_audit_and_empty_score_have_honest_status(self):
        audit = subprocess.run([sys.executable, "-m", "veka", "global-audit"],
                               cwd=ROOT, text=True, capture_output=True, check=True)
        result = json.loads(audit.stdout)
        self.assertEqual(result["candidate_count"], 8)
        self.assertFalse(result["recognition_measured"])
        score = subprocess.run([sys.executable, "-m", "veka", "global-score"],
                               cwd=ROOT, text=True, capture_output=True, check=True)
        report = json.loads(score.stdout)
        self.assertFalse(report["observed"])
        self.assertFalse(report["eligible_for_adoption"])


if __name__ == "__main__":
    unittest.main()
