"""Deterministic learner-focused surface-form audit; NOT a model of real speech."""
from __future__ import annotations

from .core import Lexicon, _syllable_info

# Pedagogical review lists, not accent-wide predictions or difficulty scores.
# The speaker's variety, surrounding vowels and acoustic context matter.
CRITERIA = {
    "en": {"coda": [], "onset": ["r"], "tone": True,
           "review": ("mi", "ti", "ni", "ne", "pa", "fu")},
    "zh": {"coda": ["k", "l", "s"], "onset": ["v", "z", "r"], "tone": False,
           "review": ("mi", "ti", "ni", "ne", "pa", "fu")},
    "pt-BR": {"coda": ["k", "l"], "onset": [], "tone": True,
              "review": ("mi", "ti", "ni", "ne", "pa", "fu")},
}


def audit_learner_forms(lex: Lexicon, *, profile: str = "tonal") -> dict:
    roots = sorted(e.form for e in lex.values() if e.kind == "root")
    groups = {}
    for language, policy in CRITERIA.items():
        categories = {"coda": [], "onset": [], "tone": [], "ti_di": []}
        for form in roots:
            try:
                onset, _, coda, rising = _syllable_info(form)
            except ValueError:
                continue
            if coda in policy["coda"]:
                categories["coda"].append(form)
            if onset in policy["onset"]:
                categories["onset"].append(form)
            if rising and policy["tone"]:
                categories["tone"].append(form)
            if language == "pt-BR" and form in ("ti", "di"):
                categories["ti_di"].append(form)
        groups[language] = {
            "root_count": len(roots),
            "criteria": {"coda": policy["coda"], "onset": policy["onset"],
                         "lexical_tone": policy["tone"],
                         "pt_br_ti_di_accent_variation": language == "pt-BR"},
            "flagged_counts": {k: len(v) for k, v in categories.items()},
            "flagged_roots": categories,
            "review_tokens": [form for form in policy["review"] if form in lex],
        }
    return {
        "schema_version": "veka.learner-audit.v1", "profile": profile,
        "method": "structural screening only", "human_tested": False,
        "groups": groups,
        "warning": ("A flag is a hypothesis for listening tests, not a predicted "
                    "pronunciation error; no speaker or listener results exist."),
        "canonical_vocabulary_changed": False,
    }
