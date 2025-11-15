# Radish Persistence Guide

## Overview

Radish provides automatic backup functionality that saves your cache data to timestamped JSON files in the `~/.radish/cache_backup` directory. This ensures your data can be recovered in case of server restarts or failures.

## Features

- **Automatic Backups**: Scheduled backups every 5 minutes (configurable)
- **Timestamped Files**: Each backup includes a timestamp in the filename
- **Named Caches**: Each cache is backed up to a separate JSON file
- **JSON Format**: Human-readable backup files
- **Restore Capability**: Load backups to restore cache data
- **Cleanup**: Automatic deletion of old backups

## Backup Directory Structure

Backups are stored in:
```
~/.radish/cache_backup/
├── cache_users_20251115_161118.json
├── cache_products_20251115_161118.json
├── cache_sessions_20251115_161210.json
└── default_store_20251115_161118.json
```

## Backup File Format

Each backup file contains:
- **type**: Type of backup (named_cache, default_store, or expiring_store)
- **cache_name**: Name of the cache
- **timestamp**: Backup timestamp (YYYYMMDD_HHMMSS)
- **datetime**: ISO format datetime
- **item_count**: Number of items in the cache
- **data**: The actual cache data

Example backup file (`cache_users_20251115_161118.json`):
```json
{
  "type": "named_cache",
  "cache_name": "users",
  "timestamp": "20251115_161118",
  "datetime": "2025-11-15T16:11:18.027451",
  "item_count": 3,
  "data": {
    "user:1": "alice@example.com",
    "user:2": "bob@example.com",
    "user:3": "charlie@example.com"
  }
}
```

## Configuration

### Default Settings

The server starts with these default persistence settings:
- **Backup Directory**: `~/.radish/cache_backup`
- **Auto-backup Interval**: 300 seconds (5 minutes)
- **Backup on Shutdown**: Yes

### Custom Configuration

You can customize persistence in `server.py`:

```python
from src.persistence_handler import PersistenceHandler

# Custom backup directory and interval
persistence_handler = PersistenceHandler(
    backup_dir="/custom/path/to/backups",  # Custom backup location
    auto_backup_interval=600,               # Backup every 10 minutes
    store=store
)

# Disable auto-backup (manual only)
persistence_handler = PersistenceHandler(
    auto_backup_interval=0,  # Set to 0 to disable
    store=store
)
```

## Using Persistence Programmatically

### Manual Backup

```python
from src.persistence_handler import PersistenceHandler

# Initialize
persistence = PersistenceHandler(store=store)

# Backup a specific cache
success = persistence.backup_cache("users")

# Backup all caches
results = persistence.backup_all()
print(f"Backed up {sum(results.values())} caches")
```

### Listing Backups

```python
# List all backups
backups = persistence.list_backups()
for backup in backups:
    print(f"{backup['filename']} - {backup['size']} bytes")

# List backups for specific cache
user_backups = persistence.list_backups("users")
```

### Restoring from Backup

```python
# Restore a cache from the most recent backup
backups = persistence.list_backups("users")
if backups:
    restored_cache = persistence.restore_cache(backups[0]['filepath'])
    print(f"Restored: {restored_cache}")
```

### Cleanup Old Backups

```python
# Delete backups older than 30 days
persistence.cleanup_old_backups(days=30)

# Delete backups older than 7 days
persistence.cleanup_old_backups(days=7)
```

## Automatic Backups

The server performs automatic backups at the configured interval:

1. Server starts
2. Every 5 minutes (default), all caches are backed up
3. On shutdown, a final backup is performed

You'll see messages like:
```
[2025-11-15 16:15:00] Running automatic backup...
Backup completed: 4/4 successful
```

## Backup on Server Shutdown

When you stop the server (Ctrl+C), a final backup is automatically performed:

```
^C
Shutting down server...
Performing final backup...
Backup completed: 4/4 successful
Cleaning up resources...
Server shutdown complete.
```

## Testing Persistence

Use the provided test script:

```bash
python3 scripts/test_persistence.py
```

This script:
1. Creates test caches with sample data
2. Performs backups
3. Lists all backup files
4. Tests restore functionality
5. Demonstrates cleanup

## Best Practices

### 1. Regular Backups

Keep the default 5-minute interval for production:
```python
persistence_handler = PersistenceHandler(
    auto_backup_interval=300,  # 5 minutes
    store=store
)
```

### 2. Monitor Backup Size

Check backup directory size periodically:
```bash
du -sh ~/.radish/cache_backup
```

### 3. Cleanup Old Backups

Schedule regular cleanup to prevent disk space issues:
```python
# Run weekly or monthly
persistence.cleanup_old_backups(days=30)
```

### 4. Test Restores

Periodically test that your backups can be restored:
```python
# Test restore process
backups = persistence.list_backups("critical_cache")
if backups:
    test_restore = persistence.restore_cache(backups[0]['filepath'])
```

### 5. Backup Before Maintenance

Perform manual backup before making changes:
```python
# Manual backup before risky operations
persistence.backup_all()
```

## Recovery Scenarios

### Scenario 1: Restore Deleted Cache

```python
# Cache was accidentally deleted
store.delete_cache("users")

# Find recent backup
backups = persistence.list_backups("users")

# Restore from most recent
persistence.restore_cache(backups[0]['filepath'])
```

### Scenario 2: Restore All Caches After Crash

```python
# Get all backup files
backups = persistence.list_backups()

# Group by cache name and get most recent
from collections import defaultdict
cache_backups = defaultdict(list)
for backup in backups:
    # Parse cache name from filename
    filename = backup['filename']
    if filename.startswith('cache_'):
        cache_name = filename.split('_')[1]
        cache_backups[cache_name].append(backup)

# Restore each cache from most recent backup
for cache_name, cache_files in cache_backups.items():
    if cache_files:
        most_recent = cache_files[0]  # Already sorted by date
        persistence.restore_cache(most_recent['filepath'])
```

### Scenario 3: Roll Back to Earlier Version

```python
# Find all backups for a cache
backups = persistence.list_backups("users")

# Restore from earlier backup (not the most recent)
# Backups are sorted newest first, so index 1 is second newest
if len(backups) > 1:
    persistence.restore_cache(backups[1]['filepath'])
```

## Command Line Tools

### View Backup Files

```bash
# List all backups
ls -lh ~/.radish/cache_backup/

# View a specific backup
cat ~/.radish/cache_backup/cache_users_20251115_161118.json

# Pretty print JSON
python3 -m json.tool ~/.radish/cache_backup/cache_users_20251115_161118.json
```

### Search Backups

```bash
# Find all backups for a specific cache
ls ~/.radish/cache_backup/cache_users_*.json

# Find backups from a specific date
ls ~/.radish/cache_backup/*_20251115_*.json

# Count backups
ls ~/.radish/cache_backup/*.json | wc -l
```

### Manual Cleanup

```bash
# Delete backups older than 30 days
find ~/.radish/cache_backup -name "*.json" -mtime +30 -delete

# Delete all backups (use with caution!)
rm ~/.radish/cache_backup/*.json
```

## Troubleshooting

### Problem: No backups being created

**Check:**
1. Verify backup interval is not 0
2. Check disk space: `df -h ~`
3. Check permissions: `ls -ld ~/.radish/cache_backup`
4. Look for errors in server output

### Problem: Backup directory not found

**Solution:**
The directory is created automatically. If it fails, check:
```bash
# Manually create directory
mkdir -p ~/.radish/cache_backup
chmod 755 ~/.radish/cache_backup
```

### Problem: Restore fails

**Check:**
1. Verify backup file exists and is readable
2. Check JSON format is valid: `python3 -m json.tool file.json`
3. Ensure cache name in backup matches target cache

### Problem: Too many backup files

**Solution:**
```python
# Reduce backup retention
persistence.cleanup_old_backups(days=7)

# Or increase backup interval
persistence_handler = PersistenceHandler(
    auto_backup_interval=600,  # 10 minutes instead of 5
    store=store
)
```

## Performance Considerations

### Backup Performance

- Backups are performed in the background thread
- Large caches may take time to serialize to JSON
- Disk I/O occurs during backup operations

### Optimization Tips

1. **Increase Backup Interval** for large datasets:
   ```python
   auto_backup_interval=900  # 15 minutes
   ```

2. **Exclude Non-Critical Caches**: Create a custom backup method that only backs up important caches

3. **Monitor Disk Space**: Set up alerts when backup directory exceeds threshold

## Integration with Monitoring

Example integration with a monitoring system:

```python
import time
from datetime import datetime

def monitor_backups():
    """Monitor backup health"""
    backups = persistence.list_backups()
    
    if not backups:
        alert("No backups found!")
        return
    
    # Check if most recent backup is too old
    most_recent = backups[0]
    backup_time = datetime.fromisoformat(most_recent['modified'])
    age_minutes = (datetime.now() - backup_time).total_seconds() / 60
    
    if age_minutes > 10:  # Alert if no backup in 10 minutes
        alert(f"Last backup was {age_minutes:.1f} minutes ago")
    
    # Check backup directory size
    total_size = sum(b['size'] for b in backups)
    if total_size > 1_000_000_000:  # 1 GB
        alert(f"Backup directory is {total_size / 1_000_000_000:.2f} GB")
```

## See Also

- [User Guide](USER_GUIDE.md) - General usage guide
- [Named Cache Guide](NAMED_CACHE_GUIDE.md) - Working with named caches
- [Logging Guide](../src/logging_handler.py) - Server logging system
