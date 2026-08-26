#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="evandrocoan/dotfiles"
REF="master"
DESTINATION="${HOME}"
FORCE=0
DRY_RUN=0
TEMP_DIRECTORY=""
FOUND_SKILL_COUNT=0
INSTALLED_COUNT=0
SKIPPED_COUNT=0

declare -a GLOBAL_INSTRUCTION_PATHS=(
    ".claude/CLAUDE.md"
    ".codex/AGENTS.md"
    ".copilot/copilot-instructions.md"
)

function printhelp() {
cat >&1 <<EOF

    Usage: bash ${0} [arguments]

    Download and install the Claude, Codex, and GitHub Copilot skills and
    global instructions from https://github.com/${REPOSITORY} without cloning
    the dotfiles repository.

    Skills are stored in ~/.claude/skills and shared with Codex and Copilot
    through ~/.agents/skills. Existing files are preserved unless --force is
    used.

    bash ${0} -h | --help                 (show this help)
    bash ${0} -r | --ref REF              (branch or tag, default: master)
    bash ${0} -d | --destination PATH     (home directory, default: \$HOME)
    bash ${0} -f | --force                (replace matching skills and instructions)
    bash ${0} -n | --dry-run              (show changes without installing)

EOF
    exit 1
}

# ${1} - Option (for example, --ref)
# ${2} - Invalid argument (for example, -f)
function invalidargument() {
    printf 'Error: Invalid argument "%s" for option "%s".\n' "${2}" "${1}" >&2
    printhelp
    exit 1
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
        printhelp
    fi
}

function cleanup() {
    if [[ -n "${TEMP_DIRECTORY}" ]] && [[ -d "${TEMP_DIRECTORY}" ]]; then
        rm -rf -- "${TEMP_DIRECTORY}"
    fi
}

function commandexists() {
    command -v "${1}" >/dev/null
}

function checkdependencies() {
    local command_name
    for command_name in tar mktemp cp mkdir rm ln; do
        if ! commandexists "${command_name}"; then
            printf 'Error: Required command "%s" was not found.\n' "${command_name}" >&2
            exit 1
        fi
    done

    if ! commandexists curl && ! commandexists wget; then
        printf 'Error: Either "curl" or "wget" is required to download the skills.\n' >&2
        exit 1
    fi
}

function downloadarchive() {
    local archive_url="${1}"
    local archive_path="${2}"

    printf 'Downloading skills and instructions from %s at ref %s...\n' "${REPOSITORY}" "${REF}"
    if commandexists curl; then
        curl --proto '=https' --tlsv1.2 --fail --silent --show-error --location \
            --retry 3 --connect-timeout 15 --output "${archive_path}" "${archive_url}"
    else
        wget --https-only --tries=3 --timeout=30 --output-document="${archive_path}" "${archive_url}"
    fi
}

function preparetarget() {
    local target_path="${1}"
    local entry_type="${2}"

    if [[ -e "${target_path}" ]] || [[ -L "${target_path}" ]]; then
        if [[ "${FORCE}" -eq 0 ]]; then
            printf 'Skipped existing %s: %s\n' "${entry_type}" "${target_path}"
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            return 1
        fi

        if [[ "${DRY_RUN}" -eq 0 ]]; then
            rm -rf -- "${target_path}"
        fi
        printf 'Replacing %s: %s\n' "${entry_type}" "${target_path}"
    else
        printf 'Installing %s: %s\n' "${entry_type}" "${target_path}"
    fi
}

function installarchiveentry() {
    local source_path="${1}"
    local target_path="${2}"
    local entry_type="${3}"
    local dereference_source="${4}"
    local target_directory="${target_path%/*}"

    if ! preparetarget "${target_path}" "${entry_type}"; then
        return
    fi

    if [[ "${DRY_RUN}" -eq 0 ]]; then
        mkdir -p -- "${target_directory}"
        if [[ "${dereference_source}" -eq 1 ]]; then
            cp -aL -- "${source_path}" "${target_path}"
        else
            cp -a -- "${source_path}" "${target_path}"
        fi
    fi
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
}

function installrelativelink() {
    local link_target="${1}"
    local target_path="${2}"
    local target_directory="${target_path%/*}"

    if ! preparetarget "${target_path}" "shared skill link"; then
        return
    fi

    if [[ "${DRY_RUN}" -eq 0 ]]; then
        mkdir -p -- "${target_directory}"
        ln -s -- "${link_target}" "${target_path}"
    fi
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
}

function installskills() {
    local source_directory="${1}/.claude/skills"
    local source_path
    local skill_name
    local claude_target_path
    local shared_target_path

    if [[ ! -d "${source_directory}" ]]; then
        return
    fi

    for source_path in "${source_directory}"/*; do
        if [[ ! -f "${source_path}/SKILL.md" ]]; then
            continue
        fi

        FOUND_SKILL_COUNT=$((FOUND_SKILL_COUNT + 1))
        skill_name="${source_path##*/}"
        claude_target_path="${DESTINATION}/.claude/skills/${skill_name}"
        shared_target_path="${DESTINATION}/.agents/skills/${skill_name}"

        installarchiveentry "${source_path}" "${claude_target_path}" "Claude skill" 1
        installrelativelink "../../.claude/skills/${skill_name}" "${shared_target_path}"
    done
}

function installglobalinstructions() {
    local source_directory="${1}"
    local relative_path
    local source_path
    local target_path

    for relative_path in "${GLOBAL_INSTRUCTION_PATHS[@]}"; do
        source_path="${source_directory}/${relative_path}"
        target_path="${DESTINATION}/${relative_path}"

        if [[ ! -e "${source_path}" ]] && [[ ! -L "${source_path}" ]]; then
            printf 'Error: Global instruction source was not found: %s\n' "${relative_path}" >&2
            exit 1
        fi

        installarchiveentry "${source_path}" "${target_path}" "global instructions" 0
    done
}

while [[ $# -gt 0 ]]; do
    case "${1}" in
        -h|--help)
            checkexpectedargs "${1}" "${2--}"
            printhelp
            ;;
        -r|--ref)
            checkargsvalid "${1}" "${2-}"
            REF="${2}"
            shift 2
            ;;
        -d|--destination)
            checkargsvalid "${1}" "${2-}"
            DESTINATION="${2}"
            shift 2
            ;;
        -f|--force)
            checkexpectedargs "${1}" "${2--}"
            FORCE=1
            shift
            ;;
        -n|--dry-run)
            checkexpectedargs "${1}" "${2--}"
            DRY_RUN=1
            shift
            ;;
        *)
            printf 'Error: Unknown parameter "%s".\n' "${1}" >&2
            printhelp
            ;;
    esac
done

if [[ ! "${REF}" =~ ^[A-Za-z0-9._/-]+$ ]] || [[ "${REF}" == *..* ]]; then
    invalidargument "--ref" "${REF}"
fi

checkdependencies
trap cleanup EXIT

TEMP_DIRECTORY="$(mktemp -d)"
ARCHIVE_PATH="${TEMP_DIRECTORY}/dotfiles.tar.gz"
SOURCE_DIRECTORY="${TEMP_DIRECTORY}/source"
ARCHIVE_URL="https://codeload.github.com/${REPOSITORY}/tar.gz/${REF}"

mkdir -p -- "${SOURCE_DIRECTORY}"
downloadarchive "${ARCHIVE_URL}" "${ARCHIVE_PATH}"
tar -xzf "${ARCHIVE_PATH}" -C "${SOURCE_DIRECTORY}" --strip-components=1

installskills "${SOURCE_DIRECTORY}"

if [[ "${FOUND_SKILL_COUNT}" -eq 0 ]]; then
    printf 'Error: No skills were found in %s at ref %s.\n' "${REPOSITORY}" "${REF}" >&2
    exit 1
fi

installglobalinstructions "${SOURCE_DIRECTORY}"

if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf 'Dry run complete: %d change(s), %d existing item(s) skipped.\n' "${INSTALLED_COUNT}" "${SKIPPED_COUNT}"
else
    printf 'Installation complete: %d change(s), %d existing item(s) skipped.\n' "${INSTALLED_COUNT}" "${SKIPPED_COUNT}"
fi
