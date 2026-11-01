"""Regression contracts for optional, canonical Veka semantic interpretation."""
import json
import subprocess
import sys
import unittest

from veka.core import VekaError
from veka.profiles import load_profile
from veka.semantic_scope import analyze_scope


class SemanticScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def analyze(self, sentence):
        return analyze_scope(sentence, self.lex)["tree"]

    def test_universal_predicate_negation_is_inside_quantifier(self):
        tree = self.analyze("Al ren ne gos.")
        self.assertEqual(tree["op"], "forall")
        self.assertEqual(tree["binder"]["role"], "subject")
        self.assertEqual(tree["binder"]["domain"]["tokens"], ["ren"])
        self.assertEqual(tree["body"]["op"], "not")
        predicate = tree["body"]["argument"]
        self.assertEqual(predicate["op"], "predicate")
        self.assertEqual(predicate["predicate"], "gos")
        self.assertEqual(predicate["arguments"][0]["value"], {"variable": "x1"})

    def test_outer_negation_has_different_scope(self):
        inner = self.analyze("Al ren ne gos.")
        outer = self.analyze("Na al ren gos yu.")
        self.assertEqual(outer["op"], "not")
        self.assertEqual(outer["argument"]["op"], "forall")
        self.assertNotEqual(inner, outer)
        self.assertEqual(outer["argument"]["body"]["op"], "predicate")

    def test_existential_and_negated_existential_are_distinct(self):
        positive = self.analyze("Kis ren gos.")
        negative = self.analyze("Na kis ren gos yu.")
        self.assertEqual(positive["op"], "exists")
        self.assertEqual(negative["op"], "not")
        self.assertEqual(negative["argument"]["op"], "exists")

    def test_quantified_direct_object_binds_only_its_role(self):
        tree = self.analyze("Mi lin kis ren.")
        self.assertEqual(tree["op"], "exists")
        self.assertEqual(tree["binder"]["role"], "object")
        args = tree["body"]["arguments"]
        self.assertEqual([a["role"] for a in args], ["subject", "object"])
        self.assertEqual(args[0]["value"]["tokens"], ["mi"])
        self.assertEqual(args[1]["value"], {"variable": "x1"})

    def test_bare_predicate_has_explicit_frame_and_adjuncts(self):
        tree = self.analyze("Mi dak mel to ti en pas sun.")
        self.assertEqual(tree["op"], "predicate")
        self.assertEqual(tree["predicate"], "dak")
        self.assertEqual([a["label"] for a in tree["arguments"]], ["sender", "sent_item"])
        self.assertEqual([a["role"] for a in tree["adjuncts"]],
                         ["recipient", "location", "time"])
        self.assertEqual(tree["adjuncts"][0]["value"]["tokens"], ["ti"])
        self.assertEqual(tree["tense"], "unspecified")

    def test_unknown_lexical_frame_uses_structural_not_invented_labels(self):
        tree = self.analyze("Mi rin mel.")
        self.assertEqual([a["label"] for a in tree["arguments"]], ["subject", "object"])

    def test_compound_and_analytic_nominal_have_same_structural_tokens(self):
        compound = self.analyze("Ren-sak gos.")
        analytic = self.analyze("Ren sak gos.")
        self.assertEqual(compound, analytic)
        self.assertEqual(compound["arguments"][0]["value"]["tokens"], ["ren", "sak"])

    def test_nested_boolean_scope_retained(self):
        tree = self.analyze("Zi na mi gos yu ve ti gos yu.")
        self.assertEqual(tree["op"], "and")
        self.assertEqual(tree["left"]["op"], "not")
        self.assertEqual(tree["right"]["op"], "predicate")

    def test_material_implication_is_not_a_causal_claim(self):
        tree = self.analyze("Fi mi gos ve ti gos yu.")
        self.assertEqual(tree["op"], "if")
        self.assertEqual(tree["interpretation"], "material_implication")

    def test_unsupported_quantification_fails_closed(self):
        for sentence in (
            "Al ren lin kis ren.",
            "Ren de kis ren gos.",
            "Mi lin ren de al ren.",
            "Na al ren gos.",
            "Sas ren yu gos.",
            "Mi dak.",
            "Mi gos ke.",
        ):
            with self.subTest(sentence=sentence), self.assertRaises(VekaError):
                self.analyze(sentence)

    def test_cli_output_contains_semantic_tree(self):
        result = subprocess.run(
            [sys.executable, "-m", "veka", "semantic", "Na al ren gos yu."],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["schema_version"], "veka.semantic-scope.v01")
        self.assertEqual(parsed["tree"]["op"], "not")
        self.assertFalse(parsed["truth_evaluated"])


if __name__ == "__main__":
    unittest.main()
