"""Noncanonical register gate: machine syntax, not human communication safety."""
import json
import subprocess
import sys
import unittest

from veka.core import VekaError
from veka.registers import inspect_register


class RegisterContractTests(unittest.TestCase):
    def test_core_is_strict_and_canonical(self):
        result = inspect_register("Mi pa dak mel.")
        self.assertEqual(result["register"], "core")
        self.assertEqual(result["grammar_register"], "core")
        self.assertEqual(result["profile"], "tonal")
        self.assertTrue(result["canonical_grammar"])
        self.assertTrue(result["canonical_lexicon"])
        self.assertEqual(result["ast"]["object"], "mel")
        self.assertFalse(result["human_comprehension_validated"])
        self.assertFalse(result["communication_safety_certified"])

    def test_core_rejects_missing_required_roles_and_unresolved_reference(self):
        for utterance in ("Mi dak.", "Sa dak mel.", "Mi dak sa."):
            with self.subTest(utterance=utterance), self.assertRaises(VekaError):
                inspect_register(utterance, max_register="core")

    def test_core_rejects_precise_and_experimental_syntax(self):
        for utterance in (
            "Zi mi gos ve ti gos yu.",
            "Mi gos zi ti gos.",
            "Sas mi yu pa dak mel.",
            "Sik ti ton mel yu mi dak mel.",
        ):
            with self.subTest(utterance=utterance), self.assertRaises(VekaError):
                inspect_register(utterance, max_register="core")

    def test_precise_accepts_fully_scoped_canonical_logic(self):
        result = inspect_register(
            "Zi mi gos ve ti gos yu.", max_register="precise"
        )
        self.assertEqual(result["register"], "precise")
        self.assertEqual(result["grammar_register"], "precise")
        self.assertEqual(result["parser"], "logic")
        self.assertTrue(result["canonical_grammar"])
        self.assertEqual(result["ast"]["op"], "and")

    def test_precise_does_not_allow_unpromoted_extension(self):
        for utterance in ("Mi gos zi ti gos.", "Sas mi yu pa dak mel."):
            with self.subTest(utterance=utterance), self.assertRaises(VekaError):
                inspect_register(utterance, max_register="precise")

    def test_research_accepts_but_flags_experimental_grammar(self):
        for utterance in (
            "Mi gos zi ti gos.",
            "Sas mi yu pa dak kol mel yu.",
            "Sik ti ton mel yu mi dak mel.",
            "Mi sen ka ti ton mel yu.",
        ):
            with self.subTest(utterance=utterance):
                result = inspect_register(utterance, max_register="research")
                self.assertEqual(result["register"], "research")
                self.assertEqual(result["grammar_register"], "research")
                self.assertFalse(result["canonical_grammar"])
                self.assertTrue(result["canonical_lexicon"])
                self.assertFalse(result["human_comprehension_validated"])

    def test_research_profile_never_gets_canonical_label(self):
        with self.assertRaises(VekaError):
            inspect_register("Mi fok mel.", profile="toneless", max_register="core")
        with self.assertRaises(VekaError):
            inspect_register("Mi fok mel.", profile="toneless", max_register="precise")
        result = inspect_register("Mi fok mel.", profile="toneless", max_register="research")
        self.assertEqual(result["register"], "research")
        self.assertEqual(result["grammar_register"], "core")
        self.assertFalse(result["canonical_lexicon"])
        self.assertTrue(result["canonical_grammar"])

    def test_toneless_rejects_tonal_root_not_silently_transliterated(self):
        with self.assertRaises(VekaError):
            inspect_register("Mi pái mel.", profile="toneless", max_register="research")

    def test_research_loanword_drafts_are_not_accepted_as_canonical(self):
        with self.assertRaises(VekaError):
            inspect_register("Mi sus mu-si-ka.", max_register="research")

    def test_rejects_unknown_profile_or_register(self):
        with self.assertRaises(VekaError):
            inspect_register("Mi gos.", profile="invented")
        with self.assertRaises(VekaError):
            inspect_register("Mi gos.", max_register="unsafe")

    def test_if_warning_does_not_equate_material_and_causal_if(self):
        result = inspect_register(
            "Fi mi dak mel ve ti ton mel yu.", max_register="precise"
        )
        self.assertEqual(result["ast"]["op"], "if")
        self.assertIn("material", " ".join(result["limitations"]).lower())

    def test_cli_returns_json_and_fail_closed_exit_status(self):
        good = subprocess.run(
            [sys.executable, "-m", "veka", "register-check", "Mi pa dak mel."],
            capture_output=True, text=True,
        )
        self.assertEqual(good.returncode, 0, good.stderr)
        payload = json.loads(good.stdout)
        self.assertEqual(payload["register"], "core")
        denied = subprocess.run(
            [sys.executable, "-m", "veka", "register-check",
             "Mi gos zi ti gos.", "--max-register", "precise"],
            capture_output=True, text=True,
        )
        self.assertEqual(denied.returncode, 2)
        self.assertIn("VEKA ERROR:", denied.stderr)

    def test_requested_research_gate_reports_lower_tier_when_appropriate(self):
        result = inspect_register("Mi gos.", max_register="research")
        self.assertEqual(result["register"], "core")
        self.assertEqual(result["allowed_through"], "research")


if __name__ == "__main__":
    unittest.main()
