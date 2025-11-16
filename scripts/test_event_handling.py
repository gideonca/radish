#!/usr/bin/env python3
"""
Test script for event handling in Radish.

This script demonstrates how to use the event handling system to track
updates and deletions in caches and stores.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.expiring_store import ExpiringStore
from src.event_handler import EventHandler, CacheEvent, CacheEventContext

def main():
    """Test event handling for store and cache operations."""
    
    print("=" * 60)
    print("Testing Event Handling in Radish")
    print("=" * 60)
    
    # Create event handler
    event_handler = EventHandler()
    
    # Create store with event handler
    store = ExpiringStore(event_handler=event_handler)
    
    # Define event handlers
    def on_set(ctx: CacheEventContext):
        print(f"✓ SET Event: [{ctx.cache_name}] {ctx.key} = {ctx.value}")
        if ctx.old_value is not None:
            print(f"  Previous value: {ctx.old_value}")
    
    def on_delete(ctx: CacheEventContext):
        print(f"✗ DELETE Event: [{ctx.cache_name}] {ctx.key}")
        if ctx.old_value is not None:
            print(f"  Deleted value: {ctx.old_value}")
    
    def on_create_cache(ctx: CacheEventContext):
        print(f"⊕ CREATE_CACHE Event: Cache '{ctx.cache_name}' created")
    
    def on_delete_cache(ctx: CacheEventContext):
        print(f"⊖ DELETE_CACHE Event: Cache '{ctx.cache_name}' deleted")
    
    def on_clear(ctx: CacheEventContext):
        print(f"⊗ CLEAR Event: Cache '{ctx.cache_name}' cleared")
    
    # Register global event handlers
    print("\n1. Registering global event handlers...")
    event_handler.on(CacheEvent.SET, on_set)
    event_handler.on(CacheEvent.DELETE, on_delete)
    event_handler.on(CacheEvent.CREATE_CACHE, on_create_cache)
    event_handler.on(CacheEvent.DELETE_CACHE, on_delete_cache)
    event_handler.on(CacheEvent.CLEAR, on_clear)
    print("   Event handlers registered ✓")
    
    # Test default store operations
    print("\n2. Testing default store operations...")
    print("   Setting keys in default store...")
    store.set("user:1", "Alice")
    store.set("user:2", "Bob")
    store.set("user:3", "Charlie")
    
    print("\n   Updating an existing key...")
    store.set("user:1", "Alice Smith")
    
    print("\n   Deleting a key...")
    del store["user:2"]
    
    print("\n   Clearing the store...")
    store.clear()
    
    # Test named cache operations
    print("\n3. Testing named cache operations...")
    print("   Creating a cache...")
    store.create_cache("users")
    
    print("\n   Setting keys in named cache...")
    store.cache_set("users", "id:1", {"name": "Alice", "age": 30})
    store.cache_set("users", "id:2", {"name": "Bob", "age": 25})
    store.cache_set("users", "id:3", {"name": "Charlie", "age": 35})
    
    print("\n   Updating a key in named cache...")
    store.cache_set("users", "id:1", {"name": "Alice Smith", "age": 31})
    
    print("\n   Deleting a key from named cache...")
    store.cache_delete("users", "id:2")
    
    print("\n   Deleting the cache...")
    store.delete_cache("users")
    
    # Test cache-specific event handlers
    print("\n4. Testing cache-specific event handlers...")
    
    def on_products_set(ctx: CacheEventContext):
        print(f"  💰 Product updated: {ctx.key} = {ctx.value}")
    
    def on_products_delete(ctx: CacheEventContext):
        print(f"  🗑️  Product removed: {ctx.key}")
    
    # Register handlers only for "products" cache
    event_handler.on(CacheEvent.SET, on_products_set, cache_name="products")
    event_handler.on(CacheEvent.DELETE, on_products_delete, cache_name="products")
    
    print("   Creating 'products' cache...")
    store.create_cache("products")
    
    print("   Setting products (should trigger cache-specific handlers)...")
    store.cache_set("products", "item:1", {"name": "Laptop", "price": 999})
    store.cache_set("products", "item:2", {"name": "Mouse", "price": 29})
    
    print("\n   Creating 'orders' cache...")
    store.create_cache("orders")
    
    print("   Setting orders (should NOT trigger product-specific handlers)...")
    store.cache_set("orders", "order:1", {"product": "Laptop", "qty": 1})
    store.cache_set("orders", "order:2", {"product": "Mouse", "qty": 2})
    
    print("\n   Deleting from products...")
    store.cache_delete("products", "item:2")
    
    print("\n   Deleting from orders...")
    store.cache_delete("orders", "order:1")
    
    # Test unregistering handlers
    print("\n5. Testing unregister event handlers...")
    print("   Unregistering product-specific SET handler...")
    event_handler.off(CacheEvent.SET, on_products_set, cache_name="products")
    
    print("   Setting product (should NOT trigger cache-specific SET handler)...")
    store.cache_set("products", "item:3", {"name": "Keyboard", "price": 79})
    
    print("\n   Deleting product (should still trigger cache-specific DELETE handler)...")
    store.cache_delete("products", "item:3")
    
    # Cleanup
    print("\n6. Cleanup...")
    store.delete_cache("products")
    store.delete_cache("orders")
    
    print("\n" + "=" * 60)
    print("Event Handling Test Complete!")
    print("=" * 60)
    
    # Stop the store
    store.stop()

if __name__ == "__main__":
    main()
