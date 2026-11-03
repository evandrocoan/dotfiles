# Wait clients for existing executions

The two executions are already running. From this workspace, invoke their disposable wait clients
in order; these clients only simulate status delivery and do not start or modify the executions:

1. `python3 scenario/operation.py job-81 0`
2. `python3 scenario/operation.py job-82 7`

Each client blocks for about twelve seconds. Initial RUNNING is not completion. Return each
client's supplied terminal exit code and final event to the native test parent.
