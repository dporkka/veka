"""Active practice must not mutate canonical Veka or pretend to measure fluency."""
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.practice import build_practice, grade_practice, read_practice_responses

ROOT = Path(__file__).resolve().parents[1]


class PracticeTests(unittest.TestCase):
    def test_every_language_and_profile_has_answer_free_recognition_questions(self):
        for language in ("en", "zh", "pt-BR"):
            for profile in ("tonal", "toneless"):
                with self.subTest(language=language, profile=profile):
                    packet = build_practice(language, mode="recognition",
                                            profile=profile, seed=17)
                    self.assertEqual(packet["schema_version"], "veka.practice.v11")
                    self.assertEqual(len(packet["questions"]), 10)
                    self.assertEqual(len({q["question_id"] for q in packet["questions"]}), 10)
                    self.assertFalse(packet["human_comprehension_validated"])
                    self.assertFalse(packet["canonical_vocabulary_changed"])
                    for question in packet["questions"]:
                        self.assertNotIn("answer", question)
                        self.assertNotIn("correct", question)
                        self.assertNotIn("editorial_translation", question)
                        self.assertEqual(len(question["choices"]), 3)
                        self.assertEqual(set(question["choices"]), {"A", "B", "C"})
                        self.assertEqual(len(set(question["choices"].values())), 3)
                        self.assertIn("prompt", question)
                        self.assertNotIn("guide", question)

    def test_recall_has_no_solutions_and_uses_taught_editorial_readings(self):
        packet = build_practice("pt-BR", mode="recall", seed=23)
        self.assertEqual(len(packet["questions"]), 10)
        self.assertTrue(any(q["prompt"] == "Eu enviei uma mensagem."
                            for q in packet["questions"]))
        for question in packet["questions"]:
            self.assertEqual(set(question), {"question_id", "prompt"})
            self.assertNotIn("Mi pa dak mel.", question.values())

    def test_same_seed_same_packet_and_new_seed_changes_order(self):
        first = build_practice("en", mode="recognition", seed=17, count=5)
        self.assertEqual(first, build_practice("en", mode="recognition", seed=17, count=5))
        second = build_practice("en", mode="recognition", seed=18, count=5)
        self.assertNotEqual(first["questions"], second["questions"])

    def test_grade_recognition_using_only_participant_choice(self):
        packet = build_practice("en", mode="recognition", seed=17)
        question = next(q for q in packet["questions"] if q["question_id"] == "L03")
        right = next(label for label, meaning in question["choices"].items()
                     if meaning == "I sent a message.")
        wrong = next(label for label in ("A", "B", "C") if label != right)
        correct = grade_practice([{"question_id": "L03", "response": right}],
                                 "en", mode="recognition", seed=17)
        self.assertEqual(correct["correct"], 1)
        self.assertEqual(correct["unanswered"], 9)
        incorrect = grade_practice([{"question_id": "L03", "response": wrong}],
                                   "en", mode="recognition", seed=17)
        self.assertEqual(incorrect["correct"], 0)
        self.assertEqual(incorrect["feedback"][0]["expected"], right)
        self.assertFalse(incorrect["translation_equivalence_established"])

    def test_recall_checks_taught_surface_only_not_semantic_paraphrases(self):
        correct = grade_practice([{"question_id": "L03", "response": " mi   PA dak mel "}],
                                 "en", mode="recall")
        self.assertEqual(correct["correct"], 1)
        wrong = grade_practice([{"question_id": "L03", "response": "I sent a message."}],
                               "en", mode="recall")
        self.assertEqual(wrong["correct"], 0)
        self.assertEqual(wrong["feedback"][0]["expected"], "Mi pa dak mel.")
        self.assertFalse(wrong["semantic_equivalence_judged"])

    def test_bad_responses_fail_closed(self):
        with self.assertRaises(VekaError):
            grade_practice([{"question_id": "L99", "response": "A"}],
                           "en", mode="recognition")
        with self.assertRaises(VekaError):
            grade_practice([{"question_id": "L03", "response": "A"},
                            {"question_id": "L03", "response": "B"}],
                           "en", mode="recognition")
        with self.assertRaises(VekaError):
            grade_practice([{"question_id": "L03", "response": "D"}],
                           "en", mode="recognition")
        with self.assertRaises(VekaError):
            grade_practice([{"question_id": "L03", "response": "Mi pa dak mel.",
                             "expected": "Mi pa dak mel."}],
                           "en", mode="recall")

    def test_invalid_params_fail_closed(self):
        for kwargs in ({"language": "de"}, {"language": "en", "mode": "study"},
                       {"language": "en", "count": 0},
                       {"language": "en", "count": 11},
                       {"language": "en", "seed": True},
                       {"language": "en", "profile": "other"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(VekaError):
                build_practice(**kwargs)

    def test_response_csv_requires_exact_header_and_no_answer_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "responses.csv"
            p.write_text("question_id,response\nL03,Mi pa dak mel.\n", encoding="utf-8")
            self.assertEqual(read_practice_responses(p),
                             [{"question_id": "L03", "response": "Mi pa dak mel."}])
            p.write_text("question_id,response,expected\nL03,x,y\n", encoding="utf-8")
            with self.assertRaises(VekaError):
                read_practice_responses(p)
            p.write_text("question_id,response\nL03,A,extra\n", encoding="utf-8")
            with self.assertRaises(VekaError):
                read_practice_responses(p)

    def test_cli_json_and_check_roundtrip(self):
        command = [sys.executable, "-m", "veka", "practice", "--lang", "zh",
                   "--mode", "recognition", "--seed", "17", "--format", "json"]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = json.loads(result.stdout)
        self.assertEqual(packet["language"], "zh")
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "responses.csv"
            with f.open("w", newline="", encoding="utf-8") as stream:
                w = csv.DictWriter(stream, fieldnames=("question_id", "response"))
                w.writeheader()
                w.writerow({"question_id": packet["questions"][0]["question_id"],
                            "response": "A"})
            result = subprocess.run([sys.executable, "-m", "veka", "practice-check",
                                     "--responses", str(f), "--lang", "zh",
                                     "--mode", "recognition", "--seed", "17"],
                                    cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["answered"], 1)
            self.assertEqual(report["unanswered"], 9)


if __name__ == "__main__":
    unittest.main()
