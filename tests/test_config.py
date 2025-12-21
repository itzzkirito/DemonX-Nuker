"""
Tests for Config class and constants
"""

import pytest
from demonx import Config


def test_config_constants():
    """Test that Config constants are properly defined"""
    assert Config.MAX_HISTORY_RECORDS > 0
    assert Config.BATCH_SIZE_BAN_KICK > 0
    assert Config.BATCH_SIZE_CHANNELS > 0
    assert Config.DELAY_MINIMAL >= 0
    assert Config.DELAY_DEFAULT >= 0
    assert Config.RETRY_BASE_DELAY > 0
    assert Config.MAX_BACKOFF > 0
    assert Config.LARGE_GUILD_THRESHOLD > 0


def test_config_retry_strategies():
    """Test that retry strategy constants are valid"""
    assert Config.RETRY_STRATEGY in ["exponential", "linear", "fixed"]


def test_config_operation_types():
    """Test that OperationType enum values are accessible"""
    from demonx import OperationType
    
    # Check that common operation types exist
    assert hasattr(OperationType, 'BAN')
    assert hasattr(OperationType, 'KICK')
    assert hasattr(OperationType, 'DELETE_CHANNEL')
    assert hasattr(OperationType, 'CREATE_CHANNEL')


def test_config_logging_constants():
    """Test that logging configuration constants exist"""
    assert hasattr(Config, 'LOG_FILE')
    assert hasattr(Config, 'LOG_MAX_BYTES')
    assert hasattr(Config, 'LOG_BACKUP_COUNT')
    assert hasattr(Config, 'LOG_LEVEL')
    assert hasattr(Config, 'LOG_FORMAT')
    assert Config.LOG_MAX_BYTES > 0
    assert Config.LOG_BACKUP_COUNT >= 0


def test_config_connector_constants():
    """Test that connection pool configuration constants exist"""
    assert hasattr(Config, 'CONNECTOR_LIMIT')
    assert hasattr(Config, 'CONNECTOR_LIMIT_PER_HOST')
    assert hasattr(Config, 'CONNECTOR_TTL_DNS_CACHE')
    assert Config.CONNECTOR_LIMIT > 0
    assert Config.CONNECTOR_LIMIT_PER_HOST > 0
    assert Config.CONNECTOR_TTL_DNS_CACHE > 0


def test_config_large_guild_constants():
    """Test that large guild configuration constants exist"""
    assert hasattr(Config, 'LARGE_GUILD_THRESHOLD')
    assert hasattr(Config, 'LARGE_GUILD_CHUNK_SIZE')
    assert Config.LARGE_GUILD_THRESHOLD > 0
    assert Config.LARGE_GUILD_CHUNK_SIZE > 0

