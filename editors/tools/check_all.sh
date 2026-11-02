#!/bin/sh
# Полная перегенерация (словарь из транслятора, Kate, mcedit, VS Code) и проверка: схема XML (xmllint), токены Kate, снимок mcedit.
# Требуются: python3, xmllint, kate-syntax-highlighter, mc, tmux.
# Схема language.xsd берётся из KDE/syntax-highlighting (data/schema/language.xsd);
# путь можно задать переменной XSD.
set -eu
cd "$(dirname "$0")/.."
python3 tools/sync_lexicon.py
python3 -I tools/gen_kate.py kate
python3 -I tools/gen_textmate.py vscode
python3 -I tools/make_vsix.py vscode
python3 -I tools/gen_mcedit.py mcedit
python3 -I tools/gen_geany.py geany
if [ -n "${XSD:-}" ]; then xmllint --noout --schema "$XSD" kate/primula.xml kate/primula-code.xml; fi
python3 tests/check_kate.py
python3 tests/check_mcedit.py
python3 tools/check_oniguruma.py vscode/syntaxes/primula.tmLanguage.json vscode/syntaxes/primula-code.tmLanguage.json || [ $? -eq 77 ]
