"""
Custom exceptions for DemonX
"""


class DemonXError(Exception):
    """Base exception for DemonX"""
    pass


class OperationError(DemonXError):
    """Error during operation execution"""
    
    def __init__(self, message: str, operation_type: str = None, details: dict = None):
        super().__init__(message)
        self.operation_type = operation_type
        self.details = details or {}


class ValidationError(DemonXError):
    """Validation error"""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field


class RateLimitError(DemonXError):
    """Rate limit error"""
    
    def __init__(self, message: str, retry_after: float = None):
        super().__init__(message)
        self.retry_after = retry_after


class PermissionError(DemonXError):
    """Permission error"""
    
    def __init__(self, message: str, required_permissions: list = None):
        super().__init__(message)
        self.required_permissions = required_permissions or []


class ConfigurationError(DemonXError):
    """Configuration error"""
    pass

