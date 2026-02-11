# Database Migrations

This directory contains SQL migration scripts for database schema changes.

## Migrations

### 001_add_oauth_to_users.sql
Adds OAuth support to the users table:
- Adds `oauth_provider` column (VARCHAR 50, nullable)
- Adds `google_id` column (VARCHAR 255, unique, nullable)
- Adds `profile_picture` column (VARCHAR 500, nullable)
- Makes `hashed_password` nullable for OAuth users
- Creates index on `google_id`

## Running Migrations

### Manual (PostgreSQL)
```bash
# Connect to database
psql -U postgres -d fumorive

# Run migration
\i migrations/001_add_oauth_to_users.sql
```

### Python Script (automated)
```bash
cd backend
python -c "from app.db.database import engine; from pathlib import Path; engine.execute(Path('migrations/001_add_oauth_to_users.sql').read_text())"
```

### Rollback
```bash
psql -U postgres -d fumorive
\i migrations/001_add_oauth_to_users_rollback.sql
```

## Note
These are manual SQL migrations. For future projects, consider using Alembic for automatic migration generation and version control.
