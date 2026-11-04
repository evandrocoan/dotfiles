"""Ephemeral browser notification reports; no message content or credentials."""
import time


class NotificationState:
    def __init__(self, clock=time.monotonic, stale_after=180):
        self.clock = clock
        self.stale_after = stale_after
        self.reports = {}

    def _expire(self, now):
        self.reports = {
            source: report for source, report in self.reports.items()
            if now - report[0] < self.stale_after
        }

    def report(self, source, sequence, state):
        now = self.clock()
        self._expire(now)
        previous = self.reports.get(source)
        if previous is not None and sequence <= previous[1]:
            return False
        if previous is None and len(self.reports) >= 32:
            raise ValueError("Too many active browser sources")
        self.reports[source] = (now, sequence, state)
        return True

    def snapshot(self):
        self._expire(self.clock())
        priority = {"idle": 0, "unknown": 1, "unread": 2, "mention": 3}
        states = [report[2] for report in self.reports.values()]
        state = max(states, key=priority.__getitem__) if states else "unknown"
        return {"state": state, "sources": len(states)}
