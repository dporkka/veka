"""An evidence-first research backlog, never a lexicon migration."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.international import read_candidates
from veka.lexical_readiness import build_lexical_readiness

ROOT = Path(__file__).resolve().parents[1]


class LexicalReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / 'data/lexicon.csv')
        cls.rows = read_candidates(ROOT / 'data/international_candidates_v04.csv')

    @staticmethod
    def attestation(language, family, branch):
        return {
            'concept_id': 'C002', 'candidate_form': 'mu-si-ka',
            'language': language, 'language_family': family,
            'language_branch': branch, 'attested_form': 'musika',
            'source_url': 'https://example.org/lexicon',
            'semantic_reviewer': 'reviewer-1', 'attestation_verified': 'yes',
            'semantic_equivalent': 'yes', 'notes': 'hypothetical fixture',
        }

    @staticmethod
    def trial(participant, family, condition, *, critical=False):
        return {
            'participant_id': participant, 'language_background_family': family,
            'concept_id': 'C002', 'condition': condition,
            'correct': '0' if critical else '1', 'elapsed_ms': '1500',
            'repair_ms': '500', 'critical_error': '1' if critical else '0',
        }

    def test_empty_dataset_requires_research_and_never_alters_core(self):
        result = build_lexical_readiness(self.rows, self.lex, [], [])
        by_id = {row['concept_id']: row for row in result['candidates']}
        self.assertEqual(result['canonical_changes'], 0)
        self.assertFalse(result['adoption_authorized'])
        self.assertEqual(result['candidate_count'], 100)
        self.assertEqual(by_id['C002']['next_action'], 'verify_cross_family_attestations')
        self.assertEqual(by_id['C002']['added_syllables_vs_core'], 2)
        self.assertEqual(by_id['C009']['next_action'], 'propose_candidate')
        self.assertIsNone(by_id['C009']['added_syllables_vs_core'])
        self.assertEqual(result['counts']['verify_cross_family_attestations'], 8)
        self.assertEqual(result['counts']['propose_candidate'], 92)

    def test_verified_cross_family_data_are_only_a_research_prefilter(self):
        evidence = [self.attestation('Spanish', 'Indo-European', 'Romance'),
                    self.attestation('English', 'Indo-European', 'Germanic'),
                    self.attestation('Swahili', 'Niger-Congo', 'Bantu')]
        result = build_lexical_readiness(self.rows, self.lex, evidence, [])
        music = next(x for x in result['candidates'] if x['concept_id'] == 'C002')
        self.assertEqual(music['verified_families'], 2)  # not three independent languages
        self.assertEqual(music['next_action'], 'collect_balanced_human_trials')
        self.assertFalse(music['human_benefit_established'])

    def test_balanced_observations_still_require_review_and_critical_errors_block(self):
        evidence = [self.attestation('Spanish', 'Indo-European', 'Romance'),
                    self.attestation('Swahili', 'Niger-Congo', 'Bantu')]
        trials = [self.trial('P1', 'Indo-European', 'core'),
                  self.trial('P2', 'Indo-European', 'candidate'),
                  self.trial('P3', 'Niger-Congo', 'core'),
                  self.trial('P4', 'Niger-Congo', 'candidate')]
        result = build_lexical_readiness(self.rows, self.lex, evidence, trials)
        music = next(x for x in result['candidates'] if x['concept_id'] == 'C002')
        self.assertEqual(music['balanced_trial_families'], ['Indo-European', 'Niger-Congo'])
        self.assertEqual(music['next_action'], 'manual_preregistered_review')
        self.assertFalse(result['adoption_authorized'])
        trials[-1] = self.trial('P4', 'Niger-Congo', 'candidate', critical=True)
        blocked = build_lexical_readiness(self.rows, self.lex, evidence, trials)
        music = next(x for x in blocked['candidates'] if x['concept_id'] == 'C002')
        self.assertEqual(music['next_action'], 'investigate_critical_errors')
        self.assertEqual(music['candidate_critical_errors'], 1)

    def test_unbalanced_conditions_do_not_count_as_evidence_of_benefit(self):
        evidence = [self.attestation('Spanish', 'Indo-European', 'Romance'),
                    self.attestation('Swahili', 'Niger-Congo', 'Bantu')]
        trials = [self.trial('P1', 'Indo-European', 'candidate')]
        result = build_lexical_readiness(self.rows, self.lex, evidence, trials)
        music = next(x for x in result['candidates'] if x['concept_id'] == 'C002')
        self.assertEqual(music['next_action'], 'collect_balanced_human_trials')
        self.assertEqual(music['balanced_trial_families'], [])

    def test_unknown_concept_or_unverified_claim_is_not_silently_credited(self):
        trial = self.trial('P1', 'Indo-European', 'core')
        with self.assertRaises(VekaError):
            build_lexical_readiness(self.rows, self.lex, [], [dict(trial, concept_id='C999')])
        unverified = self.attestation('Spanish', 'Indo-European', 'Romance')
        unverified['attestation_verified'] = 'no'
        unverified['semantic_reviewer'] = ''
        result = build_lexical_readiness(self.rows, self.lex, [unverified], [])
        music = next(x for x in result['candidates'] if x['concept_id'] == 'C002')
        self.assertEqual(music['verified_families'], 0)
        self.assertEqual(music['pending_attestation_reviews'], 1)

    def test_cli_defaults_are_noncanonical_and_machine_readable(self):
        process = subprocess.run([sys.executable, '-m', 'veka', 'lexical-readiness'],
                                 cwd=ROOT, capture_output=True, text=True, check=True)
        report = json.loads(process.stdout)
        self.assertEqual(report['schema_version'], 'veka.lexical-readiness.v09')
        self.assertFalse(report['adoption_authorized'])
        self.assertEqual(report['counts']['verify_cross_family_attestations'], 8)


if __name__ == '__main__':
    unittest.main()
