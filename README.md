<<<<<<< HEAD
# eeg-monitoring-template
=======
# 🧠 EEG Monitoring Template

A generic, reusable backend template for real-time EEG monitoring applications. Built with **FastAPI + TimescaleDB + Muse 2 (LSL)**.

## ✨ Features

- **EEG Data Pipeline**: Muse 2 → LSL → Python Processing → Backend API → TimescaleDB
- **Real-time Streaming**: WebSocket for live EEG data
- **Authentication**: JWT + Google OAuth (Firebase)
- **Session Management**: Create, track, and complete monitoring sessions
- **Fatigue Detection**: Cognitive state classification (alert/drowsy/fatigued)
- **Alerting System**: Automatic fatigue alerts with configurable thresholds
- **Session Playback**: Retrieve historical EEG data with time-range filtering
- **Data Export**: Download session data as CSV or JSON

## 🏗️ Architecture

```
Muse 2 Headband
      ↓ (Bluetooth)
   LSL Stream
      ↓
eeg-processing/     ← Python: acquisition, preprocessing, analysis
      ↓ (HTTP POST)
backend/             ← FastAPI: API, auth, database
      ↓
TimescaleDB          ← Time-series optimized PostgreSQL
```

## 📁 Structure

```
eeg-monitoring-template/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── .env.example               # Environment template
│   ├── requirements.txt           # Python dependencies
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── auth.py            # Login, register, Google OAuth
│   │   │   ├── users.py           # User profile CRUD
│   │   │   ├── sessions.py        # Monitoring session CRUD
│   │   │   ├── eeg.py             # EEG data ingestion (HTTP)
│   │   │   ├── alerts.py          # Fatigue alerting
│   │   │   ├── playback.py        # Session playback API
│   │   │   ├── export.py          # CSV/JSON export
│   │   │   └── websocket.py       # Real-time streaming
│   │   ├── core/                  # Config, security, Redis, Firebase
│   │   ├── db/                    # Models, database, migrations
│   │   └── schemas/               # Pydantic validation
│   └── alembic/                   # Database migrations
│
└── eeg-processing/
    ├── main.py                    # EEG processing entry point
    ├── server.py                  # HTTP server → backend
    ├── config.py                  # Device configuration
    └── eeg/
        ├── acquisition.py         # Muse 2 LSL connection
        ├── preprocessing.py       # Signal filtering
        ├── analysis.py            # Band power analysis & fatigue scoring
        └── features.py            # Feature extraction
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL + TimescaleDB
- Redis (optional, for caching)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python -m app.db.init_db

# Run backend
python main.py
# → http://localhost:8000/api/docs
```

### 2. EEG Processing Setup

```bash
cd eeg-processing
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

# Start EEG processing (requires Muse 2 connected via LSL)
python main.py
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login (JWT) |
| `/api/v1/auth/google` | POST | Google OAuth |
| `/api/v1/sessions` | POST/GET | Create/list sessions |
| `/api/v1/sessions/{id}` | GET/PATCH/DELETE | Session CRUD |
| `/api/v1/sessions/{id}/complete` | POST | Complete session |
| `/api/v1/eeg/stream` | POST | Ingest EEG data |
| `/api/v1/alerts` | GET/POST | Fatigue alerts |
| `/api/v1/sessions/{id}/eeg` | GET | Playback EEG data |
| `/api/v1/sessions/{id}/timeline` | GET | Session timeline |
| `/api/v1/sessions/{id}/export` | GET | Export CSV/JSON |
| `/ws/session/{id}` | WS | Real-time streaming |

## 🎯 Customization

This template uses a `session_type` field to support different use cases:

```python
# Create a study monitoring session
POST /api/v1/sessions
{
    "session_name": "Morning Study Session",
    "session_type": "study",
    "device_type": "Muse 2",
    "context_metadata": {
        "subject": "Mathematics",
        "environment": "library"
    }
}
```

Supported session types: `general`, `study`, `work`, `driving`, or any custom string.

## 📄 License

MIT
>>>>>>> 3b92bba (feat: Implement initial EEG monitoring system including backend API, EEG processing pipeline, database, and real-time WebSocket communication.)
