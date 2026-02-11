"""
Session Playback API Routes
Retrieve historical EEG data for session replay
Generic EEG Monitoring Template
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.db.database import get_db
from app.db.models import (
    User, MonitoringSession, EEGData, Alert
)
from app.schemas.eeg import (
    EEGDataResponse, PaginatedEEGResponse,
    TimelineEvent, TimelineResponse
)
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/sessions", tags=["Session Playback"])


def _get_user_session(session_id: UUID, current_user: User, db: Session) -> MonitoringSession:
    """Helper: get session and verify ownership"""
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


@router.get("/{session_id}/eeg", response_model=PaginatedEEGResponse)
async def get_session_eeg(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_time: Optional[datetime] = Query(None, description="Filter from timestamp"),
    end_time: Optional[datetime] = Query(None, description="Filter to timestamp"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
):
    """
    Get EEG data for a session with optional time-range filtering.
    """
    _get_user_session(session_id, current_user, db)

    query = db.query(EEGData).filter(EEGData.session_id == session_id)

    if start_time:
        query = query.filter(EEGData.timestamp >= start_time)
    if end_time:
        query = query.filter(EEGData.timestamp <= end_time)

    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(EEGData.timestamp.asc()).offset(offset).limit(page_size).all()

    return PaginatedEEGResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
        data=records,
    )


@router.get("/{session_id}/timeline", response_model=TimelineResponse)
async def get_session_timeline(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_time: Optional[datetime] = Query(None, description="Filter from timestamp"),
    end_time: Optional[datetime] = Query(None, description="Filter to timestamp"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(200, ge=1, le=1000, description="Items per page"),
):
    """
    Get a unified timeline of EEG data and alerts for a session,
    merged and sorted chronologically.
    """
    _get_user_session(session_id, current_user, db)

    events: list[TimelineEvent] = []

    def _time_filter(query, model):
        if start_time:
            query = query.filter(model.timestamp >= start_time)
        if end_time:
            query = query.filter(model.timestamp <= end_time)
        return query

    # EEG data
    eeg_query = _time_filter(
        db.query(EEGData).filter(EEGData.session_id == session_id), EEGData
    )
    for row in eeg_query.order_by(EEGData.timestamp.asc()).limit(500).all():
        events.append(TimelineEvent(
            type="eeg",
            timestamp=row.timestamp,
            data={
                "id": row.id,
                "theta_alpha_ratio": row.theta_alpha_ratio,
                "signal_quality": row.signal_quality,
                "cognitive_state": row.cognitive_state,
                "eeg_fatigue_score": row.eeg_fatigue_score,
            }
        ))

    # Alerts
    alert_query = _time_filter(
        db.query(Alert).filter(Alert.session_id == session_id), Alert
    )
    for row in alert_query.order_by(Alert.timestamp.asc()).all():
        events.append(TimelineEvent(
            type="alert",
            timestamp=row.timestamp,
            data={
                "id": row.id,
                "alert_level": row.alert_level,
                "fatigue_score": row.fatigue_score,
                "trigger_reason": row.trigger_reason,
                "acknowledged": row.acknowledged,
            }
        ))

    events.sort(key=lambda e: e.timestamp)

    total = len(events)
    offset = (page - 1) * page_size
    page_events = events[offset: offset + page_size]

    return TimelineResponse(
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
        events=page_events,
    )
