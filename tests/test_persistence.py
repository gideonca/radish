#!/usr/bin/env python3
"""
Test script to demonstrate persistence/backup functionality.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.expiring_store import ExpiringStore
from src.persistence_handler import PersistenceHandler

def main():
    print("=" * 60)
    print("Radish Persistence Handler Test")
    print("=" * 60)
    
    # Create store and persistence handler
    store = ExpiringStore()
    persistence = PersistenceHandler(
        auto_backup_interval=0,  # Disable auto-backup for this test
        store=store
    )
    
    print(f"\nBackup directory: {persistence.get_backup_dir()}\n")
    
    # Create some test caches
    print("Creating test caches...")
    store.create_cache("users")
    store.create_cache("products")
    store.create_cache("sessions")
    
    # Add data to caches
    print("Adding test data...")
    store.cache_set("users", "user:1", "alice@example.com")
    store.cache_set("users", "user:2", "bob@example.com")
    store.cache_set("users", "user:3", "charlie@example.com")
    
    store.cache_set("products", "prod:100", '{"name": "Laptop", "price": 1200}')
    store.cache_set("products", "prod:101", '{"name": "Mouse", "price": 25}')
    
    store.cache_set("sessions", "sess:abc123", "user:1")
    store.cache_set("sessions", "sess:def456", "user:2")
    
    print("\nCache contents:")
    for cache_name in ["users", "products", "sessions"]:
        data = store.cache_get_all(cache_name)
        print(f"  {cache_name}: {len(data)} items")
    
    # Backup individual cache
    print("\n" + "-" * 60)
    print("Backing up 'users' cache...")
    success = persistence.backup_cache("users")
    print(f"Backup result: {'Success' if success else 'Failed'}")
    
    # Backup all caches
    print("\n" + "-" * 60)
    print("Backing up all caches...")
    results = persistence.backup_all()
    print("Backup results:")
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
    
    # List backups
    print("\n" + "-" * 60)
    print("Listing all backups:")
    backups = persistence.list_backups()
    for backup in backups:
        print(f"  - {backup['filename']}")
        print(f"    Size: {backup['size']} bytes")
        print(f"    Modified: {backup['modified']}")
    
    # List backups for specific cache
    print("\n" + "-" * 60)
    print("Listing backups for 'users' cache:")
    user_backups = persistence.list_backups("users")
    for backup in user_backups:
        print(f"  - {backup['filename']}")
    
    # Test restore
    if user_backups:
        print("\n" + "-" * 60)
        print("Testing restore functionality...")
        
        # Delete the cache
        store.delete_cache("users")
        print("Deleted 'users' cache")
        
        # Verify it's gone
        caches = store.list_caches()
        print(f"Remaining caches: {caches}")
        
        # Restore from backup
        restored = persistence.restore_cache(user_backups[0]['filepath'])
        if restored:
            print(f"Restored cache: {restored}")
            
            # Verify data
            data = store.cache_get_all(restored)
            print(f"Restored data: {len(data)} items")
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print("Restore failed")
    
    # Cleanup
    print("\n" + "-" * 60)
    print("Cleaning up...")
    store.stop()
    persistence.stop()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print(f"Backup files are in: {persistence.get_backup_dir()}")
    print("=" * 60)

if __name__ == "__main__":
    main()
