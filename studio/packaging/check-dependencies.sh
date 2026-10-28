#!/usr/bin/env bash
# Check the runtime dependencies of the Primula Docs package (stage 14.11).
# Nothing is installed without the explicit --install flag (it uses sudo and the
# system package manager); --print-plan prints the commands instead.
set -euo pipefail
package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  install=false
  print_plan=false
  for argument in "$@"; do
    [[ "$argument" != --install ]] || install=true
    [[ "$argument" != --print-plan ]] || print_plan=true
  done
  if "$print_plan"; then
    echo 'Python is missing. Install Python 3.11+ with venv and PyYAML with the system package manager, then rerun --print-plan.'
    exit 0
  fi
  if ! "$install"; then
    echo 'Missing Python 3.11+. Run this script with --install to install the runtime dependencies.' >&2
    exit 1
  fi
  privilege=()
  if (( EUID != 0 )); then privilege=(sudo); fi
  if command -v zypper >/dev/null 2>&1; then
    "${privilege[@]}" zypper install python3 python3-PyYAML
  elif command -v apt-get >/dev/null 2>&1; then
    "${privilege[@]}" apt-get update
    "${privilege[@]}" apt-get install python3 python3-venv python3-yaml
  else
    echo 'Install Python 3.11+ with PyYAML using your distribution package manager.' >&2; exit 1
  fi
fi
exec python3 "${package_dir}/runtime/dependencies.py" --package-dir "$package_dir" "$@"
