#!/usr/bin/env bash
# Register build-tree or installed metadata for the desktop and host portal.
set -euo pipefail
studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_dir="${PRIMULA_STUDIO_BUILD_DIR:-${studio_dir}/build}"
install_prefix="${PRIMULA_STUDIO_INSTALL_PREFIX:-${HOME}/.local}"
mode="${1:---build}"
python3 - "$studio_dir" "$build_dir" "$install_prefix" "$mode" <<'PY'
import os
from pathlib import Path
import sys
studio, build, prefix = map(Path, sys.argv[1:4])
mode = sys.argv[4]
if mode not in ('--build', '--installed'):
    raise SystemExit('Usage: register-desktop.sh [--build|--installed]')
installed = mode == '--installed'
exe = (prefix / 'bin/primula-studio') if installed else (build / 'primula-studio')
icon = (prefix / 'share/icons/hicolor/scalable/apps/primula-studio.svg') if installed else (studio / 'resources/primula-studio.svg')
if not exe.is_file() or not icon.is_file():
    raise SystemExit('Build or install Studio before registering its desktop entry.')
data = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
target = data / 'applications/org.primula_docs.Studio.desktop'
marker = 'X-PrimulaStudio-Build-Tree=true'
# Do not redirect an already installed desktop entry to a development build.
if not installed and target.exists() and marker not in target.read_text():
    print('Keeping existing installed Studio desktop entry.')
    raise SystemExit(0)
def value(path):
    return str(path.resolve()).replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r')
# Desktop Exec has its own quoting rules; percent must be escaped as well.
command = str(exe.resolve()).replace('\\', '\\\\\\\\').replace('"', '\\\\"').replace('`', '\\\\`').replace('$', '\\\\$').replace('%', '%%')
text = (studio / 'resources/org.primula_docs.Studio.desktop').read_text()
lines = []
for line in text.splitlines():
    if line.startswith('Exec='): line = f'Exec="{command}" %f'
    if line.startswith('Icon='): line = 'Icon=' + value(icon)
    lines.append(line)
if not installed: lines.append(marker)
target.parent.mkdir(parents=True, exist_ok=True)
temporary = target.with_suffix('.desktop.tmp')
temporary.write_text('\n'.join(lines) + '\n')
os.replace(temporary, target)
print('Registered Studio desktop entry: ' + str(target))
PY
