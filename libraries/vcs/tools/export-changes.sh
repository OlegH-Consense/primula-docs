#!/bin/sh
# Export git history as JSON for the vcs module.
#
# Usage, from anywhere inside the repository:
#   tools/export-changes.sh [path...] > data/changes.json
#
# With no path, every commit is exported. A path limits the log to commits
# that touch that path, the same way "git log -- path" does. Paths are
# relative to the current directory.
#
# Each object has hash, date (YYYY-MM-DD, author date), author, message and
# files. The module, not this script, keeps only messages whose first line
# is "Зміна N: підстава". This is the library's own markup, not a DSTU or
# ESKD form.
#
# Requires git and python3. A commit message that contains the ASCII record
# separator (U+001E) is not split correctly; ordinary text does not.
set -eu
if ! command -v git >/dev/null 2>&1; then
    echo "export-changes: немає команди git" >&2
    exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
    echo "export-changes: немає команди python3" >&2
    exit 1
fi
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "export-changes: це не git-репозиторій" >&2
    exit 1
fi
python3 - "$@" << 'PY'
import json
import subprocess
import sys

# Unit separator between fields, record separator after the message.
# git adds a newline between commits on top of the record separator.
SEP_FIELD = "\x1f"
SEP_REC = "\x1e"

paths = sys.argv[1:]
cmd = [
    "git", "log", "--reverse",
    "--date=format:%Y-%m-%d",
    "--pretty=format:%H%x1f%ad%x1f%an%x1f%B%x1e",
]
if paths:
    cmd.append("--")
    cmd.extend(paths)

try:
    raw = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
except subprocess.CalledProcessError:
    sys.stderr.write("export-changes: git log не виконав команду\n")
    sys.exit(1)

commits = []
for chunk in raw.split(SEP_REC):
    chunk = chunk.strip("\n")
    if chunk == "":
        continue
    parts = chunk.split(SEP_FIELD)
    if len(parts) != 4:
        sys.stderr.write("export-changes: не вдалося розібрати рядок git log\n")
        sys.exit(1)
    sha, day, author, message = parts
    try:
        diff = subprocess.check_output(
            ["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha],
            text=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        sys.stderr.write("export-changes: git diff-tree не виконав команду\n")
        sys.exit(1)
    files = [line for line in diff.splitlines() if line != ""]
    commits.append({
        "hash": sha,
        "date": day,
        "author": author,
        "message": message,
        "files": files,
    })

json.dump(commits, sys.stdout, ensure_ascii=False, indent=2)
sys.stdout.write("\n")
PY
