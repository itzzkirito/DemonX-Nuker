"""
Tests for validation helper methods
"""

import pytest
from demonx_complete import DemonXComplete


def test_validate_token():
    """Test token validation"""
    # Valid token
    valid_token = "MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIuQWJjLkRlZg"
    assert DemonXComplete.validate_token(valid_token) == valid_token
    
    # Invalid tokens
    with pytest.raises(ValueError, match="cannot be empty"):
        DemonXComplete.validate_token("")
    
    with pytest.raises(ValueError, match="too short"):
        DemonXComplete.validate_token("short")
    
    with pytest.raises(ValueError, match="invalid"):
        DemonXComplete.validate_token("no.dots.here.extra")


def test_validate_guild_id():
    """Test guild ID validation"""
    # Valid guild ID
    valid_id = "123456789012345678"
    assert DemonXComplete.validate_guild_id(valid_id) == 123456789012345678
    
    # Invalid guild IDs
    with pytest.raises(ValueError, match="must be positive"):
        DemonXComplete.validate_guild_id("-1")
    
    with pytest.raises(ValueError, match="too small"):
        DemonXComplete.validate_guild_id("123")
    
    with pytest.raises(ValueError, match="Invalid guild ID format"):
        DemonXComplete.validate_guild_id("not_a_number")


def test_validate_count():
    """Test count validation"""
    # Valid counts
    assert DemonXComplete.validate_count(10) == 10
    assert DemonXComplete.validate_count(1, min_value=1) == 1
    assert DemonXComplete.validate_count(100, max_value=100) == 100
    
    # Invalid counts
    with pytest.raises(ValueError, match="must be at least"):
        DemonXComplete.validate_count(0)
    
    with pytest.raises(ValueError, match="must be at most"):
        DemonXComplete.validate_count(2000, max_value=1000)


def test_validate_message_length():
    """Test message length validation"""
    # Valid messages
    short_msg = "Hello"
    assert DemonXComplete.validate_message_length(short_msg) == short_msg
    
    max_msg = "x" * 2000
    assert DemonXComplete.validate_message_length(max_msg) == max_msg
    
    # Invalid messages
    with pytest.raises(ValueError, match="exceeds maximum"):
        DemonXComplete.validate_message_length("x" * 2001)

