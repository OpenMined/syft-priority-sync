"""
Python API for managing syncpriority.yaml files.

Similar to syft-perm API but for sync priorities.
"""

import yaml
from pathlib import Path
from typing import List, Optional, Union
from .models import SyncPriorityConfig, SyncPriorityRule, SyncPriority, SyncOperation


def set_sync_priority(
    file_path: Union[str, Path],
    users: Union[str, List[str]], 
    priority: Union[str, SyncPriority] = SyncPriority.INSTANT,
    operations: Optional[List[Union[str, SyncOperation]]] = None
) -> bool:
    """
    Set sync priority for a file or folder.
    
    Args:
        file_path: Path to file or folder
        users: User email(s) or "*" for all users
        priority: Sync priority level (instant/normal)
        operations: Which operations to sync (create/update/delete)
    
    Example:
        >>> import syft_priority_sync as sps
        >>> sps.set_sync_priority("important.txt", ["alice@university.edu", "bob@lab.org"])
        >>> sps.set_sync_priority("shared_folder/", "*", operations=["create", "update"])
    """
    file_path = Path(file_path)
    syncpriority_path = file_path.parent / f"{file_path.name}.syncpriority.yaml"
    
    # Convert inputs to proper types
    if isinstance(users, str):
        users = [users]
    if isinstance(priority, str):
        priority = SyncPriority(priority)
    if operations is None:
        operations = [SyncOperation.CREATE, SyncOperation.UPDATE, SyncOperation.DELETE, SyncOperation.MOVE]
    else:
        operations = [SyncOperation(op) if isinstance(op, str) else op for op in operations]
    
    # Load existing config or create new one
    config = load_sync_priority(file_path) or SyncPriorityConfig(rules=[])
    
    # Add or update rule for these users
    rule = SyncPriorityRule(
        users=users,
        priority=priority,
        operations=operations
    )
    
    # Remove any existing rules for these users and add new one
    config.rules = [r for r in config.rules if set(r.users) != set(users)]
    config.rules.append(rule)
    
    # Save config
    try:
        save_sync_priority(file_path, config)
        return True
    except Exception:
        return False


def get_sync_priority(file_path: Union[str, Path], user: str) -> SyncPriority:
    """
    Get sync priority for a specific user and file.
    
    Args:
        file_path: Path to file or folder
        user: User email to check
        
    Returns:
        SyncPriority level for this user
    """
    config = load_sync_priority(file_path)
    if not config:
        return SyncPriority.NORMAL
    
    for rule in config.rules:
        if user in rule.users or "*" in rule.users:
            return rule.priority
    
    return SyncPriority.NORMAL


def remove_sync_priority(file_path: Union[str, Path], users: Optional[Union[str, List[str]]] = None) -> bool:
    """
    Remove sync priority rules for specific users or entire file.
    
    Args:
        file_path: Path to file or folder
        users: User email(s) to remove, or None to remove entire config
    """
    file_path = Path(file_path)
    syncpriority_path = file_path.parent / f"{file_path.name}.syncpriority.yaml"
    
    if users is None:
        # Remove entire syncpriority file
        try:
            if syncpriority_path.exists():
                syncpriority_path.unlink()
            return True
        except Exception:
            return False
    
    # Remove specific users
    if isinstance(users, str):
        users = [users]
    
    config = load_sync_priority(file_path)
    if not config:
        return True
    
    # Remove specific users from rules
    new_rules = []
    for rule in config.rules:
        remaining_users = [u for u in rule.users if u not in users]
        if remaining_users:
            # Create new rule with remaining users
            new_rule = SyncPriorityRule(
                users=remaining_users,
                priority=rule.priority,
                operations=rule.operations
            )
            new_rules.append(new_rule)
    config.rules = new_rules
    
    try:
        if config.rules:
            save_sync_priority(file_path, config)
        else:
            # No rules left, remove file
            if syncpriority_path.exists():
                syncpriority_path.unlink()
        return True
    except Exception:
        return False


def list_sync_priorities(file_path: Union[str, Path]) -> List[SyncPriorityRule]:
    """
    List all sync priority rules for a file or folder.
    
    Args:
        file_path: Path to file or folder
        
    Returns:
        List of sync priority rules
    """
    config = load_sync_priority(file_path)
    return config.rules if config else []


def load_sync_priority(file_path: Union[str, Path]) -> Optional[SyncPriorityConfig]:
    """Load syncpriority config for a file/folder."""
    file_path = Path(file_path)
    syncpriority_path = file_path.parent / f"{file_path.name}.syncpriority.yaml"
    
    if not syncpriority_path.exists():
        return None
    
    try:
        with open(syncpriority_path, 'r') as f:
            data = yaml.safe_load(f)
        return SyncPriorityConfig(**data)
    except Exception:
        return None


def save_sync_priority(file_path: Union[str, Path], config: SyncPriorityConfig) -> None:
    """Save syncpriority config for a file/folder."""
    file_path = Path(file_path)
    syncpriority_path = file_path.parent / f"{file_path.name}.syncpriority.yaml"
    
    # Ensure parent directory exists
    syncpriority_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict for YAML serialization
    data = config.model_dump(mode='json')
    
    with open(syncpriority_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)