import tempfile
import unittest
from pathlib import Path

from teamviewer_session_watchdog import (
    DetectionEvent,
    LogFollower,
    RestartLimiter,
    TeamViewerSessionDetector,
)


ACTIVE_GREETER = (
    "2026/09/04 14:41:32.353 S   "
    "MultiUserSessionDesignator: New active session: 2806870654\n"
)
ACTIVE_USER = (
    "2026/09/04 14:41:32.354 S   "
    "MultiUserSessionDesignator: New active session: 1591159457\n"
)
NO_ACTIVE_SESSION = (
    "2026/09/04 14:41:32.349 S   "
    "MultiUserSessionDesignator: New active session: 4294967295\n"
)
REMOVE_GREETER = (
    "2026/09/04 14:41:32.396 S   "
    "SysSessionInfoManager::SessionRemoved: removing session XSession: 1 "
    "[SysSession 2806870654 [type=X user=lightdm]]\n"
)
ATTACH_FAILURE = (
    "2026/09/04 17:37:04.748 S!! ProcessControlBase[4]: start in session 2806870654 "
    "failed with errorcode generic:125, Unable to get session, Errorcode=11\n"
)


class TeamViewerSessionDetectorTests(unittest.TestCase):
    def test_detects_selected_session_being_removed(self):
        detector = TeamViewerSessionDetector()

        detector.process_line(ACTIVE_USER)
        detector.process_line(NO_ACTIVE_SESSION)
        self.assertIsNone(detector.process_line(ACTIVE_GREETER))
        event = detector.process_line(REMOVE_GREETER)

        self.assertEqual(
            event,
            DetectionEvent(kind="active-session-removed", session_id="2806870654"),
        )

    def test_ignores_removed_session_after_another_session_became_active(self):
        detector = TeamViewerSessionDetector()

        detector.process_line(ACTIVE_GREETER)
        detector.process_line(ACTIVE_USER)

        self.assertIsNone(detector.process_line(REMOVE_GREETER))

    def test_no_active_session_marker_clears_selected_session(self):
        detector = TeamViewerSessionDetector()

        detector.process_line(ACTIVE_GREETER)
        detector.process_line(NO_ACTIVE_SESSION)

        self.assertIsNone(detector.process_line(REMOVE_GREETER))

    def test_detects_desktop_attach_failure_as_fallback(self):
        detector = TeamViewerSessionDetector()

        self.assertEqual(
            detector.process_line(ATTACH_FAILURE),
            DetectionEvent(kind="desktop-attach-failed", session_id="2806870654"),
        )

    def test_ignores_unrelated_errors(self):
        detector = TeamViewerSessionDetector()

        self.assertIsNone(
            detector.process_line(
                "2026/09/04 17:00:00.000 S!! unrelated component failed, Errorcode=11\n"
            )
        )


class RestartLimiterTests(unittest.TestCase):
    def test_suppresses_restarts_inside_cooldown(self):
        now = [100.0]
        restarts = []
        limiter = RestartLimiter(
            restart=lambda: restarts.append(now[0]),
            cooldown_seconds=60.0,
            clock=lambda: now[0],
        )
        event = DetectionEvent(kind="desktop-attach-failed", session_id="123")

        self.assertTrue(limiter.handle(event))
        now[0] = 130.0
        self.assertFalse(limiter.handle(event))
        now[0] = 160.0
        self.assertTrue(limiter.handle(event))
        self.assertEqual(restarts, [100.0, 160.0])

    def test_failed_restart_is_also_rate_limited(self):
        now = [100.0]
        attempts = []

        def restart():
            attempts.append("restart")
            if len(attempts) == 1:
                raise RuntimeError("restart failed")

        limiter = RestartLimiter(
            restart=restart,
            cooldown_seconds=60.0,
            clock=lambda: now[0],
        )
        event = DetectionEvent(kind="active-session-removed", session_id="123")

        with self.assertRaisesRegex(RuntimeError, "restart failed"):
            limiter.handle(event)

        self.assertFalse(limiter.handle(event))
        now[0] = 160.0
        self.assertTrue(limiter.handle(event))
        self.assertEqual(attempts, ["restart", "restart"])


class LogFollowerTests(unittest.TestCase):
    def test_starts_at_end_and_only_returns_appended_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teamviewer.log"
            path.write_text(ATTACH_FAILURE, encoding="utf-8")
            follower = LogFollower(path, start_at_end=True)
            self.addCleanup(follower.close)

            self.assertEqual(follower.read_available(), [])
            with path.open("a", encoding="utf-8") as log_file:
                log_file.write(ACTIVE_USER)

            self.assertEqual(follower.read_available(), [ACTIVE_USER])

    def test_reopens_rotated_log_from_beginning(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teamviewer.log"
            rotated_path = Path(directory) / "teamviewer.log.old"
            path.write_text("old history\n", encoding="utf-8")
            follower = LogFollower(path, start_at_end=True)
            self.addCleanup(follower.close)

            path.rename(rotated_path)
            path.write_text(ACTIVE_USER, encoding="utf-8")

            self.assertEqual(follower.read_available(), [ACTIVE_USER])

    def test_drains_rotated_log_before_reading_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teamviewer.log"
            rotated_path = Path(directory) / "teamviewer.log.old"
            path.write_text("old history\n", encoding="utf-8")
            follower = LogFollower(path, start_at_end=True)
            self.addCleanup(follower.close)

            with path.open("a", encoding="utf-8") as log_file:
                log_file.write(ACTIVE_GREETER)
            path.rename(rotated_path)
            path.write_text(ACTIVE_USER, encoding="utf-8")

            self.assertEqual(
                follower.read_available(),
                [ACTIVE_GREETER, ACTIVE_USER],
            )

    def test_reopens_truncated_log_from_beginning(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teamviewer.log"
            path.write_text(f"{'x' * 1000}\n", encoding="utf-8")
            follower = LogFollower(path, start_at_end=True)
            self.addCleanup(follower.close)

            path.write_text(ACTIVE_USER, encoding="utf-8")

            self.assertEqual(follower.read_available(), [ACTIVE_USER])

    def test_waits_for_complete_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teamviewer.log"
            path.write_text("", encoding="utf-8")
            follower = LogFollower(path, start_at_end=True)
            self.addCleanup(follower.close)

            with path.open("a", encoding="utf-8") as log_file:
                log_file.write(ACTIVE_USER.rstrip("\n"))
            self.assertEqual(follower.read_available(), [])

            with path.open("a", encoding="utf-8") as log_file:
                log_file.write("\n")
            self.assertEqual(follower.read_available(), [ACTIVE_USER])


if __name__ == "__main__":
    unittest.main()
