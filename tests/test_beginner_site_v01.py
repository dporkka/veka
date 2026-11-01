"""Verify learner assets ship with the same canonical dialogue corpus."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BeginnerSiteTests(unittest.TestCase):
    def test_static_web_learner_is_self_contained_and_uses_canonical_data(self):
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("../data/beginner_dialogues_v01.json", page)
        self.assertIn('id="lesson-picker"', page)
        self.assertIn('id="quiz"', page)
        self.assertIn('id="feedback"', page)
        self.assertIn("<main", page)
        self.assertNotIn("https://cdn.", page)

    def test_canonical_data_has_only_nonexperimental_labels(self):
        data = json.loads((ROOT / "data" / "beginner_dialogues_v01.json").read_text())
        self.assertEqual(data["canonical_profile"], "tonal")
        self.assertEqual(data["canonical_language_version"], "0.4")
        self.assertTrue(all(len(lesson["turns"]) == 4 for lesson in data["lessons"]))


if __name__ == "__main__":
    unittest.main()
