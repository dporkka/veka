"""First-sight, read-only interlinear guide for canonical single-clause Veka.

The guide provides English *glosses*, not a semantic English translation.
International-looking words are unverified reading *cues*, never synonyms
registered in the Veka grammar or lexicon.
"""
from __future__ import annotations

import unicodedata

from .core import Lexicon, VekaError, _normalize_sentence, parse
from .international import audit_candidates
from .numbers import DIGIT_VALUES
from .profiles import DATA, PROFILES
from .learner_locales import LANGUAGES, localized_gloss, local_labels, local_notice

GRAMMAR_GLOSSES = {
    "pa": "past", "fu": "future", "du": "progressive", "ne": "not",
    "lu": "plural", "al": "every", "kis": "some", "ke": "yes/no question",
    "ha": "command", "es": "is / copula", "to": "recipient marker",
    "en": "location marker", "de": "of", "su": "unit marker",
    "sin": "negative number sign", "dis": "decimal point",
}


def _gloss(form: str, following: str, lex: Lexicon) -> str:
    """Label numerical roles without confusing the headword wen with its marker."""
    if form == "wen" and (following in DIGIT_VALUES or following == "sin"):
        return "exact-number marker"
    if form in DIGIT_VALUES:
        return f"digit {DIGIT_VALUES[form]}"
    return GRAMMAR_GLOSSES.get(form, lex[form].gloss)


def guide_sentence(
    sentence: str,
    lex: Lexicon,
    candidates: list[dict],
    *,
    profile: str = "tonal",
    include_cues: bool = True,
    language: str = "en",
) -> dict:
    """Explain one *strictly parsed* sentence without modifying its vocabulary.

    Any unsupported construction fails closed rather than producing misleading
    interlinear information. International cues are separate from the text.
    """
    if language not in LANGUAGES:
        raise VekaError(f"unsupported beginner language: {language}")
    if profile not in PROFILES:
        raise VekaError(f"unsupported beginner profile: {profile}")
    if not isinstance(sentence, str):
        raise VekaError("beginner sentence must be text")

    structure = parse(sentence, lex, strict=True)
    normalized = unicodedata.normalize("NFC", sentence.strip())
    tokens = _normalize_sentence(sentence)
    cue_by_root = {}
    if include_cues:
        # Validate the *entire* source queue against the canonical lexicon, not
        # just the words present in the sentence, before exposing hypotheses.
        canonical_lex = Lexicon.from_csv(DATA / "lexicon.csv")
        report = audit_candidates(candidates, canonical_lex)
        approved_for_research = {
            r["concept_id"] for r in report["candidates"]
            if r["status"] == "structurally_testable"
        }
        for row in candidates:
            if row["concept_id"] not in approved_for_research:
                continue
            key = row["core_form"]
            if key not in lex:  # alternative lexical profiles may rename roots
                matches = [
                    e.form for e in lex.values() if e.kind == "root"
                    and (e.gloss, e.pos) == (row["gloss"], row["pos"])
                ]
                if len(matches) != 1:
                    continue
                key = matches[0]
            cue_by_root[key] = row

    words = []
    cues = []
    english_fallback = 0
    for i, raw in enumerate(tokens):
        form = raw.lower()
        if form not in lex:
            # The grammar permits capitalized proper names but does not
            # translate or infer their identity.
            gloss, gloss_language = localized_gloss(raw, "proper name (not translated)", language)
            words.append({
                "token": raw, "form": raw, "gloss": gloss, "gloss_language": gloss_language,
                "pos": "proper", "kind": "proper_name",
            })
            if language != "en" and gloss_language == "en":
                english_fallback += 1
            continue

        entry = lex[form]
        following = tokens[i + 1].lower() if i + 1 < len(tokens) else ""
        if entry.kind == "compound":
            if entry.head not in lex or entry.modifier not in lex:
                raise VekaError("compound decomposition is missing from lexicon")
            head, head_lang = localized_gloss(entry.head, lex[entry.head].gloss, language)
            modifier, mod_lang = localized_gloss(entry.modifier, lex[entry.modifier].gloss, language)
            gloss = f"{head} + {modifier}"
            gloss_language = language if head_lang == mod_lang == language else "en"
            kind = "transparent_compound"
        else:
            gloss, gloss_language = localized_gloss(form, _gloss(form, following, lex), language)
            kind = "canonical_root"
        word = {"token": raw, "form": form, "gloss": gloss,
                "gloss_language": gloss_language, "pos": entry.pos, "kind": kind}
        if language != "en" and gloss_language == "en":
            english_fallback += 1
        if kind == "transparent_compound":
            word["silent_hyphen"] = True
        words.append(word)
        if include_cues and form in cue_by_root and entry.kind == "root":
            candidate = cue_by_root[form]
            cues.append({
                "canonical_form": form, "gloss": entry.gloss,
                "illustrative_spelling": candidate["reference_spelling"],
                "draft_form": candidate["candidate_form"],
                "status": "unverified_draft",
                "recognition_measured": False,
                "accepted_vocabulary": False,
            })

    ending = normalized[-1] if normalized and normalized[-1] in ".?!" else ""
    reading = " ".join(f'{w["token"]} [{w["gloss"]}]' for w in words) + ending
    return {
        "gloss_coverage": {"localized": len(words) - english_fallback,
                           "english_fallback": english_fallback},
        "canonical": normalized, "profile": profile,
        "interlinear": reading, "words": words,
        "structure": structure,
        "experimental_cues": cues,
        "grammar_validated": True, "translated": False,
        "canonical_vocabulary_changed": False,
        "human_recognition_measured": False,
        "language_of_glosses": language if language != "en" else "English",
        "notice": local_notice(language, english_fallback),
    }


def format_beginner_guide(guide: dict) -> str:
    """Human-readable display, with unverified cues never inserted in Veka text."""
    structure = guide["structure"]
    roles = []
    for label in ("subject", "predicate", "object", "recipient", "location", "time"):
        if structure.get(label):
            roles.append(f'{label}={structure[label]}')
    if structure["tense"] != "unspecified":
        roles.append(f'tense={structure["tense"]}')
    if structure["negative"]:
        roles.append("negated=yes")
    if structure["question"]:
        roles.append("question=yes")
    language = guide["language_of_glosses"]
    language = "en" if language == "English" else language
    name, structure_label, cue_label = local_labels(language)
    heading = {"en": "Reading aid", "zh": "逐词释义", "pt-BR": "Glosas"}
    lines = [
        f'Veka ({guide["profile"]}): {guide["canonical"]}',
        f'{heading[language]} ({name}): {guide["interlinear"]}',
        f'{structure_label}: ' + "; ".join(roles),
    ]
    if guide["experimental_cues"]:
        lines.append(cue_label + ":")
        for cue in guide["experimental_cues"]:
            lines.append(
                f'  {cue["canonical_form"]} [{cue["gloss"]}]: '
                f'{cue["illustrative_spelling"]} '
                f'(unverified experimental form: {cue["draft_form"]})'
            )
    lines.append(guide["notice"])
    return "\n".join(lines)
