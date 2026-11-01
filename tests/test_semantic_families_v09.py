"""Read-only Interlingua-inspired families must never promote research vocabulary."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import VekaError, parse
from veka.profiles import load_profile
from veka.international import read_candidates
from veka.semantic_families import describe_family
from veka.beginner import guide_sentence, format_beginner_guide

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = read_candidates(ROOT / "data" / "international_candidates_v04.csv")


class FamilyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_verb_family_keeps_derived_words_experimental_and_typed(self):
        fam = describe_family("dak", self.lex, CANDIDATES)
        self.assertEqual(fam["base_form"], "dak")
        self.assertEqual(fam["base_gloss"], "send")
        self.assertEqual(fam["family_type"], "event_derivations")
        self.assertEqual(fam["canonical_entry_count"], 1)
        self.assertTrue(fam["root_is_canonical"])
        self.assertGreaterEqual(len(fam["experimental_derivations"]), 4)
        agent = next(item for item in fam["experimental_derivations"] if item["form"] == "dak-nes")
        self.assertEqual(agent["operation"], "agent")
        self.assertEqual(agent["semantic_contract"]["denoted_role"], "base_subject")
        self.assertFalse(agent["accepted_vocabulary"])
        self.assertNotIn("dak-nes", self.lex)
        with self.assertRaises(VekaError):
            parse("Mi lin dak-nes.", self.lex, strict=True)

    def test_noun_family_lists_only_existing_compounds_with_clear_relation(self):
        fam = describe_family("kun", self.lex, CANDIDATES, limit=2)
        self.assertEqual(fam["family_type"], "canonical_compounds")
        self.assertEqual(len(fam["canonical_compounds"]), 2)
        self.assertGreaterEqual(fam["canonical_compound_total"], 2)
        self.assertTrue(fam["family_truncated"])
        self.assertTrue(all(item["head"] == "kun" and item["relation"] == "noun_head"
                            for item in fam["canonical_compounds"]))
        self.assertTrue(all(item["accepted_vocabulary"] for item in fam["canonical_compounds"]))

    def test_compound_lookup_preserves_silent_hyphen_and_no_distinct_sense(self):
        fam = describe_family("ren-sak", self.lex, CANDIDATES)
        self.assertEqual(fam["queried_form"], "ren-sak")
        self.assertEqual(fam["base_form"], "ren")
        self.assertEqual(fam["compound_interpretation"], "person + knowledgeable")
        self.assertTrue(fam["silent_hyphen"])
        self.assertFalse(fam["lexicalized_distinct_sense"])

    def test_cues_remain_unverified_reading_associations(self):
        fam = describe_family("kun", self.lex, CANDIDATES)
        self.assertEqual(fam["international_association"]["reference_spelling"], "informacion")
        self.assertEqual(fam["international_association"]["status"], "unverified_draft")
        self.assertFalse(fam["international_association"]["accepted_vocabulary"])
        self.assertFalse(fam["human_recognition_measured"])

    def test_alt_profile_resolves_canonical_root_identity(self):
        profile = load_profile("toneless")
        fam = describe_family("fok", profile, CANDIDATES)
        self.assertEqual(fam["lexeme_id"], "core:pái")
        self.assertEqual(fam["base_gloss"], "remember")
        self.assertTrue(all(not item["accepted_vocabulary"] for item in fam["experimental_derivations"]))

    def test_unknown_form_or_bad_limit_fails(self):
        with self.assertRaises(VekaError):
            describe_family("in-fo-ma-si-on", self.lex, CANDIDATES)
        with self.assertRaises(VekaError):
            describe_family("ren", self.lex, CANDIDATES, limit=0)

    def test_beginner_optional_families_do_not_change_default_output(self):
        before = guide_sentence("Mi pa dak mel.", self.lex, CANDIDATES)
        self.assertNotIn("word_families", before)
        enhanced = guide_sentence("Mi pa dak mel.", self.lex, CANDIDATES, include_families=True)
        self.assertEqual(enhanced["interlinear"], before["interlinear"])
        self.assertEqual(enhanced["structure"], before["structure"])
        self.assertIn("dak", enhanced["word_families"])
        self.assertEqual(enhanced["word_families"]["dak"]["family_type"], "event_derivations")
        self.assertIn("Experimental word families", format_beginner_guide(enhanced))
        self.assertFalse(enhanced["canonical_vocabulary_changed"])

    def test_illustrative_readings_are_curated_not_generated_or_guessed(self):
        guide = guide_sentence("Mi pa dak mel.", self.lex, CANDIDATES, include_readings=True)
        example = guide["editorial_reading"]
        self.assertEqual(example["en"], "I sent a message.")
        self.assertEqual(example["pt-BR"], "Eu enviei uma mensagem.")
        self.assertFalse(example["machine_translation"])
        self.assertFalse(example["human_comprehension_validated"])
        self.assertIn("Illustrative editorial reading", format_beginner_guide(guide))
        unknown = guide_sentence("Ti pa dak mel.", self.lex, CANDIDATES, include_readings=True)
        self.assertIsNone(unknown["editorial_reading"])
        self.assertNotIn("editorial_reading", guide_sentence("Mi pa dak mel.", self.lex, CANDIDATES))

    def test_no_cues_suppresses_international_associations_even_with_families(self):
        guide = guide_sentence("Mi sen kun.", self.lex, CANDIDATES,
                               include_cues=False, include_families=True)
        self.assertIsNone(guide["word_families"]["kun"]["international_association"])

    def test_curated_reading_corpus_parses_strictly(self):
        corpus = json.loads((ROOT / "data" / "editorial_readings_v09.json").read_text())
        seen = set()
        for example in corpus["examples"]:
            with self.subTest(example=example["veka"]):
                self.assertNotIn(example["veka"], seen)
                seen.add(example["veka"])
                parse(example["veka"], self.lex, strict=True)
                self.assertTrue(example["en"].strip())
                self.assertTrue(example["pt-BR"].strip())

    def test_cli_family_and_beginner_option(self):
        cmd = [sys.executable, "-m", "veka", "family", "dak", "--format", "json"]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["base_form"], "dak")
        cmd = [sys.executable, "-m", "veka", "beginner", "Mi pa dak mel.",
               "--families", "--format", "json"]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("dak", json.loads(r.stdout)["word_families"])
        r = subprocess.run([sys.executable, "-m", "veka", "beginner", "Mi pa dak mel.",
                            "--readings", "--format", "json"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["editorial_reading"]["en"], "I sent a message.")


if __name__ == "__main__":
    unittest.main()
