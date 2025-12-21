"""
Rate limiter for Discord API requests
"""

import time
import logging
import asyncio
from typing import Dict, Optional

logger = logging.getLogger('DemonX')

# Try to import Rust rate limiter
try:
    from demonx_rust_bridge import RustRateLimiter
    USE_RUST_RATE_LIMITER = True
except ImportError:
    USE_RUST_RATE_LIMITER = False


class RateLimiter:
    """Advanced rate limiter (uses Rust implementation if available)"""
    
    def __init__(self):
        if USE_RUST_RATE_LIMITER:
            self._rust_limiter = RustRateLimiter()
            self._use_rust = True
        else:
            self._use_rust = False
            self.retry_after: Dict[str, float] = {}
            self.global_rate_limit: Optional[float] = None
    
    async def wait_for_rate_limit(self, endpoint: str = "global"):
        """Wait if rate limited with automatic cleanup of expired entries"""
        if self._use_rust:
            wait_time = self._rust_limiter.wait_time(endpoint)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        else:
            current_time = time.time()
            
            # Clean up expired entries before checking
            expired = [k for k, v in self.retry_after.items() if v < current_time]
            for key in expired:
                del self.retry_after[key]
            
            # Limit dictionary size to prevent memory accumulation
            if len(self.retry_after) > 1000:
                # Remove oldest entries (keep most recent 500)
                sorted_items = sorted(self.retry_after.items(), key=lambda x: x[1])
                self.retry_after = dict(sorted_items[-500:])
            
            if endpoint in self.retry_after:
                wait_time = self.retry_after[endpoint] - current_time
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    del self.retry_after[endpoint]
            
            if self.global_rate_limit:
                wait_time = self.global_rate_limit - current_time
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    self.global_rate_limit = None
                elif wait_time <= 0:
                    # Clean up expired global rate limit
                    self.global_rate_limit = None
    
    def handle_rate_limit(self, endpoint: str, retry_after: float, is_global: bool = False):
        """Handle rate limit with cleanup of expired entries"""
        if self._use_rust:
            self._rust_limiter.handle_rate_limit(endpoint, retry_after, is_global)
        else:
            # Clean up expired entries periodically to prevent memory accumulation
            current_time = time.time()
            expired = [k for k, v in self.retry_after.items() if v < current_time]
            for key in expired:
                del self.retry_after[key]
            
            # Set new rate limit
            if is_global:
                self.global_rate_limit = current_time + retry_after
            else:
                self.retry_after[endpoint] = current_time + retry_after

