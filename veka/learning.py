"""Machine-checked teaching materials for canonical Veka, not translation validation.

Never infer fluent conversational support from this deliberately controlled
corpus. English glosses are human-authored editorial interpretations.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

from .core import VekaError, parse
from .profiles import load_profile

DEFAULT_LESSONS = Path(__file__).resolve().parents[1] / "data" / "beginner_dialogues_v01.json"
VERSION = "veka.beginner-dialogues.v01"
LESSON_ID = re.compile(r"B[0-9]{2}\Z", re.ASCII)
OPTIONS = "ABCD"


def load_lessons(path: str | Path = DEFAULT_LESSONS) -> list[dict]:
    """Load and strictly parse every utterance in the frozen beginner profile.

    Content format is stable and all sentences are checked using canonical
    Veka 0.4 tonal vocabulary plus the 0.3 strict reference parser.
    English translations are editorial and NOT mechanically proven.
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VekaError(f"cannot load beginner lessons: {exc}") from exc
    if (not isinstance(data, dict)
            or data.get("schema_version") != VERSION
            or data.get("canonical_profile") != "tonal"
            or data.get("canonical_language_version") != "0.4"
            or not isinstance(data.get("lessons"), list)
            or not data["lessons"]):
        raise VekaError("invalid beginner curriculum schema/profile")

    lex = load_profile("tonal")
    seen: set[str] = set()
    result = []
    for lesson in data["lessons"]:
        if not isinstance(lesson, dict):
            raise VekaError("invalid lesson record")
        identifier = lesson.get("id")
        title = lesson.get("title")
        turns = lesson.get("turns")
        if (not isinstance(identifier, str) or not LESSON_ID.fullmatch(identifier)
                or identifier in seen or not isinstance(title, str) or not title.strip()
                or not isinstance(turns, list) or len(turns) != 4):
            raise VekaError(f"invalid or repeated lesson: {identifier!r}")
        seen.add(identifier)
        meanings = set()
        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                raise VekaError(f"{identifier}: malformed turn")
            veka = turn.get("veka")
            english = turn.get("english")
            speaker = turn.get("speaker")
            if (speaker != ("A" if i % 2 == 0 else "B")
                    or not isinstance(veka, str) or not veka.strip()
                    or not isinstance(english, str) or not english.strip()
                    or english in meanings):
                raise VekaError(f"{identifier}: invalid turn {i + 1}")
            meanings.add(english)
            try:
                parse(veka, lex, strict=True)
            except VekaError as exc:
                raise VekaError(f"{identifier}, turn {i + 1}: {exc}") from exc
        result.append(lesson)
    return result


def lesson_by_id(lessons: list[dict], identifier: str) -> dict:
    for lesson in lessons:
        if lesson["id"] == identifier:
            return lesson
    raise VekaError(f"unknown beginner lesson: {identifier}")


def create_question(lesson: dict, question_number: int, seed: int = 20261101) -> dict:
    """Offer four candidate English interpretations for one fixed Veka sentence."""
    if type(question_number) is not int or not 1 <= question_number <= 4:
        raise VekaError("question number must be 1–4")
    if type(seed) is not int:
        raise VekaError("seed must be an integer")
    index = question_number - 1
    turns = lesson["turns"]
    correct_translation = turns[index]["english"]
    translations = [turn["english"] for turn in turns]
    if len(set(translations)) != 4:
        raise VekaError("lesson translations must be unique")
    rng = random.Random(f"{seed}:{lesson['id']}:{question_number}")
    rng.shuffle(translations)
    choices = dict(zip(OPTIONS, translations))
    correct_choice = next(choice for choice, meaning in choices.items()
                          if meaning == correct_translation)
    return {
        "lesson_id": lesson["id"],
        "question": question_number,
        "veka": turns[index]["veka"],
        "options": choices,
        "correct_choice": correct_choice,
    }


def check_answer(question: dict, answer: str) -> bool:
    if not isinstance(answer, str) or answer not in OPTIONS:
        raise VekaError("answer must be exactly one of A, B, C, D")
    return answer == question["correct_choice"]


def public_question(question: dict) -> dict:
    """Do not expose answer keys before a response is submitted."""
    return {k: v for k, v in question.items() if k != "correct_choice"}
