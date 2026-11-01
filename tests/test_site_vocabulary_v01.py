"""Guard progressive root preview against double-counting and unreviewed claims."""
import unittest

from veka.site_glosses import build_site_glosses
from veka.profiles import load_profile


class SiteVocabularyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = build_site_glosses()

    def test_every_lesson_previews_unseen_and_seen_canonical_roots(self):
        seen = set()
        lex = load_profile('tonal')
        for lesson in self.packet['lessons']:
            vocabulary = lesson['vocabulary']
            new = vocabulary['new_roots']
            review = vocabulary['review_roots']
            new_forms = new
            review_forms = review
            self.assertEqual(len(set(new_forms + review_forms)), len(new_forms + review_forms))
            self.assertFalse(set(new_forms) & seen, lesson['id'])
            self.assertTrue(set(review_forms).issubset(seen), lesson['id'])
            for form in new + review:
                item = self.packet['root_glosses'][form]
                self.assertEqual(item['kind'], 'canonical_root')
                self.assertEqual(lex[form].kind, 'root')
                self.assertEqual(set(item['glosses']), {'en', 'zh', 'pt-BR'})
                for language in self.packet['languages']:
                    gloss = item['glosses'][language]
                    self.assertTrue(gloss['gloss'])
                    self.assertIn(gloss['gloss_language'], ('en', language))
                    if language != 'en' and gloss['gloss_language'] == 'en':
                        self.assertTrue(gloss['gloss'].endswith(' (en)'))
            self.assertEqual(vocabulary['root_count'], len(new) + len(review))
            seen.update(new_forms)
        self.assertEqual(len(seen), 89)
        self.assertEqual(set(self.packet['root_glosses']), seen)
        self.assertFalse(self.packet['human_comprehension_validated'])
        self.assertFalse(self.packet['canonical_vocabulary_changed'])

    def test_first_lesson_is_all_new_later_lesson_reuses_pronouns(self):
        first, second = self.packet['lessons'][:2]
        first_new = set(first['vocabulary']['new_roots'])
        second_review = set(second['vocabulary']['review_roots'])
        self.assertIn('ti', first_new)
        self.assertIn('mi', first_new)
        self.assertEqual(first['vocabulary']['review_roots'], [])
        self.assertTrue({'ti', 'mi', 'fu'}.issubset(second_review))

    def test_untranslated_words_are_labeled_fallbacks(self):
        fallback = self.packet['root_glosses']['fos']
        self.assertEqual(fallback['glosses']['zh']['gloss_language'], 'en')
        self.assertTrue(fallback['glosses']['zh']['gloss'].endswith('(en)'))

    def test_static_page_includes_accessible_vocabulary_preview(self):
        from pathlib import Path
        page = (Path(__file__).resolve().parents[1] / 'site/index.html').read_text(encoding='utf8')
        self.assertIn('id="vocab-preview"', page)
        self.assertIn('id="vocab-new"', page)
        self.assertIn('id="vocab-review"', page)
        self.assertIn('vocabulary.new_roots', page)
        self.assertIn('vocabulary.review_roots', page)
        self.assertIn('textContent', page)
        self.assertNotIn('innerHTML', page)


if __name__ == '__main__':
    unittest.main()
