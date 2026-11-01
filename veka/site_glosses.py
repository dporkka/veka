"""Deterministic, read-only export of curated word glosses for the local learning UI.

The output contains strictly parsed canonical Veka and *word-level* editorial
labels. It is not a translation engine or a claim about human comprehension.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from .beginner import GRAMMAR_GLOSSES, guide_sentence
from .core import VekaError, _normalize_sentence
from .learner_locales import LANGUAGES, localized_gloss
from .learning import DEFAULT_LESSONS, load_lessons
from .profiles import load_profile


def build_site_glosses(path: str | Path = DEFAULT_LESSONS) -> dict:
    source = Path(path)
    lessons = load_lessons(source)  # Always validates every canonical turn first.
    lex = load_profile("tonal")
    result = []
    introduced_roots: set[str] = set()
    root_glosses = {}

    def describe_root(form: str) -> dict:
        entry = lex[form]
        glosses = {}
        for language in LANGUAGES:
            gloss, actual_language = localized_gloss(
                form, GRAMMAR_GLOSSES.get(form, entry.gloss), language)
            glosses[language] = {"gloss": gloss, "gloss_language": actual_language}
        return {"kind": "canonical_root", "pos": entry.pos, "glosses": glosses}

    for lesson in lessons:
        turns = []
        lesson_roots: list[str] = []
        seen_this_lesson: set[str] = set()
        for turn in lesson["turns"]:
            for token in _normalize_sentence(turn["veka"]):
                entry = lex.get(token.lower())
                if entry is None:
                    raise VekaError(f"beginner vocabulary cannot teach unknown root: {token}")
                if entry.kind == "compound":
                    head, modifier = lex.get(entry.head), lex.get(entry.modifier)
                    if (head is None or modifier is None or head.kind != "root"
                            or modifier.kind != "root" or head.pos != "noun"
                            or modifier.pos != "adjective"
                            or entry.form != f"{entry.head}-{entry.modifier}"):
                        raise VekaError(f"nontransparent beginner compound: {token}")
                    components = (head.form, modifier.form)
                else:
                    components = (entry.form,)
                for form in components:
                    if form not in seen_this_lesson:
                        lesson_roots.append(form)
                        seen_this_lesson.add(form)
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
        for form in lesson_roots:
            if form not in root_glosses:
                root_glosses[form] = describe_root(form)
        new_forms = [form for form in lesson_roots if form not in introduced_roots]
        review_forms = [form for form in lesson_roots if form in introduced_roots]
        result.append({"id": lesson["id"], "turns": turns,
                       "vocabulary": {
                           "root_count": len(lesson_roots),
                           "new_roots": new_forms,
                           "review_roots": review_forms,
                       }})
        introduced_roots.update(lesson_roots)
    return {
        "schema_version": "veka.site-glosses.v01",
        "canonical_profile": "tonal",
        "canonical_language_version": "0.4",
        "source_sha256": sha256(source.read_bytes()).hexdigest(),
        "languages": list(LANGUAGES),
        "root_glosses": root_glosses,
        "status": "editorial word-level glosses, not validated translations",
        "human_comprehension_validated": False,
        "canonical_vocabulary_changed": False,
        "lessons": result,
    }
