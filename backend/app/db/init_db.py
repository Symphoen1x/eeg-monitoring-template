"""
Database Initialization Script
Creates all database tables and initializes TimescaleDB

Usage:
    python -m app.db.init_db
"""

from app.db.database import Base, engine
from app.db.models import User, MonitoringSession, EEGData, Alert
from app.db.init_timescaledb import create_hypertables


def init_db():
    """
    Initialize database:
    1. Create all tables from SQLAlchemy models
    2. Convert time-series tables to TimescaleDB hypertables
    """
    
    print("=" * 60)
    print("EEG Monitoring Template - Database Initialization")
    print("=" * 60)
    
    print("\n📦 Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return
    
    print("\n" + "=" * 60)
    print("TimescaleDB Setup")
    print("=" * 60)
    
    # Setup TimescaleDB hypertables
    create_hypertables()
    
    print("\n" + "=" * 60)
    print("✨ Database initialization complete!")
    print("=" * 60)


if __name__ == "__main__":
    init_db()
