---
name: bash-scripts
description: Create, edit, review, or debug Bash scripts and shell snippets that must follow the user's conventions for strict mode, argument parsing, help output, variable scope, and error reporting. Use whenever working with .sh files, Bash executables, or Bash code blocks.
---

# Bash scripts

## Use strict mode

Start every script with:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

## Structure argument handling

Every script that accepts arguments must define:

1. `printhelp()` — print help and exit with the supplied status: `0` for an
   explicit help request and nonzero for an argument error.
2. `invalidargument()` — handle an option that receives an invalid value.
3. `checkargsvalid()` — reject a missing value or one starting with `-` for an
   option that requires a value.
4. `checkexpectedargs()` — reject a bare value after a flag that takes no
   arguments.

Use this structure:

```bash
function printhelp() {
    local exit_status="${1}"

cat >&1 <<EOF

    Usage: bash ${0} [arguments]

    <script description>

    bash ${0} -h | --help      (show this help)
    bash ${0} -x | --option    (description)

EOF
    exit "${exit_status}"
}

# ${1} - Option (for example, --load-config)
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
```

Parse arguments with this pattern:

```bash
while [[ $# -gt 0 ]]; do
    case "${1}" in
        -h|--help)
            checkexpectedargs "${1}" "${2--}"
            printhelp 0
            ;;
        -x|--option)
            checkargsvalid "${1}" "${2-}"
            OPTION_VALUE="${2}"
            shift 2
            ;;
        -f|--flag)
            checkexpectedargs "${1}" "${2--}"
            FLAG=1
            shift
            ;;
        *)
            printf 'Error: Unknown parameter "%s".\n' "${1}" >&2
            printhelp 1
            ;;
    esac
done
```

## Follow general conventions

- Provide both short and long forms for every option.
- Declare functions with `function name()`.
- Use uppercase names for global variables and lowercase names for local
  variables.
- Declare every function variable with `local`.
- Send errors to stderr with `>&2`; send help and normal output to stdout.
- End `printhelp()` with the supplied exit status. Use `0` only for explicitly
  requested help and a nonzero status for invalid usage.
- Validate enum values explicitly with `invalidargument()` after parsing.
