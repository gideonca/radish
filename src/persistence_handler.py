"""
Persistence handler module for managing cache persistence.

This module handles saving and loading cache data to/from disk,
with support for timestamped backups and automatic persistence.
"""
import os
import json
import time
import threading
from typing import Any, Optional, Dict
from datetime import datetime
from pathlib import Path
from .expiring_store import ExpiringStore
from src.logging_handler import LoggingHandler


class PersistenceHandler:
    """
    Handles persistence operations for cache data.
    
    This class manages saving cache data to timestamped JSON files in
    ~/.radish/cache_backup/ directory with automatic backup intervals.
    """
    
    def __init__(self, 
                 backup_dir: Optional[str] = None,
                 auto_backup_interval: float = 3600,  # 1 hour
                 store: Optional[ExpiringStore] = None):
        """
        Initialize the persistence handler.
        
        Args:
            backup_dir: Directory to store backup files. If None, uses ~/.radish/cache_backup
            auto_backup_interval: How often to auto-backup caches (seconds). Set to 0 to disable.
            store: The ExpiringStore instance to backup
        """
        self._lock = threading.RLock()
        self._store = store
        self._stop_backup = threading.Event()
        
        # Set up backup directory
        if backup_dir is None:
            self._backup_dir = Path.home() / ".radish" / "cache_backup"
        else:
            self._backup_dir = Path(backup_dir)
        
        # Create backup directory
        self._create_backup_directory()
        
        # Start auto-backup thread if interval > 0
        if auto_backup_interval > 0:
            self._backup_interval = auto_backup_interval
            self._backup_thread = threading.Thread(
                target=self._auto_backup_loop,
                daemon=True
            )
            self._backup_thread.start()
            
        self.logging_handler = LoggingHandler()
    
    def _create_backup_directory(self):
        """Create the backup directory with proper permissions."""
        try:
            self._backup_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(self._backup_dir, 0o755)
        except Exception as e:
            print(f"Warning: Error creating backup directory {self._backup_dir}: {e}")
            self.logging_handler.log_server_event(f"Warning: Error creating backup directory {self._backup_dir}: {e}")
    
    def set_store(self, store: ExpiringStore):
        """
        Set or update the ExpiringStore instance.
        
        Args:
            store: The ExpiringStore instance to backup
        """
        with self._lock:
            self._store = store
    
    def backup_all(self) -> Dict[str, bool]:
        """
        Backup all caches and stores.
        
        Returns:
            Dict mapping cache names to success status
        """
        if not self._store:
            return {}
        
        results = {}
        
        # Backup main default store
        results['default_store'] = self.backup_default_store()
        
        # Backup all named caches
        cache_names = self._store.list_caches()
        for cache_name in cache_names:
            results[f'cache_{cache_name}'] = self.backup_cache(cache_name)
        
        return results
    
    def backup_default_store(self) -> bool:
        """
        Backup the default store to a timestamped JSON file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._store:
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"default_store_{timestamp}.json"
            filepath = self._backup_dir / filename
            
            # Get all data from default store
            with self._lock:
                store_data = {}
                # Note: We'd need access to the internal store data
                # For now, we'll create a structure that can be extended
                backup_data = {
                    'type': 'default_store',
                    'timestamp': timestamp,
                    'datetime': datetime.now().isoformat(),
                    'data': store_data  # Would contain actual store data
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error backing up default store: {e}")
            return False
    
    def backup_cache(self, cache_name: str) -> bool:
        """
        Backup a named cache to a timestamped JSON file.
        
        Args:
            cache_name: Name of the cache to backup
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._store:
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"cache_{cache_name}_{timestamp}.json"
            filepath = self._backup_dir / filename
            
            # Get all cache data
            with self._lock:
                cache_data = self._store.cache_get_all(cache_name)
                
                if cache_data is None:
                    print(f"Cache {cache_name} does not exist")
                    return False
                
                backup_data = {
                    'type': 'named_cache',
                    'cache_name': cache_name,
                    'timestamp': timestamp,
                    'datetime': datetime.now().isoformat(),
                    'item_count': len(cache_data),
                    'data': cache_data
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error backing up cache {cache_name}: {e}")
            return False
    
    def backup_store(self, cache_name: str, store_name: str) -> bool:
        """
        Backup a specific store within a cache to a timestamped JSON file.
        
        Args:
            cache_name: Name of the cache containing the store
            store_name: Name of the store to backup
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._store:
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"store_{cache_name}_{store_name}_{timestamp}.json"
            filepath = self._backup_dir / filename
            
            # Get store data
            with self._lock:
                # This would need implementation in ExpiringStore
                # For now, we create the structure
                backup_data = {
                    'type': 'expiring_store',
                    'cache_name': cache_name,
                    'store_name': store_name,
                    'timestamp': timestamp,
                    'datetime': datetime.now().isoformat(),
                    'data': {}  # Would contain actual store data
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error backing up store {cache_name}:{store_name}: {e}")
            return False
    
    def restore_cache(self, filepath: str) -> Optional[str]:
        """
        Restore a cache from a backup file.
        
        Args:
            filepath: Path to the backup JSON file
            
        Returns:
            Optional[str]: Name of the restored cache, or None if failed
        """
        if not self._store:
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            cache_type = backup_data.get('type')
            
            if cache_type == 'named_cache':
                cache_name = backup_data['cache_name']
                cache_data = backup_data['data']
                
                # Create cache if it doesn't exist
                self._store.create_cache(cache_name)
                
                # Restore all data
                for key, value in cache_data.items():
                    self._store.cache_set(cache_name, key, value)
                
                return cache_name
            
            return None
        except Exception as e:
            print(f"Error restoring cache from {filepath}: {e}")
            return None
    
    def list_backups(self, cache_name: Optional[str] = None) -> list:
        """
        List all backup files, optionally filtered by cache name.
        
        Args:
            cache_name: Optional cache name to filter by
            
        Returns:
            List of backup file paths
        """
        try:
            backups = []
            pattern = f"*_{cache_name}_*.json" if cache_name else "*.json"
            
            for filepath in sorted(self._backup_dir.glob(pattern), reverse=True):
                backups.append({
                    'filepath': str(filepath),
                    'filename': filepath.name,
                    'size': filepath.stat().st_size,
                    'modified': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                })
            
            return backups
        except Exception as e:
            print(f"Error listing backups: {e}")
            self.logging_handler.log_server_event(f"Error listing backups: {e}")
            return []
    
    def cleanup_old_backups(self, days: int = 30):
        """
        Delete backup files older than specified days.
        
        Args:
            days: Number of days to keep backups
        """
        try:
            cutoff_time = time.time() - (days * 86400)
            
            for filepath in self._backup_dir.glob("*.json"):
                if filepath.stat().st_mtime < cutoff_time:
                    filepath.unlink()
                    print(f"Deleted old backup: {filepath.name}")
                    self.logging_handler.log_server_event(f"Deleted old backup: {filepath.name}")
        except Exception as e:
            print(f"Error cleaning up old backups: {e}")
            self.logging_handler.log_server_event(f"Error cleaning up old backups: {e}")
    
    def get_backup_dir(self) -> Path:
        """
        Get the backup directory path.
        
        Returns:
            Path object for the backup directory
        """
        return self._backup_dir
    
    def _auto_backup_loop(self):
        """Background thread for automatic backups."""
        while not self._stop_backup.is_set():
            time.sleep(self._backup_interval)
            
            if not self._stop_backup.is_set():
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running automatic backup...")
                self.logging_handler.log_server_event("Running automatic backup...")
                results = self.backup_all()
                success_count = sum(1 for v in results.values() if v)
                print(f"Backup completed: {success_count}/{len(results)} successful")
                self.logging_handler.log_server_event(f"Backup completed: {success_count}/{len(results)} successful")
    
    def stop(self):
        """Stop background backup thread."""
        self._stop_backup.set()
        if hasattr(self, '_backup_thread') and self._backup_thread.is_alive():
            self._backup_thread.join(timeout=5)