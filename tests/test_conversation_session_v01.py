"""Offline conversation sessions require researcher-authored, blinded stimuli."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.conversation_session import (
    SESSION_VERSION, MANIFEST_FIELDS, read_conversation_manifest,
    write_conversation_session,
)

ROOT = Path(__file__).resolve().parents[1]


class ConversationSessionTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            dict(participant_id='S001', trial_id='D01-1111111111111111',
                 scenario_id='ED-083', language='veka',
                 context='Context supplied by an independently reviewed researcher',
                 utterance='An independently reviewed Veka utterance'),
            dict(participant_id='S001', trial_id='D01-2222222222222222',
                 scenario_id='ED-067', language='globasa',
                 context='Other carefully checked dialogue context',
                 utterance='Other carefully checked study utterance'),
        ]

    def manifest(self, folder, rows=None):
        path = folder / 'researcher-manifest.csv'
        with path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows if rows is None else rows)
        return path

    def test_researcher_manifest_to_blinded_participant_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self.manifest(Path(tmp))
            out = Path(tmp) / 'participant.json'
            report = write_conversation_session(read_conversation_manifest(source), out)
            session = json.loads(out.read_text(encoding='utf-8'))
            self.assertEqual(session['schema_version'], SESSION_VERSION)
            self.assertEqual(session['participant_id'], 'S001')
            self.assertEqual(len(session['trials']), 2)
            self.assertEqual(set(session['trials'][0]), {'trial_id', 'language', 'context', 'utterance'})
            self.assertEqual([r['trial_id'] for r in session['trials']],
                             [r['trial_id'] for r in self.rows])
            self.assertNotIn('scenario_id', out.read_text())
            self.assertFalse(report['human_data_collected'])
            self.assertFalse(report['stimulus_review_authenticated'])

    def test_bad_researcher_rows_rejected_before_any_output(self):
        for mutation in (
            {'trial_id': 'ED-083'}, {'language': 'unknown'},
            {'scenario_id': 'ED-999'}, {'context': ''}, {'utterance': '=HYPERLINK("evil")'},
            {'participant_id': 'S002'},
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                rows = [dict(r) for r in self.rows]
                rows[-1].update(mutation)
                path = self.manifest(Path(tmp), rows)
                destination = Path(tmp) / 'participant.json'
                with self.assertRaises(VekaError):
                    write_conversation_session(read_conversation_manifest(path), destination)
                self.assertFalse(destination.exists())

    def test_duplicate_scenario_trial_and_truncated_csv_rejected(self):
        for mutation in ({'scenario_id': 'ED-083'}, {'trial_id': 'D01-1111111111111111'}):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                rows = [dict(r) for r in self.rows]
                rows[-1].update(mutation)
                with self.assertRaises(VekaError):
                    read_conversation_manifest(self.manifest(Path(tmp), rows))
        with tempfile.TemporaryDirectory() as tmp:
            path = self.manifest(Path(tmp))
            with path.open('a') as handle:
                handle.write('"unclosed quote\n')
            with self.assertRaises(VekaError):
                read_conversation_manifest(path)

    def test_writer_revalidates_direct_calls_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'session.json'
            write_conversation_session(self.rows, out)
            with self.assertRaises(VekaError):
                write_conversation_session(self.rows, out)
            with self.assertRaises(VekaError):
                write_conversation_session([dict(self.rows[0], correct='1'), self.rows[1]], Path(tmp) / 'bad.json')

    def test_maximal_unicode_session_is_accepted_by_browser_contract(self):
        # 2,000 Unicode code points can exceed 2,000 UTF-16 code units.
        # A 40-trial JSON export may exceed the old 100 KB browser limit.
        rows = []
        for i in range(40):
            rows.append(dict(participant_id='S001', trial_id=f'D01-{i:016x}',
                             scenario_id=f'ED-{i + 1:03d}', language='veka',
                             context='𐐀' * 2000, utterance='𐐀' * 2000))
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'large.json'
            result = write_conversation_session(rows, destination)
            self.assertEqual(result['trials'], 40)
            self.assertGreater(destination.stat().st_size, 100000)
            self.assertLess(destination.stat().st_size, 1048576)
            self.assertEqual(len(json.loads(destination.read_text())['trials']), 40)
        html = (ROOT / 'site/conversation-study.html').read_text(encoding='utf-8')
        self.assertIn('file.size > 1048576', html)
        self.assertIn('Array.from(text).length > 2000', html)

    def test_cli_and_offline_page_do_not_embed_keys_or_external_scripts(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            out = folder / 'session.json'
            result = subprocess.run([sys.executable, '-m', 'veka', 'conversation-session',
                                     '--manifest', str(self.manifest(folder)), '--output', str(out)],
                                    cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)['human_data_collected'])
        html = (ROOT / 'site/conversation-study.html').read_text(encoding='utf-8')
        self.assertIn('id="session-file"', html)
        self.assertIn('id="export-responses"', html)
        self.assertIn('performance.now()', html)
        self.assertIn('timing_interrupted', html)
        self.assertNotIn('target_gloss', html)
        self.assertNotIn('https://cdn.', html)


if __name__ == '__main__':
    unittest.main()
