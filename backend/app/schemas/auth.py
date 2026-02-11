"""
Authentication Schemas
Pydantic models for authentication and JWT tokens
Week 2, Tuesday - API Routes
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token"""
    user_id: Optional[UUID] = None
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request payload"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "SecurePassword123"
                }
            ]
        }
    }


class RegisterRequest(BaseModel):
    """User registration request payload"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name")
    role: str = Field(default="student", description="User role: student, researcher, admin")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "newuser@example.com",
                    "password": "SecurePassword123",
                    "full_name": "John Doe",
                    "role": "student"
                }
            ]
        }
    }


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="Refresh token to get new access token")


class GoogleAuthRequest(BaseModel):
    """Google OAuth authentication request"""
    firebase_token: str = Field(..., description="Firebase ID token from Google Sign-In")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOWdkazcifQ..."
                }
            ]
        }
    }

