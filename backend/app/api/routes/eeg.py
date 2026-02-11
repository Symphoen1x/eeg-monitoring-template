"""
EEG Data Ingestion Routes
HTTP endpoints to receive EEG data from Python LSL middleware
Week 3, Monday - EEG Data Relay System
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from typing import Dict
from uuid import UUID
from datetime import datetime

from app.schemas.eeg import EEGStreamData, EEGDataPoint
from app.api.websocket_manager import manager
from app.core.eeg_relay import relay_eeg_to_clients, save_eeg_to_database

router = APIRouter(prefix="/eeg", tags=["EEG Data"])


# Track active sessions receiving EEG data
active_eeg_sessions: Dict[str, datetime] = {}


@router.post("/stream", status_code=status.HTTP_200_OK)
async def receive_eeg_stream(
    data: EEGStreamData,
    background_tasks: BackgroundTasks
):
    """
    Receive real-time EEG data from Python LSL middleware
    
    This endpoint is called by the external Python LSL process that reads
    from the Muse 2 headband, processes the signal, and sends it here for
    relay to browser clients via WebSocket.
    
    **Data Flow**: Python LSL → HTTP POST → FastAPI → WebSocket → Browser
    
    **Request Body**:
    - session_id: UUID of active driving session
    - timestamp: ISO format timestamp
    - sample_rate: Sampling rate (e.g., 256 Hz)
    - channels: EEG channel data (TP9, AF7, AF8, TP10)
    - processed: Processed metrics (theta/alpha power, fatigue score)
    
    **Returns**:
    - status: "received"
    - clients_notified: Number of WebSocket clients that received the data
    """
    session_id_str = str(data.session_id)
    
    # Update session activity timestamp
    active_eeg_sessions[session_id_str] = datetime.now()
    
    # Relay to WebSocket clients (non-blocking)
    clients_notified = await relay_eeg_to_clients(session_id_str, data.dict())
    
    # Save to database in background (optional)
    if data.save_to_db:
        background_tasks.add_task(save_eeg_to_database, data)
    
    return {
        "status": "received",
        "timestamp": data.timestamp,
        "clients_notified": clients_notified
    }


@router.post("/batch", status_code=status.HTTP_200_OK)
async def receive_eeg_batch(
    session_id: UUID,
    data_points: list[EEGDataPoint],
    background_tasks: BackgroundTasks
):
    """
    Receive batch EEG data (alternative to streaming)
    
    Useful for sending multiple data points at once to reduce HTTP overhead.
    
    **Request Body**:
    - session_id: UUID of session
    - data_points: Array of EEG data points
    """
    session_id_str = str(session_id)
    
    # Relay each data point
    total_clients = 0
    for point in data_points:
        clients = await relay_eeg_to_clients(
            session_id_str, 
            {"type": "eeg_data", "data": point.dict()}
        )
        total_clients = max(total_clients, clients)
    
    return {
        "status": "received",
        "data_points": len(data_points),
        "clients_notified": total_clients
    }


@router.get("/status")
async def get_eeg_status():
    """
    Get status of EEG data flow
    
    Returns information about active sessions receiving EEG data
    and connected WebSocket clients.
    """
    # Get WebSocket connection stats
    ws_stats = {
        "total_connections": len(manager.active_connections),
        "session_connections": {}
    }
    
    # Count connections per session
    for session_id in manager.session_connections:
        ws_stats["session_connections"][session_id] = len(
            manager.session_connections[session_id]
        )
    
    return {
        "status": "operational",
        "active_eeg_sessions": len(active_eeg_sessions),
        "sessions": list(active_eeg_sessions.keys()),
        "websocket": ws_stats,
        "last_activity": {
            session_id: timestamp.isoformat()
            for session_id, timestamp in active_eeg_sessions.items()
        }
    }


@router.delete("/session/{session_id}")
async def stop_eeg_session(session_id: UUID):
    """
    Stop EEG data streaming for a session
    
    Call this when a session ends to cleanup tracking.
    """
    session_id_str = str(session_id)
    
    if session_id_str in active_eeg_sessions:
        del active_eeg_sessions[session_id_str]
        
        # Notify connected clients that EEG stream stopped
        await manager.broadcast_to_session(
            session_id_str,
            {"type": "eeg_stopped", "session_id": session_id_str}
        )
        
        return {"status": "stopped", "session_id": session_id_str}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active EEG session found for {session_id}"
        )


@router.get("/buffer/stats")
async def get_buffer_stats():
    """
    Get EEG data buffer statistics
    
    Returns metrics about the batch insertion buffer:
    - Current buffer size
    - Total items processed
    - Total flushes
    - Average items per flush
    - Time since last flush
    - Buffer status (running/stopped)
    
    Useful for monitoring buffer performance and debugging.
    """
    from app.core.eeg_relay import get_eeg_buffer_stats
    
    try:
        stats = get_eeg_buffer_stats()
        return {
            "status": "success",
            "buffer": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "buffer": None
        }
