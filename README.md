# Syft Priority Sync

Instant file synchronization for SyftBox - sync priority files immediately via RPC for real-time collaboration

## What is it?

Syft Priority Sync enables instant file synchronization in [SyftBox](https://www.syftbox.net/) networks. Mark files or folders for priority sync and they'll be sent immediately to collaborators via RPC, bypassing normal sync delays.

Perfect for real-time collaborative editing, live data sharing, and instant updates during research sessions.

## Quick Start

```bash
pip install syft-priority-sync
```

```python
import syft_priority_sync as sps

# Mark a file for instant sync to specific users
sps.set_sync_priority("important.txt", ["alice@university.edu", "bob@lab.org"])

# Mark a folder for instant sync to everyone
sps.set_sync_priority("shared_data/", "*")

# Check sync priority for a user
priority = sps.get_sync_priority("important.txt", "alice@university.edu")
print(f"Sync priority: {priority}")  # instant or normal
```

## How It Works

### 1. **syncpriority.yaml Files**
Next to any file or folder, create a `.syncpriority.yaml` file:

```yaml
# important.txt.syncpriority.yaml
rules:
  - users: ["alice@university.edu", "bob@lab.org"]
    priority: "instant"
    operations: ["create", "update", "delete"]
  - users: ["*"]
    priority: "normal"
    operations: ["create"]
```

### 2. **Automatic Detection**
The SyftBox app watches for file changes and automatically sends instant syncs based on your priority rules.

### 3. **Permission Validation**
Uses existing `syft.pub.yaml` permissions to validate sync requests - no unauthorized file access.

## Use Cases

**📊 Real-time Research Data**
```python
# Mark experiment results for instant sync
sps.set_sync_priority("experiments/results/", ["collaborator@university.edu"])
# Any new results are instantly available to your collaborator
```

**📝 Live Document Collaboration**
```python
# Enable instant sync for a shared document
sps.set_sync_priority("paper.md", ["coauthor1@university.edu", "coauthor2@lab.org"])
# Changes appear instantly for all authors
```

**🤖 Model Sharing**
```python
# Instantly sync trained models
sps.set_sync_priority("models/", "*", operations=["create", "update"])
# New models are immediately available to the entire network
```

## API Reference

### Core Functions

**`set_sync_priority(file_path, users, priority="instant", operations=None)`**
Set sync priority for a file or folder

**`get_sync_priority(file_path, user)`** � `"instant"` or `"normal"`  
Get sync priority for a specific user

**`remove_sync_priority(file_path, users=None)`**
Remove sync priority rules

**`list_sync_priorities(file_path)`** � `List[SyncPriorityRule]`
List all sync priority rules for a file

### Operations
- `"create"` - New files
- `"update"` - File modifications  
- `"delete"` - File deletions
- `"move"` - File moves/renames

### Users
- Specific emails: `["alice@university.edu", "bob@lab.org"]`
- Everyone: `"*"`
- Combine: `["alice@university.edu", "*"]`

## Security

- **Permission-based**: Uses existing `syft.pub.yaml` files for access control
- **Validated syncs**: Server validates sender permissions before applying changes
- **No unauthorized access**: Can't sync files without proper write/admin permissions

## Installation as SyftBox App

The package automatically installs as a SyftBox app when imported. The app:
- Watches your datasite for file changes
- Sends instant syncs when priority files change
- Receives and validates incoming sync requests
- Respects all existing SyftBox permissions

## Architecture

```
File Change � Priority Check � RPC Send � Permission Validation � Apply Change
     �              �             �              �                    �
File Watcher � .syncpriority � syft-rpc � syft.pub.yaml � Update File
```

Perfect for coordinating real-time collaboration in privacy-preserving AI research and development.

## License

Apache 2.0