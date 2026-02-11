"""
Session Management API Routes
CRUD operations for monitoring sessions
Generic EEG Monitoring Template
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.db.database import get_db
from app.db.models import User, MonitoringSession
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new monitoring session
    
    - **session_name**: Name for the session
    - **session_type**: Type of monitoring (general, study, work, etc.)
    - **device_type**: EEG device type (e.g., "Muse 2")
    - **calibration_data**: Optional baseline calibration data
    - **settings**: Optional custom settings and thresholds
    - **context_metadata**: Optional use-case-specific data
    """
    new_session = MonitoringSession(
        user_id=current_user.id,
        session_name=session_data.session_name,
        session_type=session_data.session_type,
        device_type=session_data.device_type,
        calibration_data=session_data.calibration_data,
        settings=session_data.settings,
        context_metadata=session_data.context_metadata,
        session_status="active"
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (active, completed, failed)"),
    session_type: Optional[str] = Query(None, description="Filter by session type"),
):
    """
    Get list of user's sessions with pagination
    """
    query = db.query(MonitoringSession).filter(MonitoringSession.user_id == current_user.id)
    
    if status:
        query = query.filter(MonitoringSession.session_status == status)
    if session_type:
        query = query.filter(MonitoringSession.session_type == session_type)
    
    total = query.count()
    offset = (page - 1) * page_size
    sessions = query.order_by(MonitoringSession.started_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "sessions": sessions,
        "page": page,
        "page_size": page_size
    }


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific session by ID"""
    session = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    return session


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    session_update: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a session (partial update)"""
    session = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this session"
        )
    
    update_data = session_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    
    return session


@router.post("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a session as completed.
    Sets status to 'completed', ended_at to now, calculates duration.
    """
    session = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to complete this session"
        )
    
    session.session_status = "completed"
    session.ended_at = datetime.utcnow()
    
    if session.started_at and session.ended_at:
        duration = (session.ended_at - session.started_at).total_seconds()
        session.duration_seconds = int(duration)
    
    db.commit()
    db.refresh(session)
    
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a session and all associated data (EEG data, alerts).
    """
    session = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this session"
        )
    
    db.delete(session)
    db.commit()
    
    return None
