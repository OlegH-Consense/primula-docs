#!/usr/bin/env bash
set -euo pipefail

studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_dir="${PRIMULA_STUDIO_BUILD_DIR:-${studio_dir}/build}"
install_prefix="${PRIMULA_STUDIO_INSTALL_PREFIX:-${HOME}/.local}"

"${studio_dir}/build-studio.sh"
cmake --install "${build_dir}" --prefix "${install_prefix}"

"${studio_dir}/register-desktop.sh" --installed

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${install_prefix}/share/applications" >/dev/null 2>&1 || true
fi

echo "Installed or updated: ${install_prefix}/bin/primula-studio"

