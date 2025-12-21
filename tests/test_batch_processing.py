"""
Tests for batch processing functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from demonx_complete import DemonXComplete


@pytest.mark.asyncio
async def test_batch_process_empty_list(mock_guild, mock_bot):
    """Test batch processing with empty task list"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=True)
    nuker.bot = mock_bot
    
    results = await nuker._batch_process([], batch_size=10, delay=0.1, operation_name="test")
    assert results == []


@pytest.mark.asyncio
async def test_batch_process_success(mock_guild, mock_bot):
    """Test successful batch processing"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=True)
    nuker.bot = mock_bot
    
    # Create mock coroutines that succeed
    async def success_task():
        return "success"
    
    tasks = [success_task() for _ in range(5)]
    results = await nuker._batch_process(tasks, batch_size=2, delay=0.01, operation_name="test")
    
    assert len(results) == 5
    assert all(r == "success" for r in results)


@pytest.mark.asyncio
async def test_batch_process_with_errors(mock_guild, mock_bot):
    """Test batch processing with some errors"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=True)
    nuker.bot = mock_bot
    
    # Create mix of success and error tasks
    async def success_task():
        return "success"
    
    async def error_task():
        raise ValueError("Test error")
    
    tasks = [success_task() if i % 2 == 0 else error_task() for i in range(6)]
    results = await nuker._batch_process(tasks, batch_size=2, delay=0.01, operation_name="test")
    
    # Should have 3 successes (even indices)
    assert len(results) == 3
    assert all(r == "success" for r in results)


@pytest.mark.asyncio
async def test_batch_process_cancellation(mock_guild, mock_bot):
    """Test batch processing cancellation"""
    nuker = DemonXComplete("test_token", use_proxy=False, dry_run=True)
    nuker.bot = mock_bot
    
    async def slow_task():
        await asyncio.sleep(0.1)
        return "done"
    
    tasks = [slow_task() for _ in range(10)]
    
    # Cancel after first batch
    async def cancel_after_delay():
        await asyncio.sleep(0.05)
        nuker.cancel_operations()
    
    # Run cancellation and batch process concurrently
    await asyncio.gather(
        cancel_after_delay(),
        nuker._batch_process(tasks, batch_size=5, delay=0.01, operation_name="test"),
        return_exceptions=True
    )
    
    # Should have cancelled
    assert nuker._cancellation_token.is_set()

