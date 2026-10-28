#!/usr/bin/env bash
# Build the native runtime package of Primula Docs (translator + Primula Studio) on the
# target Linux distribution (stage 14.11); see packaging/make_distribution.py.
set -euo pipefail
studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_dir="${PRIMULA_STUDIO_BUILD_DIR:-${studio_dir}/build}"
output_dir=""
archive=false
skip_build=false
while (($#)); do
  case "$1" in
    --build-dir) build_dir="${2:?Missing build directory}"; shift 2 ;;
    --output) output_dir="${2:?Missing output directory}"; shift 2 ;;
    --archive) archive=true; shift ;;
    --skip-build) skip_build=true; shift ;;
    -h|--help)
      echo 'Usage: make-distribution.sh [--output DIRECTORY] [--build-dir DIRECTORY] [--archive] [--skip-build]'
      echo 'Default: build Studio (Release), create dist/primula-docs-VERSION-DISTRO-ARCH/. Existing directories are never overwritten.'
      echo 'The optional standalone translator built with Nuitka: packaging/build-nuitka-translator.sh.'
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
if ! "$skip_build"; then
  PRIMULA_STUDIO_BUILD_DIR="$build_dir" "${studio_dir}/build-studio.sh"
fi
arguments=(--source "${studio_dir}/.." --build-dir "$build_dir")
if [[ -n "$output_dir" ]]; then arguments+=(--output "$output_dir"); fi
if "$archive"; then arguments+=(--archive); fi
python3 "${studio_dir}/packaging/make_distribution.py" "${arguments[@]}"
