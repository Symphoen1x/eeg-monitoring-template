"""
Data Buffering System
Generic async buffer for high-frequency time-series data
Week 3, Tuesday-Thursday - Backend Optimization

Provides thread-safe buffering with configurable flush strategies:
- Size-based: Flush when buffer reaches max_size
- Time-based: Flush after max_time seconds since last flush
"""

import asyncio
import time
from typing import List, Callable, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AsyncDataBuffer:
    """
    Thread-safe async buffer for batching high-frequency data writes
    
    Usage:
        async def flush_callback(items: List[Any]):
            # Write items to database
            await db.bulk_insert(items)
        
        buffer = AsyncDataBuffer(
            flush_callback=flush_callback,
            max_size=100,
            max_time=1.0
        )
        
        # Add items
        await buffer.add(data_item)
        
        # Manual flush if needed
        await buffer.flush()
    """
    
    def __init__(
        self,
        flush_callback: Callable[[List[Any]], Any],
        max_size: int = 100,
        max_time: float = 1.0,
        name: str = "DataBuffer"
    ):
        """
        Initialize async data buffer
        
        Args:
            flush_callback: Async function to call when flushing buffer
            max_size: Maximum buffer size before auto-flush
            max_time: Maximum time (seconds) before auto-flush
            name: Buffer name for logging
        """
        self.flush_callback = flush_callback
        self.max_size = max_size
        self.max_time = max_time
        self.name = name
        
        # Thread-safe buffer
        self.buffer: List[Any] = []
        self.lock = asyncio.Lock()
        
        # Timing tracking
        self.last_flush_time = time.time()
        self.total_items_processed = 0
        self.total_flushes = 0
        
        # Background worker for time-based flush
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(
            f"[{self.name}] Initialized with max_size={max_size}, "
            f"max_time={max_time}s"
        )
    
    async def start(self):
        """Start background worker for time-based flushing"""
        if self._running:
            logger.warning(f"[{self.name}] Already running")
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._background_worker())
        logger.info(f"[{self.name}] Background worker started")
    
    async def stop(self):
        """Stop background worker and flush remaining data"""
        if not self._running:
            return
        
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining data
        await self.flush()
        logger.info(f"[{self.name}] Stopped and flushed remaining data")
    
    async def add(self, item: Any) -> bool:
        """
        Add item to buffer
        
        Auto-flushes if buffer size reaches max_size
        
        Args:
            item: Data item to buffer
        
        Returns:
            True if item was added and flushed, False if just added
        """
        async with self.lock:
            self.buffer.append(item)
            
            # Check if size-based flush needed
            if len(self.buffer) >= self.max_size:
                logger.debug(
                    f"[{self.name}] Size threshold reached "
                    f"({len(self.buffer)}/{self.max_size})"
                )
                await self._flush_internal()
                return True
        
        return False
    
    async def add_many(self, items: List[Any]) -> bool:
        """
        Add multiple items to buffer
        
        Args:
            items: List of data items to buffer
        
        Returns:
            True if flush occurred, False otherwise
        """
        async with self.lock:
            self.buffer.extend(items)
            
            # Check if size-based flush needed
            if len(self.buffer) >= self.max_size:
                logger.debug(
                    f"[{self.name}] Size threshold reached after bulk add "
                    f"({len(self.buffer)}/{self.max_size})"
                )
                await self._flush_internal()
                return True
        
        return False
    
    async def flush(self) -> int:
        """
        Manually flush buffer
        
        Returns:
            Number of items flushed
        """
        async with self.lock:
            return await self._flush_internal()
    
    async def _flush_internal(self) -> int:
        """
        Internal flush (assumes lock is already held)
        
        Returns:
            Number of items flushed
        """
        if not self.buffer:
            return 0
        
        items_to_flush = self.buffer.copy()
        item_count = len(items_to_flush)
        
        # Clear buffer before calling callback
        # (in case callback is slow or fails)
        self.buffer.clear()
        self.last_flush_time = time.time()
        
        try:
            # Call flush callback
            if asyncio.iscoroutinefunction(self.flush_callback):
                await self.flush_callback(items_to_flush)
            else:
                self.flush_callback(items_to_flush)
            
            # Update statistics
            self.total_items_processed += item_count
            self.total_flushes += 1
            
            logger.debug(
                f"[{self.name}] Flushed {item_count} items "
                f"(total: {self.total_items_processed})"
            )
            
            return item_count
            
        except Exception as e:
            logger.error(
                f"[{self.name}] Error flushing {item_count} items: {e}",
                exc_info=True
            )
            # Re-add items to buffer on failure
            self.buffer.extend(items_to_flush)
            raise
    
    async def _background_worker(self):
        """Background worker for time-based flushing"""
        logger.info(f"[{self.name}] Background worker running")
        
        while self._running:
            try:
                # Check every 0.1 seconds
                await asyncio.sleep(0.1)
                
                # Check if time-based flush needed
                time_since_flush = time.time() - self.last_flush_time
                
                if time_since_flush >= self.max_time:
                    async with self.lock:
                        if self.buffer:  # Only flush if there's data
                            logger.debug(
                                f"[{self.name}] Time threshold reached "
                                f"({time_since_flush:.2f}s >= {self.max_time}s)"
                            )
                            await self._flush_internal()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"[{self.name}] Error in background worker: {e}",
                    exc_info=True
                )
    
    def get_stats(self) -> dict:
        """
        Get buffer statistics
        
        Returns:
            Dictionary with buffer stats
        """
        return {
            "name": self.name,
            "current_size": len(self.buffer),
            "max_size": self.max_size,
            "max_time": self.max_time,
            "total_items_processed": self.total_items_processed,
            "total_flushes": self.total_flushes,
            "avg_items_per_flush": (
                self.total_items_processed / self.total_flushes
                if self.total_flushes > 0 else 0
            ),
            "time_since_last_flush": time.time() - self.last_flush_time,
            "is_running": self._running
        }
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.stop()
