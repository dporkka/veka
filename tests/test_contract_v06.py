"""Veka 0.6 design-freeze and transparent-compound semantic invariants.

This is a deterministic contract suite, not evidence of human comprehension.
"""
import hashlib
import json
import random
import unittest
from dataclasses import replace
from pathlib import Path

from veka.core import Lexicon, VekaError, parse
from veka.compounds import normalize_nominal_surface
from veka.numbers import read_number, spell_number

ROOT = Path(__file__).resolve().parents[1]


class CanonicalFreezeTests(unittest.TestCase):
    def test_versioned_manifest_locks_canonical_grammar_and_lexicon(self):
        manifest = json.loads((ROOT / "data/canonical_contract_v06.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "veka.canonical-contract.v06")
        self.assertEqual(manifest["canonical_language_version"], "0.4")
        self.assertEqual(set(manifest["sha256"]), {"data/lexicon.csv", "docs/grammar_v03.md"})
        for path, digest in manifest["sha256"].items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)
        lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")
        self.assertEqual(len(lex), manifest["headwords"])
        self.assertEqual(sum(e.kind == "root" for e in lex.values()), manifest["roots"])
        self.assertEqual(sum(e.kind == "compound" for e in lex.values()), manifest["compounds"])


class TransparentCompoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")

    def test_all_708_lexical_compounds_share_their_phrase_composition(self):
        compounds = [e for e in self.lex.values() if e.kind == "compound"]
        self.assertEqual(len(compounds), 708)
        for e in compounds:
            with self.subTest(compound=e.form):
                lexical = parse(f"Mi lin {e.form}.", self.lex, strict=True)["object"]
                phrased = parse(f"Mi lin {e.head} {e.modifier}.", self.lex, strict=True)["object"]
                self.assertEqual(
                    normalize_nominal_surface(lexical, self.lex),
                    normalize_nominal_surface(phrased, self.lex),
                )

    def test_modifiers_quantifiers_and_possession_are_retained(self):
        examples = [
            ("ren-sak bon", "ren sak bon"),
            ("al ren-sak", "al ren sak"),
            ("ren-sak de ni", "ren sak de ni"),
        ]
        for lexical, expanded in examples:
            with self.subTest(lexical=lexical):
                self.assertEqual(
                    normalize_nominal_surface(lexical, self.lex),
                    normalize_nominal_surface(expanded, self.lex),
                )

    def test_reject_unknown_or_invalid_nominal_surfaces(self):
        for phrase in ("ren-sak unknown", "ren--sak", "ren-sak gos", "sil-bon", ""):
            with self.subTest(phrase=phrase), self.assertRaises(VekaError):
                normalize_nominal_surface(phrase, self.lex)

    def test_corrupt_compound_metadata_fails_closed(self):
        compromised = Lexicon(self.lex)
        compromised["ren-sak"] = replace(self.lex["ren-sak"], head="sil")
        with self.assertRaises(VekaError):
            normalize_nominal_surface("ren-sak", compromised)


class DeterministicParserInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")

    def test_exact_decimal_roundtrip_seeded(self):
        rng = random.Random(20261101)
        for _ in range(150):
            width = rng.randint(1, 30)
            integer = str(rng.randrange(1, 10)) + "".join(str(rng.randrange(10)) for _ in range(width - 1))
            fraction = "".join(str(rng.randrange(10)) for _ in range(rng.randrange(1, 10)))
            value = ("-" if rng.randrange(2) else "") + integer + "." + fraction
            with self.subTest(value=value):
                self.assertEqual(read_number(spell_number(value)), value)

    def test_number_marker_after_noun_head_not_misparsed(self):
        noun = parse("Mi lin wen val.", self.lex, strict=True)
        self.assertEqual(noun["object"], "wen val")
        self.assertIsNone(noun["object_quantity"])
        measured = parse("Mi lin wen wen ran.", self.lex, strict=True)
        self.assertEqual(measured["object"], "wen wen ran")
        self.assertEqual(measured["object_quantity"], "1")

    def test_critical_word_order_and_punctuation_fail_closed(self):
        for sentence in (
            "Mi dak mel??", "Mi dak mel.!",
            "Mi ne ne dak mel.", "Mi pa fu dak mel.",
            "Mi dak mel to.", "Mi lin ren-sak?",
            "Al ren lin kis ren.", "Mi lin sil-bon.",
        ):
            if sentence == "Mi lin ren-sak?":
                # A single final question mark is intentionally valid.
                self.assertTrue(parse(sentence, self.lex, strict=True)["predicate"] == "lin")
                continue
            with self.subTest(sentence=sentence), self.assertRaises(VekaError):
                parse(sentence, self.lex, strict=True)
