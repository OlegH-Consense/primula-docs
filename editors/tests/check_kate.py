#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автопроверка определений Kate: сверяет атрибуты токенов (через kate_dump.py)
с ожидаемыми на tests/sample.prml и вспомогательных файлах.
Запуск (из корня пакета): python3 tests/check_kate.py
Код возврата 0 — все проверки пройдены.
"""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def dump(variant, name):
    run = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "kate_dump.py"),
                          variant, os.path.join(ROOT, "tests", name)],
                         capture_output=True, text=True)
    if run.returncode != 0:
        sys.exit("kate_dump.py: " + (run.stderr.strip().splitlines() or ["ошибка без сообщения"])[-1])
    return run.stdout.split("\n")

fails = []
def expect(lines, fragment, why):
    if not any(fragment in l for l in lines):
        fails.append("нет фрагмента %r — %s" % (fragment, why))

s = dump("primula", "sample.prml")
for frag, why in [
    ("[HeaderDelim]---", "границы YAML-заголовка"),
    ("[HeaderKnownKey]kind", "предопределённый ключ заголовка"),
    ("[Comment]|% Тестовий", "строчный комментарий"),
    ("[BlockCmd]|code:", "открытие блока кода"),
    ("[PyKeyword]for", "ключевое слово ядра в |code:"),
    ("[CommentText]Блоковий коментар", "тело |comment:"),
    ("[HeadingMarker]|<<", "заголовок 2 уровня"),
    ("[Heading] Підрозділ", "текст заголовка"),
    ("[StructMarker]|>", "пункт"),
    ("[InlineBold]жирним", "|*{…}"),
    ("[InlineItalic]курсивом", "|/{…}"),
    ("[InlineStrike]закресленим", "|—{…}"),
    ("[InlineSub]2", "|,{…}"),
    ("[InlinePlaceholder]УТОЧНИТИ", "|?{…}"),
    ("[Escape]|~", "неразрывный пробел"),
    ("[UserCmd]|seller[Escape]|;", "разделитель |;"),
    ("[ControlFlow]|endif", "закрытие |if"),
    ("[DefName]signature", "имя макроса"),
    ("[BuiltinCmd]|field.page", "команда с точкой"),
    ("[StructMarker]|&", "ячейка таблицы"),
    ("[ExprDelim]|=(", "формула ячейки"),
    ("[Verbatim]Тут можна писати |end без закриття.", "|verbatim(end=…)"),
    ("[BlockCmd]EOF", "собственный маркер конца"),
]:
    expect(s, frag, why)
# Error — только на трёх заведомо неверных строках файла
bad = [l for l in s if "[Error]" in l]
if len(bad) != 3:
    fails.append("ожидалось 3 строки с [Error], получено %d: %r" % (len(bad), bad))

t1 = dump("primula", "t1.prml")          # нет заголовка: «---» в строке 3 — обычный текст
expect(t1, "[Normal]--- не заголовок", "«---» вне первой строки не открывает заголовок")
t2 = dump("primula", "t2.prml")          # kind: styles → после заголовка код
expect(t2, "[Error]class", "запрещённое слово в коде styles")
expect(t2, "[PyComment]# код, не разметка", "комментарий # в коде")
t3 = dump("primula-code", "t3.s.prml")   # вариант «код»
expect(t3, "[Error]lambda", "запрещённое слово")
t4 = dump("primula", "t4.prml")          # блоки с отступом
expect(t4, "[BlockCmd]  |end", "|end с отступом закрывает |code:")

if fails:
    print("ОШИБКИ:\n  " + "\n  ".join(fails)); sys.exit(1)
print("Kate: все проверки пройдены")
