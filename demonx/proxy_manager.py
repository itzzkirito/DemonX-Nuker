"""
Proxy manager with rotation and health checking
"""

import time
import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger('DemonX')

# Try to import Rust proxy manager
# CRITICAL: Only use RustProxyManager when Rust is ACTUALLY available (RUST_AVAILABLE = True)
# When RUST_AVAILABLE is False, RustProxyManager uses Python fallback,
# creating circular dependency: ProxyManager -> RustProxyManager -> ProxyManager (recursion!)
# Solution: Never use RustProxyManager when Rust isn't available - use Python directly
USE_RUST_PROXY_MANAGER = False
USE_RUST_IF_AVAILABLE = False  # Default to False - only set True if Rust is confirmed available
try:
    from demonx_rust_bridge import RustProxyManager, RUST_AVAILABLE
    USE_RUST_PROXY_MANAGER = True
    # CRITICAL: Only use if Rust is ACTUALLY available (not fallback mode)
    # When False, RustProxyManager would fall back to Python, causing recursion
    USE_RUST_IF_AVAILABLE = (RUST_AVAILABLE is True)  # Explicit True check, not just truthy
except ImportError:
    pass  # Already set to False above - safe default


class ProxyManager:
    """Proxy manager with rotation and health checking (uses Rust implementation if available)"""
    
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.proxy_file = proxy_file
        self._use_rust = False
        self.proxies: List[str] = []
        self.current_index = 0
        self.proxy_stats: Dict[str, Dict] = {}
        
        # CRITICAL FIX: Never use RustProxyManager when Rust isn't available
        # When RUST_AVAILABLE is False, RustProxyManager falls back to Python,
        # creating circular dependency: ProxyManager -> RustProxyManager -> ProxyManager
        # Solution: Only use RustProxyManager when Rust is ACTUALLY available (RUST_AVAILABLE = True)
        # Otherwise, use Python implementation directly to avoid recursion
        
        # Default to Python implementation (safest - prevents recursion)
        self._rust_manager = None
        
        # SAFETY CHECK: Only try Rust if module-level flag says it's safe
        # This prevents any possibility of recursion when Rust isn't available
        if not USE_RUST_IF_AVAILABLE:
            # Rust not available - use Python implementation directly (no RustProxyManager)
            self._use_rust = False
            self.load_proxies()
            return
        
        # Only reach here if USE_RUST_IF_AVAILABLE is True (Rust confirmed available)
        if USE_RUST_PROXY_MANAGER:
            # Final runtime check: verify RUST_AVAILABLE is actually True
            try:
                import sys
                rust_bridge = sys.modules.get('demonx_rust_bridge')
                if rust_bridge:
                    rust_available = getattr(rust_bridge, 'RUST_AVAILABLE', False)
                    if rust_available is True:
                        # Rust confirmed available - safe to use RustProxyManager
                        self._rust_manager = RustProxyManager(proxy_file)
                        self._use_rust = True
                        # Sync proxies list for compatibility
                        if hasattr(self._rust_manager, 'proxies'):
                            self.proxies = self._rust_manager.proxies
                        return  # Early return - Rust implementation active
            except Exception:
                # Any error means fall back to Python (safety first)
                pass
        
        # Fallback to Python implementation (Rust not available or error occurred)
        self._use_rust = False
        self._rust_manager = None
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from file"""
        if self._use_rust:
            # Rust manager loads automatically in __init__
            # Sync Python proxies list for compatibility
            try:
                if Path(self.proxy_file).exists():
                    with open(self.proxy_file, 'r', encoding='utf-8') as f:
                        self.proxies = [line.strip() for line in f if line.strip()]
                    logger.info(f"Loaded {len(self.proxies)} proxies (Rust backend)")
            except Exception as e:
                logger.error(f"Error syncing proxies: {e}")
        else:
            try:
                if Path(self.proxy_file).exists():
                    with open(self.proxy_file, 'r', encoding='utf-8') as f:
                        self.proxies = [line.strip() for line in f if line.strip()]
                    for proxy in self.proxies:
                        self.proxy_stats[proxy] = {
                            'success': 0,
                            'failed': 0,
                            'last_used': None
                        }
                    logger.info(f"Loaded {len(self.proxies)} proxies")
            except Exception as e:
                logger.error(f"Error loading proxies: {e}")
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                num = int(part)
                if not (0 <= num <= 255):
                    return False
            return True
        except (ValueError, AttributeError):
            return False
    
    def _is_valid_port(self, port: str) -> bool:
        """Validate port number"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False
    
    def parse_proxy(self, proxy_str: str) -> Optional[str]:
        """Parse proxy string to URL format with validation
        Supports: IP:PORT:USERNAME:PASSWORD or IP:PORT
        Returns: http://USERNAME:PASSWORD@IP:PORT or http://IP:PORT
        
        Security: Validates IP and port to prevent injection attacks
        """
        try:
            parts = proxy_str.split(':')
            if len(parts) == 4:
                # Format: IP:PORT:USERNAME:PASSWORD
                ip, port, username, password = parts
                
                # Validate IP format
                if not self._is_valid_ip(ip):
                    logger.warning(f"Invalid IP address in proxy: {ip}")
                    return None
                
                # Validate port
                if not self._is_valid_port(port):
                    logger.warning(f"Invalid port in proxy: {port}")
                    return None
                
                # Basic username/password validation (no special chars that could break URL)
                if not username or not password:
                    logger.warning(f"Empty username or password in proxy")
                    return None
                
                return f"http://{username}:{password}@{ip}:{port}"
            elif len(parts) == 2:
                # Format: IP:PORT (no auth)
                ip, port = parts
                
                # Validate IP format
                if not self._is_valid_ip(ip):
                    logger.warning(f"Invalid IP address in proxy: {ip}")
                    return None
                
                # Validate port
                if not self._is_valid_port(port):
                    logger.warning(f"Invalid port in proxy: {port}")
                    return None
                
                return f"http://{ip}:{port}"
            else:
                logger.warning(f"Invalid proxy format (expected IP:PORT or IP:PORT:USER:PASS): {proxy_str}")
                return None
        except Exception as e:
            logger.error(f"Error parsing proxy {proxy_str}: {e}")
            return None
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation"""
        if self._use_rust:
            return self._rust_manager.get_next_proxy()
        
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        self.proxy_stats[proxy]['last_used'] = time.time()
        return self.parse_proxy(proxy)
    
    def get_current_proxy(self) -> Optional[str]:
        """Get current proxy"""
        if self._use_rust:
            return self._rust_manager.get_current_proxy()
        
        if not self.proxies:
            return None
        return self.parse_proxy(self.proxies[self.current_index])
    
    def mark_success(self, proxy_str: str):
        """Mark proxy as successful"""
        if self._use_rust:
            self._rust_manager.mark_success(proxy_str)
        elif proxy_str in self.proxy_stats:
            self.proxy_stats[proxy_str]['success'] += 1
    
    def mark_failed(self, proxy_str: str):
        """Mark proxy as failed"""
        if self._use_rust:
            self._rust_manager.mark_failed(proxy_str)
        elif proxy_str in self.proxy_stats:
            self.proxy_stats[proxy_str]['failed'] += 1
    
    async def check_proxy_health(self, proxy_url: str) -> Dict[str, Any]:
        """Check proxy health by making a test request
        
        Args:
            proxy_url: Proxy URL to check
            
        Returns:
            Dictionary with health status, response_time, and is_alive
        """
        if not self.enable_health_check:
            return {'is_alive': True, 'response_time': 0.0, 'status': 'skipped'}
        
        start_time = time.time()
        try:
            timeout = aiohttp.ClientTimeout(total=self.health_check_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.health_check_url,
                    proxy=proxy_url,
                    allow_redirects=False
                ) as response:
                    response_time = time.time() - start_time
                    is_alive = response.status in [200, 301, 302, 307, 308]
                    
                    # Update proxy stats
                    if proxy_url in self.proxy_stats:
                        self.proxy_stats[proxy_url]['last_health_check'] = time.time()
                        self.proxy_stats[proxy_url]['response_time'] = response_time
                        self.proxy_stats[proxy_url]['is_alive'] = is_alive
                    
                    return {
                        'is_alive': is_alive,
                        'response_time': response_time,
                        'status': 'healthy' if is_alive else 'unhealthy',
                        'status_code': response.status
                    }
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            if proxy_url in self.proxy_stats:
                self.proxy_stats[proxy_url]['is_alive'] = False
            return {
                'is_alive': False,
                'response_time': response_time,
                'status': 'timeout'
            }
        except Exception as e:
            response_time = time.time() - start_time
            logger.warning(f"Proxy health check failed for {proxy_url}: {e}")
            if proxy_url in self.proxy_stats:
                self.proxy_stats[proxy_url]['is_alive'] = False
            return {
                'is_alive': False,
                'response_time': response_time,
                'status': 'error',
                'error': str(e)
            }
    
    async def check_all_proxies_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all proxies
        
        Returns:
            Dictionary mapping proxy URLs to their health status
        """
        if not self.proxies:
            return {}
        
        results = {}
        for proxy_str in self.proxies:
            proxy_url = self.parse_proxy(proxy_str)
            if proxy_url:
                # Check if we need to check this proxy (not checked recently)
                last_check = self.last_health_check.get(proxy_url, 0)
                if time.time() - last_check < self.health_check_interval:
                    # Use cached result
                    if proxy_url in self.proxy_stats:
                        results[proxy_url] = {
                            'is_alive': self.proxy_stats[proxy_url].get('is_alive', True),
                            'response_time': self.proxy_stats[proxy_url].get('response_time', 0.0),
                            'status': 'cached'
                        }
                    continue
                
                health = await self.check_proxy_health(proxy_url)
                results[proxy_url] = health
                self.last_health_check[proxy_url] = time.time()
        
        return results
    
    def get_healthy_proxies(self) -> List[str]:
        """Get list of healthy proxies based on health checks
        
        Returns:
            List of healthy proxy URLs
        """
        healthy = []
        for proxy_str in self.proxies:
            proxy_url = self.parse_proxy(proxy_str)
            if proxy_url and self.proxy_stats.get(proxy_str, {}).get('is_alive', True):
                healthy.append(proxy_url)
        return healthy
    
    def remove_dead_proxies(self, min_failures: int = 3) -> int:
        """Remove proxies that have failed too many times
        
        Args:
            min_failures: Minimum number of failures before removal
            
        Returns:
            Number of proxies removed
        """
        removed = 0
        dead_proxies = []
        
        for proxy_str, stats in self.proxy_stats.items():
            if stats.get('failed', 0) >= min_failures and not stats.get('is_alive', True):
                dead_proxies.append(proxy_str)
        
        for proxy_str in dead_proxies:
            if proxy_str in self.proxies:
                self.proxies.remove(proxy_str)
                del self.proxy_stats[proxy_str]
                removed += 1
                logger.info(f"Removed dead proxy: {proxy_str}")
        
        return removed

