"""
Tests for OperationHistory class
"""

import pytest
import json
from pathlib import Path
from demonx import OperationHistory, OperationType, OperationRecord
from datetime import datetime


def test_operation_history_initialization(tmp_path):
    """Test OperationHistory initialization"""
    history_file = tmp_path / "test_history.json"
    history = OperationHistory(str(history_file))
    assert history is not None
    assert hasattr(history, 'add_operation')
    assert hasattr(history, 'get_statistics')


def test_operation_history_add_operation(tmp_path):
    """Test adding operations to history"""
    history_file = tmp_path / "test_history.json"
    history = OperationHistory(str(history_file))
    
    # Add a test operation
    history.add_operation(
        operation_type=OperationType.BAN,
        success=True,
        details={"member_id": 123456}
    )
    
    # Check that file was created
    assert history_file.exists()


def test_operation_history_get_statistics(tmp_path):
    """Test getting statistics from history"""
    history_file = tmp_path / "test_history.json"
    history = OperationHistory(str(history_file))
    
    # Add some operations
    history.add_operation(OperationType.BAN, True)
    history.add_operation(OperationType.KICK, True)
    history.add_operation(OperationType.BAN, False)
    
    stats = history.get_statistics()
    assert isinstance(stats, dict)
    # Statistics should contain operation counts
    assert 'ban' in stats or 'ban_success' in stats or 'ban_failed' in stats

