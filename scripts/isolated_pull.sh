#!/usr/bin/env bash
set -euo pipefail

# Update a repository whose work tree must never be written by Git. See
# "Update the repository with an isolated pull" in README.md for the runbook.

REPOSITORY="${HOME}"
ISOLATED_BASE=''
ISOLATED_TREE=''
DRY_RUN=0
CLEAN_TREE=0
GIT_DIRECTORY_MOVED=0
PULL_CHILD_PID=0
ASSUME_UNCHANGED_BEFORE=''
ISOLATED_GIT_ARGUMENTS=()
PENDING_STATE_REMAINS=0

function printhelp() {
    local exit_status="${1}"

cat >&1 <<EOF

    Usage: bash ${0} [arguments]

    Update a repository whose work tree must never be written by Git: move its
    .git into a fresh isolated directory, materialize a clean tree there, run
    git pull --rebase inside it, then return .git to the repository root on
    every exit path, including failure, rebase conflict and interruption.

    Nothing in the repository root is reverted, deleted or stashed. Reviewing
    the resulting difference and deciding what to keep stays a manual step.

    bash ${0} -h | --help                (show this help)
    bash ${0} -r | --repository <path>   (repository root, default: \${HOME})
    bash ${0} -b | --base <path>         (isolated base, default: <root>/.local/state/isolated-pull)
    bash ${0} -n | --dry-run             (check preconditions and print the plan only)
    bash ${0} -c | --clean               (remove the isolated tree after a successful run)

EOF
    exit "${exit_status}"
}

# ${1} - Option (for example, --repository)
# ${2} - Invalid argument (for example, -k)
function invalidargument() {
    printf 'Error: Invalid argument "%s" for option "%s".\n' "${2}" "${1}" >&2
    printhelp 1
}

function checkargsvalid() {
    local argument_value="${2-}"
    if [[ -z "${argument_value}" ]] || [[ "${argument_value}" == '-'* ]]; then
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

# Every read of the repository root is read-only and must not create a lock the
# precondition check would then refuse on.
function repositorygit() {
    GIT_OPTIONAL_LOCKS=0 git -C "${REPOSITORY}" "${@}"
}

# Repository discovery is disabled on purpose: the isolated tree lives inside
# the repository root, so a discovering command could resolve the root itself.
# The arguments are kept in an array so the pull can run as a simple command:
# backgrounding a function would make ${!} a subshell wrapper, and terminating
# that wrapper would leave the real git process holding the database while it
# moves.
function setisolatedgitarguments() {
    ISOLATED_GIT_ARGUMENTS=(
        --git-dir="${ISOLATED_TREE}/.git"
        --work-tree="${ISOLATED_TREE}"
        -c fetch.recurseSubmodules=no
        -c submodule.recurse=false
        -c core.hooksPath=/dev/null
    )
}

function isolatedgit() {
    git "${ISOLATED_GIT_ARGUMENTS[@]}" "${@}"
}

function assumeunchangedpaths() {
    repositorygit ls-files -v | sed -n 's/^h //p' | sort
}

function checkrepository() {
    local toplevel
    if [[ ! -d "${REPOSITORY}" ]]; then
        fail "Repository root \"${REPOSITORY}\" is not a directory."
    fi
    REPOSITORY="$(cd -- "${REPOSITORY}" && pwd -P)"
    if [[ ! -e "${REPOSITORY}/.git" ]]; then
        fail "\"${REPOSITORY}/.git\" does not exist."
    fi
    if [[ ! -d "${REPOSITORY}/.git" ]]; then
        fail "\"${REPOSITORY}/.git\" is not a directory. A linked worktree or a submodule cannot be isolated this way."
    fi
    toplevel="$(cd -- "$(repositorygit rev-parse --show-toplevel)" && pwd -P)"
    if [[ "${toplevel}" != "${REPOSITORY}" ]]; then
        fail "\"${REPOSITORY}\" is not the repository root; Git reports \"${toplevel}\"."
    fi
}

function checknopendingoperation() {
    local marker
    for marker in rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD BISECT_LOG; do
        if [[ -e "${REPOSITORY}/.git/${marker}" ]]; then
            fail "A Git operation is already in progress (.git/${marker}). Finish or abort it first."
        fi
    done
}

function checkindexisclean() {
    if ! repositorygit diff --cached --quiet; then
        fail 'The index holds staged changes. Materializing the clean tree rewrites the shared index, so unstage or commit them first.'
    fi
    if [[ -n "$(repositorygit ls-files -u)" ]]; then
        fail 'The index holds unmerged entries. Resolve them first.'
    fi
}

function checksingleworktree() {
    local worktree_count
    worktree_count="$(repositorygit worktree list | wc -l)"
    if (( worktree_count != 1 )); then
        fail "The repository has ${worktree_count} registered worktrees. Moving .git breaks the linked worktrees' gitdir pointers."
    fi
}

function checkupstream() {
    local upstream
    if ! upstream="$(repositorygit rev-parse --abbrev-ref --symbolic-full-name '@{u}')"; then
        fail 'The current branch has no upstream; there is nothing to pull.'
    fi
    printf 'Upstream: %s\n' "${upstream}"
}

# Runs after every other read, so the script's own inspection cannot create the
# lock this refuses on.
function checknolocks() {
    local lock_file
    lock_file="$(find "${REPOSITORY}/.git" -path "${REPOSITORY}/.git/objects" -prune -o -name '*.lock' -print -quit)"
    if [[ -n "${lock_file}" ]]; then
        fail "Another Git process is active in the repository root (\"${lock_file}\"). Wait for it to finish."
    fi
}

function checkisolatedbase() {
    local repository_device base_device repository_mount base_mount
    local base_prefix
    if [[ -z "${ISOLATED_BASE}" ]]; then
        ISOLATED_BASE="${REPOSITORY}/.local/state/isolated-pull"
    fi
    # Resolved without creating anything, so a rejected base leaves no directory
    # behind, and a trailing slash or "/" cannot break the prefix comparisons.
    ISOLATED_BASE="$(realpath -m -- "${ISOLATED_BASE}")"
    base_prefix="${ISOLATED_BASE%/}/"
    if [[ "${base_prefix}" == "${REPOSITORY}/.git/"* ]]; then
        fail "The isolated base \"${ISOLATED_BASE}\" is inside the repository database."
    fi
    if [[ "${REPOSITORY}/" == "${base_prefix}"* ]]; then
        fail "The isolated base \"${ISOLATED_BASE}\" contains the repository root."
    fi
    mkdir -p -- "${ISOLATED_BASE}"
    repository_device="$(stat -c '%d' -- "${REPOSITORY}")"
    base_device="$(stat -c '%d' -- "${ISOLATED_BASE}")"
    repository_mount="$(stat -c '%m' -- "${REPOSITORY}")"
    base_mount="$(stat -c '%m' -- "${ISOLATED_BASE}")"
    if [[ "${repository_device}" != "${base_device}" ]] || [[ "${repository_mount}" != "${base_mount}" ]]; then
        fail "The isolated base must share the repository's device and mount point, so moving .git is a rename and never an interruptible copy. Repository: device ${repository_device} at ${repository_mount}. Base: device ${base_device} at ${base_mount}."
    fi
}

function checkpreconditions() {
    checkrepository
    checknopendingoperation
    checkindexisclean
    checksingleworktree
    checkupstream
    checknolocks
    checkisolatedbase
}

function printplan() {
    printf 'Repository root: %s\n' "${REPOSITORY}"
    printf 'Isolated base:   %s\n' "${ISOLATED_BASE}"
    printf 'Planned steps:\n'
    printf '  1. mktemp -d under the isolated base\n'
    printf '  2. mv -T -- %s/.git <isolated tree>/.git\n' "${REPOSITORY}"
    printf '  3. git reset --hard inside the isolated tree\n'
    printf '  4. git pull --rebase inside the isolated tree\n'
    printf '  5. mv -T -- <isolated tree>/.git %s/.git\n' "${REPOSITORY}"
    printf 'The repository work tree is never written; review its difference afterwards.\n'
}

function assertisolated() {
    local git_directory
    if [[ ! -d "${ISOLATED_TREE}/.git" ]]; then
        fail 'The isolated Git directory is missing.'
    fi
    git_directory="$(isolatedgit rev-parse --absolute-git-dir)"
    if [[ "${git_directory}" != "${ISOLATED_TREE}/.git" ]]; then
        fail "Refusing to continue: Git resolved \"${git_directory}\" instead of the isolated directory."
    fi
}

function movegitdirectory() {
    if [[ -e "${ISOLATED_TREE}/.git" ]]; then
        fail "The isolated tree \"${ISOLATED_TREE}\" already holds a .git directory."
    fi
    mv -T -- "${REPOSITORY}/.git" "${ISOLATED_TREE}/.git"
    GIT_DIRECTORY_MOVED=1
    printf 'Isolated tree:   %s\n' "${ISOLATED_TREE}"
}

function materializecleantree() {
    assertisolated
    isolatedgit reset --hard
}

function runpull() {
    local pull_status=0
    assertisolated
    git "${ISOLATED_GIT_ARGUMENTS[@]}" pull --rebase &
    PULL_CHILD_PID="${!}"
    set +e
    wait "${PULL_CHILD_PID}"
    pull_status="${?}"
    set -e
    PULL_CHILD_PID=0
    if (( pull_status != 0 )); then
        printf 'Error: "git pull --rebase" failed with status %s inside the isolated tree.\n' "${pull_status}" >&2
        exit "${pull_status}"
    fi
}

function stoppullchild() {
    if (( PULL_CHILD_PID == 0 )); then
        return 0
    fi
    if [[ -d "/proc/${PULL_CHILD_PID}" ]]; then
        kill -TERM "${PULL_CHILD_PID}" || true
    fi
    wait "${PULL_CHILD_PID}" || true
    PULL_CHILD_PID=0
}

# A partially replayed rebase must never reach the repository root, so the
# isolated rebase is aborted first. That returns the branch to its pre-rebase
# tip and keeps every local commit.
function abortpendingoperation() {
    local marker
    if [[ -d "${ISOLATED_TREE}/.git/rebase-merge" ]] || [[ -d "${ISOLATED_TREE}/.git/rebase-apply" ]]; then
        isolatedgit rebase --abort || true
    fi
    if [[ -e "${ISOLATED_TREE}/.git/MERGE_HEAD" ]]; then
        isolatedgit merge --abort || true
    fi
    for marker in rebase-merge rebase-apply MERGE_HEAD; do
        if [[ -e "${ISOLATED_TREE}/.git/${marker}" ]]; then
            PENDING_STATE_REMAINS=1
        fi
    done
}

function restoregitdirectory() {
    if (( GIT_DIRECTORY_MOVED == 0 )); then
        return 0
    fi
    abortpendingoperation
    if [[ -e "${REPOSITORY}/.git" ]]; then
        printf 'Error: "%s/.git" reappeared, so the database stays in the isolated tree.\n' "${REPOSITORY}" >&2
        printf 'Recover with: mv -T -- "%s/.git" "%s/.git"\n' "${ISOLATED_TREE}" "${REPOSITORY}" >&2
        return 1
    fi
    if mv -T -- "${ISOLATED_TREE}/.git" "${REPOSITORY}/.git"; then
        GIT_DIRECTORY_MOVED=0
        if (( PENDING_STATE_REMAINS == 1 )); then
            printf 'Warning: the isolated rebase or merge could not be aborted, so "%s/.git" carries unfinished state.\n' "${REPOSITORY}" >&2
            printf 'The next run will refuse to start. See "Recover an interrupted isolated pull" in README.md.\n' >&2
            return 1
        fi
        printf 'Returned the Git directory to "%s/.git".\n' "${REPOSITORY}"
        return 0
    fi
    printf 'Error: could not return the Git directory to "%s".\n' "${REPOSITORY}" >&2
    printf 'Recover with: mv -T -- "%s/.git" "%s/.git"\n' "${ISOLATED_TREE}" "${REPOSITORY}" >&2
    return 1
}

function reportassumeunchanged() {
    local lost
    lost="$(comm -23 \
        <(printf '%s' "${ASSUME_UNCHANGED_BEFORE}" | sed '/^$/d') \
        <(assumeunchangedpaths | sed '/^$/d'))"
    if [[ -z "${lost}" ]]; then
        printf 'No assume-unchanged flag was dropped.\n'
        return 0
    fi
    printf 'The pull dropped assume-unchanged for these paths, which now appear as modified:\n'
    printf '%s\n' "${lost}" | sed 's/^/  /'
    printf 'They are not re-applied automatically, because that would hide the upstream change.\n'
    printf 'After reviewing them, re-apply with:\n'
    printf '  git -C "%s" update-index --assume-unchanged <path>...\n' "${REPOSITORY}"
}

function report() {
    printf '\nReview the repository root now. Its work tree still holds the previous content:\n'
    repositorygit status --short
    if (( CLEAN_TREE == 0 )); then
        printf '\nThe isolated tree holds the new content of every tracked file, so a file can be\n'
        printf 'compared without Git: diff "%s/<path>" "%s/<path>"\n' "${REPOSITORY}" "${ISOLATED_TREE}"
    fi
    printf '\n'
    reportassumeunchanged
}

function cleanisolatedtree() {
    if (( CLEAN_TREE == 0 )); then
        printf '\nThe isolated tree was kept at "%s".\n' "${ISOLATED_TREE}"
        return 0
    fi
    if [[ -e "${ISOLATED_TREE}/.git" ]]; then
        fail "Refusing to remove \"${ISOLATED_TREE}\": it still holds a .git directory."
    fi
    if [[ ! -f "${REPOSITORY}/.git/HEAD" ]]; then
        fail "Refusing to remove \"${ISOLATED_TREE}\": \"${REPOSITORY}/.git/HEAD\" is missing."
    fi
    if [[ "${REPOSITORY}/" == "${ISOLATED_TREE}/"* ]]; then
        fail "Refusing to remove \"${ISOLATED_TREE}\": it contains the repository root."
    fi
    rm -rf -- "${ISOLATED_TREE}"
    printf '\nRemoved the isolated tree "%s".\n' "${ISOLATED_TREE}"
}

function onexit() {
    local exit_status="${?}"
    # A second interruption must not abandon the database outside the
    # repository root, so signals are ignored for the rest of the handler.
    trap '' INT TERM HUP
    set +e
    stoppullchild
    if ! restoregitdirectory; then
        exit_status=1
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
ASSUME_UNCHANGED_BEFORE="$(assumeunchangedpaths)"
printplan

if (( DRY_RUN == 1 )); then
    printf 'Dry run: nothing was moved.\n'
    exit 0
fi

ISOLATED_TREE="$(mktemp -d -- "${ISOLATED_BASE}/run-XXXXXXXX")"
setisolatedgitarguments
trap onexit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

movegitdirectory
materializecleantree
runpull
restoregitdirectory
report
cleanisolatedtree
