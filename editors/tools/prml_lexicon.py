# -*- coding: utf-8 -*-
"""
Общий словарь лексики Primula v1.1-draft для генераторов подсветки.

Назначение: единый источник списков слов (встроенные команды, ключи заголовка,
функции ядра и стандартной библиотеки), чтобы определения для Kate, mcedit
и др. редакторов не расходились между собой. При изменении спецификации
правится только этот файл, затем перезапускаются генераторы.

Источник: primula-spec-v1.1-draft.ru.md (разд. 2.3, 3, 10.6, 11.1, 12, прил. 2),
primula-stdlib-v1.1-draft.ru.md, primula-grammar-v1.1.ebnf.
"""

# --- Команды разметки (прил. 2.1 спецификации) --------------------------------

# Управляющие конструкции: после «|» образуют ControlFlow.
# end* обрабатываются отдельно (закрывающие маркеры строки).
CONTROL = ["if", "elif", "else", "for", "def"]

# Закрывающие маркеры управляющих конструкций (|endif, |endfor, |enddef).
CONTROL_END = ["endif", "endfor", "enddef"]

# Команды подключения файлов (раздел 10).
MODULE_CMDS = ["include", "import"]

# Прочие встроенные команды, ключи заголовка и функции — из справочника транслятора
# (lexicon.json, обновляется tools/sync_lexicon.py; тест проекта сверяет файл со справочником).
import json as _json
import os as _os

with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "lexicon.json"), encoding="utf-8") as _f:
    _LEXICON = _json.load(_f)

BUILTIN_CMDS = _LEXICON["builtin_cmds"]

# --- Заголовок YAML (разд. 2.3, 10.6, 11.1) ----------------------------------

# Предопределённые ключи заголовка (на любом уровне вложенности — для простоты подсветки).
HEADER_KEYS = _LEXICON["header_keys"]

# Значения kind, после заголовка которых идёт КОД, а не разметка (разд. 2.2).
CODE_KINDS = ["styles", "project"]

# --- Вычислительное ядро (разд. 12) ------------------------------------------

# Разрешённые ключевые слова Python-подмножества (разд. 12.2).
PY_KEYWORDS = [
    "and", "or", "not", "in", "is", "if", "elif", "else", "for", "while",
    "break", "continue", "pass", "return", "def",
]

# Константы.
PY_CONSTS = ["None", "True", "False"]

# Запрещённые конструкции (разд. 12.2): подсвечиваются как ошибка.
PY_FORBIDDEN = [
    "class", "import", "from", "try", "except", "raise", "with", "global",
    "nonlocal", "del", "lambda", "yield", "async", "await", "match", "finally",
    "assert",
]

# Встроенные функции и константы ядра (разд. 12.10) и функции стандартной библиотеки,
# включая std/math — из справочника транслятора.
PY_BUILTINS = _LEXICON["py_builtins"]
PY_STDLIB = _LEXICON["py_stdlib"]
