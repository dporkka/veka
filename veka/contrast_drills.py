"""Optional grammar contrast exercises; never a lexical or grammatical extension.

Editorial readings are *teaching prompts*, not uniquely entailed translations
or measured learner outcomes. Validate every utterance against strict core and
assert that only the intended parse feature changes in each minimal pair.
"""
from __future__ import annotations

from difflib import SequenceMatcher

from .beginner import guide_sentence
from .core import VekaError, parse
from .international import read_candidates
from .learner_locales import LANGUAGES
from .profiles import DATA, load_profile


# ID, audited parser field, A, B, A translations, B translations, teaching focus
# Translations are editorial approximations, not machine-generated interpretations.
CONTRASTS = (
    ("speaker", "subject", "Mi dak mel.", "Ti dak mel.",
     ("I send a message.", "我发送一条消息。", "Eu envio uma mensagem."),
     ("You send a message.", "你发送一条消息。", "Você envia uma mensagem."),
     ("A different pronoun changes the sender.", "更换代词会改变发送者。", "Outro pronome muda quem envia.")),
    ("past", "tense", "Mi dak mel.", "Mi pa dak mel.",
     ("I send a message.", "我发送一条消息。", "Eu envio uma mensagem."),
     ("I sent a message.", "我发送了一条消息。", "Eu enviei uma mensagem."),
     ("The independent particle pa marks past time.", "独立助词 pa 标记过去。", "A partícula independente pa indica passado.")),
    ("future", "tense", "Mi pa dak mel.", "Mi fu dak mel.",
     ("I sent a message.", "我发送了一条消息。", "Eu enviei uma mensagem."),
     ("I will send a message.", "我将发送一条消息。", "Eu enviarei uma mensagem."),
     ("Replacing pa with fu changes past to future.", "用 fu 替换 pa 将过去改为将来。", "Trocar pa por fu muda passado para futuro.")),
    ("negation", "negative", "Mi pa dak mel.", "Mi pa ne dak mel.",
     ("I sent a message.", "我发送了一条消息。", "Eu enviei uma mensagem."),
     ("I did not send a message.", "我没有发送消息。", "Eu não enviei uma mensagem."),
     ("The particle ne negates the clause predicate.", "助词 ne 否定句子的谓语。", "A partícula ne nega o predicado da oração.")),
    ("quantity", "subject_quantifier", "Al ren pa gos.", "Kis ren pa gos.",
     ("Every person went.", "每个人都走了。", "Todas as pessoas foram."),
     ("Some people went.", "一些人走了。", "Algumas pessoas foram."),
     ("al means every; kis means some, not necessarily all.", "al 表示每个；kis 表示某些，不一定全部。", "al significa todos; kis significa alguns, não necessariamente todos.")),
    ("object", "object", "Mi dak mel.", "Mi dak kun.",
     ("I send a message.", "我发送一条消息。", "Eu envio uma mensagem."),
     ("I send information.", "我发送信息。", "Eu envio informações."),
     ("The object changes without agreement or a case ending.", "宾语变化不需要一致或格尾。", "O objeto muda sem concordância nem desinência de caso.")),
)

# Exactly which parser attributes may change under each declared contrast.
ALLOWED_CHANGES = {
    "subject": frozenset({"subject"}),
    "tense": frozenset({"tense"}),
    "negative": frozenset({"negative"}),
    "subject_quantifier": frozenset({"subject", "subject_quantifier"}),
    "object": frozenset({"object"}),
}


def validate_contrast(feature: str, a: dict, b: dict) -> None:
    """Reject stale examples or contrast labels that misdescribe real grammar."""
    if feature not in ALLOWED_CHANGES:
        raise VekaError(f"unknown contrast feature: {feature}")
    changed = {key for key in set(a) | set(b) if a.get(key) != b.get(key)}
    if changed != ALLOWED_CHANGES[feature]:
        raise VekaError(f"contrast {feature} unexpectedly changes {sorted(changed)}")


def _one_token_change(a: str, b: str) -> bool:
    left = a.rstrip(".?!").casefold().split()
    right = b.rstrip(".?!").casefold().split()
    ops = [op for op in SequenceMatcher(a=left, b=right, autojunk=False).get_opcodes()
           if op[0] != "equal"]
    return len(ops) == 1 and max(ops[0][2] - ops[0][1], ops[0][4] - ops[0][3]) == 1


def make_contrast_drills(language: str, *, profile: str = "tonal") -> dict:
    if language not in LANGUAGES:
        raise VekaError(f"unsupported beginner language: {language}")
    lex = load_profile(profile)
    candidates = read_candidates(DATA / "international_candidates_v04.csv")
    index = LANGUAGES.index(language)
    result = []
    for identifier, feature, a, b, translations_a, translations_b, focus in CONTRASTS:
        if not _one_token_change(a, b):
            raise VekaError(f"not a minimal token contrast: {identifier}")
        first, second = parse(a, lex, strict=True), parse(b, lex, strict=True)
        validate_contrast(feature, first, second)
        def side(sentence: str, translation: tuple, structure: dict) -> dict:
            guide = guide_sentence(sentence, lex, candidates, profile=profile,
                                   language=language, include_cues=False)
            if guide["gloss_coverage"]["english_fallback"] != 0:
                raise VekaError(f"incomplete {language} contrast gloss: {sentence}")
            return {"sentence": sentence, "editorial_translation": translation[index],
                    "structure": structure, "guide": guide}
        result.append({"id": identifier, "feature": feature, "changed_feature": feature,
                       "focus": focus[index], "a": side(a, translations_a, first),
                       "b": side(b, translations_b, second)})
    return {
        "schema_version": "veka.contrast-drills.v1",
        "language": language, "profile": profile,
        "pairs": result, "human_comprehension_tested": False,
        "canonical_vocabulary_changed": False,
        "notice": "Parser-validated single-feature differences; editorial readings only. "
                  "Not proof of human comprehension, pronunciation ease or translation equivalence.",
    }


def format_contrast_drills(packet: dict) -> str:
    headers = {
        "en": ("Veka grammar contrasts", "Editorial interpretations, NOT human-tested."),
        "zh": ("Veka 语法对比练习", "人工编写的解释，尚未经过真人测试。"),
        "pt-BR": ("Contrastes gramaticais de Veka", "Interpretações editoriais, NÃO testadas com pessoas."),
    }
    header, warning = headers[packet["language"]]
    lines = [f'{header} ({packet["language"]}, {packet["profile"]})', warning]
    for item in packet["pairs"]:
        lines.extend([f'[{item["id"]}] {item["focus"]}',
                      f' A. {item["a"]["sentence"]} — {item["a"]["editorial_translation"]}',
                      f' B. {item["b"]["sentence"]} — {item["b"]["editorial_translation"]}'])
    return "\n".join(lines)
