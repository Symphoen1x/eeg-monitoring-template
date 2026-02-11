"""
Pydantic Schemas Package
Export all schemas for easy importing
"""

from .auth import *
from .user import *
from .session import *
from .eeg import *

__all__ = [
    # Auth
    "Token",
    "TokenData",
    "LoginRequest",
    "RegisterRequest",
    
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    
    # Session
    "SessionBase",
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "SessionListResponse",
    
    # EEG
    "EEGDataPoint",
    "EEGStreamData",
    "FaceDetectionData",
]
