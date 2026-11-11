#!/usr/bin/env bash
# Make the system packages (.deb and .rpm) of Primula Docs on the target Linux distribution
# (stage 26.1): builds Studio and the runtime package like make-distribution.sh, then packs it
# with packaging/make_packages.py. Nothing is installed or changed on this system.
set -euo pipefail
studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${studio_dir}/build-host.sh"
# A directory of its own per system: packages are made on the system they are for, and the build directory
# of another system (studio/build of an openSUSE host) cannot be reused.
build_dir="${PRIMULA_STUDIO_BUILD_DIR:-${studio_dir}/build-packages-$(host_tag)}"
output_dir="${studio_dir}/../dist/packages"
format=all
skip_build=false
extra=()
while (($#)); do
  case "$1" in
    --build-dir) build_dir="${2:?Missing build directory}"; shift 2 ;;
    --output) output_dir="${2:?Missing output directory}"; shift 2 ;;
    --format) format="${2:?Missing format (deb, rpm, all)}"; shift 2 ;;
    --revision) extra+=(--revision "${2:?Missing revision}"); shift 2 ;;
    --maintainer) extra+=(--maintainer "${2:?Missing maintainer}"); shift 2 ;;
    --sign) extra+=(--sign "${2:?Missing GnuPG key}"); shift 2 ;;
    --gpg-home) extra+=(--gpg-home "${2:?Missing GnuPG home}"); shift 2 ;;
    --skip-build) skip_build=true; shift ;;
    -h|--help)
      echo 'Usage: make-packages.sh [--format deb|rpm|all] [--output DIRECTORY] [--build-dir DIRECTORY] [--skip-build]'
      echo '                        [--revision N] [--maintainer "Name <address>"]'
      echo '                        [--sign GPGKEY [--gpg-home DIRECTORY]]   (sign the .rpm; needs rpm-sign; the key stays in your keyring)'
      echo 'Default: build Studio (Release) in studio/build-packages-SYSTEM, write the packages of this family of systems'
      echo '(primula-docs_VERSION-1_ARCH.deb on Debian/Ubuntu, primula-docs-VERSION-1.ARCH.rpm on openSUSE/Fedora) to dist/packages/.'
      echo 'The .rpm needs rpmbuild (package rpm-build, or rpm on openSUSE). Studio links to the Qt 6, libstdc++ and glibc of this system:'
      echo 'make the .deb on Debian 12 (it runs on Debian 12 and 13), the .rpm on openSUSE. --format deb|rpm forces a format of another family (it will not run).'
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
arguments=(--build-dir "$build_dir" --output "${work}/package")
if "$skip_build"; then arguments+=(--skip-build); fi
"${studio_dir}/make-distribution.sh" "${arguments[@]}"
python3 "${studio_dir}/packaging/make_packages.py" --package "${work}/package" --output "$output_dir" \
    --format "$format" ${extra[@]+"${extra[@]}"}
