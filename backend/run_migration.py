"""
Run OAuth migration to add OAuth fields to users table
"""
from app.db.database import engine
from sqlalchemy import text
from pathlib import Path

# Read migration SQL
migration_path = Path(__file__).parent / 'migrations' / '001_add_oauth_to_users.sql'
with open(migration_path, 'r') as f:
    sql = f.read()

# Execute migration
try:
    with engine.connect() as conn:
        # Split by statement and execute
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                conn.execute(text(statement))
        conn.commit()
    print("✅ Migration completed successfully!")
    print("   Added columns: oauth_provider, google_id, profile_picture")
    print("   Made hashed_password nullable")
    print("   Created index on google_id")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    raise
