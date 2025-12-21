"""
Operation queue system for DemonX
Allows queuing and scheduling of operations
"""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from queue import PriorityQueue
import threading

logger = logging.getLogger('DemonX')


class QueuePriority(Enum):
    """Operation queue priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class QueuedOperation:
    """Represents a queued operation"""
    operation_type: str
    operation_name: str
    params: Dict[str, Any]
    priority: QueuePriority
    scheduled_time: Optional[float] = None  # Unix timestamp, None for immediate
    created_at: float = None
    id: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().timestamp()
        if self.id is None:
            self.id = f"{self.operation_type}_{int(self.created_at * 1000)}"
    
    def __lt__(self, other):
        """Comparison for priority queue (lower priority value = higher priority)"""
        if self.scheduled_time and other.scheduled_time:
            if self.scheduled_time != other.scheduled_time:
                return self.scheduled_time < other.scheduled_time
        elif self.scheduled_time:
            return False
        elif other.scheduled_time:
            return True
        
        # Compare by priority
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        
        # Same priority, compare by creation time
        return self.created_at < other.created_at


class OperationQueue:
    """Operation queue for scheduling and managing operations"""
    
    def __init__(self, queue_file: str = "operation_queue.json"):
        self.queue_file = queue_file
        self._queue: PriorityQueue = PriorityQueue()
        self._lock = threading.Lock()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._operation_handler: Optional[Callable] = None
        
        # Load persisted queue
        self.load_queue()
    
    def set_handler(self, handler: Callable):
        """Set the operation handler function
        
        Args:
            handler: Async function that takes (operation_type, params, guild) and executes the operation
        """
        self._operation_handler = handler
    
    def add_operation(
        self,
        operation_type: str,
        operation_name: str,
        params: Dict[str, Any],
        priority: QueuePriority = QueuePriority.NORMAL,
        scheduled_time: Optional[float] = None
    ) -> str:
        """Add operation to queue
        
        Args:
            operation_type: Type of operation (e.g., 'ban_all', 'create_channels')
            operation_name: Human-readable operation name
            params: Operation parameters
            priority: Queue priority (default: NORMAL)
            scheduled_time: Unix timestamp for scheduled execution (None for immediate)
        
        Returns:
            Operation ID
        """
        operation = QueuedOperation(
            operation_type=operation_type,
            operation_name=operation_name,
            params=params,
            priority=priority,
            scheduled_time=scheduled_time
        )
        
        with self._lock:
            self._queue.put(operation)
            self.save_queue()
        
        logger.info(f"Added operation to queue: {operation_name} (ID: {operation.id}, Priority: {priority.name})")
        return operation.id
    
    def remove_operation(self, operation_id: str) -> bool:
        """Remove operation from queue by ID
        
        Args:
            operation_id: ID of operation to remove
        
        Returns:
            True if removed, False if not found
        """
        with self._lock:
            # Rebuild queue without the removed operation
            temp_queue = PriorityQueue()
            removed = False
            
            while not self._queue.empty():
                op = self._queue.get()
                if op.id != operation_id:
                    temp_queue.put(op)
                else:
                    removed = True
            
            self._queue = temp_queue
            
            if removed:
                self.save_queue()
                logger.info(f"Removed operation from queue: {operation_id}")
            
            return removed
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        with self._lock:
            return self._queue.qsize()
    
    def get_queue_list(self) -> List[Dict[str, Any]]:
        """Get list of all queued operations
        
        Returns:
            List of operation dictionaries
        """
        with self._lock:
            # Get all items without removing them
            items = []
            temp_queue = PriorityQueue()
            
            while not self._queue.empty():
                op = self._queue.get()
                items.append({
                    'id': op.id,
                    'operation_type': op.operation_type,
                    'operation_name': op.operation_name,
                    'params': op.params,
                    'priority': op.priority.name,
                    'scheduled_time': op.scheduled_time,
                    'created_at': op.created_at
                })
                temp_queue.put(op)
            
            self._queue = temp_queue
            return items
    
    def clear_queue(self) -> int:
        """Clear all operations from queue
        
        Returns:
            Number of operations cleared
        """
        with self._lock:
            count = self._queue.qsize()
            self._queue = PriorityQueue()
            self.save_queue()
            logger.info(f"Cleared {count} operations from queue")
            return count
    
    def start_processing(self, guild):
        """Start processing queue (non-blocking)
        
        Args:
            guild: Discord guild to execute operations on
        """
        if self._running:
            logger.warning("Queue processor already running")
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_queue(guild))
        logger.info("Started queue processor")
    
    def stop_processing(self):
        """Stop processing queue"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
        logger.info("Stopped queue processor")
    
    async def _process_queue(self, guild):
        """Process queue operations"""
        while self._running:
            try:
                # Get next operation (non-blocking)
                try:
                    with self._lock:
                        if self._queue.empty():
                            await asyncio.sleep(1.0)  # Check every second
                            continue
                        operation = self._queue.get()
                except:
                    await asyncio.sleep(1.0)
                    continue
                
                # Check if operation is scheduled for future
                current_time = datetime.now().timestamp()
                if operation.scheduled_time and operation.scheduled_time > current_time:
                    # Put back and wait
                    with self._lock:
                        self._queue.put(operation)
                    wait_time = operation.scheduled_time - current_time
                    await asyncio.sleep(min(wait_time, 60.0))  # Check at least every minute
                    continue
                
                # Execute operation
                if self._operation_handler:
                    try:
                        logger.info(f"Executing queued operation: {operation.operation_name} (ID: {operation.id})")
                        await self._operation_handler(operation.operation_type, operation.params, guild)
                        logger.info(f"Completed queued operation: {operation.operation_name} (ID: {operation.id})")
                    except Exception as e:
                        logger.error(f"Error executing queued operation {operation.id}: {e}")
                else:
                    logger.warning(f"No operation handler set, skipping operation: {operation.operation_name}")
                
                # Save queue after processing
                with self._lock:
                    self.save_queue()
                
                # Small delay between operations
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in queue processor: {e}", exc_info=True)
                await asyncio.sleep(1.0)
    
    def save_queue(self):
        """Save queue to file"""
        try:
            operations = []
            temp_queue = PriorityQueue()
            
            while not self._queue.empty():
                op = self._queue.get()
                operations.append({
                    'operation_type': op.operation_type,
                    'operation_name': op.operation_name,
                    'params': op.params,
                    'priority': op.priority.value,
                    'scheduled_time': op.scheduled_time,
                    'created_at': op.created_at,
                    'id': op.id
                })
                temp_queue.put(op)
            
            self._queue = temp_queue
            
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(operations, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving queue: {e}")
    
    def load_queue(self):
        """Load queue from file"""
        try:
            if not Path(self.queue_file).exists():
                return
            
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                operations = json.load(f)
            
            for op_data in operations:
                operation = QueuedOperation(
                    operation_type=op_data['operation_type'],
                    operation_name=op_data['operation_name'],
                    params=op_data['params'],
                    priority=QueuePriority(op_data.get('priority', 2)),
                    scheduled_time=op_data.get('scheduled_time'),
                    created_at=op_data.get('created_at', datetime.now().timestamp()),
                    id=op_data.get('id')
                )
                self._queue.put(operation)
            
            logger.info(f"Loaded {len(operations)} operations from queue file")
        except Exception as e:
            logger.error(f"Error loading queue: {e}")

