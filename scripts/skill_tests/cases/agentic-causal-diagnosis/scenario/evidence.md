# Incident observations

The deployed revision is r7. Its research tool can open only URLs returned by its search tool.
The search returned a release index; it omitted the version-specific contract page.
Opening that contract's direct URL was denied. The model received the index and the denial, not
the contract. A later analyst could open arbitrary approved public URLs and obtained the contract.

These are the complete structured candidate collections at the two relevant boundaries:

```json
{"event": 41, "candidates": [{"id": "c1"}, {"id": "c2"}]}
{"event": 48, "candidates": [{"id": "c1", "aliases": ["c3"]}, {"id": "c2"}]}
```

The summary log says "candidate alias c3 preserved". A diagnosis attributes the failure to a weak
model and says deduplication admitted a third candidate. It proposes a stronger model and a global
veto whenever an alias is present.

Revision r8 permits the direct URL through the existing authenticated fetch boundary. Its first
fresh run returns clean. That run's event log shows research was never requested. No run has yet
exercised the repaired URL path. The engineer marks both the diagnosis and repair validated.
