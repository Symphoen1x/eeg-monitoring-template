"""
EEG Monitoring Template — Backend API
Main application entry point
"""

import time
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.redis import init_redis, close_redis, redis_health_check
from app.core.firebase import init_firebase
from app.core.cache import get_cache_stats
from app.api.routes.auth import router as auth_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.websocket import router as websocket_router
from app.api.routes.eeg import router as eeg_router
from app.api.routes.users import router as users_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.playback import router as playback_router
from app.api.routes.export import router as export_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title="EEG Monitoring API",
    version="1.0.0",
    description="""
## EEG Monitoring Platform

Real-time EEG-based cognitive state and fatigue detection system.

**Core Features:**
- 🧠 EEG signal acquisition (Muse 2 via LSL)
- 📊 Real-time signal processing & analysis
- ⚠️ Fatigue/drowsiness alerting
- 📈 TimescaleDB for time-series data storage
- 📁 Session playback & data export

**Flexible Use Cases:**
Study monitoring, work productivity, driver safety, research, and more.

### Documentation
- **API Docs**: [Swagger UI](/api/docs)
- **Alternative**: [ReDoc](/api/redoc)
    """,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication (register, login, logout, refresh)"
        },
        {
            "name": "Users",
            "description": "User profile management"
        },
        {
            "name": "Sessions",
            "description": "Monitoring session management (CRUD)"
        },
        {
            "name": "EEG",
            "description": "EEG data streaming and ingestion"
        },
        {
            "name": "Alerts",
            "description": "Fatigue alerting system"
        },
        {
            "name": "Session Playback",
            "description": "Historical EEG data retrieval and timeline"
        },
        {
            "name": "Data Export",
            "description": "Session data export (CSV/JSON)"
        },
        {
            "name": "WebSocket",
            "description": "Real-time data streaming"
        },
        {
            "name": "Health",
            "description": "System health and monitoring"
        }
    ]
)

# ============================================
# MIDDLEWARE
# ============================================

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests with timing"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    
    return response


# CORS — customize for your deployment
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)


# ============================================
# ROUTERS
# ============================================
API_V1_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(users_router, prefix=API_V1_PREFIX)
app.include_router(sessions_router, prefix=API_V1_PREFIX)
app.include_router(websocket_router, prefix=API_V1_PREFIX)
app.include_router(eeg_router, prefix=API_V1_PREFIX)
app.include_router(alerts_router, prefix=API_V1_PREFIX)
app.include_router(playback_router, prefix=API_V1_PREFIX)
app.include_router(export_router, prefix=API_V1_PREFIX)


# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — API status"""
    return {
        "name": "EEG Monitoring API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    redis_health = redis_health_check()
    cache_stats = get_cache_stats()
    return {
        "status": "healthy",
        "service": "eeg-monitoring-backend",
        "redis": redis_health,
        "cache": cache_stats
    }


@app.get("/api/v1/info", tags=["Health"])
async def api_info():
    """API information"""
    return {
        "name": "EEG Monitoring API",
        "version": "1.0.0",
        "endpoints": {
            "auth": f"{API_V1_PREFIX}/auth",
            "sessions": f"{API_V1_PREFIX}/sessions",
            "eeg": f"{API_V1_PREFIX}/eeg",
            "websocket": f"{API_V1_PREFIX}/ws"
        },
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc"
        }
    }


# ============================================
# LIFECYCLE EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    print("=" * 60)
    print("🧠 EEG Monitoring API Starting...")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    
    print("\n🔧 Initializing Redis...")
    init_redis()
    
    print("\n🔥 Initializing Firebase...")
    init_firebase()
    
    print("\n📊 Starting EEG data buffer...")
    try:
        from app.core.eeg_relay import start_eeg_buffer
        await start_eeg_buffer()
        print("✅ EEG buffer started successfully")
    except Exception as e:
        print(f"❌ Failed to start EEG buffer: {e}")
    
    print(f"\n📚 Documentation: /api/docs")
    print(f"🔌 WebSocket: /api/v1/ws/session/{{session_id}}")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown"""
    print("=" * 60)
    print("🛑 EEG Monitoring API Shutting Down...")
    
    print("\n📊 Stopping EEG data buffer...")
    try:
        from app.core.eeg_relay import stop_eeg_buffer
        await stop_eeg_buffer()
        print("✅ EEG buffer stopped and flushed")
    except Exception as e:
        print(f"❌ Failed to stop EEG buffer: {e}")
    
    print("\n🔧 Closing Redis connection...")
    close_redis()
    
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )