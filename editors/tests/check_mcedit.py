#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автопроверка mcedit: запускает mcedit в tmux (tools/mc_dump.py) и проверяет
индексы цветов (256-цветный режим, скин по умолчанию) у характерных строк.
Нужны: mc (mcedit), tmux. Запуск (из корня пакета): python3 tests/check_mcedit.py
"""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
subprocess.run([os.path.join(ROOT, "tools", "mc_sync.sh")], check=True)
out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "mc_dump.py"),
                      os.path.join(ROOT, ".home"), os.path.join(ROOT, "tests", "sample.prml"), "140"],
                     capture_output=True, text=True, check=True, env=dict(os.environ, MCW="170")).stdout
# индексы палитры: 3 brown, 5 magenta, 10 brightgreen, 11 yellow, 13 brightmagenta, 14 brightcyan
checks = [
    ("{3:}|% Тестовий", "комментарий |%"),
    ("{14:}|code:", "открытие блока кода"),
    ("{11:}def{7:} with_tax", "ключевое слово в |code:"),
    ("{13:}|<(id=\"subject\")", "заголовок"),
    ("{10:}|>", "пункт"),
    ("{15:/b}|*{жирним}", "полужирный"),
    ("{11:}|endif", "закрытие |if"),
    ("{15:1}|–", "ошибка: en dash"),
]
fails = [w for frag, w in checks if frag not in out]
if fails:
    print("ОШИБКИ mcedit:", fails); sys.exit(1)
print("mcedit: все проверки пройдены")
