import argparse
from contextlib import redirect_stdout
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import teamviewer_session_watchdog as watchdog

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


class OrchestrationTests(unittest.TestCase):
    def test_detect_events_preserves_order_and_exact_event_identity(self):
        self.assertEqual(
            watchdog.detect_events([ACTIVE_GREETER, REMOVE_GREETER, ATTACH_FAILURE]),
            [
                DetectionEvent(
                    kind="active-session-removed", session_id="2806870654"
                ),
                DetectionEvent(
                    kind="desktop-attach-failed", session_id="2806870654"
                ),
            ],
        )

    def test_replay_reports_detections_without_restarting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teamviewer.log"
            path.write_text(ACTIVE_GREETER + REMOVE_GREETER, encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output), patch.object(
                watchdog, "restart_teamviewer"
            ) as restart:
                result = watchdog.replay_log(path)

        self.assertEqual(result, 0)
        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "detected active-session-removed session=2806870654",
                "detections=1",
            ],
        )
        restart.assert_not_called()

    def test_watch_routes_a_detected_event_through_limiter_and_closes_follower(self):
        follower = Mock()
        follower.read_available.side_effect = [
            [ACTIVE_GREETER],
            [REMOVE_GREETER],
            KeyboardInterrupt(),
        ]
        limiter = Mock()
        limiter.handle.return_value = True

        with patch.object(watchdog, "LogFollower", return_value=follower), patch.object(
            watchdog, "RestartLimiter", return_value=limiter
        ) as limiter_class:
            result = watchdog.watch_log(
                Path("fixture.log"), cooldown_seconds=30, poll_interval=0.25
            )

        self.assertEqual(result, 0)
        limiter_class.assert_called_once_with(
            restart=watchdog.restart_teamviewer, cooldown_seconds=30
        )
        limiter.handle.assert_called_once_with(
            DetectionEvent(kind="active-session-removed", session_id="2806870654")
        )
        follower.close.assert_called_once_with()

    def test_positive_float_and_argument_parser_reject_nonpositive_values(self):
        self.assertEqual(watchdog.positive_float("0.25"), 0.25)
        for value in ("0", "-1"):
            with self.subTest(value=value), self.assertRaisesRegex(
                argparse.ArgumentTypeError, "must be greater than zero"
            ):
                watchdog.positive_float(value)

    def test_main_dispatches_replay_and_watch_modes_with_exact_arguments(self):
        path = Path("fixture.log")
        with patch.object(watchdog, "replay_log", return_value=7) as replay:
            self.assertEqual(
                watchdog.main(["--replay", "--log-file", str(path)]), 7
            )
        replay.assert_called_once_with(path)

        with patch.object(watchdog, "watch_log", return_value=8) as watch:
            self.assertEqual(
                watchdog.main(
                    [
                        "--log-file",
                        str(path),
                        "--cooldown-seconds",
                        "45",
                        "--poll-interval",
                        "0.75",
                    ]
                ),
                8,
            )
        watch.assert_called_once_with(
            path, cooldown_seconds=45.0, poll_interval=0.75
        )


if __name__ == "__main__":
    unittest.main()
