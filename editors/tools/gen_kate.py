#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор определений подсветки Primula v1.1-draft для Kate / KWrite / KDevelop
(KDE Syntax Highlighting, формат XML).

Назначение: порождает два файла
  kate/primula.xml       — основной язык (документы, фрагменты, модули: *.prml);
  kate/primula-code.xml  — файлы, где после YAML-заголовка идёт КОД, а не
                           разметка (*.s.prml, *.p.prml; разд. 2.2 спецификации).

Почему генератор, а не ручной XML: вложенные контексты (тела |*{…}, |/{…}…,
скобки аргументов) для каждого вида одинаковы и отличаются только атрибутом;
ручное копирование привело бы к расхождениям. Словари слов — из prml_lexicon.py.

Модель разбора (кратко):
  Start     — начало файла: «---» в первой строке открывает YAML-заголовок
              (Kate не знает номера строки, поэтому Start — это начальный
              контекст, из которого любой другой первый символ ведёт в Body);
  Header*   — упрощённая подсветка YAML (только данные, без выражений);
  Body      — разметка: блочные формы в начале строки + внутристрочные формы;
  Args/Expr — подмножество Python в скобках аргументов и в |(…), |=(…);
  *Block    — |code:, |comment:, |verbatim: до строки |end (или своего маркера).

Запуск: python3 gen_kate.py <каталог_вывода>
Ссылки: https://api.kde.org/frameworks/syntax-highlighting/html/ (формат XML),
        schema: data/schema/language.xsd в репозитории KDE/syntax-highlighting.
"""
import os
import sys
from xml.sax.saxutils import quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prml_lexicon as L  # noqa: E402

# --- Регулярные выражения (PCRE через QRegularExpression, Unicode включён) ----
# XID_Start / XID_Continue приближены классами \p{L}\p{Nl} / \p{L}\p{N}_ :
# для подсветки точное соответствие UAX #31 не требуется.
ID_START = r"[\p{L}\p{Nl}]"
ID_CONT = r"[\p{L}\p{N}_]"
IDENT = ID_START + ID_CONT + "*"
NOT_ID = r"(?![\p{L}\p{N}_])"                 # граница справа от имени
STYLE_NAME = ID_START + r"[\p{L}\p{N}_\-]*"   # имя стиля допускает дефис
DOTTED = IDENT + r"(?:\." + IDENT + ")*"      # имя команды с модулями
# Остаток строки допускает только пробелы и комментарий |% (LineEnd грамматики).
TAIL_OK = r"(?=[ \t]*(?:\|%.*)?$)"


class Xml:
    """Накопитель XML-строк с отступами; минимальный, без зависимостей."""

    def __init__(self):
        self.lines = []
        self.depth = 0

    def add(self, text):
        self.lines.append("  " * self.depth + text)

    def open(self, text):
        self.add(text)
        self.depth += 1

    def close(self, text):
        self.depth -= 1
        self.add(text)

    def text(self):
        return "\n".join(self.lines) + "\n"


def attrs(**kw):
    """Собирает атрибуты XML; ключи с суффиксом «_» (напр. String_) — как есть."""
    out = []
    for k, v in kw.items():
        if v is None:
            continue
        k = k.rstrip("_")
        out.append(f"{k}={quoteattr(str(v))}")
    return " ".join(out)


# --- Элементы правил ----------------------------------------------------------
def rx(x, pattern, attribute=None, context=None, **kw):
    """RegExpr-правило. kw: column, firstNonSpace, lookAhead, beginRegion,
    endRegion, dynamic, minimal."""
    x.add("<RegExpr " + attrs(String=pattern, attribute=attribute,
                              context=context, **kw) + "/>")


def ch(x, char, attribute=None, context=None, **kw):
    """DetectChar-правило (один символ)."""
    x.add("<DetectChar " + attrs(char=char, attribute=attribute,
                                 context=context, **kw) + "/>")


def kw_rule(x, lst, attribute, context=None):
    """keyword-правило по списку <list name=…>."""
    x.add("<keyword " + attrs(String=lst, attribute=attribute,
                              context=context) + "/>")


def inc(x, ctx):
    """IncludeRules: подключение правил другого контекста."""
    x.add("<IncludeRules " + attrs(context=ctx) + "/>")


def context(x, name, attribute, body, lineEnd="#stay", fallthrough=None,
            lineEmpty=None, dynamic=None):
    """Контекст с телом, которое пишет функция body(x)."""
    x.open("<context " + attrs(name=name, attribute=attribute,
                               lineEndContext=lineEnd,
                               fallthroughContext=fallthrough,
                               lineEmptyContext=lineEmpty,
                               dynamic=dynamic) + ">")
    body(x)
    x.close("</context>")


# --- Атрибуты (itemData) -------------------------------------------------------
# (имя, defStyleNum, spell, доп.атрибуты). spell=False отключает проверку
# орфографии: проверяется только проза, заголовки и комментарии.
ITEMS = [
    ("Normal", "dsNormal", True, {}),
    ("HeaderDelim", "dsRegionMarker", False, {}),
    ("HeaderKey", "dsAttribute", False, {}),
    ("HeaderKnownKey", "dsKeyword", False, {}),
    ("HeaderValue", "dsNormal", False, {}),
    ("HeaderString", "dsString", False, {}),
    ("HeaderNumber", "dsDecVal", False, {}),
    ("HeaderConst", "dsConstant", False, {}),
    ("HeaderPunct", "dsOperator", False, {}),
    ("HeaderComment", "dsComment", True, {}),
    ("Comment", "dsComment", True, {}),
    ("Escape", "dsSpecialChar", False, {}),
    ("Error", "dsError", False, {}),
    ("BlockCmd", "dsControlFlow", False, {}),
    ("ControlFlow", "dsControlFlow", False, {}),
    ("ModuleCmd", "dsImport", False, {}),
    ("BuiltinCmd", "dsFunction", False, {}),
    ("UserCmd", "dsExtension", False, {}),
    ("DefName", "dsFunction", False, {"bold": "true"}),
    ("StyleName", "dsDataType", False, {}),
    ("Reference", "dsAnnotation", False, {}),
    ("StructMarker", "dsKeyword", False, {"bold": "true"}),
    ("HeadingMarker", "dsControlFlow", False, {"bold": "true"}),
    ("Heading", "dsNormal", True, {"bold": "true"}),
    ("Bracket", "dsOperator", False, {}),
    ("EnvColon", "dsOperator", False, {"bold": "true"}),
    ("ExprDelim", "dsOperator", False, {"bold": "true"}),
    ("Expression", "dsVariable", False, {}),
    ("Arguments", "dsNormal", False, {}),
    ("InlineMark", "dsOperator", False, {}),
    ("InlineBody", "dsNormal", True, {}),
    ("InlineBold", "dsNormal", True, {"bold": "true"}),
    ("InlineItalic", "dsNormal", True, {"italic": "true"}),
    ("InlineUnderline", "dsNormal", True, {"underline": "true"}),
    ("InlineSup", "dsOthers", True, {}),
    ("InlineSub", "dsOthers", True, {}),
    ("InlineStrike", "dsNormal", True, {"strikeOut": "true"}),
    ("InlineCode", "dsVerbatimString", False, {}),
    ("InlineQuote", "dsString", True, {}),
    ("InlinePlaceholder", "dsAlert", True, {}),
    ("CodeText", "dsNormal", False, {}),
    ("CommentText", "dsComment", True, {}),
    ("Verbatim", "dsVerbatimString", False, {}),
    ("PyKeyword", "dsKeyword", False, {}),
    ("PyConst", "dsConstant", False, {}),
    ("PyBuiltin", "dsBuiltIn", False, {}),
    ("PyStdlib", "dsBuiltIn", False, {"italic": "true"}),
    ("PyNumber", "dsDecVal", False, {}),
    ("PyString", "dsString", False, {}),
    ("PyEscape", "dsSpecialChar", False, {}),
    ("PyOperator", "dsOperator", False, {}),
    ("PyComment", "dsComment", True, {}),
]

# Внутристрочные короткие формы (разд. 3.3): символ → (суффикс, атрибут тела).
MARKS = {
    "*": ("Bold", "InlineBold"),
    "/": ("Italic", "InlineItalic"),
    "_": ("Underline", "InlineUnderline"),
    "^": ("Sup", "InlineSup"),
    ",": ("Sub", "InlineSub"),
    "—": ("Strike", "InlineStrike"),
    "`": ("Code", "InlineCode"),
    '"': ("Quote", "InlineQuote"),
    "?": ("Ph", "InlinePlaceholder"),
}


def esc_re(s):
    """Экранирует метасимволы regexp для литерала."""
    out = ""
    for c in s:
        out += ("\\" + c) if c in r".^$*+?()[]{}|\-" else c
    return out


def alt(names):
    """Альтернация имён, длинные вперёд (иначе «page» перехватит «pages»)."""
    return "(?:" + "|".join(esc_re(n) for n in sorted(names, key=lambda s: -len(s))) + ")"


# =============================================================================
# Контексты Python-подмножества
# =============================================================================
def py_rules(x):
    """Общие правила выражений ядра: строки, числа, слова, операторы.
    Скобки обрабатывают сами контексты (Args/Expr/код)."""
    # строки: префиксы r/f; тройные раньше одинарных
    pre = r"(?<![\p{L}\p{N}_])(?:[rRfF]{1,2})?"
    rx(x, pre + '"""', "PyString", "TripleDQ")
    rx(x, pre + "'''", "PyString", "TripleSQ")
    rx(x, pre + '"', "PyString", "StrDQ")
    rx(x, pre + "'", "PyString", "StrSQ")
    # числа: 1_000, 3.14, 1e-3 (литерал «10mm» не поддерживается языком)
    rx(x, r"(?<![\p{L}\p{N}_.])\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?(?![\p{L}\p{N}_])",
       "PyNumber")
    # имя именованного аргумента/присваивания (name=…) не должно подсвечиваться
    # как встроенное слово: list=…, type=… — обычные имена параметров
    rx(x, r"[\p{L}_][\p{L}\p{N}_]*(?=[ \t]*=(?!=))", "CodeText")
    rx(x, r":=", "Error")                      # запрещён (разд. 12.2)
    kw_rule(x, "pyforbidden", "Error")
    kw_rule(x, "pykeywords", "PyKeyword")
    kw_rule(x, "pyconsts", "PyConst")
    kw_rule(x, "pybuiltins", "PyBuiltin")
    kw_rule(x, "pystdlib", "PyStdlib")
    rx(x, r"//|\*\*|[<>=!]=|[-+*/%<>=]", "PyOperator")
    rx(x, r"[\[\]{},:;.]", "PyOperator")


def add_string_contexts(x):
    """Строки Python: одинарные кончаются в конце строки, тройные — нет."""
    def esc(x_):
        rx(x_, r"\\.", "PyEscape")

    context(x, "StrDQ", "PyString",
            lambda x_: (esc(x_), ch(x_, '"', "PyString", "#pop")),
            lineEnd="#pop")
    context(x, "StrSQ", "PyString",
            lambda x_: (esc(x_), ch(x_, "'", "PyString", "#pop")),
            lineEnd="#pop")
    context(x, "TripleDQ", "PyString",
            lambda x_: (esc(x_), rx(x_, '"""', "PyString", "#pop")))
    context(x, "TripleSQ", "PyString",
            lambda x_: (esc(x_), rx(x_, "'''", "PyString", "#pop")))


def add_paren_contexts(x):
    """Аргументы команд (Args) и выражения |( ) (Expr) с учётом вложенных скобок.
    Скобки внутри строк не считаются — строки выделены в свои контексты."""
    def make(name, attr, close_attr, nest, closer):
        def body(x_):
            ch(x_, ")", close_attr, "#pop")
            ch(x_, "(", "Bracket", nest)
            inc(x_, "PyRules")
        context(x, name, attr, body)

    make("Args", "Arguments", "Bracket", "ArgsNest", ")")
    make("ArgsNest", "Arguments", "Bracket", "ArgsNest", ")")
    make("Expr", "Expression", "ExprDelim", "ExprNest", ")")
    make("ExprNest", "Expression", "Bracket", "ExprNest", ")")


# =============================================================================
# Контексты разметки
# =============================================================================
def add_after_contexts(x):
    """Контексты «после маркера/имени команды»: необязательные аргументы (…),
    двоеточие окружения, тело {…}. Любой другой символ — выход без поглощения."""
    colon_env = (r":" + TAIL_OK)

    def after(name, brace=None, region=True, colon_line=False):
        def body(x_):
            ch(x_, "(", "Bracket", "Args")
            if brace:
                ch(x_, "{", "Bracket", brace)
            if colon_line:                     # «|.Имя: текст» — строчная форма
                rx(x_, colon_env, "EnvColon", "#pop",
                   beginRegion="env" if region else None)
                rx(x_, r":(?=[ \t])", "EnvColon", "#pop")
            else:                              # «|команда(...):» + конец строки
                rx(x_, colon_env, "EnvColon", "#pop",
                   beginRegion="env" if region else None)
        context(x, name, "Normal", body, lineEnd="#pop", fallthrough="#pop")

    after("AfterMarker")                                  # |> |- |! |: |& |@
    after("AfterCmd", brace="InlineBody")                 # команды с телом
    after("AfterCmdNR", brace="InlineBody", region=False)  # elif/else (без складки)
    after("AfterStyle", brace="InlineBody", colon_line=True)
    for m, (suf, _attr) in MARKS.items():                 # |*{ |/{ …
        after("After" + suf, brace="Inline" + suf)

    # |def имя(параметры):
    def defname(x_):
        rx(x_, r"[ \t]+", "Normal")
        rx(x_, IDENT, "DefName", "#pop!AfterCmd")
    context(x, "DefName", "Normal", defname, lineEnd="#pop", fallthrough="#pop")

    # Заголовок |<: после аргументов текст строки — стиль заголовка
    def hdr_after(x_):
        ch(x_, "(", "Bracket", "Args")
    context(x, "HeadingAfterMarker", "Normal", hdr_after, lineEnd="#pop",
            fallthrough="#pop!HeadingText")

    def hdr_text(x_):
        inc(x_, "InlineRules")
    context(x, "HeadingText", "Heading", hdr_text, lineEnd="#pop")


def add_inline_body_contexts(x):
    """Тела {…}: для каждой короткой формы — свой контекст (свой атрибут) и
    свой «вложенный» контекст для сбалансированных {…}. Закрывающая } снимает
    сразу два контекста: тело и After*, чтобы текст «}(…)» не принимался
    за аргументы."""
    names = [("InlineBody", "InlineBody")] + [
        ("Inline" + suf, attr) for (suf, attr) in MARKS.values()]
    for name, attr in names:
        nest = "Nest" + name

        def body(x_, nest=nest):
            ch(x_, "}", "Bracket", "#pop#pop")
            ch(x_, "{", "Bracket", nest)
            inc(x_, "InlineRules")

        def nbody(x_, nest=nest):
            ch(x_, "}", "Bracket", "#pop")
            ch(x_, "{", "Bracket", nest)
            inc(x_, "InlineRules")
        context(x, name, attr, body)
        context(x, nest, attr, nbody)


def add_inline_rules(x):
    """Правила, допустимые везде в строке (включаются в Body, заголовки, тела)."""
    def body(x_):
        rx(x_, r"\|%", "Comment", "LineComment")
        rx(x_, r"\|(?:\||\{|\}|;|~|\\)", "Escape")
        rx(x_, r"\|\(", "ExprDelim", "Expr")
        rx(x_, r"\|=\(", "ExprDelim", "Expr")
        for m, (suf, _attr) in MARKS.items():
            rx(x_, r"\|" + esc_re(m), "InlineMark", "After" + suf)
        rx(x_, r"\|@(?=\()", "Reference", "AfterMarker")
        rx(x_, r"\|&", "StructMarker", "AfterMarker")
        # структурные формы, не стоящие в начале строки, — ошибка (EBNF разд. 4)
        rx(x_, r"\|[<>!:\-#]", "Error")
        rx(x_, r"\|\.(?=\()", "StyleName", "AfterStyle")
        rx(x_, r"\|\." + STYLE_NAME, "StyleName", "AfterStyle")
        # управляющие: if/for открывают окружение (складка), elif/else — нет
        rx(x_, r"\|(?:if|for)" + NOT_ID + r"(?!\.)", "ControlFlow", "AfterCmd")
        rx(x_, r"\|(?:elif|else)" + NOT_ID + r"(?!\.)", "ControlFlow", "AfterCmdNR")
        rx(x_, r"\|" + alt(L.MODULE_CMDS) + NOT_ID + r"(?!\.)", "ModuleCmd", "AfterCmd")
        rx(x_, r"\|(?:" + alt(L.BUILTIN_CMDS) + r"|field\.[A-Za-z_]+)" + NOT_ID
           + r"(?!\.)", "BuiltinCmd", "AfterCmd")
        rx(x_, r"\|" + DOTTED, "UserCmd", "AfterCmd")
        ch(x_, "|", "Error")                    # любая прочая «|…» — ошибка
    context(x, "InlineRules", "Normal", body)


def add_body(x, tag_pass_through=True):
    """Контекст Body: блочные формы в начале строки, затем внутристрочные."""
    def body(x_):
        # блоки до |end: код, комментарий, буквальный текст
        rx(x_, r"\|code:" + TAIL_OK, "BlockCmd", "OpenCode",
           firstNonSpace="true", beginRegion="env")
        rx(x_, r"\|comment:" + TAIL_OK, "BlockCmd", "OpenComment",
           firstNonSpace="true", beginRegion="env")
        rx(x_, r"\|verbatim:" + TAIL_OK, "BlockCmd", "OpenVerbatim",
           firstNonSpace="true", beginRegion="env")
        # свой маркер конца: |verbatim(end="EOF"): … EOF (захват %1 → динамика)
        rx(x_, r'\|verbatim\(end="([^"\n]+)"\)[ \t]*:', "BlockCmd", "VerbatimDyn",
           firstNonSpace="true", beginRegion="env")
        # закрывающие маркеры (всегда занимают всю строку, разд. 3.5)
        rx(x_, r"\|end(?:" + "|".join(L.CONTROL_END[i][3:] for i in range(3))
           + r")" + NOT_ID, "ControlFlow", None, firstNonSpace="true",
           endRegion="env")
        rx(x_, r"\|end(?:>+|!)", "BlockCmd", None, firstNonSpace="true",
           endRegion="env")
        rx(x_, r"\|end\." + STYLE_NAME, "BlockCmd", None, firstNonSpace="true",
           endRegion="env")
        rx(x_, r"\|end[ \t]+" + DOTTED, "BlockCmd", None, firstNonSpace="true",
           endRegion="env")
        rx(x_, r"\|end" + NOT_ID, "BlockCmd", None, firstNonSpace="true",
           endRegion="env")
        # структурные формы начала строки
        rx(x_, r"\|<+", "HeadingMarker", "HeadingAfterMarker", firstNonSpace="true")
        rx(x_, r"\|>+", "StructMarker", "AfterMarker", firstNonSpace="true")
        rx(x_, r"\|[-#]+", "StructMarker", "AfterMarker", firstNonSpace="true")
        rx(x_, r"\|!", "StructMarker", "AfterMarker", firstNonSpace="true")
        rx(x_, r"\|:", "StructMarker", "AfterMarker", firstNonSpace="true")
        rx(x_, r"\|def(?=[ \t])", "ControlFlow", "DefName", firstNonSpace="true")
        inc(x_, "InlineRules")
    context(x, "Body", "Normal", body)


def add_block_contexts(x):
    """|code: |comment: |verbatim: — «открывающая строка» и тело до |end."""
    def opener(target):
        def body(x_):
            rx(x_, r"\|%.*$", "Comment")
            rx(x_, r"[ \t]+", "Normal")
        return body

    for nm, tgt in (("OpenCode", "CodeBlock"), ("OpenComment", "CommentBlock"),
                    ("OpenVerbatim", "VerbatimBlock")):
        context(x, nm, "Error", opener(tgt), lineEnd="#pop!" + tgt)

    end_rx = r"[ \t]*\|end" + TAIL_OK

    def code(x_):
        rx(x_, end_rx, "BlockCmd", "#pop", column="0", endRegion="env")
        rx(x_, r"#.*$", "PyComment")
        inc(x_, "PyRules")
        rx(x_, r"[()]", "PyOperator")

    def comment(x_):
        rx(x_, end_rx, "BlockCmd", "#pop", column="0", endRegion="env")
        inc(x_, "##Alerts")

    def verb(x_):
        rx(x_, end_rx, "BlockCmd", "#pop", column="0", endRegion="env")

    def verb_dyn(x_):
        # маркер сравнивается буквально, комментарий после него недопустим
        rx(x_, r"[ \t]*%1$", "BlockCmd", "#pop", column="0", dynamic="true",
           endRegion="env")

    context(x, "CodeBlock", "CodeText", code)
    context(x, "CommentBlock", "CommentText", comment)
    context(x, "VerbatimBlock", "Verbatim", verb)
    context(x, "VerbatimDyn", "Verbatim", verb_dyn, dynamic="true")

    def line_comment(x_):
        inc(x_, "##Alerts")
    context(x, "LineComment", "Comment", line_comment, lineEnd="#pop")


# =============================================================================
# Заголовок YAML (упрощённо)
# =============================================================================
def add_header(x, name, next_ctx, code_detect):
    """Контекст заголовка. next_ctx — куда идти после закрывающего «---».
    code_detect — реагировать ли на «kind: styles|project» (переход в
    HeaderCode, где после заголовка начинается код)."""
    known = (r"(?<![\p{L}\p{N}_\-])" + alt(L.HEADER_KEYS)
             + r"(?=[ \t]*:(?:[ \t]|$))")

    def body(x_):
        rx(x_, r"---[ \t]*$", "HeaderDelim", "#pop!" + next_ctx, column="0",
           endRegion="header")
        rx(x_, r"(?:^|(?<=[ \t]))#.*$", "HeaderComment")
        if code_detect:
            rx(x_, r"(?<![\p{L}\p{N}_\-])kind[ \t]*:[ \t]*[\"']?"
               + alt(L.CODE_KINDS) + NOT_ID + r"[\"']?",
               "HeaderKnownKey", "#pop!HeaderCode")
        rx(x_, known, "HeaderKnownKey")
        rx(x_, r"[\p{L}\p{N}_][\p{L}\p{N}_ .\-]*?(?=[ \t]*:(?:[ \t]|$))", "HeaderKey")
        rx(x_, '"', "HeaderString", "HStrDQ")
        rx(x_, "'", "HeaderString", "HStrSQ")
        rx(x_, r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?)?(?![\p{L}\p{N}_])",
           "HeaderNumber")
        rx(x_, r"(?<![\p{L}\p{N}_.\-])[-+]?\d[\d_]*(?:\.\d+)?(?![\p{L}\p{N}_])",
           "HeaderNumber")
        rx(x_, r"(?<![\p{L}\p{N}_])(?:true|false|null)(?![\p{L}\p{N}_])|~",
           "HeaderConst")
        rx(x_, r"^[ \t]*-(?=[ \t])|[:,\[\]{}]", "HeaderPunct")
    context(x, name, "HeaderValue", body)


def add_header_strings(x):
    context(x, "HStrDQ", "HeaderString",
            lambda x_: (rx(x_, r"\\.", "PyEscape"), ch(x_, '"', "HeaderString", "#pop")),
            lineEnd="#pop")
    context(x, "HStrSQ", "HeaderString",
            lambda x_: (rx(x_, r"''", "PyEscape"), ch(x_, "'", "HeaderString", "#pop")),
            lineEnd="#pop")


def add_code_body(x):
    """Тело файлов вида styles/project: код подмножества Python, комментарии «#»."""
    def body(x_):
        rx(x_, r"#.*$", "PyComment")
        inc(x_, "PyRules")
        rx(x_, r"[()]", "PyOperator")
    context(x, "CodeBody", "CodeText", body)


# =============================================================================
# Сборка документа
# =============================================================================
def lists(x):
    for name, words in (("pykeywords", L.PY_KEYWORDS), ("pyconsts", L.PY_CONSTS),
                        ("pyforbidden", L.PY_FORBIDDEN),
                        ("pybuiltins", L.PY_BUILTINS), ("pystdlib", L.PY_STDLIB)):
        x.open(f'<list name="{name}">')
        for w in words:
            x.add(f"<item>{w}</item>")
        x.close("</list>")


def debug_color(i):
    """Уникальный цвет атрибута №i для отладочной сборки (kate_dump.py)."""
    return "#%02x%02x%02x" % (20 + i * 4, (i * 53 + 30) % 200 + 20, (i * 97 + 60) % 200 + 20)


def itemdatas(x, debug=False):
    x.open("<itemDatas>")
    for i, (name, num, spell, extra) in enumerate(ITEMS):
        if debug:   # без начертаний: важен только цвет
            x.add("<itemData " + attrs(name=name, defStyleNum=num,
                                       color=debug_color(i)) + "/>")
            continue
        x.add("<itemData " + attrs(name=name, defStyleNum=num,
                                   spellChecking=None if spell else "false",
                                   **extra) + "/>")
    x.close("</itemDatas>")


def build(code_variant, debug=False):
    """Возвращает текст XML. code_variant=True — язык «Primula (код)»."""
    x = Xml()
    x.add('<?xml version="1.0" encoding="UTF-8"?>')
    x.add("<!-- Сгенерировано gen_kate.py — не править вручную. "
          "Спецификация: Primula v1.1-draft. -->")
    x.add("<!DOCTYPE language SYSTEM \"language.dtd\">")
    if code_variant:
        lang = dict(name="Primula (code)", section="Markup",
                    extensions="*.s.prml;*.p.prml", priority="5")
    else:
        lang = dict(name="Primula", section="Markup", extensions="*.prml",
                    priority="0")
    x.open("<language " + attrs(version="1", kateversion="5.0", casesensitive="true",
                                mimetype="text/x-primula", author="Primula project", **lang) + ">")
    x.open("<highlighting>")
    lists(x)
    x.open("<contexts>")

    if code_variant:
        # без заголовка весь файл — код
        context(x, "Start", "Normal",
                lambda x_: rx(x_, r"---[ \t]*$", "HeaderDelim", "#pop!HeaderCode",
                              column="0", beginRegion="header"),
                lineEnd="#pop!CodeBody", lineEmpty="#pop!CodeBody",
                fallthrough="#pop!CodeBody")
        add_header(x, "HeaderCode", "CodeBody", False)
    else:
        context(x, "Start", "Normal",
                lambda x_: rx(x_, r"---[ \t]*$", "HeaderDelim", "#pop!HeaderMk",
                              column="0", beginRegion="header"),
                lineEnd="#pop!Body", lineEmpty="#pop!Body", fallthrough="#pop!Body")
        add_header(x, "HeaderMk", "Body", True)
        add_header(x, "HeaderCode", "CodeBody", False)
    add_header_strings(x)
    add_code_body(x)
    # PyRules — отдельный контекст-контейнер правил для IncludeRules
    context(x, "PyRules", "CodeText", py_rules)
    add_string_contexts(x)
    if not code_variant:
        add_body(x)
        add_inline_rules(x)
        add_after_contexts(x)
        add_inline_body_contexts(x)
        add_paren_contexts(x)
        add_block_contexts(x)
    x.close("</contexts>")
    itemdatas(x, debug)
    x.close("</highlighting>")
    x.open("<general>")
    x.add('<comments><comment name="singleLine" start="|% " position="afterwhitespace"/></comments>'
          if not code_variant else
          '<comments><comment name="singleLine" start="# " position="afterwhitespace"/></comments>')
    x.add('<keywords casesensitive="1" weakDeliminator="." additionalDeliminator=""/>')
    x.close("</general>")
    x.close("</language>")
    return x.text()


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    for fname, variant in (("primula.xml", False), ("primula-code.xml", True)):
        with open(os.path.join(out, fname), "w", encoding="utf-8") as f:
            f.write(build(variant))
        print("записан", os.path.join(out, fname))
