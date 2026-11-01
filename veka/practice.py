"""Offline active-recall practice with existing, parser-checked editorial lessons.

Recognition is a three-choice exercise and recall is an exact taught-surface
exercise. Neither establishes semantic equivalence, spontaneous speech
competence, or empirically measured comprehension. No lexemes are adopted.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

from .core import VekaError
from .learner_locales import LANGUAGES
from .lessons import build_lessons
from .profiles import PROFILES

MODES = ("recognition", "recall")
VERSION = "veka.practice.v11"
RESPONSE_FIELDS = ("question_id", "response")


def _check_parameters(language: str, mode: str, seed: int, count: int,
                      profile: str) -> None:
    if language not in LANGUAGES:
        raise VekaError("unsupported practice language")
    if mode not in MODES:
        raise VekaError("unsupported practice mode")
    if profile not in PROFILES:
        raise VekaError("unsupported practice profile")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise VekaError("practice seed must be an integer")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 10:
        raise VekaError("practice count must be from 1 to 10")


def build_practice(language: str, *, mode: str = "recognition",
                   profile: str = "tonal", seed: int = 20261101,
                   count: int = 10) -> dict:
    """Produce self-test questions WITHOUT solutions or parser internals."""
    _check_parameters(language, mode, seed, count, profile)
    # build_lessons verifies strict canonical parser acceptance for each lesson.
    lessons = build_lessons(language, profile=profile)["lessons"]
    if len(lessons) != 10 or len({row["editorial_translation"] for row in lessons}) != 10:
        raise VekaError("practice requires 10 distinct curated lesson readings")
    rng = random.Random(seed)
    shuffled = list(lessons)
    rng.shuffle(shuffled)
    questions = []
    for row in shuffled[:count]:
        question_id = f'L{row["order"]:02d}'
        if mode == "recall":
            questions.append({"question_id": question_id,
                              "prompt": row["editorial_translation"]})
        else:
            others = [item for item in lessons if item["order"] != row["order"]]
            distractors = rng.sample(others, 2)
            choices = [row["editorial_translation"]] + [
                item["editorial_translation"] for item in distractors
            ]
            rng.shuffle(choices)
            questions.append({
                "question_id": question_id,
                "prompt": row["sentence"],
                "choices": dict(zip("ABC", choices)),
            })
    return {
        "schema_version": VERSION,
        "language": language,
        "mode": mode,
        "profile": profile,
        "seed": seed,
        "total_questions": len(questions),
        "questions": questions,
        "human_comprehension_validated": False,
        "canonical_vocabulary_changed": False,
        "notice": (
            "Self-practice only. Recognition choices and production targets are "
            "editorial teaching readings, not validated translations. "
            "Recall grading checks the taught written surface, not equivalent meanings."
        ),
    }


def format_practice(packet: dict) -> str:
    lines = [
        f'VEKA practice ({packet["language"]}, {packet["mode"]}, '
        f'{packet["profile"]}, seed={packet["seed"]})',
        packet["notice"],
        "Record question_id,response in a CSV file, then run practice-check "
        "with the SAME lang/mode/profile/seed/count.",
    ]
    for question in packet["questions"]:
        lines.append(f'{question["question_id"]}: {question["prompt"]}')
        for key, meaning in question.get("choices", {}).items():
            lines.append(f'  {key}) {meaning}')
    return "\n".join(lines)


def read_practice_responses(path: str | Path) -> list[dict[str, str]]:
    """Read participant-provided answers; reject answer-key columns and malformed CSV."""
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            if tuple(reader.fieldnames or ()) != RESPONSE_FIELDS:
                raise VekaError("practice CSV must have exactly question_id,response")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("cannot read practice responses") from exc
    if any(set(row) != set(RESPONSE_FIELDS) or
           not all(isinstance(row.get(k), str) for k in RESPONSE_FIELDS)
           for row in rows):
        raise VekaError("malformed practice response row")
    return rows


def _normalized_surface(value: str) -> str:
    """Only cosmetic case/whitespace/one final-period equivalence."""
    surface = " ".join(value.strip().split()).casefold()
    return surface[:-1] if surface.endswith(".") else surface


def grade_practice(rows: list[dict[str, str]], language: str, *,
                   mode: str = "recognition", profile: str = "tonal",
                   seed: int = 20261101, count: int = 10) -> dict:
    """Assess exact self-practice choices/forms, never infer translations."""
    packet = build_practice(language, mode=mode, profile=profile,
                            seed=seed, count=count)
    questions = {q["question_id"]: q for q in packet["questions"]}
    lessons = {f'L{row["order"]:02d}': row for row
               in build_lessons(language, profile=profile)["lessons"]}
    if not isinstance(rows, list):
        raise VekaError("practice responses must be a list")
    seen = set()
    feedback = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(RESPONSE_FIELDS):
            raise VekaError("practice response must contain only question_id and response")
        qid, response = row["question_id"], row["response"]
        if not isinstance(qid, str) or not isinstance(response, str):
            raise VekaError("practice response must be text")
        if qid not in questions or qid in seen:
            raise VekaError("unknown or duplicate practice question")
        seen.add(qid)
        if not response.strip():
            feedback.append({"question_id": qid, "status": "unanswered"})
            continue
        if mode == "recognition":
            if response not in ("A", "B", "C"):
                raise VekaError("recognition response must be A, B, or C")
            target = lessons[qid]["editorial_translation"]
            expected = next(label for label, text
                            in questions[qid]["choices"].items() if text == target)
            correct = response == expected
        else:
            expected = lessons[qid]["sentence"]
            correct = _normalized_surface(response) == _normalized_surface(expected)
        feedback.append({
            "question_id": qid,
            "status": "correct" if correct else "incorrect",
            "expected": expected if not correct else None,
        })
    correct_count = sum(row["status"] == "correct" for row in feedback)
    incorrect_count = sum(row["status"] == "incorrect" for row in feedback)
    answered = correct_count + incorrect_count
    return {
        "schema_version": "veka.practice-feedback.v11",
        "language": language, "mode": mode, "profile": profile,
        "seed": seed, "total_questions": count,
        "answered": answered, "correct": correct_count,
        "incorrect": incorrect_count, "unanswered": count - answered,
        "accuracy_answered": correct_count / answered if answered else None,
        "feedback": feedback,
        "translation_equivalence_established": False,
        "semantic_equivalence_judged": False,
        "human_comprehension_validated": False,
        "canonical_vocabulary_changed": False,
        "notice": "Exact taught-form/choice check only. No semantic equivalence or human comprehension claim.",
    }
