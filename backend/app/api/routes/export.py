"""
Data Export API Routes
Download session data as CSV or JSON
Generic EEG Monitoring Template
"""

import csv
import io
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.db.database import get_db
from app.db.models import (
    User, MonitoringSession, EEGData, Alert
)
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Data Export"])


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


# Column definitions
EEG_COLUMNS = [
    "id", "timestamp", "delta_power", "theta_power", "alpha_power",
    "beta_power", "gamma_power", "theta_alpha_ratio", "beta_alpha_ratio",
    "signal_quality", "cognitive_state", "eeg_fatigue_score",
]

ALERT_COLUMNS = [
    "id", "timestamp", "alert_level", "fatigue_score",
    "eeg_contribution", "trigger_reason", "acknowledged",
]


def _query_data(db, model, session_id, start_time, end_time):
    q = db.query(model).filter(model.session_id == session_id)
    if start_time:
        q = q.filter(model.timestamp >= start_time)
    if end_time:
        q = q.filter(model.timestamp <= end_time)
    return q.order_by(model.timestamp.asc()).all()


def _rows_to_dicts(rows, columns):
    result = []
    for row in rows:
        d = {}
        for col in columns:
            val = getattr(row, col, None)
            if isinstance(val, datetime):
                val = val.isoformat()
            d[col] = val
        result.append(d)
    return result


def _generate_csv(rows: list[dict], columns: list[str]):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return output


@router.get("/{session_id}/export")
async def export_session_data(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    format: str = Query("csv", description="Export format: csv or json"),
    data_type: str = Query("eeg", description="Data type: eeg, alert, or all"),
    start_time: Optional[datetime] = Query(None, description="Filter from timestamp"),
    end_time: Optional[datetime] = Query(None, description="Filter to timestamp"),
):
    """
    Export session data as CSV or JSON file download.
    
    - **format**: `csv` or `json`
    - **data_type**: `eeg`, `alert`, or `all`
    """
    if format not in ("csv", "json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="format must be 'csv' or 'json'"
        )
    valid_types = ("eeg", "alert", "all")
    if data_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"data_type must be one of: {', '.join(valid_types)}"
        )

    session_obj = _get_user_session(session_id, current_user, db)
    session_name = session_obj.session_name.replace(" ", "_")

    export_data = {}

    if data_type in ("eeg", "all"):
        rows = _query_data(db, EEGData, session_id, start_time, end_time)
        export_data["eeg"] = _rows_to_dicts(rows, EEG_COLUMNS)

    if data_type in ("alert", "all"):
        rows = _query_data(db, Alert, session_id, start_time, end_time)
        export_data["alert"] = _rows_to_dicts(rows, ALERT_COLUMNS)

    # JSON format
    if format == "json":
        content = json.dumps(
            {
                "session_id": str(session_id),
                "session_name": session_obj.session_name,
                "exported_at": datetime.utcnow().isoformat(),
                "data": export_data,
            },
            indent=2,
            default=str,
        )
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{session_name}_{data_type}.json"'
            },
        )

    # CSV format
    if data_type == "all":
        all_columns = ["data_type"] + list(
            dict.fromkeys(EEG_COLUMNS + ALERT_COLUMNS)
        )
        combined_rows = []
        for dtype, rows in export_data.items():
            for row in rows:
                row["data_type"] = dtype
                combined_rows.append(row)
        combined_rows.sort(key=lambda r: r.get("timestamp", ""))
        csv_stream = _generate_csv(combined_rows, all_columns)
    else:
        column_map = {"eeg": EEG_COLUMNS, "alert": ALERT_COLUMNS}
        rows = export_data[data_type]
        csv_stream = _generate_csv(rows, column_map[data_type])

    return StreamingResponse(
        csv_stream,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{session_name}_{data_type}.csv"'
        },
    )
