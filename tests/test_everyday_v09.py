"""Everyday communication requirements and beginner curriculum contracts."""
import json
import subprocess
import sys
import unittest

from veka.core import VekaError
from veka.registers import inspect_register
from veka.everyday import load_dialogues, audit_dialogues, get_lesson, load_lessons


class EverydayCorpusTests(unittest.TestCase):
    def test_100_distinct_two_turn_dialogues_in_ten_domains(self):
        rows = load_dialogues()
        self.assertEqual(len(rows), 100)
        self.assertEqual(len({r['id'] for r in rows}), 100)
        self.assertEqual(len({r['scenario'] for r in rows}), 100)
        domains = {r['domain'] for r in rows}
        self.assertEqual(len(domains), 10)
        for domain in domains:
            self.assertEqual(sum(r['domain'] == domain for r in rows), 10)
        for row in rows:
            self.assertEqual([turn['speaker'] for turn in row['turns']], ['A', 'B'])
            self.assertTrue(all(turn['text'].strip() for turn in row['turns']))
            self.assertTrue(row['required_features'])
            self.assertEqual(row['translation_status'], 'not_attempted')
            self.assertNotIn('veka', row)

    def test_audit_discloses_untranslated_requirements_not_coverage_claims(self):
        result = audit_dialogues()
        self.assertEqual(result['total_scenarios'], 100)
        self.assertEqual(result['not_attempted'], 100)
        self.assertEqual(result['machine_translations_verified'], 0)
        self.assertFalse(result['human_comprehension_validated'])
        self.assertEqual(len(result['domains']), 10)
        self.assertGreater(len(result['required_feature_counts']), 5)

    def test_filter_domain_retains_only_matching_requirements(self):
        result = audit_dialogues(domain='clarification', include_items=True)
        self.assertEqual(result['total_scenarios'], 10)
        self.assertTrue(all(row['domain'] == 'clarification' for row in result['items']))
        with self.assertRaises(VekaError):
            audit_dialogues(domain='not-a-domain')

    def test_invalid_corpus_fails_closed(self):
        rows = load_dialogues()
        broken = [dict(r) for r in rows]
        broken[0]['id'] = broken[1]['id']
        with self.assertRaises(VekaError):
            audit_dialogues(rows=broken)
        broken = [dict(r) for r in rows]
        broken[0]['translation_status'] = 'validated'
        with self.assertRaises(VekaError):
            audit_dialogues(rows=broken)


class BeginnerLessonTests(unittest.TestCase):
    def test_lesson_examples_are_real_parser_accepted_canonical_sentences(self):
        lessons = load_lessons()
        self.assertEqual([l['level'] for l in lessons], [1, 2, 3, 4])
        for lesson in lessons:
            self.assertGreaterEqual(len(lesson['examples']), 3)
            for example in lesson['examples']:
                parsed = inspect_register(example['veka'], max_register='core')
                self.assertEqual(parsed['register'], 'core')
                self.assertFalse(parsed['human_comprehension_validated'])
                self.assertTrue(example['english'].strip())

    def test_levels_and_invalid_level(self):
        lesson = get_lesson(2)
        self.assertEqual(lesson['level'], 2)
        self.assertEqual(lesson['profile'], 'tonal')
        self.assertFalse(lesson['human_learning_validated'])
        self.assertEqual(lesson['grammar_register'], 'core')
        with self.assertRaises(VekaError):
            get_lesson(20)

    def test_cli_lesson_and_dialogue_audit_return_honest_json(self):
        for args, field, expected in (
            (['learn', '--level', '1'], 'level', 1),
            (['everyday-audit', '--domain', 'clarification'], 'total_scenarios', 10),
        ):
            with self.subTest(args=args):
                proc = subprocess.run([sys.executable, '-m', 'veka', *args],
                                      capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(json.loads(proc.stdout)[field], expected)
        invalid = subprocess.run([sys.executable, '-m', 'veka', 'learn', '--level', '8'],
                                 capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertIn('VEKA ERROR:', invalid.stderr)


if __name__ == '__main__':
    unittest.main()
