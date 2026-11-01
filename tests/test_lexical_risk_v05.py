"""Veka 0.5 research-only lexical risk and proposal contract.

The outputs are structural hypotheses, NOT acoustic error probabilities.
"""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError, validate_word
from veka.lexical_risk import (
    audit_compound_surfaces,
    audit_lexical_risk,
    contrast_distance,
    load_priorities,
    propose_replacements,
)

ROOT = Path(__file__).resolve().parents[1]
PRIORITIES = ROOT / "data" / "lexical_priors_v05.csv"


class LexicalRiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data" / "lexicon.csv")

    def test_priors_are_explicit_and_unknown_roots_fall_back_to_one(self):
        weights = load_priorities(PRIORITIES, self.lex)
        self.assertGreater(weights["mi"], weights["dol"])
        self.assertGreater(weights["ne"], weights["dol"])
        self.assertGreater(weights["ran"], weights["dol"])
        self.assertEqual(weights["dol"], 1.0)

    def test_priors_fail_closed_on_duplicates_unknowns_and_invalid_weights(self):
        for rows in [
            ["mi,2,2", "mi,3,2"],
            ["unknown,2,2"],
            ["mi,0,2"],
            ["mi,nan,2"],
            ["mi,11,2"],
            ["ren-sak,2,2"],
        ]:
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "priors.csv"
                p.write_text("form,exposure,consequence\n" + "\n".join(rows) + "\n")
                with self.assertRaises(VekaError):
                    load_priorities(p, self.lex)

    def test_phonological_distance_is_symmetric_and_catches_one_feature_pairs(self):
        self.assertEqual(contrast_distance("mi", "ni"), contrast_distance("ni", "mi"))
        self.assertLess(contrast_distance("mi", "ni"), contrast_distance("mi", "kon"))
        self.assertLess(contrast_distance("ne", "no"), contrast_distance("ne", "dak"))
        self.assertLess(contrast_distance("pal", "pál"), contrast_distance("pal", "kon"))
        self.assertEqual(contrast_distance("mi", "mi"), 0.0)

    def test_proposals_are_deterministic_legal_and_not_canonical(self):
        weights = load_priorities(PRIORITIES, self.lex)
        before = tuple(self.lex.items())
        first = propose_replacements(self.lex, weights, "mi", limit=5)
        second = propose_replacements(self.lex, weights, "mi", limit=5)
        self.assertEqual(first, second)
        self.assertTrue(first)
        self.assertEqual(tuple(self.lex.items()), before)
        self.assertTrue(all(row["candidate"] not in self.lex and
                            validate_word(row["candidate"]) and
                            row["structural_gain"] > 0 for row in first))
        self.assertEqual(len({row["candidate"] for row in first}), len(first))
        self.assertTrue(all(row["human_validated"] is False for row in first))

    def test_proposals_reject_unknown_compounds_and_bad_limits(self):
        weights = load_priorities(PRIORITIES, self.lex)
        for target in ("unknown", "ren-sak"):
            with self.assertRaises(VekaError):
                propose_replacements(self.lex, weights, target)
        with self.assertRaises(VekaError):
            propose_replacements(self.lex, weights, "mi", limit=0)

    def test_spoken_compound_audit_distinguishes_syntax_from_lexical_uniqueness(self):
        report = audit_compound_surfaces(self.lex, sample_limit=3)
        self.assertEqual(report["compounds"], 708)
        self.assertEqual(report["noun_adjective_surface_equivalents"], 708)
        self.assertEqual(len(report["examples"]), 3)
        self.assertIn("ren sak", [r["spoken_tokens"] for r in report["examples"]] +
                      [r["spoken_tokens"] for r in audit_compound_surfaces(self.lex, sample_limit=708)["examples"]])
        self.assertFalse(report["spoken_word_boundaries_tested"])

    def test_audit_can_be_run_for_both_profiles_without_data_claims(self):
        from veka.profiles import load_profile
        weights = load_priorities(PRIORITIES, self.lex)
        for profile in ("tonal", "toneless"):
            lex = load_profile(profile)
            result = audit_lexical_risk(lex, weights, targets=["mi", "ne"], top=5, candidates=3)
            self.assertEqual(result["profile"], profile)
            self.assertEqual(len(result["top_risk_pairs"]), 5)
            self.assertEqual(len(result["proposals"]), 2)
            self.assertFalse(result["acoustically_validated"])
            self.assertEqual(result["compound_surfaces"]["noun_adjective_surface_equivalents"], 708)
            self.assertGreater(result["total_structural_penalty"], 0)

    def test_cli_outputs_versioned_research_only_json(self):
        from veka.__main__ import main
        from contextlib import redirect_stdout, redirect_stderr
        from io import StringIO
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["lexical-risk", "--target", "mi", "--top", "3", "--candidates", "2"])
        self.assertEqual(code, 0, stderr.getvalue())
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["schema_version"], "veka.lexical-risk.v05")
        self.assertEqual(len(result["top_risk_pairs"]), 3)
        self.assertEqual(len(result["proposals"]), 1)
        self.assertEqual(result["canonical_lexicon_modified"], False)

    def test_cli_output_file_is_valid_json(self):
        from veka.__main__ import main
        from contextlib import redirect_stdout
        from io import StringIO
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["lexical-risk", "--target", "mi",
                                       "--top", "0", "--candidates", "1",
                                       "--output", str(path)]), 0)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(data["acoustically_validated"])


if __name__ == "__main__":
    unittest.main()
