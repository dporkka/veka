"""Experimental words must not become canonical proper names due to capitalization."""
import unittest

from veka.core import Lexicon, VekaError, parse
from veka.registers import inspect_register
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ExtensionCaseBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")

    def test_capitalized_content_question_is_research_not_a_name(self):
        with self.assertRaises(VekaError):
            parse("Hon-ren pa gos.", self.lex, strict=True)
        classified = inspect_register("Hon-ren pa gos.", max_register="research")
        self.assertEqual(classified["register"], "research")
        self.assertEqual(classified["grammar_register"], "research")
        self.assertEqual(classified["ast"]["question_type"], "content")
        self.assertEqual(classified["ast"]["content_question"]["form"], "hon-ren")

    def test_capitalized_derived_agent_is_not_a_canonical_name(self):
        with self.assertRaises(VekaError):
            parse("Dak-nes pa gos.", self.lex, strict=True)
        classified = inspect_register("Dak-nes pa gos.", max_register="research")
        self.assertEqual(classified["grammar_register"], "research")
        self.assertEqual(classified["ast"]["subject"], "dak-nes")

    def test_real_hyphenated_names_remain_allowed(self):
        self.assertEqual(parse("Anne-Marie pa gos.", self.lex, strict=True)["subject"],
                         "Anne-Marie")
        self.assertEqual(parse("Mi lin O’Connor.", self.lex, strict=True)["object"],
                         "O’Connor")


if __name__ == "__main__":
    unittest.main()
