"""
Data models for syft-priority-sync instant file synchronization.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field

__all__ = [
    "SyncPriority",
    "SyncPriorityRule", 
    "SyncRequest",
    "SyncResponse",
    "SyncOperation",
]


class SyncPriority(str, Enum):
    """Priority levels for file synchronization."""
    INSTANT = "instant"  # Sync immediately via RPC
    NORMAL = "normal"    # Use default SyftBox sync


class SyncOperation(str, Enum):
    """Types of file operations that can be synced."""
    CREATE = "create"
    UPDATE = "update" 
    DELETE = "delete"
    MOVE = "move"


class SyncPriorityRule(BaseModel):
    """A rule defining sync priority for specific users."""
    users: List[str] = Field(
        min_length=1,
        description="List of user emails or '*' for all users"
    )
    priority: SyncPriority = Field(
        description="Sync priority level for these users"
    )
    operations: List[SyncOperation] = Field(
        default=[SyncOperation.CREATE, SyncOperation.UPDATE, SyncOperation.DELETE, SyncOperation.MOVE],
        description="Which operations to sync instantly"
    )


class SyncPriorityConfig(BaseModel):
    """Configuration for a file/folder's sync priorities."""
    rules: List[SyncPriorityRule] = Field(
        description="List of sync priority rules"
    )
    created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this config was created"
    )
    updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this config was last updated"
    )


class SyncRequest(BaseModel):
    """Request to sync a file/folder instantly via RPC."""
    sender: str = Field(description="Email of the sender")
    target_path: str = Field(description="Relative path where file should be placed")
    operation: SyncOperation = Field(description="Type of sync operation")
    content: Optional[bytes] = Field(default=None, description="File content (for create/update)")
    old_path: Optional[str] = Field(default=None, description="Old path (for move operations)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When sync was initiated"
    )
    checksum: Optional[str] = Field(default=None, description="Content checksum for validation")


class SyncResponse(BaseModel):
    """Response to a sync request."""
    success: bool = Field(description="Whether sync was successful")
    message: str = Field(description="Status message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When response was generated"
    )
    error_code: Optional[str] = Field(default=None, description="Error code if failed")