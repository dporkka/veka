"""Regression contracts for nonduplicate Veka 0.5 derivations salvaged from PR #3."""
import unittest

from veka.core import VekaError, parse
from veka.profiles import load_profile
from veka.extended import DERIVATIONS, derive, parse_extended


class UnifiedDerivationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tonal = load_profile("tonal")
        cls.toneless = load_profile("toneless")

    def test_existing_ops_remain_stable(self):
        self.assertEqual(derive("dak-nes", self.tonal)["operation"], "agent")
        self.assertEqual(derive("gos-vuk", self.tonal)["operation"], "cause")
        self.assertEqual(derive("dak-kas", self.tonal)["operation"], "attempt_reverse")

    def test_patient_is_not_agent(self):
        result = derive("dak-mol", self.tonal)
        self.assertEqual(result["operation"], "patient")
        self.assertEqual(result["pos"], "noun")
        self.assertEqual(result["semantics"], {"relation": "patient", "event_lemma": "dak"})
        self.assertEqual(parse_extended("Mi lin dak-mol.", self.tonal)["object"], "dak-mol")
        with self.assertRaises(VekaError):
            derive("gos-mol", self.tonal)

    def test_passive_able_is_patient_property_not_agent_ability(self):
        result = derive("dak-vau", self.tonal)
        self.assertEqual((result["operation"], result["pos"]), ("passive_able", "adjective"))
        self.assertEqual(parse_extended("Mel es dak-vau.", self.tonal)["predicate"], "dak-vau")
        with self.assertRaises(VekaError):
            derive("gos-vau", self.tonal)

    def test_repetition_preserves_transitivity(self):
        transitive = derive("dak-koin", self.tonal)
        self.assertEqual((transitive["operation"], transitive["valency"]), ("repeat", "transitive"))
        self.assertEqual(parse_extended("Mi dak-koin mel.", self.tonal)["object"], "mel")
        intransitive = derive("gos-koin", self.tonal)
        self.assertEqual(intransitive["valency"], "intransitive")
        self.assertEqual(parse_extended("Mi gos-koin.", self.tonal)["predicate"], "gos-koin")
        with self.assertRaises(VekaError):
            parse_extended("Mi gos-koin mel.", self.tonal)

    def test_extension_remains_opt_in_and_profile_aware(self):
        with self.assertRaises(VekaError):
            parse("Mi dak-koin mel.", self.tonal)
        self.assertEqual(derive("fok-koin", self.toneless)["operation"], "repeat")
        with self.assertRaises(VekaError):
            derive("fok-koin", self.tonal)

    def test_invalid_derivation_stacking_still_fails(self):
        for word in ("dak-koin-vau", "ren-mol", "dak-nosuffix"):
            with self.subTest(word=word), self.assertRaises(VekaError):
                derive(word, self.tonal)


if __name__ == "__main__":
    unittest.main()
