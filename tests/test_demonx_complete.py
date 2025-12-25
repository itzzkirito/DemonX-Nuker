"""
Tests for DemonXComplete class core functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import discord
from demonx_complete import DemonXComplete
from demonx import OperationType, Config


@pytest.mark.asyncio
async def test_demonx_complete_initialization(mock_bot):
    """Test DemonXComplete initialization"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=True)
    
    assert nuker._token == "test_token"
    assert nuker.use_proxy is False
    assert nuker.dry_run is True
    assert nuker.verbose is True
    assert nuker.rate_limiter is not None
    assert nuker.operation_history is not None
    assert nuker.preset_manager is not None


def test_validate_token_static_method():
    """Test static validate_token method"""
    # Valid token
    valid = "MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIuQWJjLkRlZg"
    assert DemonXComplete.validate_token(valid) == valid
    
    # Invalid tokens
    with pytest.raises(ValueError):
        DemonXComplete.validate_token("")
    
    with pytest.raises(ValueError):
        DemonXComplete.validate_token("short")


def test_validate_guild_id_static_method():
    """Test static validate_guild_id method"""
    # Valid guild ID
    valid = "123456789012345678"
    assert DemonXComplete.validate_guild_id(valid) == 123456789012345678
    
    # Invalid guild IDs
    with pytest.raises(ValueError):
        DemonXComplete.validate_guild_id("-1")
    
    with pytest.raises(ValueError):
        DemonXComplete.validate_guild_id("123")


def test_validate_count_static_method():
    """Test static validate_count method"""
    # Valid counts
    assert DemonXComplete.validate_count(10) == 10
    assert DemonXComplete.validate_count(1, min_value=1) == 1
    
    # Invalid counts
    with pytest.raises(ValueError):
        DemonXComplete.validate_count(0)
    
    with pytest.raises(ValueError):
        DemonXComplete.validate_count(2000, max_value=1000)


def test_validate_message_length_static_method():
    """Test static validate_message_length method"""
    # Valid messages
    assert DemonXComplete.validate_message_length("Hello") == "Hello"
    
    # Invalid messages
    with pytest.raises(ValueError):
        DemonXComplete.validate_message_length("x" * 2001)


@pytest.mark.asyncio
async def test_safe_execute_dry_run(mock_guild, mock_bot):
    """Test safe_execute in dry_run mode"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=True)
    nuker.bot = mock_bot
    
    async def coro():
        return "result"
    
    result = await nuker.safe_execute(
        coro(),
        operation_type=OperationType.BAN
    )
    
    # Should return True in dry_run mode
    assert result is True


@pytest.mark.asyncio
async def test_cancel_operations(mock_bot):
    """Test operation cancellation"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=True)
    nuker.bot = mock_bot
    
    assert not nuker._cancellation_token.is_set()
    
    nuker.cancel_operations()
    assert nuker._cancellation_token.is_set()
    
    nuker.reset_cancellation()
    assert not nuker._cancellation_token.is_set()


def test_increment_stat_thread_safe(mock_bot):
    """Test thread-safe stat increment"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=True)
    nuker.bot = mock_bot
    
    # Initial state
    assert nuker.stats.get('test_stat', 0) == 0
    
    # Increment
    nuker._increment_stat('test_stat', 5)
    assert nuker.stats['test_stat'] == 5
    
    # Increment again
    nuker._increment_stat('test_stat', 3)
    assert nuker.stats['test_stat'] == 8


def test_calculate_retry_delay(mock_bot):
    """Test retry delay calculation"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=True)
    nuker.bot = Mock()
    
    # Exponential strategy
    delay = nuker._calculate_retry_delay(0, "exponential")
    assert delay > 0
    assert delay <= Config.MAX_BACKOFF
    
    # Linear strategy
    delay = nuker._calculate_retry_delay(1, "linear")
    assert delay > 0
    
    # Fixed strategy
    delay = nuker._calculate_retry_delay(2, "fixed")
    assert delay == Config.RETRY_BASE_DELAY

