"""
EEG and Alert Schemas
Pydantic models for EEG data and alerting
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Union, List, Any
from datetime import datetime
from uuid import UUID


class EEGDataPoint(BaseModel):
    """Schema for single EEG data point"""
    timestamp: datetime
    raw_channels: Dict[str, float] = Field(..., description="Raw EEG channel data")
    delta_power: Optional[float] = Field(None, ge=0, description="Delta band power (1-4 Hz)")
    theta_power: Optional[float] = Field(None, ge=0, description="Theta band power (4-8 Hz)")
    alpha_power: Optional[float] = Field(None, ge=0, description="Alpha band power (8-13 Hz)")
    beta_power: Optional[float] = Field(None, ge=0, description="Beta band power (13-30 Hz)")
    gamma_power: Optional[float] = Field(None, ge=0, description="Gamma band power (30-50 Hz)")
    theta_alpha_ratio: Optional[float] = Field(None, ge=0, description="Drowsiness indicator")
    beta_alpha_ratio: Optional[float] = Field(None, ge=0, description="Engagement index")
    signal_quality: Optional[float] = Field(None, ge=0, le=1, description="Signal quality (0-1)")
    cognitive_state: Optional[str] = Field(None, pattern="^(alert|drowsy|fatigued)$")
    eeg_fatigue_score: Optional[float] = Field(None, ge=0, le=100, description="EEG fatigue score (0-100)")


class EEGStreamData(BaseModel):
    """
    Schema for receiving EEG data from Python LSL middleware via HTTP
    """
    session_id: UUID = Field(..., description="Active monitoring session UUID")
    timestamp: str = Field(..., description="ISO format timestamp")
    sample_rate: int = Field(256, description="Sampling rate in Hz")
    channels: Dict[str, float] = Field(
        ..., 
        description="EEG channel values (TP9, AF7, AF8, TP10)"
    )
    processed: Dict[str, Union[float, str]] = Field(
        default_factory=dict,
        description="Processed metrics (theta_power, alpha_power, cognitive_state, etc.)"
    )
    save_to_db: bool = Field(
        default=False,
        description="Whether to save this data point to database"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
                    "timestamp": "2026-01-19T12:00:00.123Z",
                    "sample_rate": 256,
                    "channels": {
                        "TP9": 0.123,
                        "AF7": 0.456,
                        "AF8": 0.789,
                        "TP10": 0.234
                    },
                    "processed": {
                        "theta_power": 0.45,
                        "alpha_power": 0.67,
                        "theta_alpha_ratio": 0.67,
                        "fatigue_score": 0.32
                    },
                    "save_to_db": False
                }
            ]
        }
    }


class EEGBatchData(BaseModel):
    """Schema for WebSocket streaming"""
    session_id: UUID
    data_points: list[EEGDataPoint]


class AlertData(BaseModel):
    """Schema for fatigue alert"""
    session_id: UUID
    timestamp: datetime
    alert_level: str = Field(..., pattern="^(warning|critical)$")
    fatigue_score: float = Field(..., ge=0, le=100)
    eeg_contribution: float = Field(default=1.0, ge=0, le=1)
    trigger_reason: str


class AlertResponse(BaseModel):
    """Schema for alert API response"""
    id: int
    session_id: UUID
    timestamp: datetime
    alert_level: str
    fatigue_score: float
    eeg_contribution: float
    trigger_reason: str
    acknowledged: bool
    
    model_config = {"from_attributes": True}


class AlertUpdate(BaseModel):
    """Schema for updating alert"""
    acknowledged: Optional[bool] = None
    trigger_reason: Optional[str] = None


class AlertList(BaseModel):
    """Schema for paginated alert list"""
    total: int
    limit: int
    offset: int
    alerts: list[AlertResponse]


# ============================================
# SESSION PLAYBACK RESPONSE SCHEMAS
# ============================================

class EEGDataResponse(BaseModel):
    """EEG data record for playback"""
    id: int
    session_id: UUID
    timestamp: datetime
    raw_channels: Optional[Dict[str, float]] = None
    delta_power: Optional[float] = None
    theta_power: Optional[float] = None
    alpha_power: Optional[float] = None
    beta_power: Optional[float] = None
    gamma_power: Optional[float] = None
    theta_alpha_ratio: Optional[float] = None
    beta_alpha_ratio: Optional[float] = None
    signal_quality: Optional[float] = None
    cognitive_state: Optional[str] = None
    eeg_fatigue_score: Optional[float] = None

    model_config = {"from_attributes": True}


class TimelineEvent(BaseModel):
    """Unified timeline event"""
    type: str  # "eeg", "alert"
    timestamp: datetime
    data: Dict[str, Any]


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper"""
    total: int
    page: int
    page_size: int
    has_next: bool


class PaginatedEEGResponse(PaginatedResponse):
    """Paginated EEG data"""
    data: List[EEGDataResponse]


class TimelineResponse(PaginatedResponse):
    """Paginated timeline"""
    events: List[TimelineEvent]
