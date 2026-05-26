#!/usr/bin/env python3
"""Integration tests for TCP server connectivity and basic command round-trips."""

import socket
import unittest


def _server_available(host: str = 'localhost', port: int = 6379) -> bool:
    """Return True if the Radish server is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect((host, port))
        sock.close()
        return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def _send(command: str, host: str = 'localhost', port: int = 6379) -> str:
    """Open a fresh connection, send one command, return the decoded response."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(3.0)
        sock.connect((host, port))
        sock.sendall(command.encode('utf-8'))
        return sock.recv(1024).decode('utf-8')


@unittest.skipUnless(_server_available(), 'Radish server not running on localhost:6379')
class TestConnection(unittest.TestCase):
    """Basic connectivity and command round-trip tests."""

    def test_connects(self):
        """Server accepts TCP connections."""
        self.assertTrue(_server_available())

    def test_ping_response(self):
        """PING returns a response containing PONG."""
        response = _send('PING\n')
        self.assertIn('PONG', response)


if __name__ == '__main__':
    unittest.main()
