"""
WebSocket Routes
Real-time EEG data streaming endpoints
Generic EEG Monitoring Template
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import json

from app.db.database import get_db
from app.db.models import MonitoringSession, EEGData, Alert
from app.api.websocket_manager import manager as ws_manager
from app.schemas.eeg import EEGDataPoint, AlertData

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/session/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time session data streaming
    
    Receives and broadcasts:
    - EEG data points
    - Fatigue alerts
    
    Connection URL: ws://localhost:8000/api/v1/ws/session/{session_id}
    """
    session = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    if not session:
        await websocket.close(code=1008, reason="Session not found")
        return
    
    await ws_manager.connect(websocket, str(session_id))
    
    try:
        await ws_manager.send_json({
            "type": "connection",
            "message": f"Connected to session {session_id}",
            "session_id": str(session_id),
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "eeg_data":
                await handle_eeg_data(data, session_id, db)
                
            elif message_type == "alert":
                await handle_alert(data, session_id, db)
                
            elif message_type == "ping":
                await ws_manager.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
            
            await ws_manager.broadcast_to_session(str(session_id), data)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, str(session_id))
        print(f"Client disconnected from session {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, str(session_id))


@router.websocket("/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    WebSocket endpoint for monitoring all sessions.
    Useful for admin/monitoring dashboard.
    
    Connection URL: ws://localhost:8000/api/v1/ws/monitor
    """
    await ws_manager.connect(websocket)
    
    try:
        await ws_manager.send_json({
            "type": "connection",
            "message": "Connected to monitoring feed",
            "timestamp": datetime.utcnow().isoformat(),
            "total_connections": ws_manager.get_total_connections()
        }, websocket)
        
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await ws_manager.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_connections": ws_manager.get_total_connections()
                }, websocket)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"Monitor WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@router.websocket("/ping")
async def websocket_ping(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for latency measurement.
    Connection URL: ws://localhost:8000/api/v1/ws/ping
    """
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "type": "ready",
            "message": "Ping service ready",
            "server_timestamp": datetime.utcnow().isoformat()
        })
        
        ping_count = 0
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                ping_count += 1
                await websocket.send_json({
                    "type": "pong",
                    "ping_number": ping_count,
                    "client_timestamp": data.get("client_timestamp"),
                    "server_timestamp": datetime.utcnow().isoformat()
                })
                
            elif data.get("type") == "get_stats":
                await websocket.send_json({
                    "type": "stats",
                    "total_pings": ping_count,
                    "server_timestamp": datetime.utcnow().isoformat()
                })
            
    except WebSocketDisconnect:
        print(f"Ping client disconnected after {ping_count} pings")
    except Exception as e:
        print(f"Ping WebSocket error: {e}")
    finally:
        await websocket.close()


# ============================================
# DATA HANDLERS
# ============================================

async def handle_eeg_data(data: dict, session_id: UUID, db: Session):
    """Handle incoming EEG data and store in database"""
    try:
        data_points = data.get("data_points", [])
        
        eeg_records = []
        for point in data_points:
            eeg_record = EEGData(
                session_id=session_id,
                timestamp=datetime.fromisoformat(point.get("timestamp").replace("Z", "+00:00")),
                raw_channels=point.get("raw_channels"),
                delta_power=point.get("delta_power"),
                theta_power=point.get("theta_power"),
                alpha_power=point.get("alpha_power"),
                beta_power=point.get("beta_power"),
                gamma_power=point.get("gamma_power"),
                theta_alpha_ratio=point.get("theta_alpha_ratio"),
                beta_alpha_ratio=point.get("beta_alpha_ratio"),
                signal_quality=point.get("signal_quality"),
                cognitive_state=point.get("cognitive_state"),
                eeg_fatigue_score=point.get("eeg_fatigue_score")
            )
            eeg_records.append(eeg_record)
        
        if eeg_records:
            db.bulk_save_objects(eeg_records)
            db.commit()
            
    except Exception as e:
        print(f"Error handling EEG data: {e}")
        db.rollback()


async def handle_alert(data: dict, session_id: UUID, db: Session):
    """Handle incoming fatigue alert and store in database"""
    try:
        alert = Alert(
            session_id=session_id,
            timestamp=datetime.fromisoformat(data.get("timestamp").replace("Z", "+00:00")),
            alert_level=data.get("alert_level"),
            fatigue_score=data.get("fatigue_score"),
            eeg_contribution=data.get("eeg_contribution", 1.0),
            trigger_reason=data.get("trigger_reason"),
            acknowledged=False
        )
        
        db.add(alert)
        
        # Update session alert count
        session = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
        if session:
            session.alert_count += 1
        
        db.commit()
        
    except Exception as e:
        print(f"Error handling alert: {e}")
        db.rollback()
