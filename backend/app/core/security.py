"""
JWT Token Management
Functions for creating and verifying JWT tokens
Week 2, Tuesday - Authentication Implementation
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from uuid import UUID

from app.core.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Data to encode in token (user_id, email, etc.)
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token with longer expiration
    
    Args:
        data: Data to encode in token (user_id, email, etc.)
    
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token to verify
        token_type: Type of token ("access" or "refresh")
    
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        print(f"🔍 Verifying {token_type} token...")
        print(f"🔍 Token (first 50 chars): {token[:50]}...")
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"✅ Token decoded successfully")
        print(f"📋 Payload type: {payload.get('type')}")
        print(f"📋 Expected type: {token_type}")
        
        # Verify token type
        if payload.get("type") != token_type:
            print(f"❌ Token type mismatch! Got {payload.get('type')}, expected {token_type}")
            return None
        
        print(f"✅ Token verified successfully")
        return payload
    except JWTError as e:
        print(f"❌ JWT Error: {str(e)}")
        return None


def get_user_id_from_token(token: str) -> Optional[UUID]:
    """
    Extract user ID from JWT token
    
    Args:
        token: JWT token
    
    Returns:
        User UUID if valid, None otherwise
    """
    payload = verify_token(token)
    if payload is None:
        return None
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None
    
    try:
        return UUID(user_id_str)
    except ValueError:
        return None
