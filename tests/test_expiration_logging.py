#!/usr/bin/env python3
"""
Test script to demonstrate cache expiration logging.
This script connects to the Radish server, sets keys with short TTL,
and waits for them to expire to generate expiration log entries.
"""

import socket
import time

def send_command(sock, command):
    """Send a command and receive response."""
    sock.sendall(f"{command}\n".encode())
    time.sleep(0.1)
    try:
        response = sock.recv(4096).decode()
        return response
    except:
        return None

def main():
    print("=" * 60)
    print("Testing Cache Expiration Logging")
    print("=" * 60)
    
    # Connect to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.connect(('localhost', 6379))
        print("Connected to Radish server\n")
        
        # Set some keys with short TTL
        print("Setting keys with 3-second TTL...")
        send_command(sock, "SET key1 'value1'")
        send_command(sock, "EXPIRE key1 3")
        
        send_command(sock, "SET key2 'value2'")
        send_command(sock, "EXPIRE key2 3")
        
        send_command(sock, "SET key3 'value3'")
        send_command(sock, "EXPIRE key3 3")
        
        print("Keys set. Waiting for expiration (4 seconds)...")
        time.sleep(4)
        
        # Try to get the keys (should be expired)
        print("\nAttempting to retrieve expired keys:")
        response1 = send_command(sock, "GET key1")
        print(f"GET key1: {response1.strip() if response1 else 'None'}")
        
        response2 = send_command(sock, "GET key2")
        print(f"GET key2: {response2.strip() if response2 else 'None'}")
        
        response3 = send_command(sock, "GET key3")
        print(f"GET key3: {response3.strip() if response3 else 'None'}")
        
        # Test with named cache
        print("\n" + "-" * 60)
        print("Testing expiration with named cache...")
        send_command(sock, "CREATECACHE testcache")
        send_command(sock, "CACHESET testcache cache_key1 'cache_value1'")
        
        # Note: Named caches don't have per-key TTL in current implementation
        # But we can demonstrate with the main store
        
        send_command(sock, "EXIT")
        
        print("\n" + "=" * 60)
        print("Test completed!")
        print("\nCheck expiration logs:")
        print("  cat ~/.radish/logs/radish_$(date +%Y-%m-%d).log | grep EXPIRATION")
        print("\nCheck server output log:")
        print("  cat ~/.radish/logs/server_$(date +%Y-%m-%d).log")
        print("=" * 60)
        
    except ConnectionRefusedError:
        print("Error: Could not connect to server. Is it running?")
        print("Start the server with: python3 server.py")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
