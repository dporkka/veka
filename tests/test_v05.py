"""Veka 0.5 experimental extensions: explicit tests written before implementation."""
import unittest
import subprocess
import sys
import json

from veka.core import VekaError, parse
from veka.profiles import load_profile
from veka.extended import parse_extended, derive, correlative, extended_lexicon, DERIVATIONS


class MorphologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_agent_and_instrument_have_compositional_semantics(self):
        a = derive("dak-nes", self.lex)
        self.assertEqual((a["base"], a["operation"], a["pos"]), ("dak", "agent", "noun"))
        self.assertEqual(derive("dak-sul", self.lex)["operation"], "instrument")
        self.assertEqual(parse_extended("Mi lin dak-nes.", self.lex)["object"], "dak-nes")

    def test_derivational_operator_forms_have_segmental_distance(self):
        suffixes = tuple(DERIVATIONS)
        for i, left in enumerate(suffixes):
            for right in suffixes[i + 1:]:
                with self.subTest(left=left, right=right):
                    self.assertGreaterEqual(sum(x != y for x, y in zip(left, right)), 2)

    def test_causative_intransitive_becomes_transitive(self):
        result = derive("gos-vuk", self.lex)
        self.assertEqual(result["valency"], "transitive")
        self.assertEqual(parse_extended("Mi gos-vuk ti.", self.lex)["predicate"], "gos-vuk")
        with self.assertRaises(VekaError):
            derive("dak-vuk", self.lex)

    def test_six_operators_and_nonverb_bases(self):
        for suffix in ("nes", "sul", "zel", "dil", "kas"):
            self.assertEqual(derive("dak-" + suffix, self.lex)["base"], "dak")
        for bad in ("ren-nes", "dak-bad", "gos-nes-tes", "unknown-nes"):
            with self.subTest(bad=bad), self.assertRaises(VekaError):
                derive(bad, self.lex)

    def test_canonical_lexicon_preserved_and_toneless_supported(self):
        self.assertEqual(len(self.lex), 1025)
        self.assertEqual(len(extended_lexicon(self.lex)), 1025 + 24)
        alt = load_profile("toneless")
        self.assertEqual(parse_extended("Fok-nes pa gos.", alt)["subject"], "fok-nes")


class CorrelativeTests(unittest.TestCase):
    def test_cross_product_and_roles(self):
        l = load_profile("tonal")
        cases = {
            "hon-ren": ("interrogative", "person"),
            "hal-ril": ("demonstrative", "thing"),
            "nis-lok": ("indefinite", "place"),
            "pan-kel": ("universal", "time"),
            "hon-wek": ("interrogative", "manner"),
            "pan-gas": ("universal", "quantity"),
        }
        for word, expected in cases.items():
            d = correlative(word, l)
            self.assertEqual((d["series"], d["domain"]), expected)
        with self.assertRaises(VekaError):
            correlative("hon-gos", l)

    def test_interrogative_requires_explicit_content_and_no_ke(self):
        l = load_profile("tonal")
        sentence = parse_extended("Hon-ren pa gos.", l)
        self.assertEqual(sentence["question_type"], "content")
        self.assertTrue(sentence["question"])
        self.assertEqual(sentence["content_question"]["role"], "subject")
        with self.assertRaises(VekaError):
            parse_extended("Hon-ren pa gos ke.", l)

    def test_quantifier_scope_rejects_two_correlative_quantifiers(self):
        l = load_profile("tonal")
        self.assertEqual(parse_extended("Pan-ren pa gos.", l)["subject_quantifier"], "every")
        with self.assertRaises(VekaError):
            parse_extended("Pan-ren lin nis-ril.", l)

    def test_unintegrated_domains_rejected_in_sentences(self):
        l = load_profile("tonal")
        self.assertEqual(correlative("hon-gas", l)["domain"], "quantity")
        with self.assertRaises(VekaError):
            parse_extended("Mi pa gos hon-wek.", l)


class CommandLineTests(unittest.TestCase):
    def test_extension_is_exposed_as_opt_in_cli(self):
        p = subprocess.run([sys.executable, "-m", "veka", "extend", "Mi sen ka ti ton mel yu."], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["object_clause"]["predicate"], "ton")


class EmbeddedClauseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_complement_proposition_has_distinct_ast(self):
        a = parse_extended("Mi sen ka ti ton mel yu.", self.lex)
        self.assertEqual(a["object_clause"]["subject"], "ti")
        self.assertEqual(a["object_clause"]["predicate"], "ton")
        self.assertEqual(a["object"], None)

    def test_complement_licensed_predicate_and_complete_roles_required(self):
        with self.assertRaises(VekaError):
            parse_extended("Mi dak ka ti ton mel yu.", self.lex)
        with self.assertRaises(VekaError):
            parse_extended("Mi sen ka ti ton yu.", self.lex)
        with self.assertRaises(VekaError):
            parse_extended("Mi sen ka ti ton mel.", self.lex)
        with self.assertRaises(VekaError):
            parse_extended("Mi sen ka ha gos yu.", self.lex)

    def test_relative_subject_and_object_gaps(self):
        a = parse_extended("Ren ri wek dak mel yu pa gos.", self.lex)
        self.assertEqual(a["subject_relative"]["gap_role"], "subject")
        self.assertEqual(a["subject_relative"]["clause"]["predicate"], "dak")
        b = parse_extended("Mi lin ren ri ti ton wek yu.", self.lex)
        self.assertEqual(b["object_relative"]["gap_role"], "object")
        self.assertEqual(b["object_relative"]["clause"]["subject"], "ti")

    def test_relative_rejects_missing_multiple_and_unsafe_gap(self):
        for s in (
            "Ren ri mi dak mel yu pa gos.",
            "Ren ri wek lin wek yu pa gos.",
            "Ren ri wek dak yu pa gos.",
            "Mi lin ren ri mi gos yu.",
            "Ren ri ti gos yu pa gos.",
            "Ren ri wek dak mel yu yu pa gos.",
        ):
            with self.subTest(s=s), self.assertRaises(VekaError):
                parse_extended(s, self.lex)

    def test_proper_object_in_original_parser(self):
        self.assertEqual(parse("Mi ton Ana.", self.lex)["object"], "Ana")

    def test_no_nested_extensions_and_existing_parse_unchanged(self):
        with self.assertRaises(VekaError):
            parse_extended("Mi sen ka ren ri wek dak mel yu pa gos yu.", self.lex)
        baseline = parse_extended("Mi pa dak mel to ti.", self.lex)
        self.assertEqual(baseline["predicate"], "dak")
        self.assertFalse(baseline["compressed"])


if __name__ == "__main__":
    unittest.main()
