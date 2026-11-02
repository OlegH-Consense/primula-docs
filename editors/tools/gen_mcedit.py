#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор файлов подсветки Primula v1.1-draft для mcedit (Midnight Commander).

Порождает:
  mc/primula.syntax       — разметка (*.prml);
  mc/primula-code.syntax  — файлы с кодом после заголовка (*.s.prml, *.p.prml);
  mc/Syntax.prml          — строки `file`/`include` для вставки в Syntax.

Ограничения движка mcedit (учтены и отражены в README):
  * нет регулярных выражений, нет вложенных контекстов, нет просмотра вперёд;
    поэтому вложенные |*{ |/{ … } подсвечиваются до первой «}», а аргументы
    команд |имя(…) — до первой «)» (см. man mcedit, раздел SYNTAX HIGHLIGHTING);
  * linestart означает «сразу после перевода строки» — отступ перед блочной
    формой отключает подсветку этой формы (кроме |code:, |comment:, |verbatim:
    и закрывающих |end, у которых linestart не требуется);
  * шаблон `*` — «любые символы до следующего литерала, не пересекая строку»;
    `\\{abc\\}` — один символ из набора, `\\[abc\\]` — ноль или больше символов
    набора; `\\s` — пробел, `\\n` — перевод строки (см. man mcedit);
  * имена команд на кириллице не подсвечиваются (наборы символов — байтовые).
Источник правил: man mcedit; исходники mc, src/editor/syntax.c.

Запуск: python3 gen_mcedit.py mcedit
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prml_lexicon as L  # noqa: E402

LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# --- Цветовая схема (имена цветов mc, man mcedit) -------------------------------
C = dict(
    comment="brown",
    escape="magenta",
    heading="brightmagenta",
    marker="brightgreen",
    control="yellow",
    module="brightred",
    builtin="brightcyan",
    user="cyan",
    expr="green",
    string="green",
    const="brightred",
    pybuiltin="brightcyan",
    header="cyan",
    headerkey="brightcyan",
    verbatim="gray",
    error="white red",           # передний цвет + фон
    code="lightgray",
)


def esc(s):
    """Экранирование для строк mcedit: пробел → \\s, обратная косая → \\\\, '*' → \\*."""
    return (s.replace("\\", "\\\\").replace(" ", "\\s").replace("*", "\\*")
            .replace("+", "\\+"))


def python_rules(indent="  "):
    """Правила подмножества Python (ядро, разд. 12): ключевые слова, константы,
    встроенные функции, запрещённые слова-ошибки, строки и комментарии."""
    out = [f"{indent}# --- подмножество Python (разд. 12) ---",
           f"{indent}keyword #*\\n {C['comment']}"]            # комментарий до конца строки
    out += [f'{indent}keyword "*" {C["string"]}',
            f"{indent}keyword '*' {C['string']}"]
    for w in L.PY_FORBIDDEN:                                   # запрещено — ошибка
        out.append(f"{indent}keyword whole {w} {C['error']}")
    for w in L.PY_KEYWORDS:
        out.append(f"{indent}keyword whole {w} {C['control']}")
    for w in L.PY_CONSTS:
        out.append(f"{indent}keyword whole {w} {C['const']}")
    for w in L.PY_BUILTINS + L.PY_STDLIB:
        out.append(f"{indent}keyword whole {w} {C['pybuiltin']}")
    return out


def header_context():
    """YAML-заголовок между строками «---» (упрощённо)."""
    return [
        "# --- YAML-заголовок: от «---» до «---» (в начале файла) ---",
        f"context linestart --- linestart --- {C['header']}",
        f"  keyword +: {C['headerkey']}",
        f'  keyword "*" {C["string"]}',
        f"  keyword '*' {C['string']}",
        f"  keyword #*\\n {C['comment']}",
    ]


def markup_syntax():
    L_ = []
    a = L_.append
    a("# Подсветка Primula v1.1-draft для mcedit — сгенерировано gen_mcedit.py.")
    a("# Не править вручную: правится prml_lexicon.py / gen_mcedit.py.")
    a("# Ограничения движка mcedit: см. README (нет вложенности и регулярных выражений).")
    a("")
    a("# '.' слева от слова = атрибут (it.qty), а не отдельное имя функции")
    a("wholechars left " + LATIN + "_0123456789.")
    a("wholechars right " + LATIN + "_0123456789")
    a("")
    a("context default")
    # --- комментарий и экранирования -----------------------------------------
    a("  # экранирования (разд. 3.3)")
    for e in ("||", "|{", "|}", "|;", "|~", "|\\\\"):
        a(f"  keyword {e} {C['escape']}")
    # --- недопустимые формы -----------------------------------------------------
    a("  # недопустимые и зарезервированные формы — ошибка (разд. 3.1)")
    a(f"  keyword |\\s {C['error']}")
    for bad in ("|$", "|[", "|]", "|–", "|−"):      # – и − вместо —
        a(f"  keyword {bad} {C['error']}")
    # --- закрывающие маркеры (вся строка) ---------------------------------------
    a("  # закрывающие маркеры (разд. 3.5)")
    for w in L.CONTROL_END:
        a(f"  keyword whole linestart |{w} {C['control']}")
    a(f"  keyword linestart |end\\{{>!\\}}\\[>\\] {C['control']}")      # |end> |end>> |end!
    a(f"  keyword linestart |end.+ {C['control']}")                    # |end.Стиль
    a(f"  keyword linestart |end\\s+ {C['control']}")                   # |end имя
    a(f"  keyword whole linestart |end {C['control']}")
    # --- структурные формы начала строки ----------------------------------------
    a("  # заголовки: вся строка (внутристрочные формы внутри не различаются)")
    a(f"  keyword linestart |<*\\n {C['heading']}")
    a("  # пункты, списки, предупреждения, строки таблиц, ячейки")
    a(f"  keyword linestart |>\\[>\\] {C['marker']}")
    a(f"  keyword linestart |\\{{-#\\}}\\[-#\\] {C['marker']}")
    a(f"  keyword linestart |! {C['marker']}")
    a(f"  keyword linestart |: {C['marker']}")
    a(f"  keyword |& {C['marker']}")
    # --- управляющие -------------------------------------------------------------
    a("  # управляющие конструкции")
    a(f"  keyword linestart |.+: {C['user']}")        # |.Стиль: (абзацный стиль)
    a(f"  keyword whole |else {C['control']}")
    a(f"  keyword whole |def {C['control']}")
    a(f"  keyword whole |if {C['control']}")
    a(f"  keyword whole |elif {C['control']}")
    a(f"  keyword whole |for {C['control']}")
    # --- команды -----------------------------------------------------------------
    a("  # модульные и встроенные команды (до общего правила пользовательских)")
    for w in L.MODULE_CMDS:
        a(f"  keyword whole |{w} {C['module']}")
    for w in sorted(L.BUILTIN_CMDS, key=lambda s: -len(s)):
        a(f"  keyword whole |{w} {C['builtin']}")
    a(f"  keyword whole |field.+ {C['builtin']}")
    a("  # команда пользователя/модуля: |имя, |модуль.имя (только латиница)")
    a(f"  keyword whole |\\{{{LATIN}\\}}\\[{LATIN}_0123456789.\\] {C['user']}")
    a("")
    # ----------------------------------------------------------------------------
    a("# --- комментарий |% до конца строки ---")
    a(f"context |% \\n {C['comment']}")
    a("")
    a("# --- блоки до |end ---")
    a(f"context exclusive whole |code: |end {C['code']}")
    for l in python_rules("  "):
        a(l)
    a(f"context exclusive whole |comment: linestart |end {C['comment']}")
    a(f"context exclusive whole |verbatim: linestart |end {C['verbatim']}")
    a(f"context exclusive whole |verbatim(end=\"EOF\"): linestart EOF {C['verbatim']}")
    a(f"context exclusive whole |verbatim(end=\"END\"): linestart END {C['verbatim']}")
    a("")
    a("# --- выражения |( … ) и формулы |=( … ) ---")
    a(f"context |( ) {C['expr']}")
    a(f"context |=( ) {C['expr']}")
    a("")
    a("# --- аргументы встроенных и управляющих команд |имя( … ) ---")
    for w in ["if", "elif", "for"] + L.MODULE_CMDS + L.BUILTIN_CMDS:
        if w in ("code", "comment", "verbatim"):
            continue
        a(f"context exclusive |{w}( ) {C['expr']}")
    a("")
    a("# --- внутристрочные формы: тело {…} до первой «}» (без вложенности) ---")
    a(f"context |\\*{{ }} white base bold")
    a(f"context |/{{ }} lightgray base italic")
    a(f"context |_{{ }} lightgray base underline")
    a(f"context |^{{ }} cyan")
    a(f"context |,{{ }} cyan")
    a(f"context |—{{ }} gray")
    a(f"context |`{{ }} brightgreen")
    a(f"context |\"{{ }} green")
    a(f"context |?{{ }} white red")
    a(f"context |.+{{ }} brightcyan")
    a("")
    a("# --- YAML-заголовок ---")
    for l in header_context():
        a(l)
    return "\n".join(L_) + "\n"


def code_syntax():
    """Файлы styles/project: заголовок YAML, затем код Python-подмножества."""
    out = ["# Подсветка Primula (файлы с кодом: *.s.prml, *.p.prml) для mcedit.",
           "# Сгенерировано gen_mcedit.py.", "",
           "context default"]
    out += python_rules("  ")
    out.append("")
    out += header_context()
    return "\n".join(out) + "\n"


def syntax_entries():
    return (
        "# Primula v1.1-draft: добавить ПЕРЕД универсальной записью «Unknown» в Syntax.\n"
        "# Порядок важен: побеждает первая подходящая запись.\n"
        "file ..\\*\\\\.[sp]\\\\.prml$ Primula\\scode\\sfile\n"
        "include primula-code.syntax\n\n"
        "file ..\\*\\\\.prml$ Primula\\sdocument\n"
        "include primula.syntax\n"
    )


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    for name, text in (("primula.syntax", markup_syntax()),
                       ("primula-code.syntax", code_syntax()),
                       ("Syntax.prml", syntax_entries())):
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(text)
        print("записан", os.path.join(out, name))
