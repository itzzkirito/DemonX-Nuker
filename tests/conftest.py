"""
Pytest configuration and fixtures for DemonX tests
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from typing import Generator

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_guild() -> Mock:
    """Create a mock Discord guild for testing"""
    guild = Mock()
    guild.id = 123456789
    guild.name = "Test Guild"
    guild.member_count = 100
    guild.members = []
    guild.channels = []
    guild.roles = []
    guild.emojis = []
    guild.me = Mock()
    guild.me.top_role = Mock()
    guild.me.top_role.position = 100
    return guild


@pytest.fixture
def mock_bot() -> Mock:
    """Create a mock Discord bot for testing"""
    bot = Mock()
    bot.user = Mock()
    bot.user.id = 987654321
    bot.guilds = []
    bot.http = Mock()
    bot.http._HTTPClient__session = Mock()
    return bot


@pytest.fixture
def mock_rate_limiter() -> Mock:
    """Create a mock rate limiter"""
    limiter = Mock()
    limiter.wait_if_needed = Mock(return_value=None)
    limiter.handle_rate_limit = Mock(return_value=0.0)
    return limiter


@pytest.fixture
def mock_proxy_manager() -> Mock:
    """Create a mock proxy manager"""
    manager = Mock()
    manager.get_next_proxy = Mock(return_value=None)
    manager.get_current_proxy = Mock(return_value=None)
    manager.load_proxies = Mock()
    return manager


@pytest.fixture
def mock_operation_history() -> Mock:
    """Create a mock operation history"""
    history = Mock()
    history.add_operation = Mock()
    history.get_statistics = Mock(return_value={})
    history.save_history = Mock()
    return history


@pytest.fixture
def mock_preset_manager() -> Mock:
    """Create a mock preset manager"""
    manager = Mock()
    manager.list_presets = Mock(return_value=[])
    manager.get_preset = Mock(return_value=[])
    manager.save_preset = Mock()
    return manager

