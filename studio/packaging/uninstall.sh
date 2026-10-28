#!/usr/bin/env bash
# Remove the Primula Docs package of the current user: the same as install.sh --uninstall.
# Run from the unpacked package or from the installed copy (PREFIX/share/primula-docs, the prefix
# is then known). --purge also removes the settings and cache of Primula Studio and the copies of
# the examples (asks first; --yes does not ask); --keep-python, --prefix as for install.sh.
set -euo pipefail
package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 is required to run the uninstaller.' >&2
  exit 1
fi
exec python3 "${package_dir}/runtime/install.py" --package-dir "$package_dir" --uninstall "$@"
