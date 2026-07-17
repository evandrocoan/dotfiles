---
applyTo: "**"
---

When browsing the web, if bot verification begins, wait for the user to complete
the verification and then continue the task. Do not try to bypass or automate
bot verifications, as that can lead to errors or account lockouts.

Do not change my code formatting style when fixing it.

When a package or import is missing, do not install it automatically. Ask the
user whether to install the missing package or look for an alternative that is
already available.

Do not create new README.md files with documentation.

Do not create new shell scripts to automate processes.

When asked to write code, only write the code. Do not create any documentation,
readmes, or tests unless explicitly asked to.

When writing markdown, do not use CamelCase for section titles. Use normal
sentence case instead.

When writing markdown tables, always use spaces around the dashes in the
separator row, like | --- | --- | --- | instead of |---|---|---|.

When asked to commit a file that is not being tracked, first check if it is
excluded by .gitignore (run `git check-ignore -v <file>`). If it is, update
.gitignore to allowlist it with `!` rules before staging — parent directories
must also be explicitly allowed. This repository uses an allowlist strategy:
everything is ignored by default (`*`) and files are opted in with `!` rules.

The development machine has an extremely slow mechanical disk. All terminal
commands take much longer than normal. Never cancel a command early — always
wait for it to fully complete before running the next one.

Never call run_in_terminal while another command is still running. The terminal
is a single synchronous shell — calling run_in_terminal again while a command
is running KILLS it. Always wait for the shell prompt to appear before issuing
another command.

If there is no output from a terminal command for a long time, use
get_terminal_output to check status. Do NOT call run_in_terminal again — that
kills the running process.

Never run multiple sleep commands back-to-back without waiting for each one to
finish. Run one command at a time with isBackground: false and wait for
completion.
