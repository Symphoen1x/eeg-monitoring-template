"""
User Management API Routes
Profile retrieval and updates
Week 3, Monday - User Profile Features
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.schemas.user import UserResponse, UserUpdate
from app.api.dependencies import get_current_user
from app.core.cache import cache_user_session, invalidate_user_cache

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current logged-in user profile
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    
    - **full_name**: Update display name
    - **profile_picture**: Update avatar URL/path
    """
    # Check if anything to update
    if not user_update.model_dump(exclude_unset=True):
        return current_user
    
    # Re-query user from this session to avoid detached instance error
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    # Update fields
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
        
    if user_update.profile_picture is not None:
        user.profile_picture = user_update.profile_picture
        
    # Commit changes
    db.commit()
    db.refresh(user)
    
    # Update cache
    user_cache_data = {
        "id": str(user.id),
        "email": user.email,
        "hashed_password": user.hashed_password,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "profile_picture": user.profile_picture
    }
    
    cache_user_session(user.id, user_cache_data)
    
    return user

