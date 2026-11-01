"""Aesthetic-listening manifest contracts: no invented audio or listener data."""
import csv
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.spoken_study import generate_spoken_manifest, write_spoken_manifest

ROOT = Path(__file__).resolve().parents[1]
ITEMS = json.loads((ROOT / 'data/spoken_aesthetics_items_v05.json').read_text())['items']


class SpokenManifestTests(unittest.TestCase):
    def test_each_participant_gets_one_condition_per_meaning(self):
        participant, key = generate_spoken_manifest(ITEMS, 'S01', 'tonal', 0)
        self.assertEqual(len(participant), len(ITEMS))
        self.assertEqual(len(key), len(ITEMS))
        self.assertEqual(len({r['item_id'] for r in key}), len(ITEMS))
        self.assertEqual(sum(r['delivery']=='guided' for r in key), len(ITEMS)//2)
        self.assertEqual(sum(r['delivery']=='baseline' for r in key), len(ITEMS)//2)
        self.assertTrue(all(r['profile']=='tonal' for r in key))
        self.assertTrue(all(r['audio_recorded']=='false' for r in key))

    def test_opposite_arms_reverse_delivery_for_each_item(self):
        _, left = generate_spoken_manifest(ITEMS, 'S01', 'toneless', 0)
        _, right = generate_spoken_manifest(ITEMS, 'S02', 'toneless', 1)
        left = {r['item_id']:r['delivery'] for r in left}
        right = {r['item_id']:r['delivery'] for r in right}
        self.assertEqual(set(left), set(right))
        self.assertTrue(all(left[k]!=right[k] for k in left))

    def test_randomization_is_reproducible_and_ids_are_unique(self):
        a = generate_spoken_manifest(ITEMS, 'S01', 'tonal', 0, seed=123)
        b = generate_spoken_manifest(ITEMS, 'S01', 'tonal', 0, seed=123)
        self.assertEqual(a,b)
        self.assertEqual(len({r['stimulus_id'] for r in a[0]}), len(ITEMS))

    def test_participant_sheet_does_not_reveal_text_meaning_or_conditions(self):
        participant, key = generate_spoken_manifest(ITEMS, 'S01', 'tonal', 0)
        self.assertNotIn('meaning', participant[0])
        self.assertNotIn('profile', participant[0])
        self.assertNotIn('delivery', participant[0])
        self.assertNotIn('utterance', participant[0])
        self.assertEqual(participant[0]['pleasantness_1_7'], '')
        self.assertEqual(participant[0]['comprehension_response'], '')
        self.assertIn('meaning',key[0])
        self.assertIn('utterance',key[0])

    def test_invalid_conditions_and_syntax_fail_closed(self):
        for profile,arm in [('toneless',2),('invalid',0),('tonal',True)]:
            with self.subTest(profile=profile, arm=arm), self.assertRaises(VekaError):
                generate_spoken_manifest(ITEMS, 'S01',profile,arm)
        with self.assertRaises(VekaError):
            generate_spoken_manifest(ITEMS, '', 'tonal', 0)
        with self.assertRaises(VekaError):
            generate_spoken_manifest(ITEMS+[dict(ITEMS[0])], 'S01', 'tonal', 0)
        bad = [dict(row) for row in ITEMS]
        bad[0]['tonal']='Mi ne.'
        with self.assertRaises(VekaError):
            generate_spoken_manifest(bad,'S01','tonal',0)

    def test_uses_correct_profile_lexical_variants(self):
        _, tonal = generate_spoken_manifest(ITEMS,'S01','tonal',0)
        _, toneless = generate_spoken_manifest(ITEMS,'S01','toneless',0)
        d={r['item_id']:r['utterance'] for r in tonal}
        e={r['item_id']:r['utterance'] for r in toneless}
        self.assertEqual(d['remember'],'Mi pái mel.')
        self.assertEqual(e['remember'],'Mi fok mel.')

    def test_never_overwrites_existing_study_files(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)/'participant.csv'
            key = Path(d)/'researcher.csv'
            result = write_spoken_manifest(ITEMS,'S01','tonal',0,out,key)
            self.assertFalse(result['audio_recorded'])
            self.assertFalse(result['human_data_collected'])
            if os.name == 'posix':
                self.assertEqual(stat.S_IMODE(key.stat().st_mode), 0o600)
            with out.open(newline='') as f:
                self.assertEqual(len(list(csv.DictReader(f))),len(ITEMS))
            with self.assertRaises(VekaError):
                write_spoken_manifest(ITEMS,'S01','tonal',0,out,key)
            with self.assertRaises(VekaError):
                write_spoken_manifest(ITEMS,'S01','tonal',0,key,key)


if __name__ == '__main__':
    unittest.main()
