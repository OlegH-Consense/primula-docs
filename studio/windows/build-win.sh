#!/usr/bin/env bash
# Cross-build of Primula Studio for Windows 10+ (x86_64) on Linux with MinGW-w64.
#
#   studio/windows/build-win.sh            configure, build, collect DLLs, zip
#   studio/windows/build-win.sh --tests    also build studio-tests.exe
#   studio/windows/build-win.sh --no-zip   stop after the application directory
#   studio/windows/build-win.sh --installer  also build the NSIS installer (PrimulaStudio-<version>-win64.exe)
#   studio/windows/build-win.sh --dist     copy the archive and the installer to dist/ (older Windows builds there are removed)
#
# Qt is not compiled: a complete Qt 6 for Linux (host tools: moc, rcc, uic, lrelease)
# and for MinGW (target) is installed by aqtinstall into $PRIMULA_WIN_QT_DIR
# (default: /works/olegh/dev/ai/claude/Common/qt-new, layout <ver>/gcc_64 and <ver>/mingw_64).
# Output: studio/build-win/ (build tree, ignored by its own .gitignore),
#         studio/build-win/primula-studio/ (application directory, runnable under wine),
#         studio/build-win/primula-studio-<version>-win64.zip.
# The translator: primula.exe (a small launcher, primula-launcher.c) + python/ (embeddable
# Python for Windows, PyYAML, fontTools and src/primula) from $PRIMULA_WIN_PYTHON_DIR
# (default: Common/python-win: python-<ver>-embed-amd64.zip and wheels/*.whl).
# Requirements: cmake, ninja, x86_64-w64-mingw32-g++ with the POSIX thread model
# (openSUSE: mingw64-cross-gcc-c++; Debian: g++-mingw-w64-x86-64-posix), zip.
# See studio/developer-guide.md, section "Windows".
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
studio_dir="$(dirname "$here")"
qt_root="${PRIMULA_WIN_QT_DIR:-/works/olegh/dev/ai/claude/Common/qt-new}"
python_dir="${PRIMULA_WIN_PYTHON_DIR:-/works/olegh/dev/ai/claude/Common/python-win}"
qt_version="${PRIMULA_WIN_QT_VERSION:-6.8.3}"
build_dir="${PRIMULA_WIN_BUILD_DIR:-${studio_dir}/build-win}"
tests=OFF
make_zip=1
make_installer=0
make_dist=0

for argument in "$@"; do
    case "$argument" in
        --tests) tests=ON ;;
        --no-zip) make_zip=0 ;;
        --installer) make_installer=1 ;;
        --dist) make_dist=1 ;;
        -h|--help) sed -n '2,17p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "Unknown option: $argument" >&2; exit 2 ;;
    esac
done

host_qt="${qt_root}/${qt_version}/gcc_64"
target_qt="${qt_root}/${qt_version}/mingw_64"
for dir in "$host_qt" "$target_qt"; do
    [ -d "$dir" ] || { echo "Qt directory not found: $dir (set PRIMULA_WIN_QT_DIR)" >&2; exit 1; }
done
gxx="${MINGW_CXX:-x86_64-w64-mingw32-g++}"
command -v "$gxx" >/dev/null || { echo "MinGW compiler not found: $gxx" >&2; exit 1; }
if ! "$gxx" -v 2>&1 | grep -q "Thread model: posix"; then
    echo "The MinGW compiler must use the POSIX thread model (Qt for MinGW is built with it)." >&2
    exit 1
fi

mkdir -p "$build_dir"
[ -f "$build_dir/.gitignore" ] || printf '*\n' > "$build_dir/.gitignore"

cmake -S "$studio_dir" -B "$build_dir" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$here/toolchain-mingw.cmake" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$target_qt" \
    -DCMAKE_FIND_ROOT_PATH="${target_qt};${MINGW_SYSROOT:-/usr/x86_64-w64-mingw32/sys-root/mingw}" \
    -DQT_HOST_PATH="$host_qt" \
    -DPRIMULA_STUDIO_BUILD_TESTS="$tests" \
    -DPRIMULA_STUDIO_TEST_TRANSLATOR="$build_dir/primula-studio/primula.exe"
cmake --build "$build_dir" -j"$(nproc)"

app_dir="$build_dir/primula-studio"
rm -rf "$app_dir"
mkdir -p "$app_dir/platforms" "$app_dir/styles" "$app_dir/imageformats" "$app_dir/iconengines" "$app_dir/translations"
cp "$build_dir/primula-studio.exe" "$app_dir/"
for module in Core Gui Widgets Pdf PdfWidgets Svg Network; do
    cp "$target_qt/bin/Qt6${module}.dll" "$app_dir/"
done
cp "$target_qt/plugins/platforms/qwindows.dll" "$app_dir/platforms/"
cp "$target_qt/plugins/styles/"*.dll "$app_dir/styles/" 2>/dev/null || true
cp "$target_qt/plugins/imageformats/"{qjpeg,qsvg,qgif,qico}.dll "$app_dir/imageformats/" 2>/dev/null || true
# SVG icons of the toolbars: the image format and the icon engine plugins (Qt6Svg.dll).
cp "$target_qt/plugins/iconengines/qsvgicon.dll" "$app_dir/iconengines/"
cp "$build_dir/translations/"*.qm "$app_dir/translations/"
cp -r "$studio_dir/help" "$app_dir/help"

# Runtime of the compiler (DLLs of Qt need them next to the program).
for dll in libgcc_s_seh-1.dll libstdc++-6.dll libwinpthread-1.dll; do
    # The newest runtime first (the compiler's), then the one shipped with Qt for MinGW
    # (built by an older GCC: enough only if the program uses no newer libstdc++ symbols).
    found="$("$gxx" -print-file-name="$dll")"
    if [ ! -f "$found" ]; then
        found="$(find /usr -name "$dll" -path '*x86_64-w64-mingw32*' 2>/dev/null | head -n1 || true)"
    fi
    if [ -z "$found" ] || [ ! -f "$found" ]; then
        found="$target_qt/bin/$dll"
        echo "Note: $dll is taken from Qt (the compiler package has no copy)." >&2
    fi
    [ -f "$found" ] || { echo "Runtime DLL not found: $dll" >&2; exit 1; }
    cp "$found" "$app_dir/"
done
# The translator next to the program: Translator.cpp looks for primula.exe there.
"${MINGW_RC:-x86_64-w64-mingw32-windres}" -I "$here" "$here/primula-studio.rc" -O coff -o "$build_dir/primula-launcher-rc.o"
"${MINGW_CC:-x86_64-w64-mingw32-gcc}" -municode -O2 -s -o "$app_dir/primula.exe" "$here/primula-launcher.c" "$build_dir/primula-launcher-rc.o"
embed="$(ls "$python_dir"/python-*-embed-amd64.zip 2>/dev/null | head -n1 || true)"
if [ -n "$embed" ]; then
    py="$app_dir/python"
    mkdir -p "$py"
    unzip -q "$embed" -d "$py"
    packages="$py/Lib/site-packages"
    mkdir -p "$packages"
    for wheel in "$python_dir"/wheels/*.whl; do unzip -qo "$wheel" -d "$packages"; done
    cp -r "$studio_dir/../src/primula" "$packages/primula"
    find "$packages" -name '__pycache__' -type d -prune -exec rm -rf {} +
    # An embeddable Python reads only python*._pth for sys.path (no PYTHONPATH, no site).
    pth="$(ls "$py"/python*._pth | head -n1)"
    printf '%s\n' "$(basename "$pth" ._pth).zip" "." "Lib\\site-packages" > "$pth"
else
    echo "Note: no embeddable Python in $python_dir: the translator is not included." >&2
fi
# Examples, libraries, the author guide and the user guides (the same selection as the Linux package).
python3 -I "$here/win_content.py" "$(cd "$studio_dir/.." && pwd)" "$app_dir"
echo "Application directory: $app_dir"

if [ "$tests" = ON ]; then
    # A directory for studio-tests.exe under wine: the program, Qt Test and the offscreen
    # platform plugin (not shipped to users).  Run with QT_QPA_PLATFORM=offscreen.
    test_dir="$build_dir/tests"
    rm -rf "$test_dir"
    mkdir -p "$test_dir/platforms"
    cp -r "$app_dir/." "$test_dir/"
    cp "$build_dir/studio-tests.exe" "$target_qt/bin/Qt6Test.dll" "$test_dir/"
    cp "$target_qt/plugins/platforms/qoffscreen.dll" "$test_dir/platforms/"
    echo "Test directory: $test_dir"
fi

if [ "$make_zip" = 1 ]; then
    version="$(sed -n 's/^version *= *"\(.*\)"/\1/p' "$studio_dir/../pyproject.toml" | head -n1)"
    archive="$build_dir/primula-studio-${version}-win64.zip"
    rm -f "$archive"
    (cd "$build_dir" && zip -qr "$archive" primula-studio)
    echo "Archive: $archive"
fi

if [ "$make_installer" = 1 ]; then
    # NSIS: a native makensis if there is one, else makensis.exe of the Windows distribution
    # (zip from nsis.sourceforge.io, unpacked into $PRIMULA_WIN_NSIS_DIR) under wine.
    version="$(sed -n 's/^version *= *"\(.*\)"/\1/p' "$studio_dir/../pyproject.toml" | head -n1)"
    setup="$build_dir/PrimulaStudio-${version}-win64.exe"
    rm -f "$setup"
    nsis_dir="${PRIMULA_WIN_NSIS_DIR:-/works/olegh/dev/ai/claude/Common/nsis/nsis-3.13}"
    if command -v makensis >/dev/null 2>&1; then
        makensis -V2 -DVERSION="$version" -DSOURCE="$app_dir" -DOUTFILE="$setup" "$here/installer.nsi"
    elif [ -f "$nsis_dir/makensis.exe" ] && command -v wine >/dev/null 2>&1; then
        win() { local p="${1//\//\\}"; echo "Z:$p"; }   # Z: is the Linux root in Wine
        NSISDIR="$(win "$nsis_dir")" WINEPREFIX="${WINEPREFIX:-/works/olegh/dev/ai/claude/Common/wine-primula}" WINEDEBUG=-all wine "$nsis_dir/makensis.exe" -V2 \
            "-DVERSION=$version" "-DSOURCE=$(win "$app_dir")" "-DOUTFILE=$(win "$setup")" "$(win "$here/installer.nsi")" > "$build_dir/nsis.log" 2>&1 \
            || { cat "$build_dir/nsis.log" >&2; exit 1; }
    else
        echo "No makensis (native or $nsis_dir/makensis.exe with wine): the installer is not built." >&2
        exit 1
    fi
    [ -f "$setup" ] || { echo "The installer was not created." >&2; exit 1; }
    echo "Installer: $setup"
fi

if [ "$make_dist" = 1 ]; then
    # dist/ keeps the latest Windows build only: the files of earlier versions are replaced.
    dist_dir="${PRIMULA_WIN_DIST_DIR:-$studio_dir/../dist}"
    mkdir -p "$dist_dir"
    copied=0
    for file in "${archive:-}" "${setup:-}"; do
        [ -n "$file" ] && [ -f "$file" ] || continue
        pattern="$(basename "$file" | sed 's/[0-9][0-9.]*-win64/*-win64/')"
        find "$dist_dir" -maxdepth 1 -type f -name "$pattern" ! -name "$(basename "$file")" -delete
        cp -f "$file" "$dist_dir/"
        echo "dist: $dist_dir/$(basename "$file")"
        copied=1
    done
    [ "$copied" = 1 ] || { echo "--dist: nothing to copy (use the archive or --installer)." >&2; exit 1; }
fi
