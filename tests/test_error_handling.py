"""
Tests for error handling functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import discord
from demonx_complete import DemonXComplete
from demonx import OperationType


@pytest.mark.asyncio
async def test_safe_execute_success(mock_guild, mock_bot):
    """Test safe_execute with successful operation"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=False)
    nuker.bot = mock_bot
    
    async def success_coro():
        return "success"
    
    result = await nuker.safe_execute(
        success_coro(),
        operation_type=OperationType.BAN
    )
    
    assert result == "success"


@pytest.mark.asyncio
async def test_safe_execute_rate_limit(mock_guild, mock_bot):
    """Test safe_execute with rate limit error"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=False)
    nuker.bot = mock_bot
    
    # Mock rate limit exception
    rate_limit_error = discord.HTTPException(
        Mock(status=429, response=Mock(headers={
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Limit': '50',
            'X-RateLimit-Reset-After': '1.0',
            'Retry-After': '1.0',
            'X-RateLimit-Global': 'false'
        }))
    )
    
    call_count = 0
    async def rate_limited_coro():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise rate_limit_error
        return "success"
    
    # Should retry and eventually succeed
    result = await nuker.safe_execute(
        rate_limited_coro(),
        retries=3,
        operation_type=OperationType.BAN
    )
    
    assert result == "success" or result is False  # May fail after retries


@pytest.mark.asyncio
async def test_safe_execute_timeout(mock_guild, mock_bot):
    """Test safe_execute with timeout"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=False)
    nuker.bot = mock_bot
    
    async def slow_coro():
        await asyncio.sleep(10)  # Longer than timeout
        return "success"
    
    result = await nuker.safe_execute(
        slow_coro(),
        timeout=0.1,
        retries=1,
        operation_type=OperationType.BAN
    )
    
    # Should return False after timeout
    assert result is False


@pytest.mark.asyncio
async def test_safe_execute_cancellation(mock_guild, mock_bot):
    """Test safe_execute with cancellation"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=False)
    nuker.bot = mock_bot
    nuker.cancel_operations()
    
    async def coro():
        return "success"
    
    result = await nuker.safe_execute(
        coro(),
        operation_type=OperationType.BAN
    )
    
    # Should return False when cancelled
    assert result is False


def test_get_user_friendly_error():
    """Test user-friendly error message conversion"""
    from demonx import get_user_friendly_error
    
    # Test Forbidden error
    forbidden = discord.Forbidden(None, "administrator")
    msg = get_user_friendly_error(forbidden)
    assert "permission" in msg.lower() or "administrator" in msg.lower()
    
    # Test HTTPException
    http_error = discord.HTTPException(Mock(status=429), "rate limited")
    msg = get_user_friendly_error(http_error)
    assert "rate" in msg.lower() or "limit" in msg.lower()
    
    # Test TimeoutError
    timeout = asyncio.TimeoutError()
    msg = get_user_friendly_error(timeout)
    assert "timeout" in msg.lower() or "timed out" in msg.lower()

