"""Deterministic, read-only export of curated word glosses for the local learning UI.

The output contains strictly parsed canonical Veka and *word-level* editorial
labels. It is not a translation engine or a claim about human comprehension.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from .beginner import guide_sentence
from .learner_locales import LANGUAGES
from .learning import DEFAULT_LESSONS, load_lessons
from .profiles import load_profile


def build_site_glosses(path: str | Path = DEFAULT_LESSONS) -> dict:
    source = Path(path)
    lessons = load_lessons(source)  # Always validates every canonical turn first.
    lex = load_profile("tonal")
    result = []
    for lesson in lessons:
        turns = []
        for turn in lesson["turns"]:
            glosses = {}
            for language in LANGUAGES:
                guide = guide_sentence(turn["veka"], lex, [], profile="tonal",
                                       language=language, include_cues=False)
                glosses[language] = [
                    {"token": word["token"], "gloss": word["gloss"],
                     "gloss_language": word["gloss_language"]}
                    for word in guide["words"]
                ]
            turns.append({"veka": turn["veka"], "glosses": glosses})
        result.append({"id": lesson["id"], "turns": turns})
    return {
        "schema_version": "veka.site-glosses.v01",
        "canonical_profile": "tonal",
        "canonical_language_version": "0.4",
        "source_sha256": sha256(source.read_bytes()).hexdigest(),
        "languages": list(LANGUAGES),
        "status": "editorial word-level glosses, not validated translations",
        "human_comprehension_validated": False,
        "canonical_vocabulary_changed": False,
        "lessons": result,
    }
