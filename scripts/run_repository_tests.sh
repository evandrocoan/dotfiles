#!/usr/bin/env bash
set -euo pipefail

if (( $# != 0 )); then
    printf 'Error: run_repository_tests.sh does not accept arguments.\n' >&2
    exit 2
fi

SCRIPT_DIRECTORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIRECTORY
REPOSITORY_ROOT="$(git -C "${SCRIPT_DIRECTORY}" rev-parse --show-toplevel)"
readonly REPOSITORY_ROOT
cd -- "${REPOSITORY_ROOT}"

TEST_CACHE_DIRECTORY="$(mktemp -d)"
readonly TEST_CACHE_DIRECTORY
trap 'rm -rf -- "${TEST_CACHE_DIRECTORY}"' EXIT
export PYTHONPYCACHEPREFIX="${TEST_CACHE_DIRECTORY}"

function list_bash_sources() {
    python3 -B - <<'PY'
from pathlib import Path
import os
import re
import subprocess
import sys


BASH_CONFIG_NAMES = {
    ".bash_login",
    ".bash_logout",
    ".bash_profile",
    ".bashrc",
    ".profile",
}
BASH_SHEBANG = re.compile(rb"^#![^\n]*(?:/|[ \t])(?:ba)?sh(?:[ \t]|$)")
repository_root = Path.cwd()
paths = subprocess.check_output(
    ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
).split(b"\0")

for encoded_path in paths:
    if not encoded_path:
        continue
    relative_path = Path(os.fsdecode(encoded_path))
    source_path = repository_root / relative_path
    if not source_path.is_file():
        continue
    with source_path.open("rb") as stream:
        first_line = stream.readline(256)
    if (
        relative_path.suffix == ".sh"
        or relative_path.name in BASH_CONFIG_NAMES
        or BASH_SHEBANG.match(first_line)
    ):
        sys.stdout.buffer.write(encoded_path + b"\0")
PY
}

python3 -m unittest discover -s scripts/performance-monitoring -p 'test_*.py' -v
python3 -m unittest discover -s scripts -p 'test_*.py' -v

PYTHON_SOURCE_LIST="${TEST_CACHE_DIRECTORY}/python-sources"
readonly PYTHON_SOURCE_LIST
git ls-files --cached --others --exclude-standard -z '*.py' >"${PYTHON_SOURCE_LIST}"
while IFS= read -r -d '' SOURCE_FILE; do
    python3 -W error::SyntaxWarning -m py_compile "${SOURCE_FILE}"
done <"${PYTHON_SOURCE_LIST}"

BASH_SOURCE_LIST="${TEST_CACHE_DIRECTORY}/bash-sources"
readonly BASH_SOURCE_LIST
list_bash_sources >"${BASH_SOURCE_LIST}"
while IFS= read -r -d '' SOURCE_FILE; do
    bash -n "${SOURCE_FILE}"
done <"${BASH_SOURCE_LIST}"
