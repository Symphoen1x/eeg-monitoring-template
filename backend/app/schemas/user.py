"""
User Schemas
Pydantic models for user data validation
Week 2, Tuesday - API Routes
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = Field(default="student", pattern="^(student|researcher|admin)$")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[str] = Field(None, pattern="^(student|researcher|admin)$")
    is_active: Optional[bool] = None
    profile_picture: Optional[str] = None


class UserInDB(UserBase):
    """Schema for user in database (includes hashed password)"""
    id: UUID
    hashed_password: Optional[str] = None  # Nullable for OAuth users
    is_active: bool
    oauth_provider: Optional[str] = None
    google_id: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """Schema for user response (excludes password)"""
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    oauth_provider: Optional[str] = None  # OAuth provider if applicable
    google_id: Optional[str] = None  # Google user ID
    profile_picture: Optional[str] = None  # Profile picture URL
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
