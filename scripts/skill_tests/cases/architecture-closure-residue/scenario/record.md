# Review queue

**Status:** Implemented

## Decision

The consumer owns admission and ordered reviewer execution.

## Publication

**Publication amendment:** Reviewers publish directly through the ordinary gateway. This amendment
replaces consumer-owned public delivery. Historical uncertain receipts remain read-back-only;
they cannot authorize resending a publication.

## Workspace

**Workspace execution amendment:** Freeze the ordered workspace roots once per round and reuse
them for each reviewer and recovery. Publication has the limits in the amendment above.

## Scratch ownership

The consumer allocates each review's temporary directory and removes only its registered original
directory after execution has stopped. Uncertain execution preserves the directory for a later
check; cleanup failure does not fail or repeat the review.

## Archive ownership

The consumer retains settled receipts in its local ledger.

**Approved amendment, in implementation:** Move settled receipts to a remote archive only after
verifying their durable remote identity. The local-ledger rule above stays in force until this
amendment is implemented.

## Compatibility rationale

Historical receipts contain an `amendment` field naming the publication change. Its exact name is
needed to decode old receipts, whose delivery may still be uncertain. Retain the historical
decoder and read-back-only recovery even though new reviews publish directly.
