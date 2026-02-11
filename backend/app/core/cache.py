"""
Caching Utilities for Authentication
Redis-based caching for user sessions and JWT token blacklist
Week 2, Wednesday - Redis Session Caching
"""

import json
from typing import Optional
from datetime import timedelta
from uuid import UUID

from app.core.redis import get_redis
from app.core.config import settings


# ============================================
# CACHE KEY PREFIXES
# ============================================

USER_CACHE_PREFIX = "user:"
TOKEN_BLACKLIST_PREFIX = "blacklist:"


# ============================================
# USER SESSION CACHING
# ============================================

def cache_user_session(user_id: UUID, user_data: dict, ttl_minutes: int = None) -> bool:
    """
    Cache user session data in Redis
    
    Args:
        user_id: User UUID
        user_data: User data to cache (dict, will be JSON serialized)
        ttl_minutes: Time to live in minutes (default: ACCESS_TOKEN_EXPIRE_MINUTES)
    
    Returns:
        True if cached successfully, False otherwise
    """
    r = get_redis()
    if not r:
        return False
    
    try:
        cache_key = f"{USER_CACHE_PREFIX}{user_id}"
        ttl = ttl_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        # Serialize user data to JSON
        user_json = json.dumps(user_data)
        
        # Set with expiration
        r.setex(
            name=cache_key,
            time=timedelta(minutes=ttl),
            value=user_json
        )
        
        return True
        
    except Exception as e:
        print(f"⚠️  Cache user session error: {e}")
        return False


def get_cached_user(user_id: UUID) -> Optional[dict]:
    """
    Get cached user session data
    
    Args:
        user_id: User UUID
    
    Returns:
        User data dict if cached, None otherwise
    """
    r = get_redis()
    if not r:
        return None
    
    try:
        cache_key = f"{USER_CACHE_PREFIX}{user_id}"
        user_json = r.get(cache_key)
        
        if user_json:
            return json.loads(user_json)
        
        return None
        
    except Exception as e:
        print(f"⚠️  Get cached user error: {e}")
        return None


def invalidate_user_cache(user_id: UUID) -> bool:
    """
    Invalidate (delete) user session cache
    
    Args:
        user_id: User UUID
    
    Returns:
        True if deleted, False otherwise
    """
    r = get_redis()
    if not r:
        return False
    
    try:
        cache_key = f"{USER_CACHE_PREFIX}{user_id}"
        r.delete(cache_key)
        return True
        
    except Exception as e:
        print(f"⚠️  Invalidate user cache error: {e}")
        return False


# ============================================
# TOKEN BLACKLIST (for Logout)
# ============================================

def blacklist_token(token: str, ttl_minutes: int = None) -> bool:
    """
    Add JWT token to blacklist (for logout)
    Token will be blacklisted until it expires naturally
    
    Args:
        token: JWT token string
        ttl_minutes: Time to live (default: ACCESS_TOKEN_EXPIRE_MINUTES)
    
    Returns:
        True if blacklisted successfully, False otherwise
    """
    r = get_redis()
    if not r:
        return False
    
    try:
        cache_key = f"{TOKEN_BLACKLIST_PREFIX}{token}"
        ttl = ttl_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        # Set with expiration (value doesn't matter, we just check existence)
        r.setex(
            name=cache_key,
            time=timedelta(minutes=ttl),
            value="1"
        )
        
        return True
        
    except Exception as e:
        print(f"⚠️  Blacklist token error: {e}")
        return False


def is_token_blacklisted(token: str) -> bool:
    """
    Check if JWT token is blacklisted
    
    Args:
        token: JWT token string
    
    Returns:
        True if blacklisted, False otherwise
    """
    r = get_redis()
    if not r:
        # If Redis not available, cannot check blacklist
        # Fallback: allow token (less secure but maintains functionality)
        return False
    
    try:
        cache_key = f"{TOKEN_BLACKLIST_PREFIX}{token}"
        return r.exists(cache_key) > 0
        
    except Exception as e:
        print(f"⚠️  Check token blacklist error: {e}")
        return False


def blacklist_refresh_token(token: str) -> bool:
    """
    Blacklist refresh token (longer TTL)
    
    Args:
        token: Refresh token string
    
    Returns:
        True if blacklisted successfully, False otherwise
    """
    r = get_redis()
    if not r:
        return False
    
    try:
        cache_key = f"{TOKEN_BLACKLIST_PREFIX}{token}"
        ttl_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        
        # Set with expiration matching refresh token lifetime
        r.setex(
            name=cache_key,
            time=timedelta(days=ttl_days),
            value="1"
        )
        
        return True
        
    except Exception as e:
        print(f"⚠️  Blacklist refresh token error: {e}")
        return False


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_cache_stats() -> dict:
    """
    Get Redis cache statistics
    
    Returns:
        dict with cache statistics
    """
    r = get_redis()
    if not r:
        return {"status": "unavailable"}
    
    try:
        # Count cached users
        user_keys = r.keys(f"{USER_CACHE_PREFIX}*")
        
        # Count blacklisted tokens
        blacklist_keys = r.keys(f"{TOKEN_BLACKLIST_PREFIX}*")
        
        # Get Redis memory usage
        info = r.info("memory")
        
        return {
            "status": "available",
            "cached_users": len(user_keys),
            "blacklisted_tokens": len(blacklist_keys),
            "memory_used": info.get("used_memory_human", "unknown")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def clear_all_cache() -> bool:
    """
    Clear all cache (DANGEROUS - use only for testing/development)
    
    Returns:
        True if cleared, False otherwise
    """
    r = get_redis()
    if not r:
        return False
    
    try:
        r.flushdb()
        print("⚠️  All Redis cache cleared!")
        return True
        
    except Exception as e:
        print(f"⚠️  Clear cache error: {e}")
        return False
