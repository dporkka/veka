"""Veka 0.6 tests: discourse marking, restricted quantifiers, temporal clauses."""
import json
import subprocess
import sys
from pathlib import Path
import unittest

from veka.core import VekaError
from veka.profiles import load_profile
from veka.discourse import parse_discourse, MARKERS


class DiscourseGrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_new_markers_have_valid_unique_segmental_forms(self):
        from veka.core import validate_word
        self.assertEqual(len(MARKERS), 5)
        for left in MARKERS:
            self.assertTrue(validate_word(left))
            self.assertNotIn(left, self.lex)
            for right in MARKERS:
                if left != right:
                    self.assertGreaterEqual(sum(a != b for a, b in zip(left, right)), 2)

    def test_mark_subject_topic_without_anaphora_guessing(self):
        ast = parse_discourse("Sas ren yu pa gos.", self.lex)
        self.assertEqual(ast["subject"], "ren")
        self.assertEqual(ast["topic"], {"role": "subject", "value": "ren"})
        self.assertFalse(ast["compressed"])

    def test_mark_object_focus_and_dual_markers(self):
        ast = parse_discourse("Mi pa dak kol mel yu.", self.lex)
        self.assertEqual(ast["focus"], {"role": "object", "value": "mel"})
        self.assertEqual(ast["object"], "mel")
        both = parse_discourse("Sas mi yu pa dak kol mel yu.", self.lex)
        self.assertEqual(both["topic"]["role"], "subject")
        self.assertEqual(both["focus"]["role"], "object")

    def test_topic_and_focus_cannot_misidentify_repeated_roles(self):
        for text in (
            "Mi lin kol ren yu to ren.",
            "Sas ren yu pa gos sas ren yu.",
            "Sas ren pa gos.",
            "Sas ren yu.",
            "Kol ren yu pa gos ke.",
            "Sas ren yu pa gos kol mel yu.",
        ):
            with self.subTest(text=text), self.assertRaises(VekaError):
                parse_discourse(text, self.lex)

    def test_ordinary_grammar_keeps_existing_ast(self):
        from veka.extended import parse_extended
        base = parse_extended("Mi pa dak mel.", self.lex)
        self.assertEqual(parse_discourse("Mi pa dak mel.", self.lex), base)

    def test_domain_restriction_is_explicit_predicate_metadata(self):
        result = parse_discourse("Al ren gin pas yu pa gos.", self.lex)
        self.assertEqual(result["subject_quantifier"], "every")
        self.assertEqual(result["quantifier_domain"],
                         {"role": "subject", "quantifier": "every",
                          "head": "ren", "relation": "located_in",
                          "place": "pas"})
        existential = parse_discourse("Mi lin kis ren gin pas yu.", self.lex)
        self.assertEqual(existential["quantifier_domain"]["quantifier"], "some")

    def test_domain_restriction_cannot_be_detached_or_untyped(self):
        for text in (
            "Mi pa gos gin pas yu.",
            "Ren gin pas yu pa gos.",
            "Al ren gin mel yu pa gos.",
            "Al ren gin pas pa gos.",
            "Al ren gin pas yu lin kis ren.",
            "Al ren gin pas yu pa gos gin pas yu.",
            "Al ren gin pas yu pa gos yu.",
        ):
            with self.subTest(text=text), self.assertRaises(VekaError):
                parse_discourse(text, self.lex)

    def test_coordination_remains_supported_only_when_unmarked(self):
        from veka.extended import parse_extended
        basic = "Mi gos zi ti gos."
        self.assertEqual(parse_discourse(basic, self.lex), parse_extended(basic, self.lex))
        for expression in (
            "Sas mi yu gos zi ti gos.",
            "Al ren gin pas yu gos zi ti gos.",
            "Sik ti gos yu mi gos zi ti gos.",
            "Sik ti gos zi mi gos yu mi dak mel.",
        ):
            with self.subTest(expression=expression), self.assertRaises(VekaError):
                parse_discourse(expression, self.lex)

    def test_temporal_before_after_has_distinct_relations(self):
        before = parse_discourse("Sik ti ton mel yu mi dak mel.", self.lex)
        after = parse_discourse("Men ti ton mel yu mi dak mel.", self.lex)
        self.assertEqual(before["temporal"]["relation"], "main_before_subordinate")
        self.assertEqual(after["temporal"]["relation"], "main_after_subordinate")
        self.assertEqual(before["temporal"]["clause"]["predicate"], "ton")
        self.assertEqual(before["predicate"], "dak")

    def test_temporal_rejects_incomplete_questions_and_nested_scopes(self):
        for text in (
            "Sik ti ton yu mi dak mel.",
            "Sik hon-ren pa gos yu mi dak mel.",
            "Sik ti ton mel mi dak mel.",
            "Sik ti ton mel yu.",
            "Sik sik ti ton mel yu mi dak mel yu mi dak mel.",
            "Sik ti ton mel yu mi dak mel ke.",
            "Men ti ton mel yu mi sen ka ti ton mel yu.",
        ):
            with self.subTest(text=text), self.assertRaises(VekaError):
                parse_discourse(text, self.lex)

    def test_combined_topic_and_restricted_quantifier(self):
        ast = parse_discourse("Sas al ren yu gin pas yu pa gos.", self.lex)
        self.assertEqual(ast["topic"]["role"], "subject")
        self.assertEqual(ast["quantifier_domain"]["place"], "pas")

    def test_toneless_profile(self):
        alt = load_profile("toneless")
        ast = parse_discourse("Kol fok-nes yu pa gos.", alt)
        self.assertEqual(ast["focus"]["value"], "fok-nes")

    def test_candidate_listening_stimuli_are_valid_and_structurally_distinct(self):
        path = Path(__file__).resolve().parents[1] / "data" / "discourse_stimuli_v06.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], "veka-v06")
        self.assertEqual(len(payload["items"]), len({i["id"] for i in payload["items"]}))
        self.assertGreaterEqual(len(payload["items"]), 6)
        for item in payload["items"]:
            with self.subTest(item=item["id"]):
                main = parse_discourse(item["sentence"], self.lex)
                control = parse_discourse(item["control"], self.lex)
                self.assertNotEqual(main, control)

    def test_cli_disclosure_and_success(self):
        result = subprocess.run(
            [sys.executable, "-m", "veka", "discourse", "Sik ti ton mel yu mi dak mel."],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["temporal"]["relation"], "main_before_subordinate")


if __name__ == "__main__":
    unittest.main()
