"""Regression tests for multilingual learning aids and hypothesis-only learner audit."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.international import read_candidates
from veka.profiles import load_profile
from veka.beginner import guide_sentence, format_beginner_guide

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = read_candidates(ROOT / "data/international_candidates_v04.csv")


class TrilingualBeginnerTests(unittest.TestCase):
    def setUp(self):
        self.lex = load_profile("tonal")

    def test_glossary_stays_consistent_with_canonical_glosses(self):
        from veka.learner_locales import WORDS
        from veka.beginner import _gloss
        for form, (english, _, _) in WORDS.items():
            with self.subTest(form=form):
                self.assertEqual(_gloss(form, "", self.lex), english)

    def test_chinese_full_glosses_and_unchanged_parse(self):
        guide = guide_sentence("Mi pa dak mel.", self.lex, CANDIDATES, language="zh")
        self.assertEqual(guide["canonical"], "Mi pa dak mel.")
        self.assertEqual(guide["interlinear"], "Mi [我] pa [过去] dak [发送] mel [消息].")
        self.assertEqual(guide["language_of_glosses"], "zh")
        self.assertEqual(guide["gloss_coverage"], {"localized": 4, "english_fallback": 0})
        self.assertEqual(guide["structure"]["predicate"], "dak")
        self.assertFalse(guide["translated"])
        self.assertFalse(guide["canonical_vocabulary_changed"])
        self.assertIn("中文", format_beginner_guide(guide))

    def test_portuguese_full_glosses(self):
        guide = guide_sentence("Mi pa dak mel.", self.lex, CANDIDATES, language="pt-BR")
        self.assertEqual(guide["interlinear"], "Mi [eu/mim] pa [passado] dak [enviar] mel [mensagem].")
        self.assertEqual([w["gloss_language"] for w in guide["words"]], ["pt-BR"] * 4)
        self.assertIn("Português (Brasil)", format_beginner_guide(guide))

    def test_uncovered_words_never_disguise_english_as_chinese(self):
        guide = guide_sentence("Mi pa dak mel.", self.lex, CANDIDATES, language="zh")
        self.assertNotIn("[en]", guide["interlinear"])
        # Deliberately make a new/unknown gloss for an otherwise legal lexeme.
        entry = self.lex["dak"]
        self.lex["dak"] = type(entry)(entry.form, "made-up-untranslated",
            entry.pos, entry.kind, entry.domain, entry.head, entry.modifier, entry.valency)
        guide = guide_sentence("Mi pa dak mel.", self.lex, CANDIDATES, language="zh", include_cues=False)
        self.assertIn("dak [made-up-untranslated (en)]", guide["interlinear"])
        self.assertEqual(guide["gloss_coverage"]["english_fallback"], 1)

    def test_compounds_and_number_roles_are_localized(self):
        compound = guide_sentence("Ren-sak pa gos.", self.lex, CANDIDATES, language="pt-BR")
        self.assertIn("Ren-sak [pessoa + conhecedor]", compound["interlinear"])
        self.assertTrue(compound["words"][0]["silent_hyphen"])
        number = guide_sentence("Mi lin wen wen ran.", self.lex, CANDIDATES, language="zh")
        self.assertIn("wen [数字] wen [精确数字标记] ran [数字1]", number["interlinear"])

    def test_locale_selection_and_default_backward_compatibility(self):
        baseline = guide_sentence("Mi pa dak mel.", self.lex, CANDIDATES)
        self.assertEqual(baseline["interlinear"], "Mi [I/me] pa [past] dak [send] mel [message].")
        for unsupported in ("pt", "zh-CN", "fr", "", "en-US"):
            with self.subTest(unsupported=unsupported), self.assertRaises(VekaError):
                guide_sentence("Mi pa dak mel.", self.lex, CANDIDATES, language=unsupported)

    def test_cli_json_and_text(self):
        for lang, value in [("zh", "我"), ("pt-BR", "eu/mim")]:
            args = [sys.executable, "-m", "veka", "beginner", "Mi pa dak mel.", "--lang", lang]
            text = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(text.returncode, 0, text.stderr)
            self.assertIn(value, text.stdout)
            result = subprocess.run(args + ["--format", "json"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["language_of_glosses"], lang)


class LearnerAuditTests(unittest.TestCase):
    def test_language_specific_structural_counts_are_not_claimed_as_measured(self):
        from veka.learner_audit import audit_learner_forms
        result = audit_learner_forms(load_profile("tonal"))
        self.assertEqual(set(result["groups"]), {"en", "zh", "pt-BR"})
        self.assertFalse(result["human_tested"])
        self.assertEqual(result["method"], "structural screening only")
        self.assertEqual(result["groups"]["zh"]["criteria"]["coda"], ["k", "l", "s"])
        self.assertIn("ti", result["groups"]["pt-BR"]["review_tokens"])
        self.assertIn("ne", result["groups"]["zh"]["review_tokens"])
        self.assertGreater(result["groups"]["zh"]["root_count"], 0)

    def test_learner_audit_cli_json_profile(self):
        p = subprocess.run([sys.executable, "-m", "veka", "learner-audit", "--profile", "toneless"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)
        self.assertEqual(result["profile"], "toneless")
        self.assertFalse(result["human_tested"])


class ProgressiveLessonsTests(unittest.TestCase):
    def test_all_learner_lessons_are_canonical_and_translated_editorially(self):
        from veka.lessons import build_lessons
        for lang in ("en", "zh", "pt-BR"):
            packet = build_lessons(lang)
            self.assertEqual(packet["language"], lang)
            self.assertGreaterEqual(len(packet["lessons"]), 8)
            self.assertFalse(packet["human_comprehension_tested"])
            self.assertEqual(packet["canonical_vocabulary_changed"], False)
            for lesson in packet["lessons"]:
                self.assertTrue(lesson["guide"]["grammar_validated"])
                self.assertFalse(lesson["guide"]["translated"])
                self.assertEqual(lesson["guide"]["experimental_cues"], [])
                self.assertTrue(lesson["editorial_translation"])
                self.assertEqual(lesson["guide"]["canonical"], lesson["sentence"])

    def test_lesson_instructions_are_localized_not_only_glosses(self):
        from veka.lessons import build_lessons, format_lessons
        chinese = build_lessons("zh")
        portuguese = build_lessons("pt-BR")
        self.assertIn("学习重点", format_lessons(chinese))
        self.assertIn("Foco", format_lessons(portuguese))
        self.assertIn("过去", chinese["lessons"][2]["focus"])
        self.assertIn("passado", portuguese["lessons"][2]["focus"])

    def test_lesson_cli_runs_without_unverified_cues(self):
        p = subprocess.run([sys.executable, "-m", "veka", "lessons", "--lang", "pt-BR",
                            "--format", "json"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        body = json.loads(p.stdout)
        self.assertEqual(body["language"], "pt-BR")
        self.assertIn("Eu enviei uma mensagem.", [
            v["editorial_translation"] for v in body["lessons"]
        ])


if __name__ == "__main__":
    unittest.main()
