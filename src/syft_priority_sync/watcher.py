"""
File system watcher for detecting changes and triggering instant syncs.
"""

import hashlib
import time
from pathlib import Path
from typing import Dict, Set, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .models import SyncOperation, SyncPriority
from .api import get_sync_priority, load_sync_priority
from .client import send_instant_sync


class SyncPriorityHandler(FileSystemEventHandler):
    """Handles file system events and triggers instant syncs."""
    
    def __init__(self, base_path: Path, client_email: str):
        self.base_path = Path(base_path)
        self.client_email = client_email
        self.file_checksums: Dict[str, str] = {}
        
    def on_created(self, event: FileSystemEvent):
        """Handle file/folder creation."""
        if event.is_directory or self._should_ignore(event.src_path):
            return
            
        self._handle_sync_event(event.src_path, SyncOperation.CREATE)
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification."""
        if event.is_directory or self._should_ignore(event.src_path):
            return
            
        # Check if content actually changed (avoid duplicate events)
        if self._content_changed(event.src_path):
            self._handle_sync_event(event.src_path, SyncOperation.UPDATE)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file/folder deletion."""
        if self._should_ignore(event.src_path):
            return
            
        self._handle_sync_event(event.src_path, SyncOperation.DELETE)
        
        # Remove from checksum cache
        if event.src_path in self.file_checksums:
            del self.file_checksums[event.src_path]
    
    def on_moved(self, event):
        """Handle file/folder move/rename."""
        if self._should_ignore(event.src_path) or self._should_ignore(event.dest_path):
            return
            
        self._handle_sync_event(event.dest_path, SyncOperation.MOVE, old_path=event.src_path)
    
    def _should_ignore(self, file_path: str) -> bool:
        """Check if file should be ignored."""
        path = Path(file_path)
        
        # Ignore syncpriority files themselves
        if path.name.endswith('.syncpriority.yaml'):
            return True
            
        # Ignore hidden files and system files
        if path.name.startswith('.'):
            return True
            
        # Ignore temporary files
        if path.suffix in ['.tmp', '.swp', '.lock']:
            return True
            
        return False
    
    def _content_changed(self, file_path: str) -> bool:
        """Check if file content actually changed."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            new_checksum = hashlib.sha256(content).hexdigest()
            old_checksum = self.file_checksums.get(file_path)
            
            if old_checksum != new_checksum:
                self.file_checksums[file_path] = new_checksum
                return True
                
            return False
        except Exception:
            return True  # Assume changed if we can't read
    
    def _handle_sync_event(self, file_path: str, operation: SyncOperation, old_path: Optional[str] = None):
        """Handle a sync event by checking priorities and sending instant syncs."""
        try:
            path = Path(file_path)
            relative_path = path.relative_to(self.base_path)
            
            # Load sync priority config
            config = load_sync_priority(path)
            if not config:
                return  # No sync priority configured
            
            # Find users who need instant sync for this operation
            instant_users = []
            for rule in config.rules:
                if (rule.priority == SyncPriority.INSTANT and 
                    operation in rule.operations):
                    instant_users.extend(rule.users)
            
            if not instant_users:
                return  # No instant sync needed
            
            # Remove duplicates and expand "*"
            unique_users = set(instant_users)
            if "*" in unique_users:
                # TODO: Get all network users
                unique_users.remove("*")
                # For now, just use explicit users
            
            # Send instant sync to each user
            for user in unique_users:
                if user != self.client_email:  # Don't sync to ourselves
                    send_instant_sync(
                        target_user=user,
                        file_path=path,
                        relative_path=str(relative_path),
                        operation=operation,
                        old_path=old_path
                    )
                    
        except Exception as e:
            # Log error but don't crash watcher
            print(f"Error handling sync event for {file_path}: {e}")


class FileWatcher:
    """Watches a directory for changes and triggers instant syncs."""
    
    def __init__(self, watch_path: Path, client_email: str):
        self.watch_path = Path(watch_path)
        self.client_email = client_email
        self.observer = Observer()
        self.handler = SyncPriorityHandler(watch_path, client_email)
        
    def start(self):
        """Start watching for file changes."""
        self.observer.schedule(
            self.handler, 
            str(self.watch_path), 
            recursive=True
        )
        self.observer.start()
        
    def stop(self):
        """Stop watching for file changes."""
        self.observer.stop()
        self.observer.join()
        
    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self.observer.is_alive()