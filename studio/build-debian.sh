#!/usr/bin/env bash
# Native build on Debian 12/13 and derivatives (stage 14.11): check the tools, configure
# Qt (minimum 6.4), build Primula Studio; the translator runs from the source tree
# (../primula) with the system Python and python3-yaml.
# No system packages are installed unless --install-deps is given explicitly.
set -euo pipefail
studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$(cd -- "$studio_dir/.." && pwd)"
build_dir="${PRIMULA_STUDIO_BUILD_DIR:-$studio_dir/build-debian}"
install_deps=false
run_app=false
while (($#)); do
  case "$1" in
    --install-deps) install_deps=true; shift ;;
    --run) run_app=true; shift ;;
    --help|-h)
      echo 'Usage: studio/build-debian.sh [--install-deps] [--run]'
      echo 'Requires Debian 12+ or a derivative with Qt 6.4+, Python 3.11+ and python3-yaml.'
      echo 'Overrides: PRIMULA_STUDIO_BUILD_DIR, PRIMULA_STUDIO_BUILD_TYPE (Release), PRIMULA_STUDIO_BUILD_JOBS (2).'
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
if "$install_deps"; then
  command -v apt-get >/dev/null || { echo 'apt-get is required for --install-deps.' >&2; exit 2; }
  privileged=()
  if [[ $EUID -ne 0 ]]; then privileged=(sudo); fi
  "${privileged[@]}" apt-get update
  "${privileged[@]}" apt-get install build-essential cmake ninja-build qt6-base-dev \
    qt6-pdf-dev qt6-tools-dev qt6-tools-dev-tools qt6-l10n-tools libqt6svg6 \
    python3 python3-yaml python3-uno libreoffice-writer fonts-liberation
  # Debian 13 splits the SVG icon plugin into a separate package; Debian 12 does not.
  if apt-cache show qt6-svg-plugins >/dev/null 2>&1; then
    "${privileged[@]}" apt-get install qt6-svg-plugins
  fi
fi
for command_name in cmake ninja c++ python3; do
  command -v "$command_name" >/dev/null || {
    echo "Missing $command_name. See studio/developer-guide.md or use --install-deps." >&2; exit 2;
  }
done
python3 -c 'import sys, yaml; sys.exit(sys.version_info < (3, 11))' || {
  echo 'The translator needs Python 3.11+ with PyYAML (python3-yaml).' >&2; exit 2;
}
source "$studio_dir/build-host.sh"
check_build_host "$build_dir"
cmake -S "$studio_dir" -B "$build_dir" -G Ninja \
  -DCMAKE_BUILD_TYPE="${PRIMULA_STUDIO_BUILD_TYPE:-Release}" -DPRIMULA_STUDIO_MIN_QT_VERSION=6.4
mark_build_host "$build_dir"
cmake --build "$build_dir" --parallel "${PRIMULA_STUDIO_BUILD_JOBS:-2}"
"$source_dir/primula" --version
echo "Built: $build_dir/primula-studio"
if "$run_app"; then
  PRIMULA_STUDIO_BUILD_DIR="$build_dir" "$studio_dir/register-desktop.sh" --build
  exec "$build_dir/primula-studio"
fi
