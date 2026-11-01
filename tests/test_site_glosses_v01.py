"""The static learner must never guess translations or silently drift from canonical lessons."""
import json
import unittest
from pathlib import Path

from veka.learning import load_lessons
from veka.site_glosses import build_site_glosses

ROOT = Path(__file__).resolve().parents[1]


class SiteGlossExportTests(unittest.TestCase):
    def test_export_is_checked_in_and_matches_every_strict_dialogue(self):
        packet = build_site_glosses()
        self.assertEqual(packet["schema_version"], "veka.site-glosses.v01")
        self.assertEqual(packet["languages"], ["en", "zh", "pt-BR"])
        self.assertFalse(packet["human_comprehension_validated"])
        self.assertFalse(packet["canonical_vocabulary_changed"])
        source = load_lessons()
        self.assertEqual(len(packet["lessons"]), len(source))
        for lesson, glossary in zip(source, packet["lessons"]):
            self.assertEqual(glossary["id"], lesson["id"])
            self.assertEqual(len(glossary["turns"]), len(lesson["turns"]))
            for turn, glosses in zip(lesson["turns"], glossary["turns"]):
                self.assertEqual(glosses["veka"], turn["veka"])
                self.assertEqual(set(glosses["glosses"]), {"en", "zh", "pt-BR"})
                for language in packet["languages"]:
                    words = glosses["glosses"][language]
                    self.assertTrue(words)
                    self.assertTrue(all("token" in word and "gloss" in word for word in words))
                    self.assertTrue(all(word["gloss"] for word in words))
        committed = (ROOT / "data" / "site_glosses_v01.json").read_text(encoding="utf8")
        self.assertEqual(committed, json.dumps(packet, ensure_ascii=False, indent=2) + "\n")

    def test_site_provides_optional_glosses_without_claiming_sentence_translation(self):
        page = (ROOT / "site" / "index.html").read_text(encoding="utf8")
        self.assertIn('id="gloss-picker"', page)
        self.assertIn("../data/site_glosses_v01.json", page)
        self.assertIn("Word-by-word", page)
        self.assertIn("editorial", page)
        self.assertIn("human", page)


if __name__ == "__main__":
    unittest.main()
