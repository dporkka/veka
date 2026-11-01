"""Beginner lessons: structural validity, stable quiz answers, and fail-closed inputs."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.learning import load_lessons, create_question, check_answer

ROOT = Path(__file__).resolve().parents[1]


class BeginnerLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lessons = load_lessons()

    def test_curated_corpus_is_parseable_and_broad_enough_to_pilot(self):
        self.assertEqual(len(self.lessons), 25)
        self.assertEqual(sum(len(lesson["turns"]) for lesson in self.lessons), 100)
        self.assertEqual([lesson["id"] for lesson in self.lessons], [f"B{i:02d}" for i in range(1, 26)])
        self.assertGreaterEqual(sum(" ke?" in turn["veka"].lower() for lesson in self.lessons for turn in lesson["turns"]), 20)

    def test_first_lesson_remains_a_teachable_exchange(self):
        first = self.lessons[0]
        self.assertEqual(first["title"], "Understanding and messages")
        self.assertEqual(first["turns"][0]["veka"], "Ti sen mel ke?")
        self.assertEqual(first["turns"][0]["english"], "Do you understand the message?")

    def test_quiz_is_reproducible_with_one_correct_answer(self):
        lesson = self.lessons[0]
        question = create_question(lesson, 1, seed=20261101)
        self.assertEqual(question, create_question(lesson, 1, seed=20261101))
        self.assertEqual(len(question["options"]), 4)
        self.assertEqual(len(set(question["options"].values())), 4)
        correct = next(k for k, v in question["options"].items() if v == lesson["turns"][0]["english"])
        self.assertTrue(check_answer(question, correct))
        for bad in set("ABCD") - {correct}:
            self.assertFalse(check_answer(question, bad))

    def test_reject_invalid_or_unsupported_quiz_inputs(self):
        with self.assertRaises(VekaError):
            create_question(self.lessons[0], 0)
        with self.assertRaises(VekaError):
            create_question(self.lessons[0], 5)
        with self.assertRaises(VekaError):
            check_answer(create_question(self.lessons[0], 1), "E")

    def test_reject_duplicated_ids_and_invalid_canonical_grammar(self):
        source = json.loads((ROOT / "data/beginner_dialogues_v01.json").read_text(encoding="utf-8"))
        source["lessons"][1]["id"] = "B01"
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "bad.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaises(VekaError):
                load_lessons(path)
            source["lessons"][1]["id"] = "B02"
            source["lessons"][0]["turns"][0]["veka"] = "Mi unknownword."
            path.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaises(VekaError):
                load_lessons(path)

    def test_cli_lists_lessons_and_hides_quiz_answer_until_submitted(self):
        def run(*args):
            return subprocess.run([sys.executable, "-m", "veka", "learn", *args],
                                  cwd=ROOT, capture_output=True, text=True)
        listing = run("list")
        self.assertEqual(listing.returncode, 0, listing.stderr)
        self.assertEqual(len(json.loads(listing.stdout)["lessons"]), 25)
        quiz = run("quiz", "B01", "--question", "1", "--seed", "6")
        self.assertEqual(quiz.returncode, 0, quiz.stderr)
        prompt = json.loads(quiz.stdout)
        self.assertNotIn("correct", prompt)
        self.assertNotIn("answer", prompt)
        self.assertEqual(prompt["veka"], "Ti sen mel ke?")
        invalid = run("quiz", "B99")
        self.assertNotEqual(invalid.returncode, 0)


if __name__ == "__main__":
    unittest.main()
