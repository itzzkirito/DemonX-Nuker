"""
Operation history tracking with batched saves
"""

import json
import logging
import asyncio
import gzip
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import asdict

from .config import Config, OperationType, OperationRecord

logger = logging.getLogger('DemonX')


class OperationHistory:
    """Track operation history with batched saves"""
    
    def __init__(self, history_file: str = "operation_history.json", batch_size: int = None, max_file_size_mb: int = None):
        self.history_file = history_file
        self.history: List[OperationRecord] = []
        self.batch_size = batch_size or Config.HISTORY_BATCH_SIZE
        self.max_file_size_mb = max_file_size_mb or Config.MAX_HISTORY_FILE_SIZE_MB
        self.pending_saves = 0
        self.load_history()
    
    def load_history(self):
        """Load history from file"""
        try:
            if Path(self.history_file).exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = [OperationRecord(**record) for record in data[-Config.MAX_HISTORY_RECORDS:]]
        except Exception as e:
            logger.error(f"Error loading history: {e}")
    
    def _check_file_size(self):
        """Check if history file is too large and rotate/compress if needed"""
        try:
            if Path(self.history_file).exists():
                size_mb = Path(self.history_file).stat().st_size / (1024 * 1024)
                if size_mb > self.max_file_size_mb:
                    # Try compression first (keeps more history)
                    compressed = self.compress_old_history(days_old=7)
                    if not compressed:
                        # If compression didn't help, rotate
                        self._rotate_history()
                    else:
                        # Check size again after compression
                        size_mb = Path(self.history_file).stat().st_size / (1024 * 1024)
                        if size_mb > self.max_file_size_mb:
                            self._rotate_history()
        except Exception as e:
            logger.error(f"Error checking history file size: {e}")
    
    def _rotate_history(self):
        """Keep only recent history records to prevent file size growth"""
        try:
            # Keep last MAX_HISTORY_RECORDS entries
            if len(self.history) > Config.MAX_HISTORY_RECORDS:
                self.history = self.history[-Config.MAX_HISTORY_RECORDS:]
                logger.info(f"Rotated history: kept last {Config.MAX_HISTORY_RECORDS} records")
        except Exception as e:
            logger.error(f"Error rotating history: {e}")
    
    def save_history(self, force: bool = False):
        """Save history to file (batched for performance)"""
        if not force and self.pending_saves < self.batch_size:
            return
        
        # Check file size before saving
        self._check_file_size()
        
        try:
            # Use compact JSON (no indent) for faster I/O
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(record) for record in self.history], f, separators=(',', ':'))
            self.pending_saves = 0
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    async def save_history_async(self, force: bool = False):
        """Async save history to file (faster for high-volume operations)"""
        if not force and self.pending_saves < self.batch_size:
            return
        
        try:
            # Use asyncio for non-blocking file I/O
            loop = asyncio.get_event_loop()
            data = [asdict(record) for record in self.history]
            
            def _save():
                """Helper function to save with proper file handling"""
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, separators=(',', ':'))
            
            await loop.run_in_executor(None, _save)
            self.pending_saves = 0
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def add_operation(self, operation_type: OperationType, success: bool, details: Dict, error: Optional[str] = None):
        """Add operation to history"""
        record = OperationRecord(
            operation_type=operation_type.value,
            timestamp=datetime.now().isoformat(),
            success=success,
            details=details,
            error=error
        )
        self.history.append(record)
        if len(self.history) > Config.MAX_HISTORY_RECORDS:
            self.history = self.history[-Config.MAX_HISTORY_RECORDS:]
        self.pending_saves += 1
        self.save_history()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get operation statistics (optimized - single pass)"""
        from collections import defaultdict
        stats = defaultdict(int)
        # Single pass through history for maximum speed
        for record in self.history:
            op_type = record.operation_type
            stats[op_type] += 1
            # Use conditional expression for speed
            key = f"{op_type}_{'success' if record.success else 'failed'}"
            stats[key] += 1
        return dict(stats)
    
    def flush(self):
        """Force save history"""
        self.save_history(force=True)
    
    def compress_old_history(self, days_old: int = 30) -> Optional[str]:
        """Compress history older than specified days
        
        Args:
            days_old: Number of days to keep uncompressed
            
        Returns:
            Path to compressed file if created, None otherwise
        """
        try:
            if not Path(self.history_file).exists():
                return None
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            old_records = []
            recent_records = []
            
            for record in self.history:
                try:
                    record_date = datetime.fromisoformat(record.timestamp)
                    if record_date < cutoff_date:
                        old_records.append(record)
                    else:
                        recent_records.append(record)
                except (ValueError, TypeError):
                    # Keep records with invalid dates in recent
                    recent_records.append(record)
            
            if not old_records:
                logger.info("No old history to compress")
                return None
            
            # Create compressed archive
            archive_name = f"{self.history_file}.{datetime.now().strftime('%Y%m%d')}.gz"
            with gzip.open(archive_name, 'wt', encoding='utf-8') as f:
                json.dump([asdict(record) for record in old_records], f, separators=(',', ':'))
            
            # Update history to only keep recent records
            self.history = recent_records
            self.save_history(force=True)
            
            logger.info(f"Compressed {len(old_records)} old records to {archive_name}")
            return archive_name
        except Exception as e:
            logger.error(f"Error compressing history: {e}")
            return None
    
    def export_history(self, output_file: str, format: str = 'json') -> bool:
        """Export history to external file
        
        Args:
            output_file: Path to output file
            format: Export format ('json' or 'json.gz' for compressed)
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            data = [asdict(record) for record in self.history]
            
            if format == 'json.gz' or output_file.endswith('.gz'):
                with gzip.open(output_file, 'wt', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            else:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            logger.info(f"Exported {len(data)} records to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting history: {e}")
            return False

