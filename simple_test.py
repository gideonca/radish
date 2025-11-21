#!/usr/bin/env python3
"""Simple test to check if server is responding at all."""

import socket

def test_ping():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 6379))
    
    # Send PING
    sock.sendall(b'PING\n')
    
    # Try to receive response
    sock.settimeout(2.0)
    try:
        response = sock.recv(1024)
        print(f"Raw response: {response}")
        print(f"Decoded: {response.decode('utf-8')}")
    except socket.timeout:
        print("No response received (timeout)")
    
    sock.close()

if __name__ == '__main__':
    try:
        test_ping()
    except Exception as e:
        print(f"Error: {e}")
