#!/usr/bin/env bash
set -euo pipefail

studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_dir="${PRIMULA_STUDIO_BUILD_DIR:-${studio_dir}/build}"

"${studio_dir}/configure-studio.sh"
cmake --build "${build_dir}" --parallel

echo "Built: ${build_dir}/primula-studio"
