# Bash Script Conventions

## Shebang and strict mode

```bash
#!/usr/bin/env bash
set -euo pipefail
```

## Required structure

Every script that accepts arguments must have:

1. `printhelp()` — printed on `--help` and on any argument error
2. `invalidargument()` — called when an option receives an invalid value
3. `checkargsvalid()` — for options that **take a value**: validates the value does
   not start with `-` (which would mean the user forgot to supply it)
4. `checkexpectedargs()` — for **flags** (no value): validates that the next token
   starts with `-`, i.e. the flag was not accidentally followed by a bare value

```bash
function printhelp() {
cat >&1 <<EOF

    Usage: bash ${0} [arguments]

    <script description>

    bash ${0} -h | --help      (show this help)
    bash ${0} -x | --option    (description)

EOF
    exit 1
}

# ${1} - Option (eg: --load-config)
# ${2} - Invalid argument (eg: -k)
function invalidargument() {
    printf 'Error: Invalid argument "%s" for option "%s".\n' "${2}" "${1}"
    printhelp
    exit 1
}

function checkargsvalid() {
    argumentvalue="$2"
    if [[ "$argumentvalue" == '-'* ]]; then
        invalidargument "${1}" "${2}"
    fi
}

function checkexpectedargs() {
    argumentvalue="$2"
    if [[ "$argumentvalue" != '-'* ]]; then
        printf 'Error: The command "%s" does not expect any arguments, but got "%s".\n' "${1}" "${argumentvalue}"
        printhelp
    fi
}
```

## Argument loop

```bash
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
        printhelp
        ;;
    -x|--option)
        checkargsvalid "$1" "${2-}"
        VARIABLE="$2"
        shift 2
        ;;
    --flag)
        FLAG=1
        checkexpectedargs "$1" "${2--}"
        shift
        ;;
    *)
        printf 'Error: Unknown parameter "%s".\n' "$1" >&2
        printhelp
        ;;
  esac
done
```

## General rules

- Always provide both short (`-x`) and long (`--option`) forms for each argument
- Declare functions with `function name()`
- Global variables in `UPPER_CASE`, local variables in `lower_case`
- Use `local` for all variables inside functions
- Errors go to stderr (`>&2`); help and normal output go to stdout
- `printhelp` always ends with `exit 1`
- Validate enum values explicitly with `invalidargument` after the loop
