#!/usr/bin/python3
"""Restart TeamViewer when its selected graphical session becomes stale."""

from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


DEFAULT_LOG_PATH = Path("/var/log/teamviewer15/TeamViewer15_Logfile.log")
NO_ACTIVE_SESSION = "4294967295"
ACTIVE_SESSION_PATTERN = re.compile(
    r"MultiUserSessionDesignator: New active session: (?P<session_id>\d+)"
)
REMOVED_SESSION_PATTERN = re.compile(
    r"SysSessionInfoManager::SessionRemoved: removing session .*?"
    r"\[SysSession (?P<session_id>\d+)\b"
)
ATTACH_FAILURE_PATTERN = re.compile(
    r"ProcessControlBase\[\d+\]: start in session (?P<session_id>\d+) "
    r"failed .*Unable to get session"
)
LOGGER = logging.getLogger("teamviewer-session-watchdog")


@dataclass(frozen=True)
class DetectionEvent:
    """A log transition that requires TeamViewer recovery."""

    kind: str
    session_id: str


class TeamViewerSessionDetector:
    """Track TeamViewer's selected session and detect stale state."""

    def __init__(self) -> None:
        self._active_session_id: str | None = None

    def process_line(self, line: str) -> DetectionEvent | None:
        active_match = ACTIVE_SESSION_PATTERN.search(line)
        if active_match:
            session_id = active_match.group("session_id")
            self._active_session_id = (
                None if session_id == NO_ACTIVE_SESSION else session_id
            )
            return None

        removed_match = REMOVED_SESSION_PATTERN.search(line)
        if removed_match:
            session_id = removed_match.group("session_id")
            if session_id == self._active_session_id:
                self._active_session_id = None
                return DetectionEvent(
                    kind="active-session-removed", session_id=session_id
                )
            return None

        attach_failure_match = ATTACH_FAILURE_PATTERN.search(line)
        if attach_failure_match:
            return DetectionEvent(
                kind="desktop-attach-failed",
                session_id=attach_failure_match.group("session_id"),
            )

        return None


class LogFollower:
    """Read complete appended lines and reopen a rotated or truncated log."""

    def __init__(self, path: Path, *, start_at_end: bool) -> None:
        self._path = path
        self._stream: TextIO | None = None
        self._identity: tuple[int, int] | None = None
        self._initial_open = True
        self._start_at_end = start_at_end
        self._open_if_available()

    def _open_if_available(self) -> None:
        try:
            stream = self._path.open("r", encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return

        file_stat = os.fstat(stream.fileno())
        self._stream = stream
        self._identity = (file_stat.st_dev, file_stat.st_ino)
        if self._initial_open and self._start_at_end:
            stream.seek(0, os.SEEK_END)
        self._initial_open = False

    def _close_stream(self) -> None:
        if self._stream is not None:
            self._stream.close()
        self._stream = None
        self._identity = None

    def close(self) -> None:
        self._close_stream()

    def _reopen_if_replaced_or_truncated(self) -> None:
        if self._stream is None:
            self._open_if_available()
            return

        try:
            path_stat = self._path.stat()
        except FileNotFoundError:
            return

        current_identity = (path_stat.st_dev, path_stat.st_ino)
        if current_identity != self._identity or path_stat.st_size < self._stream.tell():
            self._close_stream()
            self._open_if_available()

    def _read_complete_lines(self) -> list[str]:
        if self._stream is None:
            return []

        lines: list[str] = []
        while True:
            position = self._stream.tell()
            line = self._stream.readline()
            if not line:
                break
            if not line.endswith("\n"):
                self._stream.seek(position)
                break
            lines.append(line)
        return lines

    def read_available(self) -> list[str]:
        if self._stream is None:
            self._open_if_available()

        lines = self._read_complete_lines()
        self._reopen_if_replaced_or_truncated()
        lines.extend(self._read_complete_lines())
        return lines


class RestartLimiter:
    """Invoke a restart callback no more than once per cooldown window."""

    def __init__(
        self,
        *,
        restart: Callable[[], None],
        cooldown_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._restart = restart
        self._cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._last_attempt_at: float | None = None

    def handle(self, event: DetectionEvent) -> bool:
        del event
        now = self._clock()
        if (
            self._last_attempt_at is not None
            and now - self._last_attempt_at < self._cooldown_seconds
        ):
            return False

        self._last_attempt_at = now
        self._restart()
        return True


def restart_teamviewer() -> None:
    subprocess.run(
        ["/usr/bin/systemctl", "restart", "teamviewerd.service"],
        check=True,
        timeout=30,
    )


def detect_events(lines: Iterable[str]) -> list[DetectionEvent]:
    detector = TeamViewerSessionDetector()
    events = []
    for line in lines:
        event = detector.process_line(line)
        if event is not None:
            events.append(event)
    return events


def replay_log(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as log_file:
        events = detect_events(log_file)

    for event in events:
        print(f"detected {event.kind} session={event.session_id}")
    print(f"detections={len(events)}")
    return 0


def watch_log(path: Path, *, cooldown_seconds: float, poll_interval: float) -> int:
    detector = TeamViewerSessionDetector()
    follower = LogFollower(path, start_at_end=True)
    limiter = RestartLimiter(
        restart=restart_teamviewer,
        cooldown_seconds=cooldown_seconds,
    )
    LOGGER.info("watching %s", path)

    try:
        while True:
            lines = follower.read_available()
            for line in lines:
                event = detector.process_line(line)
                if event is None:
                    continue

                LOGGER.warning(
                    "detected %s for session %s", event.kind, event.session_id
                )
                try:
                    restarted = limiter.handle(event)
                except (subprocess.SubprocessError, OSError) as error:
                    LOGGER.error("failed to restart teamviewerd.service: %s", error)
                    continue

                if restarted:
                    LOGGER.warning("restarted teamviewerd.service")
                else:
                    LOGGER.info("restart suppressed by cooldown")

            if not lines:
                time.sleep(poll_interval)
    except KeyboardInterrupt:
        LOGGER.info("stopped")
        return 0
    finally:
        follower.close()


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Watch TeamViewer's daemon log and restart it when its selected "
            "graphical session becomes stale."
        )
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help=f"daemon log to follow (default: {DEFAULT_LOG_PATH})",
    )
    parser.add_argument(
        "--cooldown-seconds",
        type=positive_float,
        default=60.0,
        help="minimum interval between restart attempts (default: 60)",
    )
    parser.add_argument(
        "--poll-interval",
        type=positive_float,
        default=0.5,
        help="seconds to wait when no complete log line is available (default: 0.5)",
    )
    parser.add_argument(
        "--replay",
        action="store_true",
        help="scan the complete log, report detections, and do not restart TeamViewer",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if args.replay:
        return replay_log(args.log_file)
    return watch_log(
        args.log_file,
        cooldown_seconds=args.cooldown_seconds,
        poll_interval=args.poll_interval,
    )


if __name__ == "__main__":
    raise SystemExit(main())
