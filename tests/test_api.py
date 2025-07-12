"""
Tests for the syft_priority_sync API.
"""

import tempfile
import pytest
from pathlib import Path

from syft_priority_sync.api import (
    set_sync_priority,
    get_sync_priority, 
    remove_sync_priority,
    list_sync_priorities
)
from syft_priority_sync.models import SyncPriority


class TestSyncPriorityAPI:
    """Test sync priority API functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.txt"
        self.test_file.write_text("test content")
    
    def test_set_sync_priority_single_user(self):
        """Test setting sync priority for a single user."""
        result = set_sync_priority(
            str(self.test_file),
            ["alice@example.com"],
            priority="instant"
        )
        assert result is True
        
        # Check that .syncpriority.yaml file was created
        priority_file = self.test_file.parent / f"{self.test_file.name}.syncpriority.yaml"
        assert priority_file.exists()
    
    def test_set_sync_priority_multiple_users(self):
        """Test setting sync priority for multiple users."""
        result = set_sync_priority(
            str(self.test_file),
            ["alice@example.com", "bob@example.com"],
            priority="instant"
        )
        assert result is True
    
    def test_set_sync_priority_wildcard(self):
        """Test setting sync priority with wildcard."""
        result = set_sync_priority(
            str(self.test_file),
            "*",
            priority="instant"
        )
        assert result is True
    
    def test_get_sync_priority(self):
        """Test getting sync priority for a user."""
        # First set priority
        set_sync_priority(
            str(self.test_file),
            ["alice@example.com"],
            priority="instant"
        )
        
        # Then get it
        priority = get_sync_priority(str(self.test_file), "alice@example.com")
        assert priority == SyncPriority.INSTANT
        
        # Test user without priority
        priority = get_sync_priority(str(self.test_file), "bob@example.com")
        assert priority == SyncPriority.NORMAL
    
    def test_list_sync_priorities(self):
        """Test listing sync priorities."""
        # Set some priorities
        set_sync_priority(
            str(self.test_file),
            ["alice@example.com", "bob@example.com"],
            priority="instant"
        )
        
        rules = list_sync_priorities(str(self.test_file))
        assert len(rules) == 1
        assert rules[0].users == ["alice@example.com", "bob@example.com"]
        assert rules[0].priority == SyncPriority.INSTANT
    
    def test_remove_sync_priority_specific_users(self):
        """Test removing sync priority for specific users."""
        # Set priority first
        set_sync_priority(
            str(self.test_file),
            ["alice@example.com", "bob@example.com"],
            priority="instant"
        )
        
        # Remove for one user
        result = remove_sync_priority(str(self.test_file), ["alice@example.com"])
        assert result is True
        
        # Check that only Bob remains
        priority = get_sync_priority(str(self.test_file), "alice@example.com")
        assert priority == SyncPriority.NORMAL
        
        priority = get_sync_priority(str(self.test_file), "bob@example.com")
        assert priority == SyncPriority.INSTANT
    
    def test_remove_sync_priority_all(self):
        """Test removing all sync priorities."""
        # Set priority first
        set_sync_priority(
            str(self.test_file),
            ["alice@example.com"],
            priority="instant"
        )
        
        # Remove all
        result = remove_sync_priority(str(self.test_file))
        assert result is True
        
        # Check that file was removed
        priority_file = self.test_file.parent / f"{self.test_file.name}.syncpriority.yaml"
        assert not priority_file.exists()
    
    def test_nonexistent_file(self):
        """Test API with nonexistent file."""
        nonexistent = Path(self.temp_dir) / "nonexistent.txt"
        
        # Should still work - creates priority file
        result = set_sync_priority(
            str(nonexistent),
            ["alice@example.com"],
            priority="instant"
        )
        assert result is True
    
    def test_directory_priority(self):
        """Test setting priority on a directory."""
        test_dir = Path(self.temp_dir) / "test_dir"
        test_dir.mkdir()
        
        result = set_sync_priority(
            str(test_dir),
            ["alice@example.com"],
            priority="instant"
        )
        assert result is True
        
        # Check that .syncpriority.yaml file was created
        priority_file = test_dir.parent / f"{test_dir.name}.syncpriority.yaml"
        assert priority_file.exists()