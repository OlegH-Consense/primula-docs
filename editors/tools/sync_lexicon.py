#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Синхронизация словаря подсветки с транслятором: tools/lexicon.json.

Назначение: списки команд, ключей заголовка и функций берутся из справочника
самого транслятора (`primula commands --format json --lang en`), а не пишутся
вручную, поэтому подсветка не отстаёт от языка. Статичны только слова,
определяемые грамматикой (управляющие конструкции, ключевые слова подмножества
Python) — они лежат в prml_lexicon.py.

Использование:
  python3 tools/sync_lexicon.py            # переписать lexicon.json
  python3 tools/sync_lexicon.py --check    # код 1, если файл устарел
Транслятор: PRIMULA (команда) или ../primula исходного дерева; из проекта
(pytest) вызывается build_lexicon() с готовым справочником.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "lexicon.json")

#: Команды, которыми управляет грамматика (prml_lexicon.py): в BUILTIN_CMDS не входят.
GRAMMAR_COMMANDS = {"if", "elif", "else", "for", "def", "include", "import"}


def build_lexicon(catalogue):
    """Словарь подсветки по справочнику транслятора.

    Args:
        catalogue: результат `primula commands --format json` (dict).

    Returns:
        dict: builtin_cmds, py_builtins, py_stdlib, header_keys (отсортированные списки;
        номер версии не пишется, чтобы файл менялся только при изменении языка).
    """
    commands = sorted({c["name"] for c in catalogue["commands"]} - GRAMMAR_COMMANDS)
    builtins, stdlib = set(), set()
    for f in catalogue["functions"]:
        if f["kind"] == "method":                 # методы строк и списков вызываются после точки
            continue
        (stdlib if f["doc"] == "stdlib" else builtins).add(f["name"])
    keys = set()
    for entry in catalogue["header_keys"]:        # "targets[].source" -> targets, source
        for part in entry["path"].replace("[]", "").split("."):
            keys.add(part)
    return {"builtin_cmds": commands,
            "py_builtins": sorted(builtins), "py_stdlib": sorted(stdlib - builtins),
            "header_keys": sorted(keys)}


def run_translator():
    """Справочник из транслятора (подпроцесс)."""
    command = os.environ.get("PRIMULA")
    argv = command.split() if command else [os.path.join(HERE, "..", "..", "primula")]
    out = subprocess.run(argv + ["commands", "--format", "json", "--lang", "en"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def render(lexicon):
    return json.dumps(lexicon, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    text = render(build_lexicon(run_translator()))
    if "--check" in argv:
        current = open(TARGET, encoding="utf-8").read() if os.path.exists(TARGET) else ""
        if current != text:
            print("lexicon.json устарел: запустите tools/sync_lexicon.py", file=sys.stderr)
            return 1
        return 0
    with open(TARGET, "w", encoding="utf-8") as handle:
        handle.write(text)
    print("written", TARGET)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
