#!/usr/bin/env bash
set -euo pipefail

studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_dir="${PRIMULA_STUDIO_BUILD_DIR:-${studio_dir}/build}"

"${studio_dir}/build-studio.sh"
"${studio_dir}/register-desktop.sh" --build
exec "${build_dir}/primula-studio" "$@"

