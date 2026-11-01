"""Unicode capitalized proper names: strict parsing without broadening Veka roots."""
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError, parse
from veka.logic import parse_logic
from veka.beginner import guide_sentence
from veka.international import read_candidates

ROOT = Path(__file__).resolve().parents[1]


class UnicodeProperNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")

    def test_strict_roles_preserve_unicode_names(self):
        for name in ("São", "Łódź", "Αθήνα", "Élodie", "O’Connor", "Anne-Marie", "Renée"):
            with self.subTest(name=name):
                self.assertEqual(parse(f"Mi lin {name}.", self.lex, strict=True)["object"], name)

    def test_unicode_names_work_in_subject_and_precise_logic(self):
        self.assertEqual(parse("Łódź pa gos.", self.lex, strict=True)["subject"], "Łódź")
        logic = parse_logic("Zi São gos ve ti gos yu.", self.lex, strict=True)
        self.assertEqual(logic["left"]["clause"]["subject"], "São")

    def test_non_lexical_names_have_separate_beginner_gloss(self):
        guide = guide_sentence("Mi lin São.", self.lex, read_candidates(ROOT / "data/international_candidates_v04.csv"))
        self.assertEqual(guide["words"][-1]["kind"], "proper_name")
        self.assertEqual(guide["words"][-1]["form"], "São")

    def test_nfd_unicode_is_normalized_without_changing_meaning(self):
        ast = parse("Mi lin Sa\u0303o.", self.lex, strict=True)
        self.assertEqual(ast["object"], "São")

    def test_canonical_words_still_take_precedence_over_names(self):
        self.assertEqual(parse("Mi gos.", self.lex, strict=True)["subject"], "mi")
        self.assertEqual(parse("Mi lin Mi.", self.lex, strict=True)["object"], "mi")

    def test_reject_name_punctuation_control_and_broken_separators(self):
        for token in ("X--Y", "-São", "São-", "O''Connor", "A@B",
                      "São\u202e", "A1", "😄", "aBC"):
            with self.subTest(token=token), self.assertRaises(VekaError):
                parse(f"Mi lin {token}.", self.lex, strict=True)

    def test_uncased_multitoken_names_remain_unsupported(self):
        for text in ("Mi lin 東京.", "Mi lin São Paulo."):
            with self.subTest(text=text), self.assertRaises(VekaError):
                parse(text, self.lex, strict=True)


if __name__ == "__main__":
    unittest.main()
