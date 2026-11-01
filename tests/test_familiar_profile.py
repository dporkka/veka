import unittest
from dataclasses import replace
from unittest.mock import patch

from veka.core import VekaError, parse
from veka.familiar import REPLACEMENTS, convert, familiar_lexicon, parse_familiar
from veka.profiles import load_profile


class FamiliarProfileTests(unittest.TestCase):
    def test_lexicon_preserves_meaning_and_compounds(self):
        old = load_profile('tonal')
        new, mapping = familiar_lexicon()
        self.assertEqual(len(old), len(new))
        self.assertEqual(len(mapping), 43)
        for original, entry in old.items():
            updated = new[mapping.get(original, original)]
            self.assertEqual((entry.gloss, entry.pos, entry.kind, entry.valency),
                             (updated.gloss, updated.pos, updated.kind, updated.valency))
            if entry.kind == 'compound':
                self.assertEqual(updated.head, REPLACEMENTS.get(entry.head, entry.head))
                self.assertEqual(updated.modifier, REPLACEMENTS.get(entry.modifier, entry.modifier))
        surfaces = {}
        for word in new:
            surfaces.setdefault(word.replace('-', ''), []).append(word)
        for word in mapping.values():
            self.assertEqual(surfaces[word.replace('-', '')], [word])

    def test_parser_and_roundtrip(self):
        _, mapping = familiar_lexicon()
        for word in REPLACEMENTS:
            forms = [word] + [old for old in mapping if old.startswith(word + '-')]
            for old in forms:
                source = 'Mi sen ' + old + '.'
                updated = convert(source, 'to-familiar')
                self.assertEqual(convert(updated, 'to-core'), source)
                a, b = parse(source, load_profile('tonal'), strict=True), parse_familiar(updated)
                self.assertEqual(b.pop('object'), mapping[old])
                a.pop('object')
                self.assertEqual(a, b)
                with self.assertRaises(VekaError): parse_familiar(source)
        self.assertEqual(convert('Woi, woi-val!', 'to-familiar'), 'Mu-si-ka, mu-si-ka-val!')

    def test_teaching_examples_parse_and_reject_mixed_profile(self):
        for sentence in ('Mi rin dok-ta.', 'Mi lin ka-me-ra.', 'Mi pa vo bu-ku.'):
            self.assertFalse(parse_familiar(sentence)['compressed'])
        with self.assertRaises(VekaError):
            parse_familiar('Mi rin hek.')
        with self.assertRaises(VekaError):
            parse_familiar('Mi rin Hek.')

    def test_collision_fails_closed(self):
        with patch.dict(REPLACEMENTS, {'woi': 'vik'}):
            with self.assertRaises(VekaError): familiar_lexicon()


if __name__ == '__main__': unittest.main()
