#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладочный дамп подсветки Kate: показывает для каждого фрагмента текста имя
атрибута (itemData), а не цвет.

Как работает: gen_kate.build(debug=True) даёт каждому атрибуту уникальный цвет;
kate-syntax-highlighter выводит текст в формате ansi (24-битный цвет);
скрипт сопоставляет цвет → имя атрибута и печатает «[Имя]текст» по строкам.
Нужен для регрессионной проверки определения без графической оболочки.

Запуск: kate_dump.py <primula|primula-code> <файл> [с_строки [по_строку]]
"""
import os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_kate as G  # noqa: E402

def main():
    variant, path = sys.argv[1], sys.argv[2]
    lo = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    hi = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
    code = variant.endswith("code")
    colors = {G.debug_color(i): n for i, (n, *_r) in enumerate(G.ITEMS)}
    rgb = {tuple(int(c[k:k+2], 16) for k in (1, 3, 5)): n for c, n in colors.items()}
    with tempfile.TemporaryDirectory() as td:
        d = os.path.join(td, "org.kde.syntax-highlighting", "syntax")
        os.makedirs(d)
        open(os.path.join(d, "x.xml"), "w", encoding="utf-8").write(G.build(code, True))
        env = dict(os.environ, XDG_DATA_HOME=td)
        name = "Primula (code)" if code else "Primula"
        # Имя программы зависит от дистрибутива и версии KDE Frameworks (5 или 6).
        tool = next((t for t in ("ksyntaxhighlighter6", "kate-syntax-highlighter6", "kate-syntax-highlighter", "ksyntaxhighlighter5",
                                 "kate-syntax-highlighter5") if shutil.which(t)), None)
        if tool is None:
            sys.exit("ksyntaxhighlighter6 / kate-syntax-highlighter не найден (пакет kate или KDE Frameworks syntax-highlighting)")
        run = subprocess.run([tool, "-s", name, "-f", "ansi", "-t", "Breeze Light", path], env=env,
                             capture_output=True, text=True)
        if run.returncode != 0 or not run.stdout:
            sys.exit("%s завершился с кодом %d: %s" % (tool, run.returncode, (run.stderr or "").strip()))
        out = run.stdout
    for ln, line in enumerate(out.split("\n"), 1):
        if ln < lo or ln > hi:
            continue
        cur, res, pos = None, "", 0
        for m in re.finditer(r"\x1b\[([0-9;]*)[mK]|([^\x1b]+)", line):
            if m.group(2) is None:
                mm = re.match(r"38;2;(\d+);(\d+);(\d+)", m.group(1) or "")
                if mm:
                    cur = rgb.get(tuple(map(int, mm.groups())), "?%s" % m.group(1))
            else:
                t = m.group(2)
                if t:
                    res += "[%s]%s" % (cur, t)
        print("%3d| %s" % (ln, res))

main()
