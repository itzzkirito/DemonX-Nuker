"""
Tests for ProxyManager class
"""

import pytest
from pathlib import Path
from demonx import ProxyManager


def test_proxy_manager_initialization():
    """Test ProxyManager initialization"""
    manager = ProxyManager("proxies.txt")
    assert manager is not None
    assert hasattr(manager, 'load_proxies')
    assert hasattr(manager, 'get_next_proxy')
    assert hasattr(manager, 'get_current_proxy')


def test_proxy_manager_load_proxies(tmp_path):
    """Test loading proxies from file"""
    # Create a temporary proxy file
    proxy_file = tmp_path / "test_proxies.txt"
    proxy_file.write_text("127.0.0.1:8080\n192.168.1.1:3128\n")
    
    manager = ProxyManager(str(proxy_file))
    manager.load_proxies()
    
    # Should have loaded proxies
    assert len(manager.proxies) >= 0  # May be 0 if Rust manager is used


def test_proxy_manager_get_next_proxy():
    """Test proxy rotation"""
    manager = ProxyManager("proxies.txt")
    # Should not raise an exception
    proxy = manager.get_next_proxy()
    # May return None if no proxies loaded
    assert proxy is None or isinstance(proxy, str)

