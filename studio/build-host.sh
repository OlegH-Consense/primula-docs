# shellcheck shell=bash
# Sourced by the build scripts: a build directory belongs to the system it was configured on.
# CMake keeps absolute paths of the libraries of that system in CMakeCache.txt (/usr/lib64/libGLX.so of
# openSUSE does not exist on Debian), so a directory shared by several systems (a home on the network,
# a virtual machine over the same source tree) fails to build with a puzzling "missing and no known rule".

# Name of this system for a directory name and for the tag: ID-VERSION_ID-ARCH (debian-12-x86_64).
host_tag() {
  local ID="" VERSION_ID=""
  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
  fi
  case "${ID:-}" in opensuse-tumbleweed|arch) VERSION_ID=rolling ;; esac   # VERSION_ID of a rolling release is a date
  printf '%s-%s-%s' "${ID:-linux}" "${VERSION_ID:-0}" "$(uname -m)"
}

# check_build_host DIRECTORY: stop when the directory was configured on another system.
check_build_host() {
  local directory="$1" tag_file="$1/.primula-host" tag
  tag="$(host_tag)"
  if [[ -f "$directory/CMakeCache.txt" && -f "$tag_file" && "$(<"$tag_file")" != "$tag" ]]; then
    echo "The build directory $directory was configured on $(<"$tag_file"), this system is $tag." >&2
    echo "Use a directory of its own: PRIMULA_STUDIO_BUILD_DIR=$directory-$tag $0 ... (or remove $directory)." >&2
    return 2
  fi
}

# mark_build_host DIRECTORY: remember the system of a configured directory.
mark_build_host() {
  if [[ -d "$1" ]]; then host_tag >"$1/.primula-host"; fi
}
