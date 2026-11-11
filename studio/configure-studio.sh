#!/usr/bin/env bash
set -euo pipefail

studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_dir="${PRIMULA_STUDIO_BUILD_DIR:-${studio_dir}/build}"

source "${studio_dir}/build-host.sh"
check_build_host "${build_dir}"
cmake -S "${studio_dir}" -B "${build_dir}" -G Ninja \
  -DCMAKE_BUILD_TYPE="${PRIMULA_STUDIO_BUILD_TYPE:-Release}"
mark_build_host "${build_dir}"

echo "Configured: ${build_dir}"

