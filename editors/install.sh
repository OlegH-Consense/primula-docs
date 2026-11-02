#!/bin/sh
# Установка подсветки Primula для Kate/KWrite/KDevelop, mcedit, Geany и VS Code
# в профиль текущего пользователя (root не нужен).
#
# Использование:  ./install.sh [kate] [mcedit] [geany] [vscode] [cursor] [codium]     (без аргументов — все)
#                 ./install.sh --uninstall [kate] [mcedit] [geany] [vscode] [cursor] [codium]
#
# Что делает:
#   kate   — копирует kate/*.xml в ~/.local/share/org.kde.syntax-highlighting/syntax/
#   mcedit — копирует mcedit/*.syntax в ~/.local/share/mc/syntax/ и добавляет записи
#            Primula в пользовательский Syntax (если его нет — создаёт копию
#            системного, т.к. пользовательский Syntax ЗАМЕНЯЕТ системный целиком;
#            перед изменением делается резервная копия Syntax.bak-primula)
#   geany  — копирует geany/filetypes.Primula.conf в ~/.config/geany/filedefs/ и
#            добавляет «Primula=*.prml;» в раздел [Extensions] filetype_extensions.conf
#   vscode, cursor, codium — ставят vscode/primula-0.1.0.vsix командой самой программы
#            (code|cursor|codium --install-extension); без команды в PATH скрипт покажет путь к .vsix
# Скрипт идемпотентен: повторный запуск не дублирует записи.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONF="${XDG_CONFIG_HOME:-$HOME/.config}"
MARK_BEGIN="# >>> Primula (install.sh) >>>"
MARK_END="# <<< Primula (install.sh) <<<"

# --- Kate ------------------------------------------------------------------------
kate_install() {
    d="$DATA/org.kde.syntax-highlighting/syntax"
    mkdir -p "$d"
    cp "$HERE"/kate/primula.xml "$HERE"/kate/primula-code.xml "$d/"
    echo "Kate: файлы скопированы в $d (перезапустите Kate/KWrite/KDevelop)"
}
kate_uninstall() {
    rm -f "$DATA/org.kde.syntax-highlighting/syntax/primula.xml" \
          "$DATA/org.kde.syntax-highlighting/syntax/primula-code.xml"
    echo "Kate: удалено"
}

# --- mcedit ----------------------------------------------------------------------
mc_dir() { echo "$DATA/mc/syntax"; }
mc_sys_syntax() {
    for s in /usr/share/mc/syntax/Syntax /usr/local/share/mc/syntax/Syntax; do
        [ -f "$s" ] && { echo "$s"; return; }
    done
    return 1
}
mc_install() {
    d=$(mc_dir); mkdir -p "$d"
    cp "$HERE"/mcedit/primula.syntax "$HERE"/mcedit/primula-code.syntax "$d/"
    if [ ! -f "$d/Syntax" ]; then
        sys=$(mc_sys_syntax) || { echo "mcedit: не найден системный Syntax (установлен ли mc?)" >&2; return 1; }
        cp "$sys" "$d/Syntax"
        echo "mcedit: создана копия системного Syntax из $sys"
    fi
    if grep -q "$MARK_BEGIN" "$d/Syntax"; then
        echo "mcedit: записи Primula уже есть в $d/Syntax"
    else
        cp "$d/Syntax" "$d/Syntax.bak-primula"
        # записи должны стоять ДО первой строки «file …» (побеждает первая подходящая)
        first=$(grep -n '^file ' "$d/Syntax" | head -n1 | cut -d: -f1)
        {
            head -n $((first - 1)) "$d/Syntax"
            echo "$MARK_BEGIN"
            grep -v '^#' "$HERE/mcedit/Syntax.prml"
            echo "$MARK_END"
            echo
            tail -n +"$first" "$d/Syntax"
        } > "$d/Syntax.new" && mv "$d/Syntax.new" "$d/Syntax"
        echo "mcedit: записи добавлены в $d/Syntax (резервная копия: Syntax.bak-primula)"
    fi
}
mc_uninstall() {
    d=$(mc_dir)
    rm -f "$d/primula.syntax" "$d/primula-code.syntax"
    if [ -f "$d/Syntax" ] && grep -q "$MARK_BEGIN" "$d/Syntax"; then
        sed "/$MARK_BEGIN/,/$MARK_END/d" "$d/Syntax" > "$d/Syntax.new" && mv "$d/Syntax.new" "$d/Syntax"
    fi
    echo "mcedit: удалено (пользовательский Syntax оставлен; удалите его вручную, если он вам не нужен)"
}

# --- Geany -----------------------------------------------------------------------
geany_install() {
    d="$CONF/geany/filedefs"; mkdir -p "$d"
    cp "$HERE/geany/filetypes.Primula.conf" "$d/"
    f="$CONF/geany/filetype_extensions.conf"
    if [ ! -f "$f" ]; then
        printf '[Extensions]\nPrimula=*.prml;\n' > "$f"
    elif ! grep -q '^Primula=' "$f"; then
        if grep -q '^\[Extensions\]' "$f"; then
            sed -i 's/^\[Extensions\]$/[Extensions]\nPrimula=*.prml;/' "$f"
        else
            printf '\n[Extensions]\nPrimula=*.prml;\n' >> "$f"
        fi
    fi
    echo "Geany: установлено (перезапустите Geany)"
}
geany_uninstall() {
    rm -f "$CONF/geany/filedefs/filetypes.Primula.conf"
    f="$CONF/geany/filetype_extensions.conf"
    [ -f "$f" ] && sed -i '/^Primula=/d' "$f"
    echo "Geany: удалено"
}

# --- VS Code, Cursor, VSCodium ----------------------------------------------------
# Современные VS Code и Cursor не подхватывают расширения, просто скопированные в каталог
# extensions: они должны быть записаны в extensions.json, который ведёт сама программа.
# Поэтому расширение ставится пакетом .vsix командой самой программы (--install-extension).
VSIX="$HERE/vscode/primula-0.1.0.vsix"
# Команда программы берётся из переменной CODE_CMD, CURSOR_CMD или CODIUM_CMD (можно с ключами,
# например CURSOR_CMD="/opt/Cursor.AppImage --no-sandbox"), иначе из PATH.
vsix_install() {   # $1 — название программы, $2 — её команда (слова без пробелов внутри)
    cmd=$2
    if [ ! -f "$VSIX" ]; then
        echo "$1: нет $VSIX (соберите: python3 tools/make_vsix.py)" >&2; return 1
    fi
    if ! command -v "${cmd%% *}" >/dev/null 2>&1; then
        echo "$1: команда '${cmd%% *}' не найдена. Задайте её переменной (CURSOR_CMD=…) или установите вручную:"
        echo "     Extensions → ⋯ → Install from VSIX… → $VSIX"
        return 0
    fi
    $cmd --install-extension "$VSIX" --force || true
    # Код возврата программы ничего не доказывает (AppImage и обёртки возвращают 0 при сбое): смотрим список.
    if $cmd --list-extensions 2>/dev/null | grep -qix 'primula-docs.primula'; then
        echo "$1: расширение primula-docs.primula установлено (перезапустите $1)"
    else
        echo "$1: команда '$cmd' не установила расширение (его нет в списке --list-extensions)." >&2
        echo "     Установите вручную: Extensions → ⋯ → Install from VSIX… → $VSIX" >&2
        return 1
    fi
}
vsix_uninstall() {
    cmd=$2
    if command -v "${cmd%% *}" >/dev/null 2>&1; then
        $cmd --uninstall-extension primula-docs.primula && echo "$1: удалено"
    else
        echo "$1: команда '${cmd%% *}' не найдена; удалите расширение primula-docs.primula в списке расширений"
    fi
}
vscode_install()   { vsix_install "VS Code" "${CODE_CMD:-code}"; }
vscode_uninstall() { vsix_uninstall "VS Code" "${CODE_CMD:-code}"; }
cursor_install()   { vsix_install "Cursor" "${CURSOR_CMD:-cursor}"; }
cursor_uninstall() { vsix_uninstall "Cursor" "${CURSOR_CMD:-cursor}"; }
codium_install()   { vsix_install "VSCodium" "${CODIUM_CMD:-codium}"; }
codium_uninstall() { vsix_uninstall "VSCodium" "${CODIUM_CMD:-codium}"; }

# --- разбор аргументов ------------------------------------------------------------
action=install
[ "${1:-}" = "--uninstall" ] && { action=uninstall; shift; }
targets="${*:-kate mcedit geany vscode}"
for t in $targets; do
    case "$t" in
        kate)   kate_$action ;;
        mcedit) mc_$action ;;
        geany)  geany_$action ;;
        vscode) vscode_$action ;;
        cursor) cursor_$action ;;
        codium) codium_$action ;;
        *) echo "неизвестная цель: $t (допустимо: kate mcedit geany vscode cursor codium)" >&2; exit 1 ;;
    esac
done
