# Bash Script Conventions

## Shebang e modo estrito

```bash
#!/usr/bin/env bash
set -euo pipefail
```

## Estrutura obrigatória

Todo script com argumentos deve ter:

1. `printhelp()` — exibida em `--help` e em qualquer erro de argumento
2. `invalidargument()` — mensagem específica antes do help
3. `checkargsvalid()` — valida que o valor de uma opção não começa com `-`

```bash
function printhelp() {
cat >&1 <<EOF

    Usage: bash ${0} [arguments]

    <descrição do script>

    bash ${0} -h | --help      (show this help)
    bash ${0} -x | --option    (descrição)

EOF
    exit 1
}

function invalidargument() {
    printf 'Error: Invalid argument "%s" for option "%s".\n' "${2}" "${1}"
    printhelp
}

function checkargsvalid() {
    if [[ "${2}" == '-'* ]]; then
        invalidargument "${1}" "${2}"
    fi
}
```

## Loop de argumentos

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
        shift
        ;;
    *)
        printf 'Error: Unknown parameter "%s".\n' "$1" >&2
        printhelp
        ;;
  esac
done
```

## Regras gerais

- Sempre oferecer opção curta (`-x`) e longa (`--option`) para cada argumento
- Usar `function nome()` para declarar funções
- Variáveis globais em `UPPER_CASE`, locais em `lower_case`
- Usar `local` para todas as variáveis dentro de funções
- Erros vão para stderr (`>&2`); help e output normal para stdout
- `printhelp` sempre termina com `exit 1`
- Validar valores de enum explicitamente com `invalidargument` após o loop
