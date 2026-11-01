"""Contracts for the opt-in structural communication benchmark; not human results."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.profiles import load_profile
from veka.communication_v07 import (generate_cases, validate_cases, audit_communication)

ROOT = Path(__file__).resolve().parents[1]
SEEDS = json.loads((ROOT / "data/communication_domains_v07.json").read_text(encoding="utf-8"))


class CommunicationCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_corpus_is_large_deterministic_and_has_adversarial_controls(self):
        first = generate_cases(SEEDS, self.lex)
        self.assertEqual(first, generate_cases(SEEDS, self.lex))
        self.assertGreaterEqual(len(first), 200)
        self.assertLessEqual(len(first), 500)
        self.assertEqual(len({x["id"] for x in first}), len(first))
        categories = {x["category"] for x in first}
        self.assertEqual(categories, {
            "role_reversal", "negation", "tense", "polar_question", "quantity",
            "recipient", "location", "quantifier", "equivalent_control",
            "unsafe_ellipsis",
        })
        self.assertGreaterEqual(sum(x["category"] == "unsafe_ellipsis" for x in first), 10)
        self.assertGreaterEqual(sum(x["category"] == "equivalent_control" for x in first), 10)
        self.assertEqual({x["provenance"] for x in first}, {"synthetic_template"})

    def test_semantics_fully_checked_under_strict_parse(self):
        cases = generate_cases(SEEDS, self.lex)
        summary = audit_communication(cases, self.lex, profile="tonal")
        self.assertEqual(summary["scenarios"], len(cases))
        self.assertEqual(summary["verified"], len(cases))
        self.assertEqual(summary["structural_failures"], 0)
        self.assertGreater(summary["contrast_pairs"], 100)
        self.assertGreater(summary["equivalent_controls"], 10)
        self.assertGreater(summary["unsafe_ellipsis_rejections"], 10)
        self.assertEqual(summary["human_participants"], 0)
        self.assertIsNone(summary["human_accuracy"])
        self.assertFalse(summary["acoustic_validation"])
        self.assertTrue(summary["corpus_sha256"])
        self.assertEqual(summary, audit_communication(cases, self.lex, profile="tonal"))

    def test_toneless_profile_preserves_semantic_contrast_contract(self):
        alt = load_profile("toneless")
        cases = generate_cases(SEEDS, alt)
        result = audit_communication(cases, alt, profile="toneless")
        self.assertEqual(result["verified"], len(cases))
        self.assertEqual(result["structural_failures"], 0)

    def test_fails_closed_on_incorrect_expected_semantics_and_duplicates(self):
        cases = generate_cases(SEEDS, self.lex)
        changed = copy.deepcopy(cases)
        changed[0]["expected_differences"] = ["negative"]
        with self.assertRaises(VekaError):
            validate_cases(changed, self.lex)
        changed = copy.deepcopy(cases)
        changed[0]["b"] = changed[0]["a"]
        with self.assertRaises(VekaError):
            validate_cases(changed, self.lex)
        with self.assertRaises(VekaError):
            validate_cases(cases + [cases[0]], self.lex)
        changed = copy.deepcopy(cases)
        changed[0]["a"] = "Mi blarg mel."
        with self.assertRaises(VekaError):
            validate_cases(changed, self.lex)

    def test_rejects_unsafe_context_and_invalid_seed(self):
        cases = generate_cases(SEEDS, self.lex)
        i = next(i for i, x in enumerate(cases) if x["category"] == "unsafe_ellipsis")
        changed = copy.deepcopy(cases)
        changed[i]["ambiguous_subjects"] = ["mi"]
        with self.assertRaises(VekaError):
            validate_cases(changed, self.lex)
        changed = copy.deepcopy(SEEDS)
        changed["transitive"][0]["verb"] = "gos"
        with self.assertRaises(VekaError):
            generate_cases(changed, self.lex)
        changed = copy.deepcopy(SEEDS)
        changed["transitive"][0]["countable"] = True
        changed["transitive"][0]["object"] = "sil"
        with self.assertRaises(VekaError):
            generate_cases(changed, self.lex)

    def test_cli_emits_explicit_machine_only_limits(self):
        p = subprocess.run(
            [sys.executable, "-m", "veka", "communication-audit"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        output = json.loads(p.stdout)
        self.assertGreaterEqual(output["scenarios"], 200)
        self.assertEqual(output["profile"], "tonal")
        self.assertFalse(output["acoustic_validation"])
        self.assertIsNone(output["human_accuracy"])
        self.assertEqual(output["human_participants"], 0)
        self.assertNotIn("correct_messages_per_minute", output)


if __name__ == "__main__":
    unittest.main()
