"""
RPC server for receiving instant file syncs.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

try:
    from syft_core import Client as SyftBoxClient
    from syft_event import SyftEvents
    from syft_event.types import Request
except ImportError:
    # Mock for development
    class MockSyftBoxClient:
        def __init__(self):
            self.email = "demo@example.com"
        
        @classmethod
        def load(cls):
            return cls()
    
    class MockSyftEvents:
        def __init__(self, app_name, client=None):
            self.app_name = app_name
            self.client = client or MockSyftBoxClient()
            
        def on_request(self, endpoint):
            def decorator(func):
                return func
            return decorator
            
        def run_forever(self):
            pass
    
    SyftBoxClient = MockSyftBoxClient
    SyftEvents = MockSyftEvents

from .models import SyncRequest, SyncResponse, SyncOperation
from .client import validate_sync_permissions


class PrioritySyncServer:
    """Server for handling instant file sync requests."""
    
    def __init__(self, client: Optional[SyftBoxClient] = None):
        self.client = client or SyftBoxClient.load()
        self.server = SyftEvents("syft-priority-sync", client=self.client)
        self.base_path = self._get_base_path()
        
        # Register sync endpoint
        @self.server.on_request("/sync")
        def sync_handler(request: SyncRequest, ctx: Request) -> SyncResponse:
            return self.handle_sync_request(request, ctx)
    
    def _get_base_path(self) -> Path:
        """Get the base path for this user's datasite."""
        try:
            # Get user's datasite directory
            home = Path.home()
            datasite_path = home / "SyftBox" / "datasites" / self.client.email
            return datasite_path
        except Exception:
            # Fallback to current directory
            return Path(".")
    
    def handle_sync_request(self, request: SyncRequest, ctx: Request) -> SyncResponse:
        """
        Handle an incoming sync request.
        
        Args:
            request: The sync request
            ctx: RPC request context
            
        Returns:
            SyncResponse indicating success/failure
        """
        try:
            # Validate permissions
            if not validate_sync_permissions(
                sender=request.sender,
                target_path=request.target_path,
                operation=request.operation,
                base_path=self.base_path
            ):
                return SyncResponse(
                    success=False,
                    message=f"Permission denied for {request.sender} to {request.operation} {request.target_path}",
                    error_code="PERMISSION_DENIED"
                )
            
            # Get target file path
            target_path = self.base_path / request.target_path
            
            # Handle different sync operations
            if request.operation == SyncOperation.CREATE:
                return self._handle_create(request, target_path)
            elif request.operation == SyncOperation.UPDATE:
                return self._handle_update(request, target_path)
            elif request.operation == SyncOperation.DELETE:
                return self._handle_delete(request, target_path)
            elif request.operation == SyncOperation.MOVE:
                return self._handle_move(request, target_path)
            else:
                return SyncResponse(
                    success=False,
                    message=f"Unknown operation: {request.operation}",
                    error_code="UNKNOWN_OPERATION"
                )
                
        except Exception as e:
            return SyncResponse(
                success=False,
                message=f"Sync failed: {str(e)}",
                error_code="SYNC_ERROR"
            )
    
    def _handle_create(self, request: SyncRequest, target_path: Path) -> SyncResponse:
        """Handle file creation."""
        try:
            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Don't overwrite existing files
            if target_path.exists():
                return SyncResponse(
                    success=False,
                    message=f"File already exists: {target_path}",
                    error_code="FILE_EXISTS"
                )
            
            # Write content
            if request.content is not None:
                with open(target_path, 'wb') as f:
                    f.write(request.content)
            else:
                # Create empty file
                target_path.touch()
            
            return SyncResponse(
                success=True,
                message=f"Created: {target_path}"
            )
            
        except Exception as e:
            return SyncResponse(
                success=False,
                message=f"Create failed: {str(e)}",
                error_code="CREATE_ERROR"
            )
    
    def _handle_update(self, request: SyncRequest, target_path: Path) -> SyncResponse:
        """Handle file update."""
        try:
            # File must exist for update
            if not target_path.exists():
                return SyncResponse(
                    success=False,
                    message=f"File not found: {target_path}",
                    error_code="FILE_NOT_FOUND"
                )
            
            # Update content
            if request.content is not None:
                with open(target_path, 'wb') as f:
                    f.write(request.content)
            
            return SyncResponse(
                success=True,
                message=f"Updated: {target_path}"
            )
            
        except Exception as e:
            return SyncResponse(
                success=False,
                message=f"Update failed: {str(e)}",
                error_code="UPDATE_ERROR"
            )
    
    def _handle_delete(self, request: SyncRequest, target_path: Path) -> SyncResponse:
        """Handle file deletion."""
        try:
            if not target_path.exists():
                return SyncResponse(
                    success=True,
                    message=f"File already deleted: {target_path}"
                )
            
            if target_path.is_file():
                target_path.unlink()
            elif target_path.is_dir():
                shutil.rmtree(target_path)
            
            return SyncResponse(
                success=True,
                message=f"Deleted: {target_path}"
            )
            
        except Exception as e:
            return SyncResponse(
                success=False,
                message=f"Delete failed: {str(e)}",
                error_code="DELETE_ERROR"
            )
    
    def _handle_move(self, request: SyncRequest, target_path: Path) -> SyncResponse:
        """Handle file move/rename."""
        try:
            if not request.old_path:
                return SyncResponse(
                    success=False,
                    message="Old path required for move operation",
                    error_code="MISSING_OLD_PATH"
                )
            
            old_path = self.base_path / request.old_path
            
            if not old_path.exists():
                return SyncResponse(
                    success=False,
                    message=f"Source file not found: {old_path}",
                    error_code="SOURCE_NOT_FOUND"
                )
            
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(old_path), str(target_path))
            
            return SyncResponse(
                success=True,
                message=f"Moved: {old_path} -> {target_path}"
            )
            
        except Exception as e:
            return SyncResponse(
                success=False,
                message=f"Move failed: {str(e)}",
                error_code="MOVE_ERROR"
            )
    
    def run(self):
        """Start the sync server."""
        self.server.run_forever()


def create_server(client: Optional[SyftBoxClient] = None) -> PrioritySyncServer:
    """Create and return a PrioritySyncServer."""
    return PrioritySyncServer(client)