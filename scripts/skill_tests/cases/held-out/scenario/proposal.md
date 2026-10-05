# Proposed transport cutover

Replace the only active transport adapter in an atomic deployment. The new adapter's happy-path
test passes. Existing guarantees include distinct timeout classification and resource cleanup
when a request is cancelled. The proposal defers those tests until after disabling the old adapter
because an atomic switch is said to eliminate every transition risk.
