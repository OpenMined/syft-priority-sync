#!/usr/bin/env python3
"""
SyftBox app for syft-priority-sync.

Runs the file watcher and RPC server for instant file synchronization.
"""

import sys
import signal
from pathlib import Path
from threading import Thread

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from syft_priority_sync.server import create_server
from syft_priority_sync.watcher import FileWatcher

try:
    from syft_core import Client as SyftBoxClient
except ImportError:
    print("Warning: syft_core not available, using mock client")
    class MockSyftBoxClient:
        def __init__(self):
            self.email = "demo@example.com"
        
        @classmethod
        def load(cls):
            return cls()
    
    SyftBoxClient = MockSyftBoxClient


class PrioritySyncApp:
    """Main application for syft-priority-sync."""
    
    def __init__(self):
        self.client = SyftBoxClient.load()
        self.server = create_server(self.client)
        self.watcher = None
        self.server_thread = None
        self.running = False
        
    def start(self):
        """Start the sync server and file watcher."""
        print(f"Starting syft-priority-sync for {self.client.email}")
        
        # Start RPC server in a separate thread
        self.server_thread = Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        
        # Start file watcher for the user's datasite
        watch_path = self._get_watch_path()
        if watch_path.exists():
            print(f"Watching for changes in: {watch_path}")
            self.watcher = FileWatcher(watch_path, self.client.email)
            self.watcher.start()
        else:
            print(f"Watch path does not exist: {watch_path}")
        
        self.running = True
        print("Syft-priority-sync is running. Press Ctrl+C to stop.")
        
        # Wait for shutdown signal
        try:
            while self.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the sync server and file watcher."""
        print("Stopping syft-priority-sync...")
        self.running = False
        
        if self.watcher:
            self.watcher.stop()
            
        print("Syft-priority-sync stopped.")
    
    def _run_server(self):
        """Run the RPC server."""
        try:
            self.server.run()
        except Exception as e:
            print(f"Server error: {e}")
    
    def _get_watch_path(self) -> Path:
        """Get the path to watch for file changes."""
        try:
            home = Path.home()
            return home / "SyftBox" / "datasites" / self.client.email
        except Exception:
            return Path(".")


def main():
    """Main entry point."""
    app = PrioritySyncApp()
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        app.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    app.start()


if __name__ == "__main__":
    main()