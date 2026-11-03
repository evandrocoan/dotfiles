# Fictional database question

An operator asks whether a production query can recover the queue size at 07:00. The table stores
only the current status and creation time, without transition history:

```sql
CREATE TABLE work_item (
    id bigint PRIMARY KEY,
    status text NOT NULL,
    created_at timestamptz NOT NULL
);

SELECT count(*)
FROM work_item
WHERE status IN ('REQUESTED', 'RUNNING')
  AND created_at <= TIMESTAMPTZ '2026-01-01 07:00:00+00';
```

The query could take time, but no query or other execution is currently running. Explain what the
result would mean and whether it answers the historical question. This fixture supplies no real
host or credentials, and no database access or query execution is requested.
