"""
Tests for the syft_priority_sync models.
"""

import pytest
from pydantic import ValidationError

from syft_priority_sync.models import (
    SyncPriority,
    SyncOperation,
    SyncPriorityRule,
    SyncRequest,
    SyncResponse
)


class TestSyncPriority:
    """Test SyncPriority enum."""
    
    def test_enum_values(self):
        """Test enum values."""
        assert SyncPriority.INSTANT == "instant"
        assert SyncPriority.NORMAL == "normal"


class TestSyncOperation:
    """Test SyncOperation enum."""
    
    def test_enum_values(self):
        """Test enum values."""
        assert SyncOperation.CREATE == "create"
        assert SyncOperation.UPDATE == "update"
        assert SyncOperation.DELETE == "delete"
        assert SyncOperation.MOVE == "move"


class TestSyncPriorityRule:
    """Test SyncPriorityRule model."""
    
    def test_valid_rule(self):
        """Test creating a valid sync priority rule."""
        rule = SyncPriorityRule(
            users=["alice@example.com", "bob@example.com"],
            priority=SyncPriority.INSTANT,
            operations=[SyncOperation.CREATE, SyncOperation.UPDATE]
        )
        
        assert rule.users == ["alice@example.com", "bob@example.com"]
        assert rule.priority == SyncPriority.INSTANT
        assert rule.operations == [SyncOperation.CREATE, SyncOperation.UPDATE]
    
    def test_default_operations(self):
        """Test default operations."""
        rule = SyncPriorityRule(
            users=["alice@example.com"],
            priority=SyncPriority.INSTANT
        )
        
        # Should default to all operations
        expected_ops = [
            SyncOperation.CREATE,
            SyncOperation.UPDATE,
            SyncOperation.DELETE,
            SyncOperation.MOVE
        ]
        assert rule.operations == expected_ops
    
    def test_wildcard_user(self):
        """Test wildcard user."""
        rule = SyncPriorityRule(
            users=["*"],
            priority=SyncPriority.INSTANT
        )
        
        assert rule.users == ["*"]
    
    def test_empty_users_validation(self):
        """Test that empty users list raises validation error."""
        with pytest.raises(ValidationError):
            SyncPriorityRule(
                users=[],
                priority=SyncPriority.INSTANT
            )


class TestSyncRequest:
    """Test SyncRequest model."""
    
    def test_create_request(self):
        """Test creating a sync request."""
        request = SyncRequest(
            sender="alice@example.com",
            target_path="documents/test.txt",
            operation=SyncOperation.CREATE,
            content=b"test content",
            checksum="abc123"
        )
        
        assert request.sender == "alice@example.com"
        assert request.target_path == "documents/test.txt"
        assert request.operation == SyncOperation.CREATE
        assert request.content == b"test content"
        assert request.checksum == "abc123"
    
    def test_move_request(self):
        """Test creating a move request."""
        request = SyncRequest(
            sender="alice@example.com",
            target_path="documents/new_location.txt",
            operation=SyncOperation.MOVE,
            old_path="documents/old_location.txt"
        )
        
        assert request.old_path == "documents/old_location.txt"
    
    def test_delete_request(self):
        """Test creating a delete request."""
        request = SyncRequest(
            sender="alice@example.com",
            target_path="documents/test.txt",
            operation=SyncOperation.DELETE
        )
        
        assert request.content is None
        assert request.checksum is None


class TestSyncResponse:
    """Test SyncResponse model."""
    
    def test_success_response(self):
        """Test creating a success response."""
        response = SyncResponse(
            success=True,
            message="File synced successfully"
        )
        
        assert response.success is True
        assert response.message == "File synced successfully"
        assert response.error_code is None
    
    def test_error_response(self):
        """Test creating an error response."""
        response = SyncResponse(
            success=False,
            message="Permission denied",
            error_code="PERMISSION_DENIED"
        )
        
        assert response.success is False
        assert response.message == "Permission denied"
        assert response.error_code == "PERMISSION_DENIED"