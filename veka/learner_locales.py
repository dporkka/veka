"""Curated, explicitly partial first-sight vocabulary glosses (not translations).

Keys include the English meaning to prevent silently giving an obsolete or
incorrect foreign-language gloss after a lexical revision. Unlisted entries are
clearly marked as English fallbacks. These labels do not change Veka lexemes.
"""
from __future__ import annotations

from .core import VekaError

LANGUAGES = ("en", "zh", "pt-BR")

# canonical_form -> (expected English gloss, Mandarin gloss, pt-BR gloss)
# Include phonological and grammatical particles as well as the first-sight
# core; glosses are intentionally word-level, not fluent sentence translations.
WORDS = {
    "mi": ("I/me", "我", "eu/mim"),
    "ti": ("you", "你", "você"),
    "ni": ("we/us", "我们", "nós"),
    "sa": ("he/she/it (established referent)", "他/她/它（已知对象）", "ele/ela/isso (referente conhecido)"),
    "pa": ("past", "过去", "passado"),
    "fu": ("future", "将来", "futuro"),
    "du": ("progressive", "进行体", "progressivo"),
    "ne": ("not", "不", "não"),
    "lu": ("plural", "复数", "plural"),
    "al": ("every", "每个", "cada"),
    "kis": ("some", "某些", "algum"),
    "ke": ("yes/no question", "是非疑问", "pergunta de sim/não"),
    "ha": ("command", "祈使", "imperativo"),
    "es": ("is / copula", "是（系词）", "ser/estar (cópula)"),
    "to": ("recipient marker", "接受者标记", "marcador de destinatário"),
    "en": ("location marker", "地点标记", "marcador de lugar"),
    "de": ("of", "的", "de"),
    "su": ("unit marker", "单位标记", "marcador de unidade"),
    "sin": ("negative number sign", "负号", "sinal de número negativo"),
    "dis": ("decimal point", "小数点", "separador decimal"),
    "dak": ("send", "发送", "enviar"),
    "mel": ("message", "消息", "mensagem"),
    "sen": ("understand", "理解", "entender"),
    "kun": ("information", "信息", "informação"),
    "lin": ("see", "看见", "ver"),
    "za": ("computer", "计算机", "computador"),
    "ren": ("person", "人", "pessoa"),
    "gos": ("go", "去", "ir"),
    "rok": ("read", "阅读", "ler"),
    "sau": ("book", "书", "livro"),
    "nol": ("language", "语言", "língua"),
    "sus": ("listen", "听", "escutar"),
    "woi": ("music", "音乐", "música"),
    "sil": ("water", "水", "água"),
    "rin": ("need", "需要", "precisar"),
    "wok": ("liter", "升", "litro"),
    "sak": ("knowledgeable", "有知识的", "conhecedor"),
    "ton": ("receive", "接收", "receber"),
    "vak": ("speak", "说话", "falar"),
    "kon": ("arrive", "到达", "chegar"),
    "fen": ("find", "找到", "encontrar"),
    "wen": ("number", "数字", "número"),
}

# Grammar uses positional disambiguation of wen vs its noun head.
SPECIAL = {
    "exact-number marker": ("精确数字标记", "marcador de número exato"),
    "proper name (not translated)": ("专有名词（未翻译）", "nome próprio (não traduzido)"),
}


def localized_gloss(form: str, english: str, language: str) -> tuple[str, str]:
    """Return (display gloss, language actually used). Never silently translate."""
    if language not in LANGUAGES:
        raise VekaError(f"unsupported beginner language: {language}")
    if language == "en":
        return english, "en"
    index = 1 if language == "zh" else 2
    if english.startswith("digit ") and english[6:].isdigit():
        return (f"数字{english[6:]}" if language == "zh"
                else f"dígito {english[6:]}"), language
    pair = SPECIAL.get(english)
    if pair:
        return pair[index - 1], language
    row = WORDS.get(form)
    if row is not None and row[0] == english:
        return row[index], language
    return english + " (en)", "en"


def local_notice(language: str, fallback_count: int) -> str:
    if language == "en":
        return ("English word glosses are a learning aid, not a complete translation. "
                "International-looking draft forms are NOT accepted Veka and have no measured recognition benefit.")
    if language == "zh":
        return (f"词语释义仅供学习，不是完整句子翻译。有 {fallback_count} 个词尚无中文释义，"
                "其英语释义以 (en) 标注。国际词形只是未验证的草案，不属于标准 Veka，"
                "识别效果尚未经过真人测试。")
    return ("As glosas são auxiliares de aprendizagem, não traduções completas. "
            f"{fallback_count} itens usam inglês marcado com (en). "
            "Formas internacionais são propostas não verificadas, não vocabulário Veka aceito.")


def local_labels(language: str) -> tuple[str, str, str]:
    if language == "zh":
        return "中文", "语法结构（标准角色名）", "国际词形联想（未获 Veka 接纳）"
    if language == "pt-BR":
        return "Português (Brasil)", "Estrutura sintática (campos canônicos)", "Associações internacionais (NÃO são Veka)"
    return "English", "Parsed structure", "Illustrative international associations (NOT accepted Veka)"
