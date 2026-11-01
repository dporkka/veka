"""Research-only modal scopes and exact typed numerical comparisons."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError, parse, validate_word
from veka.profiles import DATA, load_profile
from veka.modality_comparison import MODALS, COMPARATORS, parse_modality_comparison

ROOT = Path(__file__).resolve().parents[1]


class ModalComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_three_modals_have_distinct_nonassertive_scope(self):
        for sentence, modality in (
            ("A-bi-li Mi gos yu.", "dynamic_ability"),
            ("Po-si-bi Ti gos yu.", "epistemic_possibility"),
            ("De-be-ri Mi dak mel yu.", "deontic_obligation"),
        ):
            with self.subTest(sentence=sentence):
                node = parse_modality_comparison(sentence, self.lex)
                self.assertEqual((node["kind"], node["modality"]), ("modality", modality))
                self.assertEqual(node["register"], "research")
                self.assertFalse(node["proposition_truth_verified"])
                self.assertFalse(node["canonical_grammar_changed"])
                self.assertFalse(node["canonical_lexicon_changed"])

    def test_explicit_outer_vs_inner_negation_are_not_equivalent(self):
        outer = parse_modality_comparison("Na A-bi-li Mi gos yu yu.", self.lex)
        inner = parse_modality_comparison("A-bi-li Mi ne gos yu.", self.lex)
        self.assertEqual(outer["negation_scope"], "outside_modality")
        self.assertFalse(outer["scope"]["ast"]["negative"])
        self.assertEqual(inner["negation_scope"], "inside_modality")
        self.assertTrue(inner["scope"]["ast"]["negative"])
        self.assertNotEqual(outer["semantics"], inner["semantics"])

    def test_modal_refuses_unclear_scope_and_implicit_context(self):
        for phrase in (
            "A-bi-li Ti gos ke yu.", "A-bi-li Al ren gos yu.",
            "A-bi-li Mi pa gos yu.", "A-bi-li Ha gos yu.",
            "A-bi-li Mi gos.", "Na A-bi-li Mi gos yu.",
            "A-bi-li Mi gos yu yu.", "A-bi-li Po-si-bi Mi gos yu yu.",
            "Po-si-bi Mi gos yu ke.", "A-bi-li Mi gos ve Ti gos yu.",
            "A-bi-li Sa gos yu.", "A-bi-li Mi gos yu Mi gos.",
        ):
            with self.subTest(phrase=phrase), self.assertRaises(VekaError):
                parse_modality_comparison(phrase, self.lex)

    def test_exact_greater_less_equal_and_false_comparison(self):
        cases = (
            ("Ga-val sil wen ran dis gel su wok ve sil wen ran su wok yu.", "greater_than", True),
            ("Ga-min sil wen ran su wok ve sil wen ran dis gel su wok yu.", "less_than", True),
            ("Ga-pal ren wen kuk ve ren wen kuk dis nul yu.", "equal_to", True),
            ("Ga-val sil wen ran su wok ve sil wen kuk su wok yu.", "greater_than", False),
            ("Ga-min ren wen sin ran ve ren wen nul yu.", "less_than", True),
        )
        for phrase, relation, truth in cases:
            with self.subTest(phrase=phrase):
                node = parse_modality_comparison(phrase, self.lex)
                self.assertEqual(node["kind"], "quantity_comparison")
                self.assertEqual(node["relation"], relation)
                self.assertEqual(node["numeric_relation_holds_for_literals"], truth)
                self.assertEqual(node["left"]["noun"], node["right"]["noun"])
                self.assertFalse(node["real_world_measurement_verified"])

    def test_mismatched_measurements_and_malformed_numbers_fail_closed(self):
        for phrase in (
            "Ga-val sil wen ran su wok ve sil wen kuk su vos yu.",
            "Ga-val sil wen ran su wok ve ren wen kuk su wok yu.",
            "Ga-min sil wen ran su wok ve sil wen kuk yu.",
            "Ga-pal sil wen ran ve sil wen ran su wok yu.",
            "Ga-val sil wen ran dis ve sil wen kuk yu.",
            "Ga-val sil wen nul ran ve sil wen ran yu.",
            "Ga-val sil wen sin nul ve sil wen ran yu.",
            "Ga-val sil wen ran su wok ve sil wen ran su bogus yu.",
            "Ga-val sil wen ran ve sil wen kuk ve sil wen ran yu.",
            "Ga-val sil wen ran ve sil wen kuk yu yu.",
            "Ga-pal sil wen ran ve sil wen ran.",
            "Ga-val mi wen ran ve mi wen kuk yu.",
            "Ga-val sil min wen ran ve sil wen kuk yu.",
            "Ga-val sil wen ran ve sil wen kuk yu ke.",
        ):
            with self.subTest(phrase=phrase), self.assertRaises(VekaError):
                parse_modality_comparison(phrase, self.lex)

    def test_big_numbers_are_compared_without_float_roundoff(self):
        left = "wen ran" + " nul" * 40 + " ran"
        right = "wen ran" + " nul" * 40 + " kuk"
        self.assertTrue(parse_modality_comparison(
            f"Ga-min ren {left} ve ren {right} yu.", self.lex
        )["numeric_relation_holds_for_literals"])
        with self.assertRaises(VekaError):
            parse_modality_comparison(
                "Ga-val ren wen ran" + " nul" * 65 + " ve ren wen ran yu.", self.lex
            )

    def test_marker_and_core_freeze_contract(self):
        canonical = Lexicon.from_csv(DATA / "lexicon.csv")
        markers = {*MODALS, *COMPARATORS}
        self.assertEqual(len(markers), 6)
        surfaces = {w.replace("-", "") for w in canonical}
        self.assertEqual(len({w.replace("-", "") for w in markers}), 6)
        for word in markers:
            with self.subTest(word=word):
                self.assertTrue(validate_word(word))
                self.assertNotIn(word.replace("-", ""), surfaces)
                with self.assertRaises(VekaError):
                    parse(f"{word} Mi gos yu.", canonical, strict=True)

    def test_invalid_input_and_toneless_boundary(self):
        for phrase in (None, "", " ", "A-bi-li Mi gos yu?",
                       "A-bi-li Mi gos yu!","A-bi-li Mi gos yu.\nMi gos."):
            with self.subTest(phrase=phrase), self.assertRaises(VekaError):
                parse_modality_comparison(phrase, self.lex)
        alt = load_profile("toneless")
        self.assertEqual(parse_modality_comparison(
            "Po-si-bi Mi fok mel yu.", alt
        )["scope"]["ast"]["predicate"], "fok")
        with self.assertRaises(VekaError):
            parse_modality_comparison("Po-si-bi Mi pái mel yu.", alt)

    def test_proper_names_are_not_lowercased_or_reinterpreted(self):
        node = parse_modality_comparison("A-bi-li São gos yu.", self.lex)
        self.assertEqual(node["scope"]["ast"]["subject"], "São")

    def test_cli_and_unmodified_register(self):
        proc = subprocess.run(
            [sys.executable, "-m", "veka", "modal-compare",
             "Ga-val sil wen ran dis gel su wok ve sil wen ran su wok yu."],
            cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(json.loads(proc.stdout)["numeric_relation_holds_for_literals"])
        rejected = subprocess.run(
            [sys.executable, "-m", "veka", "register-check",
             "A-bi-li Mi gos yu.", "--max-register", "research"],
            cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("not accepted", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
