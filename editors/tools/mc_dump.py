#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Снимок подсветки mcedit: запускает mcedit в tmux, делает capture-pane с
SGR-последовательностями и печатает строки как «{fg:bg}текст» по сменам цвета.
Нужен для проверки определения без графической оболочки (режим 256 цветов).

Запуск: mc_dump.py <HOME_для_mc> <файл> [высота]
HOME_для_mc должен содержать .local/share/mc/syntax/{Syntax,*.syntax}.
"""
import os, re, subprocess, sys, time

home, path = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
rows = int(sys.argv[3]) if len(sys.argv) > 3 else 60
sock = "mcdump%d" % os.getpid()
env = dict(os.environ, HOME=home, TERM="xterm-256color", LANG="C.UTF-8",
           XDG_DATA_HOME="", XDG_CONFIG_HOME="")
env.pop("XDG_DATA_HOME"); env.pop("XDG_CONFIG_HOME")
subprocess.run(["tmux", "-L", sock, "new-session", "-d", "-x", os.environ.get("MCW", "140"), "-y", str(rows),
                "mcedit " + path], env=env, check=True)
time.sleep(1.5)
out = subprocess.run(["tmux", "-L", sock, "capture-pane", "-p", "-e"],
                     capture_output=True, text=True).stdout
subprocess.run(["tmux", "-L", sock, "kill-server"], capture_output=True)
for ln, line in enumerate(out.split("\n"), 1):
    res, fg, bg, attr = "", "", "", ""
    cur = None
    for m in re.finditer(r"\x1b\[([0-9;]*)m|([^\x1b]+)", line):
        if m.group(2) is None:
            codes = (m.group(1) or "0").split(";")
            j = 0
            while j < len(codes):
                c = codes[j]
                if c in ("0", ""): fg = bg = attr = ""
                elif c == "38" and codes[j+1] == "5": fg = codes[j+2]; j += 2
                elif c == "48" and codes[j+1] == "5": bg = codes[j+2]; j += 2
                elif c in ("1", "3", "4", "7"): attr += {"1": "b", "3": "i", "4": "u", "7": "r"}[c]
                elif c in ("22", "23", "24", "27"): attr = ""
                elif 30 <= int(c) <= 37: fg = str(int(c) - 30)
                elif 90 <= int(c) <= 97: fg = str(int(c) - 90 + 8)
                elif 40 <= int(c) <= 47: bg = str(int(c) - 40)
                j += 1
        else:
            key = "%s:%s%s" % (fg, bg, ("/" + attr) if attr else "")
            if key != cur:
                res += "{%s}" % key
                cur = key
            res += m.group(2)
    print("%2d|%s" % (ln, res))
