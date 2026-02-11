"""
Redis Connection Manager
Handles Redis connection pool and provides connection access
Week 2, Wednesday - Redis Session Caching
"""

import redis
from typing import Optional
from app.core.config import settings


# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


def init_redis() -> redis.Redis:
    """
    Initialize Redis connection pool
    Call this on application startup
    
    Returns:
        Redis client instance
    """
    global _redis_pool, _redis_client
    
    try:
        # Create connection pool
        _redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,  # Auto-decode bytes to strings
            max_connections=10,
            socket_connect_timeout=5,
            socket_keepalive=True
        )
        
        # Create Redis client
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        
        # Test connection
        _redis_client.ping()
        print(f"✅ Redis connected: {settings.REDIS_URL}")
        
        return _redis_client
        
    except redis.ConnectionError as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("    Application will run without Redis caching")
        return None
    except Exception as e:
        print(f"⚠️  Redis initialization error: {e}")
        return None


def get_redis() -> Optional[redis.Redis]:
    """
    Get Redis client instance
    
    Returns:
        Redis client if connected, None otherwise
        
    Example:
        r = get_redis()
        if r:
            r.set('key', 'value')
    """
    return _redis_client


def close_redis():
    """
    Close Redis connection and cleanup pool
    Call this on application shutdown
    """
    global _redis_pool, _redis_client
    
    if _redis_client:
        try:
            _redis_client.close()
            print("✅ Redis connection closed")
        except Exception as e:
            print(f"⚠️  Error closing Redis: {e}")
    
    if _redis_pool:
        try:
            _redis_pool.disconnect()
        except Exception as e:
            print(f"⚠️  Error disconnecting Redis pool: {e}")
    
    _redis_pool = None
    _redis_client = None


def redis_health_check() -> dict:
    """
    Check Redis connection health
    
    Returns:
        dict with status and info
    """
    r = get_redis()
    
    if not r:
        return {
            "status": "disconnected",
            "message": "Redis client not initialized"
        }
    
    try:
        # Test connection
        r.ping()
        
        # Get Redis info
        info = r.info("server")
        
        return {
            "status": "connected",
            "redis_version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0)
        }
        
    except redis.ConnectionError:
        return {
            "status": "error",
            "message": "Cannot connect to Redis server"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
