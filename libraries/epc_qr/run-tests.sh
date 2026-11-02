#!/bin/sh
# Check every test document of the library and the example project that links
# it. "primula check" exits with 2 when a fail() of a test fires. PRIMULA may
# name the translator (default: primula in PATH).
set -u
here=$(cd "$(dirname "$0")" && pwd)
primula=${PRIMULA:-}
if [ -z "$primula" ]; then
    if command -v primula >/dev/null 2>&1; then primula=primula
    else echo "primula not found: set PRIMULA" >&2; exit 2; fi
fi
status=0
# demo/project.p.prml is a project file, not a test. demo/demo.prml imports
# lib/epc_qr through a symlink and may warn P2639; that warning is not a failure.
for test in "$here"/tests/*.prml "$here"/demo/demo.prml; do
    if "$primula" check "$test" >/dev/null 2>&1; then
        echo "ok    ${test#"$here"/}"
    else
        echo "FAIL  ${test#"$here"/}"
        "$primula" check "$test" --lang uk
        status=1
    fi
done
exit $status
