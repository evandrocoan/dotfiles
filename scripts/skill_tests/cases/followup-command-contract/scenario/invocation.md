# Prescribed disposable test invocation

The repository test contract is `scenario/ci.json`. Resolve its relative paths from the workspace
root. Its required working directory is `scenario/target`; schema environment values are relative
to that directory. Python is already installed; no dependency installation or container is needed.

The suite has a controlled twelve-second startup to exercise execution ownership and waiting.
Use the exact declared command and both environment variables. The suite owns
`scenario/target/run-events.jsonl`; do not change that receipt or any source file.
