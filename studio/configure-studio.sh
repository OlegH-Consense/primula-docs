#!/usr/bin/env bash
set -euo pipefail

studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_dir="${PRIMULA_STUDIO_BUILD_DIR:-${studio_dir}/build}"

cmake -S "${studio_dir}" -B "${build_dir}" -G Ninja \
  -DCMAKE_BUILD_TYPE="${PRIMULA_STUDIO_BUILD_TYPE:-Release}"

echo "Configured: ${build_dir}"

