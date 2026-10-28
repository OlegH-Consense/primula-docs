#!/bin/sh
# Check every test document of the library: "primula check" exits with 2 when a
# fail() of a test fires. PRIMULA may name the translator (default: primula in
# PATH, else the launcher of the source tree two levels up from examples/).
set -u
here=$(cd "$(dirname "$0")" && pwd)
primula=${PRIMULA:-}
if [ -z "$primula" ]; then
    if command -v primula >/dev/null 2>&1; then primula=primula
    else primula="$here/../../primula"; fi
fi
status=0
for test in "$here"/tests/*.prml; do
    if "$primula" check "$test" >/dev/null 2>&1; then
        echo "ok    ${test#"$here"/}"
    else
        echo "FAIL  ${test#"$here"/}"
        "$primula" check "$test"
        status=1
    fi
done
exit $status
