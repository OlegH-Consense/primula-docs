#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор подсветки Primula для VS Code (грамматика TextMate, Oniguruma).

Порождает каталог расширения vscode/:
  package.json, language-configuration.json,
  syntaxes/primula.tmLanguage.json       — документы, фрагменты, модули (*.prml);
  syntaxes/primula-code.tmLanguage.json  — файлы с кодом после заголовка (*.s.prml, *.p.prml).
Грамматика TextMate подходит и другим редакторам на движке TextMate (JetBrains, Sublime Text
с преобразованием, Atom-подобные). Слова — из prml_lexicon.py (lexicon.json).

Ограничения: TextMate не знает номера строки и вложенности произвольной глубины; выражения
в скобках разбираются как упрощённое подмножество Python (строки, числа, слова ядра).
Не проверялось в самом VS Code (нет окна); структура и регулярные выражения проверяются
тестом проекта (tests/test_editors.py).

Запуск: python3 gen_textmate.py <каталог_вывода>
Ссылки: https://macromates.com/manual/en/language_grammars,
        https://code.visualstudio.com/api/language-extensions/syntax-highlight-guide
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prml_lexicon as L  # noqa: E402

ID = r"[\p{L}_][\p{L}\p{N}_]*"
NOT_ID = r"(?![\p{L}\p{N}_])"


def alt(words):
    """Альтернатива слов: длинные первыми, точки экранированы."""
    return "|".join(w.replace(".", r"\.") for w in sorted(set(words), key=lambda w: (-len(w), w)))


def python_rules():
    """Упрощённое подмножество Python: комментарии, строки, числа, слова ядра."""
    return {
        "patterns": [
            {"name": "comment.line.number-sign.primula", "match": r"#.*$"},
            {"name": "string.quoted.triple.primula", "begin": r'[fFrR]?"""', "end": r'"""'},
            {"name": "string.quoted.triple.primula", "begin": r"[fFrR]?'''", "end": r"'''"},
            {"name": "string.quoted.double.primula", "match": r'[fFrR]?"(?:[^"\\\n]|\\.)*"'},
            {"name": "string.quoted.single.primula", "match": r"[fFrR]?'(?:[^'\\\n]|\\.)*'"},
            {"name": "constant.numeric.primula", "match": r"(?<![\p{L}\p{N}_])\d[\d_]*(?:\.\d+)?(?![\p{L}\p{N}_])"},
            {"name": "constant.language.primula", "match": r"(?<![\p{L}\p{N}_])(?:" + alt(L.PY_CONSTS) + r")" + NOT_ID},
            {"name": "invalid.illegal.forbidden.primula",
             "match": r"(?<![\p{L}\p{N}_])(?:" + alt(L.PY_FORBIDDEN) + r")" + NOT_ID},
            {"match": r"(?<![\p{L}\p{N}_])(def)\s+(" + ID + ")",
             "captures": {"1": {"name": "keyword.control.primula"}, "2": {"name": "entity.name.function.primula"}}},
            {"name": "keyword.control.primula", "match": r"(?<![\p{L}\p{N}_])(?:" + alt(L.PY_KEYWORDS) + r")" + NOT_ID},
            {"name": "support.function.builtin.primula",
             "match": r"(?<![\p{L}\p{N}_.])(?:" + alt(L.PY_BUILTINS + L.PY_STDLIB) + r")(?=\s*\()"},
            {"name": "keyword.operator.primula", "match": r":=|[-+*/%<>=!]=?|//|\*\*"},
        ]
    }


def parens():
    return {"begin": r"\(", "end": r"\)", "patterns": [{"include": "#python"}, {"include": "#parens"}]}


def markup_rules():
    inline = []
    for mark, scope in (("*", "markup.bold"), ("/", "markup.italic"), ("_", "markup.underline"),
                        ("^", "markup.inline"), (",", "markup.inline"), ("—", "markup.strikethrough"),
                        ("`", "markup.inline.raw"), ('"', "markup.quote"), ("?", "markup.placeholder")):
        inline.append({"name": scope + ".primula", "begin": r"(\|" + ("\\" + mark if mark in "*^?_," else mark) + r")(\{)",
                       "end": r"\}", "beginCaptures": {"1": {"name": "keyword.operator.inline.primula"}},
                       "patterns": [{"include": "#markup"}]})
    args = [{"include": "#python"}, {"include": "#parens"}]
    return {
        "patterns": [
            {"name": "comment.line.primula", "match": r"\|%.*$"},
            {"name": "comment.block.primula", "begin": r"^\|comment(?:\([^)]*\))?:[ \t]*$", "end": r"^\|end\b.*$"},
            {"begin": r"^(\|code):[ \t]*$", "end": r"^(\|end)[ \t]*$", "contentName": "meta.embedded.block.python",
             "beginCaptures": {"1": {"name": "keyword.control.primula"}},
             "endCaptures": {"1": {"name": "keyword.control.primula"}}, "patterns": [{"include": "#python"}]},
            {"name": "string.unquoted.verbatim.primula", "begin": r'^\|verbatim\(end="([^"]+)"\):[ \t]*$',
             "end": r"^\1[ \t]*$"},
            {"name": "string.unquoted.verbatim.primula", "begin": r"^\|verbatim:[ \t]*$", "end": r"^\|end[ \t]*$"},
            {"name": "constant.character.escape.primula", "match": r"\|[|{};~\\]"},
            {"name": "invalid.illegal.primula", "match": r"\|(?:[ \t0-9$\[\]–−]|$)"},
            {"name": "markup.heading.marker.primula", "match": r"^\|<{1,6}"},
            {"name": "keyword.control.structure.primula", "match": r"^\|(?:>+|[-#!:])"},
            {"name": "keyword.control.structure.primula", "match": r"\|&"},
            {"name": "entity.name.tag.style.primula", "match": r"\|\.[\p{L}_][\p{L}\p{N}_\-]*"},
            {"name": "keyword.control.end.primula",
             "match": r"\|end(?:if|for|def|[>!]|\.[\p{L}][\p{L}\p{N}_\-]*|[ \t]+" + ID + r")?" + NOT_ID},
            {"name": "keyword.control.primula", "match": r"\|(?:" + alt(L.CONTROL) + r")" + NOT_ID},
            {"name": "keyword.control.import.primula", "match": r"\|(?:" + alt(L.MODULE_CMDS) + r")" + NOT_ID},
            *inline,
            {"begin": r"(\|=?)(\()", "end": r"\)", "beginCaptures": {"1": {"name": "keyword.operator.primula"}},
             "contentName": "meta.embedded.expression.python", "patterns": args},
            {"begin": r"(\|(?:" + alt(L.BUILTIN_CMDS) + r"))(\()", "end": r"\)",
             "beginCaptures": {"1": {"name": "support.function.command.primula"}}, "patterns": args},
            {"name": "support.function.command.primula", "match": r"\|(?:" + alt(L.BUILTIN_CMDS) + r")" + NOT_ID},
            {"begin": r"(\|" + ID + r"(?:\." + ID + r")*)(\()", "end": r"\)",
             "beginCaptures": {"1": {"name": "entity.name.function.user.primula"}}, "patterns": args},
            {"name": "entity.name.function.user.primula", "match": r"\|" + ID + r"(?:\." + ID + r")*"},
        ]
    }


def grammar(scope, code_after_header):
    repository = {"markup": markup_rules(), "python": python_rules(), "parens": parens(),
                  "header": {"name": "meta.header.primula", "begin": r"\A---[ \t]*$", "end": r"^---[ \t]*$",
                             "patterns": [{"include": "source.yaml"}]}}
    top = [{"include": "#header"}, {"include": "#python" if code_after_header else "#markup"}]
    return {"$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
            "name": "Primula (code)" if code_after_header else "Primula", "scopeName": scope,
            "patterns": top, "repository": repository}


def extension_files():
    return {
        "package.json": {
            "name": "primula", "displayName": "Primula", "description": "Syntax highlighting for Primula documents (.prml)",
            "version": "0.1.0", "publisher": "primula-docs", "license": "Apache-2.0",
            "engines": {"vscode": "^1.60.0"}, "categories": ["Programming Languages"],
            "contributes": {
                "languages": [
                    {"id": "primula", "aliases": ["Primula", "primula"], "extensions": [".prml"],
                     "configuration": "./language-configuration.json"},
                    {"id": "primula-code", "aliases": ["Primula (code)"], "filenamePatterns": ["*.s.prml", "*.p.prml"],
                     "configuration": "./language-configuration.json"}],
                "grammars": [
                    {"language": "primula", "scopeName": "source.primula", "path": "./syntaxes/primula.tmLanguage.json"},
                    {"language": "primula-code", "scopeName": "source.primula-code",
                     "path": "./syntaxes/primula-code.tmLanguage.json"}]}},
        "language-configuration.json": {
            "comments": {"lineComment": "|%"},
            "brackets": [["(", ")"], ["{", "}"], ["[", "]"]],
            "autoClosingPairs": [["(", ")"], ["{", "}"], ["[", "]"], {"open": "\"", "close": "\"", "notIn": ["comment"]}],
            "surroundingPairs": [["(", ")"], ["{", "}"], ["[", "]"], ["\"", "\""]]},
        "syntaxes/primula.tmLanguage.json": grammar("source.primula", False),
        "syntaxes/primula-code.tmLanguage.json": grammar("source.primula-code", True),
    }


def main(argv):
    out = argv[0] if argv else "vscode"
    for name, data in extension_files().items():
        path = os.path.join(out, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        print("записан", path)


if __name__ == "__main__":
    main(sys.argv[1:])
