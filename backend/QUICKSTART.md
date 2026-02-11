# 🚀 Quick Start Guide - Backend API

## Prerequisites
- Python 3.10+
- PostgreSQL with TimescaleDB
- Redis (optional, for future caching)

## Setup Instructions

### 1. Activate Virtual Environment
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies (if not installed)
```bash
pip install -r requirements.txt
pip install pydantic[email] python-jose[cryptography] passlib[bcrypt]
```

### 3. Configure Environment
Check `.env` file and update if needed:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/ergodrive
SECRET_KEY=your-secret-key-here  # Change this!
CORS_ORIGINS=["http://localhost:5173"]
```

### 4. Initialize Database
```bash
# Make sure PostgreSQL is running
# Run migrations (if using Alembic)
alembic upgrade head

# Or create tables manually using init scripts
python -m app.db.init_db
python -m app.db.init_timescaledb
```

### 5. Start Database & Server

**IMPORTANT**: You need BOTH Docker (database) and Python (API server) running!

```bash
# STEP 1: Start PostgreSQL Database (Docker)
# First, open Docker Desktop application
# Then start the database container:
docker start fumorive-db

# Verify database is running:
docker ps
# You should see "fumorive-db" container with status "Up"

# STEP 2: Start FastAPI Backend Server (Python)
cd C:\Users\User\Fumorive\backend
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Method A: Using main.py
python main.py

# Method B: Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**What's Running:**
- 🐳 **Docker**: PostgreSQL database on `localhost:5432`
- 🐍 **Python**: FastAPI server on `localhost:8000`
- ✅ **Both are required** for the API to work properly!

You should see:
```
============================================================
🚀 ERGODRIVE Backend API Starting...
📝 Environment: development
🌐 CORS Origins: ['http://localhost:5173', ...]
📚 Documentation: /api/docs
🔌 WebSocket: /api/v1/ws/session/{session_id}
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 6. Access API Documentation
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **API Info**: http://localhost:8000/api/v1/info

## Testing the API

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"healthy","service":"ergodrive-backend"}`

### Test 2: Register a User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123",
    "full_name": "Test User",
    "role": "student"
  }'
```

### Test 3: Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

Save the `access_token` from the response!

### Test 4: Create a Session
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "session_name": "Test Drive Session",
    "device_type": "Muse 2",
    "settings": {"difficulty": "easy"}
  }'
```

### Test 5: WebSocket Connection (Browser Console)
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/session/YOUR_SESSION_ID');

ws.onopen = () => {
  console.log('Connected!');
  
  // Send ping
  ws.send(JSON.stringify({
    type: 'ping'
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

## Common Issues

### Issue 1: Port Already in Use
```bash
# Find process using port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Issue 2: Database Connection Failed
- Make sure PostgreSQL is running
- Check database name, user, and password in `.env`
- Verify TimescaleDB extension is installed

### Issue 3: Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
pip install pydantic[email] python-jose[cryptography] passlib[bcrypt]
```

## Next Steps

1. ✅ Backend API is running
2. Connect frontend (React + Vite)
3. Test WebSocket with Python LSL middleware
4. Integrate with game logic (Babylon.js)

## API Endpoints Summary

### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - OAuth2 login
- `POST /login/json` - JSON login
- `POST /refresh` - Refresh token
- `POST /logout` - Logout

### Sessions (`/api/v1/sessions`)
- `POST /` - Create session
- `GET /` - List sessions (with pagination)
- `GET /{id}` - Get session details
- `PATCH /{id}` - Update session
- `POST /{id}/complete` - Complete session
- `DELETE /{id}` - Delete session

### WebSocket (`/api/v1/ws`)
- `WS /session/{id}` - Real-time session streaming
- `WS /monitor` - Global monitoring feed

## Development Tips

1. **Auto-reload**: Use `--reload` flag for development
2. **Debug mode**: Set `LOG_LEVEL=DEBUG` in `.env`
3. **API Testing**: Use Swagger UI at `/api/docs` for interactive testing
4. **Database Viewer**: Use pgAdmin or DBeaver to inspect data

---

Happy coding! 🎉
