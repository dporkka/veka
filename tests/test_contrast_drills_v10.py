"""Regression contracts for explicit multilingual contrast training."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.profiles import load_profile

ROOT = Path(__file__).resolve().parents[1]


class ContrastDrillsTests(unittest.TestCase):
    def test_licensed_minimal_pairs_are_parse_distinct_and_locally_glossed(self):
        from veka.contrast_drills import make_contrast_drills
        for profile in ("tonal", "toneless"):
            for language in ("en", "zh", "pt-BR"):
                with self.subTest(profile=profile, language=language):
                    packet = make_contrast_drills(language, profile=profile)
                    self.assertEqual(packet["schema_version"], "veka.contrast-drills.v1")
                    self.assertEqual(packet["language"], language)
                    self.assertEqual(packet["profile"], profile)
                    self.assertFalse(packet["human_comprehension_tested"])
                    self.assertFalse(packet["canonical_vocabulary_changed"])
                    self.assertGreaterEqual(len(packet["pairs"]), 5)
                    for pair in packet["pairs"]:
                        self.assertNotEqual(pair["a"]["structure"], pair["b"]["structure"])
                        self.assertEqual(pair["a"]["guide"]["gloss_coverage"]["english_fallback"], 0)
                        self.assertEqual(pair["b"]["guide"]["gloss_coverage"]["english_fallback"], 0)
                        self.assertTrue(pair["a"]["guide"]["grammar_validated"])
                        self.assertTrue(pair["b"]["guide"]["grammar_validated"])
                        self.assertTrue(pair["a"]["editorial_translation"])
                        self.assertTrue(pair["b"]["editorial_translation"])
                        self.assertEqual(pair["changed_feature"], pair["feature"])

    def test_invalid_language_and_profile_fail_closed(self):
        from veka.contrast_drills import make_contrast_drills
        for language in ("pt", "en-US", "", "fr"):
            with self.subTest(language=language), self.assertRaises(VekaError):
                make_contrast_drills(language)
        with self.assertRaises(VekaError):
            make_contrast_drills("en", profile="made-up")

    def test_drifted_semantics_or_unlicensed_syntax_are_rejected(self):
        from veka.contrast_drills import validate_contrast
        from veka.core import parse
        lex = load_profile("tonal")
        first = parse("Mi pa dak mel.", lex, strict=True)
        same = parse("Mi pa dak mel.", lex, strict=True)
        changed = parse("Mi fu dak mel.", lex, strict=True)
        with self.assertRaises(VekaError):
            validate_contrast("past", first, same)
        with self.assertRaises(VekaError):
            validate_contrast("negative", first, changed)
        with self.assertRaises(VekaError):
            validate_contrast("invented", first, changed)

    def test_cli_preserves_read_only_text_and_json_modes(self):
        for language in ("en", "zh", "pt-BR"):
            cmd = [sys.executable, "-m", "veka", "contrast-drills",
                   "--lang", language, "--format", "json"]
            result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            packet = json.loads(result.stdout)
            self.assertEqual(packet["language"], language)
            self.assertGreaterEqual(len(packet["pairs"]), 5)
        result = subprocess.run([sys.executable, "-m", "veka", "contrast-drills",
                                "--lang", "pt-BR"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Mi pa ne dak mel.", result.stdout)
        self.assertIn("Você", result.stdout)


if __name__ == "__main__":
    unittest.main()
