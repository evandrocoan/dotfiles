#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="evandrocoan/dotfiles"
REF="master"
DESTINATION="${HOME}"
STATE_FORMAT_VERSION="1"
STATE_DIRECTORY=""
STATE_PATH=""
STATE_TEMP_PATH=""
FORCE=0
DRY_RUN=0
TEMP_DIRECTORY=""
FOUND_SKILL_COUNT=0
INSTALLED_COUNT=0
SKIPPED_COUNT=0
PRUNED_COUNT=0
UNMANAGED_SKIPPED_COUNT=0
DISOWNED_COUNT=0

declare -A PREVIOUS_MANAGED_ENTRIES=()
declare -A PREVIOUS_MANAGED_ENTRY_DIGESTS=()
declare -a PREVIOUS_MANAGED_ENTRY_ORDER=()
declare -A DESIRED_MANAGED_ENTRIES=()
declare -A NEXT_MANAGED_ENTRIES=()
declare -A NEXT_MANAGED_ENTRY_DIGESTS=()
declare -a NEXT_MANAGED_ENTRY_ORDER=()
declare -A SOURCE_SKILL_DIGESTS=()

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

    Skills are installed canonically in ~/.claude/skills and shared with Codex
    and Copilot through relative links in ~/.agents/skills. Existing files are
    preserved unless --force is used. Managed skills are recorded below the
    selected destination in .local/state/install-ia-skills/manifest. With
    --force, managed entries absent from the downloaded version are removed.
    Modified discontinued skills are preserved and removed from the control
    file.

    bash ${0} -h | --help                 (show this help)
    bash ${0} -r | --ref REF              (branch or tag, default: master)
    bash ${0} -d | --destination PATH     (home directory, default: \$HOME)
    bash ${0} -f | --force                (replace current and remove discontinued managed skills)
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
    if [[ -n "${STATE_TEMP_PATH}" ]] && [[ -e "${STATE_TEMP_PATH}" ]]; then
        rm -f -- "${STATE_TEMP_PATH}"
    fi

    if [[ -n "${TEMP_DIRECTORY}" ]] && [[ -d "${TEMP_DIRECTORY}" ]]; then
        rm -rf -- "${TEMP_DIRECTORY}"
    fi
}

function commandexists() {
    command -v "${1}" >/dev/null
}

function checkdependencies() {
    local command_name
    for command_name in tar mktemp cp mkdir rm ln mv readlink sha256sum; do
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

function validateskillname() {
    local skill_name="${1}"

    [[ "${skill_name}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]
}

function calculateskilldigest() {
    local skill_path="${1}"
    local parent_directory="${skill_path%/*}"
    local skill_name="${skill_path##*/}"
    local digest_output

    digest_output="$(
        tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner --format=gnu \
            -cf - -C "${parent_directory}" "${skill_name}" |
            sha256sum
    )"
    printf '%s\n' "${digest_output%% *}"
}

function invalidstate() {
    local reason="${1}"

    printf 'Error: Invalid control file "%s": %s.\n' "${STATE_PATH}" "${reason}" >&2
    exit 1
}

function loadstate() {
    local line
    local line_number=0
    local state_ref
    local entry
    local entry_type
    local entry_payload
    local skill_name
    local skill_digest

    if [[ ! -e "${STATE_PATH}" ]] && [[ ! -L "${STATE_PATH}" ]]; then
        return
    fi

    if [[ -L "${STATE_PATH}" ]] || [[ ! -f "${STATE_PATH}" ]]; then
        invalidstate "expected a regular file, not a symbolic link or directory"
    fi

    while IFS= read -r line || [[ -n "${line}" ]]; do
        line_number=$((line_number + 1))

        case "${line_number}" in
            1)
                if [[ "${line}" != "format=${STATE_FORMAT_VERSION}" ]]; then
                    invalidstate "unsupported format on line 1"
                fi
                ;;
            2)
                if [[ "${line}" != "repository=${REPOSITORY}" ]]; then
                    invalidstate "unexpected repository on line 2"
                fi
                ;;
            3)
                if [[ "${line}" != last-successful-ref=* ]]; then
                    invalidstate "missing ref on line 3"
                fi
                state_ref="${line#last-successful-ref=}"
                if [[ ! "${state_ref}" =~ ^[A-Za-z0-9._/-]+$ ]] || [[ "${state_ref}" == *..* ]]; then
                    invalidstate "invalid ref on line 3"
                fi
                ;;
            *)
                case "${line}" in
                    canonical=*" sha256="*)
                        entry_type="canonical"
                        entry_payload="${line#canonical=}"
                        skill_name="${entry_payload%% sha256=*}"
                        skill_digest="${entry_payload#* sha256=}"
                        if [[ "${line}" != "canonical=${skill_name} sha256=${skill_digest}" ]] ||
                            [[ ! "${skill_digest}" =~ ^[0-9a-f]{64}$ ]]; then
                            invalidstate "invalid canonical skill digest on line ${line_number}"
                        fi
                        entry="canonical=${skill_name}"
                        ;;
                    shared-link=*)
                        entry_type="shared-link"
                        skill_name="${line#shared-link=}"
                        skill_digest=""
                        entry="shared-link=${skill_name}"
                        ;;
                    *)
                        invalidstate "unknown entry on line ${line_number}"
                        ;;
                esac

                case "${entry_type}" in
                    canonical|shared-link)
                        if ! validateskillname "${skill_name}"; then
                            invalidstate "invalid skill name on line ${line_number}"
                        fi
                        if [[ -n "${PREVIOUS_MANAGED_ENTRIES["${entry}"]+present}" ]]; then
                            invalidstate "duplicate entry on line ${line_number}"
                        fi
                        PREVIOUS_MANAGED_ENTRIES["${entry}"]="${entry_type}"
                        PREVIOUS_MANAGED_ENTRY_DIGESTS["${entry}"]="${skill_digest}"
                        PREVIOUS_MANAGED_ENTRY_ORDER+=("${entry}")
                        ;;
                    *)
                        invalidstate "unknown managed entry type on line ${line_number}"
                        ;;
                esac
                ;;
        esac
    done < "${STATE_PATH}"

    if [[ "${line_number}" -lt 3 ]]; then
        invalidstate "incomplete header"
    fi
}

function markdesired() {
    local entry="${1}"

    DESIRED_MANAGED_ENTRIES["${entry}"]=1
}

function markmanaged() {
    local entry="${1}"
    local skill_digest="${2-}"

    if [[ -n "${NEXT_MANAGED_ENTRIES["${entry}"]+present}" ]]; then
        return
    fi

    case "${entry}" in
        canonical=*)
            if [[ ! "${skill_digest}" =~ ^[0-9a-f]{64}$ ]]; then
                printf 'Error: Cannot manage canonical skill without a valid SHA-256 digest: %s\n' "${entry}" >&2
                exit 1
            fi
            ;;
        shared-link=*)
            skill_digest=""
            ;;
        *)
            printf 'Error: Cannot manage unknown entry: %s\n' "${entry}" >&2
            exit 1
            ;;
    esac

    NEXT_MANAGED_ENTRIES["${entry}"]=1
    NEXT_MANAGED_ENTRY_DIGESTS["${entry}"]="${skill_digest}"
    NEXT_MANAGED_ENTRY_ORDER+=("${entry}")
}

function recordskippedmanagement() {
    local entry="${1}"

    if [[ -n "${PREVIOUS_MANAGED_ENTRIES["${entry}"]+present}" ]]; then
        markmanaged "${entry}" "${PREVIOUS_MANAGED_ENTRY_DIGESTS["${entry}"]}"
    else
        UNMANAGED_SKIPPED_COUNT=$((UNMANAGED_SKIPPED_COUNT + 1))
    fi
}

function writestate() {
    local entry

    if [[ "${DRY_RUN}" -eq 1 ]]; then
        return
    fi

    if [[ -L "${STATE_PATH}" ]] || { [[ -e "${STATE_PATH}" ]] && [[ ! -f "${STATE_PATH}" ]]; }; then
        invalidstate "expected a regular file, not a symbolic link or directory"
    fi

    mkdir -p -- "${STATE_DIRECTORY}"
    STATE_TEMP_PATH="$(mktemp "${STATE_DIRECTORY}/manifest.tmp.XXXXXX")"

    {
        printf 'format=%s\n' "${STATE_FORMAT_VERSION}"
        printf 'repository=%s\n' "${REPOSITORY}"
        printf 'last-successful-ref=%s\n' "${REF}"
        for entry in "${NEXT_MANAGED_ENTRY_ORDER[@]}"; do
            case "${entry}" in
                canonical=*)
                    printf '%s sha256=%s\n' "${entry}" "${NEXT_MANAGED_ENTRY_DIGESTS["${entry}"]}"
                    ;;
                shared-link=*)
                    printf '%s\n' "${entry}"
                    ;;
            esac
        done
    } > "${STATE_TEMP_PATH}"

    mv -- "${STATE_TEMP_PATH}" "${STATE_PATH}"
    STATE_TEMP_PATH=""
    printf 'Updated control file: %s\n' "${STATE_PATH}"
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
    local managed_entry="${4}"
    local managed_digest="${5-}"
    local target_directory="${target_path%/*}"

    if ! preparetarget "${target_path}" "${entry_type}"; then
        if [[ -n "${managed_entry}" ]]; then
            recordskippedmanagement "${managed_entry}"
        fi
        return
    fi

    if [[ "${DRY_RUN}" -eq 0 ]]; then
        mkdir -p -- "${target_directory}"
        cp -a -- "${source_path}" "${target_path}"
    fi
    if [[ -n "${managed_entry}" ]]; then
        markmanaged "${managed_entry}" "${managed_digest}"
    fi
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
}

function installrelativelink() {
    local link_target="${1}"
    local target_path="${2}"
    local managed_entry="${3}"
    local target_directory="${target_path%/*}"

    if ! preparetarget "${target_path}" "shared skill link"; then
        recordskippedmanagement "${managed_entry}"
        return
    fi

    if [[ "${DRY_RUN}" -eq 0 ]]; then
        mkdir -p -- "${target_directory}"
        ln -s -- "${link_target}" "${target_path}"
    fi
    markmanaged "${managed_entry}"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
}

function installskills() {
    local source_directory="${1}/.claude/skills"
    local source_path
    local skill_name
    local claude_target_path
    local shared_target_path
    local managed_entry
    local -a skill_source_paths=()

    if [[ ! -d "${source_directory}" ]]; then
        return
    fi

    for source_path in "${source_directory}"/*; do
        if [[ ! -f "${source_path}/SKILL.md" ]]; then
            continue
        fi

        if [[ -L "${source_path}" ]]; then
            printf 'Error: Canonical skill source must be a directory, not a symbolic link: %s\n' "${source_path}" >&2
            exit 1
        fi

        skill_name="${source_path##*/}"
        if ! validateskillname "${skill_name}"; then
            printf 'Error: Invalid skill directory name: %s\n' "${skill_name}" >&2
            exit 1
        fi

        FOUND_SKILL_COUNT=$((FOUND_SKILL_COUNT + 1))
        skill_source_paths+=("${source_path}")
        SOURCE_SKILL_DIGESTS["${skill_name}"]="$(calculateskilldigest "${source_path}")"
        markdesired "canonical=${skill_name}"
        markdesired "shared-link=${skill_name}"
    done

    for source_path in "${skill_source_paths[@]}"; do
        skill_name="${source_path##*/}"
        claude_target_path="${DESTINATION}/.claude/skills/${skill_name}"
        managed_entry="canonical=${skill_name}"

        installarchiveentry "${source_path}" "${claude_target_path}" "canonical skill" \
            "${managed_entry}" "${SOURCE_SKILL_DIGESTS["${skill_name}"]}"
    done

    for source_path in "${skill_source_paths[@]}"; do
        skill_name="${source_path##*/}"
        shared_target_path="${DESTINATION}/.agents/skills/${skill_name}"
        managed_entry="shared-link=${skill_name}"

        installrelativelink "../../.claude/skills/${skill_name}" "${shared_target_path}" "${managed_entry}"
    done
}

function prunediscontinuedentries() {
    local entry
    local skill_name
    local canonical_entry
    local shared_link_entry
    local canonical_target_path
    local shared_link_target_path
    local expected_link_target
    local actual_link_target
    local installed_digest
    local canonical_is_managed
    local shared_link_is_managed
    local changed_managed_item
    local -A processed_skills=()

    for entry in "${PREVIOUS_MANAGED_ENTRY_ORDER[@]}"; do
        skill_name="${entry#*=}"
        if [[ -n "${processed_skills["${skill_name}"]+present}" ]]; then
            continue
        fi
        processed_skills["${skill_name}"]=1

        canonical_entry="canonical=${skill_name}"
        shared_link_entry="shared-link=${skill_name}"
        if [[ -n "${DESIRED_MANAGED_ENTRIES["${canonical_entry}"]+present}" ]]; then
            continue
        fi

        canonical_target_path="${DESTINATION}/.claude/skills/${skill_name}"
        shared_link_target_path="${DESTINATION}/.agents/skills/${skill_name}"
        expected_link_target="../../.claude/skills/${skill_name}"
        canonical_is_managed=0
        shared_link_is_managed=0

        if [[ -n "${PREVIOUS_MANAGED_ENTRIES["${canonical_entry}"]+present}" ]]; then
            canonical_is_managed=1
        fi
        if [[ -n "${PREVIOUS_MANAGED_ENTRIES["${shared_link_entry}"]+present}" ]]; then
            shared_link_is_managed=1
        fi

        if [[ "${FORCE}" -eq 0 ]]; then
            printf 'Preserved discontinued managed skill: %s (use --force to remove)\n' "${skill_name}"
            if [[ "${canonical_is_managed}" -eq 1 ]]; then
                markmanaged "${canonical_entry}" "${PREVIOUS_MANAGED_ENTRY_DIGESTS["${canonical_entry}"]}"
                SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            fi
            if [[ "${shared_link_is_managed}" -eq 1 ]]; then
                markmanaged "${shared_link_entry}"
                SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            fi
            continue
        fi

        changed_managed_item=0
        if [[ "${canonical_is_managed}" -eq 1 ]] &&
            { [[ -e "${canonical_target_path}" ]] || [[ -L "${canonical_target_path}" ]]; }; then
            if [[ -L "${canonical_target_path}" ]] || [[ ! -d "${canonical_target_path}" ]]; then
                changed_managed_item=1
            else
                installed_digest="$(calculateskilldigest "${canonical_target_path}")"
                if [[ "${installed_digest}" != "${PREVIOUS_MANAGED_ENTRY_DIGESTS["${canonical_entry}"]}" ]]; then
                    changed_managed_item=1
                fi
            fi
        fi

        if [[ "${shared_link_is_managed}" -eq 1 ]] &&
            { [[ -e "${shared_link_target_path}" ]] || [[ -L "${shared_link_target_path}" ]]; }; then
            if [[ ! -L "${shared_link_target_path}" ]]; then
                changed_managed_item=1
            else
                actual_link_target="$(readlink -- "${shared_link_target_path}")"
                if [[ "${actual_link_target}" != "${expected_link_target}" ]]; then
                    changed_managed_item=1
                fi
            fi
        fi

        if [[ "${changed_managed_item}" -eq 1 ]]; then
            if [[ "${DRY_RUN}" -eq 1 ]]; then
                printf 'Warning: Would preserve modified discontinued skill and remove it from the control file: %s\n' "${skill_name}" >&2
            else
                printf 'Warning: Preserved modified discontinued skill and removed it from the control file: %s\n' "${skill_name}" >&2
            fi
            DISOWNED_COUNT=$((DISOWNED_COUNT + 1))
            continue
        fi

        if [[ "${canonical_is_managed}" -eq 1 ]]; then
            if [[ -d "${canonical_target_path}" ]] && [[ ! -L "${canonical_target_path}" ]]; then
                printf 'Removing discontinued managed canonical skill: %s\n' "${canonical_target_path}"
                if [[ "${DRY_RUN}" -eq 0 ]]; then
                    rm -rf -- "${canonical_target_path}"
                fi
            else
                printf 'Forgetting missing discontinued managed canonical skill: %s\n' "${canonical_target_path}"
            fi
            PRUNED_COUNT=$((PRUNED_COUNT + 1))
        fi

        if [[ "${shared_link_is_managed}" -eq 1 ]]; then
            if [[ -L "${shared_link_target_path}" ]]; then
                printf 'Removing discontinued managed shared skill link: %s\n' "${shared_link_target_path}"
                if [[ "${DRY_RUN}" -eq 0 ]]; then
                    rm -- "${shared_link_target_path}"
                fi
            else
                printf 'Forgetting missing discontinued managed shared skill link: %s\n' "${shared_link_target_path}"
            fi
            PRUNED_COUNT=$((PRUNED_COUNT + 1))
        fi
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

        installarchiveentry "${source_path}" "${target_path}" "global instructions" "" ""
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

STATE_DIRECTORY="${DESTINATION}/.local/state/install-ia-skills"
STATE_PATH="${STATE_DIRECTORY}/manifest"

checkdependencies
trap cleanup EXIT
loadstate

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
prunediscontinuedentries
writestate

if [[ "${UNMANAGED_SKIPPED_COUNT}" -gt 0 ]]; then
    printf 'Notice: %d existing skill item(s) were not added to the control file; use --force to replace and manage them.\n' "${UNMANAGED_SKIPPED_COUNT}"
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf 'Dry run complete: %d change(s), %d managed item(s) would be pruned, %d modified skill(s) would be preserved and disowned, %d existing item(s) skipped.\n' \
        "${INSTALLED_COUNT}" "${PRUNED_COUNT}" "${DISOWNED_COUNT}" "${SKIPPED_COUNT}"
else
    printf 'Installation complete: %d change(s), %d managed item(s) pruned, %d modified skill(s) preserved and disowned, %d existing item(s) skipped.\n' \
        "${INSTALLED_COUNT}" "${PRUNED_COUNT}" "${DISOWNED_COUNT}" "${SKIPPED_COUNT}"
fi
