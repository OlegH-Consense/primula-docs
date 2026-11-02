#!/bin/sh
# Пересобирает определения mcedit и раскладывает их в тестовый HOME (.home).
# Пользовательский Syntax = системный + записи Primula перед первой записью.
set -e
cd "$(dirname "$0")/.."
python3 -I tools/gen_mcedit.py mcedit >/dev/null
H="$PWD/.home/.local/share/mc/syntax"
rm -rf "$PWD/.home"; mkdir -p "$H"
cp mcedit/primula.syntax mcedit/primula-code.syntax "$H/"
python3 - <<'PY'
import os
H=os.path.abspath('.home')+'/.local/share/mc/syntax/'
s=open('/usr/share/mc/syntax/Syntax',encoding='utf-8').read()
a=open("mcedit/Syntax.prml",encoding='utf-8').read()
i=s.index('file [Ss]yntax$')
open(H+'Syntax','w',encoding='utf-8').write(s[:i]+a+'\n'+s[i:])
PY
