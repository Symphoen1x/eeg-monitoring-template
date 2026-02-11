"""
Database Models for EEG Monitoring Template
SQLAlchemy ORM models — Generic EEG monitoring platform
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


# ============================================
# USER MODEL
# ============================================

class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="user")  # user, researcher, admin
    is_active = Column(Boolean, default=True)
    oauth_provider = Column(String(50), nullable=True)  # google, etc.
    google_id = Column(String(255), nullable=True, unique=True)
    profile_picture = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sessions = relationship("MonitoringSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(email={self.email}, role={self.role})>"


# ============================================
# MONITORING SESSION MODEL
# ============================================

class MonitoringSession(Base):
    """Generic monitoring session"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_name = Column(String(255), nullable=False)
    session_type = Column(String(100), default="general")  # general, study, work, driving, etc.
    device_type = Column(String(100))  # Muse 2, OpenBCI, etc.
    session_status = Column(String(50), default="active")  # active, completed, failed
    calibration_data = Column(JSONB)  # Baseline calibration parameters
    settings = Column(JSONB)  # Custom settings and thresholds
    context_metadata = Column(JSONB)  # Flexible field for use-case-specific data
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    avg_fatigue_score = Column(Float, nullable=True)
    max_fatigue_score = Column(Float, nullable=True)
    alert_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    eeg_data = relationship("EEGData", back_populates="session", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MonitoringSession(id={self.id}, name={self.session_name}, type={self.session_type})>"


# ============================================
# EEG DATA MODEL (TimescaleDB Hypertable)
# ============================================

class EEGData(Base):
    """
    EEG time-series data model
    Will be converted to TimescaleDB hypertable after creation
    """
    __tablename__ = "eeg_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    
    # Raw EEG channels (JSON array)
    raw_channels = Column(JSONB)  # {"AF7": 0.5, "AF8": 0.3, "TP9": 0.2, "TP10": 0.4}
    
    # Band powers (Hz)
    delta_power = Column(Float)  # 1-4 Hz
    theta_power = Column(Float)  # 4-8 Hz
    alpha_power = Column(Float)  # 8-13 Hz
    beta_power = Column(Float)  # 13-30 Hz
    gamma_power = Column(Float)  # 30-50 Hz
    
    # Derived metrics
    theta_alpha_ratio = Column(Float)  # Drowsiness indicator
    beta_alpha_ratio = Column(Float)  # Engagement index
    
    # Quality metrics
    signal_quality = Column(Float)  # 0-1 scale
    
    # Classification
    cognitive_state = Column(String(50))  # alert, drowsy, fatigued
    eeg_fatigue_score = Column(Float)  # 0-100
    
    # Relationship
    session = relationship("MonitoringSession", back_populates="eeg_data")
    
    def __repr__(self):
        return f"<EEGData(session_id={self.session_id}, timestamp={self.timestamp})>"


# ============================================
# ALERTS MODEL
# ============================================

class Alert(Base):
    """Fatigue/cognitive state alerts triggered during session"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    
    # Alert details
    alert_level = Column(String(50))  # warning, critical
    fatigue_score = Column(Float)  # Combined fatigue score (0-100)
    
    # Contribution weights
    eeg_contribution = Column(Float, default=1.0)  # EEG-only by default
    
    # Trigger reason
    trigger_reason = Column(String(255))  # high_theta_alpha, sustained_drowsiness, etc.
    
    # User interaction
    acknowledged = Column(Boolean, default=False)
    
    # Relationship
    session = relationship("MonitoringSession", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(session_id={self.session_id}, level={self.alert_level})>"
