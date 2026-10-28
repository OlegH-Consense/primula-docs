#!/usr/bin/env bash
# OPTIONAL, NON-STANDARD (stage 14.11): the translator compiled by Nuitka into a standalone
# directory that needs no Python on the target system. The standard package is
# make-distribution.sh (the translator as a Python package); this one is an extra variant
# a developer builds on request.
#
# Measured on the 30-page contract (15–16.10.2026, Nuitka 4.3, CPython 3.13): the binary is
# about 15–20 % slower than CPython (check 0.74 s with the _json/_bisect accelerators,
# 0.78 s without them, vs 0.63 s; build 0.79 s vs 0.67 s), the
# directory takes ~39 MB, the build ~11 min. Its only gain is running without Python and
# PyYAML. Like Studio, it is bound to the glibc of the build system: build it on the
# oldest target (Debian 12 for Debian 12 and 13).
#
# Requirements: a Python with Nuitka (pip install nuitka) and PyYAML importable from it,
# a C compiler, patchelf, the Python headers (python3-dev / python3XY-devel).
# Usage: packaging/build-nuitka-translator.sh [--python PATH] [--output DIRECTORY] [--archive] [--jobs N]
#   --python   the interpreter with Nuitka (default: $NUITKA_PYTHON, else python3)
#   --output   result directory (default: dist/primula-VERSION-nuitka-DISTRO-ARCH); never overwritten
#   PYTHONPATH may add the directory of PyYAML when it is not installed into that Python.
#   NUITKA_CACHE_DIR moves the Nuitka cache (default ~/.cache/Nuitka).
set -euo pipefail
packaging_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$(cd -- "$packaging_dir/../.." && pwd)"
python="${NUITKA_PYTHON:-python3}"
output=""
archive=false
jobs="$(nproc 2>/dev/null || echo 2)"
while (($#)); do
  case "$1" in
    --python) python="${2:?Missing interpreter}"; shift 2 ;;
    --output) output="${2:?Missing directory}"; shift 2 ;;
    --archive) archive=true; shift ;;
    --jobs) jobs="${2:?Missing number}"; shift 2 ;;
    -h|--help) sed -n '2,23p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

# --- requirements, checked before the long build ---------------------------------------
export PYTHONPATH="$source_dir/src${PYTHONPATH:+:$PYTHONPATH}"
"$python" -m nuitka --version >/dev/null 2>&1 || { echo "Nuitka is not available in $python (pip install nuitka)." >&2; exit 2; }
"$python" -c 'import yaml' 2>/dev/null || { echo "PyYAML is not importable from $python (pip install pyyaml, or PYTHONPATH)." >&2; exit 2; }
command -v patchelf >/dev/null || { echo 'patchelf is required for a standalone build.' >&2; exit 2; }
command -v cc >/dev/null || command -v gcc >/dev/null || { echo 'A C compiler is required.' >&2; exit 2; }
"$python" -c 'import os, sysconfig, sys; sys.exit(not os.path.isfile(os.path.join(sysconfig.get_paths()["include"], "Python.h")))' \
  || { echo 'Python headers (Python.h) are missing: install python3-dev / python3XY-devel.' >&2; exit 2; }

version="$(sed -n 's/^version = "\(.*\)"/\1/p' "$source_dir/pyproject.toml")"
. /etc/os-release 2>/dev/null || true
distro="$(printf '%s%s' "${ID:-linux}" "${VERSION_ID:-}" | tr -c 'A-Za-z0-9_.\n-' '-')"
output="${output:-$source_dir/dist/primula-$version-nuitka-$distro-$(uname -m)}"
if [[ -e "$output" ]]; then echo "Refusing to overwrite: $output" >&2; exit 2; fi
if "$archive" && [[ -e "$output.tar.gz" ]]; then echo "Refusing to overwrite: $output.tar.gz" >&2; exit 2; fi
mkdir -p "$(dirname -- "$output")"
work="$(mktemp -d "$(dirname -- "$output")/.primula-nuitka-XXXXXX")"
trap 'rm -rf -- "$work"' EXIT

# --- build ---------------------------------------------------------------------------------
# The anti-bloat plugin leaves out the C accelerators _json and _bisect ("may slow down by
# using fallback implementation"); they are included explicitly.
# The executable must not be named "primula": the package data directory primula/ next to
# it would collide with it and Nuitka would silently leave the data files out.
"$python" -m nuitka --mode=standalone --python-flag=-m \
  --include-package=primula --include-package-data=primula --include-package=yaml \
  --include-module=_json --include-module=_bisect \
  --assume-yes-for-downloads --jobs="$jobs" \
  --output-filename=primula-nuitka --output-dir="$work/build" "$source_dir/src/primula"
dist="$(find "$work/build" -maxdepth 1 -type d -name '*.dist' | head -n 1)"
[[ -x "$dist/primula-nuitka" ]] || { echo 'Nuitka produced no executable.' >&2; exit 1; }
# Data files of the package (read through __file__): add any Nuitka left out.
(cd "$source_dir/src" && find primula -type f ! -name '*.py' ! -name '*.pyc' ! -path '*__pycache__*') |
while IFS= read -r data; do
  if [[ ! -f "$dist/$data" ]]; then
    mkdir -p "$(dirname -- "$dist/$data")"
    cp -p "$source_dir/src/$data" "$dist/$data"
    echo "Added a data file Nuitka left out: $data"
  fi
done

# --- layout: lib/primula-nuitka/ and the launcher bin/primula -------------------------------
mkdir -p "$work/package/bin" "$work/package/lib"
mv "$dist" "$work/package/lib/primula-nuitka"
cat > "$work/package/bin/primula" <<'LAUNCHER'
#!/bin/sh
# Launcher of the standalone Primula translator (Nuitka build, a non-standard variant).
here=$(dirname -- "$(readlink -f -- "$0")")
exec "$here/../lib/primula-nuitka/primula-nuitka" "$@"
LAUNCHER
chmod +x "$work/package/bin/primula"
cat > "$work/package/README.txt" <<README
Primula translator $version — standalone build by Nuitka (NON-STANDARD VARIANT)

This is an optional extra build of the translator that runs without Python. The standard
package is primula-docs-$version-…: the translator as a Python package with Primula Studio.
The standalone build is about 15–20 % slower than CPython and is bound to the glibc of the
system it was built on ($([[ -n "${PRETTY_NAME:-}" ]] && echo "$PRETTY_NAME" || echo "$distro"), $(uname -m)).

Run:      bin/primula --help
Install:  copy the directory anywhere and link bin/primula into PATH, e.g.
          ln -s "\$PWD/bin/primula" ~/.local/bin/primula
PDF export still needs LibreOffice Writer.
README

# --- smoke test: version and a check of the first example --------------------------------
"$work/package/bin/primula" --version
(cd "$source_dir/examples/01-basics" && "$work/package/bin/primula" check basics.prml >/dev/null)
echo 'Smoke test: --version and check of examples/01-basics passed.'

mv "$work/package" "$output"
if "$archive"; then
  tar -C "$(dirname -- "$output")" -czf "$output.tar.gz" "$(basename -- "$output")"
  echo "Archive: $output.tar.gz"
fi
echo "Standalone translator (non-standard): $output"
