"""Experimental repair utterances must preserve their quoted, overt targets."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError, parse
from veka.profiles import DATA, load_profile
from veka.repair import parse_repair, MARKERS

ROOT = Path(__file__).resolve().parents[1]


class RepairProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_quote_is_explicit_and_never_asserts_quoted_content(self):
        value = parse_repair("Ko-ta-ra Mi pa dak mel yu.", self.lex)
        self.assertEqual(value["act"], "quotation")
        self.assertEqual(value["quote"]["ast"], parse("Mi pa dak mel.", self.lex, strict=True))
        self.assertFalse(value["asserts_quoted_proposition"])
        self.assertFalse(value["human_comprehension_validated"])
        self.assertFalse(value["canonical_grammar_changed"])
        self.assertFalse(value["canonical_lexicon_changed"])
        self.assertEqual(value["register"], "research")

    def test_repetition_and_confirmation_require_exact_anchoring(self):
        base = "Mi pa dak mel."
        for word, act in (("Re-pe-ta", "repetition_request"),
                          ("Kon-fi-ra", "confirmation_request")):
            with self.subTest(word=word):
                parsed = parse_repair(f"{word} Mi pa dak mel yu.", self.lex, prior=base)
                self.assertEqual(parsed["act"], act)
                self.assertTrue(parsed["quoted_prior_verified"])
                self.assertFalse(parsed["asserts_quoted_proposition"])
                self.assertEqual(parsed["quote"]["ast"]["predicate"], "dak")
                with self.assertRaises(VekaError):
                    parse_repair(f"{word} Mi pa dak mel yu.", self.lex)
                with self.assertRaises(VekaError):
                    parse_repair(f"{word} Mi pa dak mel yu.", self.lex,
                                 prior="Mi pa ne dak mel.")

    def test_correction_has_distinct_scoped_source_and_replacement(self):
        result = parse_repair(
            "Ko-re-ta Mi pa dak mel yu Mi pa ne dak mel yu.",
            self.lex, prior="Mi pa dak mel."
        )
        self.assertEqual(result["act"], "correction")
        self.assertTrue(result["quoted_prior_verified"])
        self.assertFalse(result["source_asserted"])
        self.assertTrue(result["replacement_proposition_presented"])
        self.assertFalse(result["replacement_truth_verified"])
        self.assertFalse(result["quote"]["ast"]["negative"])
        self.assertTrue(result["replacement"]["ast"]["negative"])
        self.assertEqual(len(result["scope_sequence"]), 2)

    def test_correction_rejects_unchanged_or_unanchored_or_questions(self):
        invalid = (
            ("Ko-re-ta Mi pa dak mel yu Mi pa dak mel yu.", "Mi pa dak mel."),
            ("Ko-re-ta Mi pa dak mel yu Mi pa ne dak mel yu.", None),
            ("Ko-re-ta Mi pa dak mel yu.", "Mi pa dak mel."),
            ("Ko-re-ta Mi pa dak mel yu Mi pa ne dak mel yu yu.", "Mi pa dak mel."),
            ("Ko-re-ta Ti gos ke yu Ti pa gos yu.", "Ti gos ke."),
            ("Ko-re-ta Mi gos yu Ha gos yu.", "Mi gos."),
        )
        for utterance, prior in invalid:
            with self.subTest(utterance=utterance), self.assertRaises(VekaError):
                parse_repair(utterance, self.lex, prior=prior)

    def test_scope_and_unknown_content_fail_closed(self):
        invalid = (
            "Re-pe-ta Mi pa dak mel yu.",
            "Re-pe-ta Mi pa dak mel yu yu.",
            "Kon-fi-ra yu.",
            "Ko-ta-ra yu.",
            "Ko-ta-ra Mi pa dak unknown yu.",
            "Ko-ta-ra Mi pa dak mel yu Mi gos.",
            "Ko-re-ta Mi pa dak mel yu",
            "Ko-ta-ra Ko-ta-ra Mi gos yu yu",
        )
        for utterance in invalid:
            with self.subTest(utterance=utterance), self.assertRaises(VekaError):
                parse_repair(utterance, self.lex)

    def test_quotes_support_explicit_polar_questions_without_asserting(self):
        result = parse_repair("Ko-ta-ra Ti gos ke yu.", self.lex)
        self.assertTrue(result["quote"]["ast"]["question"])
        check = parse_repair("Kon-fi-ra Ti gos ke yu.", self.lex,
                             prior="Ti gos ke.")
        self.assertEqual(check["act"], "confirmation_request")

    def test_forms_are_research_only_and_collision_checked(self):
        core = Lexicon.from_csv(DATA / "lexicon.csv")
        self.assertTrue(all(marker not in core for marker in MARKERS))
        self.assertTrue(all("-" in marker for marker in MARKERS))
        self.assertEqual(len({m.replace("-", "") for m in MARKERS}), len(MARKERS))
        for marker in MARKERS:
            with self.assertRaises(VekaError):
                parse(f"{marker} Mi gos yu.", core, strict=True)

    def test_invalid_provenance_and_unspecified_prior_rejected(self):
        for utterance, prior in (
            ("Ko-ta-ra Mi pa dak mel yu.", "Mi pa dak mel."),
            ("Re-pe-ta Mi pa dak mel yu.", "Ha gos."),
            ("Re-pe-ta Mi pa dak mel yu.", "Mi pa ne dak mel."),
            ("Ko-ta-ra Mi pa dak mel yu.", None),
        ):
            if utterance.startswith("Ko-ta-ra") and prior is None:
                continue
            with self.subTest(utterance=utterance, prior=prior), self.assertRaises(VekaError):
                parse_repair(utterance, self.lex, prior=prior)
        for phrase in ("", "Mi gos", "ko-ta-ra Mi gos yu yu"):
            with self.subTest(phrase=phrase), self.assertRaises(VekaError):
                parse_repair(phrase, self.lex)
        with self.assertRaises(VekaError):
            parse_repair("Ko-ta-ra Mi gos yu.", self.lex, max_words=2)

    def test_toneless_profile_quote_does_not_accept_tonal_form(self):
        lex = load_profile("toneless")
        allowed = parse_repair("Ko-ta-ra Mi fok mel yu.", lex)
        self.assertEqual(allowed["quote"]["ast"]["predicate"], "fok")
        with self.assertRaises(VekaError):
            parse_repair("Ko-ta-ra Mi pái mel yu.", lex)

    def test_cli_roundtrip_and_rejects_unbound_repair(self):
        good = subprocess.run(
            [sys.executable, "-m", "veka", "repair",
             "Ko-re-ta Mi pa dak mel yu Mi pa ne dak mel yu.",
             "--prior", "Mi pa dak mel."],
            cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(good.returncode, 0, good.stderr)
        result = json.loads(good.stdout)
        self.assertEqual(result["act"], "correction")
        bad = subprocess.run(
            [sys.executable, "-m", "veka", "repair",
             "Ko-re-ta Mi pa dak mel yu Mi pa ne dak mel yu."],
            cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(bad.returncode, 2)
        self.assertIn("prior", bad.stderr.lower())


if __name__ == "__main__":
    unittest.main()
