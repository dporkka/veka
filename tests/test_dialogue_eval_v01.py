"""Audit proposed everyday dialogue utterances without certifying translation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from veka.core import VekaError
from veka.dialogue_eval import evaluate_attempts

SCHEMA = "veka.dialogue-attempts.v01"


def packet(*turns, scenario="ED-001"):
    return {"schema_version": SCHEMA, "attempts": [
        {"id": scenario, "turns": list(turns)}]}


def turn(speaker, veka, act):
    return {"speaker": speaker, "veka": veka, "intended_act": act}


class DialogueEvaluationTests(unittest.TestCase):
    def test_case_sensitive_extended_question_and_independent_semantic_gate(self):
        source = packet(
            turn("A", "Hon-ren pa gos.", "content_question"),
            turn("B", "Mi pa gos.", "statement"),
        )
        result = evaluate_attempts(source, max_register="research")
        self.assertEqual(result["total_scenarios"], 100)
        self.assertEqual(result["attempted_scenarios"], 1)
        self.assertEqual(result["unattempted_scenarios"], 99)
        self.assertEqual(result["syntax_accepted_turns"], 2)
        self.assertEqual(result["speech_act_aligned_turns"], 2)
        self.assertEqual(result["ready_for_semantic_review"], 1)
        self.assertEqual(result["verified_translations"], 0)
        self.assertFalse(result["human_comprehension_validated"])
        sample = result["attempts"][0]
        self.assertFalse(sample["meaning_equivalence_verified"])
        self.assertEqual(sample["turns"][0]["grammar_register"], "research")
        self.assertEqual(sample["turns"][0]["observed_act"], "content_question")

    def test_intended_speech_act_disagreement_blocks_readiness(self):
        source = packet(turn("A", "Mi gos.", "content_question"),
                        turn("B", "Mi pa gos.", "statement"))
        result = evaluate_attempts(source)
        self.assertEqual(result["syntax_accepted_turns"], 2)
        self.assertEqual(result["speech_act_aligned_turns"], 1)
        self.assertEqual(result["ready_for_semantic_review"], 0)
        self.assertEqual(result["attempts"][0]["turns"][0]["observed_act"], "statement")

    def test_research_syntax_not_silently_promoted_into_core(self):
        source = packet(turn("A", "Hon-ren pa gos.", "content_question"),
                        turn("B", "Mi pa gos.", "statement"))
        result = evaluate_attempts(source, max_register="core")
        self.assertEqual(result["syntax_accepted_turns"], 1)
        self.assertEqual(result["ready_for_semantic_review"], 0)
        self.assertFalse(result["attempts"][0]["turns"][0]["syntax_accepted"])

    def test_reject_unknown_duplicate_or_invalid_attempts(self):
        basic = [turn("A", "Mi gos.", "statement"),
                 turn("B", "Ti gos.", "statement")]
        for invalid in (
            packet(*basic, scenario="ED-999"),
            {"schema_version": SCHEMA, "attempts": [
                {"id": "ED-001", "turns": basic}, {"id": "ED-001", "turns": basic}]},
            packet(turn("B", "Mi gos.", "statement"), basic[1]),
            packet(turn("A", "Mi gos.", "unknown"), basic[1]),
            packet(turn("A", "Mi gos.", []), basic[1]),
            {"schema_version": SCHEMA, "attempts": [{"id": ["ED-001"], "turns": basic}]},
            packet(turn("A", "Mi gos.", "statement"), turn("B", "", "statement")),
            packet(turn("A", "Mi gos.", "statement"), basic[1], scenario="ED-000"),
            {"schema_version": SCHEMA, "attempts": [
                {"id": "ED-001", "turns": basic, "translation_status": "validated"}]},
        ):
            with self.subTest(source=invalid), self.assertRaises(VekaError):
                evaluate_attempts(invalid)
        with self.assertRaises(VekaError):
            evaluate_attempts(packet(*basic), max_register="invalid")

    def test_cli_accepts_external_attempt_file(self):
        source = packet(turn("A", "Mi gos.", "statement"),
                        turn("B", "Ti gos.", "statement"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "attempts.json"
            path.write_text(json.dumps(source), encoding="utf8")
            proc = subprocess.run(
                [sys.executable, "-m", "veka", "dialogue-check",
                 "--attempts", str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["ready_for_semantic_review"], 1)


if __name__ == "__main__":
    unittest.main()
