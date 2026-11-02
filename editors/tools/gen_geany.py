#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор geany/filetypes.Primula.conf: шаблон tools/geany.conf.in + список слов из словаря
(lexicon.json, то есть из справочника транслятора), чтобы новые команды (parallel, segment, track…)
попадали в подсветку Geany так же, как в остальные редакторы.

Geany подсвечивает слова лексером «Matlab/Octave» без регулярных выражений, поэтому слова,
часто встречающиеся в тексте и данных, в список не входят (DENY). Составные имена (field.page)
пропускаются: лексер видит три слова.

Запуск: python3 gen_geany.py <каталог_вывода>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prml_lexicon as L  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
#: Слова, которые нельзя выделять: они обычны в тексте и в полях данных.
DENY = {"code", "name", "list", "page", "section", "header", "footer", "link", "set", "block", "part",
        "scope", "index", "row", "cell", "caption", "call", "export", "document", "field"}
#: Слова подмножества Python (разд. 12.2), которые не конфликтуют с текстом.
PYTHON = ["return", "while", "break", "continue", "pass", "in", "not", "and", "or", "is", "None", "True", "False"]


def primary():
    words = list(L.CONTROL) + list(L.CONTROL_END) + ["end"] + list(L.MODULE_CMDS)
    words += [w for w in L.BUILTIN_CMDS if "." not in w and w not in DENY]
    words += PYTHON
    seen, result = set(), []
    for word in words:
        if word not in seen:
            seen.add(word)
            result.append(word)
    return " ".join(result)


def main(argv):
    out = argv[0] if argv else "geany"
    template = open(os.path.join(HERE, "geany.conf.in"), encoding="utf-8").read()
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "filetypes.Primula.conf")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(template.replace("@PRIMARY@", primary()))
    print("записан", path)


if __name__ == "__main__":
    main(sys.argv[1:])
