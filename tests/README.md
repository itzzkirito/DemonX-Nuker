# DemonX Test Suite

This directory contains unit tests for the DemonX Nuker codebase.

## Running Tests

### Install Dependencies
```bash
pip install -r requirements-dev.txt
```

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_config.py
```

### Run with Coverage
```bash
pytest --cov=demonx --cov=demonx_complete --cov-report=html
```

### Run with Verbose Output
```bash
pytest -v
```

## Test Structure

- `conftest.py` - Pytest configuration and shared fixtures
- `test_config.py` - Tests for Config class and constants
- `test_rate_limiter.py` - Tests for RateLimiter class
- `test_proxy_manager.py` - Tests for ProxyManager class
- `test_operation_history.py` - Tests for OperationHistory class
- `test_preset_manager.py` - Tests for PresetManager class

## Adding New Tests

When adding new tests:

1. Create a new file `test_<module_name>.py`
2. Import necessary fixtures from `conftest.py`
3. Use `@pytest.mark.asyncio` for async tests
4. Use `tmp_path` fixture for temporary files
5. Follow the naming convention: `test_<function_name>`

## Mock Discord API

For testing Discord-related functionality, use the `mock_guild` and `mock_bot` fixtures from `conftest.py`. These provide mock objects that simulate Discord API responses without requiring actual API calls.

## Notes

- Tests use `pytest-asyncio` for async test support
- Tests use `pytest-mock` for mocking functionality
- Tests use `tmp_path` for temporary file operations
- All tests should be independent and not rely on external services

