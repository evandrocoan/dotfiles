"""Notification leases and precedence, without FastAPI or desktop dependencies."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mattermost_notifications import NotificationState


class NotificationStateTest(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.state = NotificationState(clock=lambda: self.now)

    def test_initial_and_expired_reports_are_unknown(self):
        self.assertEqual(self.state.snapshot(), {"state": "unknown", "sources": 0})
        self.state.report("tab-a", 1, "idle")
        self.assertEqual(self.state.snapshot(), {"state": "idle", "sources": 1})
        self.now += 180
        self.assertEqual(self.state.snapshot(), {"state": "unknown", "sources": 0})

    def test_red_precedence_and_clearing_without_sticky_alerts(self):
        self.state.report("tab-a", 1, "unread")
        self.state.report("tab-b", 1, "mention")
        self.assertEqual(self.state.snapshot(), {"state": "mention", "sources": 2})
        self.state.report("tab-b", 2, "idle")
        self.assertEqual(self.state.snapshot(), {"state": "unread", "sources": 2})
        self.state.report("tab-a", 2, "idle")
        self.assertEqual(self.state.snapshot(), {"state": "idle", "sources": 2})

    def test_out_of_order_and_duplicate_reports_do_not_refresh_or_replace(self):
        self.state.report("tab-a", 3, "idle")
        self.now += 179
        self.assertFalse(self.state.report("tab-a", 2, "mention"))
        self.assertFalse(self.state.report("tab-a", 3, "mention"))
        self.assertEqual(self.state.snapshot()["state"], "idle")
        self.now += 1
        self.assertEqual(self.state.snapshot(), {"state": "unknown", "sources": 0})

    def test_heartbeat_refresh_and_reconnect(self):
        self.state.report("tab-a", 1, "unread")
        self.now += 170
        self.assertTrue(self.state.report("tab-a", 2, "unread"))
        self.now += 20
        self.assertEqual(self.state.snapshot()["state"], "unread")
        self.now += 180
        self.assertEqual(self.state.snapshot()["state"], "unknown")
        self.assertTrue(self.state.report("tab-a", 3, "mention"))
        self.assertEqual(self.state.snapshot()["state"], "mention")

    def test_unknown_tab_cannot_confirm_idle_but_alerts_take_precedence(self):
        self.state.report("tab-a", 1, "idle")
        self.state.report("tab-b", 1, "unknown")
        self.assertEqual(self.state.snapshot()["state"], "unknown")
        self.state.report("tab-a", 2, "unread")
        self.assertEqual(self.state.snapshot()["state"], "unread")

    def test_expired_sources_do_not_accumulate(self):
        for i in range(32):
            self.state.report(f"tab-{i}", 1, "idle")
        with self.assertRaisesRegex(ValueError, "Too many"):
            self.state.report("extra", 1, "mention")
        self.assertEqual(self.state.snapshot(), {"state": "idle", "sources": 32})
        self.now += 180
        self.assertTrue(self.state.report("extra", 1, "mention"))
        self.assertEqual(self.state.snapshot(), {"state": "mention", "sources": 1})


if __name__ == "__main__":
    unittest.main()
