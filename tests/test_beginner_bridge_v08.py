"""First-sight Veka reading aids, not a new vocabulary or a translation model."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import VekaError, parse
from veka.profiles import load_profile
from veka.international import read_candidates
from veka.beginner import guide_sentence, format_beginner_guide

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = read_candidates(ROOT / "data" / "international_candidates_v04.csv")


class BeginnerGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_interlinear_reading_preserves_canonical_text_and_role_semantics(self):
        sentence = "Mi pa dak mel."
        guide = guide_sentence(sentence, self.lex, CANDIDATES)
        self.assertEqual(guide["canonical"], sentence)
        self.assertEqual(
            guide["interlinear"],
            "Mi [I/me] pa [past] dak [send] mel [message].",
        )
        self.assertEqual([w["form"] for w in guide["words"]], ["mi", "pa", "dak", "mel"])
        self.assertEqual(guide["structure"]["subject"], "mi")
        self.assertEqual(guide["structure"]["tense"], "past")
        self.assertEqual(guide["structure"]["object"], "mel")
        self.assertTrue(guide["grammar_validated"])
        self.assertFalse(guide["translated"])
        self.assertFalse(guide["canonical_vocabulary_changed"])

    def test_unverified_international_spelling_is_a_separate_reading_hint_only(self):
        guide = guide_sentence("Mi sen kun.", self.lex, CANDIDATES)
        self.assertIn("kun [information]", guide["interlinear"])
        self.assertEqual(guide["experimental_cues"], [{
            "canonical_form": "kun",
            "gloss": "information",
            "illustrative_spelling": "informacion",
            "draft_form": "in-fo-ma-si-on",
            "status": "unverified_draft",
            "recognition_measured": False,
            "accepted_vocabulary": False,
        }])
        self.assertFalse(guide["human_recognition_measured"])
        with self.assertRaises(VekaError):
            parse("Mi sen in-fo-ma-si-on.", self.lex, strict=True)
        self.assertIn("NOT accepted Veka", format_beginner_guide(guide))

    def test_numeric_tokens_and_compounds_get_structural_explanations(self):
        guide = guide_sentence("Mi rin sil wen ran dis gel su wok.", self.lex, CANDIDATES)
        self.assertIn("wen [exact-number marker]", guide["interlinear"])
        self.assertIn("ran [digit 1]", guide["interlinear"])
        self.assertIn("dis [decimal point]", guide["interlinear"])
        self.assertIn("wok [liter]", guide["interlinear"])
        self.assertEqual(guide["structure"]["object_quantity"], "1.5")

        compound = guide_sentence("Ren-sak pa gos.", self.lex, CANDIDATES)
        self.assertIn("Ren-sak [person + knowledgeable]", compound["interlinear"])
        self.assertEqual(compound["words"][0]["kind"], "transparent_compound")
        self.assertTrue(compound["words"][0]["silent_hyphen"])

    def test_headword_wen_remains_distinct_from_number_marker(self):
        guide = guide_sentence("Mi lin wen wen ran.", self.lex, CANDIDATES)
        self.assertIn("wen [number] wen [exact-number marker] ran [digit 1]", guide["interlinear"])

    def test_toneless_profile_and_no_cues_mode(self):
        lex = load_profile("toneless")
        guide = guide_sentence("Mi fok mel.", lex, CANDIDATES, profile="toneless")
        self.assertIn("fok [remember]", guide["interlinear"])
        self.assertEqual(guide["profile"], "toneless")
        self.assertEqual(guide["experimental_cues"], [])
        guide = guide_sentence("Mi sen kun.", self.lex, CANDIDATES, include_cues=False)
        self.assertEqual(guide["experimental_cues"], [])

    def test_invalid_or_unsupported_sentences_fail_closed(self):
        for sentence in ("Mi dak.", "Mi pa unknown mel.", "Mi pa dak mel; ti gos.",
                         "Mi pa dak mel. Ti gos.", "", "Pa dak mel."):
            with self.subTest(sentence=sentence):
                with self.assertRaises(VekaError):
                    guide_sentence(sentence, self.lex, CANDIDATES)

    def test_candidate_remapping_cannot_be_used_to_mislead_beginner(self):
        corrupted = [dict(row) for row in CANDIDATES]
        corrupted[3]["gloss"] = "safe"
        with self.assertRaises(VekaError):
            guide_sentence("Mi sen kun.", self.lex, corrupted)

    def test_cli_text_and_json_outputs(self):
        args = [sys.executable, "-m", "veka", "beginner", "Mi sen kun."]
        text_out = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(text_out.returncode, 0, text_out.stderr)
        self.assertIn("Mi [I/me] sen [understand] kun [information].", text_out.stdout)
        self.assertIn("NOT accepted Veka", text_out.stdout)

        json_out = subprocess.run(args + ["--format", "json"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(json_out.returncode, 0, json_out.stderr)
        data = json.loads(json_out.stdout)
        self.assertEqual(data["canonical"], "Mi sen kun.")
        self.assertFalse(data["canonical_vocabulary_changed"])


if __name__ == "__main__":
    unittest.main()
