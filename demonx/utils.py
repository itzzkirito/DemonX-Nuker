"""
Utility functions for DemonX
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import asyncio
import discord
from colorama import Fore, Style

logger = logging.getLogger('DemonX')

# User-friendly error messages - standardized format
ERROR_MESSAGES = {
    'permission_denied': "Bot lacks required permissions. Please grant Administrator role.",
    'rate_limited': "Rate limited. Please wait and try again.",
    'guild_not_found': "Guild not found. Verify bot is in the server and ID is correct.",
    'invalid_token': "Invalid bot token. Check token from Discord Developer Portal.",
    'timeout': "Operation timed out. The server may be slow or unresponsive.",
    'connection_error': "Connection error. Check your internet connection.",
    'proxy_error': "Proxy connection failed. Check proxy configuration.",
    'invalid_input': "Invalid input provided. Please check your input and try again.",
    'operation_failed': "Operation failed. Check logs for details.",
    'unknown_error': "An unknown error occurred. Please check logs for details.",
}

# Error message templates for consistent formatting
ERROR_TEMPLATES = {
    'format': "[{level}] {message}",
    'with_context': "[{level}] {message} (Context: {context})",
    'with_suggestion': "[{level}] {message}\nSuggestion: {suggestion}",
}


def get_user_friendly_error(error: Exception, context: Optional[str] = None, suggestion: Optional[str] = None) -> str:
    """Convert technical errors to user-friendly messages with standardized format
    
    Args:
        error: Exception to convert
        context: Optional context information
        suggestion: Optional suggestion for resolving the error
    
    Returns:
        User-friendly error message string with standardized format
    """
    message = None
    
    if isinstance(error, discord.Forbidden):
        message = ERROR_MESSAGES['permission_denied']
    elif isinstance(error, discord.HTTPException):
        if error.status == 429:
            message = ERROR_MESSAGES['rate_limited']
        elif error.status == 404:
            message = ERROR_MESSAGES['guild_not_found']
        else:
            message = ERROR_MESSAGES.get('operation_failed', str(error))
    elif isinstance(error, discord.LoginFailure):
        message = ERROR_MESSAGES['invalid_token']
    elif isinstance(error, (asyncio.TimeoutError, TimeoutError)):
        message = ERROR_MESSAGES['timeout']
    elif isinstance(error, (ConnectionError, OSError)):
        message = ERROR_MESSAGES['connection_error']
    elif 'proxy' in str(error).lower():
        message = ERROR_MESSAGES['proxy_error']
    else:
        message = ERROR_MESSAGES.get('unknown_error', str(error))
    
    # Format message with context and suggestion if provided
    if suggestion:
        return ERROR_TEMPLATES['with_suggestion'].format(
            level='ERROR',
            message=message,
            suggestion=suggestion
        )
    elif context:
        return ERROR_TEMPLATES['with_context'].format(
            level='ERROR',
            message=message,
            context=context
        )
    else:
        return ERROR_TEMPLATES['format'].format(
            level='ERROR',
            message=message
        )


def load_config() -> Dict[str, Any]:
    """Load and validate configuration file with schema validation
    
    Uses a schema-based validation approach with clear error messages.
    Supports config file versioning and migration for future changes.
    
    Returns:
        Dictionary with validated configuration values
    
    Raises:
        ValueError: If configuration values are invalid (logged, not raised)
    """
    default_config = {
        'proxy': False,
        'dry_run': False,
        'verbose': True,
        'version': '2.0'  # Config file version for migration support
    }
    
    # Configuration schema for validation
    # Format: key: (expected_type, type_name, validator_function, error_message)
    config_schema = {
        'proxy': (bool, 'boolean', lambda v: isinstance(v, bool) or str(v).lower() in ('true', '1', 'yes', 'on', 'false', '0', 'no', 'off'), 
                 'proxy must be a boolean (true/false)'),
        'dry_run': (bool, 'boolean', lambda v: isinstance(v, bool) or str(v).lower() in ('true', '1', 'yes', 'on', 'false', '0', 'no', 'off'),
                   'dry_run must be a boolean (true/false)'),
        'verbose': (bool, 'boolean', lambda v: isinstance(v, bool) or str(v).lower() in ('true', '1', 'yes', 'on', 'false', '0', 'no', 'off'),
                   'verbose must be a boolean (true/false)'),
        'version': (str, 'string', lambda v: isinstance(v, str), 'version must be a string')
    }
    
    try:
        config_path = Path('config.json')
        if not config_path.exists():
            # Create default config
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            logger.info("Created default config.json")
            return default_config
        
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check config version for migration support
        config_version = config.get('version', '1.0')
        if config_version != default_config['version']:
            logger.info(f"Config version {config_version} detected, current version is {default_config['version']}")
            # Future: Add migration logic here if needed
        
        # Enhanced validation with schema checking
        validated = {}
        validation_errors = []
        
        for key, default_value in default_config.items():
            value = config.get(key, default_value)
            
            # Type validation using schema
            if key in config_schema:
                expected_type, type_name, validator, error_msg = config_schema[key]
                
                # Validate using validator function
                if not validator(value):
                    validation_errors.append(f"{key}: {error_msg}")
                    logger.warning(f"Invalid value for {key}: {value}, expected {type_name}, using default: {default_value}")
                    value = default_value
                else:
                    # Convert to expected type
                    if expected_type == bool:
                        if isinstance(value, str):
                            value = value.lower() in ('true', '1', 'yes', 'on')
                        elif isinstance(value, int):
                            value = bool(value)
                    elif expected_type == str:
                        value = str(value)
            
            # Additional validation
            if isinstance(default_value, bool):
                # Ensure boolean values are properly converted
                validated[key] = bool(value) if isinstance(value, (bool, int, str)) else default_value
            else:
                validated[key] = value if value is not None else default_value
        
        # Report validation errors
        if validation_errors:
            error_summary = "; ".join(validation_errors)
            logger.warning(f"Config validation issues: {error_summary}")
        
        # Validate file paths if specified
        if 'proxy_file' in config:
            proxy_path = Path(config['proxy_file'])
            if not proxy_path.exists() and proxy_path != Path('proxies.txt'):
                logger.warning(f"Proxy file not found: {proxy_path}, will use default")
        
        # Validate unknown keys
        unknown_keys = set(config.keys()) - set(default_config.keys()) - {'proxy_file'}  # proxy_file is allowed
        if unknown_keys:
            logger.info(f"Unknown config keys found (ignored): {', '.join(unknown_keys)}")
        
        return validated
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in config.json: {e}. Line {e.lineno if hasattr(e, 'lineno') else 'unknown'}"
        logger.error(error_msg)
        logger.info("Using default configuration")
        return default_config
    except (IOError, OSError) as e:
        logger.error(f"Error reading config.json: {e}")
        logger.info("Using default configuration")
        return default_config
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}", exc_info=True)
        logger.info("Using default configuration")
        return default_config


def print_banner():
    """Print banner with neon purple/blue"""
    # Large ASCII art DEMONX in neon purple/blue style
    banner = f"""
{Fore.MAGENTA}{Style.BRIGHT}
 ██████████                                                █████ █████
░░███░░░░███                                              ░░███ ░░███ 
 ░███   ░░███  ██████  █████████████    ██████  ████████   ░░███ ███  
 ░███    ░███ ███░░███░░███░░███░░███  ███░░███░░███░░███   ░░█████   
 ░███    ░███░███████  ░███ ░███ ░███ ░███ ░███ ░███ ░███    ███░███  
 ░███    ███ ░███░░░   ░███ ░███ ░███ ░███ ░███ ░███ ░███   ███ ░░███ 
 ██████████  ░░██████  █████░███ █████░░██████  ████ █████ █████ █████
░░░░░░░░░░    ░░░░░░  ░░░░░ ░░░ ░░░░░  ░░░░░░  ░░░░ ░░░░░ ░░░░░ ░░░░░ 
{Fore.CYAN}
{Style.RESET_ALL}
"""
    print(banner)

