"""
Tests for RateLimiter class
"""

import pytest
import asyncio
from demonx import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_initialization():
    """Test RateLimiter initialization"""
    limiter = RateLimiter()
    assert limiter is not None
    assert hasattr(limiter, 'wait_if_needed')
    assert hasattr(limiter, 'handle_rate_limit')


@pytest.mark.asyncio
async def test_rate_limiter_wait_if_needed():
    """Test wait_if_needed method"""
    limiter = RateLimiter()
    # Should not raise an exception
    await limiter.wait_if_needed("test_endpoint")


@pytest.mark.asyncio
async def test_rate_limiter_handle_rate_limit():
    """Test handle_rate_limit method"""
    limiter = RateLimiter()
    # Should return a delay (float)
    delay = limiter.handle_rate_limit("test_endpoint", 1.0)
    assert isinstance(delay, (int, float))
    assert delay >= 0

