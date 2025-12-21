"""
Python bridge for Rust rate limiter and proxy manager
"""
import os
import sys
import time
from typing import Optional, List, Dict

try:
    import demonx_rust  # type: ignore[import-untyped]
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    print("[!] Rust components not available. Using Python fallback.")
    print("[*] Install Rust components with: python build_rust.py")

class RustRateLimiter:
    """Python wrapper for Rust rate limiter"""
    
    def __init__(self):
        if RUST_AVAILABLE:
            self._limiter = demonx_rust.PyRateLimiter()
            self._fallback = None
        else:
            self._limiter = None
            # Simple Python fallback implementation (avoid circular dependency)
            self._retry_after: Dict[str, float] = {}
            self._global_rate_limit: Optional[float] = None
            self._fallback = True  # Flag to indicate we're using fallback
    
    def can_request(self, endpoint: str) -> bool:
        """Check if we can make a request"""
        if self._limiter:
            return self._limiter.can_request(endpoint)
        return True  # Fallback always allows
    
    def wait_time(self, endpoint: str) -> float:
        """Get wait time in seconds"""
        if self._limiter:
            return self._limiter.wait_time(endpoint)
        # Simple fallback implementation
        current_time = time.time()
        if endpoint in self._retry_after:
            wait_time = self._retry_after[endpoint] - current_time
            if wait_time > 0:
                return wait_time
            else:
                del self._retry_after[endpoint]
        if self._global_rate_limit:
            wait_time = self._global_rate_limit - current_time
            if wait_time > 0:
                return wait_time
            else:
                self._global_rate_limit = None
        return 0.0
    
    def handle_rate_limit(self, endpoint: str, retry_after: float, is_global: bool = False):
        """Handle rate limit"""
        if self._limiter:
            self._limiter.handle_rate_limit(endpoint, retry_after, is_global)
        else:
            # Simple fallback implementation
            current_time = time.time()
            if is_global:
                self._global_rate_limit = current_time + retry_after
            else:
                self._retry_after[endpoint] = current_time + retry_after
    
    def decrement(self, endpoint: str):
        """Decrement remaining count"""
        if self._limiter:
            self._limiter.decrement(endpoint)
    
    def get_stats(self) -> dict:
        """Get statistics"""
        if self._limiter:
            return dict(self._limiter.get_stats())
        return {}

class RustProxyManager:
    """Python wrapper for Rust proxy manager"""
    
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.proxy_file = proxy_file
        if RUST_AVAILABLE:
            self._manager = demonx_rust.PyProxyManager()
            self._load_proxies()
            self._fallback = None
        else:
            self._manager = None
            # Simple Python fallback implementation (avoid circular dependency)
            self.proxies: List[str] = []
            self.current_index = 0
            self.proxy_stats: Dict[str, Dict] = {}
            self._fallback = True  # Flag to indicate we're using fallback
            self._load_proxies_fallback()
    
    def _load_proxies(self):
        """Load proxies from file"""
        if self._manager and os.path.exists(self.proxy_file):
            try:
                count = self._manager.load_from_file(self.proxy_file)
                print(f"[+] Loaded {count} proxies (Rust)")
            except Exception as e:
                print(f"[!] Failed to load proxies: {e}")
    
    def _load_proxies_fallback(self):
        """Load proxies from file (fallback implementation)"""
        if os.path.exists(self.proxy_file):
            try:
                with open(self.proxy_file, 'r', encoding='utf-8') as f:
                    self.proxies = [line.strip() for line in f if line.strip()]
                for proxy in self.proxies:
                    self.proxy_stats[proxy] = {
                        'success': 0,
                        'failed': 0,
                        'last_used': None
                    }
            except Exception as e:
                print(f"[!] Failed to load proxies: {e}")
    
    def _parse_proxy(self, proxy_str: str) -> Optional[str]:
        """Parse proxy string to URL format (fallback implementation)"""
        try:
            parts = proxy_str.split(':')
            if len(parts) == 4:
                # Format: IP:PORT:USERNAME:PASSWORD
                ip, port, username, password = parts
                return f"http://{username}:{password}@{ip}:{port}"
            elif len(parts) == 2:
                # Format: IP:PORT (no auth)
                ip, port = parts
                return f"http://{ip}:{port}"
            return None
        except Exception:
            return None
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy URL"""
        if self._manager:
            return self._manager.get_next_proxy()
        # Fallback implementation
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['last_used'] = time.time()
        return self._parse_proxy(proxy)
    
    def get_current_proxy(self) -> Optional[str]:
        """Get current proxy URL"""
        if self._manager:
            return self._manager.get_current_proxy()
        # Fallback implementation
        if not self.proxies:
            return None
        return self._parse_proxy(self.proxies[self.current_index])
    
    def mark_success(self, proxy_url: str):
        """Mark proxy as successful"""
        if self._manager:
            self._manager.mark_success(proxy_url)
        else:
            # Fallback implementation - find proxy string from URL
            for proxy_str, stats in self.proxy_stats.items():
                if self._parse_proxy(proxy_str) == proxy_url:
                    stats['success'] += 1
                    break
    
    def mark_failed(self, proxy_url: str):
        """Mark proxy as failed"""
        if self._manager:
            self._manager.mark_failed(proxy_url)
        else:
            # Fallback implementation - find proxy string from URL
            for proxy_str, stats in self.proxy_stats.items():
                if self._parse_proxy(proxy_str) == proxy_url:
                    stats['failed'] += 1
                    break
    
    def count(self) -> int:
        """Get proxy count"""
        if self._manager:
            return self._manager.count()
        return len(self.proxies) if hasattr(self, 'proxies') else 0
    
    def get_stats(self) -> dict:
        """Get statistics"""
        if self._manager:
            return dict(self._manager.get_stats())
        return {}

