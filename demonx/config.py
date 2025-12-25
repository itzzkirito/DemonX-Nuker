"""
Configuration constants and data structures
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional


class Config:
    """Configuration constants to replace magic numbers throughout the codebase"""
    # History Configuration
    MAX_HISTORY_RECORDS = 1000
    HISTORY_BATCH_SIZE = 50
    MAX_HISTORY_FILE_SIZE_MB = 10  # Maximum history file size before rotation
    
    # Batch Processing Defaults - OPTIMIZED FOR MAXIMUM SPEED
    DEFAULT_BATCH_SIZE = 50
    DEFAULT_DELAY = 0.0  # No delay - maximum speed
    BATCH_SIZE_BAN_KICK = 50  # Increased from 30 - maximum parallel bans/kicks
    BATCH_SIZE_CHANNELS = 30  # Increased from 15 - faster channel operations
    BATCH_SIZE_ROLES = 10  # Increased from 5 - faster role operations
    BATCH_SIZE_MASS_PING = 50  # Increased from 20 - maximum message throughput
    BATCH_SIZE_WEBHOOK = 30  # Increased from 10 - faster webhook creation
    BATCH_SIZE_NICKNAME = 50  # Increased from 25 - faster nickname changes
    BATCH_SIZE_ROLE_OPS = 10  # Increased from 5 - faster role operations
    
    # Delays - MINIMIZED FOR MAXIMUM SPEED
    DELAY_MINIMAL = 0.0  # No delay
    DELAY_SHORT = 0.0  # No delay
    DELAY_DEFAULT = 0.0  # No delay - maximum speed
    DELAY_MEDIUM = 0.01  # Minimal delay only when absolutely necessary
    DELAY_LONG = 0.02  # Minimal delay only when absolutely necessary
    DELAY_ROLE_OPS = 0.1  # Reduced from 2.0 - minimal delay for role operations
    
    # Retry Configuration - OPTIMIZED FOR MAXIMUM SPEED
    MAX_RETRIES = 3
    MAX_BACKOFF = 2.0  # Reduced from 5.0 - faster recovery
    RETRY_STRATEGY = "linear"  # Changed to linear for faster retries
    RETRY_BASE_DELAY = 0.5  # Reduced from 1.0 - faster retry attempts
    
    # Preset Configuration - OPTIMIZED FOR MAXIMUM SPEED
    PRESET_DELAY = 0.0  # No delay between preset operations
    
    # Operation Timeout
    DEFAULT_OPERATION_TIMEOUT = 30.0  # 30 seconds default timeout
    TIMEOUT_BAN_KICK = 60.0  # Longer timeout for member operations
    TIMEOUT_CHANNEL_OPS = 45.0  # Channel operations timeout
    TIMEOUT_ROLE_OPS = 45.0  # Role operations timeout
    TIMEOUT_MESSAGE_OPS = 20.0  # Message operations timeout
    TIMEOUT_WEBHOOK_OPS = 30.0  # Webhook operations timeout
    
    # Large Guild Threshold
    LARGE_GUILD_THRESHOLD = 5000  # Process large guilds in chunks
    LARGE_GUILD_CHUNK_SIZE = 1000  # Members per chunk for large guilds
    
    # Logging Configuration
    LOG_FILE = "demonx.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Connection Pool Configuration - OPTIMIZED FOR MAXIMUM SPEED
    CONNECTOR_LIMIT = 200  # Increased from 100 - more concurrent connections
    CONNECTOR_LIMIT_PER_HOST = 100  # Increased from 30 - more per-host connections
    CONNECTOR_TTL_DNS_CACHE = 600  # Increased from 300 - longer DNS cache (10 minutes)
    CONNECTOR_FORCE_CLOSE = False  # Reuse connections for better performance
    CONNECTOR_ENABLE_CLEANUP_CLOSED = True  # Clean up closed connections


class OperationType(Enum):
    """Operation types for history tracking"""
    BAN = "ban"
    KICK = "kick"
    PRUNE = "prune"
    NICKNAME = "nickname"
    GRANT_ADMIN = "grant_admin"
    UNBAN = "unban"
    ASSIGN_ROLE = "assign_role"
    REMOVE_ROLE = "remove_role"
    DELETE_CHANNEL = "delete_channel"
    CREATE_CHANNEL = "create_channel"
    RENAME_CHANNEL = "rename_channel"
    SHUFFLE_CHANNEL = "shuffle_channel"
    MASS_PING = "mass_ping"
    CREATE_CATEGORY = "create_category"
    DELETE_CATEGORY = "delete_category"
    CREATE_ROLE = "create_role"
    DELETE_ROLE = "delete_role"
    RENAME_ROLE = "rename_role"
    RENAME_GUILD = "rename_guild"
    DELETE_EMOJI = "delete_emoji"
    WEBHOOK_SPAM = "webhook_spam"
    REACT_MESSAGE = "react_message"


@dataclass
class OperationRecord:
    """Record of an operation"""
    operation_type: str
    timestamp: str
    success: bool
    details: Dict[str, Any]
    error: Optional[str] = None

