"""
Base classes for all operations
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import discord
from enum import Enum


class OperationCategory(Enum):
    """Operation categories"""
    MEMBER = "member"
    CHANNEL = "channel"
    ROLE = "role"
    GUILD = "guild"
    ADVANCED = "advanced"


class BaseOperation(ABC):
    """Base class for all operations
    
    All operations should inherit from this class and implement
    the required methods.
    """
    
    # Operation metadata
    name: str = ""
    description: str = ""
    category: OperationCategory = OperationCategory.ADVANCED
    requires_admin: bool = True
    rate_limit_sensitive: bool = True
    
    @abstractmethod
    async def execute(
        self,
        guild: discord.Guild,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute the operation
        
        Args:
            guild: The Discord guild to perform the operation on
            **kwargs: Operation-specific parameters
            
        Returns:
            Dictionary with operation results:
            - success: bool - Whether operation succeeded
            - count: int - Number of items processed
            - errors: List[str] - List of error messages
            - details: Dict[str, Any] - Additional operation details
        """
        pass
    
    @abstractmethod
    def validate(
        self,
        guild: discord.Guild,
        **kwargs
    ) -> tuple:
        """Validate operation parameters
        
        Args:
            guild: The Discord guild
            **kwargs: Operation parameters to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: bool - Whether parameters are valid
            - error_message: Optional[str] - Error message if invalid
        """
        pass
    
    def get_required_permissions(self) -> List[str]:
        """Get list of required Discord permissions
        
        Returns:
            List of permission names (e.g., ['ban_members', 'manage_channels'])
        """
        return []
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get rate limit information for this operation
        
        Returns:
            Dictionary with rate limit info:
            - batch_size: int - Recommended batch size
            - delay: float - Delay between batches
            - endpoint: str - API endpoint (if applicable)
        """
        return {
            'batch_size': 20,
            'delay': 0.1,
            'endpoint': None
        }


class MemberOperation(BaseOperation):
    """Base class for member-related operations"""
    category = OperationCategory.MEMBER
    
    def validate(self, guild: discord.Guild, **kwargs) -> tuple:
        """Base validation for member operations"""
        if not guild:
            return False, "Guild is required"
        return True, None


class ChannelOperation(BaseOperation):
    """Base class for channel-related operations"""
    category = OperationCategory.CHANNEL
    
    def validate(self, guild: discord.Guild, **kwargs) -> tuple:
        """Base validation for channel operations"""
        if not guild:
            return False, "Guild is required"
        return True, None


class RoleOperation(BaseOperation):
    """Base class for role-related operations"""
    category = OperationCategory.ROLE
    
    def validate(self, guild: discord.Guild, **kwargs) -> tuple:
        """Base validation for role operations"""
        if not guild:
            return False, "Guild is required"
        return True, None


class GuildOperation(BaseOperation):
    """Base class for guild-related operations"""
    category = OperationCategory.GUILD
    
    def validate(self, guild: discord.Guild, **kwargs) -> tuple:
        """Base validation for guild operations"""
        if not guild:
            return False, "Guild is required"
        return True, None

