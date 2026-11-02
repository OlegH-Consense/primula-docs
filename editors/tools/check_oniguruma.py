#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка регулярных выражений грамматик TextMate настоящим Oniguruma (libonig через ctypes):
каждое "match", "begin", "end" должно компилироваться тем же движком, что в VS Code.
Запуск: python3 tools/check_oniguruma.py vscode/syntaxes/*.json   (нужна libonig.so.5, пакет oniguruma)
Код возврата 1 — есть непроходящие выражения; 77 — библиотеки нет (проверка пропущена).
"""
import ctypes, json, sys
try:
    lib = ctypes.CDLL("libonig.so.5")
except OSError:
    print("libonig.so.5 не найдена: проверка пропущена")
    sys.exit(77)
enc = ctypes.c_char.in_dll(lib, "OnigEncodingUTF8")          # a struct; its address is the OnigEncoding
syn = ctypes.c_char.in_dll(lib, "OnigSyntaxOniguruma")
enc_p = ctypes.c_void_p(ctypes.addressof(enc))
arr = (ctypes.c_void_p * 1)(enc_p.value)
print("initialize:", lib.onig_initialize(arr, 1))
class Info(ctypes.Structure):
    _fields_ = [("enc", ctypes.c_void_p), ("par", ctypes.c_void_p), ("par_end", ctypes.c_void_p)]
lib.onig_error_code_to_str.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p]
def compile_(p):
    b = ctypes.create_string_buffer(p.encode("utf-8"))
    n = len(p.encode("utf-8"))
    reg = ctypes.c_void_p(); info = Info()
    start = ctypes.addressof(b)
    r = lib.onig_new(ctypes.byref(reg), ctypes.c_void_p(start), ctypes.c_void_p(start + n), 0,
                     enc_p, ctypes.c_void_p(ctypes.addressof(syn)), ctypes.byref(info))
    msg = ""
    if r != 0:
        s = ctypes.create_string_buffer(256); lib.onig_error_code_to_str(s, r, ctypes.byref(info)); msg = s.value.decode(errors="replace")
    return r, msg
bad = n = 0
def walk(o):
    global bad, n
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("match", "begin", "end") and isinstance(v, str):
                n += 1
                r, e = compile_(v.replace("\\1", "x") if k == "end" else v)
                if r != 0:
                    bad += 1; print("BAD", k, v[:80], r, e)
            else: walk(v)
    elif isinstance(o, list):
        for x in o: walk(x)
for f in sys.argv[1:]:
    walk(json.load(open(f, encoding="utf-8")))
print("checked", n, "bad", bad)
sys.exit(1 if bad else 0)
