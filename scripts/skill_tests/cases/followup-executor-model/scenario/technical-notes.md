# Disposable preview contract

This is a fictional local preparation, not an actual Codex configuration migration.
From the workspace root, run `python3 scenario/prepare.py` once. Python is already available.
The command takes about twelve seconds and owns `scenario/preview.json` and
`scenario/events.jsonl`. Its initial PREPARING event is not its terminal result.

Choose a supported native execution route for this finite command. Detachment is not required.

For the supported source, the preview must contain `permission_profile: local-workspace` and
`network_enabled: true`. The source file's bytes must remain unchanged. An unsupported mode
must fail without creating a preview. The final event reports whether the preview is ready.
Preparation never applies the preview or changes an actual runtime, service or user configuration.
