#!/usr/bin/env bash
# Install, update (--prefix as before) or remove (--uninstall) the Primula Docs package
# for the current user; the default prefix is ~/.local. See README.md of the package.
set -euo pipefail
package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3.11+ is required. Run ./check-dependencies.sh --install first.' >&2
  exit 1
fi
exec python3 "${package_dir}/runtime/install.py" --package-dir "$package_dir" "$@"
