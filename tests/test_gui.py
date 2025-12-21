"""
Tests for GUI functionality
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import queue
from demonx_gui import DemonXGUI
import discord


@pytest.fixture
def root():
    """Create a root window for testing"""
    root = tk.Tk()
    root.withdraw()  # Hide window during tests
    yield root
    root.destroy()


@pytest.fixture
def gui(root):
    """Create a GUI instance for testing"""
    return DemonXGUI(root)


def test_gui_initialization(gui):
    """Test GUI initialization"""
    assert gui.root is not None
    assert gui.nuker is None
    assert gui.bot_running is False
    assert gui.gui_queue is not None
    assert isinstance(gui.gui_queue, queue.Queue)


def test_gui_queue_creation(gui):
    """Test GUI queue is created"""
    assert hasattr(gui, 'gui_queue')
    assert isinstance(gui.gui_queue, queue.Queue)


def test_safe_gui_update(gui):
    """Test thread-safe GUI update"""
    # Test log update
    gui._safe_gui_update('log', message="Test message", color='#ffffff')
    assert not gui.gui_queue.empty()
    
    # Test messagebox update
    gui._safe_gui_update('messagebox_error', title="Error", message="Test error")
    assert gui.gui_queue.qsize() == 2


def test_check_connected_not_connected(gui):
    """Test check_connected when not connected"""
    gui.bot_running = False
    gui.guild = None
    
    result = gui.check_connected()
    assert result is False


def test_check_connected_connected(gui):
    """Test check_connected when connected"""
    gui.bot_running = True
    gui.guild = Mock()
    
    result = gui.check_connected()
    assert result is True


def test_update_status(gui):
    """Test status update"""
    gui.update_status("Test Status", '#ffffff')
    assert gui.status_label.cget('text') == "Test Status"
    assert gui.status_label.cget('foreground') == '#ffffff'


def test_run_async_with_success(gui):
    """Test run_async with successful operation"""
    gui.loop = asyncio.new_event_loop()
    
    async def success_coro():
        return "success"
    
    gui.run_async(success_coro())
    
    # Should queue a log message
    assert not gui.gui_queue.empty()


def test_run_async_with_permission_error(gui):
    """Test run_async with permission error"""
    gui.loop = asyncio.new_event_loop()
    
    async def forbidden_coro():
        raise discord.Forbidden(None, "administrator")
    
    gui.run_async(forbidden_coro())
    
    # Should queue error messages
    assert not gui.gui_queue.empty()


def test_run_async_with_rate_limit(gui):
    """Test run_async with rate limit error"""
    gui.loop = asyncio.new_event_loop()
    
    async def rate_limit_coro():
        error = discord.HTTPException(Mock(status=429), "rate limited")
        raise error
    
    gui.run_async(rate_limit_coro())
    
    # Should queue warning messages
    assert not gui.gui_queue.empty()


def test_run_async_with_timeout(gui):
    """Test run_async with timeout error"""
    gui.loop = asyncio.new_event_loop()
    
    async def timeout_coro():
        raise asyncio.TimeoutError()
    
    gui.run_async(timeout_coro())
    
    # Should queue error messages
    assert not gui.gui_queue.empty()


def test_run_async_with_connection_error(gui):
    """Test run_async with connection error"""
    gui.loop = asyncio.new_event_loop()
    
    async def connection_error_coro():
        raise ConnectionError("Connection failed")
    
    gui.run_async(connection_error_coro())
    
    # Should queue error messages
    assert not gui.gui_queue.empty()


def test_process_gui_queue(gui):
    """Test GUI queue processing"""
    # Add items to queue
    gui.gui_queue.put({'type': 'log', 'message': 'Test', 'color': '#ffffff'})
    gui.gui_queue.put({'type': 'status', 'status': 'Test Status', 'color': '#ffffff'})
    
    # Process queue
    gui._process_gui_queue()
    
    # Queue should be empty after processing
    assert gui.gui_queue.empty()


def test_process_gui_queue_empty(gui):
    """Test GUI queue processing with empty queue"""
    # Process empty queue
    gui._process_gui_queue()
    
    # Should not raise exception
    assert True


def test_process_gui_queue_invalid_action(gui):
    """Test GUI queue processing with invalid action"""
    # Add invalid action
    gui.gui_queue.put({'type': 'invalid_type'})
    
    # Should not raise exception
    gui._process_gui_queue()
    assert True

