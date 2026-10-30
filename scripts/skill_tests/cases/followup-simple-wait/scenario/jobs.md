# Disposable operations

Run these independent local fixture operations from this workspace, in order:

1. `python3 scenario/operation.py job-81 0`
2. `python3 scenario/operation.py job-82 7`

Each runs for about twelve seconds. The initial RUNNING event is only startup output. Return
each operation's actual exit code and final event to the native test parent when it finishes.
