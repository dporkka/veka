"""Opt-in spoken coordination and reversible script metadata contracts."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from veka.core import VekaError, render_svg, read_svg, parse
from veka.extended import parse_extended
from veka.logic import evaluate_logic, parse_logic
from veka.profiles import load_profile


class ConciseCoordinationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_two_atomic_statements_have_exact_formal_logic_ast(self):
        for operator in ("zi", "oi"):
            with self.subTest(operator=operator):
                concise = parse_extended(f"Mi gos {operator} ti gos.", self.lex)
                formal = parse_logic(f"{operator} mi gos ve ti gos yu.", self.lex)
                self.assertEqual(concise, formal)
                self.assertEqual(concise["op"], {"zi": "and", "oi": "or_inclusive"}[operator])

    def test_canonical_parser_is_unchanged_and_toneless_register_works(self):
        with self.assertRaises(VekaError):
            parse("Mi gos zi ti gos.", self.lex)
        alternate = load_profile("toneless")
        ast = parse_extended("Mi fok mel zi ti gos.", alternate)
        self.assertEqual(ast["left"]["clause"]["predicate"], "fok")

    def test_truth_values_match_the_explicitly_scoped_register(self):
        concise = parse_extended("Mi gos oi ti gos.", self.lex)
        self.assertFalse(evaluate_logic(concise, {"mi gos": False, "ti gos": False}))
        self.assertTrue(evaluate_logic(concise, {"mi gos": False, "ti gos": True}))

    def test_unsupported_infix_syntax_fails_closed(self):
        for utterance in (
            "Mi gos zi ti gos oi ni gos.",  # no hidden precedence
            "Mi gos zi.",                  # missing right operand
            "Zi mi gos ve ti gos yu.",     # formal register belongs to 'logic'
            "Mi gos zi ti gos ke.",        # questions need explicit scope
            "Ha gos zi ti gos.",           # commands aren't truth-valued
            "Mi dak zi ti gos.",           # obligatory object omitted
            "Mi gos fi ti gos.",           # material implication is never abbreviated
            "Mi sen ka ti gos yu zi ti gos.",  # embedded structures require full scope
        ):
            with self.subTest(utterance=utterance), self.assertRaises(VekaError):
                parse_extended(utterance, self.lex)


class ScriptRoundtripTests(unittest.TestCase):
    def test_svg_roundtrips_words_compounds_and_tones_through_metadata(self):
        for sentence, expected in (
            ("Mi pa dak mel.", "mi pa dak mel"),
            ("pál pal", "pál pal"),
            ("mi ren-sak", "mi ren-sak"),
            ("Mi pái mel.", "mi pái mel"),
        ):
            with self.subTest(sentence=sentence):
                self.assertEqual(read_svg(render_svg(sentence)), expected)

    def test_complete_canonical_and_toneless_vocabulary_metadata_roundtrip(self):
        for profile in ("tonal", "toneless"):
            lex = load_profile(profile)
            for word in lex:
                with self.subTest(profile=profile, word=word):
                    self.assertEqual(read_svg(render_svg(word)), word)

    def test_invalid_or_tampered_script_metadata_fails_closed(self):
        image = render_svg("mi dak")
        for corrupted in (
            image.replace('data-word-index="1"', 'data-word-index="0"'),
            image.replace('data-veka="dak"', 'data-veka="zzzzz"'),
            image.replace('data-tone="level"', 'data-tone="rising"'),
            image.replace('data-word-index="0"', 'data-word-index="2"'),
            image.replace('data-syllable-index="0"', 'data-syllable-index="2"'),
            '<svg xmlns="http://www.w3.org/2000/svg" />',
        ):
            with self.subTest(corrupted=corrupted[:80]), self.assertRaises(VekaError):
                read_svg(corrupted)

    def test_read_script_cli_reads_renderer_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_file = Path(tmp) / "words.svg"
            input_file.write_text(render_svg("Mi pa dak mel."), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "veka", "read-script", "--input", str(input_file)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            decoded = json.loads(result.stdout)
            self.assertEqual(decoded["romanized"], "mi pa dak mel")
            self.assertFalse(decoded["optical_recognition"])

    def test_read_svg_rejects_malformed_and_non_text_input(self):
        for invalid in ('<svg>', '<!DOCTYPE svg><svg/>', '', None, 42):
            with self.subTest(invalid=invalid), self.assertRaises(VekaError):
                read_svg(invalid)


if __name__ == "__main__":
    unittest.main()
