"""Opt-in, interpretable Veka spoken-aesthetics heuristics.

Not acoustic, perceptual, aesthetic, phoneme-duration or comprehension evidence.
Never rewrite canonical forms, drop consonants, or alter lexical tone.
"""
from __future__ import annotations

from .core import Lexicon, VekaError, _syllable_info, syllabify, parse
from .phonology import CRITICAL_OPERATORS, edit_distance
from .numbers import DIGITS

SONORANT_ONSETS = frozenset('mnlryw')
STOP_ONSETS = frozenset('pbtdkg')
OBSTRUENT_CODAS = frozenset('sk')
VALID_PROFILES = frozenset(('tonal', 'toneless'))


def score_form(form: str) -> dict:
    """Score legal Veka root or hyphenated compound spelling, structurally.

    This is an arbitrary, documented ranking heuristic, NOT a beauty rating.
    End consonants and contrasts must always be pronounced.
    """
    try:
        segments = syllabify(form)
        parsed = [_syllable_info(s) for s in segments]
    except (TypeError, ValueError) as exc:
        raise VekaError(f'invalid Veka form for aesthetics: {form!r}') from exc
    count = len(parsed)
    open_fraction = sum(not c for _, _, c, _ in parsed) / count
    sonorant_coda_fraction = sum(c in ('', 'n', 'l') for _, _, c, _ in parsed) / count
    sonorant_onset_fraction = sum(o in SONORANT_ONSETS for o, _, _, _ in parsed) / count
    vowel_diversity = len({n for _, n, _, _ in parsed}) / count
    hard_coda_fraction = sum(c in OBSTRUENT_CODAS for _, _, c, _ in parsed) / count
    difficult_boundaries = sum(
        c in OBSTRUENT_CODAS and next_o in STOP_ONSETS
        for (_, _, c, _), (next_o, _, _, _) in zip(parsed, parsed[1:])
    )
    # Fixed transparent weights: favor open syllables and sonorants,
    # penalize articulatory stop sequences. No claims of correlation with taste.
    raw = (35 + 25 * open_fraction + 15 * sonorant_coda_fraction
           + 12 * sonorant_onset_fraction + 8 * vowel_diversity
           - 8 * hard_coda_fraction - 10 * difficult_boundaries)
    return {
        'form': form,
        'score': round(max(0.0, min(100.0, raw)), 2),
        'syllables': count,
        'open_syllable_fraction': round(open_fraction, 4),
        'sonorant_coda_fraction': round(sonorant_coda_fraction, 4),
        'sonorant_onset_fraction': round(sonorant_onset_fraction, 4),
        'vowel_diversity_fraction': round(vowel_diversity, 4),
        'hard_coda_fraction': round(hard_coda_fraction, 4),
        'difficult_consonant_boundaries': difficult_boundaries,
        'empirically_validated': False,
    }


def rank_candidates(forms: list[str], lexicon: Lexicon) -> list[dict]:
    """Sort proposed WORD forms while checking similarity to established words.

    Safety screening uses literal spelling edit distance, not an acoustic metric.
    No existing words or their meanings are changed.
    """
    if not forms:
        raise VekaError('supply at least one candidate form')
    if len(forms) > 100:
        raise VekaError('candidate limit is 100')
    if any(not isinstance(f, str) for f in forms):
        raise VekaError('candidate forms must be strings')
    headwords = tuple(lexicon)
    critical = set(CRITICAL_OPERATORS) | set(DIGITS)
    results = []
    for form in dict.fromkeys(forms):
        if not form or form != form.lower():
            raise VekaError('candidate forms must be lowercase Veka romanization')
        assessment = score_form(form)
        existing = form in lexicon
        nearest = min(edit_distance(form, w) for w in headwords)
        critical_distance = min(edit_distance(form, w) for w in critical)
        # A conservative exclusion only, not a guarantee of intelligibility.
        # Hyphens are silent: an apparent compound may have the same audio
        # as two neighboring independent words. Defer to compound review.
        segmentation_review = '-' in form
        eligible = (not existing and nearest >= 2 and critical_distance >= 2
                    and not segmentation_review)
        warnings = []
        if existing:
            warnings.append('already assigned to an existing lexical meaning')
        if nearest < 2:
            warnings.append('identical or one spelling edit from a headword')
        if critical_distance < 2:
            warnings.append('identical or one spelling edit from a critical marker/digit')
        if segmentation_review:
            warnings.append('silent hyphen requires separate spoken segmentation review')
        assessment.update({
            'existing_headword': existing,
            'nearest_headword_edit_distance': nearest,
            'critical_marker_distance': critical_distance,
            'requires_spoken_segmentation_review': segmentation_review,
            'eligible_new_word': eligible,
            'screening_warnings': warnings,
            'lexical_collision_free_is_acoustic_evidence': False,
        })
        results.append(assessment)
    results.sort(key=lambda x: (not x['eligible_new_word'], -x['score'],
                                -x['nearest_headword_edit_distance'], x['form']))
    return results


def prosody_guidance(spoken_text: str, lexicon: Lexicon, *, profile: str = 'tonal') -> dict:
    """Return a non-rendering delivery guide only for parseable Veka.

    This is advice for human recording, not a sentence-to-speech synthesizer.
    Pitch must not override contrastive lexical tone in the tonal condition.
    """
    if profile not in VALID_PROFILES:
        raise VekaError(f'unknown spoken profile: {profile}')
    if not isinstance(spoken_text, str) or not spoken_text.strip():
        raise VekaError('spoken_text must be a nonempty Veka sentence')
    if spoken_text.rstrip().endswith('?'):
        raise VekaError('Veka 0.4 does not define interrogative semantics')
    # Fail closed: prose advice must not legitimize syntactically unknown text.
    try:
        parse(spoken_text, lexicon, strict=True)
    except VekaError as atomic_error:
        from .logic import parse_logic
        try:
            parse_logic(spoken_text, lexicon, strict=True)
        except VekaError as logic_error:
            raise VekaError(
                f'prosody requires a strict parseable clause: '
                f'{atomic_error}; logical parse: {logic_error}'
            ) from logic_error
    tonal = profile == 'tonal'
    return {
        'spoken_text': spoken_text,
        'profile': profile,
        'cadence': ('phrase-final soft fall subordinate to lexical tones' if tonal
                    else 'gentle phrase-final fall'),
        'preserve_lexical_tone': tonal,
        'delivery': 'mostly even syllable pacing; gentle phrase-level prominence',
        'consonants': 'pronounce every licensed onset and coda clearly',
        'vowels': 'maintain distinct a/e/i/o/u without neutralization',
        'scope_and_numbers': 'preserve pauses only where they cannot change logical scope; articulate markers and digits',
        'changes_to_canonical_wording': False,
        'audio_generated': False,
        'empirically_validated': False,
    }
