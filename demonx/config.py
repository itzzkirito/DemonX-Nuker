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
    
    # Batch Processing Defaults
    DEFAULT_BATCH_SIZE = 30
    DEFAULT_DELAY = 0.05
    BATCH_SIZE_BAN_KICK = 30
    BATCH_SIZE_CHANNELS = 15
    BATCH_SIZE_ROLES = 5  # Reduced from 10 - Discord limits role ops to ~5 per 10s
    BATCH_SIZE_MASS_PING = 20
    BATCH_SIZE_WEBHOOK = 10
    BATCH_SIZE_NICKNAME = 25
    BATCH_SIZE_ROLE_OPS = 5  # Reduced from 20 - match role deletion rate limits
    
    # Delays
    DELAY_MINIMAL = 0.01
    DELAY_SHORT = 0.02
    DELAY_DEFAULT = 0.05
    DELAY_MEDIUM = 0.1
    DELAY_LONG = 0.2
    DELAY_ROLE_OPS = 2.0  # 2 seconds between role operation batches to respect rate limits
    
    # Retry Configuration
    MAX_RETRIES = 3
    MAX_BACKOFF = 5.0
    RETRY_STRATEGY = "exponential"  # exponential, linear, fixed
    RETRY_BASE_DELAY = 1.0
    
    # Preset Configuration
    PRESET_DELAY = 0.1
    
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
    
    # Connection Pool Configuration
    CONNECTOR_LIMIT = 100  # Max connections
    CONNECTOR_LIMIT_PER_HOST = 30  # Per host
    CONNECTOR_TTL_DNS_CACHE = 300  # DNS cache TTL (5 minutes)
    CONNECTOR_FORCE_CLOSE = False  # Reuse connections
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

