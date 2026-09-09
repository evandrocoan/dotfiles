#!/usr/bin/env python3
"""Live regression checks for the local netatop-bpf daemon (run with sudo).

Use only loopback sockets and this process's counters. Failed receives and MSG_PEEK
must not change transferred-byte totals; successful TCP and UDP traffic must count.
"""

import os
import socket
import struct
import unittest


RECORD = struct.Struct("=i4xQ16s8Q")
PAYLOAD = b"netatop-check" * 256


class NetworkAccountingTest(unittest.TestCase):
    def setUp(self):
        self.collector = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(self.collector.close)
        self.collector.settimeout(5)
        self.collector.connect("/run/netatop-bpf-socket")
        self.counters()  # Complete the attach handshake before generating traffic.

    def counters(self):
        self.collector.sendall(bytes(RECORD.size))
        own = (0,) * 8
        while True:
            record = bytearray()
            while len(record) < RECORD.size:
                chunk = self.collector.recv(RECORD.size - len(record))
                if not chunk:
                    self.fail("Collector closed the connection before the terminator")
                record.extend(chunk)
            pid, _, _, *values = RECORD.unpack(record)
            if pid == 0:
                return own
            if pid == os.getpid():
                own = tuple(values)

    def check_transfer(self, sender, receiver, send_index, receive_index):
        before = self.counters()
        receiver.setblocking(False)
        for _ in range(3):
            with self.assertRaises(BlockingIOError):
                receiver.recv(128)
        receiver.settimeout(5)
        sender.sendall(PAYLOAD)
        for _ in range(3):
            self.assertEqual(receiver.recv(128, socket.MSG_PEEK), PAYLOAD[:128])
        received = bytearray()
        while len(received) < len(PAYLOAD):
            chunk = receiver.recv(len(PAYLOAD) - len(received))
            self.assertTrue(chunk, "Connection ended before the payload arrived")
            received.extend(chunk)
        self.assertEqual(received, PAYLOAD)
        after = self.counters()
        # Kernel counters are unsigned and may wrap in the defective implementation.
        mask = (1 << 64) - 1
        self.assertEqual((after[send_index] - before[send_index]) & mask, len(PAYLOAD))
        self.assertEqual((after[receive_index] - before[receive_index]) & mask, len(PAYLOAD))

    def test_udp_bytes_exclude_failed_and_peek_receives(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as endpoint:
            endpoint.bind(("127.0.0.1", 0))
            endpoint.connect(endpoint.getsockname())
            self.check_transfer(endpoint, endpoint, 5, 7)

    def test_tcp_bytes_exclude_failed_and_peek_receives(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            with socket.create_connection(listener.getsockname(), timeout=5) as sender:
                receiver, _ = listener.accept()
                with receiver:
                    self.check_transfer(sender, receiver, 1, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
