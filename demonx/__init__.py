"""
DemonX Nuker Package
Professional Discord server management tool
"""

from .config import Config, OperationType, OperationRecord
from .rate_limiter import RateLimiter
from .proxy_manager import ProxyManager
from .history import OperationHistory
from .presets import PresetManager
from .utils import get_user_friendly_error, load_config, print_banner, ERROR_MESSAGES

# Optional: Import operation queue if available
try:
    from .operation_queue import OperationQueue, QueuePriority
    __all__ = [
        'Config',
        'OperationType',
        'OperationRecord',
        'RateLimiter',
        'ProxyManager',
        'OperationHistory',
        'PresetManager',
        'OperationQueue',
        'QueuePriority',
        'get_user_friendly_error',
        'load_config',
        'print_banner',
        'ERROR_MESSAGES',
    ]
except ImportError:
    # Operation queue not available
    __all__ = [
        'Config',
        'OperationType',
        'OperationRecord',
        'RateLimiter',
        'ProxyManager',
        'OperationHistory',
        'PresetManager',
        'get_user_friendly_error',
        'load_config',
        'print_banner',
        'ERROR_MESSAGES',
    ]

# Note: DemonXComplete is in demonx_complete.py, not in this package
# Import it directly: from demonx_complete import DemonXComplete

__version__ = '2.3'

