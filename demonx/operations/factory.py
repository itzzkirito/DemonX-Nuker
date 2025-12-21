"""
Operation factory for creating operation instances
"""

from typing import Dict, Type, Optional, List
from .base import BaseOperation, OperationCategory


class OperationFactory:
    """Factory for creating and managing operation instances"""
    
    _operations: Dict[str, Type[BaseOperation]] = {}
    _operation_metadata: Dict[str, Dict[str, any]] = {}
    
    @classmethod
    def register(
        cls,
        op_type: str,
        operation_class: Type[BaseOperation],
        metadata: Optional[Dict[str, any]] = None
    ) -> None:
        """Register an operation type
        
        Args:
            op_type: Operation type identifier (e.g., 'ban_all', 'create_channel')
            operation_class: The operation class to register
            metadata: Optional metadata about the operation
        """
        cls._operations[op_type] = operation_class
        cls._operation_metadata[op_type] = metadata or {}
    
    @classmethod
    def create(cls, op_type: str) -> Optional[BaseOperation]:
        """Create an operation instance
        
        Args:
            op_type: Operation type identifier
            
        Returns:
            Operation instance or None if not found
        """
        operation_class = cls._operations.get(op_type)
        if operation_class:
            return operation_class()
        return None
    
    @classmethod
    def get_operation_types(cls) -> List[str]:
        """Get list of all registered operation types
        
        Returns:
            List of operation type identifiers
        """
        return list(cls._operations.keys())
    
    @classmethod
    def get_operations_by_category(
        cls,
        category: OperationCategory
    ) -> List[str]:
        """Get operations by category
        
        Args:
            category: Operation category
            
        Returns:
            List of operation type identifiers in the category
        """
        result = []
        for op_type, op_class in cls._operations.items():
            instance = op_class()
            if instance.category == category:
                result.append(op_type)
        return result
    
    @classmethod
    def get_metadata(cls, op_type: str) -> Dict[str, any]:
        """Get metadata for an operation type
        
        Args:
            op_type: Operation type identifier
            
        Returns:
            Metadata dictionary
        """
        return cls._operation_metadata.get(op_type, {})
    
    @classmethod
    def is_registered(cls, op_type: str) -> bool:
        """Check if an operation type is registered
        
        Args:
            op_type: Operation type identifier
            
        Returns:
            True if registered, False otherwise
        """
        return op_type in cls._operations

