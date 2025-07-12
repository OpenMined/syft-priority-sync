"""
Client for sending instant file syncs via RPC.
"""

import hashlib
from pathlib import Path
from typing import Optional, Union

try:
    from syft_core import Client as SyftBoxClient
    from syft_rpc import rpc
except ImportError:
    # Mock for development
    class MockSyftBoxClient:
        def __init__(self):
            self.email = "demo@example.com"
        
        @classmethod
        def load(cls):
            return cls()
    
    class MockRPC:
        @staticmethod
        def send(url, body, expiry="30s", cache=False):
            class MockFuture:
                def wait(self, timeout=30):
                    class MockResponse:
                        def raise_for_status(self):
                            pass
                        
                        def model(self, model_class):
                            return model_class(success=True, message="Mock sync successful")
                    
                    return MockResponse()
            
            return MockFuture()
    
    SyftBoxClient = MockSyftBoxClient
    rpc = MockRPC()

from .models import SyncRequest, SyncResponse, SyncOperation

__all__ = [
    "send_instant_sync",
    "validate_sync_permissions",
]


def send_instant_sync(
    target_user: str,
    file_path: Path,
    relative_path: str,
    operation: SyncOperation,
    old_path: Optional[str] = None,
    timeout: int = 30
) -> Optional[SyncResponse]:
    """
    Send an instant file sync to a target user via RPC.
    
    Args:
        target_user: Email of user to sync to
        file_path: Full path to the file being synced
        relative_path: Relative path where file should be placed
        operation: Type of sync operation
        old_path: Old path (for move operations)
        timeout: RPC timeout in seconds
        
    Returns:
        SyncResponse if successful, None if failed
    """
    try:
        client = SyftBoxClient.load()
        
        # Read file content for create/update operations
        content = None
        checksum = None
        
        if operation in [SyncOperation.CREATE, SyncOperation.UPDATE]:
            if file_path.exists() and file_path.is_file():
                with open(file_path, 'rb') as f:
                    content = f.read()
                checksum = hashlib.sha256(content).hexdigest()
        
        # Create sync request
        request = SyncRequest(
            sender=client.email,
            target_path=relative_path,
            operation=operation,
            content=content,
            old_path=old_path,
            checksum=checksum
        )
        
        # Send RPC request
        url = rpc.make_url(
            datasite=target_user, 
            app_name="syft-priority-sync", 
            endpoint="sync"
        )
        
        future = rpc.send(
            url=url,
            body=request,
            expiry="30s",
            cache=False
        )
        
        response = future.wait(timeout=timeout)
        response.raise_for_status()
        
        return response.model(SyncResponse)
        
    except Exception:
        return None


def validate_sync_permissions(
    sender: str,
    target_path: str,
    operation: SyncOperation,
    base_path: Path
) -> bool:
    """
    Validate if sender has permission to sync to target path.
    
    Uses syft.pub.yaml files to check permissions.
    
    Args:
        sender: Email of the sender
        target_path: Target path for the sync
        operation: Type of sync operation
        base_path: Base path to resolve relative paths
        
    Returns:
        True if sync is allowed, False otherwise
    """
    try:
        # Import syft-core permission validation
        from syft_core.permissions import check_permission
        
        full_path = base_path / target_path
        
        # Map sync operations to permission types
        permission_map = {
            SyncOperation.CREATE: "write",
            SyncOperation.UPDATE: "write", 
            SyncOperation.DELETE: "admin",
            SyncOperation.MOVE: "admin"
        }
        
        required_permission = permission_map.get(operation, "write")
        
        return check_permission(
            user=sender,
            path=str(full_path),
            permission=required_permission
        )
        
    except Exception:
        # If permission check fails, deny by default
        return False