"""
Authentication API Routes
Login, Register, Token Refresh endpoints
Week 2, Wednesday - Updated with Redis Caching
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import Token, LoginRequest, RegisterRequest, RefreshTokenRequest, GoogleAuthRequest
from app.schemas.user import UserResponse
from app.core.password import hash_password, verify_password
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.core.cache import cache_user_session, blacklist_token, blacklist_refresh_token, invalidate_user_cache
from app.core.firebase import verify_firebase_token, is_firebase_available
from app.api.dependencies import get_current_user, oauth2_scheme

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account
    
    - **email**: Valid email address (must be unique)
    - **password**: Password (min 8 characters)
    - **full_name**: User's full name
    - **role**: User role (student, researcher, admin)
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate role
    if user_data.role not in ["student", "researcher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be: student, researcher, or admin"
        )
    
    # Create new user
    hashed_pwd = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pwd,
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password to get JWT tokens
    
    Uses OAuth2 password flow (username field = email)
    
    Returns:
    - **access_token**: Short-lived token for API requests
    - **refresh_token**: Long-lived token for getting new access tokens
    """
    # Find user by email (username field contains email)
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    # Create tokens with user info
    token_data = {
        "sub": str(user.email),  # JWT standard: sub = unique identifier (email)
        "user_id": str(user.id),  # Include user_id for reference
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Cache user session in Redis
    user_cache_data = {
        "id": str(user.id),
        "email": user.email,
        "hashed_password": user.hashed_password,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active
    }
    cache_user_session(user.id, user_cache_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login/json", response_model=Token)
async def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with JSON payload (alternative to OAuth2 form)
    
    - **email**: User email
    - **password**: User password
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    # Create tokens with user info
    token_data = {
        "sub": str(user.email),  # JWT standard: sub = unique identifier (email)
        "user_id": str(user.id),  # Include user_id for reference
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Cache user session in Redis
    user_cache_data = {
        "id": str(user.id),
        "email": user.email,
        "hashed_password": user.hashed_password,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active
    }
    cache_user_session(user.id, user_cache_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Get new access token using refresh token
    
    - **refresh_token**: Valid refresh token
    """
    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token, token_type="refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")  # sub now contains email
    user_id = payload.get("user_id")  # get user_id if available
    
    # Verify user still exists and is active
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Blacklist old refresh token (prevent reuse)
    blacklist_refresh_token(refresh_data.refresh_token)
    
    # Create new tokens with user info
    token_data = {
        "sub": str(user.email),  # JWT standard: sub = unique identifier (email)
        "user_id": str(user.id),  # Include user_id for reference
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    # Cache user session with new token
    user_cache_data = {
        "id": str(user.id),
        "email": user.email,
        "hashed_password": user.hashed_password,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active
    }
    cache_user_session(user.id, user_cache_data)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/google", response_model=Token)
async def google_login(
    auth_data: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Google OAuth via Firebase
    
    Flow:
    1. Frontend authenticates with Google via Firebase SDK
    2. Frontend sends Firebase ID token to this endpoint
    3. Backend verifies token with Firebase Admin SDK
    4. Backend creates/finds user in database
    5. Backend generates JWT tokens (same as traditional login)
    
    - **firebase_token**: Firebase ID token from Google Sign-In
    """
    # Check if Firebase is available
    if not is_firebase_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google authentication is not available. Firebase is not configured."
        )
    
    # Verify Firebase token and extract user info
    firebase_user = verify_firebase_token(auth_data.firebase_token)
    
    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user information from Firebase token
    email = firebase_user.get('email')
    google_id = firebase_user.get('uid')
    full_name = firebase_user.get('name', email.split('@')[0])  # Use email prefix if name not provided
    profile_picture = firebase_user.get('picture')
    email_verified = firebase_user.get('email_verified', False)
    
    if not email or not google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and Google ID are required from Firebase token"
        )
    
    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified by Google. Please verify your email first."
        )
    
    # Try to find existing user by email or google_id
    user = db.query(User).filter(
        (User.email == email) | (User.google_id == google_id)
    ).first()
    
    if user:
        # Existing user - update OAuth info if needed
        if not user.google_id:
            # Link Google account to existing email/password account
            user.google_id = google_id
            user.oauth_provider = "google"
            user.profile_picture = profile_picture
            db.commit()
            db.refresh(user)
        elif user.google_id != google_id:
            # Email exists but with different Google account - this shouldn't happen
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered with a different account"
            )
        # Update profile picture if changed
        elif user.profile_picture != profile_picture:
            user.profile_picture = profile_picture
            db.commit()
            db.refresh(user)
    else:
        # New user - create account with OAuth
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=None,  # OAuth users don't have passwords
            oauth_provider="google",
            google_id=google_id,
            profile_picture=profile_picture,
            role="student",  # Default role
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    # Create JWT tokens (same as traditional login)
    token_data = {
        "sub": str(user.email),
        "user_id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Cache user session in Redis
    user_cache_data = {
        "id": str(user.id),
        "email": user.email,
        "hashed_password": user.hashed_password if user.hashed_password else "",
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "oauth_provider": user.oauth_provider,
        "google_id": user.google_id
    }
    cache_user_session(user.id, user_cache_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }



@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """
    Logout endpoint with proper token invalidation
    
    Blacklists the access token and clears user cache.
    Client should also discard refresh token.
    
    Requires authentication (must provide access token).
    """
    # Blacklist the access token
    blacklist_token(token, ttl_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Invalidate user cache
    invalidate_user_cache(current_user.id)
    
    return {
        "message": "Successfully logged out",
        "detail": "Token has been revoked and cache cleared"
    }
