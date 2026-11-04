"""Run explicitly with scripts/.venv/bin/python -m unittest discover
-s scripts/tests -p mattermost_http_check.py -v (requires existing FastAPI/Uvicorn).
Exercises a disposable real HTTP server; does not contact Mattermost.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import mattermost_tray


class MattermostHTTPCheck(unittest.TestCase):
    def test_real_http_reports_validation_and_existing_screen_endpoint(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryFile() as log:
            command = Path(directory) / "xscreensaver-command"
            command.write_text("#!/usr/bin/python3\nprint('screen locked since fixture')\n")
            command.chmod(0o700)
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                listener.listen()
                base = f"http://127.0.0.1:{listener.getsockname()[1]}"
                environment = dict(os.environ, PATH=directory + os.pathsep + os.environ["PATH"],
                                   PYTHONDONTWRITEBYTECODE="1")
                process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "monitor_screen_lock:app",
                     "--fd", str(listener.fileno()), "--log-level", "warning", "--ws", "none"],
                    cwd=SCRIPTS, env=environment, pass_fds=(listener.fileno(),),
                    stdout=log, stderr=subprocess.STDOUT,
                )
                try:
                    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

                    def request(path, body=None, headers=None, method=None):
                        request_headers = {"Content-Type": "application/json", "X-Mattermost-Tray": "1"}
                        if headers is not None:
                            request_headers = headers
                        req = urllib.request.Request(base + path,
                            data=json.dumps(body).encode() if body is not None else None,
                            headers=request_headers, method=method)
                        try:
                            with opener.open(req, timeout=2) as response:
                                return response.status, json.load(response)
                        except urllib.error.HTTPError as error:
                            return error.code, error.read().decode()

                    deadline = time.monotonic() + 15
                    while True:
                        try:
                            initial = request("/mattermost/notifications")
                            break
                        except (OSError, TimeoutError):
                            if process.poll() is not None or time.monotonic() >= deadline:
                                log.seek(0)
                                self.fail("Server startup failed: " + log.read().decode())
                            time.sleep(0.05)
                    self.assertEqual(initial, (200, {"state": "unknown", "sources": 0}))
                    path = "/mattermost/notifications"
                    for sequence, state in enumerate(("idle", "unread", "mention", "idle"), 1):
                        payload = {"source": "http-test", "sequence": sequence, "state": state}
                        self.assertEqual(request(path, payload),
                                         (200, {"accepted": True, "state": state, "sources": 1}))
                        original_url = mattermost_tray.API_URL
                        try:
                            mattermost_tray.API_URL = base + path
                            self.assertEqual(mattermost_tray.read_state(), state)
                        finally:
                            mattermost_tray.API_URL = original_url
                    self.assertEqual(request(path, {"source": "http-test", "sequence": 2, "state": "mention"}),
                                     (200, {"accepted": False, "state": "idle", "sources": 1}))
                    for invalid in (
                        {"source": "http-test", "sequence": 5, "state": "red"},
                        {"source": "http-test", "sequence": True, "state": "mention"},
                        {"source": "http-test", "sequence": -1, "state": "mention"},
                        {"source": "http-test", "sequence": 5, "state": "mention", "message": "private"},
                        {"source": "../bad", "sequence": 5, "state": "mention"},
                    ):
                        self.assertEqual(request(path, invalid)[0], 422)
                    valid = {"source": "http-test", "sequence": 5, "state": "mention"}
                    self.assertEqual(request(path, valid, {"Content-Type": "application/json"})[0], 422)
                    self.assertEqual(request(path, valid, {"Content-Type": "text/plain", "X-Mattermost-Tray": "1"})[0], 422)
                    self.assertEqual(request(path, valid, {"Host": "external.example", "Content-Type": "application/json", "X-Mattermost-Tray": "1"})[0], 400)
                    self.assertEqual(request(path, headers={"Origin": "https://external.example", "Access-Control-Request-Method": "POST"}, method="OPTIONS")[0], 405)
                    self.assertEqual(request(path), (200, {"state": "idle", "sources": 1}))
                    self.assertEqual(request("/screen-status"),
                                     (200, {"status": "locked", "raw_output": "screen locked since fixture"}))
                    command.write_text("#!/usr/bin/python3\nimport sys\nsys.exit(1)\n")
                    self.assertEqual(request("/screen-status")[0], 500)
                    self.assertEqual(request(path), (200, {"state": "idle", "sources": 1}))
                finally:
                    process.terminate()
                    process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
