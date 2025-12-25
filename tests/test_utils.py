"""
Tests for utility functions
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open
from demonx import load_config, get_user_friendly_error
import discord
import asyncio


def test_load_config_default_creation(tmp_path, monkeypatch):
    """Test config file creation with defaults"""
    monkeypatch.chdir(tmp_path)
    
    config = load_config()
    
    assert config['proxy'] is False
    assert config['dry_run'] is False
    assert config['verbose'] is True
    assert Path('config.json').exists()


def test_load_config_loads_existing(tmp_path, monkeypatch):
    """Test loading existing config file"""
    monkeypatch.chdir(tmp_path)
    
    # Create config file
    config_data = {
        'proxy': True,
        'dry_run': True,
        'verbose': False
    }
    with open('config.json', 'w') as f:
        json.dump(config_data, f)
    
    config = load_config()
    
    assert config['proxy'] is True
    assert config['dry_run'] is True
    assert config['verbose'] is False


def test_load_config_invalid_json(tmp_path, monkeypatch):
    """Test handling of invalid JSON"""
    monkeypatch.chdir(tmp_path)
    
    # Create invalid JSON file
    with open('config.json', 'w') as f:
        f.write("{ invalid json }")
    
    config = load_config()
    
    # Should return defaults
    assert config['proxy'] is False
    assert config['dry_run'] is False


def test_load_config_type_conversion(tmp_path, monkeypatch):
    """Test type conversion in config loading"""
    monkeypatch.chdir(tmp_path)
    
    # Create config with string booleans
    config_data = {
        'proxy': 'true',
        'dry_run': '1',
        'verbose': 'yes'
    }
    with open('config.json', 'w') as f:
        json.dump(config_data, f)
    
    config = load_config()
    
    # Should convert to booleans
    assert config['proxy'] is True
    assert config['dry_run'] is True
    assert config['verbose'] is True


def test_get_user_friendly_error_permission():
    """Test permission error conversion"""
    error = discord.Forbidden(None, "administrator")
    msg = get_user_friendly_error(error)
    assert isinstance(msg, str)
    assert len(msg) > 0


def test_get_user_friendly_error_rate_limit():
    """Test rate limit error conversion"""
    error = discord.HTTPException(Mock(status=429), "rate limited")
    msg = get_user_friendly_error(error)
    assert isinstance(msg, str)
    assert "rate" in msg.lower() or "limit" in msg.lower()


def test_get_user_friendly_error_with_context():
    """Test error conversion with context"""
    error = discord.Forbidden(None, "ban_members")
    msg = get_user_friendly_error(error, context="banning members")
    assert isinstance(msg, str)
    assert "banning" in msg.lower() or "context" in msg.lower()


def test_get_user_friendly_error_with_suggestion():
    """Test error conversion with suggestion"""
    error = discord.Forbidden(None, "administrator")
    msg = get_user_friendly_error(error, suggestion="Grant administrator role")
    assert isinstance(msg, str)
    assert "suggestion" in msg.lower() or "administrator" in msg.lower()

