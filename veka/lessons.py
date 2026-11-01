"""Small, canonical, progressive first-sight lessons with editorial translations.

Only the restricted core is taught; translations are curated sentence readings,
never outputs of the Veka parser or evidence of learner comprehension.
"""
from __future__ import annotations

from .beginner import guide_sentence
from .core import VekaError
from .international import read_candidates
from .learner_locales import LANGUAGES
from .profiles import DATA, load_profile

# (core sentence, English, 简体中文, Português brasileiro, teaching focus)
# All sentences must continue to pass strict parsing in every profile.
LESSONS = (
    ("Ti sen kun.", "You understand information.", "你理解信息。", "Você entende informações.", "pronoun + verb + object"),
    ("Mi lin za.", "I see a computer.", "我看到一台计算机。", "Eu vejo um computador.", "subject–verb–object"),
    ("Mi pa dak mel.", "I sent a message.", "我发送了一条消息。", "Eu enviei uma mensagem.", "past particle pa"),
    ("Mi pa ne dak mel.", "I did not send a message.", "我没有发送消息。", "Eu não enviei uma mensagem.", "negation ne"),
    ("Mi rok sau.", "I read a book.", "我读书。", "Eu leio um livro.", "everyday object"),
    ("Al ren pa gos.", "Every person went.", "每个人都走了。", "Todas as pessoas foram.", "restricted quantifier al"),
    ("Mi sus woi.", "I listen to music.", "我听音乐。", "Eu escuto música.", "everyday activity"),
    ("Mi sen nol.", "I understand a language.", "我理解一种语言。", "Eu entendo uma língua.", "language vocabulary"),
    ("Mi rin sil wen ran dis gel su wok.", "I need 1.5 liters of water.",
     "我需要1.5升水。", "Eu preciso de 1,5 litro de água.", "exact decimal and unit"),
    ("Ren-sak pa gos.", "A knowledgeable person went.", "一位有知识的人走了。",
     "Uma pessoa com conhecimento foi.", "transparent compound, silent hyphen"),
)


FOCUS_TRANSLATIONS = {
    "pronoun + verb + object": ("代词 + 动词 + 宾语", "pronome + verbo + objeto"),
    "subject–verb–object": ("主语–动词–宾语", "sujeito–verbo–objeto"),
    "past particle pa": ("过去标记 pa", "partícula de passado pa"),
    "negation ne": ("否定词 ne", "negação ne"),
    "everyday object": ("日常事物", "objeto do cotidiano"),
    "restricted quantifier al": ("限定全称量词 al", "quantificador universal restrito al"),
    "everyday activity": ("日常活动", "atividade cotidiana"),
    "language vocabulary": ("语言词汇", "vocabulário sobre línguas"),
    "exact decimal and unit": ("精确小数和单位", "decimal exato e unidade"),
    "transparent compound, silent hyphen": ("透明复合词（连字符不发音）", "composto transparente (hífen não pronunciado)"),
}


def build_lessons(language: str, *, profile: str = "tonal") -> dict:
    if language not in LANGUAGES:
        raise VekaError(f"unsupported beginner language: {language}")
    lex = load_profile(profile)
    candidates = read_candidates(DATA / "international_candidates_v04.csv")
    index = {"en": 1, "zh": 2, "pt-BR": 3}[language]
    lessons = []
    for ordinal, row in enumerate(LESSONS, 1):
        sentence = row[0]
        guide = guide_sentence(sentence, lex, candidates, profile=profile,
                               language=language, include_cues=False)
        lessons.append({"order": ordinal, "sentence": sentence,
                        "editorial_translation": row[index],
                        "focus": (row[4] if language == "en" else
                                  FOCUS_TRANSLATIONS[row[4]][0 if language == "zh" else 1]),
                        "guide": guide})
    return {
        "schema_version": "veka.lessons.v1", "language": language, "profile": profile,
        "lessons": lessons, "human_comprehension_tested": False,
        "canonical_vocabulary_changed": False,
        "notice": "Curated editorial translations; not generated translations or human validation.",
    }


def format_lessons(packet: dict) -> str:
    language = packet["language"]
    labels = {
        "en": ("VEKA beginner lessons", "Curated translations; NOT human-tested learning outcomes.", "Focus"),
        "zh": ("VEKA 初学者课程", "人工编写的译文；尚未进行真人学习效果测试。", "学习重点"),
        "pt-BR": ("Lições iniciais de VEKA", "Traduções editoriais; resultados de aprendizagem NÃO testados.", "Foco"),
    }
    title, notice, focus_label = labels[language]
    lines = [f'{title} ({language}, {packet["profile"]})', notice]
    for lesson in packet["lessons"]:
        word_glosses = " ".join("{} [{}]".format(w["token"], w["gloss"])
                               for w in lesson["guide"]["words"])
        lines.extend([f'{lesson["order"]}. {lesson["sentence"]}',
                      f'   {lesson["editorial_translation"]}',
                      f'   {word_glosses}',
                      f'   {focus_label}: {lesson["focus"]}'])
    return "\n".join(lines)
