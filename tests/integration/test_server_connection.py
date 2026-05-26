#!/usr/bin/env python3
"""Integration tests for basic server connectivity."""

import socket
import unittest


def _send_command(command: str, host: str = 'localhost', port: int = 6379) -> str:
    """Send a raw command to the server and return the response."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    sock.connect((host, port))
    try:
        sock.sendall(command.encode('utf-8'))
        return sock.recv(1024).decode('utf-8')
    finally:
        sock.close()


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


@unittest.skipUnless(_server_available(), 'Radish server not running on localhost:6379')
class TestServerConnection(unittest.TestCase):
    """Tests that require a live Radish server."""

    def test_ping(self):
        """Server responds to PING with PONG."""
        response = _send_command('PING\n')
        self.assertIn('PONG', response)


if __name__ == '__main__':
    unittest.main()
