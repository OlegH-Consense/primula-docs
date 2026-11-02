#!/bin/sh
# Снимок окна Geany в виртуальном X-сервере (Xvfb) для проверки подсветки.
# Использование: geany_shot.sh <каталог_конфига_XDG> <файл> <выход.png>
# Конфиг должен содержать geany/filedefs/filetypes.*.conf и geany/filetype_extensions.conf.
CFG="$1"; FILE="$2"; OUT="$3"
D=:77
Xvfb $D -screen 0 1500x1000x24 >/dev/null 2>&1 &
XP=$!
sleep 1
mkdir -p "$CFG/geany"
printf '[interface]\ngeometry=0;0;1500;1000;0;\nmsgwin_visible=false\nsidebar_visible=false\n' > "$CFG/geany/geany.conf"
export DISPLAY=$D XDG_CONFIG_HOME="$CFG" GDK_BACKEND=x11 NO_AT_BRIDGE=1
geany --no-session --no-plugins -i "$FILE" >/dev/null 2>&1 &
GP=$!
sleep 5
for w in $(xdotool search --onlyvisible --name "geany" 2>/dev/null); do xdotool windowsize $w 1500 1000 2>/dev/null; done
sleep 2
# необязательная прокрутка: KEYS="Next Next" (клавиши xdotool)
if [ -n "$KEYS" ]; then xdotool key --delay 150 $KEYS; sleep 1; fi
import -window root "$OUT"
kill $GP $XP 2>/dev/null
