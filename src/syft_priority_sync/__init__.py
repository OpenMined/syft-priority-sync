"""
Syft Priority Sync - Instant file synchronization for SyftBox

Sync priority files immediately via RPC for real-time collaboration.
"""

__version__ = "0.1.1"

# Auto-install as SyftBox app if SyftBox is available
try:
    import importlib
    _auto_mod = importlib.import_module('.auto_install', package=__name__)
    _auto_mod.auto_install()
    del importlib, _auto_mod
except Exception:
    pass

# Import core API functions - use importlib to avoid namespace pollution
import importlib as _importlib
_api_mod = _importlib.import_module('.api', package=__name__)

set_sync_priority = _api_mod.set_sync_priority
get_sync_priority = _api_mod.get_sync_priority
remove_sync_priority = _api_mod.remove_sync_priority
list_sync_priorities = _api_mod.list_sync_priorities

del _importlib, _api_mod

__all__ = [
    "set_sync_priority",
    "get_sync_priority",
    "remove_sync_priority", 
    "list_sync_priorities",
]

# Clean up namespace completely
import sys as _sys
_this_module = _sys.modules[__name__]
_all_names = list(globals().keys())
for _name in _all_names:
    if _name not in __all__ and not _name.startswith('_') and _name not in ['__doc__', '__file__', '__name__', '__package__', '__path__', '__spec__', '__version__']:
        try:
            delattr(_this_module, _name)
        except (AttributeError, ValueError):
            pass
del _sys, _this_module, _all_names, _name
