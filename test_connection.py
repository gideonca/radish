#!/usr/bin/env python3
"""Simple connection test."""

import socket
import sys

def test_connection():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        
        print("Connecting to localhost:6379...")
        sock.connect(('localhost', 6379))
        print("Connected!")
        
        print("Sending PING command...")
        sock.sendall(b'PING\n')
        
        print("Waiting for response...")
        response = sock.recv(1024)
        print(f"Response received: {repr(response)}")
        print(f"Decoded: {response.decode('utf-8')}")
        
        sock.close()
        return True
    except socket.timeout:
        print("ERROR: Connection timeout - no response from server")
        return False
    except ConnectionRefusedError:
        print("ERROR: Connection refused - is the server running?")
        return False
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
