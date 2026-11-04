#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
ISOLATED_BASE=''
ISOLATED_TREE=''
DRY_RUN=0
CLEAN_TREE=0
LOCK_HELD=0
UPSTREAM=''
ISOLATED_GIT_ARGUMENTS=()

function printhelp() {
    local exit_status="${1}"
cat <<EOF
Usage: bash ${0} [arguments]

Keep .git in place, prepare a clean temporary directory, and pull --rebase
using that directory for files. The original work tree is left untouched.
The branch and shared index are updated; staged changes are refused.
Keep other Git clients idle until this command finishes.

  -h | --help                Show this help.
  -r | --repository <path>   Repository root (default: parent of this script's directory).
  -b | --base <path>         Temporary base (default: <root>/.local/state/isolated-pull).
  -n | --dry-run             Check and print the steps without creating anything.
  -c | --clean               Remove this run's temporary tree after success.
EOF
    exit "${exit_status}"
}

function invalidargument() {
    printf 'Error: Invalid argument "%s" for option "%s".\n' "${2}" "${1}" >&2
    printhelp 1
}

function checkargsvalid() {
    local argument_value="${2-}"
    if [[ -z "${argument_value}" || "${argument_value}" == '-'* ]]; then
        invalidargument "${1}" "${argument_value}"
    fi
}

function checkexpectedargs() {
    local argument_value="${2--}"
    if [[ "${argument_value}" != '-'* ]]; then
        printf 'Error: The command "%s" does not expect any arguments, but got "%s".\n' "${1}" "${argument_value}" >&2
        printhelp 1
    fi
}

function fail() {
    printf 'Error: %s\n' "${1}" >&2
    exit 1
}

function repositorygit() {
    git --no-optional-locks --git-dir="${REPOSITORY}/.git" --work-tree="${REPOSITORY}" "${@}"
}

function isolatedgit() {
    git "${ISOLATED_GIT_ARGUMENTS[@]}" "${@}"
}

function assertisolated() {
    local actual_tree actual_git
    # Keep Git queries separate from cd: a failed query must not be masked.
    actual_tree="$(isolatedgit rev-parse --show-toplevel)"
    actual_tree="$(cd -- "${actual_tree}" && pwd -P)"
    actual_git="$(isolatedgit rev-parse --absolute-git-dir)"
    actual_git="$(cd -- "${actual_git}" && pwd -P)"
    [[ "${actual_tree}" == "${ISOLATED_TREE}" ]] || fail 'Git did not select the isolated tree.'
    [[ "${actual_git}" == "${REPOSITORY}/.git" ]] || fail 'Git did not select the original database.'
}

function checkpreconditions() {
    local variable marker lock_file
    for variable in GIT_DIR GIT_COMMON_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_NAMESPACE; do
        [[ ! -v "${variable}" ]] || fail "Unset ${variable} before running this script."
    done
    REPOSITORY="$(cd -- "${REPOSITORY}" && pwd -P)"
    [[ -d "${REPOSITORY}/.git" && ! -L "${REPOSITORY}/.git" ]] ||
        fail 'The repository must have its own .git directory, not a linked worktree or submodule.'
    for marker in rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD BISECT_LOG sequencer; do
        [[ ! -e "${REPOSITORY}/.git/${marker}" ]] || fail "A Git operation is already in progress (.git/${marker})."
    done
    repositorygit diff --cached --quiet ||
        fail 'The index holds staged changes; commit or unstage them before running this script.'
    repositorygit symbolic-ref --quiet HEAD >/dev/null || fail 'A branch must be checked out.'
    UPSTREAM="$(repositorygit rev-parse --abbrev-ref --symbolic-full-name '@{u}')" ||
        fail 'The current branch has no upstream; there is nothing to pull.'
    lock_file="$(find "${REPOSITORY}/.git" -name '*.lock' -print -quit)"
    [[ -z "${lock_file}" ]] || fail "A Git lock exists: ${lock_file}. Wait for its owner to finish."

    ISOLATED_BASE="$(realpath -m -- "${ISOLATED_BASE:-${REPOSITORY}/.local/state/isolated-pull}")"
    [[ "${ISOLATED_BASE}/" != "${REPOSITORY}/.git/"* ]] ||
        fail 'The isolated base must not be inside the repository database.'
    [[ "${REPOSITORY}/" != "${ISOLATED_BASE%/}/"* ]] ||
        fail 'The isolated base must not contain the repository root.'
}

function onexit() {
    local exit_status="${?}"
    trap - EXIT
    if (( LOCK_HELD )); then
        if ! rmdir -- "${REPOSITORY}/.git/isolated-pull.lock"; then
            printf 'Error: could not remove the isolated-pull lock directory.\n' >&2
            exit_status=1
        fi
    fi
    if (( exit_status != 0 )) && [[ -n "${ISOLATED_TREE}" ]]; then
        printf 'The Git directory remains at "%s/.git". Temporary files kept at "%s".\n' \
            "${REPOSITORY}" "${ISOLATED_TREE}" >&2
        if [[ -d "${REPOSITORY}/.git/rebase-merge" || -d "${REPOSITORY}/.git/rebase-apply" ]]; then
            printf 'After Git has stopped, abort using this exact command (never a bare abort in the original tree):\n  git' >&2
            printf ' %q' "${ISOLATED_GIT_ARGUMENTS[@]}" rebase --abort >&2
            printf '\n' >&2
        fi
    fi
    exit "${exit_status}"
}

while [[ $# -gt 0 ]]; do
    case "${1}" in
        -h|--help)
            checkexpectedargs "${1}" "${2--}"
            printhelp 0
            ;;
        -r|--repository)
            checkargsvalid "${1}" "${2-}"
            REPOSITORY="${2}"
            shift 2
            ;;
        -b|--base)
            checkargsvalid "${1}" "${2-}"
            ISOLATED_BASE="${2}"
            shift 2
            ;;
        -n|--dry-run)
            checkexpectedargs "${1}" "${2--}"
            DRY_RUN=1
            shift
            ;;
        -c|--clean)
            checkexpectedargs "${1}" "${2--}"
            CLEAN_TREE=1
            shift
            ;;
        *)
            printf 'Error: Unknown parameter "%s".\n' "${1}" >&2
            printhelp 1
            ;;
    esac
done

checkpreconditions
printf 'Upstream: %s\nRepository root: %s\nIsolated base: %s\n' "${UPSTREAM}" "${REPOSITORY}" "${ISOLATED_BASE}"
printf 'Steps: create temporary tree; git reset --hard HEAD there; git pull --rebase there.\n'
printf 'The original .git stays in place; the original work tree is never written.\n'
if (( DRY_RUN )); then
    exit 0
fi

# This lock serializes this helper only; other Git clients must remain idle.
trap onexit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
mkdir -- "${REPOSITORY}/.git/isolated-pull.lock"
LOCK_HELD=1
mkdir -p -- "${ISOLATED_BASE}"
ISOLATED_TREE="$(mktemp -d -- "${ISOLATED_BASE}/run-XXXXXXXX")"
ISOLATED_TREE="$(cd -- "${ISOLATED_TREE}" && pwd -P)"
ISOLATED_GIT_ARGUMENTS=(
    --git-dir="${REPOSITORY}/.git"
    --work-tree="${ISOLATED_TREE}"
    -c core.hooksPath=/dev/null
    -c submodule.recurse=false
    -c fetch.recurseSubmodules=false
    -c rebase.updateRefs=false
    -c maintenance.auto=false
    -c gc.auto=0
)
printf 'Isolated tree: %s\n' "${ISOLATED_TREE}"
ASSUME_UNCHANGED_BEFORE="$(repositorygit ls-files -v | sed -n 's/^h //p' | LC_ALL=C sort)"
assertisolated
isolatedgit reset --hard HEAD
assertisolated

# Foreground Git owns its subprocesses. No database moves or /proc supervision.
if isolatedgit pull --rebase --no-autostash; then
    printf 'Pull completed. Review the original work tree against the updated history.\n'
else
    PULL_STATUS="${?}"
    printf 'Error: git pull --rebase failed with status %s.\n' "${PULL_STATUS}" >&2
    if [[ -d "${REPOSITORY}/.git/rebase-merge" || -d "${REPOSITORY}/.git/rebase-apply" ]]; then
        assertisolated
        isolatedgit rebase --abort || printf 'Error: automatic rebase abort failed.\n' >&2
    fi
    exit "${PULL_STATUS}"
fi

ASSUME_UNCHANGED_AFTER="$(repositorygit ls-files -v | sed -n 's/^h //p' | LC_ALL=C sort)"
LOST_FLAGS="$(LC_ALL=C comm -23 \
    <(printf '%s\n' "${ASSUME_UNCHANGED_BEFORE}" | sed '/^$/d') \
    <(printf '%s\n' "${ASSUME_UNCHANGED_AFTER}" | sed '/^$/d'))"
if [[ -n "${LOST_FLAGS}" ]]; then
    printf 'Dropped assume-unchanged flags (not reapplied; review these paths):\n%s\n' "${LOST_FLAGS}"
fi
repositorygit status --short

if (( CLEAN_TREE )); then
    [[ "${ISOLATED_TREE}" == "${ISOLATED_BASE}/run-"* && ! -L "${ISOLATED_TREE}" ]] ||
        fail 'Refusing to remove a directory outside this isolated run.'
    [[ ! -e "${ISOLATED_TREE}/.git" ]] || fail 'Refusing to remove an isolated tree containing .git.'
    rm -rf -- "${ISOLATED_TREE}"
    printf 'Removed the isolated tree "%s".\n' "${ISOLATED_TREE}"
else
    printf 'Temporary files kept at "%s" for comparison.\n' "${ISOLATED_TREE}"
fi
