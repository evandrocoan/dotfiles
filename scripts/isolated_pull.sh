#!/usr/bin/env bash
set -euo pipefail

# Update a repository whose work tree must never be written by Git. See
# "Update the repository with an isolated pull" in README.md for the runbook.

REPOSITORY="${HOME}"
ISOLATED_BASE=''
ISOLATED_TREE=''
DRY_RUN=0
CLEAN_TREE=0
PULL_CHILD_PID=0
PULL_PROCESS_GROUP=0
PULL_INTERRUPTED=0
PULL_STOP_FAILED=0
ASSUME_UNCHANGED_BEFORE=''
ISOLATED_GIT_ARGUMENTS=()

function printhelp() {
    local exit_status="${1}"

cat >&1 <<EOF

    Usage: bash ${0} [arguments]

    Update a repository whose work tree must never be written by Git: move its
    .git into a fresh isolated directory, materialize a clean tree there, run
    git pull --rebase inside it, then return .git to the repository root when
    the supervised pull process group has stopped and any unfinished operation
    was aborted.
    Otherwise .git stays isolated for manual recovery.

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
        -c maintenance.auto=false
        -c gc.auto=0
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
function findgitlock() {
    local git_directory="${1}" lock_file
    if ! lock_file="$(find "${git_directory}" -path "${git_directory}/objects" -prune -o -name '*.lock' -print -quit)"; then
        return 1
    fi
    if [[ -z "${lock_file}" ]] && [[ -d "${git_directory}/objects/pack" ]]; then
        if ! lock_file="$(find "${git_directory}/objects/pack" -name '*.lock' -print -quit)"; then
            return 1
        fi
    fi
    if [[ -z "${lock_file}" ]] && [[ -d "${git_directory}/objects/info" ]]; then
        if ! lock_file="$(find "${git_directory}/objects/info" -name '*.lock' -print -quit)"; then
            return 1
        fi
    fi
    printf '%s' "${lock_file}"
}

function checknolocks() {
    local lock_file
    if ! lock_file="$(findgitlock "${REPOSITORY}/.git")"; then
        fail 'Could not inspect Git locks in the repository root.'
    fi
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
    printf 'Isolated tree:   %s\n' "${ISOLATED_TREE}"
}

function materializecleantree() {
    assertisolated
    isolatedgit reset --hard
}

function runpull() {
    local pull_status=0
    assertisolated
    # Job control gives the pull and its descendants a separate process group.
    # The exit handler can then stop all of them without signalling this shell.
    trap 'PULL_INTERRUPTED=130' INT
    trap 'PULL_INTERRUPTED=143' TERM
    trap 'PULL_INTERRUPTED=129' HUP
    set -m
    git "${ISOLATED_GIT_ARGUMENTS[@]}" pull --rebase &
    PULL_CHILD_PID="${!}"
    PULL_PROCESS_GROUP="${PULL_CHILD_PID}"
    printf '%s\n' "${PULL_PROCESS_GROUP}" > "${ISOLATED_TREE}/pull-process-group"
    set +m
    trap 'exit 130' INT
    trap 'exit 143' TERM
    trap 'exit 129' HUP
    if (( PULL_INTERRUPTED != 0 )); then
        exit "${PULL_INTERRUPTED}"
    fi
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

# Linux process state distinguishes live members from orphaned zombies, which
# cannot access the database but can remain visible until init reaps them.
function processgroupisactive() {
    local stat_file stat_line stat_tail state parent_pid process_group rest
    if [[ ! -d /proc ]]; then
        return 2
    fi
    for stat_file in /proc/[0-9]*/stat; do
        if [[ ! -r "${stat_file}" ]]; then
            if [[ -e "${stat_file}" ]]; then
                return 2
            fi
            continue
        fi
        if ! IFS= read -r stat_line < "${stat_file}"; then
            if [[ -e "${stat_file}" ]]; then
                return 2
            fi
            continue
        fi
        stat_tail="${stat_line##*) }"
        read -r state parent_pid process_group rest <<< "${stat_tail}"
        if [[ "${process_group}" == "${PULL_PROCESS_GROUP}" ]] && [[ "${state}" != Z ]] && [[ "${state}" != X ]]; then
            return 0
        fi
    done
    return 1
}

function stoppullchild() {
    local attempt group_status
    if (( PULL_PROCESS_GROUP == 0 )); then
        return 0
    fi
    if processgroupisactive; then
        kill -TERM -- "-${PULL_PROCESS_GROUP}" || true
    else
        group_status="${?}"
        if (( group_status != 1 )); then
            printf 'Error: cannot inspect pull process group %s; the Git directory remains at "%s/.git".\n' \
                "${PULL_PROCESS_GROUP}" "${ISOLATED_TREE}" >&2
            printf 'See "Recover an interrupted isolated pull" in README.md before returning it.\n' >&2
            PULL_STOP_FAILED=1
            return 1
        fi
    fi
    for (( attempt = 0; attempt < 10; attempt++ )); do
        if processgroupisactive; then
            sleep 0.1
            continue
        else
            group_status="${?}"
        fi
        if (( group_status == 1 )); then
            if (( PULL_CHILD_PID != 0 )); then
                wait "${PULL_CHILD_PID}" || true
                PULL_CHILD_PID=0
            fi
            if ! rm -f -- "${ISOLATED_TREE}/pull-process-group"; then
                printf 'Error: cannot clear the pull process marker in "%s"; the Git directory remains at "%s/.git".\n' \
                    "${ISOLATED_TREE}" "${ISOLATED_TREE}" >&2
                printf 'See "Recover an interrupted isolated pull" in README.md before returning it.\n' >&2
                PULL_STOP_FAILED=1
                return 1
            fi
            PULL_PROCESS_GROUP=0
            return 0
        fi
        break
    done
    printf 'Error: pull process group %s may still use the Git directory; it remains isolated at "%s/.git".\n' \
        "${PULL_PROCESS_GROUP}" "${ISOLATED_TREE}" >&2
    printf 'See "Recover an interrupted isolated pull" in README.md before returning it.\n' >&2
    PULL_STOP_FAILED=1
    return 1
}

# A partially replayed rebase must never reach the repository root, so the
# isolated rebase is aborted first. That returns the branch to its pre-rebase
# tip and keeps every local commit.
function abortpendingoperation() {
    local marker abort_failed=0
    if [[ -d "${ISOLATED_TREE}/.git/rebase-merge" ]] || [[ -d "${ISOLATED_TREE}/.git/rebase-apply" ]]; then
        if ! isolatedgit rebase --abort; then
            abort_failed=1
        fi
    fi
    if [[ -e "${ISOLATED_TREE}/.git/MERGE_HEAD" ]]; then
        if ! isolatedgit merge --abort; then
            abort_failed=1
        fi
    fi
    for marker in rebase-merge rebase-apply MERGE_HEAD; do
        if [[ -e "${ISOLATED_TREE}/.git/${marker}" ]]; then
            abort_failed=1
        fi
    done
    (( abort_failed == 0 ))
}

function restoregitdirectory() {
    local lock_file
    # A signal can arrive after either atomic rename and before the next shell
    # assignment. The directory locations, rather than a flag, decide recovery.
    if [[ -e "${REPOSITORY}/.git" ]] || [[ -L "${REPOSITORY}/.git" ]]; then
        if [[ -e "${ISOLATED_TREE}/.git" ]] || [[ -L "${ISOLATED_TREE}/.git" ]]; then
            printf 'Error: "%s/.git" reappeared while the database remains at "%s/.git".\n' \
                "${REPOSITORY}" "${ISOLATED_TREE}" >&2
            printf 'See "Recover an interrupted isolated pull" in README.md; resolve the collision before moving the database.\n' >&2
            return 1
        fi
        return 0
    fi
    if [[ ! -d "${ISOLATED_TREE}/.git" ]]; then
        printf 'Error: the Git directory is missing from both "%s" and "%s".\n' \
            "${REPOSITORY}" "${ISOLATED_TREE}" >&2
        return 1
    fi
    if ! abortpendingoperation; then
        printf 'Error: the isolated rebase or merge could not be fully aborted; the Git directory remains at "%s/.git".\n' \
            "${ISOLATED_TREE}" >&2
        printf 'See "Recover an interrupted isolated pull" in README.md before returning it.\n' >&2
        return 1
    fi
    if ! lock_file="$(findgitlock "${ISOLATED_TREE}/.git")"; then
        printf 'Error: cannot inspect locks in "%s/.git"; the database remains isolated.\n' "${ISOLATED_TREE}" >&2
        return 1
    fi
    if [[ -n "${lock_file}" ]]; then
        printf 'Error: the isolated Git directory still has a lock at "%s"; it remains at "%s/.git".\n' \
            "${lock_file}" "${ISOLATED_TREE}" >&2
        printf 'See "Recover an interrupted isolated pull" in README.md before returning it.\n' >&2
        return 1
    fi
    if mv -T -- "${ISOLATED_TREE}/.git" "${REPOSITORY}/.git"; then
        printf 'Returned the Git directory to "%s/.git".\n' "${REPOSITORY}"
        return 0
    fi
    printf 'Error: could not return the Git directory to "%s".\n' "${REPOSITORY}" >&2
    printf 'The database remains at "%s/.git". See "Recover an interrupted isolated pull" in README.md.\n' \
        "${ISOLATED_TREE}" >&2
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
    if (( PULL_STOP_FAILED == 1 )); then
        exit_status=1
    elif ! stoppullchild; then
        exit_status=1
    elif ! restoregitdirectory; then
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
stoppullchild
restoregitdirectory
report
cleanisolatedtree
