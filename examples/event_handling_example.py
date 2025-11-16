"""
Example: Using Event Handling in Radish

This example demonstrates how to use the event handling system to monitor
and react to cache operations in real-time.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.expiring_store import ExpiringStore
from src.event_handler import EventHandler, CacheEvent, CacheEventContext

# Initialize event handler and store
event_handler = EventHandler()
store = ExpiringStore(event_handler=event_handler)

# Define a simple event logger
def log_all_events(ctx: CacheEventContext):
    """Log all cache events with timestamp."""
    import datetime
    timestamp = datetime.datetime.fromtimestamp(ctx.timestamp).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {ctx.event_type.value.upper()}: [{ctx.cache_name}] {ctx.key}")

# Define a cache audit logger
def audit_sensitive_cache(ctx: CacheEventContext):
    """Audit operations on sensitive data."""
    if ctx.event_type == CacheEvent.SET:
        print(f"AUDIT: Value updated in sensitive cache: {ctx.key}")
    elif ctx.event_type == CacheEvent.DELETE:
        print(f"AUDIT: Value deleted from sensitive cache: {ctx.key}")
    elif ctx.event_type == CacheEvent.DELETE_CACHE:
        print(f"AUDIT: CRITICAL - Sensitive cache deleted!")

# Define a cache statistics tracker
cache_stats = {"sets": 0, "deletes": 0, "creates": 0}

def track_statistics(ctx: CacheEventContext):
    """Track basic statistics about cache operations."""
    if ctx.event_type == CacheEvent.SET:
        cache_stats["sets"] += 1
    elif ctx.event_type == CacheEvent.DELETE:
        cache_stats["deletes"] += 1
    elif ctx.event_type == CacheEvent.CREATE_CACHE:
        cache_stats["creates"] += 1

# Register global event handlers
event_handler.on(CacheEvent.SET, log_all_events)
event_handler.on(CacheEvent.DELETE, log_all_events)
event_handler.on(CacheEvent.CREATE_CACHE, log_all_events)
event_handler.on(CacheEvent.DELETE_CACHE, log_all_events)

# Track statistics globally
event_handler.on(CacheEvent.SET, track_statistics)
event_handler.on(CacheEvent.DELETE, track_statistics)
event_handler.on(CacheEvent.CREATE_CACHE, track_statistics)

# Create a sensitive cache and add audit logging for it
store.create_cache("sensitive_data")
event_handler.on(CacheEvent.SET, audit_sensitive_cache, cache_name="sensitive_data")
event_handler.on(CacheEvent.DELETE, audit_sensitive_cache, cache_name="sensitive_data")
event_handler.on(CacheEvent.DELETE_CACHE, audit_sensitive_cache, cache_name="sensitive_data")

# Perform some operations
print("=" * 70)
print("Performing cache operations...")
print("=" * 70)

# Default store operations
store.set("user:1", "Alice")
store.set("user:2", "Bob")
del store["user:1"]

# Named cache operations
store.create_cache("users")
store.cache_set("users", "id:1", {"name": "Alice", "age": 30})
store.cache_set("users", "id:2", {"name": "Bob", "age": 25})

# Sensitive cache operations (should trigger audit logs)
store.cache_set("sensitive_data", "ssn:123", "123-45-6789")
store.cache_set("sensitive_data", "ssn:456", "987-65-4321")
store.cache_delete("sensitive_data", "ssn:123")

print("\n" + "=" * 70)
print("Statistics Summary:")
print("=" * 70)
print(f"Total SETs: {cache_stats['sets']}")
print(f"Total DELETEs: {cache_stats['deletes']}")
print(f"Total CACHEs CREATED: {cache_stats['creates']}")
print("=" * 70)

# Cleanup
store.delete_cache("users")
store.delete_cache("sensitive_data")
store.stop()
