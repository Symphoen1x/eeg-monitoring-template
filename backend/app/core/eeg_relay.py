"""
EEG Data Relay Logic
Bridge between HTTP endpoint and WebSocket clients
Week 3, Monday-Tuesday - EEG Data Relay System with Batch Insertion
"""

from typing import Dict, Any, List
import logging

from app.api.websocket_manager import manager
from app.schemas.eeg import EEGStreamData
from app.db.database import get_db
from app.db.models import EEGData
from app.core.data_buffer import AsyncDataBuffer

logger = logging.getLogger(__name__)


# ============================================================================
# Batch Insertion Configuration
# ============================================================================

# Global buffer for EEG data batch insertion
# Flushes every 100 records OR 1 second (whichever comes first)
_eeg_buffer: AsyncDataBuffer = None


async def _batch_flush_eeg_to_db(eeg_data_list: List[EEGStreamData]):
    """
    Batch flush EEG data to TimescaleDB
    
    This is the callback for AsyncDataBuffer.
    Performs bulk insert for better performance.
    
    Args:
        eeg_data_list: List of EEG data to insert
    """
    if not eeg_data_list:
        return
    
    db = next(get_db())
    
    try:
        # Convert EEGStreamData to EEGData models
        eeg_records = []
        for data in eeg_data_list:
            eeg_record = EEGData(
                session_id=data.session_id,
                timestamp=data.timestamp,
                sample_rate=data.sample_rate,
                tp9=data.channels.get("TP9"),
                af7=data.channels.get("AF7"),
                af8=data.channels.get("AF8"),
                tp10=data.channels.get("TP10"),
                # Processed metrics
                theta_power=data.processed.get("theta_power") if data.processed else None,
                alpha_power=data.processed.get("alpha_power") if data.processed else None,
                beta_power=data.processed.get("beta_power") if data.processed else None,
                gamma_power=data.processed.get("gamma_power") if data.processed else None,
                theta_alpha_ratio=data.processed.get("theta_alpha_ratio") if data.processed else None,
                fatigue_score=data.processed.get("fatigue_score") if data.processed else None
            )
            eeg_records.append(eeg_record)
        
        # Bulk insert (much faster than individual inserts)
        db.bulk_save_objects(eeg_records)
        db.commit()
        
        logger.info(f"Batch inserted {len(eeg_records)} EEG records to database")
        
    except Exception as e:
        logger.error(f"Error batch saving EEG data to database: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def get_eeg_buffer() -> AsyncDataBuffer:
    """
    Get or create global EEG data buffer
    
    Returns:
        AsyncDataBuffer instance for EEG data
    """
    global _eeg_buffer
    
    if _eeg_buffer is None:
        _eeg_buffer = AsyncDataBuffer(
            flush_callback=_batch_flush_eeg_to_db,
            max_size=100,  # Flush every 100 records
            max_time=1.0,  # OR every 1 second
            name="EEG_Buffer"
        )
        logger.info("Created global EEG data buffer")
    
    return _eeg_buffer


async def start_eeg_buffer():
    """
    Start EEG data buffer background worker
    
    Should be called on application startup
    """
    buffer = get_eeg_buffer()
    await buffer.start()
    logger.info("Started EEG data buffer background worker")


async def stop_eeg_buffer():
    """
    Stop EEG data buffer and flush remaining data
    
    Should be called on application shutdown
    """
    buffer = get_eeg_buffer()
    await buffer.stop()
    logger.info("Stopped EEG data buffer")


def get_eeg_buffer_stats() -> dict:
    """
    Get EEG buffer statistics
    
    Returns:
        Dictionary with buffer stats
    """
    buffer = get_eeg_buffer()
    return buffer.get_stats()


# ============================================================================
# EEG Relay Functions
# ============================================================================

async def relay_eeg_to_clients(session_id: str, data: Dict[str, Any]) -> int:
    """
    Relay EEG data to all WebSocket clients watching a session
    
    Args:
        session_id: Session UUID as string
        data: EEG data dictionary to broadcast
    
    Returns:
        Number of clients that received the data
    """
    # Prepare message for WebSocket clients
    # Frontend expects type: "eeg_data" with flattened structure
    message = {
        "type": "eeg_data",
        "session_id": session_id,  # Already string from caller
        "timestamp": data.get("timestamp"),
        "sample_rate": data.get("sample_rate"),
        "channels": data.get("channels"),
        "processed": data.get("processed")
    }
    
    # Broadcast to all clients connected to this session
    await manager.broadcast_to_session(session_id, message)
    
    # Return count of notified clients
    if session_id in manager.session_connections:
        return len(manager.session_connections[session_id])
    
    return 0


async def save_eeg_to_database(data: EEGStreamData):
    """
    Save EEG data to TimescaleDB using batch insertion
    
    This runs in background to not block the relay.
    Uses AsyncDataBuffer for automatic batching and performance optimization.
    
    Data is buffered and flushed when:
    - Buffer reaches 100 records, OR
    - 1 second has passed since last flush
    
    Args:
        data: EEG stream data to save
    """
    try:
        # Add to buffer (non-blocking)
        buffer = get_eeg_buffer()
        await buffer.add(data)
        
    except Exception as e:
        logger.error(f"Error buffering EEG data: {e}", exc_info=True)
        # Don't raise - we don't want to block the relay


def validate_eeg_timestamp(timestamp: str) -> bool:
    """
    Validate EEG data timestamp
    
    Ensures timestamp is recent and not too far in the future.
    Helps detect clock sync issues.
    
    Args:
        timestamp: ISO format timestamp string
    
    Returns:
        True if timestamp is valid
    """
    from datetime import datetime, timedelta
    
    try:
        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(ts.tzinfo)
        
        # Check if timestamp is within acceptable range
        # Allow 1 minute in past, 10 seconds in future
        time_diff = (now - ts).total_seconds()
        
        return -10 <= time_diff <= 60
        
    except Exception:
        return False
